# Visualizes Palmeiras' performance patterns in the Brasileirão (2003-2025).
# Produces two charts: fixture congestion impact and dropped-points distribution.
#
# Run from project root: python src/visualize.py

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from utils import load_data, get_match_points, build_standings

df = load_data()

# --- Fixture Congestion Analysis ---
palmeiras = df[(df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras')].copy()
palmeiras = palmeiras.sort_values('data').reset_index(drop=True)
# Consecutive difference gives days elapsed since the previous Palmeiras match
palmeiras['days_rest'] = palmeiras['data'].diff().dt.days
palmeiras = palmeiras.dropna(subset=['days_rest'])
palmeiras['days_rest'] = palmeiras['days_rest'].astype(int)

palmeiras['points'] = palmeiras.apply(lambda r: get_match_points(r, 'Palmeiras'), axis=1)

# Thresholds: <=3 days = back-to-back (midweek + weekend), 4-6 = standard
# weekly rhythm, 7+ = international break or calendar gap.
def rest_bucket(days):
    if days <= 3:
        return 'Short rest\n(<=3 days)'
    elif days <= 6:
        return 'Normal rest\n(4-6 days)'
    else:
        return 'Long rest\n(7+ days)'

palmeiras['rest_category'] = palmeiras['days_rest'].apply(rest_bucket)

congestion_summary = palmeiras.groupby('rest_category').agg(
    matches=('points', 'count'),
    avg_points=('points', 'mean'),
    wins=('points', lambda s: (s == 3).sum()),
).reset_index()
congestion_summary['win_rate'] = (congestion_summary['wins'] / congestion_summary['matches'] * 100).round(1)

# Force the order short -> normal -> long
order = ['Short rest\n(<=3 days)', 'Normal rest\n(4-6 days)', 'Long rest\n(7+ days)']
congestion_summary = congestion_summary.set_index('rest_category').loc[order].reset_index()


# --- Dropped Points Analysis ---
standings = build_standings(df)

palmeiras_seasons = standings[standings['team'] == 'Palmeiras'].copy()
qualifying = palmeiras_seasons[palmeiras_seasons['position'] <= 4].copy()
# Top-4 = "title contender" season: 1st = Champion, 2nd-4th = Near-miss.
# Seasons below 4th are excluded because the gap to the title is too large
# to meaningfully compare dropped-point patterns.
qualifying['season_type'] = qualifying['position'].apply(
    lambda p: 'Champion (1st)' if p == 1 else 'Near-miss (2nd-4th)'
)

palmeiras_matches = df[
    ((df['mandante'] == 'Palmeiras') | (df['visitante'] == 'Palmeiras'))
    & (df['season'].isin(qualifying['season'].tolist()))
].copy()

def get_opponent(row):
    return row['visitante'] if row['mandante'] == 'Palmeiras' else row['mandante']

palmeiras_matches['opponent'] = palmeiras_matches.apply(get_opponent, axis=1)
palmeiras_matches['points'] = palmeiras_matches.apply(lambda r: get_match_points(r, 'Palmeiras'), axis=1)
palmeiras_matches['points_dropped'] = 3 - palmeiras_matches['points']

# The merge uses both 'season' and 'opponent' as keys, so a team's strength
# is judged by where they actually finished that specific year — not overall.
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

dropped_only = palmeiras_matches[palmeiras_matches['points'] < 3]
dropped_summary = dropped_only.groupby(['season_type', 'opp_category'])['points_dropped'].sum().reset_index()
totals = dropped_summary.groupby('season_type')['points_dropped'].sum().to_dict()
# Normalize within each season type so Champion and Near-miss are comparable
# despite having different total dropped-point counts.
dropped_summary['pct'] = dropped_summary.apply(
    lambda r: round(100 * r['points_dropped'] / totals[r['season_type']], 1),
    axis=1
)


# --- Build Charts ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Palmeiras Performance Analysis — Brasileirao Serie A (2003-2025)',
             fontsize=15, fontweight='bold', y=1.02)

# LEFT: Fixture Congestion
ax1 = axes[0]
colors = ['#2E7D32', '#66BB6A', '#C62828']  # green, light green, red
bars1 = ax1.bar(congestion_summary['rest_category'], congestion_summary['win_rate'],
                color=colors, edgecolor='black', linewidth=0.8)

ax1.set_title('Does fixture congestion hurt Palmeiras?',
              fontsize=12, fontweight='bold', pad=12)
ax1.set_ylabel('Win rate (%)', fontsize=11)
ax1.set_ylim(0, 65)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

for bar, row in zip(bars1, congestion_summary.itertuples()):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, height + 1,
             f'{row.win_rate}%', ha='center', fontweight='bold', fontsize=11)
    ax1.text(bar.get_x() + bar.get_width()/2, height/2,
             f'n={row.matches}', ha='center', color='white',
             fontweight='bold', fontsize=10)

short_wr = congestion_summary.loc[congestion_summary['rest_category'].str.startswith('Short'), 'win_rate'].values[0]
long_wr = congestion_summary.loc[congestion_summary['rest_category'].str.startswith('Long'), 'win_rate'].values[0]
ax1.text(0.5, -0.18,
         f'Surprise: Palmeiras performs BEST with short rest ({short_wr}%).\n'
         f'Long rest (7+ days) shows the lowest win rate ({long_wr}%).',
         transform=ax1.transAxes, ha='center', fontsize=9, style='italic', color='#444')


# RIGHT: Dropped Points
ax2 = axes[1]

champion = dropped_summary[dropped_summary['season_type'] == 'Champion (1st)'].set_index('opp_category')
near_miss = dropped_summary[dropped_summary['season_type'] == 'Near-miss (2nd-4th)'].set_index('opp_category')

n_champion = qualifying[qualifying['season_type'] == 'Champion (1st)']['season'].nunique()
n_near_miss = qualifying[qualifying['season_type'] == 'Near-miss (2nd-4th)']['season'].nunique()

categories = ['Top half\n(1-10)', 'Bottom half\n(11-20)']
champion_pct = [champion.loc[c, 'pct'] for c in categories]
near_miss_pct = [near_miss.loc[c, 'pct'] for c in categories]

x = np.arange(len(categories))
width = 0.35

bars_c = ax2.bar(x - width/2, champion_pct, width,
                 label=f'Champion seasons ({n_champion})', color='#FFB300', edgecolor='black', linewidth=0.8)
bars_n = ax2.bar(x + width/2, near_miss_pct, width,
                 label=f'Near-miss seasons ({n_near_miss})', color='#5C6BC0', edgecolor='black', linewidth=0.8)

ax2.set_title('Where does Palmeiras drop points?',
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

bottom_champ = champion.loc['Bottom half\n(11-20)', 'pct']
bottom_near = near_miss.loc['Bottom half\n(11-20)', 'pct']
ax2.text(0.5, -0.18,
         f'In near-miss seasons, more points are dropped\n'
         f'to bottom-half teams ({bottom_near}%) than in title years ({bottom_champ}%).',
         transform=ax2.transAxes, ha='center', fontsize=9, style='italic', color='#444')


plt.tight_layout()
os.makedirs('output', exist_ok=True)
output_path = 'output/palmeiras_analysis.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Chart saved to: {output_path}")
plt.show()
