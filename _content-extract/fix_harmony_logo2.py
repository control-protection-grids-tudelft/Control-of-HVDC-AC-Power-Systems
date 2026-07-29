from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import urllib.request
import re
import numpy as np

ROOT = Path(r"C:\Users\alekic\Documents\GitHub\Control-of-HVDC-AC-Power-Systems\assets\projects")

req = urllib.request.Request("https://cresym.eu/harmony/", headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
uploads = sorted(set(re.findall(r"https://cresym\.eu/wp-content/uploads/[^\s\"']+", html)))
print("uploads on harmony page:")
for u in uploads:
    print(" ", u)

# Use official full PNG; remove white/transparent and gray mats by luminance clustering on border
req = urllib.request.Request(
    "https://cresym.eu/wp-content/uploads/2023/01/PNG.png",
    headers={"User-Agent": "Mozilla/5.0"},
)
data = urllib.request.urlopen(req, timeout=45).read()
(ROOT / "cresym-official.png").write_bytes(data)
im = Image.open(ROOT / "cresym-official.png").convert("RGBA")
arr = np.array(im)
r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

# Background candidates: white-ish OR very dark OR mid gray with low chroma
chroma = np.maximum(np.maximum(r, g), b).astype(int) - np.minimum(np.minimum(r, g), b).astype(int)
is_white = (r > 245) & (g > 245) & (b > 245)
is_black = (r < 12) & (g < 12) & (b < 12)
is_gray = (chroma < 18) & (r > 80) & (r < 210)
is_bg = (a < 15) | is_white | is_black | is_gray
is_fg = ~is_bg

# Keep only largest connected? Use density rows/cols of fg
row = is_fg.sum(axis=1)
col = is_fg.sum(axis=0)
# require substantial occupancy
thr_r = max(30, int(row.max() * 0.04))
thr_c = max(30, int(col.max() * 0.04))
ys = np.where(row >= thr_r)[0]
xs = np.where(col >= thr_c)[0]
print("fg frac", float(is_fg.mean()), "mass", xs[0], ys[0], xs[-1], ys[-1])

x0, y0, x1, y1 = int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1
cropped = arr[y0:y1, x0:x1].copy()
# make bg transparent inside crop
cr, cg, cb, ca = cropped[:, :, 0], cropped[:, :, 1], cropped[:, :, 2], cropped[:, :, 3]
chroma = np.maximum(np.maximum(cr, cg), cb).astype(int) - np.minimum(np.minimum(cr, cg), cb).astype(int)
bg2 = (ca < 15) | ((cr > 245) & (cg > 245) & (cb > 245)) | ((cr < 12) & (cg < 12) & (cb < 12)) | ((chroma < 18) & (cr > 80) & (cr < 210))
cropped[:, :, 3] = np.where(bg2, 0, np.maximum(ca, 230)).astype(np.uint8)

logo = Image.fromarray(cropped, "RGBA")
# trim again by alpha
ys, xs = np.where(cropped[:, :, 3] > 0)
logo = logo.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
print("logo size", logo.size)

pad = 28
canvas = Image.new("RGBA", (logo.width + 2 * pad, logo.height + 2 * pad), (0, 0, 0, 0))
canvas.paste(logo, (pad, pad), logo)
canvas.save(ROOT / "harmony-cresym.png")
canvas.save(ROOT / "cresym-biger.png")

# Card with even padding — fill height for square-ish logo
W, H = 1200, 750
for name in ["harmony-card.jpg", "biger-explore-card.jpg"]:
    bg = Image.new("RGBA", (W, H), (247, 250, 249, 255))
    s = canvas.copy()
    s.thumbnail((int(W * 0.82), int(H * 0.90)), Image.Resampling.LANCZOS)
    x = (W - s.width) // 2
    y = (H - s.height) // 2
    bg.alpha_composite(s, (x, y))
    bg.convert("RGB").save(ROOT / name, quality=93, optimize=True)
    print(name, s.size)
