import pandas as pd
# read and display missing values for each csv file
A = pd.read_csv("tableA.csv")
B = pd.read_csv("tableB.csv")

print("TABLE A MISSING")
missing_A = A.isnull().sum()
percent_A = (missing_A / len(A)) * 100
print(percent_A)

print("\nTABLE B MISSING")
missing_B = B.isnull().sum()
percent_B = (missing_B / len(B)) * 100
print(percent_B)