"""Printer module: GDI printing (Windows) + ESC/POS fallback for thermal printers."""

import io
import os
import sys
from PIL import Image, ImageFilter

# Receipt paper widths in pixels (at 203 DPI for thermal printers)
PAPER_WIDTHS = {
    "58mm": 384,
    "80mm": 576,
}
DEFAULT_PAPER = "80mm"


def prepare_for_print(image_path_or_bytes, paper_width=None):
    """Resize and process image for thermal printing.

    Returns PIL Image resized to paper width with Floyd-Steinberg dithering.
    """
    if paper_width is None:
        paper_width = PAPER_WIDTHS[DEFAULT_PAPER]

    if isinstance(image_path_or_bytes, bytes):
        img = Image.open(io.BytesIO(image_path_or_bytes))
    else:
        img = Image.open(image_path_or_bytes)

    # If image is landscape (wider than tall), rotate 90° so the
    # long side goes along the paper length for maximum size
    w, h = img.size
    if w > h:
        img = img.rotate(90, expand=True)
        w, h = img.size

    # Resize to paper width, maintain aspect ratio
    ratio = paper_width / w
    new_h = int(h * ratio)
    img = img.resize((paper_width, new_h), Image.LANCZOS)

    return img


def dither_for_thermal(img):
    """Convert image to 1-bit with Floyd-Steinberg dithering for thermal printing."""
    grayscale = img.convert("L")
    # Slight contrast enhancement before dithering
    dithered = grayscale.convert("1")  # PIL uses Floyd-Steinberg by default
    return dithered


class Printer:
    def __init__(self, paper_size=DEFAULT_PAPER, printer_name=None):
        self.paper_width = PAPER_WIDTHS.get(paper_size, PAPER_WIDTHS[DEFAULT_PAPER])
        self.paper_size = paper_size
        self.printer_name = printer_name
        self.method = None  # 'gdi' or 'escpos'
        self._detect_method()

    def _detect_method(self):
        """Detect available printing method."""
        if sys.platform == "win32":
            try:
                import win32print
                self.method = "gdi"
                if not self.printer_name:
                    self.printer_name = win32print.GetDefaultPrinter()
                print(f"Printer: GDI mode, using '{self.printer_name}'")
                return
            except ImportError:
                pass

        # Try ESC/POS
        try:
            from escpos.printer import Usb
            self.method = "escpos"
            print("Printer: ESC/POS mode")
            return
        except ImportError:
            pass

        self.method = None
        print("WARNING: No printing backend available. Print will be simulated.")

    @property
    def is_available(self):
        return self.method is not None

    def get_status(self):
        """Return printer status dict."""
        if self.method == "gdi":
            return self._gdi_status()
        elif self.method == "escpos":
            return {"available": True, "method": "escpos", "name": "USB Thermal"}
        return {"available": False, "method": None, "name": None}

    def _gdi_status(self):
        """Check GDI printer status."""
        try:
            import win32print
            handle = win32print.OpenPrinter(self.printer_name)
            info = win32print.GetPrinter(handle, 2)
            win32print.ClosePrinter(handle)
            status = info["Status"]
            return {
                "available": status == 0,
                "method": "gdi",
                "name": self.printer_name,
                "status_code": status,
            }
        except Exception as e:
            return {"available": False, "method": "gdi", "error": str(e)}

    def print_image(self, image_path):
        """Print an image file. Returns (success, message)."""
        if not os.path.exists(image_path):
            return False, f"File not found: {image_path}"

        img = prepare_for_print(image_path, self.paper_width)

        if self.method == "gdi":
            return self._print_gdi(img)
        elif self.method == "escpos":
            return self._print_escpos(img)
        else:
            return self._print_simulated(image_path)

    def _print_gdi(self, img):
        """Print using Windows GDI."""
        try:
            import win32print
            import win32ui
            from PIL import ImageWin

            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(self.printer_name)

            hdc.StartDoc("PhotoBudka")
            hdc.StartPage()

            # Get printer page size
            page_w = hdc.GetDeviceCaps(110)  # PHYSICALWIDTH
            page_h = hdc.GetDeviceCaps(111)  # PHYSICALHEIGHT

            # Scale image to fit page width
            w, h = img.size
            ratio = min(page_w / w, page_h / h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)

            # Center horizontally
            x = (page_w - new_w) // 2
            y = 0

            dib = ImageWin.Dib(img)
            dib.draw(hdc.GetHandleOutput(), (x, y, x + new_w, y + new_h))

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()

            return True, "Printed successfully via GDI"
        except Exception as e:
            return False, f"GDI print error: {e}"

    def _print_escpos(self, img):
        """Print using ESC/POS commands."""
        try:
            from escpos.printer import Usb

            # Common vendor/product IDs for thermal printers
            # User may need to adjust these
            p = Usb(0x0416, 0x5011)

            # Dither for thermal
            dithered = dither_for_thermal(img)

            p.image(dithered)
            p.cut()

            return True, "Printed successfully via ESC/POS"
        except Exception as e:
            return False, f"ESC/POS print error: {e}"

    def _print_simulated(self, image_path):
        """Simulate printing (for development on non-Windows)."""
        print(f"[SIMULATED PRINT] Would print: {image_path}")
        return True, "Print simulated (no printer backend available)"
