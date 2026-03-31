import csv
import gzip
import re

# ---------------- CONFIG ----------------
RT_CSV_IN = "rt_movies.csv"          # downloaded CSV from the Reddit/Drive link
IMDB_BASICS_GZ = "title.basics.tsv.gz"
IMDB_RATINGS_GZ = "title.ratings.tsv.gz"

OUT_CSV = "tableB.csv"
TARGET_ROWS = 1000
MIN_YEAR = 1970
MAX_YEAR = 2000

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

# ---------------- HELPERS ----------------
def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()

def norm_title(s):
    s = clean(s).lower()
    s = re.sub(r"[\u2018\u2019\u201c\u201d]", "", s)  # smart quotes
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def year_from_text(s):
    m = re.search(r"(19\d{2}|20\d{2})", s or "")
    return int(m.group(1)) if m else 0

def to_int(s):
    try:
        return int(s)
    except:
        return 0

def open_gz_text(path):
    return gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="")

# ---------------- LOAD IMDB ----------------
def load_imdb_ratings(path_gz):
    ratings = {}
    with open_gz_text(path_gz) as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            tconst = parts[0]
            avg = parts[1]
            if tconst and avg and avg != r"\N":
                ratings[tconst] = avg
    return ratings

def load_imdb_horror_index(path_gz):
    # Build lookup: (norm_title, startYear) -> (tconst, runtimeMinutes, genres_str)
    idx = {}
    with open_gz_text(path_gz) as f:
        header = f.readline().rstrip("\n").split("\t")
        col = {name: i for i, name in enumerate(header)}

        need = ["tconst", "primaryTitle", "startYear", "runtimeMinutes", "genres", "titleType"]
        for n in need:
            if n not in col:
                raise RuntimeError(f"Missing column in IMDb basics: {n}")

        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(col.values()):
                continue

            title_type = parts[col["titleType"]]
            if title_type != "movie":
                continue

            start_year = parts[col["startYear"]]
            y = to_int(start_year)
            if y < MIN_YEAR or y > MAX_YEAR:
                continue

            genres = parts[col["genres"]]
            if not genres or genres == r"\N":
                continue

            # Keep only horror (IMDb genres are comma-separated)
            if "Horror" not in genres.split(","):
                continue

            title = parts[col["primaryTitle"]]
            if not title or title == r"\N":
                continue

            tconst = parts[col["tconst"]]
            runtime = parts[col["runtimeMinutes"]]
            runtime = "" if (not runtime or runtime == r"\N") else runtime

            key = (norm_title(title), y)
            # Keep first match; good enough for this assignment scale
            if key not in idx:
                idx[key] = (tconst, runtime, genres)
    return idx

# ---------------- LOAD RT CSV ----------------
def sniff_rt_columns(fieldnames):
    # Try common variations. We only need title, release date/year, critic score.
    f = { (name or "").strip().lower(): name for name in (fieldnames or []) }

    def pick(*cands):
        for c in cands:
            if c in f:
                return f[c]
        return ""

    col_title = pick("title", "movie_title", "movie", "name")
    col_release = pick("release_date", "releasedate", "release", "release year", "year", "release_year", "date")
    col_critic = pick("critic_score", "critics_score", "tomatometer", "tomatometer_score", "critics rating", "critics_rating", "critic rating")

    return col_title, col_release, col_critic

def main():
    imdb_ratings = load_imdb_ratings(IMDB_RATINGS_GZ)
    imdb_horror = load_imdb_horror_index(IMDB_BASICS_GZ)

    out_rows = []
    seen_ids = set()

    with open(RT_CSV_IN, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        col_title, col_release, col_critic = sniff_rt_columns(r.fieldnames)

        if not col_title or not col_release or not col_critic:
            raise RuntimeError(
                "rt_movies.csv columns not recognized.\n"
                f"Found columns: {r.fieldnames}\n"
                "Expected something like: title, release_date, critic_score/tomatometer."
            )

        for row in r:
            if len(out_rows) >= TARGET_ROWS:
                break

            title = clean(row.get(col_title, ""))
            rel = clean(row.get(col_release, ""))
            score = clean(row.get(col_critic, ""))

            y = year_from_text(rel)
            if y < MIN_YEAR or y > MAX_YEAR:
                continue

            key = (norm_title(title), y)
            if key not in imdb_horror:
                continue

            tconst, runtime, genres = imdb_horror[key]
            if not tconst or tconst in seen_ids:
                continue

            imdb_rating = imdb_ratings.get(tconst, "")

            out_rows.append({
                "ID": tconst,                      # stable unique ID
                "title": title,
                "release_year": str(y),
                "genre": "Horror",                 # enforced via IMDb filter
                "director": "",                    # not available from these two datasets
                "runtime_minutes": runtime,
                "imdb_rating": imdb_rating,
                "rotten_tomatoes_score": re.sub(r"[^\d]", "", score)  # keep digits only
            })
            seen_ids.add(tconst)

    if len(out_rows) < TARGET_ROWS:
        print(f"[!] Only built {len(out_rows)} rows. Common causes:")
        print("    - Title/year mismatches between RT CSV and IMDb basics")
        print("    - Your RT CSV isn’t the expected one (wrong columns/content)")
        print("    - You don’t have the IMDb .tsv.gz files in this folder")
    else:
        print(f"[+] Built {len(out_rows)} rows.")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out_rows)

    print(f"[+] Wrote {len(out_rows)} rows to {OUT_CSV}")

if __name__ == "__main__":
    main()
