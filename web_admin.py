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
    disk = psutil.disk_usage('/')
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
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "uptime": f"{h}h {m}m {s}s",
        "local_ip": get_local_ip(),
        "stats": stats
    }
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quan Tri Tiem Sach - Headless Server</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
body{background:#0f172a;color:#f8fafc;padding:16px}
.container{max-width:900px;margin:0 auto}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;border-bottom:1px solid #334155;padding-bottom:12px}
h1{font-size:20px;color:#38bdf8}
.ip-badge{background:#1e293b;border:1px solid #334155;padding:4px 10px;border-radius:6px;font-size:13px;color:#94a3b8}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.card{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:14px}
.card-title{font-size:12px;color:#94a3b8;margin-bottom:6px;text-transform:uppercase}
.card-val{font-size:22px;font-weight:bold;color:#f8fafc}
.bar-bg{background:#334155;height:6px;border-radius:3px;margin-top:8px;overflow:hidden}
.bar-fill{background:#38bdf8;height:100%;transition:width 0.3s}
.panel{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:18px;margin-bottom:20px}
.panel-title{font-size:16px;font-weight:bold;color:#f8fafc;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.badge-lan{font-size:11px;background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px}
.badge-remote{font-size:11px;background:#7f1d1d;color:#fca5a5;padding:3px 8px;border-radius:4px}
.form-group{margin-bottom:14px}
label{display:block;font-size:13px;color:#94a3b8;margin-bottom:4px}
input,select,textarea{width:100%;background:#0f172a;border:1px solid #334155;color:#f8fafc;padding:10px;border-radius:6px;font-size:14px}
input:focus,select:focus,textarea:focus{outline:none;border-color:#38bdf8}
textarea{resize:vertical;min-height:75px}
.btn{background:#0284c7;color:#fff;border:none;padding:10px 20px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500}
.btn:hover{background:#0369a1}
.btn:disabled{background:#475569;cursor:not-allowed}
.alert{padding:10px;border-radius:6px;font-size:13px;margin-bottom:14px;display:none}
.alert-ok{background:#065f46;color:#a7f3d0}
.alert-err{background:#7f1d1d;color:#fecaca}
</style>
</head>
<body>
<div class="container">
<header>
<div>
<h1>QUAN TRI MAY CHU DANG BAI & KHO SACH</h1>
<div style="font-size:12px;color:#64748b;margin-top:2px">Headless Server Controller</div>
</div>
<div class="ip-badge">IP: <span id="local-ip">Loading...</span>:8080</div>
</header>
<div class="grid">
<div class="card">
<div class="card-title">CPU</div>
<div class="card-val" id="cpu-val">0%</div>
<div class="bar-bg"><div class="bar-fill" id="cpu-bar" style="width:0%"></div></div>
</div>
<div class="card">
<div class="card-title">RAM (Bo Nho)</div>
<div class="card-val" id="ram-val">0 / 0 GB</div>
<div class="bar-bg"><div class="bar-fill" id="ram-bar" style="width:0%"></div></div>
</div>
<div class="card">
<div class="card-title">O Cung (Disk)</div>
<div class="card-val" id="disk-val">0 / 0 GB</div>
<div class="bar-bg"><div class="bar-fill" id="disk-bar" style="width:0%"></div></div>
</div>
<div class="card">
<div class="card-title">Kho Sach</div>
<div class="card-val" id="books-val">0 con / 0 ban</div>
<div style="font-size:11px;color:#94a3b8;margin-top:6px">Uptime: <span id="uptime-val">0s</span></div>
</div>
</div>
<div class="panel">
<div class="panel-title">
<span>Cau Hinh He Thong</span>
<span id="access-badge" class="badge-lan">Kiem tra quyen...</span>
</div>
<div id="alert-box" class="alert"></div>
<form id="config-form">
<div class="form-group">
<label>Nha cung cap AI (AI Provider)</label>
<select id="ai-provider" name="AI_PROVIDER">
<option value="gemini">Google Gemini (Mien phi)</option>
<option value="openai_compatible">OpenAI-Compatible (DeepSeek, Groq, OpenAI)</option>
<option value="ollama">Local Ollama (Offline tren may)</option>
</select>
</div>
<div class="form-group">
<label>Gemini API Key</label>
<input type="password" id="gemini-key" name="GEMINI_API_KEY" placeholder="AIzaSy...">
</div>
<div class="form-group">
<label>OpenAI / DeepSeek API Key</label>
<input type="password" id="openai-key" name="OPENAI_API_KEY" placeholder="sk-...">
</div>
<div class="form-group">
<label>OpenAI / DeepSeek Base URL</label>
<input type="text" id="openai-base" name="OPENAI_BASE_URL" placeholder="https://api.deepseek.com">
</div>
<div class="form-group">
<label>Danh sach Nhom can QUET TIM KHACH (Moi dong 1 link Group)</label>
<textarea id="monitored-groups" name="MONITORED_GROUP_URLS" placeholder="https://www.facebook.com/groups/hoimesachcu&#10;https://www.facebook.com/groups/traodoisach"></textarea>
</div>
<div class="form-group">
<label>Nhom can TU DONG DANG 1 BAI/NGAY (Moi dong 1 link Group)</label>
<textarea id="target-post-groups" name="TARGET_POST_GROUP_URLS" placeholder="https://www.facebook.com/groups/nhom_dang_bai"></textarea>
</div>
<div class="form-group">
<label>Gio dang bai vao Nhom moi ngay</label>
<input type="text" id="group-post-hour" name="GROUP_POSTING_HOUR" placeholder="09:30">
</div>
<button type="submit" id="save-btn" class="btn">Luu Cau Hinh</button>
</form>
</div>
</div>
<script>
let isLocal = false;
async function fetchMetrics(){
try{
const res = await fetch('/api/system');
const d = await res.json();
document.getElementById('local-ip').innerText = d.local_ip;
document.getElementById('cpu-val').innerText = d.cpu_percent + '%';
document.getElementById('cpu-bar').style.width = d.cpu_percent + '%';
document.getElementById('ram-val').innerText = d.ram_used_gb + ' / ' + d.ram_total_gb + ' GB';
document.getElementById('ram-bar').style.width = d.ram_percent + '%';
document.getElementById('disk-val').innerText = d.disk_used_gb + ' / ' + d.disk_total_gb + ' GB';
document.getElementById('disk-bar').style.width = d.disk_percent + '%';
document.getElementById('books-val').innerText = d.stats.available_in_stock + ' con / ' + d.stats.sold_out + ' ban';
document.getElementById('uptime-val').innerText = d.uptime;
}catch(e){}
}
async function loadSettings(){
try{
const res = await fetch('/api/settings');
const d = await res.json();
isLocal = d.is_local;
const badge = document.getElementById('access-badge');
const saveBtn = document.getElementById('save-btn');
if(isLocal){
badge.className = 'badge-lan';
badge.innerText = 'Mang Noi Bo (Duoc phep sua)';
saveBtn.disabled = false;
}else{
badge.className = 'badge-remote';
badge.innerText = 'Truy cap tu xa (Chi xem - Khong duoc sua)';
saveBtn.disabled = true;
}
const s = d.settings;
document.getElementById('ai-provider').value = s.AI_PROVIDER || 'gemini';
document.getElementById('gemini-key').value = s.GEMINI_API_KEY || '';
document.getElementById('openai-key').value = s.OPENAI_API_KEY || '';
document.getElementById('openai-base').value = s.OPENAI_BASE_URL || '';
document.getElementById('monitored-groups').value = (s.MONITORED_GROUP_URLS || []).join('\\n');
document.getElementById('target-post-groups').value = (s.TARGET_POST_GROUP_URLS || []).join('\\n');
document.getElementById('group-post-hour').value = s.GROUP_POSTING_HOUR || '09:30';
}catch(e){}
}
document.getElementById('config-form').onsubmit = async (e) => {
e.preventDefault();
const alertBox = document.getElementById('alert-box');
if(!isLocal){
alertBox.className = 'alert alert-err';
alertBox.innerText = 'Ban chi co the sua cau hinh khi dang o cung mang noi bo (LAN/Wi-Fi) cua may.';
alertBox.style.display = 'block';
return;
}
const payload = {
AI_PROVIDER: document.getElementById('ai-provider').value,
GEMINI_API_KEY: document.getElementById('gemini-key').value,
OPENAI_API_KEY: document.getElementById('openai-key').value,
OPENAI_BASE_URL: document.getElementById('openai-base').value,
MONITORED_GROUP_URLS: document.getElementById('monitored-groups').value.split('\\n').map(s=>s.strip ? s.strip() : s.trim()).filter(s=>s),
TARGET_POST_GROUP_URLS: document.getElementById('target-post-groups').value.split('\\n').map(s=>s.strip ? s.strip() : s.trim()).filter(s=>s),
GROUP_POSTING_HOUR: document.getElementById('group-post-hour').value.trim()
};
try{
const res = await fetch('/api/settings', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify(payload)
});
const result = await res.json();
if(result.success){
alertBox.className = 'alert alert-ok';
alertBox.innerText = 'Da luu va ap dung cau hinh thanh cong!';
}else{
alertBox.className = 'alert alert-err';
alertBox.innerText = result.error || 'Loi khi luu cau hinh.';
}
alertBox.style.display = 'block';
setTimeout(()=>{ alertBox.style.display = 'none'; }, 4000);
}catch(err){
alertBox.className = 'alert alert-err';
alertBox.innerText = 'Loi ket noi: ' + err;
alertBox.style.display = 'block';
}
};
fetchMetrics();
loadSettings();
setInterval(fetchMetrics, 3000);
</script>
</body>
</html>
"""
class AdminRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_GET(self):
        client_ip = self.client_address[0]
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/system":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = get_system_metrics()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        elif self.path == "/api/settings":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "is_local": is_local_network(client_ip),
                "settings": settings_manager.get_current_settings()
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
    def do_POST(self):
        client_ip = self.client_address[0]
        if self.path == "/api/settings":
            if not is_local_network(client_ip):
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Chi cho phep thay doi cau hinh tu mang noi bo (LAN/Wi-Fi)."}).encode("utf-8"))
                return
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                new_data = json.loads(body.decode("utf-8"))
                ok = settings_manager.save_settings(new_data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": ok}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
def run_web_admin(port: int = 8080):
    settings_manager.load_and_apply_settings()
    server = ThreadedHTTPServer(("0.0.0.0", port), AdminRequestHandler)
    local_ip = get_local_ip()
    logging.info(f"[WEB ADMIN] Dang chay tai: http://{local_ip}:{port} (RAM tieu thu ~10MB)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
if __name__ == "__main__":
    run_web_admin()

