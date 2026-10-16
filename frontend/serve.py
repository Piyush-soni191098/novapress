"""Serve the frontend with correct UTF-8 Content-Type headers."""
import http.server
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class UTF8Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        ctype = super().guess_type(path)
        if isinstance(ctype, str) and ctype.startswith("text/html"):
            return "text/html; charset=utf-8"
        return ctype

    def log_message(self, fmt, *args):
        pass  # silence per-request noise; errors still print


with socketserver.TCPServer(("", PORT), UTF8Handler) as httpd:
    print(f"Frontend running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    httpd.serve_forever()
