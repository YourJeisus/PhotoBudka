"""Camera module: OpenCV-based capture and MJPEG streaming."""

import cv2
import threading
import time
import os


class Camera:
    def __init__(self, source=None):
        self.lock = threading.Lock()
        self.cap = None
        self.source = source
        self.last_frame = None
        self._running = False
        self._grab_thread = None
        self._init_camera()

    def _init_camera(self):
        """Initialize camera. Supports IP camera URL or USB index."""
        # Try explicit source first (URL or index)
        if self.source is not None:
            if self._try_open(self.source):
                return

        # Try IP camera from environment variable
        ip_url = os.environ.get("CAMERA_URL")
        if ip_url and self._try_open(ip_url):
            return

        # Try default IP camera (kiosk)
        default_ip = "rtsp://admin:123456@192.168.1.30:554/stream1"
        if self._try_open(default_ip):
            return

        # Fallback: auto-detect USB camera (indices 0-4)
        for idx in range(5):
            if self._try_open(idx):
                return

        print("WARNING: No camera found. Running in no-camera mode.")

    def _try_open(self, source):
        """Try to open a camera source. Returns True on success."""
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            self.cap = cap
            self.source = source
            self._configure()
            self._start_grab_thread()
            print(f"Camera connected: {source}")
            return True
        cap.release()
        return False

    def _configure(self):
        """Set camera properties for low latency."""
        if self.cap:
            # Reduce buffer to 1 frame for minimal latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def _start_grab_thread(self):
        """Start background thread that continuously grabs frames."""
        self._running = True
        self._grab_thread = threading.Thread(target=self._grab_loop, daemon=True)
        self._grab_thread.start()

    def _grab_loop(self):
        """Continuously grab frames to keep buffer fresh."""
        while self._running:
            if self.cap and self.cap.isOpened():
                with self.lock:
                    ret, frame = self.cap.read()
                if ret:
                    # Mirror horizontally for natural selfie view
                    frame = cv2.flip(frame, 1)
                    self.last_frame = frame
                else:
                    self._reconnect()
                    time.sleep(1)
            else:
                time.sleep(0.5)
            # Small sleep to not hog CPU, ~30 FPS
            time.sleep(0.01)

    def _reconnect(self):
        """Reconnect to camera if stream dropped."""
        if self.source is not None:
            print(f"Reconnecting to camera: {self.source}")
            with self.lock:
                if self.cap:
                    self.cap.release()
                self.cap = cv2.VideoCapture(self.source)
                if self.cap.isOpened():
                    self._configure()
                    print("Camera reconnected")

    @property
    def is_available(self):
        return self.last_frame is not None

    def read_frame(self):
        """Return the latest frame (grabbed by background thread)."""
        return self.last_frame

    def get_jpeg(self, quality=80):
        """Return latest frame as JPEG bytes."""
        frame = self.last_frame
        if frame is None:
            return None
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ret:
            return jpeg.tobytes()
        return None

    def capture_photo(self, save_dir="photos"):
        """Capture a high-quality photo, save to disk, return (filename, jpeg_bytes)."""
        frame = self.last_frame
        if frame is None:
            return None, None

        os.makedirs(save_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)

        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        jpeg_bytes = jpeg.tobytes() if ret else None

        return filename, jpeg_bytes

    def generate_mjpeg(self):
        """Generator for MJPEG streaming."""
        while True:
            jpeg = self.get_jpeg(quality=70)
            if jpeg is None:
                time.sleep(0.1)
                continue
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n'
            )
            time.sleep(0.033)  # ~30 FPS

    def release(self):
        """Release camera resources."""
        self._running = False
        if self._grab_thread:
            self._grab_thread.join(timeout=2)
        if self.cap:
            self.cap.release()
