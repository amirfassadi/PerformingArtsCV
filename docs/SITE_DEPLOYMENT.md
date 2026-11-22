# DGM production deployment

The only production source branch is `codex/restore-artistic-design`.
Local development for this project uses `E:\miranco.project\Performing Arts-CV`.
Do not deploy an issue/backend branch or the historical Studio ZIP/patch.
The approved design is charcoal (`#0c0d0e`) and crimson (`#b91c1c`).

## Release gates

GitHub Actions runs Django checks, migration drift, 64 application tests and
concurrency checks on Python 3.11 (the VPS version) and 3.14. The browser job
uses isolated synthetic data and verifies account/media flows and the rendered
dark background/red primary button at 1440, 390 and 360px. Screenshots are
available in the `verified-design` Actions artifact. These assertions catch a
missing stylesheet or wrong theme; screenshots still need human review when
design changes are intentional.

Only after every check succeeds, the production branch's exact commit receives
the lightweight tag `site-verified/<40-character SHA>`. PR runs and other branch
runs cannot publish this marker. Do not create these tags manually. Restrict
production branch pushes and verification-tag writes to trusted maintainers.

The VPS polls GitHub over outbound HTTPS every two minutes. It deploys only the
current production branch head with its matching verification marker. No SSH
private key or GitHub token is stored on the VPS or in Actions secrets for CD.
Pending or failed checks leave the live version unchanged. Git/network failure
also leaves the site unchanged. An app deployment includes brief downtime while
the service is restarted; this is not a zero-downtime release mechanism.

## VPS layout

- Checkout/venv: `/home/amir/performingartscv` (live checkout deliberately detached at an exact tested SHA).
- Root-owned deploy controller: `/usr/local/sbin/dgm-deploy`.
- App: `dgm-portfolio.service`, bound to `127.0.0.1:8012`.
- Environment: `/etc/dgm-portfolio.env` (root-only; never commit or print it).
- Database and private media: `/var/lib/dgm-portfolio`.
- Public CSS/assets: `/var/www/dgm-static`, with public `release.json` identity.
- Backups: `/var/backups/dgm-portfolio` via `dgm-backup.service` and timer.

Before each deployment the existing verified backup service must succeed.
Code and public assets are reverted if deployment/HTTPS validation fails. Database
schema and dependency changes are deliberately refused by automatic deployment;
review compatibility and perform a planned manual upgrade for those changes.
No automatic database restore is performed. The deploy controller does not edit
DNS, nginx configuration, other sites, credentials, users or subscriptions.
CSS URLs include a content fingerprint and the actual HTTPS CSS bytes are compared
against the checked-out source after restart. `/static/release.json` exposes the
deployed commit so the browser/site can be matched to GitHub.

## One-time installation on the existing VPS

First publish and review the files in this commit. Fetch the production branch
as `amir`. Copy the deploy controller and systemd units out of that exact reviewed
commit, install them root-owned, then run the controller with `--check`. A `WAIT`
message means CI has not approved the candidate; do not bypass it.

```bash
git -C /home/amir/performingartscv fetch origin \
  '+refs/heads/codex/restore-artistic-design:refs/remotes/origin/codex/restore-artistic-design'
setup_dir=$(mktemp -d)
for path in scripts/deploy_vps.py deploy/dgm-deploy.service deploy/dgm-deploy.timer; do
  git -C /home/amir/performingartscv show "origin/codex/restore-artistic-design:$path" > "$setup_dir/$(basename "$path")"
done
sudo install -o root -g root -m 755 "$setup_dir/deploy_vps.py" /usr/local/sbin/dgm-deploy
sudo install -o root -g root -m 644 "$setup_dir/dgm-deploy.service" "$setup_dir/dgm-deploy.timer" /etc/systemd/system/
sudo /usr/local/sbin/dgm-deploy --check
sudo systemctl daemon-reload
sudo systemctl start dgm-deploy.service
sudo systemctl enable --now dgm-deploy.timer
sudo journalctl -u dgm-deploy.service -n 30 --no-pager
```

Run these commands in a `set -e` subshell so failures stop installation. The
installer itself requires manual SSH; committing files alone does not activate CD.
Updating the root-owned controller later also requires a reviewed manual install.

## Verification and stopping automatic releases

Open `https://dgm.co.ir/` and review desktop/mobile styling, then log in with the
existing account and test an invited signup and private upload. Never send real
credentials into the chat. Read `https://dgm.co.ir/static/release.json` for the
deployed SHA; use a unique query string if a browser cache is present.

```bash
sudo systemctl disable --now dgm-deploy.timer
sudo journalctl -u dgm-deploy.service -n 50 --no-pager
git -C /home/amir/performingartscv show-ref refs/dgm/previous
```

Stopping the timer leaves the currently running site up. For a deliberate rollback,
revert the relevant commit on the production branch, let CI approve the revert,
and deploy it normally. A failure of rollback itself needs operator attention.
Backups on this VPS are not off-server disaster recovery; that remains separate work.
