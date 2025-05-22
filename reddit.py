import subprocess
import threading
import time
import io
import cv2
import numpy as np
from PIL import Image
import sys
import termios
import tty
import os
import ntplib
from time import ctime
from datetime import datetime
import platform

RTSP_URL = "" # ENTER YOUR RTSP CAMERA STREAM
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080

latest_frame = None
frame_lock = threading.Lock()
frame_counter = 0

def read_frames():
    global latest_frame, frame_counter
    print("[INFO] Starting FFmpeg subprocess...")
    proc = subprocess.Popen([
        "ffmpeg",
        
        "-rtsp_transport", "udp",
        "-i", RTSP_URL,
        "-an",
        "-f", "image2pipe",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ], stdout=subprocess.PIPE)

    frame_size = FRAME_WIDTH * FRAME_HEIGHT * 3

    while True:
        raw = proc.stdout.read(frame_size)
        if not raw:
            break
        try:
            frame = np.frombuffer(raw, np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))
            with frame_lock:
                latest_frame = frame.copy()
            global frame_counter
            frame_counter += 1
        except Exception as e:
            print(f"[ERROR] Frame decode failed: {e}")

def get_ntp_time():
    start_time = time.time()  # float, seconds with fractions
    print("[ATOMIC TIMESTAMP]System time before request:", datetime.fromtimestamp(start_time).strftime('%H:%M:%S.%f')[:-3])
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')  # or other reliable NTP server
    end_time = time.time()
    print("[ATOMIC TIMESTAMP]System time after response:", datetime.fromtimestamp(end_time).strftime('%H:%M:%S.%f')[:-3])
    loss_ms = (end_time - start_time) * 1000
    print(f"[ATOMIC TIMESTAMP]Atomic timestamp time loss: {loss_ms:.3f} ms")
    # response.tx_time is a float timestamp with fractional seconds
    dt = datetime.fromtimestamp(response.tx_time)
    return dt.strftime('%H:%M:%S.%f')[:-3]  # formatted to milliseconds

def live_fps_display():
    last_count = 0
    while True:
        time.sleep(1)
        current = frame_counter
        fps = current - last_count
        last_count = current
        # Clear the line and print updated live stats in place
        print(f"\r\033[K[INFO] Frames: {current} | FPS: {fps}", end='', flush=True)

def key_listener():
    print("[INFO] Press any key to capture a frame, or press 'q' to quit...")
    while True:
        key = get_keypress()
        if key == 'q':
            print("\n[EXIT] Quit signal received. Exiting...")
            os._exit(0)
        elif key:
            print()
            ntp_1 = get_ntp_time()
            print("[KEY PRESSED] Atomic timestamp:",ntp_1," → Capturing frame...")
            capture_frame(ntp_1)
            print("[INFO] Press any key to capture a frame, or press 'q' to quit...", end='')
  
def get_keypress():
    if platform.system() == "Windows":
        import msvcrt
        return msvcrt.getch().decode('utf-8')
    else:
        import sys
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def capture_frame(ntp_1):
    with frame_lock:
        frame = latest_frame.copy() if latest_frame is not None else None

    if frame is None:
        print("[WARN] No frame available yet.")
        return

    buffer = io.BytesIO()
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    pil.save(buffer, format="JPEG", quality=85)
    ntp_2 = get_ntp_time()
    fmt = "%H:%M:%S.%f"
    t1 = datetime.strptime(ntp_1, fmt)
    t2 = datetime.strptime(ntp_2, fmt)
    diff = (t2 - t1).total_seconds() * 1000  # in milliseconds
    print("[SCREENSHOT STORED] Atomic timestamp:",ntp_2, buffer,f"| JPEG Size: {len(buffer.getvalue())} bytes | Took: {diff:.2f} ms\n\n")
    print("[INFO] Press any key to capture a frame, or press 'q' to quit...")

    with open("preview.jpg", "wb") as f:
        f.write(buffer.getvalue())

    # Open the image depending on the OS
    if platform.system() == "Darwin":  # macOS
        subprocess.run(["open", "preview.jpg"])
    elif platform.system() == "Windows":
        os.startfile("preview.jpg")
    else:  # Linux and others
        subprocess.run(["xdg-open", "preview.jpg"])

# Start threads
threading.Thread(target=read_frames, daemon=True).start()
threading.Thread(target=live_fps_display, daemon=True).start()
threading.Thread(target=key_listener, daemon=True).start()

# Keep main thread alive
while True:
    time.sleep(1)
