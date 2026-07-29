"""Download Vaibhav and Rashmi portraits from TU Delft SUNRISE / BiGER pages."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_content-extract" / "tud_project_pages"
TEAM = ROOT / "assets" / "team"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

PAGES = {
    "sunrise": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/completed-projects/sunrise",
    "biger": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/completed-projects/biger-explore",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=45).read()


def abs_url(base: str, src: str) -> str:
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http"):
        return src
    if src.startswith("/"):
        return "https://www.tudelft.nl" + src
    return base.rsplit("/", 1)[0] + "/" + src


def parse_imgs(html: str, base: str):
    for tag in re.findall(r"<img[^>]+>", html, flags=re.I):
        src_m = re.search(r'src=["\']([^"\']+)', tag, flags=re.I)
        alt_m = re.search(r'alt=["\']([^"\']*)', tag, flags=re.I)
        if not src_m:
            continue
        src = src_m.group(1)
        alt = alt_m.group(1) if alt_m else ""
        yield abs_url(base, src), alt, tag


def save_portrait(url: str, slug: str) -> Path:
    data = fetch(url)
    raw = OUT / f"{slug}_raw"
    # guess extension
    ext = ".jpg"
    if ".png" in url.lower():
        ext = ".png"
    elif ".webp" in url.lower():
        ext = ".webp"
    raw = raw.with_suffix(ext)
    raw.write_bytes(data)
    im = Image.open(raw).convert("RGB")
    # Center-crop to square then resize for team cards
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((640, 640), Image.Resampling.LANCZOS)
    dest = TEAM / f"{slug}.jpg"
    im.save(dest, quality=92, optimize=True)
    print(f"saved {dest} from {url} ({len(data)} bytes, {w}x{h})")
    return dest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {
        "vaibhav": ("vaibhav-nougain", ("vaibhav", "nougain")),
        "rashmi": ("rashmi-prasad", ("rashmi", "prasad")),
    }
    found: dict[str, str] = {}

    for name, url in PAGES.items():
        html = fetch(url).decode("utf-8", "replace")
        (OUT / f"{name}.html").write_text(html, encoding="utf-8")
        print(f"\n=== {name} ===")
        for src, alt, tag in parse_imgs(html, url):
            blob = f"{src} {alt}".lower()
            print(f" img alt={alt!r} src={src}")
            for key, (slug, keys) in targets.items():
                if any(k in blob for k in keys):
                    found[slug] = src
                    print(f"  -> match {slug}")

        # Also look near name mentions for data-src / background images
        for key, (slug, keys) in targets.items():
            if slug in found:
                continue
            for k in keys:
                # figure/img blocks near the name
                for m in re.finditer(re.escape(k), html, flags=re.I):
                    window = html[max(0, m.start() - 800) : m.start() + 800]
                    for src, alt, tag in parse_imgs(window, url):
                        if any(x in src.lower() for x in ("fileadmin", "user_upload", "media", "typo3temp", "image")):
                            found[slug] = src
                            print(f"  nearby match {slug}: {src}")
                            break
                    if slug in found:
                        break

    # Fallback: staff pages
    fallbacks = {
        "vaibhav-nougain": [
            "https://www.tudelft.nl/staff/v.nougain/",
            "https://www.tudelft.nl/staff/v.nougain/?cHash=",
        ],
        "rashmi-prasad": [
            "https://www.tudelft.nl/staff/r.prasad/",
            "https://www.tudelft.nl/staff/r.prasad-1/",
        ],
    }

    for slug, keys in [("vaibhav-nougain", ("vaibhav", "nougain")), ("rashmi-prasad", ("rashmi", "prasad"))]:
        if slug in found:
            continue
        for fb in fallbacks.get(slug, []):
            try:
                html = fetch(fb).decode("utf-8", "replace")
            except Exception as e:
                print(f"fallback fail {fb}: {e}")
                continue
            (OUT / f"staff_{slug}.html").write_text(html, encoding="utf-8")
            for src, alt, tag in parse_imgs(html, fb):
                blob = f"{src} {alt}".lower()
                if any(k in blob for k in keys) or ("fileadmin" in src and "staff" in src.lower()):
                    found[slug] = src
                    print(f"staff match {slug}: {src}")
                    break
            if slug in found:
                break
            # largest content image on staff page
            cands = []
            for src, alt, tag in parse_imgs(html, fb):
                if any(x in src.lower() for x in ("fileadmin", "user_upload", "media")) and not src.lower().endswith(".svg"):
                    cands.append(src)
            if cands:
                found[slug] = cands[0]
                print(f"staff first media {slug}: {cands[0]}")

    print("\nFOUND:", found)
    for slug, src in found.items():
        save_portrait(src, slug)

    missing = [s for s in ("vaibhav-nougain", "rashmi-prasad") if s not in found]
    if missing:
        raise SystemExit(f"Missing portraits for: {missing}")


if __name__ == "__main__":
    main()
