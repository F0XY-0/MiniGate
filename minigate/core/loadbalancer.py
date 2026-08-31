from .circuit_breaker import Circuitbreaker

class Loadbalancer : 
    def __init__(self , conf : dict , circuit_breaker = None ):
        backend_conf = conf.get("backend" , {})
        self.URLS = backend_conf.get("urls" , [])

        if not self.URLS : 
            raise ValueError("no backend urls configured under backend.urls")

        self.INDEX = 0
        self.circuit_breaker = circuit_breaker

    def NEXT_BACKEND(self) -> str : 
        attemps = 0 
        total = len(self.URLS)

        while attemps < total : 
            url = self.URLS[self.INDEX]
            self.INDEX = ( self.INDEX + 1 ) % total
            attemps += 1 

            if self.circuit_breaker is None or self.circuit_breaker.ALLOW_REQUEST(url):
                return url

        return None