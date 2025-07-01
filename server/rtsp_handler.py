import threading
from vvideo_stream import VideoStream
import time
import socket
import struct

class RTSPHandler:
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.video_file = None # Will be set in SETUP
        self.session_id = 123456  # For simplicity, use a static session ID
        self.is_streaming = False
        self.client_address = client_socket.getpeername()
        self.video_stream = None
        self.stream_thread = None
        self.stream_thread_stop = threading.Event()
        self.rtp_socket = None
        self.client_rtp_port = None
        self.sequence_number = 0
        self.timestamp = 0

    def handle(self):
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                request = data.decode()
                print(f"Received RTSP request from {self.client_address}:\n{request}")
                self.process_request(request)
        except Exception as e:
            print(f"Error handling client {self.client_address}: {e}")
        finally:
            self.stop_streaming()
            self.client_socket.close()
            print(f"Connection closed for {self.client_address}")

    def process_request(self, request):
        lines = request.strip().split('\n')
        if not lines:
            return
        request_line = lines[0]
        parts = request_line.split()
        if len(parts) < 2:
            return
        command = parts[0]
        cseq = None
        for line in lines:
            if line.startswith('CSeq:'):
                cseq = line.split(':')[1].strip()
                break
        if command == 'SETUP':
            # Extract video file from request line: SETUP rtsp://.../video_file RTSP/1.0
            self.video_file = parts[1].split('/')[-1]
            print(f"Client requested to stream file: {self.video_file}")
            self.handle_setup(cseq, lines)
        elif command == 'PLAY':
            self.handle_play(cseq)
        elif command == 'PAUSE':
            self.handle_pause(cseq)
        elif command == 'TEARDOWN':
            self.handle_teardown(cseq)
        else:
            self.send_response(cseq, 400, 'Bad Request')

    def handle_setup(self, cseq, lines):
        print("Handling SETUP")
        # Parse client RTP port from Transport header
        for line in lines:
            if line.startswith('Transport:'):
                # Example: Transport: RTP/UDP;client_port=5004
                parts = line.split(';')
                for part in parts:
                    if part.strip().startswith('client_port='):
                        self.client_rtp_port = int(part.strip().split('=')[1])
        if not self.video_stream:
            self.video_stream = VideoStream(self.video_file)
        if not self.rtp_socket:
            self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_response(cseq, 200, 'OK', extra_headers=f'Session: {self.session_id}')

    def handle_play(self, cseq):
        print("Handling PLAY")
        if not self.is_streaming:
            self.is_streaming = True
            self.stream_thread_stop.clear()
            self.stream_thread = threading.Thread(target=self.stream_video, daemon=True)
            self.stream_thread.start()
        self.send_response(cseq, 200, 'OK', extra_headers=f'Session: {self.session_id}')

    def handle_pause(self, cseq):
        print("Handling PAUSE")
        self.is_streaming = False
        self.stop_streaming()
        self.send_response(cseq, 200, 'OK', extra_headers=f'Session: {self.session_id}')

    def handle_teardown(self, cseq):
        print("Handling TEARDOWN")
        self.is_streaming = False
        self.stop_streaming()
        self.send_response(cseq, 200, 'OK', extra_headers=f'Session: {self.session_id}')

    def stop_streaming(self):
        self.stream_thread_stop.set()
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join()
        if self.video_stream:
            self.video_stream.release()
            self.video_stream = None
        if self.rtp_socket:
            self.rtp_socket.close()
            self.rtp_socket = None

    def stream_video(self):
        print(f"Starting video stream to {self.client_address}")
        if not self.client_rtp_port:
            print("No client RTP port specified. Cannot stream.")
            return
        client_ip = self.client_address[0]
        while not self.stream_thread_stop.is_set():
            frame = self.video_stream.get_next_frame()
            if frame is None:
                print("End of video or error reading frame.")
                break
            # Packetize and send as RTP
            rtp_packet = self.create_rtp_packet(frame)
            self.rtp_socket.sendto(rtp_packet, (client_ip, self.client_rtp_port))
            print(f"Sent RTP packet of size {len(rtp_packet)} bytes to {client_ip}:{self.client_rtp_port}")
            time.sleep(1/25)  # Simulate 25 FPS
        print(f"Stopped video stream to {self.client_address}")

    def create_rtp_packet(self, payload):
        # Minimal RTP header: Version(2b),P(1b),X(1b),CC(4b),M(1b),PT(7b),SeqNum(16b),Timestamp(32b),SSRC(32b)
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        payload_type = 26  # JPEG
        seqnum = self.sequence_number & 0xFFFF
        timestamp = self.timestamp
        ssrc = 12345  # Arbitrary SSRC
        header = struct.pack('!BBHII',
            (version << 6) | (padding << 5) | (extension << 4) | cc,
            (marker << 7) | payload_type,
            seqnum,
            timestamp,
            ssrc
        )
        self.sequence_number += 1
        self.timestamp += 3600  # Arbitrary increment for demo
        return header + payload

    def send_response(self, cseq, code, message, extra_headers=None):
        response = f"RTSP/1.0 {code} {message}\r\nCSeq: {cseq}\r\n"
        if extra_headers:
            response += f"{extra_headers}\r\n"
        response += "\r\n"
        self.client_socket.send(response.encode())
