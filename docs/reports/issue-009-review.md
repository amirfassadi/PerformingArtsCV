# Issue 9 — independent coordinator review

Reviewed source: 46ce479a404c3979213d1bea60b6945c99639744 (implementation 6e70af79346de2094370fd363bb9a66532d8a174), based on ae3b84d4670831456446b3995fc48e93d279d826. Date: 2026-11-10. Initial worktree clean.

Disposition: CHANGES_REQUESTED for DEPLOY-001. The prepared backup/recovery behavior below is independently verified; no real deployment, external backup transfer or production monitoring was performed.

## Independent verification

- All 84 Django tests passed with isolated temporary data/media roots; system check passed, migration check found no missing changes.
- The complete existing Edge browser smoke independently passed, including invitations/copy/privacy, profile edits, private image and recorded H.264 playback (1.7374s, 160x90, readyState 4), links, paywall/access/favorites/mobile and backup/restore. This is local application-flow evidence, not a deployed-server or real payment test.
- Independently created two synthetic accounts/profiles, their invitation/link relationship, a paid Payment linked to an Entitlement and a private-file record/content. Ran healthcheck, backup_to_secondary and verify_backup using a second temporary local directory.
- Copied the resulting database and private media to a third isolated restore directory. A new Django process using those restored paths verified account/profile/link counts, inviter/invitee relationship, paid order/entitlement link and exact private-file bytes. FULL_RESTORE_PASS.
- Deleted only the original synthetic media payload, attempted a second secondary backup and confirmed rejection, no final or staging artifact added, and the previously published snapshot remained valid. INCOMPLETE_SNAPSHOT_NOT_PUBLISHED_AND_PREVIOUS_SNAPSHOT_INTACT.
- Corrupted only the temporary snapshot's media bytes and confirmed verify_backup rejected it. CORRUPT_SNAPSHOT_REJECTED.
- All mutations above were confined to newly created temporary directories; no real application data was touched. This was a local destination/restore test, not independent offsite durability or disaster recovery evidence.

## DEPLOY-001 — reverse-proxy identity is not configured end to end (P1)

deploy/performingartscv.service.example starts Waitress with only --listen=127.0.0.1:8000. Caddy forwards requests to that loopback address, while portfolio.security.request_identity uses REMOTE_ADDR and intentionally ignores arbitrary forwarding headers. No explicit trusted proxy/header translation is configured in the WSGI server command. TRUST_PROXY_HTTPS only handles scheme in Django; it does not restore the client address used by the limiter.

Independent live local reproduction using the installed Waitress and exactly the sample listen configuration: send two requests with different synthetic X-Forwarded-For values, 198.51.100.10 and 203.0.113.20. The WSGI environment for both returned REMOTE_ADDR=127.0.0.1 and HTTP_X_FORWARDED_FOR=null. The default behavior safely strips untrusted headers, but the prepared proxy/server integration does not replace it with a trusted client identity. Behind this template, users share the same throttle key and can exhaust each other's login/reset/signup quotas.

Correct the proxy-to-WSGI trust boundary explicitly, using supported trusted-proxy configuration, an exact trusted peer/header policy and a proxy that overwrites/sanitizes incoming identity headers. Keep direct application exposure blocked. Do not fix this by trusting all incoming X-Forwarded-For in Django or setting wildcard trust. Add integration evidence for distinct proxied clients, same-client limits and spoofed headers/untrusted peers. Keep the non-proxy local mode safe.

## Other acceptance gaps

The quota concurrency smoke is useful, but is not an HTTP workload/latency/capacity test. Do not label it a completed representative pilot load test. A PowerShell example script is not evidence of an installed scheduled job, completed independent-destination transfer or operational alert delivery. Healthcheck checks database/disk/media path; it does not itself monitor stopped service or failed backup delivery. These are explicitly incomplete, not additional reproduced application bugs.

## Original Issue 9 seven-item rubric

1. Approved domain/server/email/second backup location: not accepted, decisions absent.
2. Real HTTPS deployment, production settings and automatic service restart: not accepted, only templates; DEPLOY-001 open.
3. Private-file behavior on the actual server and release checks: not accepted, actual server unavailable.
4. Scheduled second-location backups/secure transfer with approved retention: not accepted, local preparation only.
5. Full isolated restore and data/file reconciliation: accepted from the independent local exercise above.
6. Operational error/disk/service/backup failure monitoring: not accepted, health command alone is partial.
7. Representative load evidence and deployment/rollback/restore guide: not accepted, quota concurrency alone is insufficient.

Stage 7 = 1/7 = 14.3%. Overall = (4 + 5/7 + 2/6 + 1/7)/8 = 64.9%. Prior stage-5/6 gaps remain open; Issue 9 must remain open and no production-readiness claim is made.

Next task: docs/handoffs/ISSUE-009-DEPLOYMENT-FIX.md. Executor Copilot; preparation and isolated testing only. Publication belongs to the coordinator.
