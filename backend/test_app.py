import asyncio
import json
import os
import secrets
import security
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
import core
from app import app

@pytest.fixture(autouse=True)
def database(tmp_path,monkeypatch,postgres_url):
    global headers
    monkeypatch.setenv('APP_ENV','development')
    monkeypatch.setenv('SESSION_SECRET',secrets.token_urlsafe(48))
    monkeypatch.setenv('DEMO_ACCESS_HASHES_JSON',json.dumps({u:security.code_hash(u+'-test-code') for u in security.USERS}))
    monkeypatch.setenv('MCP_ACCESS_HASHES_JSON',json.dumps({u:security.code_hash(u+'-demo-token') for u in security.USERS}))
    if postgres_url:
        import psycopg
        from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
        schema='test_'+secrets.token_hex(8)
        with psycopg.connect(postgres_url,autocommit=True) as db: db.execute('CREATE SCHEMA '+schema)
        url=urlsplit(postgres_url)
        query=parse_qsl(url.query)+[('options','-csearch_path='+schema)]
        monkeypatch.setattr(core,'DB',urlunsplit((url.scheme,url.netloc,url.path,urlencode(query),url.fragment)))
    else: monkeypatch.setattr(core,'DB',str(tmp_path/'test.sqlite3'))
    monkeypatch.setenv('AI_PROVIDER','fixture')
    core.initialize()
    headers={'Authorization':'Bearer '+security.login('alice-test-code')['token']}
    yield
    if postgres_url:
        with psycopg.connect(postgres_url,autocommit=True) as db: db.execute('DROP SCHEMA '+schema+' CASCADE')

client = TestClient(app)
headers = {}

def review(project='harbor'):
    return client.post(f'/api/projects/{project}/reviews',headers=headers)

def test_identity_and_listing():
    assert client.get('/api/projects').status_code == 401
    assert client.get('/api/projects',headers={'Authorization':'Bearer fake'}).status_code == 401
    for token,pid in [('alice','harbor'),('bob','cedar'),('carol','quarry')]:
        result=client.get('/api/projects',headers={'Authorization':'Bearer '+security.login(token+'-test-code')['token']})
        assert [p['id'] for p in result.json()]==[pid]

def test_every_project_operation_denies_cross_project():
    assert client.get('/api/projects/cedar/documents',headers=headers).status_code==403
    assert review('cedar').status_code==403
    for action in ['approve','save']:
        assert client.post(f'/api/projects/cedar/reviews/forged/{action}',headers=headers,json={'request_key':'x'}).status_code==403

def test_approval_and_retry():
    r=review().json(); path=f"/api/projects/harbor/reviews/{r['id']}"
    assert 'FIXTURE' in r['content'] and r['mode']=='fixture'
    assert client.post(path+'/save',headers=headers,json={'request_key':'retry-1'}).status_code==409
    assert client.post(path+'/approve',headers=headers).status_code==200
    first=client.post(path+'/save',headers=headers,json={'request_key':'retry-1'})
    assert first.status_code==200
    assert client.post(path+'/save',headers=headers,json={'request_key':'retry-1'}).json()==first.json()
    assert client.post(path+'/save',headers=headers,json={'request_key':'different'}).status_code==409
    with core.connect() as db: assert db.execute('SELECT count(*) FROM reports').fetchone()[0]==1

def test_key_conflict_and_forged_review():
    a,b=review().json(),review().json()
    for r in (a,b): core.approve('alice','harbor',r['id'])
    core.save('alice','harbor',a['id'],'same')
    with pytest.raises(core.Problem,match='already used'): core.save('alice','harbor',b['id'],'same')
    with pytest.raises(core.Problem,match='not found'): core.save('alice','harbor','forged','x')

def test_concurrent_retries():
    r=review().json();core.approve('alice','harbor',r['id'])
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:core.save('alice','harbor',r['id'],'concurrent'),range(16)))
    assert len({r['id'] for r in results})==1
    with core.connect() as db: assert db.execute('SELECT count(*) FROM reports').fetchone()[0]==1

def test_missing_key_never_fakes_ai(monkeypatch):
    for mode,key in [('openai','OPENAI_API_KEY'),('anthropic','ANTHROPIC_API_KEY')]:
        monkeypatch.setenv('AI_PROVIDER',mode);monkeypatch.delenv(key,raising=False)
        assert review().status_code==503
    with core.connect() as db: assert db.execute('SELECT count(*) FROM reviews').fetchone()[0]==0

