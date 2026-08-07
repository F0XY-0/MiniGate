import os 
import yaml 
from aiohttp import web 

from minigate.core.proxy import proxy_req 
CONF_PATH = os.path.join(os.path.dirname(__file__) , ".." , "config" , "config.yaml")

def LOAD_CONF( path : str ) -> dict : 
    if not os.path.exists(path):
        raise FileNotFoundError(
            f'config fiel not found at {path}'
            f'copy config/config.example.yaml to config/config.yaml and edit it .' 
        )
    with open(path , 'r') as f :
        return yaml.safe_load(f)

def CREATE_APP(conf : dict) -> web.Application:
    BACKEND_URL = conf["backend"]["url"] 
    """
    [backend] > should return > {"url": "http://127.0.0.1:9001"}
    [url] > should look in the key 'url' inside  > return > str "http://127.0.0.1:9001"
    """

    async def HANDEL_ALL(req : web.Request) -> web.Response : 
        return await proxy_req( req , BACKEND_URL )

    app = web.Application()
    app.router.add_route("*", "/{tail:.*}" , HANDEL_ALL)
    return app 

def main():
    conf = LOAD_CONF(CONF_PATH)
    app = CREATE_APP(conf)
    gateWay_port = conf["gateway"]["port"]
    print(f"MiniGate listening on http://127.0.0.1:{gateWay_port}")
    print(f"Forwarding to backend: {conf['backend']['url']}")

    web.run_app(app , host="127.0.0.1" , port=gateWay_port)

if __name__ == "__main__" :
    main()