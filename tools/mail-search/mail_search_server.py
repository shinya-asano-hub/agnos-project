#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, json, urllib.parse, urllib.request, os

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/':
            with open(os.path.expanduser('~/mail_search.html'), 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        elif parsed.path == '/fetch-url':
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get('url', [''])[0]
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as r:
                    raw = r.read().decode('utf-8', errors='ignore')
                import re
                text = re.sub(r'<[^>]+>', '', raw)
                text = re.sub(r'\s+', ' ', text).strip()[:2000]
            except Exception as e:
                text = f'取得失敗: {e}'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(text.encode())

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        keyword = body.get('keyword', '')
        account = body.get('account', 'all')

        results = search_mail_spotlight(keyword)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'results': results}, ensure_ascii=False).encode())

def search_mail_spotlight(keyword):
    """Use mdfind + grep to search mail files, with AppleScript fallback"""
    results = []

    # Method 1: Try mdfind (Spotlight)
    try:
        r = subprocess.run(
            ['mdfind', f'kMDItemSubject == "*{keyword}*"wc'],
            capture_output=True, text=True, timeout=10
        )
        if r.stdout.strip():
            for path in r.stdout.strip().split('\n')[:20]:
                if path:
                    results.append({'subject': os.path.basename(path), 'from': path, 'date': '', 'body': ''})
    except:
        pass

    if results:
        return results

    # Method 2: AppleScript - search ONLY inbox, subject only, with tight timeout
    escaped = keyword.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    script = f'''
tell application "Mail"
    set out to ""
    set n to 0
    repeat with msg in (messages of inbox)
        if n >= 20 then exit repeat
        try
            set s to subject of msg
            if s contains "{escaped}" then
                set f to sender of msg
                set d to date received of msg
                set out to out & s & "<<S>>" & f & "<<S>>" & (d as string) & "<<S>>" & "<<E>>"
                set n to n + 1
            end if
        end try
    end repeat
    return out
end tell
'''
    try:
        r = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=45)
        raw = r.stdout.strip()
        if raw:
            for item in raw.split('<<E>>'):
                parts = item.split('<<S>>')
                if len(parts) >= 3 and parts[0].strip():
                    results.append({
                        'subject': parts[0].strip(),
                        'from': parts[1].strip(),
                        'date': parts[2].strip(),
                        'body': ''
                    })
    except subprocess.TimeoutExpired:
        if not results:
            results.append({
                'subject': '⏱ タイムアウト',
                'from': '',
                'date': '',
                'body': 'メールアプリの応答が遅いです。Gmail/Outlookボタンでウェブ検索してください。'
            })
    except Exception as e:
        if not results:
            results.append({'subject': f'エラー: {e}', 'from': '', 'date': '', 'body': ''})

    return results

print("メール検索アプリ起動中... http://localhost:8877")
HTTPServer(('localhost', 8877), Handler).serve_forever()
