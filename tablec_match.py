import pandas as pd
from rapidfuzz import fuzz

A = pd.read_csv("tableA.csv")
B = pd.read_csv("tableB.csv")

# Keep only likely movie rows from A
A_movies = A[A["runtime_minutes"].notna()].copy()

matches = []
pair_id = 0

for _, a in A_movies.iterrows():
    candidates = B[B["release_year"] == a["release_year"]]

    for _, b in candidates.iterrows():
        director_score = fuzz.token_sort_ratio(str(a["director"]), str(b["title"]))

        if director_score > 85:
            matches.append({
                "ID": pair_id,
                "ltable_ID": a["ID"],
                "rtable_ID": b["ID"]
            })
            pair_id += 1

C = pd.DataFrame(matches)
C.to_csv("tableC.csv", index=False)

print("Matches found:", len(C))
print("A size:", len(A))
print("B size:", len(B))
print("Cartesian product:", len(A) * len(B))
print("Filtered A movie rows:", len(A_movies))