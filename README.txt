TOUCHLINE 2.5 — PLAYER PROJECTIONS (UPGRADE EXISTING RENDER PROJECT)

Upload these files to the ROOT of your EXISTING GitHub repository, replacing
server.py, index.html, config.json and adding projection_model.py and
press_conferences.json. Your current Render service and URL stay unchanged.
Keep Build Command: echo "No dependencies needed"
Keep Start Command: python server.py

After deploy, look at your Render URL -> Lineups -> click a player.
The projections are NOT actual fantasy points; existing XI-only scoring is unchanged.
A number appears after earlier Gameweeks can be fetched. Estimates use an average
of up to five previous weeks, availability, and opponent strength only when
at least 10 clubs have >=3 finished score-bearing fixtures. Opponent ranking
is a descriptive rank based on goals scored/conceded, not official PL rank.
Position rank is limited to players seen in the six tracked fantasy squads.
No verified inputs = show "not enough data", not made-up ranks.

OPTIONAL PRESS CONFERENCE NEWS
Add entries to press_conferences.json with real player IDs from Draft API,
a real HTTPS source, a date, and a concise factual headline, for example:
[
  {"player_id": 123, "date": "2026-10-25", "headline": "Manager reported player back in training", "source_url": "https://example.org/real-report"}
]
This example is illustrative only; do NOT use it as actual news.
Remove it after following the format (the supplied file is empty: []).
Only manually verified news gets displayed. It currently does NOT numerically
affect projections (to avoid converting uncertain commentary into fake percentages).

WHAT ABOUT AI COMMENTARY?
Optional AI-written paragraphs need server-side integration with an AI API.
API = service for code. Key = secret credential charged to an account.
Never place secret keys in index.html, GitHub, or URLs. Use Render Environment.
Statistical explanations in this release are free and need no API key.
If you later add AI, generate commentary only from checked football data,
not unsourced rumors, and cache responses to manage costs.

IMPORTANT
Render's free tier sleeps when idle and loses temporary local files on restart.
The server refetches old Gameweeks when possible. Press news entered in GitHub
persists, and tracked individual players change with each week's transfers.
