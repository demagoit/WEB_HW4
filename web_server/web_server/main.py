from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import urllib.parse
import mimetypes
import pathlib
import socket
import logging
import json
import datetime

HOST = {
    # 'location': 'localhost',
    'location': '0.0.0.0',
    'web_port': 3000,
    'form_port': 5000
}

RES = {
    'web_root': 'front-init',
    'json_folder': 'front-init/storage',
    'json_file': 'data.json'
}

# storage for form messages
form_data_log = None


logger = logging.getLogger('AD')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
format = logging.Formatter('%(message)s - PID=%(process)d - TID=%(thread)d - %(name)s - %(funcName)s')
ch.setFormatter(format)
logger.addHandler(ch)

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        web_root = pathlib.Path.cwd().joinpath(RES.get('web_root')) 

        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            obj = web_root.joinpath('index.html')
            status = 200
        else:
            obj = web_root.joinpath(pr_url.path[1:])
            status = 200
            if not obj.exists():
                obj = web_root.joinpath('error.html')
                status = 404

        self.send_reply(obj, status)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        UDP_socket_client(HOST.get('location'), HOST.get('form_port'), data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_reply(self, filename, status=200):
        mt = mimetypes.guess_type(self.path)

        self.send_response(status)

        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')

        self.end_headers()

        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def UDP_socket_server(host = None, port = None):
    logger.debug(f'{host}:{port} - UDP_server up')
    if not host:
        host = HOST.get('location')
    if not port:
        port = HOST.get('form_port')

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        while True:
            data, adr = sock.recvfrom(1024)
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {key: value for key, value in [
                el.split('=') for el in data_parse.split('&')]}
            logger.debug(f"{host}:{port} - received {data_dict} from {adr}")
            save_json(data=data_dict, filename=RES.get('json_file'), folder=RES.get('json_folder'))
            logger.debug(f'{host}:{port} - UDP_server alive...')

        
def UDP_socket_client(host, port, msg: bin = b"Hello!"):
    logger.debug(f'{host}:{port} - UDP_client up...')
    if not host:
        host = HOST.get('location')
    if not port:
        port = HOST.get('form_port')

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server = (host, port)
        logger.debug(f"{host}:{port} - sending {msg.decode()} to {server}")
        sock.sendto(msg, server)
    logger.debug(f'{host}:{port} - UDP_client down')

def HTTP_server(host, port, handler_class=HttpHandler):
    server_address = (host, port)
    http = HTTPServer(server_address, handler_class)

    logger.debug(f'{host}:{port} - web_server up...')
    http.serve_forever()
    
def save_json(data: dict, filename: str = RES.get('json_file'), folder: str = RES.get('json_folder')):
    global form_data_log
    form_data_log[str(datetime.datetime.now())] = data

    folder = pathlib.Path.cwd().joinpath(folder)
    if not pathlib.Path.exists(folder) or not pathlib.Path.is_dir(folder):
        pathlib.Path.mkdir(folder)
    target = pathlib.Path.joinpath(folder, filename)

    with open(target, 'w') as fh:
        json.dump(form_data_log, fh, indent=4)

def read_json(filename: str = RES.get('json_file'), folder: str = RES.get('json_folder')):
    folder = pathlib.Path.cwd().joinpath(folder)
    target = pathlib.Path.joinpath(folder, filename)
    if pathlib.Path.exists(target):
        with open(target, 'r') as fh:
            data = json.load(fh)
    else:
        data = {}
    return data

if __name__ == '__main__':
    form_data_log = read_json(filename=RES.get('json_file'), folder=RES.get('json_folder'))

    form_server = Thread(target=UDP_socket_server, args=(HOST.get('location'), HOST.get('form_port')))
    web_server = Thread(target=HTTP_server, args=(HOST.get('location'), HOST.get('web_port'), HttpHandler))
    
    try:
        logger.debug('Start web_server')
        web_server.start()
    except:
        logger.debug('web_server fail to start')
    
    try:
        logger.debug('Start form_server')
        form_server.start()
    except:
        logger.debug('form_server fail to start')
