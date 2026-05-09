#!/usr/bin/env python3
"""
Verify a paper's bib entries against OpenAlex.

For each cite key actually used in the paper:
  - Look up the bib entry.
  - If the bib entry has a DOI, fetch OpenAlex.
  - Compare author surname sets, year, and a loose title check.
  - Print findings grouped by severity:
        ERROR    bib author set differs significantly from OpenAlex
        WARN     year differs
        WARN     title differs in a substantive way (not just punctuation)
        OK       all checks pass
        SKIP     no DOI in bib, cannot verify automatically

Usage:
    python3 verify_references.py <paper-directory>

Defaults to the tsp_survey paper if no argument is given.
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

PAPER_PIPELINE = Path(__file__).resolve().parent.parent
MAILTO = "vinceabella05@gmail.com"
OPENALEX_BASE = "https://api.openalex.org"


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
    starts = [(m.start(), m.group(2)) for m in pattern.finditer(text)]
    for i, (start, key) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        body = text[start:end]
        entries[key] = parse_fields(body)
    return entries


def parse_fields(body: str) -> dict:
    fields = {}
    for fname in ("title", "author", "year", "doi"):
        m = re.search(rf"\b{fname}\s*=\s*", body, re.IGNORECASE)
        if not m:
            continue
        pos = m.end()
        if pos >= len(body):
            continue
        first = body[pos]
        if first == "{":
            depth, i = 1, pos + 1
            while i < len(body) and depth:
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
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
        fields[fname] = re.sub(r"[{}]", "", raw).strip()
    return fields


LATEX_ACCENT_REGEX = re.compile(r'\\["\'^~`=.uvHtcdbk]')
LATEX_LETTER_REGEX = re.compile(r'\\(ae|AE|oe|OE|ss|aa|AA|o|O|l|L|i|I|j|J)')
UNICODE_TO_ASCII = str.maketrans({
    "ø": "o", "Ø": "o",
    "æ": "ae", "Æ": "ae",
    "ß": "ss",
    "ł": "l", "Ł": "l",
    "å": "a", "Å": "a",
})


def normalize(s: str) -> str:
    s = LATEX_ACCENT_REGEX.sub("", s)
    s = LATEX_LETTER_REGEX.sub(r"\1", s)
    s = s.translate(UNICODE_TO_ASCII)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def surname_from(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    if "," in name:
        return normalize(name.split(",", 1)[0])
    parts = name.split()
    if not parts:
        return ""
    return normalize(parts[-1])


def surname_tokens(name: str) -> set[str]:
    """Token set of the surname portion of one bib author name.

    Handles hyphenated surnames like "Salles-Loustau" by treating them as a
    multi-token set, so the comparison still passes if any constituent token
    appears in the OpenAlex display name.
    """
    name = name.strip()
    if not name:
        return set()
    if "," in name:
        surname = normalize(name.split(",", 1)[0])
    else:
        parts = normalize(name).split()
        surname = parts[-1] if parts else ""
    return set(surname.split()) if surname else set()


def split_bib_authors(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"\s+and\s+", raw)
    return [p.strip() for p in parts if p.strip()]


def fetch_openalex(doi: str) -> dict | None:
    url = f"{OPENALEX_BASE}/works/doi:{urllib.parse.quote(doi, safe='/:.')}?mailto={urllib.parse.quote(MAILTO)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"paper-pipeline/1.0 ({MAILTO})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"_error": str(exc)}


def search_openalex_title_author(title: str, first_surname: str) -> dict | None:
    """Soft-match fallback: search OpenAlex by title and accept any hit
    whose title is similar and whose authorships contain the bib's first
    author surname."""
    title_clean = re.sub(r"\{|\}", "", title or "").strip()
    if not title_clean or not first_surname:
        return None
    qs = urllib.parse.urlencode({
        "search": f"{title_clean} {first_surname}",
        "per-page": "5",
        "mailto": MAILTO,
    })
    url = f"{OPENALEX_BASE}/works?{qs}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"paper-pipeline/1.0 ({MAILTO})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    for r in data.get("results", []):
        oa_title = r.get("title", "")
        if not title_similar(title_clean, oa_title):
            continue
        oa_token_union: set[str] = set()
        for a in r.get("authorships") or []:
            name = (a.get("author") or {}).get("display_name", "")
            oa_token_union.update(normalize(name).split())
        if first_surname in oa_token_union:
            return r
    return None


def oa_authors(work: dict) -> list[str]:
    out = []
    for a in work.get("authorships") or []:
        name = (a.get("author") or {}).get("display_name")
        if name:
            out.append(name)
    return out


def title_similar(a: str, b: str) -> bool:
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # If one contains the other after normalization, treat as match
    if na in nb or nb in na:
        return True
    # Token Jaccard
    ta, tb = set(na.split()), set(nb.split())
    if not ta or not tb:
        return False
    j = len(ta & tb) / len(ta | tb)
    return j >= 0.6


def compare(key: str, bib: dict, work: dict | None) -> dict:
    finding = {"key": key, "level": "OK", "messages": []}
    if work is None:
        finding["level"] = "SKIP"
        finding["messages"].append("no DOI in bib")
        return finding
    if "_error" in work:
        finding["level"] = "WARN"
        finding["messages"].append(f"openalex fetch failed: {work['_error']}")
        return finding

    bib_authors = split_bib_authors(bib.get("author", ""))
    bib_author_tokens: list[set[str]] = [
        toks for toks in (surname_tokens(a) for a in bib_authors) if toks
    ]
    oa_list = oa_authors(work)
    oa_token_union: set[str] = set()
    for a in oa_list:
        oa_token_union.update(normalize(a).split())

    if bib_author_tokens and oa_token_union:
        missing_authors: list[set[str]] = []
        for tokens in bib_author_tokens:
            if not (tokens & oa_token_union):
                missing_authors.append(tokens)
        n_total = len(bib_author_tokens)
        n_missing = len(missing_authors)
        ratio = (n_total - n_missing) / n_total
        if missing_authors:
            if ratio < 0.5:
                finding["level"] = "ERROR"
                finding["messages"].append(
                    f"author overlap {ratio:.2f} too low, bib surname-tokens absent from openalex: {[sorted(t) for t in missing_authors]}, openalex tokens: {sorted(oa_token_union)}"
                )
            else:
                finding["level"] = "WARN"
                finding["messages"].append(
                    f"bib authors with no matching openalex token: {[sorted(t) for t in missing_authors]}"
                )
        if len(oa_list) > 0 and abs(len(oa_list) - n_total) > max(1, n_total // 4):
            if finding["level"] == "OK":
                finding["level"] = "WARN"
            finding["messages"].append(
                f"author count differs significantly, bib={len(bib_authors)}, openalex={len(oa_list)}"
            )
    elif not oa_token_union:
        finding["level"] = "WARN"
        finding["messages"].append("openalex returned no authors")

    bib_year = bib.get("year")
    oa_year = work.get("publication_year")
    if bib_year and oa_year:
        try:
            if abs(int(bib_year) - int(oa_year)) > 1:
                if finding["level"] == "OK":
                    finding["level"] = "WARN"
                finding["messages"].append(f"year mismatch, bib={bib_year}, openalex={oa_year}")
        except ValueError:
            pass

    bib_title = bib.get("title", "")
    oa_title = work.get("title", "")
    if bib_title and oa_title and not title_similar(bib_title, oa_title):
        if finding["level"] == "OK":
            finding["level"] = "WARN"
        finding["messages"].append(f"title differs, bib={bib_title!r}, openalex={oa_title!r}")

    return finding


PROSE_PATTERN = re.compile(
    r"([A-Z][\w'\-]+)\s+(?:et\s+al\.?|and\s+([A-Z][\w'\-]+))[~ ]*\\cite\{([^}]+)\}"
)


def lead_surname(bib_author_raw: str) -> str:
    authors = split_bib_authors(bib_author_raw)
    if not authors:
        return ""
    return surname_from(authors[0])


def verify_prose(tex_path: Path, bib: dict[str, dict]) -> list[dict]:
    text = tex_path.read_text(encoding="utf-8", errors="ignore")
    findings: list[dict] = []
    for m in PROSE_PATTERN.finditer(text):
        first = normalize(m.group(1))
        second = normalize(m.group(2) or "")
        cite_block = m.group(3)
        for raw_key in cite_block.split(","):
            key = raw_key.strip()
            entry = bib.get(key)
            if not entry:
                continue
            lead = lead_surname(entry.get("author", ""))
            if not lead:
                continue
            attributed = {first}
            if second:
                attributed.add(second)
            if lead in attributed:
                continue
            attributed_authors = split_bib_authors(entry.get("author", ""))
            attributed_surnames = {surname_from(a) for a in attributed_authors}
            if attributed & attributed_surnames:
                continue
            findings.append({
                "key": key,
                "prose": m.group(0).strip(),
                "lead": lead,
                "attributed": sorted(attributed),
            })
    return findings


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
    tex_path, bib_path = tex_files[0], bib_files[0]

    keys = find_cited_keys(tex_path)
    bib = parse_bib(bib_path)
    findings: list[dict] = []
    print(f"verifying {len(keys)} keys...", file=sys.stderr)
    for i, key in enumerate(keys, 1):
        entry = bib.get(key)
        if not entry:
            findings.append({"key": key, "level": "ERROR", "method": "none", "messages": ["missing bib entry"]})
            continue
        doi = entry.get("doi")
        method = "no-identifiers"
        work: dict | None = None
        if doi:
            work = fetch_openalex(doi)
            method = "doi"
        else:
            first_surname = lead_surname(entry.get("author", ""))
            title = entry.get("title", "").strip()
            if first_surname and title:
                work = search_openalex_title_author(title, first_surname)
                method = "title-found" if work else "title-no-match"
        f = compare(key, entry, work)
        f["method"] = method
        if method == "title-found" and f["level"] == "OK":
            f["level"] = "OK*"
        findings.append(f)
        print(f"  [{i:3d}/{len(keys)}] {f['level']:5} {key} ({method})", file=sys.stderr)
        if work and "_error" not in (work or {}):
            time.sleep(0.15)

    levels = {"ERROR": 0, "WARN": 0, "OK": 0, "OK*": 0, "SKIP": 0}
    for f in findings:
        levels[f["level"]] = levels.get(f["level"], 0) + 1

    print()
    print(
        f"summary: ERROR={levels['ERROR']} WARN={levels['WARN']} "
        f"OK={levels['OK']} OK*={levels['OK*']} SKIP={levels['SKIP']}"
    )
    print("OK             = DOI verified against OpenAlex.")
    print("OK*            = title + first-author verified against OpenAlex (no DOI in bib).")
    print("SKIP           = no DOI verified against OpenAlex.")
    print("Method values  : doi, title-found, title-no-match, no-identifiers.")
    print()

    for level in ("ERROR", "WARN"):
        items = [f for f in findings if f["level"] == level]
        if not items:
            continue
        print(f"== {level} ({len(items)}) ==")
        for f in items:
            print(f"  {f['key']}")
            for msg in f["messages"]:
                print(f"      - {msg}")
        print()

    print()
    print("== prose attributions ==")
    prose_findings = verify_prose(tex_path, bib)
    if not prose_findings:
        print("  no mismatches detected")
    else:
        print(f"  {len(prose_findings)} mismatch(es) detected:")
        for f in prose_findings:
            print(f"  {f['key']}")
            print(f"      prose says     : {f['attributed']}")
            print(f"      bib lead author: {f['lead']!r}")
            print(f"      context        : {f['prose'][:120]}")
        print()
    return 0 if (levels["ERROR"] == 0 and not prose_findings) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
