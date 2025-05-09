import cv2
import time
from datetime import datetime
import os

# Folder to save videos
VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Webcam input (0 is usually USB webcam)
cap = cv2.VideoCapture(0)

# Check resolution
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = 20.0  # Frames per second
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec

# How long each video segment should be (in seconds)
segment_time = 10 * 60  # 10 minutes

def get_filename():
    now = datetime.now()
    return os.path.join(VIDEO_DIR, now.strftime("%Y-%m-%d_%H-%M-%S") + ".avi")

print("📹 Recording started...")
out = cv2.VideoWriter(get_filename(), fourcc, fps, (width, height))
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠ Frame not captured!")
        break

    out.write(frame)

    # If segment time passed, start a new file
    if time.time() - start_time > segment_time:
        out.release()
        out = cv2.VideoWriter(get_filename(), fourcc, fps, (width, height))
        start_time = time.time()

# Cleanup
cap.release()
out.release()
print("📼 Recording stopped.")