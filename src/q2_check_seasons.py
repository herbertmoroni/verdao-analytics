#Quick check: how often did Palmeiras finish 1st-4th?
#Run from project root: python src/q2_check_seasons.py


import pandas as pd

df = pd.read_csv("data/campeonato-brasileiro-full.csv")
df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
df['season'] = df['data'].dt.year

# Calculate points per match for each team
def points_for_team(row, team_col):
    if row['vencedor'] == row[team_col]:
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0

# Build a long-format table: one row per (team, match) with points earned
home = df[['season', 'mandante']].copy()
home['team'] = df['mandante']
home['points'] = df.apply(lambda r: points_for_team(r, 'mandante'), axis=1)

away = df[['season', 'visitante']].copy()
away['team'] = df['visitante']
away['points'] = df.apply(lambda r: points_for_team(r, 'visitante'), axis=1)

all_team_matches = pd.concat([home[['season', 'team', 'points']],
                              away[['season', 'team', 'points']]])

# Sum points per team per season
standings = all_team_matches.groupby(['season', 'team'])['points'].sum().reset_index()

# Rank within each season (1 = top)
standings['position'] = standings.groupby('season')['points'].rank(method='min', ascending=False).astype(int)

# Show Palmeiras' finishes
palmeiras_seasons = standings[standings['team'] == 'Palmeiras'].sort_values('season')
print("Palmeiras finishing position per season:")
print(palmeiras_seasons[['season', 'points', 'position']].to_string(index=False))

# Filter to 1st-4th
top4 = palmeiras_seasons[palmeiras_seasons['position'] <= 4]
print(f"\nSeasons where Palmeiras finished 1st-4th: {len(top4)}")
print(top4[['season', 'position']].to_string(index=False))