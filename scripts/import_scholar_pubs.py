"""Re-import Google Scholar citations with correct per-row HTML parsing."""
from __future__ import annotations

import html as html_lib
import json
import re
import unicodedata
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "_content-extract"
USER = "xwCWAb0AAAAJ"
SCHOLAR = f"https://scholar.google.com/citations?user={USER}&hl=en"


def fold(t: str | None) -> str:
    t = (t or "").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def scholar_q(title: str) -> str:
    q = urllib.parse.quote(f'author:"Aleksandra Lekić" "{title[:80]}"')
    return f"https://scholar.google.com/scholar?q={q}"


def titles_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    wa, wb = a.split(), b.split()
    if len(wa) < 5 or len(wb) < 5:
        return a[:60] == b[:60]
    common = 0
    for x, y in zip(wa, wb):
        if x != y:
            break
        common += 1
    return common >= min(8, min(len(wa), len(wb))) and abs(len(wa) - len(wb)) <= 3


SKIP = re.compile(
    r"Acknowledgement to Reviewers|Acknowledgment to Reviewers|"
    r"Announcement of the .* Best Paper Award|"
    r"New \d{4} IEEE IAS Senior Members|"
    r"IEEE RTSI \d{4} Reviewer Board|"
    r"^Energy Reports$|"
    r"Development of the game Hangman|"
    r"Using Assembly Language for Creating Games|"
    r"Program Co-chairs|Review Committee Members|"
    r"Telfor \d{4}.?reviewers|reviewers$",
    re.I,
)


def parse_html(html: str) -> list[dict]:
    out = []
    parts = re.split(r'<tr\s+class="gsc_a_tr">', html)
    for part in parts[1:]:
        tm = re.search(
            r'<a\s+href="([^"]+)"\s+class="gsc_a_at">(.*?)</a>',
            part,
            re.S,
        )
        if not tm:
            tm = re.search(
                r'class="gsc_a_at"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                part,
                re.S,
            )
        if not tm:
            continue
        href, title = tm.groups()
        title = html_lib.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        grays = re.findall(r'<div class="gs_gray">(.*?)</div>', part, re.S)
        authors = html_lib.unescape(re.sub(r"<[^>]+>", "", grays[0])).strip() if grays else ""
        venue = html_lib.unescape(re.sub(r"<[^>]+>", "", grays[1])).strip() if len(grays) > 1 else ""
        ym = re.search(r'class="gsc_a_y"[^>]*>.*?<span[^>]*>(\d{4})</span>', part, re.S)
        if ym:
            year = int(ym.group(1))
        else:
            ym2 = re.search(r"\b(20\d{2}|19\d{2})\b", venue)
            year = int(ym2.group(1)) if ym2 else 0
        cite = href.replace("&amp;", "&")
        if not cite.startswith("http"):
            cite = "https://scholar.google.com" + cite
        out.append(
            {
                "title": title,
                "authors": authors,
                "venue": venue,
                "year": year,
                "scholar_cite": cite,
            }
        )
    return out


def main():
    pages = []
    for cstart in (0, 100, 200):
        path = EXTRACT / f"scholar_page_{cstart}.html"
        if path.exists():
            pages.append(path.read_text(encoding="utf-8"))

    entries = []
    for html in pages:
        entries.extend(parse_html(html))

    seen = set()
    uniq = []
    for e in entries:
        k = fold(e["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    print(f"Parsed Scholar titles: {len(uniq)}")
    (EXTRACT / "scholar_parsed.json").write_text(
        json.dumps(uniq, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    pubs_path = EXTRACT / "publications.json"
    pubs = json.loads(pubs_path.read_text(encoding="utf-8"))
    # Drop previous broken google-scholar imports
    before = len(pubs)
    pubs = [p for p in pubs if p.get("source") != "google-scholar"]
    print(f"Removed prior scholar imports: {before - len(pubs)}")

    existing_titles = {fold(p.get("title")) for p in pubs if p.get("title")}
    max_n = max((p.get("n") or 0) for p in pubs) if pubs else 0
    added = []

    for e in uniq:
        title = e["title"]
        if SKIP.search(title):
            continue
        nt = fold(title)
        if any(titles_match(nt, et) for et in existing_titles if et):
            continue
        max_n += 1
        year = e.get("year") or 0
        venue = e.get("venue") or ""
        doi = None
        url = None
        # Recover DOI/URL from Scholar venue line when present
        dm = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", venue, re.I)
        if dm:
            doi = dm.group(1).rstrip(".,)")
            url = f"https://doi.org/{doi}"
        elif venue.startswith("http"):
            url = venue.split(",")[0].strip()
        pub = {
            "n": max_n,
            "year": year,
            "authors": e.get("authors") or "Lekić, A. et al.",
            "title": title,
            "venue": venue,
            "doi": doi,
            "url": url,
            "scholar": e.get("scholar_cite") or scholar_q(title),
            "kind": "journal",
            "source": "google-scholar",
            "raw": f"{e.get('authors')} ({year or 'n.d.'}). {title}. {venue}",
        }
        pubs.append(pub)
        added.append(pub)
        existing_titles.add(nt)

    pubs_path.write_text(json.dumps(pubs, indent=2, ensure_ascii=False), encoding="utf-8")
    (EXTRACT / "publications_added_scholar.json").write_text(
        json.dumps(added, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Added {len(added)}; total={len(pubs)}")
    for a in sorted(added, key=lambda x: (-(x.get("year") or 0), x["title"])):
        line = f"  + {a['year']} | {a['title'][:90]}"
        print(line.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
