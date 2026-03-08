"""Print a poem on POS-58 thermal printer via GDI (Windows).

Auto-fits font size so every line fits without wrapping.
Minimal margins. Uses the same GDI approach as printer.py.
"""

import sys
from PIL import Image, ImageDraw, ImageFont

# --- CONFIG ---
PRINTER_NAME = "POS-58(copy of 1)"
PAPER_WIDTH_PX = 384  # 58mm @ 203 DPI
MARGIN = 8  # minimal side margin in pixels
LINE_SPACING = 4  # extra pixels between lines
STANZA_SPACING = 16  # extra pixels between stanzas (blank lines)
TOP_MARGIN = 16
BOTTOM_MARGIN = 24

POEM_LINES = [
    ("В каждом слове есть смысл", "left"),
    ("В каждом букете тоже.", "left"),
    ("Раньше тут были ромашки,", "left"),
    ("Теперь на тебя не похожи.", "left"),
    ("", "blank"),
    ("Ты выглядеть стала моложе", "left"),
    ("Как солнечный, рыжий апрель", "left"),
    ("И россыпь веснушек на коже", "left"),
    ("Как будто цветочная пыль", "left"),
    ("", "blank"),
    ("Москва встречает рассвет!", "left"),
    ("И ты ее луч единственный.", "left"),
    ("Может это не самый большой букет,", "left"),
    ("Но точно он самый искренний!", "left"),
    ("", "blank"),
    ("С 8 марта, Анют!", "center"),
]

# "ВМЕСТО ОТКРЫТКИ" prints below with big gap so you fold the receipt
# and it shows on the back like a card cover
FOOTER_TEXT = "ВМЕСТО ОТКРЫТКИ"
FOOTER_GAP = 300  # pixels gap before footer (adjust for fold point)


def get_font_path():
    """Get a font path that supports Cyrillic."""
    import os
    candidates = [
        "arial.ttf",  # Windows
        "C:\\Windows\\Fonts\\arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def find_best_font_size(lines, max_width, font_path=None):
    """Find the largest font size where every line fits within max_width."""
    if font_path is None:
        font_path = get_font_path()
    for size in range(40, 6, -1):
        try:
            if font_path:
                font = ImageFont.truetype(font_path, size)
            else:
                font = ImageFont.load_default()
                return font, 12
        except (OSError, IOError):
            font = ImageFont.load_default()
            return font, 12

        # Check if ALL lines fit
        tmp = Image.new("L", (1, 1))
        draw = ImageDraw.Draw(tmp)
        fits = True
        for line in lines:
            if line.strip() == "":
                continue
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            if text_w > max_width:
                fits = False
                break
        if fits:
            return font, size

    # Fallback to smallest
    try:
        font = ImageFont.truetype("arial.ttf", 7)
    except (OSError, IOError):
        font = ImageFont.load_default()
    return font, 7


def render_poem():
    """Render poem to a PIL Image sized for thermal printing."""
    text_lines = [text for text, _ in POEM_LINES]
    usable_width = PAPER_WIDTH_PX - 2 * MARGIN

    font, font_size = find_best_font_size(text_lines, usable_width)
    print(f"Auto-selected font size: {font_size}px")

    # Calculate line height
    tmp = Image.new("L", (1, 1))
    draw = ImageDraw.Draw(tmp)
    line_height = draw.textbbox((0, 0), "Щф", font=font)[3] + LINE_SPACING

    # Calculate total height: poem + gap + footer
    total_height = TOP_MARGIN
    for text, align in POEM_LINES:
        if align == "blank":
            total_height += STANZA_SPACING
        else:
            total_height += line_height

    # Footer font (for "ВМЕСТО ОТКРЫТКИ") — find size that fits
    footer_lines = [FOOTER_TEXT]
    footer_font, footer_size = find_best_font_size(footer_lines, usable_width)
    footer_height = draw.textbbox((0, 0), FOOTER_TEXT, font=footer_font)[3]

    total_height += FOOTER_GAP + footer_height + BOTTOM_MARGIN

    # Render
    img = Image.new("L", (PAPER_WIDTH_PX, total_height), 255)
    draw = ImageDraw.Draw(img)

    y = TOP_MARGIN
    for text, align in POEM_LINES:
        if align == "blank":
            y += STANZA_SPACING
            continue

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]

        if align == "center":
            x = (PAPER_WIDTH_PX - text_w) // 2
        else:
            x = MARGIN

        draw.text((x, y), text, fill=0, font=font)
        y += line_height

    # Footer: "ВМЕСТО ОТКРЫТКИ" centered after big gap
    y += FOOTER_GAP
    bbox = draw.textbbox((0, 0), FOOTER_TEXT, font=footer_font)
    text_w = bbox[2] - bbox[0]
    x = (PAPER_WIDTH_PX - text_w) // 2
    draw.text((x, y), FOOTER_TEXT, fill=0, font=footer_font)

    return img


def print_gdi(img, printer_name):
    """Print image via Windows GDI."""
    import win32print
    import win32ui
    from PIL import ImageWin

    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)
    hdc.StartDoc("Poem")
    hdc.StartPage()

    page_w = hdc.GetDeviceCaps(110)  # PHYSICALWIDTH
    page_h = hdc.GetDeviceCaps(111)  # PHYSICALHEIGHT

    w, h = img.size
    ratio = min(page_w / w, page_h / h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)

    x = (page_w - new_w) // 2
    y = 0

    dib = ImageWin.Dib(img)
    dib.draw(hdc.GetHandleOutput(), (x, y, x + new_w, y + new_h))

    hdc.EndPage()
    hdc.EndDoc()
    hdc.DeleteDC()
    print("Printed!")


def main():
    img = render_poem()

    # Save preview
    img.save("poem_preview.png")
    print(f"Preview saved: poem_preview.png ({img.size[0]}x{img.size[1]})")

    if sys.platform == "win32":
        printer = PRINTER_NAME
        if len(sys.argv) > 1 and sys.argv[1] == "--no-print":
            print("Skipping print (--no-print)")
            return
        try:
            print_gdi(img, printer)
        except Exception as e:
            print(f"Print error: {e}")
            print("Run with --no-print to just generate preview")
    else:
        print("Not on Windows — preview only (no GDI printing)")


if __name__ == "__main__":
    main()
