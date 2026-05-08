"""
Exploration script — verify the dataset is what we expect.
Run from the project root: python src/explore.py
"""

import pandas as pd

# 1. Load the CSV
df = pd.read_csv("data/campeonato-brasileiro-full.csv")

# Convert "data" column from string "DD/MM/YYYY" to real datetime
df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')

# 2. Basic shape
print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)
print(f"Total matches: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print()

# 3. Column names and types
print("=" * 60)
print("COLUMNS AND DATA TYPES")
print("=" * 60)
print(df.dtypes)
print()

# 4. First 3 rows — sanity check
print("=" * 60)
print("FIRST 3 ROWS")
print("=" * 60)
print(df.head(3))
print()

# 5. Date range — how many seasons do we have?
print("=" * 60)
print("DATE RANGE")
print("=" * 60)
print(f"First match date: {df['data'].min()}")
print(f"Last match date:  {df['data'].max()}")
print()

# 6. Confirm Palmeiras is in the data
print("=" * 60)
print("PALMEIRAS CHECK")
print("=" * 60)
unique_teams = pd.concat([df['mandante'], df['visitante']]).unique()
palmeiras_variants = [t for t in unique_teams if 'palmeiras' in str(t).lower()]
print(f"Team names containing 'palmeiras': {palmeiras_variants}")

palmeiras_matches = df[(df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras')]
print(f"Total Palmeiras matches found: {len(palmeiras_matches)}")