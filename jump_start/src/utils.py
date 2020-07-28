import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import colorama
import json


#def run_ansible


def prep_local():
    user = os.getenv('USER')
    if not os.path.isdir('/home/' + user + '/.jump-start/'):
        os.mkdir('/home/' + user + '/.jump-start/')
    if not os.path.isdir('/home/' + user + '/.jump-start/' + 'web/'):
        os.mkdir('/home/' + user + '/.jump-start/' + 'web/')
    if not os.path.isdir('/home/' + user + '/.jump-start/' + 'web/cache/'):
        os.mkdir('/home/' + user + '/.jump-start/' + 'web/cache/')


class Listener(HTTPServer):
    hosts = []
    output = None


class ListenerRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            self.server.output.debug('Recieved data from {0}'.format(self.client_address))
            if not self.headers['Content-Type'] == 'application/json':
                raise ValueError
            data = self.rfile.read()
            self.server.hosts.append(json.loads(data))
            self.send_response(200)
            self.server.output.print('Recieved callback from {0}'.format(data['hostname']))
        except json.JSONDecoderError:
            self.send_error(400)
        except ValueError:
            self.send_error(400)


class Output():

    def __init__(self, logger):
        self.logger = logger

    def error(self, msg):
        print(colorama.Fore.RED+'==> ', msg, '\n==> exiting...',file=sys.stderr)
        print(colorama.Style.RESET_ALL)
        sys.exit(1)

    def print(self, msg):
        print(colorama.Fore.GREEN+'==> ', msg, file=sys.stderr)
        print(colorama.Style.RESET_ALL)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)
