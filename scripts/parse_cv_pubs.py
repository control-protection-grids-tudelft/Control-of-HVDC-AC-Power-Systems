"""Parse CV (1).pdf spaced text into publications.json and related CV data."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "_content-extract"
TEXT = (EXTRACT / "cv1_spaced.txt").read_text(encoding="utf-8")


def section(start: str, end: str | None = None, *, last: bool = False) -> str:
    if last:
        i = TEXT.rfind(start)
    else:
        i = TEXT.find(start)
    if i < 0:
        raise SystemExit(f"missing section {start}")
    j = TEXT.find(end, i + len(start)) if end else len(TEXT)
    if j < 0:
        j = len(TEXT)
    return TEXT[i:j]


def normalize(s: str) -> str:
    s = s.replace("\u0012", " ").replace("ὑ7", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n+", " ", s)
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff").replace("ﬃ", "ffi")
    s = s.replace("–", "-").replace("—", "-")
    return s.strip()


def title_case_fix(t: str) -> str:
    t = t.strip().rstrip(".")
    if not t:
        return t
    # Keep all-caps acronyms; otherwise sentence case from first letter
    if t[0].islower():
        t = t[0].upper() + t[1:]
    return t


def parse_numbered_bib(block: str, kind: str) -> list[dict]:
    block = normalize(block)
    # Split on " N Author" patterns at start of entries: digit(s) + capital letter
    parts = re.split(r"(?:(?<=\s)|^)(\d{1,2})\s+(?=[A-Za-zÁÉÍÓÚČĆŽŠĐáéíóúčćžšđ])", block)
    # parts: [preamble, n1, body1, n2, body2, ...]
    pubs = []
    i = 1
    while i + 1 < len(parts):
        n = int(parts[i])
        body = parts[i + 1].strip()
        i += 2
        m = re.match(
            r"(.+?)\((\d{4})[a-z]?\)\.\s*(.+)",
            body,
            re.S,
        )
        if not m:
            continue
        authors = m.group(1).strip().rstrip(".")
        year = int(m.group(2))
        rest = m.group(3).strip()
        doi_m = re.search(r"(?:doi:\s*|https://doi\.org/)([^\s]+)", rest, re.I)
        doi = doi_m.group(1).rstrip(".,;)") if doi_m else None
        if doi:
            rest = rest[: doi_m.start()].strip().rstrip(".")
        # title vs venue: for journals often Title. Venue, vol...
        # For conferences: Title. In Venue
        venue = ""
        title = rest
        in_m = re.search(r"\.\s*(In\s+.+)$", rest, re.I)
        if in_m:
            title = rest[: in_m.start()].strip()
            venue = in_m.group(1).strip().rstrip(".")
        else:
            # split at first period followed by capital journal-like word
            jm = re.search(
                r"\.\s*((?:IEEE|International|Electric|Energies|Energy|High|Heliyon|Tehnika|Journal|Special|CIGRE|e\+i|SoftwareX|Open).+)$",
                rest,
                re.I,
            )
            if jm:
                title = rest[: jm.start()].strip()
                venue = jm.group(1).strip().rstrip(".")
        title = title_case_fix(title)
        pubs.append(
            {
                "n": n,
                "year": year,
                "authors": authors,
                "title": title,
                "venue": venue,
                "doi": doi,
                "kind": kind,
                "raw": normalize(body)[:500],
            }
        )
    return pubs


def parse_simple_list(block: str, kind: str) -> list[dict]:
    """Books / software / deliverables - numbered."""
    block = normalize(block)
    parts = re.split(r"(?:(?<=\s)|^)(\d{1,2})\s+(?=[A-ZÁÉÍÓÚ])", block)
    items = []
    i = 1
    while i + 1 < len(parts):
        n = int(parts[i])
        body = parts[i + 1].strip()
        i += 2
        m = re.match(r"(.+?)\((\d{4})[a-z]?\)\.\s*(.+)", body, re.S)
        if not m:
            # software may use different format
            ym = re.search(r"\((\d{4})[a-z]?\)", body)
            year = int(ym.group(1)) if ym else None
            items.append(
                {
                    "n": n,
                    "year": year,
                    "authors": "",
                    "title": title_case_fix(body[:200]),
                    "venue": "",
                    "doi": None,
                    "kind": kind,
                    "raw": body[:400],
                }
            )
            continue
        authors = m.group(1).strip()
        year = int(m.group(2))
        rest = m.group(3).strip()
        doi_m = re.search(r"(?:doi:\s*|https://doi\.org/)([^\s]+)", rest, re.I)
        doi = doi_m.group(1).rstrip(".,;)") if doi_m else None
        if doi:
            rest = rest[: doi_m.start()].strip()
        url_m = re.search(r"(https?://\S+)", rest)
        url = url_m.group(1).rstrip(".,)") if url_m else None
        items.append(
            {
                "n": n,
                "year": year,
                "authors": authors,
                "title": title_case_fix(rest.split("Retrieved")[0].split("GitHub")[0][:220]),
                "venue": "",
                "doi": doi,
                "url": url,
                "kind": kind,
                "raw": body[:400],
            }
        )
    return items


journal_sec = section("Journal Articles", "Conference Proceedings")
conf_sec = section("Conference Proceedings", "Project Deliverables")
deliv_sec = section("Project Deliverables and Brochures", "Books and Chapters")
books_sec = section("Books and Chapters", "Software")
soft_sec = section("\nSoftware\n", "Media exposure", last=True)

journals = parse_numbered_bib(journal_sec, "journal")
conferences = parse_numbered_bib(conf_sec, "conference")
deliverables = parse_simple_list(deliv_sec, "deliverable")
books = parse_simple_list(books_sec, "book")
software = parse_simple_list(soft_sec, "software")

# Prefer journals+conferences for main list; attach extras separately
main = journals + conferences
# Dedup by doi/title
seen = set()
uniq = []
for p in sorted(main, key=lambda x: (-(x.get("year") or 0), x.get("n") or 0)):
    key = (p.get("doi") or "").lower() or (p.get("title") or "")[:90].lower()
    if not key or key in seen:
        continue
    seen.add(key)
    uniq.append(p)

(EXTRACT / "publications.json").write_text(json.dumps(uniq, indent=2, ensure_ascii=False), encoding="utf-8")
(EXTRACT / "publications_extra.json").write_text(
    json.dumps(
        {"deliverables": deliverables, "books": books, "software": software},
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"journals={len(journals)} conferences={len(conferences)} main_uniq={len(uniq)}")
print(f"deliverables={len(deliverables)} books={len(books)} software={len(software)}")
print("sample journal:", uniq[0]["title"][:80] if uniq else None)
print("years", sorted({p['year'] for p in uniq if p.get('year')}, reverse=True)[:8])
