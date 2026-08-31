import subprocess
import sys
import time
import urllib.request
import urllib.error
import json

"""
this will be testing ground to see everything works as inteaded 
(note before the test u shouldve have 3 terminal open at the same time)
Starts 3 dummy backends + the gateway as background processes,
runs test requests through the full auth/rate-limit/load-balance chain,
then shuts everything down.
"""
GATEWAY_URL = "http://127.0.0.1:8080"
API_KEY = "dev-key-12345"
TOTAL_REQUESTS = 40 
KILL_BACKEND_AFTER = 5   
KILL_PORT = 9002

class ProcessManager:

    def __init__(self):
        self.procs = {}

    def START_ALL(self):
        for port in [9001, 9002, 9003]:
            p = subprocess.Popen(
                [sys.executable, "backends/dummy_backend.py", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.procs["backend-" + str(port)] = p

        gateway = subprocess.Popen(
            [sys.executable, "-m", "minigate.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.procs["gateway"] = gateway

    def KILL_BACKEND(self, port: int):
        name = "backend-" + str(port)
        if name in self.procs:
            print(f"\n>>> Killing {name} to simulate a failure <<<\n")
            self.procs[name].terminate()
            self.procs[name].wait()
            del self.procs[name]

    def SHUTDOWN_ALL(self):
        print("\nShutting down remaining processes...")

        names = list(self.procs.keys())
        for i in range(len(names)):
            self.procs[names[i]].terminate()

        for i in range(len(names)):
            self.procs[names[i]].wait()


class GatewayClient:

    def __init__(self, base_url: str, api_key: str):
        self.BASE_URL = base_url
        self.API_KEY = api_key
        self.TOKEN = None

    def FETCH_TOKEN(self):
        req = urllib.request.Request(
            f"{self.BASE_URL}/token",
            method="POST",
            headers={"X-API-Key": self.API_KEY},
        )
        with urllib.request.urlopen(req) as response:
            body = json.loads(response.read())
            self.TOKEN = body["token"]

    def SEND_REQUEST(self):
        req = urllib.request.Request(
            f"{self.BASE_URL}/anything",
            headers={"Authorization": f"Bearer {self.TOKEN}"},
        )
        try:
            response = urllib.request.urlopen(req, timeout=3)
            body = json.loads(response.read())
            return response.status, body.get("backend_port")
        except urllib.error.HTTPError as e:
            return e.code, None
        except (urllib.error.URLError, TimeoutError):
            return None, None  # gateway itself unreachable, shouldn't normally happen


class TestRunner:

    def __init__(self, client: GatewayClient, manager: ProcessManager, total_requests: int):
        self.client = client
        self.manager = manager
        self.TOTAL_REQUESTS = total_requests
        self.results = []
        self.ports_hit = {}

    def RUN(self):
        print("Waiting for processes to boot...")
        time.sleep(2)

        print("Requesting JWT via /token...")
        self.client.FETCH_TOKEN()
        print(f"Got token: {self.client.TOKEN[:30]}...\n")

        for i in range(self.TOTAL_REQUESTS):

            if i == KILL_BACKEND_AFTER:
                self.manager.KILL_BACKEND(KILL_PORT)
                time.sleep(1)  # give things a moment to settle

            status, backend_port = self.client.SEND_REQUEST()
            self.results.append(status)
            print(f"request {i + 1}: {status} (backend: {backend_port})")

            if status == 200:
                self.ports_hit[backend_port] = self.ports_hit.get(backend_port, 0) + 1

            time.sleep(1.2)  # spread requests out so rate limiting doesn't dominate the run

    def PRINT_SUMMARY(self):
        allowed = 0
        blocked = 0
        errors = 0
        unavailable = 0

        for i in range(len(self.results)):
            status = self.results[i]
            if status == 200:
                allowed += 1
            elif status == 429:
                blocked += 1
            elif status == 502:
                errors += 1
            elif status == 503:
                unavailable += 1

        print()
        print(f"allowed (200): {allowed}")
        print(f"rate-limited (429): {blocked}")
        print(f"backend errors (502): {errors}")
        print(f"all-backends-down (503): {unavailable}")
        print(f"load distribution (successful requests): {self.ports_hit}")
        print(f"\nNote: {KILL_PORT} was killed after request {KILL_BACKEND_AFTER}.")
        print(f"Watch above for requests routed to it failing (502), then it")
        print(f"disappearing from routing once its circuit breaker trips OPEN.")


def main():
    manager = ProcessManager()
    manager.START_ALL()

    try:
        client = GatewayClient(GATEWAY_URL, API_KEY)
        runner = TestRunner(client, manager, TOTAL_REQUESTS)
        runner.RUN()
        runner.PRINT_SUMMARY()
    finally:
        manager.SHUTDOWN_ALL()


if __name__ == "__main__":
    main()