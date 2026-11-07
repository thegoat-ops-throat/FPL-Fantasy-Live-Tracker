TOUCHLINE 3.5 — TRADE ANALYZER (EXISTING RENDER PROJECT)

Deploy to your EXISTING Touchline GitHub repository (same repository connected to Render):
1. Extract this ZIP.
2. Upload the 7 project files (index.html, server.py, projection_model.py, config.json, press_conferences.json, external_projection_inputs.json, README_TOUCHLINE_3_5.txt) to the ROOT of your existing GitHub repo. Replace existing files with the same names. You can leave other unrelated files unchanged.
3. Render redeploys automatically if linked to GitHub. Otherwise, choose Manual Deploy > Deploy latest commit.
4. Keep existing Render settings: Build Command: echo "No dependencies needed"; Start Command: python server.py.
5. Open Touchline and select the new 'Trade Analyzer' tab. Select two different managers and 1–3 players from each side, then press Analyze proposed trade.

Trade Analyzer features:
- Uses six managers' existing official Draft roster snapshots (same GW for both managers).
- Validates equal number of players and equal counts of GK/DEF/MID/FWD.
- Shows net projected points for each side using existing Touchline model, recent-form comparison, confidence coverage, injury news, and limitations.
- Does not submit or accept trades and does not change lineups.
- Does not restore the old Transfer Market, admin toggle, or pickup recommendations.

Important: A projected trade advantage is a one-Gameweek snapshot, NOT a season-long ranking, trade acceptance probability, or a guarantee. Projections require the current API sync to have completed. Older snapshot weeks may lack projections. Private pending trades are not available from the public Draft API.
