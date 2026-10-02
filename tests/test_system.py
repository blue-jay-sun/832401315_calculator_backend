import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from calculator import CalculationError, calculate


class ParserTests(unittest.TestCase):
    def test_supported_expressions(self):
        cases = {'12+8': '20', '8-3*2': '2', '(1+2)*3': '9', '10/2+7': '12', '-5+8': '3', '3*-2': '-6', '+2--3': '5', '0.1+0.2': '0.3', '.5×4': '2', '8÷2': '4', '1/3': '0.3333333333333333333333333333'}
        for expression, expected in cases.items():
            with self.subTest(expression=expression):
                self.assertEqual(calculate(expression), expected)

    def test_rejects_invalid_input(self):
        for expression in ['', None, '1/0', '(1+2', '2(3)', '1..2', '1+', 'abc', '__import__("os")', '1**2', '(' * 70 + '1' + ')' * 70, '1' * 501]:
            with self.subTest(expression=expression):
                with self.assertRaises(CalculationError):
                    calculate(expression)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = {**os.environ, 'PORT': '18080', 'CALCULATOR_DB': str(Path(self.temp.name) / 'history.sqlite3')}
        self.start_server()

    def start_server(self):
        self.process = subprocess.Popen([sys.executable, 'src/server.py'], cwd=Path(__file__).resolve().parents[1], env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                self.api('/api/health')
                return
            except URLError:
                time.sleep(.05)
        self.fail('Server failed to start')

    def tearDown(self):
        self.process.terminate()
        self.process.wait(timeout=10)
        self.temp.cleanup()

    def api(self, path, method='GET', data=None):
        body = json.dumps(data).encode() if data is not None else None
        request = Request('http://127.0.0.1:18080' + path, data=body, method=method, headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_persistence_deletion_and_validation(self):
        status, record = self.api('/api/calculate', 'POST', {'expression': '(2+3)*4'})
        self.assertEqual(status, 201)
        self.assertEqual(record['result'], '20')
        self.assertEqual(self.api('/api/calculate', 'POST', {'expression': '1/0'})[0], 400)
        self.assertEqual(self.api('/api/calculate', 'POST', [1, 2])[0], 400)
        self.assertEqual(self.api('/api/history')[1]['total'], 1)
        self.process.terminate()
        self.process.wait(timeout=10)
        self.start_server()
        self.assertEqual(self.api('/api/history')[1]['items'][0]['id'], record['id'])
        self.assertEqual(self.api('/api/history?q=notfound')[1]['total'], 0)
        self.assertEqual(self.api('/api/history?page=bad')[0], 400)
        self.assertEqual(self.api(f'/api/history/{record["id"]}', 'DELETE')[0], 200)
        self.assertEqual(self.api('/api/history')[1]['total'], 0)
        self.assertEqual(self.api(f'/api/history/{record["id"]}', 'DELETE')[0], 404)

    def test_pagination(self):
        for number in range(12):
            self.api('/api/calculate', 'POST', {'expression': str(number)})
        self.assertEqual(len(self.api('/api/history')[1]['items']), 10)
        self.assertEqual(len(self.api('/api/history?page=2')[1]['items']), 2)

    def test_extreme_identifiers_and_pages(self):
        for page in ['0', '-1', '1000001', '9' * 100]:
            self.assertEqual(self.api('/api/history?page=' + page)[0], 400)
        for record_id in ['0', '9' * 100]:
            self.assertEqual(self.api('/api/history/' + record_id, 'DELETE')[0], 400)
        self.assertEqual(self.api('/api/health')[0], 200)

    def test_cors_and_record_fields(self):
        request = Request('http://127.0.0.1:18080/api/calculate', method='OPTIONS')
        with urlopen(request) as response:
            self.assertEqual(response.status, 204)
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:5500')
            self.assertIn('DELETE', response.headers['Access-Control-Allow-Methods'])
        _, record = self.api('/api/calculate', 'POST', {'expression': ' 8 / 4 / 2 '})
        self.assertEqual(record['result'], '1')
        self.assertEqual(record['expression'], '8 / 4 / 2')
        self.assertTrue(record['created_at'].endswith('+00:00'))
        self.assertEqual(self.api('/api/unknown')[0], 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
