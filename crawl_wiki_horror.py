import os
import time
import requests

OUT_DIR = "wiki_html"

# Adjust the range if you want more/less
START_YEAR = 1970
END_YEAR = 2000  # inclusive

BASE = "https://en.wikipedia.org/wiki/List_of_horror_films_of_{}"

HEADERS = {
    # Wikipedia asks that automated requests identify themselves.
    "User-Agent": "CS739_HW1 (student project) - polite crawler; contact: your_email@example.com"
}

DELAY_SECONDS = 1.2  # be polite

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ok = 0
    fail = 0

    for year in range(START_YEAR, END_YEAR + 1):
        url = BASE.format(year)
        out_path = os.path.join(OUT_DIR, f"wiki_horror_{year}.html")

        print(f"Downloading {year} -> {out_path}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and "<html" in r.text.lower():
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(r.text)
                ok += 1
            else:
                print(f"  !! Failed {year}: status={r.status_code}, bytes={len(r.text)}")
                fail += 1
        except Exception as e:
            print(f"  !! Error {year}: {e}")
            fail += 1

        time.sleep(DELAY_SECONDS)

    print(f"\nDone. Success: {ok}, Failed: {fail}")
    print(f"HTML saved to: {OUT_DIR}/")

if __name__ == "__main__":
    main()
