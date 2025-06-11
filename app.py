from flask import Flask, Response, send_from_directory, render_template, request, redirect, url_for, session
import cv2
import os
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session management

# Hardcoded user credentials (username: password)
USERS = {
    'admin': 'password123',
    'user': 'cctv456'
}

# Path to video files folder
VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Webcam input (0 is usually the USB webcam)
cap = cv2.VideoCapture(0)

# Video recording parameters
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = 20.0  # Frames per second
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for saved videos
segment_duration = 600  # 10 minutes in seconds

# Global variables for video recording
recording = False
video_writer = None
last_segment_time = time.time()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_video_info(filename):
    try:
        # Extract timestamp from filename (format: recording_YYYY-MM-DD_HH-MM-SS.avi)
        timestamp_str = filename.replace("recording_", "").replace(".avi", "")
        start_time = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
        end_time = start_time + timedelta(seconds=segment_duration)
        return {
            "filename": filename,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "10:00"  # Fixed duration for our segments
        }
    except:
        return {
            "filename": filename,
            "start_time": "Unknown",
            "end_time": "Unknown",
            "duration": "Unknown"
        }

def start_recording():
    global video_writer, last_segment_time, recording
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(VIDEO_DIR, f"recording_{timestamp}.avi")
    
    # Create VideoWriter object
    video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    last_segment_time = time.time()
    recording = True
    print(f"Started recording: {filename}")

def stop_recording():
    global video_writer, recording
    if video_writer is not None:
        video_writer.release()
        video_writer = None
    recording = False
    print("Stopped recording")

def check_recording_segment():
    global last_segment_time
    while True:
        if recording and (time.time() - last_segment_time) >= segment_duration:
            stop_recording()
            start_recording()
        time.sleep(1)

# Start the recording segment checker thread
recording_thread = threading.Thread(target=check_recording_segment, daemon=True)
recording_thread.start()

def generate_frames():
    global video_writer
    
    # Start recording when first client connects
    if not recording:
        start_recording()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        else:
            # Write frame to video file if recording
            if recording and video_writer is not None:
                video_writer.write(frame)
            
            # Convert frame to jpeg and yield it as MJPEG stream
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=session.get('username'))

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/videos/<filename>')
@login_required
def get_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

@app.route('/list_videos')
@login_required
def list_videos():
    files = sorted(os.listdir(VIDEO_DIR), reverse=True)
    video_info = [get_video_info(f) for f in files if f.endswith('.avi')]
    return {'videos': video_info}

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        # Clean up when the application stops
        stop_recording()
        cap.release()
