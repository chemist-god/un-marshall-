import socket
import threading
from rtsp_handler import RTSPHandler
import sys
import os

# Server configuration
RTSP_PORT = 8554

def get_video_file():
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        if not os.path.isfile(video_file):
            print(f"File not found: {video_file}")
            sys.exit(1)
        return video_file
    else:
        video_file = input("Enter the path to the video file to stream: ").strip()
        if not os.path.isfile(video_file):
            print(f"File not found: {video_file}")
            sys.exit(1)
        return video_file

class RTSPServer:
    def __init__(self, host='0.0.0.0', port=RTSP_PORT, video_file=None):
        self.host = host
        self.port = port
        self.video_file = video_file or get_video_file()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"RTSP Server listening on {self.host}:{self.port}")
        print(f"Streaming video file: {self.video_file}")

    def start(self):
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted connection from {client_address}")
                handler = RTSPHandler(client_socket, self.video_file)
                thread = threading.Thread(target=handler.handle, daemon=True)
                thread.start()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            self.server_socket.close()

if __name__ == '__main__':
    video_file = get_video_file()
    server = RTSPServer(video_file=video_file)
    server.start()
