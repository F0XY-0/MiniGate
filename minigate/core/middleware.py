from aiohttp import web

from minigate.core.rate_limiter import RateLimiter

rate_limiter = RateLimiter(cap=10, ref_rate=1)


@web.middleware
async def RATE_LIMIT_MIDDLEWARE(req: web.Request, handler):
    client_ip = req.remote

    if not rate_limiter.check(client_ip):
        return web.json_response(
            {"error": "rate limit exceeded"},
            status=429,
        )

    return await handler(req)