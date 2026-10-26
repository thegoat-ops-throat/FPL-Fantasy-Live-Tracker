TOUCHLINE 3.3 — STRONGER MATCHUP-BASED PROJECTIONS

This updates your existing Render/GitHub project; no new Render service is required.

Upload all package files to the ROOT of the existing GitHub repository and commit.
Render will deploy your updated server. Keep Build: echo "No dependencies needed"
and Start: python server.py.

WHAT CHANGED
- Opponent attack/defense matchup adjustments now vary as much as -30% to +30%
  (for goalkeepers, defenders and forwards; midfielders use up to +/-25%).
- A neutral opponent projects near recent/historical form. Strong opponents
  lower the projection; weak opponents raise it.
- 75/20/5 historical season target weighting, confidence percentages,
  optional FotMob context, admin controls and XI-only points remain unchanged.
- The matchup adjustment is ONLY applied when sufficient verified prior
  league fixture results exist; otherwise it stays neutral.

PROJECTIONS ARE ESTIMATES. Larger matchup adjustments can reduce accuracy
when team form changes suddenly or a player has an unusual role.
Actual player points and team score computation are unchanged.
