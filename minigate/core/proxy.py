import aiohttp 
from aiohttp import web 

HOP_BY_HOP_HEAD = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

def FILTER_HEADERS(head):
    filterd = {}
    head_items = list(head.items())
    for i in range(len(head_items)):
        key, val = head_items[i]
        if key.lower() not in HOP_BY_HOP_HEAD:
            filterd[key] = val
    return filterd

async def PROXY_REQ(req: web.Request, backend_url: str) -> web.Response:
    target_url = f"{backend_url}{req.path_qs}"

    body = await req.read()
    FORWARD_HEAD = FILTER_HEADERS(req.headers)

    session = req.app["client_session"]

    async with session.request(
        method=req.method,
        url=target_url,
        headers=FORWARD_HEAD,
        data=body if body else None,
    ) as backend_response:
        response_body = await backend_response.read()
        response_headers = FILTER_HEADERS(backend_response.headers)

        return web.Response(
            body=response_body,
            status=backend_response.status,
            headers=response_headers,
        )