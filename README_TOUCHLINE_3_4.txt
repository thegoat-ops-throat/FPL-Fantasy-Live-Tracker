Touchline 3.4 — Remove Transfer Market

Upload ALL files in this ZIP to the ROOT of your EXISTING GitHub Render repository, replacing same-named files. Render will redeploy.

Removed: Top 10 potential pickups/transfer-market tab, prospect recommendations, and the associated admin toggle/API.

Retained: Biweekly and overall standings, clickable player lineups, matchup projections, archives, waiver order, and confirmed roster-change history under Transfers.

The old admin.html, transfer_watch.py, feature_flags.json, and manager_lineup_watch*.json can be deleted from GitHub, since they are no longer used. Removing old files is recommended.

Render build: echo "No dependencies needed"
Render start: python server.py

Your former TOUCHLINE_ADMIN_PASSWORD, TOUCHLINE_GITHUB_REPO, TOUCHLINE_GITHUB_TOKEN variables are no longer needed for the removed admin toggle.
