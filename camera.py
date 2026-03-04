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
        self._init_camera()

    def _init_camera(self):
        """Initialize camera. Supports IP camera URL or USB index."""
        # Try explicit source first (URL or index)
        if self.source is not None:
            self.cap = cv2.VideoCapture(self.source)
            if self.cap.isOpened():
                self._configure()
                print(f"Camera connected: {self.source}")
                return

        # Try IP camera from environment variable
        ip_url = os.environ.get("CAMERA_URL")
        if ip_url:
            self.cap = cv2.VideoCapture(ip_url)
            if self.cap.isOpened():
                self.source = ip_url
                self._configure()
                print(f"IP camera connected: {ip_url}")
                return

        # Try default IP camera (kiosk)
        default_ip = "rtsp://admin:123456@192.168.1.30:554/stream1"
        cap = cv2.VideoCapture(default_ip)
        if cap.isOpened():
            self.cap = cap
            self.source = default_ip
            self._configure()
            print(f"IP camera connected: {default_ip}")
            return
        cap.release()

        # Fallback: auto-detect USB camera (indices 0-4)
        for idx in range(5):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self.cap = cap
                self.source = idx
                self._configure()
                print(f"USB camera found at index {idx}")
                return
            cap.release()

        print("WARNING: No camera found. Running in no-camera mode.")
        self.cap = None

    def _configure(self):
        """Set camera resolution."""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    @property
    def is_available(self):
        return self.cap is not None and self.cap.isOpened()

    def _reconnect(self):
        """Reconnect to camera if stream dropped."""
        if self.source is not None:
            print(f"Reconnecting to camera: {self.source}")
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.source)
            if self.cap.isOpened():
                self._configure()
                print("Camera reconnected")

    def read_frame(self):
        """Read a single frame, return as numpy array or None."""
        if not self.is_available:
            self._reconnect()
            if not self.is_available:
                return None
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                # Stream may have dropped — try reconnect
                self._reconnect()
                return self.last_frame  # return cached frame while reconnecting
            # Mirror horizontally for natural selfie view
            frame = cv2.flip(frame, 1)
            self.last_frame = frame
            return frame

    def get_jpeg(self, quality=80):
        """Capture a frame and return JPEG bytes."""
        frame = self.read_frame()
        if frame is None:
            return None
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        ret, jpeg = cv2.imencode('.jpg', frame, encode_params)
        if ret:
            return jpeg.tobytes()
        return None

    def capture_photo(self, save_dir="photos"):
        """Capture a high-quality photo, save to disk, return (filename, jpeg_bytes)."""
        frame = self.read_frame()
        if frame is None:
            return None, None

        os.makedirs(save_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)

        # Save high-quality JPEG
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # Also return as bytes for immediate display
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        jpeg_bytes = jpeg.tobytes() if ret else None

        return filename, jpeg_bytes

    def generate_mjpeg(self):
        """Generator for MJPEG streaming."""
        while True:
            jpeg = self.get_jpeg(quality=70)
            if jpeg is None:
                # Send a placeholder frame if camera unavailable
                time.sleep(0.1)
                continue
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n'
            )
            time.sleep(0.033)  # ~30 FPS

    def release(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
