#!/usr/bin/env python3
import re, os, sys
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

BASE = "https://www.shoklo-unit.com"
URL  = "https://www.shoklo-unit.com/resources/reports"
UA   = {"User-Agent": "METF-mapping-bot/1.0 (+https://github.com/DMParker1/METF-mapping)"}

MARKER_START = "<!-- METF_REPORTS:START -->"
MARKER_END   = "<!-- METF_REPORTS:END -->"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], 1)}
FULL2SHORT = {
    "january":"jan","february":"feb","march":"mar","april":"apr","may":"may","june":"jun",
    "july":"jul","august":"aug","september":"sep","october":"oct","november":"nov","december":"dec"
}

def month_num(tok: str):
    t = FULL2SHORT.get(tok.strip().lower(), tok.strip().lower())
    return MONTHS.get(t)

def parse_date_from_text(s: str):
    s = s.strip()

    # e.g., "May 2014 to Dec 2019"
    m = re.search(r'([A-Za-z]{3,9})\s+(\d{4})\s+(?:to|–|-)\s+([A-Za-z]{3,9})\s+(\d{4})', s, re.I)
    if m:
        mo2, yr2 = month_num(m.group(3)), int(m.group(4))
        if mo2: return datetime(yr2, mo2, 1)

    # e.g., "2014 to 2018" or "2014–2019"
    m = re.search(r'(\d{4})\s*(?:to|–|-)\s*(\d{4})', s)
    if m:
        return datetime(int(m.group(2)), 12, 31)

    # e.g., "March 2016"
    m = re.search(r'([A-Za-z]{3,9})\s+(\d{4})', s)
    if m:
        mo, yr = month_num(m.group(1)), int(m.group(2))
        if mo: return datetime(yr, mo, 1)

    # lone year
    m = re.search(r'\b(20\d{2}|19\d{2})\b', s)
    if m:
        return datetime(int(m.group(1)), 12, 31)
    return None

def parse_date_from_href(href: str):
    name = href.split("/")[-1].lower()

    # e.g., ..._mar2016.pdf
    m = re.search(r'[_\-\.]([a-z]{3})(20\d{2}|19\d{2})', name)
    if m and m.group(1) in MONTHS:
        return datetime(int(m.group(2)), MONTHS[m.group(1)], 1)

    # e.g., ...2014-2018.pdf or ...2014to2018.pdf
    m = re.findall(r'(19|20)\d{2}', name)
    if len(m) >= 2:
        years = [int(x.group(0)) if hasattr(x, "group") else int(x) for x in re.finditer(r'(19|20)\d{2}', name)]
        if years:
            return datetime(max(years), 12, 31)

    # lone year
    m = re.search(r'(20\d{2}|19\d{2})', name)
    if m:
        return datetime(int(m.group(1)), 12, 31)
    return None

def last_modified(url: str):
    try:
        h = requests.head(url, headers=UA, timeout=12, allow_redirects=True)
        if 'Last-Modified' in h.headers:
            return parsedate_to_datetime(h.headers['Last-Modified']).replace(tzinfo=None)
    except Exception:
        pass
    return None

def fetch_items():
    r = requests.get(URL, headers=UA, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    for a in soup.select("a[href]"):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if "files/resources/reports" in href and "metf" in href.lower():
            abs_url = urljoin(BASE, href)
            d = (parse_date_from_text(text) or
                 parse_date_from_href(href) or
                 last_modified(abs_url) or
                 datetime(1900,1,1))
            title = text or abs_url.split("/")[-1]
            items.append((d, title, abs_url))
    # dedupe by URL
    seen, out = set(), []
    for d, t, u in items:
        if u not in seen:
            seen.add(u)
            out.append((d, t, u))
    # newest first
    out.sort(key=lambda x: x[0], reverse=True)
    return out

def build_markdown(items):
    lines = ["## METF reports (SMRU)", ""]
    for d, title, url in items:
        tag = d.strftime("%Y-%m") if d.year > 1900 else ""
        disp = f"{title} ({tag})" if tag and tag not in title else title
        lines.append(f"- [{disp}]({url})")
    lines.append("")  # trailing newline
    return "\n".join(lines)

def update_readme(md):
    path = "README.md"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if MARKER_START not in content or MARKER_END not in content:
        # append section if markers missing
        block = f"{MARKER_START}\n{md}\n{MARKER_END}"
        content = content.rstrip() + "\n\n" + block + "\n"
    else:
        # replace between markers
        pattern = re.compile(
            re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
            flags=re.DOTALL
        )
        block = f"{MARKER_START}\n{md}\n{MARKER_END}"
        content = pattern.sub(block, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    items = fetch_items()
    md = build_markdown(items)
    update_readme(md)

if __name__ == "__main__":
    main()
