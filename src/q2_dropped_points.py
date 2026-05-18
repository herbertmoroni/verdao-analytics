#Question 2: Where does Palmeiras drop points they shouldn't?

#Hypothesis: In near-title seasons (1st-4th), more than 30% of Palmeiras'
#dropped points (draws + losses) come from matches against bottom-half teams.

#Run from project root: python src/q2_dropped_points.py


import pandas as pd

# 1. Load the Data
df = pd.read_csv("data/campeonato-brasileiro-full.csv")
df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
df['season'] = df['data'].dt.year


# 2. Helper: Points Earned in a Match
def points_for_team(row, team_col):
    if row['vencedor'] == row[team_col]:
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0


# 3. Build Final Standings Per Season
# The dataset has no standings column — we calculate them from scratch by
# aggregating each team's points across all matches in a season.
home = df[['season', 'mandante']].copy()
home['team'] = df['mandante']
home['points'] = df.apply(lambda r: points_for_team(r, 'mandante'), axis=1)

away = df[['season', 'visitante']].copy()
away['team'] = df['visitante']
away['points'] = df.apply(lambda r: points_for_team(r, 'visitante'), axis=1)

all_team_matches = pd.concat([home[['season', 'team', 'points']],
                              away[['season', 'team', 'points']]])

standings = all_team_matches.groupby(['season', 'team'])['points'].sum().reset_index()

# method='min' gives tied teams the same (best) position; ascending=False ranks highest points as 1st
standings['position'] = standings.groupby('season')['points'].rank(
    method='min', ascending=False
).astype(int)

# 4. Identify Palmeiras' Qualifying Seasons
palmeiras_seasons = standings[standings['team'] == 'Palmeiras'].copy()
qualifying = palmeiras_seasons[palmeiras_seasons['position'] <= 4].copy()

# Tag each season as "Champion" or "Near-miss"
qualifying['season_type'] = qualifying['position'].apply(
    lambda p: 'Champion (1st)' if p == 1 else 'Near-miss (2nd-4th)'
)

print("Qualifying seasons:")
print(qualifying[['season', 'position', 'season_type']].to_string(index=False))
print()

# 5. Filter Palmeiras Matches in Qualifying Seasons
qualifying_seasons_list = qualifying['season'].tolist()

palmeiras_matches = df[
    ((df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras'))
    & (df['season'].isin(qualifying_seasons_list))
].copy()

# Identify the opponent and points earned by Palmeiras in each match
def get_opponent(row):
    return row['visitante'] if row['mandante'] == 'Palmeiras' else row['mandante']

def palmeiras_points(row):
    if row['vencedor'] == 'Palmeiras':
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0

palmeiras_matches['opponent'] = palmeiras_matches.apply(get_opponent, axis=1)
palmeiras_matches['points'] = palmeiras_matches.apply(palmeiras_points, axis=1)
palmeiras_matches['points_dropped'] = 3 - palmeiras_matches['points']  # 0 if win, 2 if draw, 3 if loss

# 6. Look Up Opponent Position in That Season
# The merge uses both 'season' and 'opponent' as keys, so a team's strength
# is judged by where they actually finished that specific year — not overall.
opp_positions = standings.rename(columns={'team': 'opponent', 'position': 'opp_position'})
palmeiras_matches = palmeiras_matches.merge(
    opp_positions[['season', 'opponent', 'opp_position']],
    on=['season', 'opponent'],
    how='left'
)

# Classify opponent as top-half or bottom-half
palmeiras_matches['opp_category'] = palmeiras_matches['opp_position'].apply(
    lambda p: 'Top half (1-10)' if p <= 10 else 'Bottom half (11-20)'
)

# Add season type to each match
palmeiras_matches = palmeiras_matches.merge(
    qualifying[['season', 'season_type']],
    on='season'
)

# 7. Aggregate Dropped Points by Category
print("=" * 70)
print("Q2 RESULT: Where does Palmeiras drop points in qualifying seasons?")
print("=" * 70)

# Only matches where points were dropped (draws + losses)
dropped_only = palmeiras_matches[palmeiras_matches['points'] < 3]

summary = dropped_only.groupby(['season_type', 'opp_category']).agg(
    matches=('points', 'count'),
    points_dropped=('points_dropped', 'sum'),
    draws=('points', lambda s: (s == 1).sum()),
    losses=('points', lambda s: (s == 0).sum()),
)

print(summary)
print()

# 8. Calculate Percentages
print("=" * 70)
print("Percentage of dropped points by opponent category")
print("=" * 70)

totals_by_season_type = summary.groupby('season_type')['points_dropped'].sum()
summary['pct_of_dropped'] = summary.apply(
    lambda row: round(100 * row['points_dropped'] / totals_by_season_type[row.name[0]], 1),
    axis=1
)

print(summary[['matches', 'points_dropped', 'pct_of_dropped']])