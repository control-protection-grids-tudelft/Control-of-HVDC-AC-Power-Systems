"""Import ALL OpenAlex + ORCID works for Aleksandra Lekić into publications.json.

Keeps entries even without DOI/URL. Relaxes filters so Scholar-scale coverage
is reflected on the site.
"""
from __future__ import annotations

import json
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "_content-extract"
AUTHOR_OPENALEX = "A5073473404"
ORCID = "0000-0003-2727-0767"
SCHOLAR = "https://scholar.google.com/citations?user=xwCWAb0AAAAJ&hl=en"
UA = {"User-Agent": "Mozilla/5.0 (compatible; TUD-group-site/1.0; mailto:dev@example.com)"}


def get_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fold(t: str | None) -> str:
    t = (t or "").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def doi_key(d: str | None) -> str:
    if not d:
        return ""
    d = d.lower().strip()
    d = d.replace("https://doi.org/", "").replace("http://doi.org/", "")
    return d.rstrip(".")


def scholar_q(title: str) -> str:
    q = urllib.parse.quote(f'author:"Aleksandra Lekić" "{title[:80]}"')
    return f"https://scholar.google.com/scholar?q={q}"


def fetch_openalex() -> list[dict]:
    base = (
        f"https://api.openalex.org/works?filter=author.id:{AUTHOR_OPENALEX}"
        "&per-page=200&mailto=dev@example.com"
    )
    works, cursor = [], "*"
    while True:
        data = get_json(f"{base}&cursor={urllib.parse.quote(cursor)}")
        batch = data.get("results") or []
        works.extend(batch)
        cursor = (data.get("meta") or {}).get("next_cursor")
        print(f"OpenAlex +{len(batch)} total={len(works)}")
        if not cursor or not batch:
            break
    (EXTRACT / "openalex_works.json").write_text(
        json.dumps(works, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return works


def fetch_semanticscholar() -> list[dict]:
    path = EXTRACT / "semanticscholar_papers.json"
    if path.exists():
        papers = json.loads(path.read_text(encoding="utf-8"))
        print(f"Semantic Scholar cached: {len(papers)}")
        return papers
    allp, offset = [], 0
    while True:
        url = (
            "https://api.semanticscholar.org/graph/v1/author/8272751/papers"
            f"?fields=title,year,authors,venue,externalIds,url,publicationTypes"
            f"&limit=100&offset={offset}"
        )
        data = get_json(url)
        batch = data.get("data") or []
        allp.extend(batch)
        nxt = data.get("next")
        print(f"S2 +{len(batch)} total={len(allp)}")
        if not batch or nxt is None:
            break
        offset = nxt
    path.write_text(json.dumps(allp, indent=2, ensure_ascii=False), encoding="utf-8")
    return allp


def ss_to_pub(p: dict, n: int) -> dict:
    title = (p.get("title") or "").strip()
    authors = ", ".join(a.get("name") for a in (p.get("authors") or []) if a.get("name"))
    ext = p.get("externalIds") or {}
    doi = doi_key(ext.get("DOI"))
    url = None
    if doi:
        url = f"https://doi.org/{doi}"
    elif p.get("url"):
        url = p["url"]
    elif ext.get("ArXiv"):
        url = f"https://arxiv.org/abs/{ext['ArXiv']}"
    year = p.get("year")
    types = p.get("publicationTypes") or []
    kind = "journal"
    joined = " ".join(types).lower()
    if "conference" in joined:
        kind = "conference"
    elif "review" in joined:
        kind = "journal"
    return {
        "n": n,
        "year": int(year) if year else None,
        "authors": authors,
        "title": title,
        "venue": p.get("venue") or "",
        "doi": doi or None,
        "url": url,
        "scholar": scholar_q(title) if title else SCHOLAR,
        "kind": kind,
        "source": "semanticscholar",
        "raw": f"{authors} ({year}). {title}. {p.get('venue') or ''}."
        + (f" doi: {doi}" if doi else ""),
    }

def fetch_orcid() -> list[dict]:
    """ORCID public works summary (titles/years; may lack DOIs)."""
    url = f"https://pub.orcid.org/v3.0/{ORCID}/works"
    req = urllib.request.Request(
        url,
        headers={**UA, "Accept": "application/vnd.orcid+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("ORCID fetch failed:", e)
        return []
    (EXTRACT / "orcid_works.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    out = []
    for group in data.get("group") or []:
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        s = summaries[0]
        title = (((s.get("title") or {}).get("title") or {}).get("value")) or ""
        year = None
        pub = s.get("publication-date") or {}
        if pub.get("year") and pub["year"].get("value"):
            try:
                year = int(pub["year"]["value"])
            except Exception:
                year = None
        ext_ids = ((s.get("external-ids") or {}).get("external-id")) or []
        doi = None
        url_ext = None
        for eid in ext_ids:
            typ = (eid.get("external-id-type") or "").lower()
            val = eid.get("external-id-value")
            if typ == "doi" and val:
                doi = val
            if typ in {"uri", "url"} and val and not url_ext:
                url_ext = val
        out.append(
            {
                "title": title.strip(),
                "year": year,
                "doi": doi,
                "url": url_ext,
                "type": (s.get("type") or "").lower(),
            }
        )
    print(f"ORCID works: {len(out)}")
    return out


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


def kind_from_type(typ: str) -> str:
    typ = (typ or "").lower()
    if "proceeding" in typ or "conference" in typ:
        return "conference"
    if typ in {"preprint", "posted-content"}:
        return "preprint"
    if typ in {"book", "book-chapter", "chapter"}:
        return "book"
    if typ in {"dissertation", "thesis"}:
        return "thesis"
    if typ in {"dataset", "software"}:
        return "software"
    if typ in {"report"}:
        return "report"
    return "journal"


def oa_to_pub(w: dict, n: int) -> dict:
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
    year = w.get("publication_year")
    typ = w.get("type") or ""
    return {
        "n": n,
        "year": int(year) if year else None,
        "authors": authors_str(w),
        "title": title,
        "venue": venue_str(w),
        "doi": doi or None,
        "url": url,
        "scholar": scholar_q(title) if title else SCHOLAR,
        "kind": kind_from_type(typ),
        "source": "openalex",
        "raw": f"{authors_str(w)} ({year}). {title}. {venue_str(w)}."
        + (f" doi: {doi}" if doi else ""),
    }


def titles_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    wa, wb = a.split(), b.split()
    if len(wa) < 6 or len(wb) < 6:
        return a[:70] == b[:70]
    common = 0
    for x, y in zip(wa, wb):
        if x != y:
            break
        common += 1
    return common >= min(10, min(len(wa), len(wb))) and abs(len(wa) - len(wb)) <= 2


def main():
    works = fetch_openalex()
    orcid = fetch_orcid()
    ss = fetch_semanticscholar()
    pubs_path = EXTRACT / "publications.json"
    pubs = json.loads(pubs_path.read_text(encoding="utf-8"))

    # Enrich existing
    for p in pubs:
        title = p.get("title") or ""
        if not p.get("scholar") and title:
            p["scholar"] = scholar_q(title)
        if not p.get("url"):
            d = doi_key(p.get("doi"))
            if d:
                p["url"] = f"https://doi.org/{d}"

    existing_dois = {doi_key(p.get("doi")) for p in pubs if p.get("doi")}
    existing_titles = {fold(p.get("title")) for p in pubs if p.get("title")}
    max_n = max((p.get("n") or 0) for p in pubs) if pubs else 0
    added = []

    skip_types = {"paratext", "peer-review", "editorial", "erratum"}

    def consider(pub: dict):
        nonlocal max_n
        title = (pub.get("title") or "").strip()
        if not title:
            return
        doi = doi_key(pub.get("doi"))
        nt = fold(title)
        if doi and doi in existing_dois:
            return
        if any(titles_match(nt, et) for et in existing_titles if et):
            return
        year = pub.get("year")
        if year and (year < 2008 or year > 2035):
            return
        if not year:
            pub["year"] = 0  # Undated — still list it
        max_n += 1
        pub = {**pub, "n": max_n}
        if not pub.get("scholar"):
            pub["scholar"] = scholar_q(title)
        pubs.append(pub)
        added.append(pub)
        if doi:
            existing_dois.add(doi)
        existing_titles.add(nt)

    for w in works:
        typ = (w.get("type") or "").lower()
        if typ in skip_types:
            continue
        consider(oa_to_pub(w, 0))

    for o in orcid:
        title = (o.get("title") or "").strip()
        doi = doi_key(o.get("doi"))
        url = f"https://doi.org/{doi}" if doi else o.get("url")
        consider(
            {
                "year": o.get("year"),
                "authors": "Lekić, A.",
                "title": title,
                "venue": "",
                "doi": doi or None,
                "url": url,
                "scholar": scholar_q(title) if title else SCHOLAR,
                "kind": kind_from_type(o.get("type") or ""),
                "source": "orcid",
                "raw": f"Lekić, A. ({o.get('year')}). {title}." + (f" doi: {doi}" if doi else ""),
            }
        )

    for p in ss:
        consider(ss_to_pub(p, 0))

    pubs_path.write_text(json.dumps(pubs, indent=2, ensure_ascii=False), encoding="utf-8")
    (EXTRACT / "publications_added_full.json").write_text(
        json.dumps(added, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Total pubs now: {len(pubs)}; newly added: {len(added)}")
    for a in sorted(added, key=lambda x: (-(x.get("year") or 0), x.get("title") or "")):
        line = f"  + {a.get('year')} | {a.get('kind')} | {(a.get('title') or '')[:90]}"
        print(line.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
