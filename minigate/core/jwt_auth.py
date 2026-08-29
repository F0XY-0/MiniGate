import jwt 
import time 
from aiohttp import web 
# encode > generates | # decode > verify 
class JwtHandler : 
    def __init__(self , conf : dict ):
        jwt_conf = conf.get('jwt' , {})
        self.SECRET = jwt_conf.get("secret" , "change_Me")
        self.ALGORITHM = jwt_conf.get("algorithm" , "HS256")
        self.EXPIRY_SECONDS = jwt_conf.get("expiry_seconds" , 3600)

    def GENERATE_TOKENS(self , client_name : str ) -> str : 

        payload = {
            'client' : client_name , 
            'iat' : int(time.time()) ,
            'exp' : int(time.time() + self.EXPIRY_SECONDS) ,
        }
        return jwt.encode( payload , self.SECRET , algorithm = self.ALGORITHM )

    def VERIFY_TOKEN(self , token : str ) -> str | None : 
        try : 
            payload = jwt.decode(token , self.SECRET , algorithms = [self.ALGORITHM] ) 
            return payload.get('client')
        except jwt.ExpiredSignatureError : 
            return None
        except jwt.InvalidTokenError :
            return None

    def BUILD_JWT_ERROR(self, message : str , status : int ) -> web.Response : 
        return web.json_response(
            { "error" : message } , 
            status = status 
        )

