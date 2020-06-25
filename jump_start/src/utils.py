import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandle
import coloroma
import json


def prep_local():
    user = os.getenv('USER')
    if not os.path.isdir('/home/' + user + '/.jump-start/'):
        os.mkdir('/home/' + user + '/.jump-start/')


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
        except ValueError:
            self.send_error(400)


class Output():

    def __init__(self, logger):
        self.logger = logger

    def error(self, msg):
        print(coloroma.Fore.RED, '==> ', msg, file=sys.stderr)
        print(coloroma.Style.RESET_ALL)
        sys.exit(1)

    def print(self, msg):
        print(coloroma.Fore.GREEN, '==> ', msg, file=sys.stderr)
        print(coloroma.Style.RESET_ALL)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)
