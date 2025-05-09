from flask import Flask, Response, send_from_directory, render_template
import cv2
import os

app = Flask(_name_)

# Path to video files folder
VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Webcam input (0 is usually the USB webcam)
cap = cv2.VideoCapture(0)

# Check resolution and set frame rate
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = 20.0  # Frames per second
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for saved videos

def generate_frames():
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        else:
            # Convert frame to jpeg and yield it as MJPEG stream
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/videos/<filename>')
def get_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

@app.route('/list_videos')
def list_videos():
    files = os.listdir(VIDEO_DIR)
    return {'files': files}

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000)