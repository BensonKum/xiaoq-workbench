#!/usr/bin/env python3
"""Simple static file server for tools-hub that serves index.html on /"""
import http.server
import os

os.chdir(r"C:\Users\benso\WorkBuddy\Claw\tools-hub")

class IndexHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return super().do_GET()

http.server.HTTPServer(('0.0.0.0', 8082), IndexHandler).serve_forever()
