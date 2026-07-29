"""Map images on team slides by spatial position relative to name textboxes."""
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from collections import defaultdict

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def emu(s):
    return int(s) if s is not None else 0


def get_off(spPr):
    # look for a:xfrm/a:off
    for xfrm in spPr.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm"):
        off = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}off")
        ext = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}ext")
        if off is not None:
            return emu(off.get("x")), emu(off.get("y")), emu(ext.get("cx") if ext is not None else 0), emu(ext.get("cy") if ext is not None else 0)
    return None


def parse_slide(slide_path, rels_path):
    rels = ET.parse(rels_path).getroot()
    id_to_target = {}
    for rel in rels:
        rid, target = rel.attrib.get("Id"), rel.attrib.get("Target")
        if rid and target and "media/" in target.replace("\\", "/"):
            id_to_target[rid] = Path(target).name

    root = ET.parse(slide_path).getroot()
    texts = []
    images = []
    for sp in root.iter("{http://schemas.openxmlformats.org/presentationml/2006/main}sp"):
        # text
        ts = [
            t.text.strip()
            for t in sp.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t")
            if t.text and t.text.strip()
        ]
        if not ts:
            continue
        spPr = sp.find("{http://schemas.openxmlformats.org/presentationml/2006/main}spPr")
        if spPr is None:
            continue
        box = get_off(spPr)
        if box:
            texts.append({"text": " ".join(ts), "x": box[0], "y": box[1], "w": box[2], "h": box[3]})

    for pic in root.iter("{http://schemas.openxmlformats.org/presentationml/2006/main}pic"):
        blip = pic.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
        if blip is None:
            continue
        embed = blip.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        name = id_to_target.get(embed)
        if not name:
            continue
        spPr = pic.find("{http://schemas.openxmlformats.org/presentationml/2006/main}spPr")
        box = get_off(spPr) if spPr is not None else None
        # also try nvPicPr sibling xfrm under pic:blipFill sibling - actually xfrm often under pic/spPr
        if box is None:
            for xfrm in pic.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm"):
                off = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}off")
                ext = xfrm.find("{http://schemas.openxmlformats.org/drawingml/2006/main}ext")
                if off is not None:
                    box = (
                        emu(off.get("x")),
                        emu(off.get("y")),
                        emu(ext.get("cx") if ext is not None else 0),
                        emu(ext.get("cy") if ext is not None else 0),
                    )
                    break
        if box:
            images.append({"file": name, "x": box[0], "y": box[1], "w": box[2], "h": box[3], "cx": box[0] + box[2] / 2, "cy": box[1] + box[3] / 2})

    return texts, images


def nearest_name(img, names):
    best = None
    best_d = 1e30
    for n in names:
        # prefer text below or near the image center
        dx = n["x"] + n["w"] / 2 - img["cx"]
        dy = n["y"] + n["h"] / 2 - img["cy"]
        # weight: text usually under photo
        d = (dx / 10000) ** 2 + (dy / 10000) ** 2
        # bonus if text is below image and roughly same x
        if abs(dx) < max(img["w"], n["w"]) and n["y"] >= img["y"]:
            d *= 0.3
        if d < best_d:
            best_d = d
            best = n
    return best, best_d


PEOPLE_PATTERNS = [
    (r"Victor\s+Daniel\s+Reyes\s+Dreke|Victor\s+Reyes", "victor-reyes-dreke"),
    (r"Rahul\s+Rane", "rahul-rane"),
    (r"Sunny\s+Singh", "sunny-singh"),
    (r"Rohan\s+Kamat\s+Tarcar|Rohan\s+Kamat", "rohan-kamat-tarcar"),
    (r"Arjita\s+Pal", "arjita-pal"),
    (r"Haixiao\s+Li", "haixiao-li"),
    (r"Saif\s+Alsarayreh", "saif-alsarayreh"),
    (r"Hao\s+Xu", "hao-xu"),
    (r"Hongjin\s+Du", "hongjin-du"),
    (r"Tunku\s+Badzlin\s+Hashfi|Tuanku\s+Badzlin\s+Hashfi|Badzlin\s+Hashfi", "tuanku-badzlin-hashfi"),
    (r"Aleksandra\s+Leki", "aleksandra-lekic"),
    (r"Farzad\s+Dehghan\s+Marvasti|Farzad\s+Dehghan", "farzad-dehghan-marvasti"),
    (r"Reza\s+Bah?khshi|Bakhshi", "reza-bakhshi-jafarabadi"),
    (r"Azadeh\s+Kermansaravi", "azadeh-kermansaravi"),
    (r"Muhammad\s+Noman\s+Ashraf|Noman\s+Ashraf", "muhammad-noman-ashraf"),
    (r"Remko\s+Koornneef", "remko-koornneef"),
    (r"Marjan\s+Popov", "marjan-popov"),
    (r"Robert\s+Dimitrovski", "robert-dimitrovski"),
    (r"Yasel\s+Quintero", "yasel-quintero"),
]


def match_person(text):
    for pat, slug in PEOPLE_PATTERNS:
        if re.search(pat, text, re.I):
            return slug
    return None


base = Path(r"C:\Users\alekic\Documents\GitHub\Control-of-HVDC-AC-Power-Systems\_content-extract\pptx")
targets = [
    ("toshiba", 3),
    ("research", 13),
    ("research", 24),
    ("research", 31),
    ("research", 36),
    ("research", 60),
]

out = []
for label, n in targets:
    slide = base / label / "ppt" / "slides" / f"slide{n}.xml"
    rels = base / label / "ppt" / "slides" / "_rels" / f"slide{n}.xml.rels"
    texts, images = parse_slide(slide, rels)
    name_boxes = []
    for t in texts:
        slug = match_person(t["text"])
        if slug:
            name_boxes.append({**t, "slug": slug})
    out.append(f"\n===== {label} slide {n} =====")
    out.append("NAMES:")
    for nb in sorted(name_boxes, key=lambda x: (x["y"], x["x"])):
        out.append(f"  {nb['slug']:30} x={nb['x']:8} y={nb['y']:8} text={nb['text'][:60]}")
    out.append("IMAGES (portrait-ish):")
    # filter larger portrait candidates
    for img in sorted(images, key=lambda x: (x["y"], x["x"])):
        if img["w"] < 200000 and img["h"] < 200000:
            continue  # skip tiny logos
        nb, d = nearest_name(img, name_boxes) if name_boxes else (None, None)
        slug = nb["slug"] if nb else "?"
        out.append(f"  {img['file']:20} {img['w']}x{img['h']} @({img['x']},{img['y']}) -> {slug} (d={d})")

Path(base / "parsed" / "photo_map.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
