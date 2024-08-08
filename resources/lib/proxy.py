import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import request

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
host = 'localhost'
port = 8079

class Data(object):
    api_key = ''
    server_url = ''


class ProxyHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        pass

    def do_GET(self):
        uuid = self.path[1:]
        url = Data.server_url + '/api/assets/' + uuid + '/original'
        print(url)
        req = request.Request(url)
        req.add_header('x-api-key', Data.api_key)
        self.send_response(200)
        self.send_header('Content-type', 'application/octet-stream')
        self.end_headers()
        with request.urlopen(req) as res:
            dat = res.read()
            try:
                self.wfile.write(dat)   # ConnectionResetError ocurring here for unknown reason, but data comes through
            except ConnectionResetError:
                pass


def start(api_key: str, server_url: str):
    Data.api_key = api_key
    Data.server_url = server_url
    proxy = HTTPServer((host, port), ProxyHandler)
    LOG.info("Immich proxy started http://%s:%s" % (host, port))

    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        pass

    proxy.server_close()
    LOG.info('Immich proxy stopped.')
