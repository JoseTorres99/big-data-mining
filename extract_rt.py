import os, time, re, json
import requests
from bs4 import BeautifulSoup

MIN_YEAR = 1970
MAX_YEAR = 2000
MAX_BROWSE_PAGES = 160

BROWSE_URL = "https://www.rottentomatoes.com/browse/movies_at_home/genres:horror?page={}"
MOVIE_URL  = "https://www.rottentomatoes.com/m/{}"

OUT_DIR = "rt_html"
os.makedirs(OUT_DIR, exist_ok=True)

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def extract_year(text: str) -> int:
    m = re.search(r"(19\d{2}|20\d{2})", text or "")
    return int(m.group(1)) if m else 0

def parse_movie_page(html: str):
    soup = BeautifulSoup(html, "lxml")
    title = ""
    year = 0

    if soup.title and soup.title.text:
        t = clean(soup.title.text)
        title = clean(re.sub(r"\(\d{4}\).*", "", t))
        year = extract_year(t)

    txt = clean(soup.get_text(" ", strip=True))
    is_horror = ("Genre" in txt and "Horror" in txt) or (" Horror " in f" {txt} ")

    return title, year, is_horror

def extract_slugs_from_browse_html(html: str):
    slugs = set()

    # 1) Direct /m/<slug> links (works when present)
    for m in re.findall(r'href="(/m/[^"?]+)"', html):
        slug = m.split("/m/", 1)[1].strip("/ ")
        if slug:
            slugs.add(slug)

    # 2) Embedded JSON blobs often contain "/m/<slug>" too
    # Grab big script blocks and scan for /m/
    for blob in re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S | re.I):
        if "/m/" not in blob:
            continue
        for mm in re.findall(r'"/m/([^"/?]+)"', blob):
            if mm:
                slugs.add(mm)

    return sorted(slugs)

def main():
    seen = set()
    saved = 0

    for page in range(1, MAX_BROWSE_PAGES + 1):
        url = BROWSE_URL.format(page)
        print("[browse] downloading:", url)

        r = session.get(url, headers=headers, timeout=30)
        if r.status_code != 200 or len(r.text) < 2000:
            print("Browse page blocked/empty. Stopping.")
            break

        slugs = extract_slugs_from_browse_html(r.text)
        print(f"[browse] page {page} slugs found:", len(slugs))

        if not slugs:
            print("No slugs found. Stopping.")
            break

        for slug in slugs:
            if slug in seen:
                continue
            seen.add(slug)

            movie_url = MOVIE_URL.format(slug)
            print("  -> fetching:", movie_url)

            mr = session.get(movie_url, headers=headers, timeout=30)
            if mr.status_code != 200 or len(mr.text) < 2000:
                continue

            title, year, is_horror = parse_movie_page(mr.text)
            if not is_horror:
                continue
            if year < MIN_YEAR or year > MAX_YEAR:
                continue

            out_path = os.path.join(OUT_DIR, f"{slug}.html")
            if os.path.exists(out_path):
                continue

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(mr.text)

            saved += 1
            print(f"    ✅ saved: {title} ({year}) -> {out_path}")
            time.sleep(1)

        time.sleep(2)

    print(f"RT download complete. Saved {saved} movie HTML files in {OUT_DIR}/")

if __name__ == "__main__":
    main()
