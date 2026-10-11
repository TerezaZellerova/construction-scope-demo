"""Create private local configuration; never print access credentials."""
import hashlib
import json
import os
from pathlib import Path
import secrets

root=Path(__file__).resolve().parent.parent
private=root/'.demo-access.json'
env=root/'.env'
if private.exists() or env.exists():raise SystemExit('Refusing to overwrite existing configuration; rotate deliberately.')
codes={u:secrets.token_urlsafe(32) for u in ('alice','bob','carol')}
mcp={u:secrets.token_urlsafe(32) for u in codes}
hashes=lambda d:json.dumps({u:hashlib.sha256(c.encode()).hexdigest() for u,c in d.items()},separators=(',',':'))
content='\n'.join(['APP_ENV=development','AI_PROVIDER=fixture','SESSION_SECRET='+secrets.token_urlsafe(48),"DEMO_ACCESS_HASHES_JSON='"+hashes(codes)+"'","MCP_ACCESS_HASHES_JSON='"+hashes(mcp)+"'",'DATABASE_PATH=demo.sqlite3','FRONTEND_ORIGINS=http://127.0.0.1:5173'])+'\n'
for path,value in [(private,json.dumps({'human':codes,'mcp':mcp},indent=2)),(env,content)]:
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(descriptor,'w') as f:f.write(value)
print('Private .env and .demo-access.json created. Distribute human codes privately; keep MCP codes in the trusted host.')
