#!/usr/bin/env python3
"""Stockpulse Dashboard — HTTP server with API + chat + journal."""
import json, os, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
WEB = ROOT / "web"
CONTEXT = ROOT / "context"
JOURNAL = DATA / "journal"
INDEX = DATA / "journal-index.jsonl"
INBOX = DATA / "owner-inbox.md"

def load_json(path, default=None):
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return default or {}

def load_jsonl(path, limit=50):
    if not path.exists(): return []
    items = []
    for line in path.read_text().strip().splitlines():
        try: items.append(json.loads(line))
        except: pass
    return items[-limit:]

def load_text(path, limit_lines=100):
    if not path.exists(): return ""
    lines = path.read_text().strip().splitlines()
    return "\n".join(lines[-limit_lines:])

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""

        if path == "/api/chat":
            try:
                data = json.loads(body) if body else {}
                message = data.get("message", "").strip()
                if not message:
                    self.send_json({"error": "empty message"}, 400)
                    return
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                entry = "\n---\n[{}] Owner says:\n{}\n".format(now, message)
                with open(str(INBOX), "a") as f:
                    f.write(entry)
                self.send_json({"ok": True, "queued": message, "next_cycle": "Message will be read at top of next cycle"})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        self.send_error(404)

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path == "/" or path == "/index.html":
            index = WEB / "index.html"
            if index.exists():
                body = index.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404)
            return

        if path == "/api/all":
            data = load_json(OUTPUT / "dashboard-data.json", {})
            # Always serve fresh trades/portfolio/performance from source files
            data["trades"] = load_jsonl(DATA / "trades.jsonl", 100)[::-1]
            data["portfolio"] = load_json(DATA / "portfolio.json", data.get("portfolio", {}))
            data["performance"] = load_json(DATA / "performance.json", data.get("performance", {}))
            self.send_json(data)
            return

        if path == "/api/health":
            import subprocess
            health = {}
            try:
                health["temp"] = round(int(open("/sys/class/thermal/thermal_zone0/temp").read().strip()) / 1000, 1)
            except: health["temp"] = 0
            try:
                m = open("/proc/meminfo").read()
                total = int([l for l in m.split(chr(10)) if "MemTotal" in l][0].split()[1])
                avail = int([l for l in m.split(chr(10)) if "MemAvailable" in l][0].split()[1])
                health["ram_used"] = round((total - avail) / 1024)
                health["ram_total"] = round(total / 1024)
            except: pass
            try:
                r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
                parts = r.stdout.strip().split(chr(10))[1].split()
                health["disk"] = parts[2] + "/" + parts[1]
            except: pass
            try:
                health["load"] = open("/proc/loadavg").read().split()[0]
            except: pass
            try:
                import glob
                # Estimate total tokens from all cycle logs
                logs = sorted(glob.glob(str(ROOT) + "/data/logs/cycle_*.log"))
                total_prompt = 0
                total_resp = 0
                for log in logs[-50:]:  # last 50 cycles only for speed
                    with open(log) as lf:
                        for line in lf:
                            if "Prompt size:" in line:
                                try: total_prompt += int(line.split("Prompt size:")[1].strip().split()[0])
                                except: pass
                            elif "LLM response:" in line:
                                try: total_resp += int(line.split("LLM response:")[1].strip().split()[0])
                                except: pass
                health["total_prompt_tokens"] = total_prompt // 4
                health["total_resp_tokens"] = total_resp // 4
                health["total_tokens"] = (total_prompt + total_resp) // 4
                health["cycles_sampled"] = len(logs[-50:])
            except: pass
            try:
                pf = Path(str(ROOT) + "/tmp_prompt.md")
                if pf.exists():
                    health["prompt_bytes"] = pf.stat().st_size
                    health["prompt_tokens"] = pf.stat().st_size // 4
            except: pass
            try:
                health["mode"] = json.loads(Path(str(ROOT) + "/data/cycle-mode.json").read_text()).get("max_turns", "?")
            except: health["mode"] = "?"
            # Daily P&L history
            try:
                daily = []
                dp = Path(str(ROOT) + "/data/daily-pnl.jsonl")
                if dp.exists():
                    for line in dp.read_text().strip().splitlines()[-14:]:
                        try: daily.append(json.loads(line))
                        except: pass
                health["daily_pnl"] = daily
            except: pass
            self.send_json(health)
            return

        if path == "/api/portfolio":
            port = load_json(DATA / "portfolio.json")
            cache = load_json(DATA / "price_cache.json")
            for pos in port.get("positions", []):
                ticker = pos.get("ticker", "")
                if ticker in cache:
                    price = cache[ticker].get("price")
                    if price:
                        entry = pos.get("entry_price", 0)
                        shares = pos.get("shares", 0)
                        is_short = pos.get("direction") == "short"
                        pos["current_price"] = price
                        if is_short:
                            pos["unrealized_pnl"] = round((entry - price) * shares, 2)
                        else:
                            pos["unrealized_pnl"] = round((price - entry) * shares, 2)
                        pos["unrealized_pnl_pct"] = round((pos["unrealized_pnl"] / (entry * shares)) * 100, 2) if entry and shares else 0
            self.send_json(port)
            return

        if path == "/api/trades":
            self.send_json(load_jsonl(DATA / "trades.jsonl", 30))
            return

        if path == "/api/predictions":
            self.send_json(load_jsonl(DATA / "predictions.jsonl", 20))
            return

        if path == "/api/performance":
            self.send_json(load_json(DATA / "performance.json"))
            return

        if path == "/api/mind":
            self.send_json({
                "inner_voice": load_text(DATA / "inner-voice.md", 20),
                "thoughts": load_text(DATA / "thoughts.md", 20),
                "mood": load_json(DATA / "mood.json"),
                "memory": load_text(DATA / "memory.md", 10),
                "strategy": load_json(DATA / "strategy.json")
            })
            return

        if path == "/api/market":
            market = {}
            for name in ["prices", "news", "sentiment", "sectors", "calendar"]:
                p = CONTEXT / "{}.md".format(name)
                if p.exists():
                    market[name] = p.read_text()
            self.send_json(market)
            return

        if path == "/api/lessons":
            lessons_dir = ROOT / "knowledge" / "lessons"
            lessons = []
            if lessons_dir.exists():
                for lf in sorted(lessons_dir.glob("review-cycle-*.md"), reverse=True)[:5]:
                    lessons.append({"file": lf.name, "content": lf.read_text()[:1000]})
            self.send_json(lessons)
            return

        if path == "/api/knowledge":
            knowledge_dir = ROOT / "knowledge"
            result = {}
            if knowledge_dir.exists():
                for cat_dir in sorted(knowledge_dir.iterdir()):
                    if cat_dir.is_dir():
                        files = []
                        for f in sorted(cat_dir.glob("*.md")):
                            content = f.read_text()
                            files.append({"name": f.stem, "content": content[:2000], "size": len(content)})
                        if files:
                            result[cat_dir.name] = files
            self.send_json(result)
            return

        # === JOURNAL API ===
        if path == "/api/journal":
            # List all journal entries from index
            entries = load_jsonl(INDEX, 500)
            entries.reverse()
            self.send_json(entries)
            return

        if path == "/api/journal/tags":
            # Get all unique tags with counts
            entries = load_jsonl(INDEX, 500)
            tag_counts = {}
            for e in entries:
                for t in e.get("tags", []):
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
            self.send_json(sorted_tags)
            return

        if path.startswith("/api/journal/cycle/"):
            # Get a specific journal entry
            try:
                cycle_num = int(path.split("/")[-1])
                jfile = JOURNAL / "cycle-{:04d}.md".format(cycle_num)
                if jfile.exists():
                    self.send_json({"cycle": cycle_num, "content": jfile.read_text()})
                else:
                    self.send_json({"error": "not found"}, 404)
            except:
                self.send_json({"error": "invalid cycle"}, 400)
            return

        if path == "/api/journal/search":
            # Search by tag
            tag = query.get("tag", [""])[0].lower()
            if not tag:
                self.send_json([])
                return
            entries = load_jsonl(INDEX, 500)
            matches = [e for e in entries if tag in e.get("tags", [])]
            matches.reverse()
            self.send_json(matches)
            return

        if path == "/api/tokens":
            self.send_json(load_json(DATA / "token-usage.json"))
            return

        if path == "/api/inbox":
            # Get current owner inbox
            content = load_text(INBOX, 50)
            self.send_json({"content": content, "has_messages": bool(content.strip())})
            return

        # Serve static files from web/
        static = WEB / path.lstrip('/')
        if static.exists() and static.is_file():
            body = static.read_bytes()
            ct = 'application/octet-stream'
            if path.endswith('.js'): ct = 'application/javascript; charset=utf-8'
            elif path.endswith('.css'): ct = 'text/css; charset=utf-8'
            elif path.endswith('.html'): ct = 'text/html; charset=utf-8'
            elif path.endswith('.json'): ct = 'application/json; charset=utf-8'
            elif path.endswith('.png'): ct = 'image/png'
            elif path.endswith('.svg'): ct = 'image/svg+xml'
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

def main():
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    server = HTTPServer(("0.0.0.0", port), Handler)
    print("[webserver] Stockpulse on http://0.0.0.0:{}".format(port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    main()
