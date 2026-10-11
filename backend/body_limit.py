from starlette.responses import JSONResponse

class BodyLimitMiddleware:
    """Bound streamed request bodies before FastAPI's JSON/form parsers run."""
    def __init__(self,app,limit=4096):self.app,self.limit=app,limit
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            chunk=message.get('body',b'')
            if len(body)+len(chunk)>self.limit:
                return await JSONResponse(status_code=413,content={'detail':'Request too large'})(scope,receive,send)
            body.extend(chunk)
            if not message.get('more_body',False):break
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)
