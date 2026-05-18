#Stretch challenge: Visualize Q1 and Q2 findings as side-by-side charts.

#Output: output/palmeiras_analysis.png

#Run from project root: python src/q3_visualize.py


import pandas as pd
import matplotlib.pyplot as plt

# Load the Data
df = pd.read_csv("data/campeonato-brasileiro-full.csv")
df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
df['season'] = df['data'].dt.year



# Q1 ANALYSIS — Fixture congestion
palmeiras = df[(df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras')].copy()
palmeiras = palmeiras.sort_values('data').reset_index(drop=True)
# Consecutive difference gives days elapsed since the previous Palmeiras match
palmeiras['days_rest'] = palmeiras['data'].diff().dt.days
palmeiras = palmeiras.dropna(subset=['days_rest'])
palmeiras['days_rest'] = palmeiras['days_rest'].astype(int)

def points_earned(row):
    if row['vencedor'] == 'Palmeiras':
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0

palmeiras['points'] = palmeiras.apply(points_earned, axis=1)

def rest_bucket(days):
    if days <= 3:
        return 'Short rest\n(<=3 days)'
    elif days <= 6:
        return 'Normal rest\n(4-6 days)'
    else:
        return 'Long rest\n(7+ days)'

palmeiras['rest_category'] = palmeiras['days_rest'].apply(rest_bucket)

q1_summary = palmeiras.groupby('rest_category').agg(
    matches=('points', 'count'),
    avg_points=('points', 'mean'),
    wins=('points', lambda s: (s == 3).sum()),
).reset_index()
q1_summary['win_rate'] = (q1_summary['wins'] / q1_summary['matches'] * 100).round(1)

# Force the order short -> normal -> long
order_q1 = ['Short rest\n(<=3 days)', 'Normal rest\n(4-6 days)', 'Long rest\n(7+ days)']
q1_summary = q1_summary.set_index('rest_category').loc[order_q1].reset_index()



# Q2 ANALYSIS — Dropped points vs opponent strength
def points_for_team(row, team_col):
    if row['vencedor'] == row[team_col]:
        return 3
    elif row['vencedor'] == '-':
        return 1
    else:
        return 0

# Each match appears once as home and once as away; union both sides to get
# each team's full point tally per season for final standings.
home = df[['season', 'mandante']].copy()
home['team'] = df['mandante']
home['points'] = df.apply(lambda r: points_for_team(r, 'mandante'), axis=1)

away = df[['season', 'visitante']].copy()
away['team'] = df['visitante']
away['points'] = df.apply(lambda r: points_for_team(r, 'visitante'), axis=1)

all_team_matches = pd.concat([home[['season', 'team', 'points']],
                              away[['season', 'team', 'points']]])
standings = all_team_matches.groupby(['season', 'team'])['points'].sum().reset_index()
standings['position'] = standings.groupby('season')['points'].rank(
    method='min', ascending=False
).astype(int)

palmeiras_seasons = standings[standings['team'] == 'Palmeiras'].copy()
qualifying = palmeiras_seasons[palmeiras_seasons['position'] <= 4].copy()
qualifying['season_type'] = qualifying['position'].apply(
    lambda p: 'Champion (1st)' if p == 1 else 'Near-miss (2nd-4th)'
)

qualifying_seasons_list = qualifying['season'].tolist()
palmeiras_matches = df[
    ((df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras'))
    & (df['season'].isin(qualifying_seasons_list))
].copy()

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
palmeiras_matches['points_dropped'] = 3 - palmeiras_matches['points']

opp_positions = standings.rename(columns={'team': 'opponent', 'position': 'opp_position'})
palmeiras_matches = palmeiras_matches.merge(
    opp_positions[['season', 'opponent', 'opp_position']],
    on=['season', 'opponent'], how='left'
)
palmeiras_matches['opp_category'] = palmeiras_matches['opp_position'].apply(
    lambda p: 'Top half\n(1-10)' if p <= 10 else 'Bottom half\n(11-20)'
)
palmeiras_matches = palmeiras_matches.merge(
    qualifying[['season', 'season_type']], on='season'
)

# Calculate % of dropped points per (season_type, opp_category)
dropped_only = palmeiras_matches[palmeiras_matches['points'] < 3]
q2_summary = dropped_only.groupby(['season_type', 'opp_category'])['points_dropped'].sum().reset_index()
totals = q2_summary.groupby('season_type')['points_dropped'].sum().to_dict()
q2_summary['pct'] = q2_summary.apply(
    lambda r: round(100 * r['points_dropped'] / totals[r['season_type']], 1),
    axis=1
)



# BUILD THE CHART
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Palmeiras Performance Analysis — Brasileirao Serie A (2003-2025)',
             fontsize=15, fontweight='bold', y=1.02)

# LEFT CHART: Q1 
ax1 = axes[0]
colors_q1 = ['#2E7D32', '#66BB6A', '#C62828']  # green, light green, red
bars1 = ax1.bar(q1_summary['rest_category'], q1_summary['win_rate'],
                color=colors_q1, edgecolor='black', linewidth=0.8)

ax1.set_title('Q1: Does fixture congestion hurt Palmeiras?',
              fontsize=12, fontweight='bold', pad=12)
ax1.set_ylabel('Win rate (%)', fontsize=11)
ax1.set_ylim(0, 65)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Annotate bars with win rate and match count
for bar, row in zip(bars1, q1_summary.itertuples()):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, height + 1,
             f'{row.win_rate}%', ha='center', fontweight='bold', fontsize=11)
    ax1.text(bar.get_x() + bar.get_width()/2, height/2,
             f'n={row.matches}', ha='center', color='white',
             fontweight='bold', fontsize=10)

ax1.text(0.5, -0.18,
         'Surprise: Palmeiras performs BEST with short rest.\n'
         'Long rest (7+ days) shows the lowest win rate.',
         transform=ax1.transAxes, ha='center', fontsize=9, style='italic',
         color='#444')


# RIGHT CHART: Q2 
ax2 = axes[1]

champion = q2_summary[q2_summary['season_type'] == 'Champion (1st)'].set_index('opp_category')
near_miss = q2_summary[q2_summary['season_type'] == 'Near-miss (2nd-4th)'].set_index('opp_category')

categories = ['Top half\n(1-10)', 'Bottom half\n(11-20)']
champion_pct = [champion.loc[c, 'pct'] for c in categories]
near_miss_pct = [near_miss.loc[c, 'pct'] for c in categories]

import numpy as np
x = np.arange(len(categories))
width = 0.35

bars_c = ax2.bar(x - width/2, champion_pct, width,
                 label='Champion seasons (4)', color='#FFB300', edgecolor='black', linewidth=0.8)
bars_n = ax2.bar(x + width/2, near_miss_pct, width,
                 label='Near-miss seasons (9)', color='#5C6BC0', edgecolor='black', linewidth=0.8)

ax2.set_title('Q2: Where does Palmeiras drop points?',
              fontsize=12, fontweight='bold', pad=12)
ax2.set_ylabel('% of total dropped points', fontsize=11)
ax2.set_xticks(x)
ax2.set_xticklabels(categories)
ax2.set_ylim(0, 75)
ax2.legend(loc='upper left', frameon=True)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.set_axisbelow(True)

for bars, values in [(bars_c, champion_pct), (bars_n, near_miss_pct)]:
    for bar, val in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f'{val}%', ha='center', fontweight='bold', fontsize=10)

ax2.text(0.5, -0.18,
         'In near-miss seasons, more points are dropped\n'
         'to bottom-half teams (42.3%) than in title years (36.6%).',
         transform=ax2.transAxes, ha='center', fontsize=9, style='italic',
         color='#444')


# Save the chart
plt.tight_layout()
import os
os.makedirs('output', exist_ok=True)
output_path = 'output/palmeiras_analysis.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Chart saved to: {output_path}")
plt.show()