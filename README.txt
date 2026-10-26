TOUCHLINE 2.8 — CLEAN SCOUT + CONFIRMED TRANSFERS ONLY

Update the existing Render project. Upload all six application files from this ZIP
to the ROOT of your connected GitHub repository. Commit to main.
Keep Build: echo "No dependencies needed"
Keep Start: python server.py

CHANGES
- Removed the stale "Standings you supplied" snapshot panel from Overall Standings.
- Reworked player scout stats into a centered, readable 2-column grid.
- Deleted the old static 18-entry waiver-claims list.
- Transfer activity is now derived from consecutive 15-player Draft Gameweek rosters.
  The newer week's deadline must have passed before changes are shown.
  Only differences in the squad are shown; claims that did not change a roster
  do NOT appear. When several players move in one position, additions and
  departures are displayed separately to avoid inventing exact swaps.
- "Confirmed" means the membership change was observed in two Gameweek
  snapshots, NOT that its transaction type (waiver vs trade) is known.
- Injuries use a hospital (🏥) indicator. Yellow/red cards only display when match card stats are recorded.
- Custom XI-only scoring is unchanged.

LIMITATIONS
The roster comparison detects net changes between Gameweek squads. If a player
was added and dropped again between the snapshots, it will not appear. The Draft
API may not provide earlier lineups when a GW is missing; no changes are invented
for those intervals. Standings-based waiver priority is still an estimate.
