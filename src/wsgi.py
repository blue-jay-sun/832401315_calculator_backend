"""WSGI deployment entry point sharing the local HTTP implementation."""
import io
from http import HTTPStatus

from server import Handler, initialize

initialize()


def application(environ, start_response):
    handler = Handler.__new__(Handler)
    handler.path = environ.get('PATH_INFO', '/')
    if environ.get('QUERY_STRING'):
        handler.path += '?' + environ['QUERY_STRING']
    handler.headers = {'Content-Length': environ.get('CONTENT_LENGTH', '0')}
    handler.rfile = environ['wsgi.input']
    handler.wfile = io.BytesIO()
    response_headers = []
    status = [500]
    handler.send_response = lambda code: status.__setitem__(0, code)
    handler.send_header = lambda name, value: response_headers.append((name, value))
    handler.end_headers = lambda: None
    method = environ.get('REQUEST_METHOD', 'GET')
    dispatch = {
        'GET': handler.do_GET,
        'POST': handler.do_POST,
        'DELETE': handler.do_DELETE,
        'OPTIONS': handler.do_OPTIONS,
    }
    if method in dispatch:
        dispatch[method]()
    else:
        handler.respond(405, {'success': False, 'message': '请求方法不支持'})
    start_response(f'{status[0]} {HTTPStatus(status[0]).phrase}', response_headers)
    return [handler.wfile.getvalue()]
