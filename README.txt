TOUCHLINE — STARTING XI ONLY SCORING FIX

RULE: Total team points = sum of the points of the 11 players whose API pick positions are 1 through 11. Positions 12 through 15 are bench and contribute ZERO to Touchline team totals. No automatic-substitution adjustments and no entry_history score override are used.

Individual points, pitch, club uniforms, projected/confirmed substitution DISPLAY, season table, biweekly archives, and waiver section remain available. This is a custom fantasy scoring display and may differ from official FPL Draft totals after autosubs.

Upload server.py, index.html and config.json into the ROOT of your EXISTING GitHub repository: https://github.com/thegoat-ops-throat/FPL-Fantasy-Live-Tracker . Commit the files and your existing Render service will auto-redeploy. No new Render project is needed.

Render Build Command: echo "No dependencies needed"
Render Start Command: python server.py

The server bumps scoring_version to 3 and clears previously cached totals on startup. After deployment confirm /api/status displays scoring_version 3, and that scores match the 11 players shown on the pitch. Free Render plans may sleep.
