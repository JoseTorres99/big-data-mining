import pandas as pd
import matplotlib.pyplot as plt

TABLE_A = "tableA.csv"
TABLE_B = "tableB.csv"

def load_csv(path: str) -> pd.DataFrame:
    # keep everything as string initially to avoid parsing weirdness
    return pd.read_csv(path, dtype=str)

def coerce_numeric(series: pd.Series) -> pd.Series:
    # strip spaces and convert to numeric where possible
    return pd.to_numeric(series.astype(str).str.strip(), errors="coerce")

def text_lengths(series: pd.Series) -> pd.Series:
    s = series.dropna().astype(str)
    # treat blank strings as missing
    s = s[s.str.strip() != ""]
    return s.str.len()

def missing_stats(df: pd.DataFrame, col: str):
    total = len(df)
    s = df[col]
    # missing = NaN or blank
    missing = s.isna() | (s.astype(str).str.strip() == "")
    missing_count = int(missing.sum())
    frac = f"{missing_count}/{total}"
    pct = (missing_count / total * 100) if total else 0.0
    return frac, pct

def classify_attribute(df: pd.DataFrame, col: str) -> str:
    # quick heuristic classification
    s = df[col].dropna().astype(str)
    s = s[s.str.strip() != ""]
    if len(s) == 0:
        return "Unknown (all missing)"
    lower = s.str.lower()

    # boolean-ish
    if set(lower.unique()).issubset({"true","false","0","1","yes","no"}):
        return "boolean"

    # numeric-ish
    numeric = coerce_numeric(s)
    numeric_ratio = numeric.notna().mean()
    if numeric_ratio > 0.90:
        return "numeric"

    # categorical-ish (low unique count relative to rows)
    unique_ratio = s.nunique() / len(s)
    if unique_ratio < 0.20:
        return "categorical"

    return "textual"

def main():
    A = load_csv(TABLE_A)
    B = load_csv(TABLE_B)

    print("Schema A:", list(A.columns))
    print("Schema B:", list(B.columns))

    # Align schemas (if one has extra cols, union them)
    all_cols = sorted(set(A.columns).union(set(B.columns)))
    A = A.reindex(columns=all_cols)
    B = B.reindex(columns=all_cols)

    # Choose S (you currently have 8 columns; keep them)
    S = [c for c in ["ID","title","release_year","genre","director","runtime_minutes","imdb_rating","rotten_tomatoes_score"] if c in A.columns]
    print("\nChosen S:", S)
    print("Row count Table A:", len(A))

    # Build a summary table for the report
    rows = []
    for col in S:
        frac, pct = missing_stats(A, col)
        attr_type = classify_attribute(A, col)

        row = {
            "attribute": col,
            "missing_fraction": frac,
            "missing_percent": round(pct, 2),
            "type": attr_type
        }

        # text length stats (only if textual)
        if attr_type == "textual":
            lens = text_lengths(A[col])
            if len(lens) > 0:
                row["avg_len"] = round(float(lens.mean()), 2)
                row["min_len"] = int(lens.min())
                row["max_len"] = int(lens.max())
            else:
                row["avg_len"] = row["min_len"] = row["max_len"] = None

        rows.append(row)

    summary = pd.DataFrame(rows)
    summary.to_csv("tableA_profile_summary.csv", index=False)
    print("\nWrote: tableA_profile_summary.csv")

    # ---- Histograms (choose 2) ----
    # 1) release_year histogram
    if "release_year" in A.columns:
        years = coerce_numeric(A["release_year"]).dropna()
        if len(years) > 0:
            plt.figure()
            plt.hist(years, bins=20)
            plt.title("Histogram: release_year (Table A)")
            plt.xlabel("release_year")
            plt.ylabel("count")
            plt.tight_layout()
            plt.savefig("hist_release_year.png", dpi=200)
            plt.close()
            print("Wrote: hist_release_year.png")

    # 2) runtime_minutes histogram (or title length if runtime empty)
    runtime_ok = False
    if "runtime_minutes" in A.columns:
        runtime = coerce_numeric(A["runtime_minutes"]).dropna()
        if len(runtime) > 0:
            plt.figure()
            plt.hist(runtime, bins=20)
            plt.title("Histogram: runtime_minutes (Table A)")
            plt.xlabel("runtime_minutes")
            plt.ylabel("count")
            plt.tight_layout()
            plt.savefig("hist_runtime_minutes.png", dpi=200)
            plt.close()
            runtime_ok = True
            print("Wrote: hist_runtime_minutes.png")

    if not runtime_ok and "title" in A.columns:
        lens = text_lengths(A["title"])
        if len(lens) > 0:
            plt.figure()
            plt.hist(lens, bins=20)
            plt.title("Histogram: title length (characters) (Table A)")
            plt.xlabel("title length")
            plt.ylabel("count")
            plt.tight_layout()
            plt.savefig("hist_title_length.png", dpi=200)
            plt.close()
            print("Wrote: hist_title_length.png")

if __name__ == "__main__":
    main()