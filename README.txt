TOUCHLINE 2.7 — AUTOMATIC DRAFT PROJECTION INPUTS + REAL PLAYER TEMPLATES

UPGRADE EXISTING RENDER PROJECT (same URL)
Upload the SIX files to your existing GitHub repository root:
  index.html, server.py, config.json, projection_model.py,
  press_conferences.json, external_projection_inputs.json
Render build: echo "No dependencies needed"
Render start: python server.py

AUTOMATIC FEATURES
- Every 5 minutes while your Render app is awake, server collects FPL Draft
  player scores, lineups, injuries, fixtures, and (where present) official
  Draft bootstrap form and points-per-game fields.
- Projects from previous five Gameweeks; if history is absent and Draft
  supplies numeric form/points_per_game, falls back to that verified value.
- Uses completed fixture results for opponent attacking/defensive ranks when
  the minimum sample is available. Shows insufficient data rather than guessing.
- Preserves your customized starting XI ONLY actual scoring; does not count bench.

OPTIONAL LICENSED EXTERNAL FEED
Render > Environment: TOUCHLINE_EXTERNAL_FEED_URL = HTTPS URL to a JSON endpoint
which you are AUTHORIZED to access. Accepted JSON format:
{ "players": [ { "player_id": 250, "sources": ["Licensed data"],
 "source_url": "https://provider.example/report", "source_date": "2026-10-25",
 "predicted_minutes": 75, "form_adjustment": 0.3, "note": "..." } ] }
It overrides matching player entries in the local file. If unavailable, the
server continues using automatic FPL Draft data and local manual entries.
This is a generic provider adapter: it does NOT scrape FotMob or Transfermarkt
or claim direct integration with those sites.

READY-TO-EDIT PLAYER FILE
external_projection_inputs.json has historical GW8 example IDs for players
in your league: Leno, Bassey, Milenkovic, Delap, Joao Pedro, Sels,
Donnarumma and Raya. No performance facts are fabricated. Null fields mean
not entered, and have NO effect on a projection.
When adding real FotMob/Premier League/Transfermarkt reporting, supply an
actual source_url and source_date. Treat player_name_reference as a note only:
matching is exclusively by verified Draft player_id.

CHECKS & LIMITATIONS
- Free Render may sleep and does not guarantee stored local history.
- Source permissions and changing provider schemas matter. Never put keys
  into GitHub or browser HTML; use Render Environment.
- Live transfer and suspension information still derives from Draft API.
- Forecasts are estimates. No external source data is fetched unless the
  optional authorized feed is configured.
