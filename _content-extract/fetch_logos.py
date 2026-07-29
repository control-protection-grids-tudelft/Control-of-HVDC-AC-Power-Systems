import re
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Users\alekic\Documents\GitHub\Control-of-HVDC-AC-Power-Systems\assets\projects")
OUT = Path(r"C:\Users\alekic\Documents\GitHub\Control-of-HVDC-AC-Power-Systems\_content-extract\logos")
OUT.mkdir(parents=True, exist_ok=True)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def find_imgs(page_url: str):
    html = fetch(page_url).decode("utf-8", "replace")
    abs_u = sorted(set(re.findall(r"https?://[^\"'\s>]+\.(?:png|jpg|jpeg|svg|webp)", html, re.I)))
    rel_u = sorted(set(re.findall(r"(?:src|href)=[\"']([^\"']+\.(?:png|jpg|jpeg|svg|webp))[\"']", html, re.I)))
    return abs_u, rel_u, html


print("=== EASY-RES press ===")
abs_u, rel_u, html = find_imgs("https://www.easyres-project.eu/press/")
for u in abs_u:
    print("ABS", u)
for u in rel_u:
    print("REL", u)
# typo-friendly search
for m in re.finditer(r"[^\"']*logo[^\"']*\.(?:png|jpg|jpeg|svg)", html, re.I):
    print("HIT", m.group(0)[:160])

print("\n=== EASY-RES home ===")
abs_u, rel_u, html = find_imgs("https://www.easyres-project.eu/")
for u in abs_u[:30]:
    print("ABS", u)
for u in rel_u[:30]:
    print("REL", u)

print("\n=== Inter-oPEn ===")
abs_u, rel_u, html = find_imgs("https://inter-open.eu/")
for u in abs_u[:40]:
    print("ABS", u)
for u in rel_u[:40]:
    print("REL", u)
