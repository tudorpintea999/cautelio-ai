"""
Run once to generate extension icons:
  pip install Pillow
  python extension/icons/create_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZES = [16, 48, 128]
BG = (10, 10, 15, 255)
RED = (230, 57, 70, 255)
WHITE = (232, 232, 232, 255)
OUT = Path(__file__).parent


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG)
    d = ImageDraw.Draw(img)

    # Red rounded rectangle border
    pad = max(1, size // 10)
    d.rounded_rectangle([pad, pad, size - pad - 1, size - pad - 1],
                        radius=max(2, size // 8),
                        outline=RED,
                        width=max(1, size // 16))

    # "C" letter centered
    font_size = max(8, int(size * 0.45))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = d.textbbox((0, 0), "C", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
           "C", fill=WHITE, font=font)

    return img


for s in SIZES:
    path = OUT / f"icon{s}.png"
    draw_icon(s).save(path)
    print(f"Created {path}")
