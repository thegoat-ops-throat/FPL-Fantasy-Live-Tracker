TOUCHLINE 3.6 — ALL FREE AGENTS (EXISTING RENDER PROJECT)

INSTALL
1. Unzip this package.
2. Upload index.html, server.py, projection_model.py, config.json,
   external_projection_inputs.json, and press_conferences.json to the ROOT
   of your existing GitHub repo, replacing matching files.
3. Render will redeploy the existing service. Keep your Start Command:
   python server.py
4. Open the new "Free Agents" tab after all six current GW squads load.

FEATURES
- Every Draft player absent from all SIX tracked manager rosters, not top 10.
- Sort by next-GW projection, form, points/game, or player name.
- Filter GK/DEF/MID/FWD, search by player/club, filter flagged status.
- Paginated 40 rows at a time, with next fixture and availability warnings.
- Updated with the existing five-minute refresh cycle.
- Uses the existing transparent Touchline projection model; missing values
  display as dashes rather than fabricated estimates.
- Existing Trade Analyzer and other tabs remain intact.

IMPORTANT LIMITATIONS
- Free-agent availability is INFERRED from the six tracked 15-player GW
  squads, not an official league-wide live ownership / claim status feed.
- If there are more than six teams in the league, this list is incomplete
  as an ownership check. Check the official Draft app before a waiver claim.
- Recent transactions after the GW snapshot may not be reflected yet.
- Rankings are single-Gameweek projections, not rest-of-season valuations.
- Projections are estimates; do not interpret confidence as a probability.
