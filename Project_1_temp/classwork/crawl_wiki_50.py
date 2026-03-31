import os, re, time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

OUT_DIR = "wiki_html_A"
MIN_YEAR = 1990
MAX_YEAR = 2020
TARGET = 1000
SLEEP = 1.5

BASE = "https://en.wikipedia.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()

def get(url: str) -> str:
    for attempt in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(3 + attempt * 2)
                continue
            r.raise_for_status()
            return r.text
        except Exception:
            time.sleep(2 + attempt * 2)
    raise RuntimeError(f"Failed after retries: {url}")

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def slug_from_href(href: str) -> str:
    return href.split("/wiki/", 1)[1].split("#", 1)[0]

def collect_movie_links(html: str):
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one("div#mw-content-text")
    if not content:
        return []

    links = []

    for a in content.select("table.wikitable a[href^='/wiki/']"):
        href = a.get("href", "")
        title = clean(a.get_text())
        if not href.startswith("/wiki/"):
            continue
        if ":" in href:
            continue
        if title and len(title) > 1:
            links.append(href)

    for a in content.select("ul a[href^='/wiki/']"):
        href = a.get("href", "")
        title = clean(a.get_text())
        if not href.startswith("/wiki/"):
            continue
        if ":" in href:
            continue
        if title and len(title) > 1:
            links.append(href)

    seen = set()
    out = []
    for href in links:
        if href not in seen:
            seen.add(href)
            out.append(href)
    return out

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    saved = 0
    seen_slugs = set()

    for year in range(MIN_YEAR, MAX_YEAR + 1):
        if saved >= TARGET:
            break

        year_url = f"{BASE}/wiki/List_of_horror_films_of_{year}"
        print(f"[YEAR] {year} -> {year_url}")

        try:
            html = get(year_url)
        except Exception as e:
            print("  !! failed year page:", e)
            continue

        year_links = collect_movie_links(html)
        print(f"  found {len(year_links)} candidate links")

        for idx, href in enumerate(year_links, 1):
            if saved >= TARGET:
                break

            slug = slug_from_href(href)
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            movie_url = urljoin(BASE, href)

            try:
                mhtml = get(movie_url)
            except Exception as e:
                # print occasional failures but keep going
                if idx % 25 == 0:
                    print(f"  .. skipped (fetch fail) {movie_url}")
                continue

            if "class=\"infobox" not in mhtml:
                continue

            out_path = os.path.join(OUT_DIR, f"{saved+1:05d}_{year}_{slug}.html")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(mhtml)

            saved += 1

            if saved % 10 == 0:
                print(f"  saved {saved}/{TARGET}")

            time.sleep(SLEEP)

        time.sleep(SLEEP)

    print(f"Done. Saved {saved} HTML pages in {OUT_DIR}/")

if __name__ == "__main__":
    main()
