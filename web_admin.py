import os
import sys
import json
import time
import socket
import logging
import ipaddress
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime
import psutil
import config
import database
import settings_manager
from web_view import get_admin_html
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
START_TIME = time.time()
def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
def is_local_network(ip_str: str) -> bool:
    if ip_str in ["127.0.0.1", "localhost", "::1"]:
        return True
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback
    except Exception:
        return False
def get_system_metrics() -> dict:
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    uptime_sec = int(time.time() - START_TIME)
    h, rem = divmod(uptime_sec, 3600)
    m, s = divmod(rem, 60)
    stats = database.get_stats()
    return {
        "cpu_percent": cpu,
        "ram_used_gb": round(mem.used / (1024 ** 3), 2),
        "ram_total_gb": round(mem.total / (1024 ** 3), 2),
        "ram_percent": mem.percent,
        "uptime": f"{h}h {m}m {s}s",
        "stats": stats
    }
class AdminRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        client_ip = self.client_address[0]
        if not is_local_network(client_ip):
            self.send_error(403, "Access denied: Local network only.")
            return
        path = self.path.split('?')[0]
        if path in ['/', '/index.html']:
            content = get_admin_html(get_local_ip()).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif path == '/api/metrics':
            self._send_json(get_system_metrics())
        elif path == '/api/books':
            books = database.get_all_books(500)
            self._send_json(books)
        elif path == '/api/leads':
            leads = database.get_leads("all")
            self._send_json(leads)
        elif path == '/api/settings':
            self._send_json(settings_manager.get_settings())
        elif path == '/api/categories':
            self._send_json(database.get_all_categories())
        elif path.startswith('/storage/images/'):
            filename = os.path.basename(path)
            file_path = os.path.join(str(config.IMAGES_DIR), filename)
            if os.path.exists(file_path):
                ext = os.path.splitext(filename)[1].lower()
                mime = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(os.path.getsize(file_path)))
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Image Not Found")
        else:
            self.send_error(404, "Not Found")
    def do_POST(self):
        client_ip = self.client_address[0]
        if not is_local_network(client_ip):
            self.send_error(403, "Access denied")
            return
        path = self.path
        length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(length) if length > 0 else b'{}'
        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            payload = {}
        if path == '/api/add-book':
            title = payload.get("title", "").strip()
            author = payload.get("author", "").strip()
            category = payload.get("category", "").strip()
            price = str(payload.get("price", "")).strip()
            status = payload.get("status", "available")
            if not title:
                self._send_json({"success": False, "error": "Thiếu tựa sách"}, 400)
                return
            new_id = database.add_book_manually(title, author, category, price, status, is_reviewed=1)
            self._send_json({"success": True, "id": new_id})
        elif path == '/api/update-book':
            book_id = payload.get("id")
            title = payload.get("title", "").strip()
            author = payload.get("author", "").strip()
            category = payload.get("category", "").strip()
            price = str(payload.get("price", "")).strip()
            is_single = payload.get("is_single_book", 1)
            status = payload.get("status", "available")
            is_reviewed = payload.get("is_reviewed", 1)
            if not book_id or not title:
                self._send_json({"success": False, "error": "Thiếu thông tin sách"}, 400)
                return
            database.update_book_details(book_id, title, author, price, is_single, status, is_reviewed, category=category)
            self._send_json({"success": True})
        elif path == '/api/approve-book':
            book_id = payload.get("id")
            if book_id:
                database.mark_book_reviewed(int(book_id))
                self._send_json({"success": True})
            else:
                self._send_json({"success": False, "error": "Thiếu ID"}, 400)
        elif path == '/api/approve-all':
            database.approve_all_books()
            self._send_json({"success": True})
        elif path == '/api/delete-book':
            book_id = payload.get("id")
            if book_id:
                ok = database.delete_image_record(int(book_id))
                self._send_json({"success": ok})
            else:
                self._send_json({"success": False, "error": "Thiếu ID"}, 400)
        elif path == '/api/update-lead':
            lead_id = payload.get("id")
            status = payload.get("status", "contacted")
            if lead_id:
                ok = database.update_lead_status(int(lead_id), status)
                self._send_json({"success": ok})
            else:
                self._send_json({"success": False, "error": "Thiếu lead ID"}, 400)
        elif path == '/api/delete-lead':
            lead_id = payload.get("id")
            if lead_id:
                ok = database.delete_lead(int(lead_id))
                self._send_json({"success": ok})
            else:
                self._send_json({"success": False, "error": "Thiếu lead ID"}, 400)
        elif path == '/api/add-category':
            name = payload.get("name", "").strip()
            if name:
                ok = database.add_category(name)
                self._send_json({"success": ok, "categories": database.get_all_categories()})
            else:
                self._send_json({"success": False, "error": "Tên thể loại trống"}, 400)
        elif path == '/api/delete-category':
            name = payload.get("name", "").strip()
            if name:
                ok = database.delete_category(name)
                self._send_json({"success": ok, "categories": database.get_all_categories()})
            else:
                self._send_json({"success": False, "error": "Thiếu tên thể loại"}, 400)
        elif path == '/api/settings':
            saved = settings_manager.update_settings(payload)
            self._send_json({"success": saved})
        else:
            self.send_error(404, "Not Found")
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
def start_server(port: int = 8080):
    server_address = ('0.0.0.0', port)
    httpd = ThreadedHTTPServer(server_address, AdminRequestHandler)
    local_ip = get_local_ip()
    logging.info(f"[WEB ADMIN] Đang chạy tại: http://{local_ip}:{port} (RAM tiêu thụ ~10MB)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
run_web_admin = start_server
if __name__ == '__main__':
    start_server(8080)
