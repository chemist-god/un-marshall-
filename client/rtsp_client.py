import socket

class RTSPClient:
    def __init__(self, server_ip, server_port=8554, rtp_port=5004, video_file="video"):
        self.server_ip = server_ip
        self.server_port = server_port
        self.rtp_port = rtp_port
        self.video_file = video_file
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.session_id = None
        self.cseq = 1

    def connect(self):
        self.rtsp_socket.connect((self.server_ip, self.server_port))
        print(f"Connected to RTSP server at {self.server_ip}:{self.server_port}")

    def send_request(self, command):
        if command == 'SETUP':
            request = (
                f"SETUP rtsp://{self.server_ip}:{self.server_port}/{self.video_file} RTSP/1.0\r\n"
                f"CSeq: {self.cseq}\r\n"
                f"Transport: RTP/UDP;client_port={self.rtp_port}\r\n"
                "\r\n"
            )
        else:
            request = (
                f"{command} rtsp://{self.server_ip}:{self.server_port}/{self.video_file} RTSP/1.0\r\n"
                f"CSeq: {self.cseq}\r\n"
            )
            if self.session_id:
                request += f"Session: {self.session_id}\r\n"
            request += "\r\n"
        self.rtsp_socket.send(request.encode())
        print(f"Sent RTSP request:\n{request}")
        self.cseq += 1
        response = self.rtsp_socket.recv(1024).decode()
        print(f"Received RTSP response:\n{response}")
        self._parse_response(response)
        return response

    def _parse_response(self, response):
        lines = response.split('\n')
        for line in lines:
            if line.startswith('Session:'):
                self.session_id = line.split(':')[1].strip()

    def close(self):
        self.rtsp_socket.close()
