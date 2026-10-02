"""JSON HTTP API with SQLite persistence."""
import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from calculator import CalculationError, calculate

DATABASE = Path(os.environ.get('CALCULATOR_DB', 'data/history.sqlite3'))
ORIGIN = os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5500')


@contextmanager
def connect():
    database = sqlite3.connect(DATABASE, timeout=15)
    try:
        with database:
            yield database
    finally:
        database.close()


def initialize():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with connect() as database:
        database.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, expression TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL)')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        logging.info('%s %s', self.client_address[0], format_string % args)

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Vary', 'Origin')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path != '/api/calculate':
            return self.respond(404, {'success': False, 'message': '接口不存在'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise CalculationError('请求大小无效')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise CalculationError('请求必须是 JSON 对象')
            expression = data.get('expression')
            result = calculate(expression)
            created_at = datetime.now(timezone.utc).isoformat()
            with connect() as database:
                cursor = database.execute('INSERT INTO history(expression,result,created_at) VALUES(?,?,?)', (expression.strip(), result, created_at))
                record_id = cursor.lastrowid
            self.respond(201, {'success': True, 'id': record_id, 'expression': expression.strip(), 'result': result, 'created_at': created_at})
        except (ValueError, UnicodeError) as error:
            self.respond(400, {'success': False, 'message': str(error) if isinstance(error, CalculationError) else '请求 JSON 格式错误'})
        except sqlite3.Error:
            logging.exception('Database write failed')
            self.respond(500, {'success': False, 'message': '数据库操作失败'})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/health':
            return self.respond(200, {'success': True})
        if parsed.path != '/api/history':
            return self.respond(404, {'success': False, 'message': '接口不存在'})
        try:
            query = parse_qs(parsed.query)
            page = int(query.get('page', ['1'])[0])
            if not 1 <= page <= 1_000_000:
                raise ValueError('Page out of range')
            search = query.get('q', [''])[0][:500]
            with connect() as database:
                database.row_factory = sqlite3.Row
                where = ' WHERE instr(expression, ?) > 0'
                total = database.execute('SELECT count(*) FROM history' + where, (search,)).fetchone()[0]
                rows = database.execute('SELECT * FROM history' + where + ' ORDER BY id DESC LIMIT 10 OFFSET ?', (search, (page - 1) * 10)).fetchall()
            self.respond(200, {'success': True, 'items': [dict(row) for row in rows], 'page': page, 'total': total, 'page_size': 10})
        except ValueError:
            self.respond(400, {'success': False, 'message': '页码无效'})
        except sqlite3.Error:
            logging.exception('Database read failed')
            self.respond(500, {'success': False, 'message': '数据库操作失败'})

    def do_DELETE(self):
        try:
            parts = self.path.split('/')
            if len(parts) != 4 or parts[1:3] != ['api', 'history'] or not parts[3].isdigit():
                return self.respond(404, {'success': False, 'message': '接口不存在'})
            record_id = int(parts[3])
            if not 1 <= record_id <= 9_223_372_036_854_775_807:
                return self.respond(400, {'success': False, 'message': '记录编号无效'})
            with connect() as database:
                changed = database.execute('DELETE FROM history WHERE id=?', (record_id,)).rowcount
            self.respond(200 if changed else 404, {'success': bool(changed), 'message': '已删除' if changed else '记录不存在'})
        except ValueError:
            self.respond(400, {'success': False, 'message': '记录编号无效'})
        except sqlite3.Error:
            logging.exception('Database delete failed')
            self.respond(500, {'success': False, 'message': '数据库操作失败'})


if __name__ == '__main__':
    initialize()
    address = (os.environ.get('HOST', '127.0.0.1'), int(os.environ.get('PORT', '8000')))
    print(f'Calculator API: http://{address[0]}:{address[1]}', flush=True)
    ThreadingHTTPServer(address, Handler).serve_forever()
