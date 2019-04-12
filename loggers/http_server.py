from http.server import BaseHTTPRequestHandler, HTTPServer


class HttpServer(BaseHTTPRequestHandler):
    """
    basic http server duck taped together
    """
    LOG_FILE: str = "LOG.json"  # log file path

    def _set_headers(self):
        self.send_response(200)
        self.send_header(b'Content-type', b'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        try:
            self.wfile.write(open(self.LOG_FILE, "r").read().encode())
        except Exception as e:
            self.wfile.write(b'{"exception": ' + str(e).encode() + b'}')

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write(b"<html><body><h1>POST!</h1></body></html>")


def run(server_class=HTTPServer, handler_class=HttpServer, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
