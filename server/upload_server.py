import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi

UPLOAD_DIR = 'uploads'
PORT = 8080

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class SimpleUploadHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        if ctype == 'multipart/form-data':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            if 'file' in form:
                fileitem = form['file']
                filename = os.path.basename(fileitem.filename)
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(fileitem.file.read())
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f'File uploaded: {filename}\n'.encode())
                print(f'File uploaded: {filepath}')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'No file part in the request.')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Content-Type must be multipart/form-data.')

if __name__ == '__main__':
    httpd = HTTPServer(('0.0.0.0', PORT), SimpleUploadHandler)
    print(f'Upload server running on port {PORT}...')
    httpd.serve_forever() 