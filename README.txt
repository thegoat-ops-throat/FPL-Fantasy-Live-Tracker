TOUCHLINE 2.1 — SCORING CORRECTION FOR EXISTING RENDER SERVICE

This ZIP contains the updated server.py along with your existing index.html
and config.json. It does not create a new Render project.

The fix:
- Prevents auto-substitution points from being added twice if the incoming
  player already appears in the starting XI returned by the Draft API.
- Applies a confirmed substitution once if the API still returns the original XI.
- Uses entry_history.points, when available, as the authoritative Gameweek score.
- Clears previously cached scores produced by old scoring logic and retrieves
  them again from the Draft API.
- Retains the pitch, club-colored kits, archives, and leaderboards.

HOW TO INSTALL:
1. Go to https://github.com/thegoat-ops-throat/FPL-Fantasy-Live-Tracker
2. Upload the three root files server.py, index.html, config.json, replacing
   the same-named files in the repo root. (README.txt is optional.)
3. Commit changes. Existing Render service should auto-deploy.
4. Start command: python server.py
5. Open YOUR existing Render URL + /api/status; check updated_at and status.
6. Compare one completed Gameweek for each manager with official FPL Draft.

IMPORTANT:
FPL Draft's API is unofficial and can change. We cannot guarantee historical
scores or verified final totals where the API does not provide them. Some
Gameweeks may remain calculated / provisional. Do not treat projected subs
as final. Render free instances can sleep between requests.

Run local tests (optional): python -m unittest -v test_server.py
