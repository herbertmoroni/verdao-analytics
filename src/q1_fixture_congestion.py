#Question 1: Does fixture congestion hurt Palmeiras?

#Hypothesis: Palmeiras' average points per match will be lower in matches
#played with <=3 days of rest compared to matches with 7+ days of rest.

#Run from project root: python src/q1_fixture_congestion.py


import pandas as pd

# 1. Load the Data
df = pd.read_csv("data/campeonato-brasileiro-full.csv")

# 2. Convert Dates - stored as strings (DD/MM/YYYY)
df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')

# 3. Filter Palmeiras Matches
palmeiras = df[(df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras')].copy()

# 4. Sort Chronologically
# Reset the index so diff() compares adjacent rows correctly
palmeiras = palmeiras.sort_values('data').reset_index(drop=True)

print(f"Total Palmeiras matches: {len(palmeiras)}")
print(f"Date range: {palmeiras['data'].min().date()}  ->  {palmeiras['data'].max().date()}")
print()

# 5. Calculate Days Since Previous Match

# diff() gives us the difference between each row and the row above
# .dt.days converts the timedelta into a plain integer number of days
palmeiras['days_rest'] = palmeiras['data'].diff().dt.days

# The very first match has no "previous match" — drop it
palmeiras = palmeiras.dropna(subset=['days_rest'])
palmeiras['days_rest'] = palmeiras['days_rest'].astype(int)

# 6. Calculate Points Earned Each Match
def points_earned(row):
    if row['vencedor'] == 'Palmeiras':
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0

palmeiras['points'] = palmeiras.apply(points_earned, axis=1)

# 7. Bucket Matches by Rest Days
# Thresholds: <=3 days = back-to-back (midweek + weekend), 4-6 = standard
# weekly rhythm, 7+ = international break or calendar gap.
def rest_bucket(days):
    if days <= 3:
        return '1. Short rest (<=3 days)'
    elif days <= 6:
        return '2. Normal rest (4-6 days)'
    else:
        return '3. Long rest (7+ days)'

palmeiras['rest_category'] = palmeiras['days_rest'].apply(rest_bucket)

# 8. Aggregate by Bucket
summary = palmeiras.groupby('rest_category').agg(
    matches=('points', 'count'),
    avg_points=('points', 'mean'),
    wins=('points', lambda s: (s == 3).sum()),
    draws=('points', lambda s: (s == 1).sum()),
    losses=('points', lambda s: (s == 0).sum()),
).round(2)

# 9. Show Results
print("=" * 60)
print("Q1 RESULT: Palmeiras performance by fixture congestion")
print("=" * 60)
print(summary)
print()

# Calculate win rate as a percentage for easier reading
summary['win_rate_%'] = (summary['wins'] / summary['matches'] * 100).round(1)
print("With win rate:")
print(summary[['matches', 'avg_points', 'win_rate_%']])