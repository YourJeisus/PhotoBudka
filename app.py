"""PhotoBudka — Photo booth Flask application."""

import os
import base64
from flask import Flask, render_template, Response, jsonify, request
from camera import Camera
from printer import Printer

app = Flask(__name__)

# Initialize components
camera = Camera()
printer = Printer(paper_size=os.environ.get("PAPER_SIZE", "80mm"))

# Store last captured photo path
last_photo = {"path": None, "filename": None}


@app.route("/")
def index():
    """Main photo booth page."""
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    """MJPEG video stream from camera."""
    if not camera.is_available:
        return "Camera not available", 503
    return Response(
        camera.generate_mjpeg(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/capture", methods=["POST"])
def capture():
    """Capture a photo, save to disk, return base64 image."""
    filename, jpeg_bytes = camera.capture_photo(save_dir="photos")
    if filename is None:
        return jsonify({"success": False, "error": "Camera capture failed"}), 500

    last_photo["path"] = os.path.join("photos", filename)
    last_photo["filename"] = filename

    # Return base64-encoded image for immediate display
    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    return jsonify({
        "success": True,
        "filename": filename,
        "image": f"data:image/jpeg;base64,{b64}",
    })


@app.route("/print", methods=["POST"])
def print_photo():
    """Print the last captured photo."""
    if last_photo["path"] is None:
        return jsonify({"success": False, "error": "No photo to print"}), 400

    if not os.path.exists(last_photo["path"]):
        return jsonify({"success": False, "error": "Photo file not found"}), 404

    success, message = printer.print_image(last_photo["path"])
    return jsonify({"success": success, "message": message})


@app.route("/status")
def status():
    """System status check."""
    return jsonify({
        "camera": camera.is_available,
        "printer": printer.get_status(),
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  PhotoBudka — Photo Booth")
    print("=" * 50)
    print(f"  Camera: {'OK' if camera.is_available else 'NOT FOUND'}")
    print(f"  Printer: {printer.get_status()}")
    print(f"  Open http://localhost:5000")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
