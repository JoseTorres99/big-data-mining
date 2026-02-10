import os
import re
import csv
from bs4 import BeautifulSoup

WIKI_HTML_DIR = "wiki_html"
OUT_CSV = "tableB.csv"

FIELDS = [
    "ID",
    "title",
    "release_year",
    "genre",
    "director",
    "runtime_minutes",
    "imdb_rating",
    "rotten_tomatoes_score",
]

def clean(text: str) -> str:
    text = text or ""
    text = re.sub(r"\s+", " ", text).strip()
    return text

def infer_year_from_filename(filename: str) -> str:
    m = re.search(r"(\d{4})", filename)
    return m.group(1) if m else ""

def extract_rows_from_wiki_page(html_path: str):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    year = infer_year_from_filename(os.path.basename(html_path))

    rows = []
    # Wikipedia lists usually have one or more "wikitable" tables.
    tables = soup.select("table.wikitable")
    for tbl in tables:
        # Get header names so we can locate "Film" and "Director" columns when present.
        header_cells = tbl.select("tr th")
        headers = [clean(th.get_text(" ", strip=True)).lower() for th in header_cells]

        # Find likely indices (best-effort)
        # Many pages have headers like Film / Director / Cast / Notes
        title_idx = None
        director_idx = None

        # If headers were captured in the first row only, handle that below.
        # We'll compute from the first row that actually contains <th>.
        first_header_row = tbl.select_one("tr")
        if first_header_row and first_header_row.select("th"):
            hdrs = [clean(th.get_text(" ", strip=True)).lower() for th in first_header_row.select("th")]
            for i, h in enumerate(hdrs):
                if "film" in h or "title" in h:
                    title_idx = i
                if "director" in h:
                    director_idx = i

        # Now parse body rows
        for tr in tbl.select("tr"):
            tds = tr.select("td")
            if not tds:
                continue

            # Title is usually the first td if we can't detect header
            t_i = title_idx if title_idx is not None and title_idx < len(tds) else 0
            d_i = director_idx if director_idx is not None and director_idx < len(tds) else None

            title = clean(tds[t_i].get_text(" ", strip=True))
            if not title:
                continue

            director = ""
            if d_i is not None:
                director = clean(tds[d_i].get_text(" ", strip=True))

            rows.append({
                "title": title,
                "release_year": year,
                "genre": "Horror",
                "director": director,
                "runtime_minutes": "",
                "imdb_rating": "",
                "rotten_tomatoes_score": "",
            })

    return rows

def main():
    html_files = sorted(
        f for f in os.listdir(WIKI_HTML_DIR)
        if f.lower().endswith(".html")
    )

    all_rows = []
    for f in html_files:
        path = os.path.join(WIKI_HTML_DIR, f)
        page_rows = extract_rows_from_wiki_page(path)
        all_rows.extend(page_rows)

    # De-dupe by (title, year) so you get closer to 1000 unique tuples
    seen = set()
    deduped = []
    for r in all_rows:
        key = (r["title"].lower(), r["release_year"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    # Assign IDs
    for i, r in enumerate(deduped, start=1):
        r["ID"] = f"w{i:06d}"

    # Write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()
        for r in deduped:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    print(f"Saved {len(deduped)} rows to {OUT_CSV}")

    if len(deduped) < 1000:
        print("WARNING: < 1000 rows. Expand year range (e.g., 1950–2020) or add more wiki pages.")

if __name__ == "__main__":
    main()
