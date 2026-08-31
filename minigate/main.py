import os
import yaml
import aiohttp
from aiohttp import web

from minigate.core.proxy import PROXY_REQ
from minigate.core.auth import APIKeyValidator, BUILD_AUTH_ERROR
from minigate.core.jwt_auth import JwtHandler
from minigate.core.middleware import JWTAuthMiddleware, RateLimitMiddleware
from minigate.core.loadbalancer import Loadbalancer
from minigate.core.circuit_breaker import Circuitbreaker


CONF_PATH = os.path.join(os.path.dirname(__file__) , ".." , "config" , "config.yaml")

def LOAD_CONF( path : str ) -> dict :

    if not os.path.exists(path):
        raise FileNotFoundError(
            f'config fiel not found at {path}'
            f'copy config/config.example.yaml to config/config.yaml and edit it .'
        )

    with open(path , 'r') as f :
        return yaml.safe_load(f)

async def CLIENT_SESSION_CTX(app: web.Application):
    session = aiohttp.ClientSession()
    app["client_session"] = session

    yield

    await session.close()

def CREATE_APP(conf : dict) -> web.Application:
    circuit_breaker = Circuitbreaker(failure_threshold=5, recovery_timeout=30, success_threshold=2)
    load_balancer = Loadbalancer(conf, circuit_breaker=circuit_breaker)

    async def HANDEL_ALL(req : web.Request) -> web.Response :
        backend_url = load_balancer.NEXT_BACKEND()

        if backend_url is None : 
            return web.json_response({"error" : "all backends are unavailable"} , status=503 )

        print(f"[gateway] routing {req.method} {req.path} -> {backend_url}")

        try:
            response = await PROXY_REQ( req , backend_url )
            circuit_breaker.RECORD_SUCCESS(backend_url)
            return response
        except aiohttp.ClientError:
            circuit_breaker.RECORD_FAILURE(backend_url)
            return web.json_response({"error": "backend request failed"}, status=502)


    api_key_validator = APIKeyValidator(conf)
    jwt_handler = JwtHandler(conf)

    async def HANDLE_TOKEN(req: web.Request) -> web.Response:
        key = req.headers.get(api_key_validator.HEADER_NAME)
        client = api_key_validator.VALIDATE_KEY(key)

        if client is None:
            return BUILD_AUTH_ERROR("Invalid or missing API key", 401)

        token = jwt_handler.GENERATE_TOKENS(client)
        return web.json_response({"token": token})

    jwt_mw = JWTAuthMiddleware(conf)
    rate_limit_mw = RateLimitMiddleware(cap=10, ref_rate=1)

    app = web.Application(middlewares=[jwt_mw.handle, rate_limit_mw.handle])
    app.cleanup_ctx.append(CLIENT_SESSION_CTX)
    app.router.add_route("POST", "/token", HANDLE_TOKEN)
    app.router.add_route("*", "/{tail:.*}" , HANDEL_ALL)

    return app

def main():

    conf = LOAD_CONF(CONF_PATH)
    app = CREATE_APP(conf)

    gateWay_port = conf["gateway"]["port"]

    print(f"MiniGate listening on http://127.0.0.1:{gateWay_port}")
    print(f"Forwarding to backend: {conf['backend']['urls']}")

    web.run_app(app , host="127.0.0.1" , port=gateWay_port)

if __name__ == "__main__" :
    main()