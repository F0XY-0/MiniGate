import argparse
import json
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

"""
fake/stub HTTP backend for testing MiniGate against — it listens on a 
port (default 9001) and responds to any GET/POST/PUT/DELETE with a JSON body
"""

class DummyHead(BaseHTTPRequestHandler):
    port = 9001

    def _log_line(self , method : str ) : 
        timetamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        clinetip , clinet_port = self.client_address 
        print(
            f"{timetamp} [backend :{self.port}]" 
            f"{clinetip}:{clinet_port} -> {method} {self.path}"
        )

    def _handler(self, method):
        body = {
            "backend_port": self.port,
            "method": method,
            "path": self.path,
            "timeStamp": time.time()
        }

        content_len = int(self.headers.get('Content-Length', 0))
        if content_len > 0:
            raw_body = self.rfile.read(content_len)
            try:
                body['received_body'] = json.loads(raw_body)
            except json.JSONDecodeError:
                body["received_body"] = raw_body.decode("utf-8", errors="replace")

        response_bytes = json.dumps(body).encode("UTF-8")

        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.send_header('content-length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_GET(self):
        self._handler('GET')

    def do_POST(self):
        self._handler('POST')

    def do_PUT(self):
        self._handler('PUT')

    def do_DELETE(self):
        self._handler('DELETE')

    def log_message(self, format_str, *args):
        pass # changed do the cli new message 

def main():
    parser = argparse.ArgumentParser(description="dummy backend for the mini gate")
    parser.add_argument("--port", type=int, default=9001, help="port to listen on")
    args = parser.parse_args()

    DummyHead.port = args.port
    server = ThreadingHTTPServer(('127.0.0.1', args.port), DummyHead)
    
    print(f"Dummy backend running on http://127.0.0.1:{args.port}")

    try:
        server.serve_forever()
    except:
        print('\nShutting down the dummy server')
        server.shutdown()

if __name__ == "__main__":
    main()