import time 
import threading

class Circuitbreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self , failure_threshold = 5 , recovery_timeout = 30 , success_threshold=2):
        self.FAILURE_THRESHOLD = failure_threshold
        self.RECOVERY_TIMEOUT = recovery_timeout
        self.SUCCESS_THRESHOLD = success_threshold
        self.backends = {}
        self.lock = threading.Lock()

    def REGISTER_BACKEND(self , backend_id) : 
        if backend_id not in self.backends : 
            self.backends[backend_id] = {
                "state": self.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "opened_at": None,                
            }      

    def ALLOW_REQUEST(self , backend_id):
        with self.lock : 
            self.REGISTER_BACKEND(backend_id)
            state_info = self.backends[backend_id]
            if state_info["state"] == self.CLOSED:
                return True

            if state_info["state"] == self.OPEN : 
                elapsed = time.time() - state_info["opened_at"]
                if elapsed >= self.RECOVERY_TIMEOUT:
                    state_info["state"] = self.HALF_OPEN
                    state_info["success_count"] = 0
                    return True
                return False

            if state_info["state"] == self.HALF_OPEN:
                return True

            return False 

    def RECORD_SUCCESS(self, backend_id):
        with self.lock:
            self.REGISTER_BACKEND(backend_id)
            state_info = self.backends[backend_id]

            if state_info["state"] == self.HALF_OPEN:
                state_info["success_count"] += 1
                if state_info["success_count"] >= self.SUCCESS_THRESHOLD:
                    state_info["state"] = self.CLOSED
                    state_info["failure_count"] = 0
                    state_info["success_count"] = 0
                    state_info["opened_at"] = None
            else:
                state_info["failure_count"] = 0

    def RECORD_FAILURE(self, backend_id):
        with self.lock:
            self.REGISTER_BACKEND(backend_id)
            state_info = self.backends[backend_id]

            if state_info["state"] == self.HALF_OPEN:
                state_info["state"] = self.OPEN
                state_info["opened_at"] = time.time()
                state_info["success_count"] = 0
                return

            state_info["failure_count"] += 1
            if state_info["failure_count"] >= self.FAILURE_THRESHOLD:
                state_info["state"] = self.OPEN
                state_info["opened_at"] = time.time()

    def GET_STATE(self, backend_id):
        with self.lock:
            self.REGISTER_BACKEND(backend_id)
            return self.backends[backend_id]["state"]
