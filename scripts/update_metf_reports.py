#!/usr/bin/env python3
import re
from datetime import datetime
from urllib.parse import urljoin
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup

BASE = "https://www.shoklo-unit.com"
URL  = "https://www.shoklo-unit.com/resources/reports"
UA   = {"User-Agent": "METF-mapping-bot/1.1 (+https://github.com/DMParker1/METF-mapping)"}

MARKER_START = "<!-- METF_REPORTS:START -->"
MARKER_END   = "<!-- METF_REPORTS:END -->"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}
FULL2SHORT = {
    "january":"jan","february":"feb","march":"mar","april":"apr","may":"may","june":"jun",
    "july":"jul","august":"aug","september":"sep","october":"oct","november":"nov","december":"dec"
}

def month_num(tok: str) -> int | None:
    t = FULL2SHORT.get(tok.strip().lower(), tok.strip().lower())
    return MONTHS.get(t)

# ---- text/filename/header parsers ------------------------------------------

def best_date_from_text(s: str) -> datetime | None:
    """Find the *latest* date mentioned in text, preferring the end of ranges."""
    s = " ".join(s.split())  # collapse whitespace

    # 1) Month Year to Month Year (prefer end)
    for m in re.finditer(r'([A-Za-z]{3,9})\s+(\d{4})\s*(?:to|–|-|—)\s*([A-Za-z]{3,9})\s+(\d{4})', s, re.I):
        mo2, yr2 = month_num(m.group(3)), int(m.group(4))
        if mo2: 
            return datetime(yr2, mo2, 1)

    # 2) Year to Year (prefer end)
    yrs = [int(y) for y in re.findall(r'\b(19|20)\d{2}\b\s*(?:to|–|-|—)\s*\b(19|20)\d{2}\b', s)]
    if yrs:
        return datetime(max(yrs), 12, 31)

    # 3) Any Month Year mentions → choose latest month/year found
    candidates = []
    for m in re.finditer(r'([A-Za-z]{3,9})\s+(\d{4})', s):
        mo = month_num(m.group(1))
        yr = int(m.group(2))
        if mo:
            candidates.append(datetime(yr, mo, 1))
    if candidates:
        return max(candidates)

    # 4) Lone years → choose latest
    years = [int(y) for y in re.findall(r'\b(19|20)\d{2}\b', s)]
    if years:
        return datetime(max(years), 12, 31)
    return None

def parse_date_from_href(href: str) -> datetime | None:
    name = href.split("/")[-1].lower()

    # e.g., ..._mar2016.pdf
    m = re.search(r'[_\-\.]([a-z]{3})(20\d{2}|19\d{2})', name)
    if m and m.group(1) in MONTHS:
        return datetime(int(m.group(2)), MONTHS[m.group(1)], 1)

    # year ranges like ...2014-2019.pdf
    yrs = [int(y) for y in re.findall(r'(19|20)\d{2}', name)]
    if len(yrs) >= 2:
        return datetime(max(yrs), 12, 31)

    if yrs:
        return datetime(max(yrs), 12, 31)
    return None

def last_modified(url: str) -> datetime | None:
    try:
        h = requests.head(url, headers=UA, timeout=12, allow_redirects=True)
        if 'Last-Modified' in h.headers:
            return parsedate_to_datetime(h.headers['Last-Modified']).replace(tzinfo=None)
    except Exception:
        pass
    return None

# ---- PDF text extraction ----------------------------------------------------

def date_from_pdf(url: str) -> datetime | None:
    """Download the PDF (first ~2 pages) and parse dates from its text."""
    try:
        r = requests.get(url, headers=UA, timeout=40)
        r.raise_for_status()
        from io import BytesIO
        from pdfminer.high_level import extract_text
        # Only first 2 pages; title pages usually contain the report date
        txt = extract_text(BytesIO(r.content), maxpages=2) or ""
        return best_date_from_text(txt)
    except Exception:
        return None

# ---- main scraping / README update -----------------------------------------

def fetch_items():
    r = requests.get(URL, headers=UA, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    for a in soup.select("a[href]"):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if "files/resources/reports" in href and "metf" in href.lower():
            url = urljoin(BASE, href)
            # Prefer PDF text date > anchor text > filename > Last-Modified
            d = (date_from_pdf(url) or
                 best_date_from_text(text) or
                 parse_date_from_href(href) or
                 last_modified(url) or
                 datetime(1900,1,1))
            title = text or url.split("/")[-1]
            items.append((d, title, url))

    # Deduplicate by URL
    seen, out = set(), []
    for d, t, u in items:
        if u not in seen:
            seen.add(u)
            out.append((d, t, u))

    out.sort(key=lambda x: x[0], reverse=True)  # newest first
    return out

def build_markdown(items):
    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = ["## METF reports (SMRU)", f"_Auto-updated: {stamp}_", ""]
    for d, title, url in items:
        tag = d.strftime("%Y-%m") if d.year > 1900 else ""
        disp = f"{title} ({tag})" if tag and tag not in title else title
        lines.append(f"- [{disp}]({url})")
    lines.append("")
    return "\n".join(lines)

def update_readme(md):
    path = "README.md"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    block = f"{MARKER_START}\n{md}\n{MARKER_END}"
    if MARKER_START not in content or MARKER_END not in content:
        content = content.rstrip() + "\n\n" + block + "\n"
    else:
        import re as _re
        pattern = _re.compile(_re.escape(MARKER_START)+r".*?"+_re.escape(MARKER_END), flags=_re.DOTALL)
        content = pattern.sub(block, content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    items = fetch_items()
    md = build_markdown(items)
    update_readme(md)

if __name__ == "__main__":
    main()
