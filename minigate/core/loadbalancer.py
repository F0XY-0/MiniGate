class Loadbalancer : 
    def __init__(self , conf : dict ):
        backend_conf = conf.get("backend" , {})
        self.URLS = backend_conf.get("urls" , [])

        if not self.URLS : 
            raise ValueError("no backend urls configured under backend.urls")
        self.INDEX = 0

    def NEXT_BACKEND(self) -> str : 
        url = self.URLS[self.INDEX]
        self.INDEX = (self.INDEX + 1 ) % len(self.URLS)
        return url