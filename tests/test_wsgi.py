import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import server


class WsgiTests(unittest.TestCase):
    def test_hosted_api_uses_same_database_and_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            original = server.DATABASE
            server.DATABASE = Path(directory) / 'history.sqlite3'
            try:
                spec = importlib.util.spec_from_file_location('deployment_wsgi', Path(__file__).resolve().parents[1] / 'src/wsgi.py')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                def request(method, path, data=None):
                    body = json.dumps(data).encode() if data is not None else b''
                    response = []
                    environ = {'REQUEST_METHOD': method, 'PATH_INFO': path, 'CONTENT_LENGTH': str(len(body)), 'wsgi.input': io.BytesIO(body)}
                    output = b''.join(module.application(environ, lambda status, headers: response.append((status, dict(headers)))))
                    return response[0], json.loads(output) if output else None

                response, record = request('POST', '/api/calculate', {'expression': '3*-2'})
                self.assertTrue(response[0].startswith('201'))
                self.assertEqual(record['result'], '-6')
                self.assertEqual(request('GET', '/api/history')[1]['total'], 1)
                self.assertTrue(request('POST', '/api/calculate', {'expression': '1/0'})[0][0].startswith('400'))
                self.assertTrue(request('OPTIONS', '/api/calculate')[0][0].startswith('204'))
                self.assertTrue(request('PATCH', '/api/history')[0][0].startswith('405'))
                self.assertTrue(request('DELETE', f'/api/history/{record["id"]}')[0][0].startswith('200'))
                self.assertEqual(request('GET', '/api/history')[1]['total'], 0)
            finally:
                server.DATABASE = original
