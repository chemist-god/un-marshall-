import socket
import threading
import cv2
import numpy as np

class VideoReceiver:
    def __init__(self, rtp_port=5004):
        self.rtp_port = rtp_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.rtp_port))
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.sock.close()

    def receive_loop(self):
        print(f"Listening for RTP packets on UDP port {self.rtp_port}")
        while self.running:
            try:
                data, _ = self.sock.recvfrom(65536)  # Max UDP packet size
                if len(data) < 12:
                    continue  # Not a valid RTP packet
                # RTP header is 12 bytes
                payload = data[12:]
                # Decode JPEG frame
                frame = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow('RTSP Client Video', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.stop()
                        break
            except Exception as e:
                print(f"Error receiving RTP packet: {e}")
                break
        cv2.destroyAllWindows()
