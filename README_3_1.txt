TOUCHLINE 3.1 — TOP 10 PICKUPS + OPTIONAL COMMISSIONER XI PREVIEWS

This upgrades your EXISTING GitHub/Render project. No new Render project or URL.

Upload to GitHub repository root:
  index.html, server.py, config.json, projection_model.py,
  transfer_watch.py, external_projection_inputs.json,
  press_conferences.json, manager_lineup_watch.json

Do not overwrite scores.json with a sample. Do not upload example files if you
have your own information in manager_lineup_watch.json.

Keep Render settings:
  Build Command: echo "No dependencies needed"
  Start Command: python server.py

WHAT IT DOES
1. Every five minutes WHILE THE RENDER SERVER IS RUNNING, it fetches Draft
   bootstrap and the six tracked squad lineups. New Gameweek squads and confirmed
   additions/removals are still taken only from the official Draft API.
2. The 'Top 10 pickups' tab ranks potential pickups using public Draft form,
   points per match, minutes history, position and current status.
3. It removes anyone owned by the six tracked teams and anyone coded by Draft
   as unavailable (i, s, u). Doubtful players are flagged, not hidden.
4. It shows why each candidate is suggested, and filters by position.
5. Transfer suggestions NEVER become actual transfers in the UI unless the
   Gameweek roster changes and it appears in official Draft data.

IMPORTANT LIMITATION
These are NOT confirmed free agents. They are players absent from the tracked
six squads. If the real Draft league has any untracked managers, they could be
owned there. Even with exactly six managers, waiver claims/locks can apply.
Always check the official Draft Transactions page before claiming anyone.

YOU CAN PROVIDE LINEUPS
If you know who managers intend to start in an upcoming GW, update
manager_lineup_watch.json with:
  "gameweek": [the week number],
  "manager_lineups": {"Andrew":{"starting_xi_ids":[11 distinct Draft player IDs],
    "note":"Confirmed by Andrew at [time]"}}
These show on the pickups page as commissioner-supplied PROSPECTIVE PREVIEWS,
never overwrite the actual Draft squads or points. The API confirms the actual
lineup at/after the relevant deadline. Ignore the illustrative separate
manager_lineup_watch_EXAMPLE.json unless you need formatting guidance.

The existing starting-XI-only scoring, injury/red/yellow icons, projections,
waiver estimate, standings and biweekly history remain intact.

FotMob stats: use external_projection_inputs.json with verified source URLs,
as before. This update does not falsely imply direct FotMob data access.
