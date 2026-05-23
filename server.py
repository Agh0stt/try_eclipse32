#!/usr/bin/env python3
"""Simple HTTP server with Range request support for v86."""
import http.server, os, sys

class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404)
            return

        file_size = os.path.getsize(path)
        range_header = self.headers.get("Range")

        if range_header:
            # Parse "bytes=start-end"
            ranges = range_header.strip().replace("bytes=", "")
            start_str, _, end_str = ranges.partition("-")
            start = int(start_str) if start_str else 0
            end   = int(end_str)   if end_str   else file_size - 1
            end   = min(end, file_size - 1)
            length = end - start + 1

            self.send_response(206)
            self.send_header("Content-Type",  self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining:
                    chunk = f.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Type",   self.guess_type(path))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges",  "bytes")
            self.end_headers()
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}")

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

# Serve from the directory where this script lives
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Serving {os.getcwd()} on http://localhost:{port}/")
http.server.HTTPServer(("", port), RangeHandler).serve_forever()
