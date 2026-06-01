# Does fixture congestion affect Palmeiras' performance?
#
# Hypothesis: Win rate will be lower after short rest (<=3 days) than after
# normal rest (4-6 days), reflecting fatigue from compressed schedules.
#
# Run from project root: python src/fixture_congestion.py

import pandas as pd
from utils import load_data, get_match_points

df = load_data()

palmeiras = df[(df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras')].copy()
palmeiras = palmeiras.sort_values('data').reset_index(drop=True)

# Consecutive difference gives days elapsed since the previous Palmeiras match
palmeiras['days_rest'] = palmeiras['data'].diff().dt.days
# The very first match has no previous match — drop it
palmeiras = palmeiras.dropna(subset=['days_rest'])
palmeiras['days_rest'] = palmeiras['days_rest'].astype(int)

palmeiras['points'] = palmeiras.apply(lambda r: get_match_points(r, 'Palmeiras'), axis=1)

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

summary = palmeiras.groupby('rest_category').agg(
    matches=('points', 'count'),
    avg_points=('points', 'mean'),
    wins=('points', lambda s: (s == 3).sum()),
    draws=('points', lambda s: (s == 1).sum()),
    losses=('points', lambda s: (s == 0).sum()),
).round(2)

print("=" * 60)
print("Palmeiras performance by fixture congestion")
print("=" * 60)
print(summary)
print()

summary['win_rate_%'] = (summary['wins'] / summary['matches'] * 100).round(1)
print("With win rate:")
print(summary[['matches', 'avg_points', 'win_rate_%']])
