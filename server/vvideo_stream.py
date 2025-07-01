import cv2

class VideoStream:
    def __init__(self, video_file):
        self.cap = cv2.VideoCapture(video_file)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open video file: {video_file}")

    def get_next_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None
        # Encode frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return jpeg.tobytes()

    def release(self):
        self.cap.release()
