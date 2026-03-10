#!/usr/bin/env python3
"""Generate PWA icons for the Marvel Comic Reader."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

SIZES = {
    "icon-192.png": 192,
    "icon-512.png": 512,
}

BG_COLOR = (10, 10, 15)        # #0a0a0f
ACCENT   = (200, 50, 50)       # Red X accent
TEXT_COL = (255, 255, 255)


def generate_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # Draw a bold "X" in red
    margin = int(size * 0.15)
    lw = max(int(size * 0.12), 4)
    draw.line([(margin, margin), (size - margin, size - margin)], fill=ACCENT, width=lw)
    draw.line([(size - margin, margin), (margin, size - margin)], fill=ACCENT, width=lw)

    # Draw a small book emoji-like shape at center
    cx, cy = size // 2, size // 2
    bw, bh = int(size * 0.28), int(size * 0.22)
    draw.rectangle(
        [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2],
        fill=(30, 30, 50), outline=(100, 100, 140), width=max(lw // 3, 1),
    )
    # Spine line
    draw.line([(cx, cy - bh // 2), (cx, cy + bh // 2)], fill=(100, 100, 140), width=max(lw // 4, 1))

    return img


def main():
    for name, size in SIZES.items():
        icon = generate_icon(size)
        path = WEB_DIR / name
        icon.save(str(path), "PNG")
        print(f"  ✓ {path.name}  ({size}×{size})")


if __name__ == "__main__":
    main()
