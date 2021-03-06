import os
import re
import shutil
import json
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer  # , ThreadingHTTPServer
from socketserver import ThreadingMixIn

log = logging.getLogger(__name__)

www = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../www')


# exists only in python 3.7
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True

    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)


class RESTRequestHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.handle_method('HEAD')

    def do_GET(self):
        self.handle_method('GET')

    def do_POST(self):
        self.handle_method('POST')

    def do_PUT(self):
        self.handle_method('PUT')

    def do_DELETE(self):
        self.handle_method('DELETE')

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        BaseHTTPRequestHandler.end_headers(self)

    def get_payload(self):
        payload_len = int(self.headers.get('content-length', 0))
        payload = self.rfile.read(payload_len)
        if type(payload) is str:
            payload = json.loads(payload)
        elif type(payload) is bytes:
            payload = json.loads(payload.decode("utf-8"))
        return payload

    def handle_file(self, method, route):
        if method == 'GET':
            try:
                log.debug('xhandle file: {0}'.format(self.get_file_path(route)))
                f = open(self.get_file_path(route), "rb")
                try:
                    self.send_response(200)
                    if 'media_type' in route:
                        self.send_header('Content-type', route['media_type'])
                    self.end_headers()
                    shutil.copyfileobj(f, self.wfile)
                finally:
                    f.close()
            except Exception as e:
                log.debug('exception  : {0}'.format(e))
                #raise e
                self.send_response(404)
                self.end_headers()
                self.wfile.write('File not found\n'.encode('utf-8'))
        else:
            self.send_response(405)
            self.end_headers()
            self.wfile.write('Only GET is supported\n'.encode('utf-8'))

    def handle_api(self, method, route):
        if method in route:
            content = route[method](self)
            if content is not None:
                self.send_response(200)
                if 'media_type' in route:
                    self.send_header('Content-type', route['media_type'])
                self.end_headers()
                if method != 'DELETE':
                    try:
                        self.wfile.write(json.dumps(content).encode('utf-8'))
                    except TypeError:
                        self.wfile.write(json.dumps(content, default=lambda x: x.__dict__).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write('Not found\n'.encode('utf-8'))
        else:
            self.send_response(405)
            self.end_headers()
            self.wfile.write('{0} is not supported for {1}\n'.format(method, self.path).encode('utf-8'))

    def handle_method(self, method):
        route = self.get_route()
        if route is None:
            self.send_response(404)
            self.end_headers()
            self.wfile.write('Route not found\n'.encode('utf-8'))
        else:
            if 'file' in route:
                self.handle_file(method, route)
            else:
                self.handle_api(method, route)

    def get_route(self):
        if self.server and self.server.routes:
            for path, route in self.server.routes.items():
                if re.match(path, self.path):
                    return route
        return None

    def get_file_path(self, route):
        if 'file' not in route:
            return None
        # get file path from self.path
        # servedir = os.path.join(here, self.server.servedir)
        #servedir = here + "/../www"
        if route['file'] == '/':
            filepath = www + self.path
        else:
            filepath = www + route['file']
        return filepath


class RESTHttpServer():
    def __init__(self, ip, port, routes=None, servedir=None):
        log.info('Starting HTTP server on port {0}, root {1}'.format(port, www))
        self.server = ThreadingHTTPServer((ip, port), RESTRequestHandler)
        log.debug('HTTP server started')
        self.server.routes = routes
        self.server.servedir = servedir

    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        log.info('Started HTTP server at {0}'.format(self.server.server_address))

    def stop(self):
        self.server.shutdown()
        self.server_thread.join()
        log.info('Stopped HTTP server')
