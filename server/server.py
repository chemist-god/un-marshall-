import socket
import threading
from rtsp_handler import RTSPHandler
import sys

# Server configuration
RTSP_PORT = 8554

class RTSPServer:
    def __init__(self, host='0.0.0.0', port=RTSP_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"RTSP Server listening on {self.host}:{self.port}")

    def start(self):
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted connection from {client_address}")
                handler = RTSPHandler(client_socket)
                thread = threading.Thread(target=handler.handle, daemon=True)
                thread.start()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            self.server_socket.close()

if __name__ == '__main__':
    server = RTSPServer()
    server.start()
