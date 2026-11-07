TOUCHLINE v3.9 — DEPLOYMENT FIX FOR MULTI-FACTOR TRADE ANALYZER

The old interface shown in the screenshot is not the multi-factor code in the previously provided v3.7/v3.8 ZIP. It shows the legacy single-gameweek points analysis. This package includes the complete composite logic, a visible version badge and no-cache HTTP headers.

INSTALL ON EXISTING RENDER/GITHUB PROJECT
1. Extract ZIP. Upload ALL the included .py/.html/.json project files to the SAME root directory where Render runs `python server.py`. Replace index.html and server.py, not just add a ZIP to GitHub.
2. Commit the changes to the exact branch Render deploys. Check Render deployment status: Live.
3. Visit https://YOUR-SITE.onrender.com/api/version — should return `version: 3.9` and `trade_analyzer: six-factor composite`. If not, Render is deploying the wrong branch/folder or has not yet deployed the commit.
4. Open Touchline Trade Analyzer — title should show `v3.9 · MULTI-FACTOR`. If /api/version is v3.9 but the badge is absent, you are viewing an alternate HTML file or a browser-cached old page; hard-refresh using Ctrl+Shift+R.
5. Analyze any valid trade: output should show `Net composite value gained`, `TRADE SCOUT · v3.9 · SIX-FACTOR VALUE` and an All categories combined table, NOT `gains more projected points`.

METHOD
Season production 25%, recent form 20%, next-match projection 20%, minutes 15%, availability 15%, expected goal involvement 5% (MID/FWD). Relative to peers by position. Inapplicable/missing factors are reweighted. It is a heuristic and not a full rest-of-season forecast.

Existing features including free-agent list, leaderboards and trade selection remain included. No Draft transactions are submitted.
