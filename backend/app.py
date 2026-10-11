import os
from fastapi import FastAPI, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
import core
import security
from body_limit import BodyLimitMiddleware

security.validate_configuration()
core.initialize()
production=os.getenv('APP_ENV')=='production'
app = FastAPI(title='Synthetic Construction Scope Assistant',docs_url=None if production else '/docs',redoc_url=None,openapi_url=None if production else '/openapi.json')
origins=os.getenv('FRONTEND_ORIGINS','http://127.0.0.1:5173').split(',')
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type'],allow_credentials=False)
app.add_middleware(BodyLimitMiddleware)

@app.middleware('http')
async def safeguards(request: Request,call_next):
    try: size=int(request.headers.get('content-length','0') or 0)
    except ValueError: return JSONResponse(status_code=400,content={'detail':'Invalid content length'})
    if size>4096:
        return JSONResponse(status_code=413,content={'detail':'Request too large'})
    if request.method=='POST':
        origin=request.headers.get('origin')
        if origin and origin not in origins:
            return JSONResponse(status_code=403,content={'detail':'Origin denied'})
    try:
        if request.url.path.startswith('/api/'):
            # Global request cap cannot be bypassed by spoofing proxy headers.
            core.rate_limit('global','http',300,60)
        response=await call_next(request)
    except core.Problem as exc:
        response=JSONResponse(status_code=exc.status,content={'detail':exc.message})
    if production: response.headers['Strict-Transport-Security']='max-age=31536000'
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'"
    response.headers['Referrer-Policy']='no-referrer'
    if response.status_code==429: response.headers['Retry-After']='60'
    return response

@app.exception_handler(core.Problem)
async def problem_handler(request, exc):
    return JSONResponse(status_code=exc.status, content={'detail':exc.message})

@app.exception_handler(Exception)
async def internal_error(request,exc):
    return JSONResponse(status_code=503,content={'detail':'Service temporarily unavailable'})

def identity(authorization: str = Header(default='')):
    if not authorization.startswith('Bearer '): raise core.Problem(401,'Bearer session required')
    return security.session_identity(authorization[7:])

class LoginInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    access_code: str = Field(min_length=1,max_length=256)
class SaveInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_key: str = Field(min_length=1,max_length=128)

@app.get('/health')
def health():
    with core.connect() as db: db.execute('SELECT 1')
    return {'status':'ok','mode':os.getenv('AI_PROVIDER','fixture'),'data':'synthetic','integration':'standalone demonstration; no InQI integration'}
@app.post('/api/session')
def login(body: LoginInput):
    core.rate_limit('global','login',20,60)
    return security.login(body.access_code)
@app.get('/api/projects')
def projects(user=Depends(identity)): return core.list_projects(user)
@app.get('/api/projects/{project}/documents')
def documents(project: str,user=Depends(identity)): return core.documents(user,project)
@app.post('/api/projects/{project}/reviews')
async def generate(project: str,user=Depends(identity)): return await core.generate(user,project)
@app.post('/api/projects/{project}/reviews/{rid}/approve')
def approve(project: str,rid: str,user=Depends(identity)): return core.approve(user,project,rid)
@app.post('/api/projects/{project}/reviews/{rid}/save')
def save(project: str,rid: str,body: SaveInput,user=Depends(identity)): return core.save(user,project,rid,body.request_key)
