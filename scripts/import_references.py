#!/usr/bin/env python3
"""
Import every cited reference of a paper into a single Markdown digest at
paper-pipeline/references/{paper_slug}.md. Pulls abstracts from OpenAlex
when a DOI is available, and falls back to bib metadata otherwise.

Usage:
    python3 import_references.py <paper-directory>

The paper directory must contain at least one .tex and one .bib file. The
output filename is the directory name with any leading {template}-latex_
prefix stripped, so:

    papers-latex/easychair-latex_simbox-detection
        -> references/simbox-detection.md
    papers-latex/tsp_survey
        -> references/tsp_survey.md

If no argument is given, the script defaults to the tsp_survey paper.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PAPER_PIPELINE = Path(__file__).resolve().parent.parent
REFERENCES_DIR = PAPER_PIPELINE / "references"
MAILTO = "vinceabella05@gmail.com"
OPENALEX_BASE = "https://api.openalex.org"

TEMPLATE_PREFIXES = ("ieee-latex_", "mdpi-latex_", "easychair-latex_", "tsp-latex_")


def find_cited_keys(tex_path: Path) -> list[str]:
    text = tex_path.read_text(encoding="utf-8", errors="ignore")
    keys: set[str] = set()
    for match in re.finditer(r"\\cite\{([^}]+)\}", text):
        for key in match.group(1).split(","):
            keys.add(key.strip())
    return sorted(keys)


def parse_bib(bib_path: Path) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    text = bib_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
    starts = [(m.start(), m.group(1).lower(), m.group(2)) for m in pattern.finditer(text)]
    for i, (start, kind, key) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        body = text[start:end]
        entries[key] = {"kind": kind, "raw": body, **parse_fields(body)}
    return entries


def parse_fields(body: str) -> dict:
    fields = {}
    for fname in ("title", "author", "year", "doi", "journal", "booktitle",
                  "publisher", "pages", "volume", "number", "month", "url",
                  "eprint", "shorttitle", "archiveprefix"):
        value = extract_field(body, fname)
        if value is not None:
            fields[fname] = value
    return fields


def extract_field(body: str, name: str) -> str | None:
    pattern = re.compile(rf"\b{name}\s*=\s*", re.IGNORECASE)
    m = pattern.search(body)
    if not m:
        return None
    pos = m.end()
    if pos >= len(body):
        return None
    first = body[pos]
    if first == "{":
        depth = 1
        i = pos + 1
        while i < len(body) and depth:
            c = body[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        raw = body[pos + 1:i - 1]
    elif first == '"':
        i = pos + 1
        while i < len(body) and body[i] != '"':
            i += 1
        raw = body[pos + 1:i]
    else:
        end = pos
        while end < len(body) and body[end] not in ",}\n":
            end += 1
        raw = body[pos:end]
    return clean_brace(raw).strip()


def clean_brace(s: str) -> str:
    return re.sub(r"\{|\}", "", s)


def split_authors(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"\s+and\s+", raw)
    return [a.strip() for a in parts if a.strip()]


def fetch_openalex(doi: str | None) -> dict | None:
    if not doi:
        return None
    url = f"{OPENALEX_BASE}/works/doi:{urllib.parse.quote(doi, safe='/:.')}?mailto={urllib.parse.quote(MAILTO)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"paper-pipeline/1.0 ({MAILTO})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"  ! openalex fetch failed for {doi}: {exc}", file=sys.stderr)
        return None


def reconstruct_abstract(work: dict | None) -> str | None:
    if not work:
        return None
    inverted = work.get("abstract_inverted_index") or {}
    if not inverted:
        return None
    positions = []
    for token, idx_list in inverted.items():
        for idx in idx_list:
            positions.append((idx, token))
    positions.sort()
    return " ".join(token for _, token in positions)


def venue_from_bib(entry: dict) -> str:
    return entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""


def derive_record(key: str, entry: dict, work: dict | None) -> dict:
    title = (work or {}).get("title") or entry.get("title", "")
    authors_oa = []
    if work and work.get("authorships"):
        for a in work["authorships"]:
            name = (a.get("author") or {}).get("display_name")
            if name:
                authors_oa.append(name)
    authors = authors_oa or split_authors(entry.get("author", ""))
    year = (work or {}).get("publication_year") or entry.get("year") or ""
    venue = ""
    if work and work.get("primary_location"):
        loc = work["primary_location"] or {}
        src = (loc.get("source") or {}) if isinstance(loc, dict) else {}
        venue = src.get("display_name") or ""
    if not venue:
        venue = venue_from_bib(entry)
    doi = entry.get("doi")
    if not doi and work and work.get("doi"):
        doi = work["doi"].replace("https://doi.org/", "")
    arxiv_id = entry.get("eprint") if entry.get("archiveprefix", "").lower() == "arxiv" else ""
    landing = ""
    if work and work.get("primary_location"):
        landing = (work["primary_location"] or {}).get("landing_page_url") or ""
    url = entry.get("url") or landing or (f"https://doi.org/{doi}" if doi else "")
    abstract = reconstruct_abstract(work) or ""
    return {
        "key": key,
        "title": title,
        "authors": authors,
        "year": str(year),
        "venue": venue,
        "doi": doi or "",
        "arxiv_id": arxiv_id or "",
        "url": url,
        "abstract": abstract,
    }


def render_section(rec: dict) -> str:
    authors = ", ".join(rec["authors"]) if rec["authors"] else "(authors unknown)"
    doi_line = f"[{rec['doi']}](https://doi.org/{rec['doi']})" if rec["doi"] else "—"
    arxiv_line = (
        f"[{rec['arxiv_id']}](https://arxiv.org/abs/{rec['arxiv_id']})"
        if rec["arxiv_id"] else "—"
    )
    url_line = f"<{rec['url']}>" if rec["url"] else "—"
    abstract = rec["abstract"] or "_Abstract not retrieved. Add manually after fetching from publisher._"
    return (
        f"## `{rec['key']}`\n\n"
        f"- **Title:** {rec['title']}\n"
        f"- **Authors:** {authors}\n"
        f"- **Year:** {rec['year']}\n"
        f"- **Venue:** {rec['venue'] or '—'}\n"
        f"- **DOI:** {doi_line}\n"
        f"- **arXiv:** {arxiv_line}\n"
        f"- **URL:** {url_line}\n\n"
        f"### Abstract\n\n{abstract}\n\n"
        f"### Notes\n\n_(blank, fill in manually)_\n"
    )


def derive_paper_slug(paper_dir: Path) -> str:
    name = paper_dir.name
    for prefix in TEMPLATE_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def render_document(paper_dir: Path, slug: str, records: list[dict], stats: dict) -> str:
    today = _dt.date.today().isoformat()
    head = (
        f"# References, {slug}\n\n"
        f"Source paper: `papers-latex/{paper_dir.name}/`\n\n"
        f"Generated by `paper-pipeline/scripts/import_references.py` on {today}.\n\n"
        f"Total cited keys: {stats['total']}. "
        f"With abstracts: {stats['with_abstract']}. "
        f"Without DOI: {stats['no_doi']}.\n\n"
        f"Each section below corresponds to one `\\cite{{}}` key used in the source paper. "
        f"Cite keys follow the `lastnameKeywordYear` convention. "
        f"Sections are sorted alphabetically by key.\n\n---\n\n"
    )
    body = "\n---\n\n".join(render_section(r) for r in records)
    return head + body + "\n"


def main(argv: list[str]) -> int:
    if len(argv) >= 2:
        paper_dir = Path(argv[1]).resolve()
    else:
        paper_dir = PAPER_PIPELINE / "papers-latex" / "tsp_survey"

    if not paper_dir.is_dir():
        print(f"not a directory: {paper_dir}", file=sys.stderr)
        return 1

    tex_files = sorted(paper_dir.glob("*.tex"))
    bib_files = sorted(paper_dir.glob("*.bib"))
    if not tex_files or not bib_files:
        print(f"missing .tex or .bib in {paper_dir}", file=sys.stderr)
        return 1
    tex_path = tex_files[0]
    bib_path = bib_files[0]

    keys = find_cited_keys(tex_path)
    bib = parse_bib(bib_path)
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"paper: {paper_dir}")
    print(f"  .tex: {tex_path.name}")
    print(f"  .bib: {bib_path.name}")
    print(f"  cited keys: {len(keys)}; bib entries: {len(bib)}")

    records: list[dict] = []
    no_doi = 0
    with_abstract = 0
    for i, key in enumerate(keys, 1):
        entry = bib.get(key, {"kind": "unknown", "raw": "", "title": f"<missing bib entry: {key}>"})
        doi = entry.get("doi")
        if not doi:
            no_doi += 1
        work = fetch_openalex(doi)
        rec = derive_record(key, entry, work)
        if rec["abstract"]:
            with_abstract += 1
        records.append(rec)
        marker = "OA hit" if work else ("missing bib" if not entry.get("title") else "bib only")
        print(f"  [{i:3d}/{len(keys)}] {key} ({marker})")
        if work:
            time.sleep(0.15)

    slug = derive_paper_slug(paper_dir)
    out_path = REFERENCES_DIR / f"{slug}.md"
    stats = {"total": len(records), "with_abstract": with_abstract, "no_doi": no_doi}
    out_path.write_text(render_document(paper_dir, slug, records, stats), encoding="utf-8")

    print(f"\nwritten: {out_path.relative_to(PAPER_PIPELINE)}")
    print(f"  total: {stats['total']}, with abstracts: {stats['with_abstract']}, no DOI: {stats['no_doi']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
