# Frontend follow-up: mobile dashboard

Status: READY_FOR_IMPLEMENTATION. Finding: FRONTEND-001.

Read docs/reports/frontend-google-review.md and docs/handoffs/GOOGLE-STUDIO.md first. Use the current codex/restore-artistic-design branch, including the received Studio CSS extension and signup formatting. Do not restart from main or replace this UI with a new design.

For local Copilot execution, the existing checkout is E:/miranco.project/PerformingArtsCV-artistic-review. The other checkout E:/miranco.project/Performing Arts-CV is the backend-stage checkout, not the frontend working tree. Verify branch and clean status before editing; preserve unrelated work.

## Required correction

The populated /dashboard/ is 420 CSS pixels wide in a 390- or 360-pixel viewport. Both document scrollWidth and real element bounds fail; header/navigation and dashboard content extend beyond the viewport. The same fixture passes at desktop 1440. Use the synthetic artist account and uploads from scripts/browser_smoke.py, including its long escaped text, rather than checking only an empty dashboard.

Find and correct the source of intrinsic width/overflow in grid/flex children, text, links or media as supported by browser measurements. Keep long literal user content readable and escaped. Do not solve this by adding overflow:hidden/clip to conceal content, shrinking the whole page, truncating all biographies, hiding controls or changing server validation.

Preserve charcoal #0c0d0e, red #b91c1c/#dc2626 and gold #d4af37, RTL, the original artistic homepage, accessible keyboard focus and the newly styled delete/file/copy controls. Check header navigation, media cards, quota section, invitation URL/copy and long external-link titles/URLs. Add CSS min-width/wrapping/media sizing only where investigation supports it.

Only templates/ and static/ application changes are allowed, plus this task's report. Do not change Python, dependencies, database, migrations, access/privacy, payment, invitation behavior, form contracts, CSRF, named routes or test hooks. Current database remains SQLite; no database migration is part of this task.

## Evidence and acceptance

1. Reproduce and record the before failure at 390 and 360; identify the offending element and cause.
2. Check home, login, valid/invalid/invitation-required signup, populated/empty dashboard, profile, directory/empty result, edit/upload/link forms and errors, plans, checkout and pending/failed payment at 1440, 390 and 360. Use local synthetic data and sandbox fixtures; no real payment. If any state cannot be checked, record it explicitly.
3. At 360/390, document.documentElement.scrollWidth must be <= innerWidth (allow at most 1px rounding). Also inspect visible content bounds so overflow hidden by ancestors is not counted as a pass. Preserve usability of all actions, invitation copying, keyboard focus and video controls.
4. Run the existing 64 Django tests and scripts/browser_smoke.py using the existing project virtual environment, Edge and isolated temporary DATA_ROOT/PRIVATE_MEDIA_ROOT. Reuse existing checks; do not create implementation-mirroring unit tests for CSS. No need to rerun unrelated concurrency checks for this CSS-only change.
5. Capture desktop and both mobile screenshots of the corrected populated dashboard; include paths and measured widths in the report. State which checks actually ran.

Fixed report: docs/reports/frontend-mobile-fix.md (absolute local path E:/miranco.project/PerformingArtsCV-artistic-review/docs/reports/frontend-mobile-fix.md). Include status READY_FOR_REVIEW or BLOCKED, root cause, changed files, actual test results, visual coverage/omissions and screenshot paths. Commit locally on codex/restore-artistic-design; record the resulting commit SHA in your final response. Publication belongs to the coordinator: do not push, authenticate, create/update PRs, merge or deploy.

If execution is in Google Studio without local repository access, return only the changed templates/static files as a valid patch or ZIP, this report and screenshots. Do not claim Django/browser tests passed if unavailable; the coordinator will run them.
