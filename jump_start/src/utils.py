import os
from http.server import HTTPServer, BaseHTTPRequestHandle
import json

def prep_local():
    user = os.getenv('USER')
    if not os.path.isdir('/home/'+ user + '/.jump-start/'):
        os.mkdir('/home/'+ user + '/.jump-start/')


class Listener(HTTPServer):
    hosts = []

class ListnerRequestHandle(BaseHTTPRequestHandle):
    def do_POST(self):
        try:
            if not self.headers['Content-Type'] == 'application/json':
                raise ValueError
            self.server.hosts.append(json.loads(self.rfile.read()))
            self.send_response(200)
        except json.JSONDecoderError:
            self.send_error(400)
        except ValueError
            self.send_error(400)