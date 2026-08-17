import time 

class TokenBucket : 
    def __init__(self , cap , ref):
        self.cap = cap 
        self.ref = ref 
        self.token = cap 
        self.last_ref = time.monotonic()

    def _refill(self) :
        now = time.monotonic()
        elapsed = now - self.last_ref

        new_token = elapsed * self.ref 
        self.token = min(self.cap , self.token + new_token)
        self.last_ref = now 

    def allow_req(self) : 
        self._refill()

        if self.token >= 1 : 
            self.token -= 1 
            return True 
        return False

# Holds one TokenBucket per client key (e.g. IP address).
class RateLimitor:
    def __init__(self , cap = 10 , ref_rate = 1):
        self.cap = cap 
        self.ref_rate = ref_rate
        self.buckets = {}

    def _get_bucket(self, clinet_key):
        if clinet_key not in self.buckets :
            self.buckets[clinet_key] = TokenBucket(self.cap , self.ref_rate) 
        return self.buckets[clinet_key]

    def check(self , clinet_key) : 
        bucket = self._get_bucket(clinet_key)
        return bucket.allow_req()