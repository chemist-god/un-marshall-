from rtsp_client import RTSPClient
from video_stream import VideoReceiver
import time
import requests
import os

UPLOAD_PORT = 8080
UPLOAD_ENDPOINT = '/'

if __name__ == '__main__':
    SERVER_IP = '127.0.0.1'
    RTSP_PORT = 8554
    RTP_PORT = 5004

    # Prompt user for video file to upload
    video_path = input('Enter the path to the video file to upload and stream: ').strip()
    if not os.path.isfile(video_path):
        print(f'File not found: {video_path}')
        exit(1)

    # Upload the file to the server
    upload_url = f'http://{SERVER_IP}:{UPLOAD_PORT}{UPLOAD_ENDPOINT}'
    with open(video_path, 'rb') as f:
        files = {'file': (os.path.basename(video_path), f, 'application/octet-stream')}
        print(f'Uploading {video_path} to {upload_url}...')
        response = requests.post(upload_url, files=files)
        if response.status_code == 200:
            print('Upload successful.')
        else:
            print(f'Upload failed: {response.text}')
            exit(1)

    remote_video_path = f"uploads/{os.path.basename(video_path)}"
    # Create RTSP client and video receiver
    rtsp_client = RTSPClient(SERVER_IP, RTSP_PORT, RTP_PORT, remote_video_path)
    video_receiver = VideoReceiver(RTP_PORT)

    try:
        rtsp_client.connect()
        rtsp_client.send_request('SETUP')
        video_receiver.start()
        rtsp_client.send_request('PLAY')
        print('Streaming video... Press Q in the video window to quit.')
        # Keep the main thread alive while video is playing
        while video_receiver.thread and video_receiver.thread.is_alive():
            time.sleep(0.5)
        rtsp_client.send_request('TEARDOWN')
    except KeyboardInterrupt:
        print('Interrupted by user.')
        rtsp_client.send_request('TEARDOWN')
    finally:
        video_receiver.stop()
        rtsp_client.close()
        print('Client exited.')
