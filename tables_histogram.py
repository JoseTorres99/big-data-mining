import pandas as pd
import matplotlib.pyplot as plt
# read csv files
tableA = pd.read_csv("tableA.csv")
tableB = pd.read_csv("tableB.csv")

# release year histogram

plt.figure()
plt.hist(tableA["release_year"].dropna(), bins=20, alpha=0.5, label="Table A")
plt.hist(tableB["release_year"].dropna(), bins=20, alpha=0.5, label="Table B")
plt.xlabel("Release Year")
plt.ylabel("Frequency")
plt.title("Release Year Distribution")
plt.legend()
plt.savefig("release_year_histogram.png")
plt.close()

# runtime histogram

plt.figure()
plt.hist(tableA["runtime_minutes"].dropna(), bins=20, alpha=0.5, label="Table A")
plt.hist(tableB["runtime_minutes"].dropna(), bins=20, alpha=0.5, label="Table B")
plt.xlabel("Runtime (minutes)")
plt.ylabel("Frequency")
plt.title("Runtime Distribution")
plt.legend()
plt.savefig("runtime_histogram.png")
plt.close()

print("Histograms saved as PNG files.")