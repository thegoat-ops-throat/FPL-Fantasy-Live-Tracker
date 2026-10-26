Touchline 3.2 — admin toggle

1. Upload all application files in this ZIP to the ROOT of the EXISTING GitHub repository. Commit to main. Render auto-deploys.
2. In existing Render service > Environment, add TOUCHLINE_ADMIN_PASSWORD: a long unique password (never commit it to GitHub). Redeploy.
3. Open https://YOUR-RENDER-SERVICE.onrender.com/admin.html and enter your admin password. Enable or disable Top 10 Pickups for everyone.
4. For durability on Render free tier, create a GitHub fine-grained token limited to this repository with Contents: Read and write. Add TOUCHLINE_GITHUB_TOKEN and TOUCHLINE_GITHUB_REPO=thegoat-ops-throat/FPL-Fantasy-Live-Tracker as Render environment variables. Do not upload the token to GitHub. Changing the toggle then commits feature_flags.json to the repository, making it survive restarts. Changes may trigger an automatic deploy; the new file is loaded after redeploy.
5. Without the GitHub token, changes work immediately but feature_flags.json is only local ephemeral data. It may revert on Render restart.

This affects public visibility, not underlying recommendations. All public visitors receive a features setting via /api/status, and the pickup candidate list is removed from that response while disabled. The admin password is checked on the server; only a private POST can change the setting.
