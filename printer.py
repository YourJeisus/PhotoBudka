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

    # Resize to paper width, maintain aspect ratio
    w, h = img.size
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
        """Print image via RAW ESC/POS commands through win32print."""
        try:
            import win32print

            # Convert to 1-bit dithered for thermal
            bw = dither_for_thermal(img)
            w, h = bw.size

            # Build ESC/POS raster bit image command
            # We send the image line by line
            bytes_per_line = (w + 7) // 8
            raw_data = bytearray()

            # ESC @ - Initialize printer
            raw_data += b'\x1b\x40'

            # Center alignment
            raw_data += b'\x1b\x61\x01'

            # Print image using GS v 0 (raster bit image)
            # GS v 0 m xL xH yL yH
            xl = bytes_per_line & 0xFF
            xh = (bytes_per_line >> 8) & 0xFF
            yl = h & 0xFF
            yh = (h >> 8) & 0xFF
            raw_data += b'\x1d\x76\x30\x00'
            raw_data += bytes([xl, xh, yl, yh])

            # Image data: 1 = black in ESC/POS (PIL 1-bit: 0=black, 255=white)
            pixels = bw.load()
            for y_pos in range(h):
                line = bytearray(bytes_per_line)
                for x_pos in range(w):
                    if pixels[x_pos, y_pos] == 0:  # black pixel
                        byte_idx = x_pos // 8
                        bit_idx = 7 - (x_pos % 8)
                        line[byte_idx] |= (1 << bit_idx)
                raw_data += bytes(line)

            # Feed and cut
            raw_data += b'\n\n\n'
            raw_data += b'\x1d\x56\x00'  # GS V 0 - full cut

            # Send RAW data to printer
            hprinter = win32print.OpenPrinter(self.printer_name)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("PhotoBudka", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, bytes(raw_data))
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)

            return True, "Printed successfully"
        except Exception as e:
            return False, f"Print error: {e}"

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
