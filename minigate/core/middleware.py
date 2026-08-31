from aiohttp import web
from minigate.core.rate_limiter import RateLimiter
from minigate.core.auth import APIKeyValidator, BUILD_AUTH_ERROR 
from minigate.core.jwt_auth import JwtHandler 

class AuthMiddleware:

    def __init__(self, conf: dict):
        self.validator = APIKeyValidator(conf)

    @web.middleware
    async def handle(self, req: web.Request, handler):

        if not self.validator.ENABLED:
            req["client_name"] = req.remote
            return await handler(req)

        key = req.headers.get(self.validator.HEADER_NAME)
        client = self.validator.VALIDATE_KEY(key)

        if client is None:
            return BUILD_AUTH_ERROR("Invalid or missing API key", 401)

        req["client_name"] = client
        return await handler(req)

class JWTAuthMiddleware:

    def __init__(self, conf: dict):
        self.jwt_handler = JwtHandler(conf)

    @web.middleware
    async def handle(self, req: web.Request, handler):

        if req.path == "/token":
            return await handler(req)

        auth_header = req.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return self.jwt_handler.BUILD_JWT_ERROR("Missing or invalid Authorization header", 401)

        token = auth_header[len("Bearer "):]
        client = self.jwt_handler.VERIFY_TOKEN(token)
        
        if client is None:
            return self.jwt_handler.BUILD_JWT_ERROR("Invalid or expired token", 401)

        req["client_name"] = client
        return await handler(req)        

class RateLimitMiddleware:

    def __init__(self, cap: int = 10, ref_rate: int = 1):
        self.limiter = RateLimiter(cap=cap, ref_rate=ref_rate)

    @web.middleware
    async def handle(self, req: web.Request, handler):

        client_key = req.get("client_name", req.remote)

        if not self.limiter.check(client_key):
            return web.json_response(
                {"error": "rate limit exceeded"},
                status=429,
            )
        return await handler(req)