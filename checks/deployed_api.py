"""Authenticated smoke test for synthetic deployed data. No credentials printed."""
import os
import uuid
import httpx

base=os.environ['LIVE_API_URL'].rstrip('/')
if not base.startswith('https://'):raise SystemExit('Deployed checks require HTTPS')
with httpx.Client(base_url=base,timeout=60) as client:
    health=client.get('/health');health.raise_for_status()
    assert health.json()['mode']=='fixture' and health.json()['data']=='synthetic'
    assert client.get('/api/projects').status_code==401
    session=client.post('/api/session',json={'access_code':os.environ['LIVE_ALICE_ACCESS_CODE']})
    session.raise_for_status();client.headers['Authorization']='Bearer '+session.json()['token']
    listing=client.get('/api/projects');listing.raise_for_status()
    assert [p['id'] for p in listing.json()]==['harbor']
    for path in ['/api/projects/cedar/documents','/api/projects/quarry/documents']:
        assert client.get(path).status_code==403
    docs=client.get('/api/projects/harbor/documents');docs.raise_for_status();assert len(docs.json())==2
    result=client.post('/api/projects/harbor/reviews');result.raise_for_status();review=result.json()
    assert review['mode']=='fixture' and 'FIXTURE' in review['content']
    path='/api/projects/harbor/reviews/'+review['id'];body={'request_key':str(uuid.uuid4())}
    assert client.post(path+'/save',json=body).status_code==409
    approval=client.post(path+'/approve');approval.raise_for_status()
    saved=client.post(path+'/save',json=body);saved.raise_for_status()
    retry=client.post(path+'/save',json=body);retry.raise_for_status()
    assert retry.json()==saved.json()
    assert client.post(path+'/save',json={'request_key':str(uuid.uuid4())}).status_code==409
    assert client.get('/docs').status_code==404
    assert client.get('/api/projects').headers['Cache-Control']=='no-store'
print('Deployed authenticated API smoke passed: fixture, authorization, approval, save and retry')
