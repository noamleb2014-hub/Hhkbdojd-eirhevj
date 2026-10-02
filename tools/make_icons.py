#!/usr/bin/env python3
"""Generate the SkyFinder PWA icon set from the brand mark.

Runs during the GitHub Pages build. Renders a 1024px master, then downsamples
to each required size so every icon is crisply antialiased. Artwork is defined
in the same 32x32 coordinate space as the inline SVG logo in index.html.
"""
import os
from PIL import Image, ImageDraw, ImageFilter

OUT = "icons"
MASTER = 1024
VB = 32.0  # viewBox size

CYAN = (60, 232, 207)
VIOLET = (143, 124, 255)
BG_TOP = (8, 13, 29)
BG_BOT = (4, 6, 13)

RING_C = (16.0, 16.0)
RING_R = 14.2
RING_W = 1.4
MOUNTAIN = [(7.0, 22.5), (14.0, 11.0), (17.6, 16.6), (19.9, 13.5), (25.0, 22.5)]
STAR = (23.0, 9.0, 2.4)
SPARK = (9.4, 8.0, 1.2)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def diagonal_gradient(size, c1, c2):
    """Top-left -> bottom-right linear gradient."""
    try:
        import numpy as np
        y, x = np.mgrid[0:size, 0:size]
        t = ((x + y) / (2.0 * (size - 1))).clip(0, 1)
        arr = np.zeros((size, size, 3), dtype=np.uint8)
        for i in range(3):
            arr[..., i] = (c1[i] + (c2[i] - c1[i]) * t).astype(np.uint8)
        return Image.fromarray(arr, "RGB")
    except ImportError:
        big = size * 2
        img = Image.new("RGB", (big, big))
        d = ImageDraw.Draw(img)
        for i in range(big):
            d.line([(i, 0), (i, big)], fill=lerp(c1, c2, i / (big - 1)))
        img = img.rotate(-45, resample=Image.BICUBIC)
        half = size // 2
        c = big // 2
        return img.crop((c - half, c - half, c + half, c + half))


def glow(size, cx, cy, radius, color, alpha):
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = radius * size
    x, y = cx * size, cy * size
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(radius=size * 0.16))


def build_master(art_scale):
    S = MASTER
    base = diagonal_gradient(S, BG_TOP, BG_BOT).convert("RGBA")
    base = Image.alpha_composite(base, glow(S, 0.78, 0.14, 0.40, VIOLET, 62))
    base = Image.alpha_composite(base, glow(S, 0.20, 0.82, 0.36, CYAN, 40))
    base = Image.alpha_composite(base, glow(S, 0.50, 1.02, 0.34, (255, 179, 92), 22))

    span = S * art_scale
    off = (S - span) / 2.0

    def px(x, y):
        return (off + (x / VB) * span, off + (y / VB) * span)

    def u(v):
        return (v / VB) * span

    paint = diagonal_gradient(S, CYAN, VIOLET).convert("RGBA")

    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    rc = px(*RING_C)
    rr = u(RING_R)
    rw = max(2, int(round(u(RING_W))))
    md.ellipse([rc[0] - rr, rc[1] - rr, rc[0] + rr, rc[1] + rr], outline=255, width=rw)
    md.polygon([px(x, y) for x, y in MOUNTAIN], fill=255)
    base = Image.composite(paint, base, mask)

    d = ImageDraw.Draw(base)
    sx, sy, sr = STAR
    c = px(sx, sy)
    r = u(sr)
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=CYAN + (255,))
    px_, py_, pr = SPARK
    c = px(px_, py_)
    r = u(pr)
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 255, 255, 220))
    return base


def save(img, name, size):
    path = os.path.join(OUT, name)
    img.resize((size, size), Image.LANCZOS).save(path, "PNG", optimize=True)
    print("wrote", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    standard = build_master(0.88)
    maskable = build_master(0.78)

    save(standard, "icon-192.png", 192)
    save(standard, "icon-512.png", 512)
    save(standard, "apple-touch-icon.png", 180)
    save(maskable, "icon-512-maskable.png", 512)
    save(standard, "favicon-32.png", 32)

    ico = os.path.join(OUT, "favicon.ico")
    standard.resize((64, 64), Image.LANCZOS).save(
        ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
    )
    print("wrote", ico)


if __name__ == "__main__":
    main()
