# Issue 9 follow-up — proxy identity and operational preparation

Status: READY_FOR_IMPLEMENTATION. Read docs/reports/issue-009-review.md, docs/reports/issue-009.md and docs/OPERATIONS.md first.

Continue in E:/miranco.project/PerformingArtsCV-artistic-review on codex/issue-9-deployment-backup. Current implementation source is 46ce479a404c3979213d1bea60b6945c99639744; preserve the following coordinator review commit as well. Do not reset history or replace approved frontend/media/payment/account work.

## Required correction — DEPLOY-001

The sample service starts Waitress with only --listen=127.0.0.1:8000. Independently running that configuration with two different synthetic forwarded client IPs yields REMOTE_ADDR=127.0.0.1 for both and strips untrusted X-Forwarded-For. Django's intentional REMOTE_ADDR limiter therefore treats all Caddy clients as one IP.

Configure the proxy-to-WSGI trust boundary explicitly using supported Waitress configuration for the pinned installed version and matching Caddy behavior. Trust only the actual proxy peer and required sanitized headers; keep app listener private and preserve the safe direct/non-proxy mode. Do not read arbitrary client X-Forwarded-For directly in Django or use wildcard proxy trust.

Update systemd/Caddy examples and both documented startup paths consistently. Explain scheme/HTTPS handling separately from client-IP identity. Test using the real installed WSGI server: two safely simulated trusted-proxy client identities must reach the intended REMOTE_ADDR values and have independent quotas; the same identity must share its quota across normal/admin login; a forged incoming forwarding chain or an untrusted peer must not bypass limits. If Caddy itself cannot be run locally, explicitly record which proxy side was emulated rather than claiming real Caddy integration or production deployment.

## Complete safe local preparation

- Add a bounded, configurable local HTTP workload exercise with synthetic accounts/data and limited concurrency. Record endpoint mix, duration/request count, failures and latency; keep quota concurrency as a separate correctness check. Do not assert pilot capacity without an approved group size and representative environment. Do not bypass security in application defaults.
- Prepare practical examples for backup scheduling, failure exit propagation and service/disk/backup-failure checks on the proposed platform. Distinguish a script/config template from an installed schedule or delivered alert. Do not invent an external alert destination, retention policy, SLA, RPO/RTO or cloud provider.
- Preserve verified backup staging/atomic publication, corruption rejection and isolated restore behavior. Do not delete real backups or live data, and do not schedule a job against real data as part of this task.

## Verification and delivery

Use E:/miranco.project/Performing Arts-CV/.venv/Scripts/python.exe and isolated temporary DATA_ROOT/PRIVATE_MEDIA_ROOT. Run relevant regressions/integration checks, the complete existing tests, check/migration checks and Edge browser smoke if application behavior changes. Record actual results and omissions. External domain/server/SMTP/merchant/backup destinations are still owner decisions; do local independent work without waiting for them.

Fixed report: E:/miranco.project/PerformingArtsCV-artistic-review/docs/reports/issue-009.md. Include corrected proxy command/config, proof of identities/quotas/anti-spoofing, operational sample behavior, workload conditions/results, tests, remaining external decisions and screenshots/log paths if relevant. Keep coordinator findings as historical review; do not self-award acceptance or mark real deployment complete.

No actual server deployment, DNS/account change, external mail/payment, secrets in Git, PostgreSQL migration, production scheduling, PR/push/authentication, merge or issue closure. Commit implementation/report locally only. Final response: status READY_FOR_REVIEW or concrete technical BLOCKED reason, full report path, branch and local SHA. Publication belongs to the coordinator.