def test_mcp_tools_revalidate_identity(monkeypatch):
    import mcp_server
    monkeypatch.setenv('MCP_DEMO_TOKEN','alice-demo-token')
    assert mcp_server.list_authorized_projects()[0]['id']=='harbor'
    for call in [lambda:mcp_server.retrieve_project_documents('cedar'),lambda:asyncio.run(mcp_server.generate_scope_review('cedar')),lambda:mcp_server.save_approved_report('cedar','x','key')]:
        with pytest.raises(core.Problem,match='denied'): call()
    monkeypatch.setenv('MCP_DEMO_TOKEN','bad')
    with pytest.raises(core.Problem,match='Invalid'):mcp_server.list_authorized_projects()

def test_real_mcp_stdio_protocol(tmp_path):
    import os,sys,json
    from pathlib import Path
    from mcp import ClientSession,StdioServerParameters
    from mcp.client.stdio import stdio_client
    async def run():
        wire_database=core.DB if core.DB.startswith(('postgresql://','postgres://')) else str(tmp_path/'wire.sqlite3')
        env={**os.environ,'MCP_DEMO_TOKEN':'alice-demo-token','DATABASE_PATH':wire_database,'AI_PROVIDER':'fixture','DATABASE_URL':wire_database if wire_database.startswith(('postgresql://','postgres://')) else '', 'APP_ENV':'development'}
        params=StdioServerParameters(command=sys.executable,args=[str(Path(__file__).parent/'mcp_server.py')],env=env)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                assert {t.name for t in tools.tools}=={'list_authorized_projects','retrieve_project_documents','generate_scope_review','save_approved_report'}
                assert all('user_id' not in t.inputSchema.get('properties',{}) for t in tools.tools)
                result=await session.call_tool('list_authorized_projects',{})
                assert not result.isError and 'harbor' in result.content[0].text
                for name,args in [('retrieve_project_documents',{'project_id':'cedar'}),('generate_scope_review',{'project_id':'cedar'}),('save_approved_report',{'project_id':'cedar','review_id':'fake','request_key':'x'})]:
                    result=await session.call_tool(name,args)
                    assert result.isError and 'denied' in result.content[0].text
                result=await session.call_tool('generate_scope_review',{'project_id':'harbor'})
                assert not result.isError
                r=json.loads(result.content[0].text)
                result=await session.call_tool('save_approved_report',{'project_id':'harbor','review_id':r['id'],'request_key':'wire'})
                assert result.isError and 'approval' in result.content[0].text
                # Simulate the separate, authenticated human API writing approval to shared DB.
                old=core.DB
                try:
                    core.DB=wire_database;core.approve('alice','harbor',r['id'])
                finally: core.DB=old
                args={'project_id':'harbor','review_id':r['id'],'request_key':'wire'}
                first=await session.call_tool('save_approved_report',args)
                second=await session.call_tool('save_approved_report',args)
                assert not first.isError and first.content==second.content
    asyncio.run(run())

@pytest.mark.parametrize('provider',['openai','anthropic'])
def test_provider_adapter_and_failure(monkeypatch,provider):
    import httpx
    monkeypatch.setenv('AI_PROVIDER',provider)
    monkeypatch.setenv('OPENAI_API_KEY','test-only');monkeypatch.setenv('ANTHROPIC_API_KEY','test-only')
    real_client=httpx.AsyncClient
    requests=[]
    def handler(request):
        requests.append(request)
        assert 'harbor-scope' in request.content.decode()
        assert 'cedar' not in request.content.decode()
        if provider=='openai': return httpx.Response(200,json={'output':[{'content':[{'type':'output_text','text':'Mock provider review'}]}]})
        return httpx.Response(200,json={'content':[{'type':'text','text':'Mock provider review'}]})
    monkeypatch.setattr(core.httpx,'AsyncClient',lambda **kwargs:real_client(transport=httpx.MockTransport(handler),**kwargs))
    result=review()
    assert result.status_code==200 and result.json()['mode']==provider
    assert result.json()['content']=='Mock provider review' and len(requests)==1
    monkeypatch.setattr(core.httpx,'AsyncClient',lambda **kwargs:real_client(transport=httpx.MockTransport(lambda r:httpx.Response(429,json={'error':'rate limit'})),**kwargs))
    assert review().status_code==502
