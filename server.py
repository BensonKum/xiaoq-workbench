#!/usr/bin/env python3
"""Static file server for tools-hub — serves index.html on / (no directory listing)."""
import http.server
import os
import sys

# 用腳本所在目錄，唔 hardcode 絕對路徑（搬機都通用）
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8082

class IndexHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', ''):
            self.path = '/index.html'
        return super().do_GET()

    def log_message(self, fmt, *args):
        pass  # 靜默，減少 log 噪音

print('Serving %s at http://0.0.0.0:%d/' % (HERE, PORT), flush=True)
http.server.HTTPServer(('0.0.0.0', PORT), IndexHandler).serve_forever()
