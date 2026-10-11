import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlsplit
import jwt

USERS={'alice','bob','carol'}

def code_hash(code): return hashlib.sha256(code.encode()).hexdigest()

def access_hashes():
    return json.loads(os.getenv('DEMO_ACCESS_HASHES_JSON','{}'))

def validate_configuration():
    if os.getenv('APP_ENV','development')!='production': return
    if not os.getenv('DATABASE_URL','').startswith(('postgresql://','postgres://')):
        raise RuntimeError('Production requires PostgreSQL DATABASE_URL')
    if len(os.getenv('SESSION_SECRET',''))<48:
        raise RuntimeError('Production requires a random SESSION_SECRET of at least 48 characters')
    hashes=access_hashes()
    if set(hashes)!=USERS or any(len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in hashes.values()) or len(set(hashes.values()))!=3:
        raise RuntimeError('Configure three distinct SHA256 access-code hashes')
    if any(v in {code_hash(''),code_hash(u+'-demo-token')} for u,v in hashes.items()):
        raise RuntimeError('Public development access codes forbidden')
    mcp=json.loads(os.getenv('MCP_ACCESS_HASHES_JSON','{}'))
    if set(mcp)-USERS or any(len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in mcp.values()) or set(mcp.values()) & set(hashes.values()):
        raise RuntimeError('MCP credentials must be distinct from human access codes')
    origins=os.getenv('FRONTEND_ORIGINS','').split(',')
    if not origins or any(not o.startswith('https://') or '*' in o or urlsplit(o).username or urlsplit(o).password or urlsplit(o).path or urlsplit(o).query or urlsplit(o).fragment or not urlsplit(o).hostname for o in origins):
        raise RuntimeError('Configure exact HTTPS frontend origins')
    if os.getenv('AI_PROVIDER')!='fixture':
        raise RuntimeError('Public demonstration is restricted to explicit fixture mode')

def session_secret():
    value=os.getenv('SESSION_SECRET','')
    if len(value)<48: raise ValueError('SESSION_SECRET not configured')
    return value

def login(code):
    from core import Problem
    hashed=code_hash(code)
    user=next((u for u,v in access_hashes().items() if u in USERS and hmac.compare_digest(v,hashed)),None)
    if not user: raise Problem(401,'Invalid demo access code')
    now=int(time.time())
    return {'token':jwt.encode({'sub':user,'aud':'construction-ui','iss':'construction-demo','iat':now,'exp':now+1800,'role':'human'},session_secret(),algorithm='HS256'),'user':user,'expires_in':1800}

def session_identity(token):
    from core import Problem
    try:
        claims=jwt.decode(token,session_secret(),algorithms=['HS256'],audience='construction-ui',issuer='construction-demo',options={'require':['sub','iat','exp','role']})
        if claims['sub'] not in USERS or claims['role']!='human': raise ValueError()
        return claims['sub']
    except (jwt.PyJWTError,ValueError): raise Problem(401,'Session invalid or expired')

def mcp_identity(token):
    from core import Problem
    digest=code_hash(token)
    hashes=json.loads(os.getenv('MCP_ACCESS_HASHES_JSON','{}'))
    user=next((u for u,v in hashes.items() if u in USERS and hmac.compare_digest(v,digest)),None)
    if not user: raise Problem(401,'Invalid MCP credential')
    return user
