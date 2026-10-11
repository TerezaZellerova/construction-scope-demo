import json
import os
import secrets
import time
import jwt
import pytest
import security
import core
from app import app
from fastapi.testclient import TestClient
# Share the isolation fixture with the full service suite.
from test_app import database

client=TestClient(app)

def auth(): return {'Authorization':'Bearer '+security.login('alice-test-code')['token']}

def test_login_and_no_public_tokens():
    assert client.post('/api/session',json={'access_code':'invalid'}).status_code==401
    r=client.post('/api/session',json={'access_code':'alice-test-code'})
    assert r.status_code==200 and r.json()['user']=='alice'
    assert client.get('/api/projects',headers={'Authorization':'Bearer alice-demo-token'}).status_code==401
    assert client.post('/api/session',json={'access_code':'alice-test-code','user':'bob'}).status_code==422

def test_expiry_and_tampering():
    token=security.login('alice-test-code')['token']
    with pytest.raises(core.Problem):security.session_identity(token+'tamper')
    claims={'sub':'alice','aud':'construction-ui','iss':'construction-demo','iat':int(time.time())-60,'exp':int(time.time())-1,'role':'human'}
    with pytest.raises(core.Problem):security.session_identity(jwt.encode(claims,security.session_secret(),algorithm='HS256'))

def test_separate_mcp_credentials_cannot_approve():
    assert client.post('/api/session',json={'access_code':'alice-demo-token'}).status_code==401
    assert client.post('/api/projects/harbor/reviews/fake/approve',headers={'Authorization':'Bearer alice-demo-token'}).status_code==401
    with pytest.raises(core.Problem):security.mcp_identity(security.login('alice-test-code')['token'])

def test_persistent_rate_limit():
    for _ in range(3):core.rate_limit('test','test',3,3600)
    with pytest.raises(core.Problem) as e:core.rate_limit('test','test',3,3600)
    assert e.value.status==429
    # Independent connections use the same bucket; no in-memory/reset-per-worker limiter.
    with core.connect() as db:assert db.execute("SELECT hits FROM rate_limits WHERE subject='test'").fetchone()[0]==3

def test_login_rate_limit():
    for _ in range(20):assert client.post('/api/session',json={'access_code':'bad'}).status_code==401
    r=client.post('/api/session',json={'access_code':'bad'})
    assert r.status_code==429 and r.headers['Retry-After']=='60'

def test_generation_quota_and_rate_limit():
    core.rate_limit('alice','generation',1,3600)
    for _ in range(9):core.rate_limit('alice','generation',10,3600)
    assert client.post('/api/projects/harbor/reviews',headers=auth()).status_code==429

def test_origin_body_and_security_headers():
    assert client.post('/api/session',headers={'Origin':'https://evil.example'},json={'access_code':'x'}).status_code==403
    assert client.post('/api/session',content='x'*4097).status_code==413
    r=client.get('/api/projects',headers=auth())
    assert r.headers['Cache-Control']=='no-store'
    assert r.headers['X-Content-Type-Options']=='nosniff'
    r=client.options('/api/projects',headers={'Origin':'https://evil.example','Access-Control-Request-Method':'GET'})
    assert 'access-control-allow-origin' not in r.headers

def test_production_fails_closed(monkeypatch):
    monkeypatch.setenv('APP_ENV','production')
    monkeypatch.setenv('DATABASE_URL','sqlite:///unsafe')
    with pytest.raises(RuntimeError):security.validate_configuration()
    monkeypatch.setenv('DATABASE_URL','postgresql://localhost/demo')
    monkeypatch.setenv('SESSION_SECRET','short')
    with pytest.raises(RuntimeError):security.validate_configuration()
    monkeypatch.setenv('SESSION_SECRET',secrets.token_urlsafe(48))
    monkeypatch.setenv('DEMO_ACCESS_HASHES_JSON',json.dumps({u:security.code_hash(secrets.token_urlsafe(32)) for u in security.USERS}))
    monkeypatch.setenv('FRONTEND_ORIGINS','https://demo.vercel.app')
    security.validate_configuration()
    monkeypatch.setenv('AI_PROVIDER','openai')
    with pytest.raises(RuntimeError):security.validate_configuration()
    monkeypatch.setenv('AI_PROVIDER','fixture');monkeypatch.setenv('FRONTEND_ORIGINS','*')
    with pytest.raises(RuntimeError):security.validate_configuration()

def test_body_limit_without_content_length():
    from body_limit import BodyLimitMiddleware
    import asyncio
    async def run():
        called=False;sent=[]
        async def downstream(scope,receive,send):
            nonlocal called
            called=True
        chunks=iter([{'type':'http.request','body':b'x'*3000,'more_body':True},{'type':'http.request','body':b'x'*2000,'more_body':False}])
        async def receive():return next(chunks)
        async def send(message):sent.append(message)
        await BodyLimitMiddleware(downstream)({'type':'http','method':'POST','path':'/api/session'},receive,send)
        assert not called and sent[0]['status']==413
    asyncio.run(run())

def test_storage_quota_blocks_new_review():
    with core.connect() as db:
        for i in range(100):db.execute('INSERT INTO reviews(id,project_id,user_id,content,mode) VALUES (?,?,?,?,?)',(f'quota-{i}','harbor','alice','Synthetic fixture','fixture'))
    assert client.post('/api/projects/harbor/reviews',headers=auth()).status_code==429
    with core.connect() as db:assert db.execute('SELECT count(*) FROM reviews').fetchone()[0]==100

def test_membership_revocation_applies_to_existing_review():
    import asyncio
    r=asyncio.run(core.generate('alice','harbor'))
    core.approve('alice','harbor',r['id'])
    with core.connect() as db:db.execute('DELETE FROM members WHERE user_id=? AND project_id=?',('alice','harbor'))
    for operation in [lambda:core.documents('alice','harbor'),lambda:core.approve('alice','harbor',r['id']),lambda:core.save('alice','harbor',r['id'],'revoked')]:
        with pytest.raises(core.Problem) as e:operation()
        assert e.value.status==403
