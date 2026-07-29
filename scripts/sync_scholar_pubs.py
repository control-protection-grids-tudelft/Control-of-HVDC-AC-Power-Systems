"""Fetch OpenAlex works for Aleksandra Lekić and merge missing pubs into publications.json.

Also attaches DOI / landing / Scholar search links for site rendering.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "_content-extract"
AUTHOR_ID = "A5073473404"
SCHOLAR_PROFILE = "https://scholar.google.com/citations?user=xwCWAb0AAAAJ&hl=en"


def fetch_openalex_works() -> list[dict]:
    base = (
        f"https://api.openalex.org/works?filter=author.id:{AUTHOR_ID}"
        "&per-page=200&mailto=dev@example.com"
    )
    works: list[dict] = []
    cursor = "*"
    while True:
        url = f"{base}&cursor={cursor}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        batch = data.get("results") or []
        works.extend(batch)
        cursor = (data.get("meta") or {}).get("next_cursor")
        print(f"OpenAlex batch {len(batch)}, total {len(works)}")
        if not cursor or not batch:
            break
    (EXTRACT / "openalex_works.json").write_text(
        json.dumps(works, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return works


def norm_title(t: str | None) -> str:
    import unicodedata

    t = (t or "").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def titles_match(a: str, b: str) -> bool:
    """Strict-ish title match: exact, or shared long prefix after first 12 words."""
    if not a or not b:
        return False
    if a == b:
        return True
    # Require substantial overlap — avoid "cuk ... piecewise" vs "cuk ... polytopic"
    wa, wb = a.split(), b.split()
    if len(wa) < 6 or len(wb) < 6:
        return a[:70] == b[:70]
    common = 0
    for x, y in zip(wa, wb):
        if x != y:
            break
        common += 1
    return common >= min(10, min(len(wa), len(wb))) and abs(len(wa) - len(wb)) <= 2


def doi_key(d: str | None) -> str:
    if not d:
        return ""
    return d.lower().replace("https://doi.org/", "").strip().rstrip(".")


def authors_str(w: dict) -> str:
    names = []
    for a in w.get("authorships") or []:
        n = (a.get("author") or {}).get("display_name")
        if n:
            names.append(n)
    return ", ".join(names)


def venue_str(w: dict) -> str:
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name") or ""


def work_to_pub(w: dict, n: int) -> dict:
    title = (w.get("display_name") or "").strip()
    doi = doi_key(w.get("doi"))
    landing = (w.get("primary_location") or {}).get("landing_page_url")
    oa = (w.get("open_access") or {}).get("oa_url")
    url = None
    if doi:
        url = f"https://doi.org/{doi}"
    elif landing:
        url = landing
    elif oa:
        url = oa
    year = w.get("publication_year") or 0
    typ = w.get("type") or ""
    kind = "journal"
    if "proceeding" in typ or "conference" in typ:
        kind = "conference"
    elif typ in {"preprint", "posted-content"}:
        kind = "preprint"
    elif typ in {"book", "book-chapter"}:
        kind = "book"
    elif typ == "dataset":
        kind = "dataset"
    # Scholar deep-link via title search on profile
    scholar = (
        "https://scholar.google.com/scholar?q="
        + urllib.request.quote(f'author:"Aleksandra Lekić" "{title[:80]}"')
    )
    return {
        "n": n,
        "year": int(year) if year else None,
        "authors": authors_str(w),
        "title": title,
        "venue": venue_str(w),
        "doi": doi or None,
        "url": url,
        "scholar": scholar,
        "kind": kind,
        "source": "openalex",
        "raw": f"{authors_str(w)} ({year}). {title}. {venue_str(w)}."
        + (f" doi: {doi}" if doi else ""),
    }


def main():
    works = fetch_openalex_works()
    pubs_path = EXTRACT / "publications.json"
    pubs = json.loads(pubs_path.read_text(encoding="utf-8"))

    existing_dois = {doi_key(p.get("doi")) for p in pubs if p.get("doi")}
    existing_titles = {norm_title(p.get("title")) for p in pubs}

    # Enrich existing pubs with scholar + url links
    for p in pubs:
        title = p.get("title") or ""
        if not p.get("scholar"):
            p["scholar"] = (
                "https://scholar.google.com/scholar?q="
                + urllib.request.quote(f'author:"Aleksandra Lekić" "{title[:80]}"')
            )
        if not p.get("url"):
            d = doi_key(p.get("doi"))
            if d:
                p["url"] = f"https://doi.org/{d}"
            else:
                p["url"] = p["scholar"]

    added = []
    skip_types = {"paratext", "peer-review", "editorial", "erratum"}
    max_n = max((p.get("n") or 0) for p in pubs) if pubs else 0
    for w in works:
        typ = (w.get("type") or "").lower()
        if typ in skip_types:
            continue
        title = (w.get("display_name") or "").strip()
        if not title:
            continue
        doi = doi_key(w.get("doi"))
        nt = norm_title(title)
        if doi and doi in existing_dois:
            continue
        if any(titles_match(nt, et) for et in existing_titles if et):
            continue
        # Skip pure software deposits already covered in publications_extra
        if "harmony - harmonic stability" in nt and "zenodo" in (doi or ""):
            continue
        if "stabilno prekidacko upravljanje" in nt:
            continue  # PhD thesis — not a journal paper
        max_n += 1
        pub = work_to_pub(w, max_n)
        if not pub.get("year") or pub["year"] < 2010:
            continue
        pubs.append(pub)
        added.append(pub)
        existing_dois.add(doi)
        existing_titles.add(nt)

    pubs_path.write_text(json.dumps(pubs, indent=2, ensure_ascii=False), encoding="utf-8")
    report = EXTRACT / "publications_added_from_openalex.json"
    report.write_text(json.dumps(added, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Enriched pubs: {len(pubs)}; newly added: {len(added)}")
    for a in sorted(added, key=lambda x: (-(x.get("year") or 0), x.get("title") or "")):
        line = f"  + {a.get('year')} | {a.get('kind')} | {a.get('title')[:100]}"
        print(line.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
