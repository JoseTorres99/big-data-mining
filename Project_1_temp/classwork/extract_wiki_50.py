import csv
import glob
import os
import re
from bs4 import BeautifulSoup

HTML_DIR = "wiki_html_A"
OUT_CSV = "tableA.csv"

FIELDS = ["ID","title","release_year","genre","director","runtime_minutes","imdb_rating","rotten_tomatoes_score"]

def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()

def parse_infobox_value(soup: BeautifulSoup, label: str) -> str:
    infobox = soup.select_one("table.infobox")
    if not infobox:
        return ""
    for row in infobox.select("tr"):
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        if clean(th.get_text(" ", strip=True)).lower() == label.lower():
            return clean(td.get_text(" ", strip=True))
    return ""

def runtime_to_minutes(text: str) -> str:
    t = (text or "").lower()
    m = re.search(r"(\d+)\s*(?:minutes|minute|min)\b", t)
    if m:
        return m.group(1)
    mh = re.search(r"(\d+)\s*h", t)
    mm = re.search(r"(\d+)\s*m", t)
    if mh:
        hours = int(mh.group(1))
        mins = int(mm.group(1)) if mm else 0
        return str(hours * 60 + mins)
    return ""

def year_from_filename(filename: str) -> str:
    m = re.search(r"^\d+_(19\d{2}|20\d{2})_", filename)
    return m.group(1) if m else ""

def main(limit=1000):
    files = sorted(glob.glob(os.path.join(HTML_DIR, "*.html")))
    if not files:
        raise SystemExit(f"No HTML files found in {HTML_DIR}/")

    rows = []
    seen_ids = set()

    for fp in files:
        base = os.path.basename(fp)
        year = year_from_filename(base)

        slug = base.replace(".html", "")
        parts = slug.split("_", 2)
        wiki_id = parts[2] if len(parts) == 3 else slug

        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        title_el = soup.select_one("h1#firstHeading")
        title = clean(title_el.get_text()) if title_el else ""
        if not title:
            continue

        director = parse_infobox_value(soup, "Directed by")
        runtime_raw = parse_infobox_value(soup, "Running time")
        runtime_minutes = runtime_to_minutes(runtime_raw)

        if wiki_id in seen_ids:
            continue
        seen_ids.add(wiki_id)

        rows.append({
            "ID": wiki_id,
            "title": title,
            "release_year": year,
            "genre": "Horror",
            "director": director,
            "runtime_minutes": runtime_minutes,
            "imdb_rating": "",
            "rotten_tomatoes_score": ""
        })

        if len(rows) >= limit:
            break

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_CSV} with {len(rows)} rows.")

if __name__ == "__main__":
    main(limit=1000)
