# Where does Palmeiras drop points in title-contending seasons?
#
# Hypothesis: In near-miss seasons (2nd-4th place), a higher share of dropped
# points comes from bottom-half opponents than in championship seasons.
#
# Run from project root: python src/dropped_points.py

import pandas as pd
from utils import load_data, get_match_points, build_standings

df = load_data()
standings = build_standings(df)

palmeiras_seasons = standings[standings['team'] == 'Palmeiras'].copy()
qualifying = palmeiras_seasons[palmeiras_seasons['position'] <= 4].copy()

# Top-4 = "title contender" season: 1st = Champion, 2nd-4th = Near-miss.
# Seasons below 4th are excluded because the gap to the title is too large
# to meaningfully compare dropped-point patterns.
qualifying['season_type'] = qualifying['position'].apply(
    lambda p: 'Champion (1st)' if p == 1 else 'Near-miss (2nd-4th)'
)

print("Title-contending seasons:")
print(qualifying[['season', 'position', 'season_type']].to_string(index=False))
print()

palmeiras_matches = df[
    ((df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras'))
    & (df['season'].isin(qualifying['season'].tolist()))
].copy()

def get_opponent(row):
    return row['visitante'] if row['mandante'] == 'Palmeiras' else row['mandante']

palmeiras_matches['opponent'] = palmeiras_matches.apply(get_opponent, axis=1)
palmeiras_matches['points'] = palmeiras_matches.apply(lambda r: get_match_points(r, 'Palmeiras'), axis=1)
palmeiras_matches['points_dropped'] = 3 - palmeiras_matches['points']  # 0 if win, 2 if draw, 3 if loss

# The merge uses both 'season' and 'opponent' as keys, so a team's strength
# is judged by where they actually finished that specific year — not overall.
opp_positions = standings.rename(columns={'team': 'opponent', 'position': 'opp_position'})
palmeiras_matches = palmeiras_matches.merge(
    opp_positions[['season', 'opponent', 'opp_position']],
    on=['season', 'opponent'],
    how='left'
)

palmeiras_matches['opp_category'] = palmeiras_matches['opp_position'].apply(
    lambda p: 'Top half (1-10)' if p <= 10 else 'Bottom half (11-20)'
)

palmeiras_matches = palmeiras_matches.merge(
    qualifying[['season', 'season_type']],
    on='season'
)

# Only matches where points were dropped (draws + losses)
dropped_only = palmeiras_matches[palmeiras_matches['points'] < 3]

summary = dropped_only.groupby(['season_type', 'opp_category']).agg(
    matches=('points', 'count'),
    points_dropped=('points_dropped', 'sum'),
    draws=('points', lambda s: (s == 1).sum()),
    losses=('points', lambda s: (s == 0).sum()),
)

print("=" * 70)
print("Dropped points by opponent tier in title-contending seasons")
print("=" * 70)
print(summary)
print()

print("=" * 70)
print("Percentage of dropped points by opponent tier")
print("=" * 70)

totals_by_season_type = summary.groupby('season_type')['points_dropped'].sum()
# Normalize within each season type so Champion and Near-miss are comparable
# despite having different total dropped-point counts.
summary['pct_of_dropped'] = summary.apply(
    lambda row: round(100 * row['points_dropped'] / totals_by_season_type[row.name[0]], 1),
    axis=1
)

print(summary[['matches', 'points_dropped', 'pct_of_dropped']])
