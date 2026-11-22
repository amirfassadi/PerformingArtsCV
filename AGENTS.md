# Project working and release rules

- Use the connected workspace at `E:\miranco.project\Performing Arts-CV`.
- The production source is `codex/restore-artistic-design`. Never choose an issue
  branch as the live version merely because it is the current checkout.
- Preserve the approved charcoal/crimson RTL design. The historical imported ZIP
  and patch are not the current release source. See `docs/SITE_DEPLOYMENT.md`.
- Verify both templates and their CSS; HTTP 200 and backend tests alone do not
  establish that the correct frontend has been deployed.
- For frontend/release changes run the browser smoke with screenshots and review
  desktop/mobile output. It checks actual rendered theme colors and layout.
- Production deploys only an exact commit carrying its CI-generated
  `site-verified/<SHA>` tag. Never create or bypass these markers manually.
- Preserve `/etc/dgm-portfolio.env`, production accounts, database/private media,
  existing DNS zones, nginx configurations for other sites, and backup services.
- Schema/dependency upgrades require an explicit compatibility/rollback plan;
  the automatic deploy controller deliberately refuses those changes.
- VPS changes are currently performed by the user over SSH. Do not claim that
  local/GitHub edits have changed the VPS until deployment output verifies it.
