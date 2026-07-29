import re
import urllib.request
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT = Path(r"C:\Users\alekic\Documents\GitHub\Control-of-HVDC-AC-Power-Systems\assets\projects")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


for url in ["https://cresym.eu/harmony/", "https://cresym.eu/", "https://github.com/CRESYM/Harmony"]:
    try:
        html = fetch(url).decode("utf-8", "replace")
        imgs = sorted(set(re.findall(r"https?://[^\"'\s>]+\.(?:png|jpg|jpeg|svg|webp)", html, re.I)))
        print("===", url)
        for u in imgs:
            if re.search(r"logo|harmon|cresym", u, re.I):
                print(" ", u)
    except Exception as e:
        print("fail", url, e)

# Crop existing CRESYM/Harmony assets tightly and rebuild cards
src = Image.open(ROOT / "harmony-cresym.png").convert("RGBA")
arr = np.array(src)
rgb = arr[:, :, :3].astype(np.int16)
a = arr[:, :, 3]
# content = not near-black
content = (rgb.max(axis=2) > 25) & (a > 10)
ys, xs = np.where(content)
print("harmony-cresym bbox", xs.min(), ys.min(), xs.max(), ys.max(), "size", src.size)
bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
cropped = src.crop(bbox)
carr = np.array(cropped)
crgb = carr[:, :, :3].astype(np.int16)
is_bg = crgb.max(axis=2) < 25
carr[:, :, 3] = np.where(is_bg, 0, np.maximum(carr[:, :, 3], 220)).astype(np.uint8)
cropped = Image.fromarray(carr, "RGBA")
pad = 48
canvas = Image.new("RGBA", (cropped.width + 2 * pad, cropped.height + 2 * pad), (0, 0, 0, 0))
canvas.paste(cropped, (pad, pad), cropped)
canvas.save(ROOT / "harmony-cresym.png")
print("saved harmony-cresym.png", canvas.size)

# Card
W, H = 1200, 750
bg = Image.new("RGBA", (W, H), (247, 250, 249, 255))
logo = canvas.copy()
logo.thumbnail((int(W * 0.72), int(H * 0.82)), Image.Resampling.LANCZOS)
x = (W - logo.width) // 2
y = (H - logo.height) // 2
bg.alpha_composite(logo, (x, y))
bg.convert("RGB").save(ROOT / "harmony-card.jpg", quality=93, optimize=True)
print("saved harmony-card.jpg", logo.size)

# Same for BiGER card which uses identical cresym-biger.png
src2 = Image.open(ROOT / "cresym-biger.png").convert("RGBA")
arr = np.array(src2)
rgb = arr[:, :, :3].astype(np.int16)
a = arr[:, :, 3]
content = (rgb.max(axis=2) > 25) & (a > 10)
ys, xs = np.where(content)
bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
cropped = src2.crop(bbox)
carr = np.array(cropped)
crgb = carr[:, :, :3].astype(np.int16)
is_bg = crgb.max(axis=2) < 25
carr[:, :, 3] = np.where(is_bg, 0, np.maximum(carr[:, :, 3], 220)).astype(np.uint8)
cropped = Image.fromarray(carr, "RGBA")
pad = 48
canvas = Image.new("RGBA", (cropped.width + 2 * pad, cropped.height + 2 * pad), (0, 0, 0, 0))
canvas.paste(cropped, (pad, pad), cropped)
canvas.save(ROOT / "cresym-biger.png")
bg = Image.new("RGBA", (W, H), (247, 250, 249, 255))
logo = canvas.copy()
logo.thumbnail((int(W * 0.72), int(H * 0.82)), Image.Resampling.LANCZOS)
x = (W - logo.width) // 2
y = (H - logo.height) // 2
bg.alpha_composite(logo, (x, y))
bg.convert("RGB").save(ROOT / "biger-explore-card.jpg", quality=93, optimize=True)
print("also refreshed biger card")
