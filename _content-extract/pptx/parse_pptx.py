from pathlib import Path
import re
from xml.etree import ElementTree as ET

NAMES = [
    "Aleksandra", "Lekić", "Lekic", "Rohan", "Tarcar", "Arjita", "Saif", "Alsarayreh",
    "Haixiao", "Sunny", "Singh", "Hashfi", "Badzlin", "Victor", "Reyes", "Rahul", "Rane",
    "Hongjin", "Hao Xu", "Noman", "Ashraf", "Farzad", "Dehghan", "Reza", "Bakhshi",
    "Azadeh", "Ajay", "Shetgaonkar", "MITIGATE", "Harmony", "PROSECCO", "InterOPERA",
    "Inter-oPEn", "SAFE-GRID", "SUNRISE", "Le Liu", "Debottam", "Rashmi", "Dongyu",
    "Sounak", "Vaibhav", "Marvasti", "Kermansaravi",
]


def slide_text(xml_path):
    root = ET.parse(xml_path).getroot()
    texts = []
    for t in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t"):
        if t.text and t.text.strip():
            texts.append(t.text.strip())
    return " ".join(texts)


def slide_images(slide_path, rels_path):
    if not rels_path.exists():
        return []
    rels = ET.parse(rels_path).getroot()
    id_to_target = {}
    for rel in rels:
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rid and target and "media/" in target.replace("\\", "/"):
            id_to_target[rid] = Path(target).name
    root = ET.parse(slide_path).getroot()
    used = []
    for blip in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
        embed = blip.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        )
        if embed and embed in id_to_target:
            used.append(id_to_target[embed])
    return used


base = Path(__file__).resolve().parent
out_dir = base / "parsed"
out_dir.mkdir(exist_ok=True)

for label in ["toshiba", "research"]:
    slides_dir = base / label / "ppt" / "slides"
    lines = []
    lines.append("=" * 80)
    lines.append(label.upper())
    for sp in sorted(slides_dir.glob("slide*.xml"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))):
        n = int(re.search(r"(\d+)", sp.stem).group(1))
        text = slide_text(sp)
        rels = slides_dir / "_rels" / f"{sp.name}.rels"
        imgs = slide_images(sp, rels)
        hits = [k for k in NAMES if k.lower() in text.lower()]
        # keep interesting slides
        personish = any(
            h
            for h in hits
            if h
            not in (
                "Harmony",
                "PROSECCO",
                "InterOPERA",
                "Inter-oPEn",
                "SAFE-GRID",
                "SUNRISE",
                "MITIGATE",
            )
        )
        if personish or "MITIGATE" in hits or "team" in text.lower() or n <= 20:
            lines.append(f"\n--- slide {n} hits={hits} imgs={imgs} ---")
            lines.append(text[:2500])
    (out_dir / f"{label}_interesting.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", out_dir / f"{label}_interesting.txt")

# full toshiba
slides_dir = base / "toshiba" / "ppt" / "slides"
lines = []
for sp in sorted(slides_dir.glob("slide*.xml"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))):
    n = int(re.search(r"(\d+)", sp.stem).group(1))
    text = slide_text(sp)
    rels = slides_dir / "_rels" / f"{sp.name}.rels"
    imgs = slide_images(sp, rels)
    lines.append(f"\n### SLIDE {n} imgs={imgs}\n{text}\n")
(out_dir / "toshiba_full.txt").write_text("\n".join(lines), encoding="utf-8")
print("wrote toshiba_full")

# research: dump all slides mentioning people or MITIGATE fully
slides_dir = base / "research" / "ppt" / "slides"
lines = []
for sp in sorted(slides_dir.glob("slide*.xml"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1))):
    n = int(re.search(r"(\d+)", sp.stem).group(1))
    text = slide_text(sp)
    if any(k.lower() in text.lower() for k in NAMES) or "team" in text.lower() or "group" in text.lower():
        rels = slides_dir / "_rels" / f"{sp.name}.rels"
        imgs = slide_images(sp, rels)
        lines.append(f"\n### SLIDE {n} imgs={imgs}\n{text}\n")
(out_dir / "research_people.txt").write_text("\n".join(lines), encoding="utf-8")
print("wrote research_people", len(lines), "sections")
