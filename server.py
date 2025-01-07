import http.server
import socketserver
import json
from pathlib import Path

# Configure the server
PORT = 8000
DIRECTORY = Path(__file__).parent

class ChatRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def do_POST(self):
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Process the message
            message = data.get('message', '')
            response = f"Server received: {message}"
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode())
        else:
            self.send_error(404, "Path not found")
    
    def do_GET(self):
        super().do_GET()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), ChatRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
