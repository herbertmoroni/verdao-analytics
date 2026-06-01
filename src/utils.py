from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).parent.parent / "data" / "campeonato-brasileiro-full.csv"


def load_data():
    df = pd.read_csv(DATA_PATH)
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
    df['season'] = df['data'].dt.year
    return df


def get_match_points(row, team):
    if row['vencedor'] == team:
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0


def build_standings(df):
    # Each match appears once as home and once as away; union both sides to get
    # each team's full point tally per season for final standings.
    home = df[['season', 'mandante']].copy()
    home['team'] = df['mandante']
    home['points'] = df.apply(lambda r: get_match_points(r, r['mandante']), axis=1)

    away = df[['season', 'visitante']].copy()
    away['team'] = df['visitante']
    away['points'] = df.apply(lambda r: get_match_points(r, r['visitante']), axis=1)

    all_matches = pd.concat([home[['season', 'team', 'points']],
                             away[['season', 'team', 'points']]])
    standings = all_matches.groupby(['season', 'team'])['points'].sum().reset_index()
    # method='min' gives tied teams the same (best) position; ascending=False ranks highest points as 1st
    standings['position'] = standings.groupby('season')['points'].rank(
        method='min', ascending=False
    ).astype(int)
    return standings
