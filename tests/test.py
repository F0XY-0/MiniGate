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
TOTAL_REQUESTS = 15


class ProcessManager:

    def __init__(self):
        self.procs = []

    def START_ALL(self):
        for port in [9001, 9002, 9003]:
            p = subprocess.Popen(
                [sys.executable, "backends/dummy_backend.py", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.procs.append(("backend-" + str(port), p))

        gateway = subprocess.Popen(
            [sys.executable, "-m", "minigate.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.procs.append(("gateway", gateway))

    def SHUTDOWN_ALL(self):
        print("\nShutting down all processes...")

        for i in range(len(self.procs)):
            name, p = self.procs[i]
            p.terminate()

        for i in range(len(self.procs)):
            name, p = self.procs[i]
            p.wait()


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
            response = urllib.request.urlopen(req)
            body = json.loads(response.read())
            return response.status, body.get("backend_port")
        except urllib.error.HTTPError as e:
            return e.code, None


class TestRunner:

    def __init__(self, client: GatewayClient, total_requests: int):
        self.client = client
        self.TOTAL_REQUESTS = total_requests
        self.allowed = 0
        self.blocked = 0
        self.ports_hit = {}

    def RUN(self):
        print("Waiting for processes to boot...")
        time.sleep(2)

        print("Requesting JWT via /token...")
        self.client.FETCH_TOKEN()
        print(f"Got token: {self.client.TOKEN[:30]}...")

        print(f"\nSending {self.TOTAL_REQUESTS} requests through the gateway...\n")

        for i in range(self.TOTAL_REQUESTS):
            status, backend_port = self.client.SEND_REQUEST()
            print(f"request {i + 1}: {status} (backend: {backend_port})")

            if status == 200:
                self.allowed += 1
                self.ports_hit[backend_port] = self.ports_hit.get(backend_port, 0) + 1
            elif status == 429:
                self.blocked += 1

    def PRINT_SUMMARY(self):
        print()
        print(f"allowed (200): {self.allowed}")
        print(f"blocked (429): {self.blocked}")
        print(f"load distribution: {self.ports_hit}")


def main():
    manager = ProcessManager()
    manager.START_ALL()

    try:
        client = GatewayClient(GATEWAY_URL, API_KEY)
        runner = TestRunner(client, TOTAL_REQUESTS)
        runner.RUN()
        runner.PRINT_SUMMARY()
    finally:
        manager.SHUTDOWN_ALL()


if __name__ == "__main__":
    main()