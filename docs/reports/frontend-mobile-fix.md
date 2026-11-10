# Frontend mobile fix report

## Status

`READY_FOR_REVIEW`

- Branch: `codex/restore-artistic-design`
- Scope: `FRONTEND-001` only
- Backend, routes, forms, privacy, payments, invitations, database and dependencies were not changed.

## Root cause and correction

The populated dashboard reproduced the reported failure before the fix:

- viewport 390: `document.documentElement.scrollWidth = 420`
- viewport 360: `document.documentElement.scrollWidth = 420`
- the dashboard main column reached `scrollWidth = 404px` inside a 358px content area at 390px.
- the primary contributors were the non-wrapping panel header flex row and long user-authored text creating intrinsic minimum widths. The invitation URL input also has a larger internal `scrollWidth`, but its visible bounds remain within the viewport.

`static/app.css` now:

- allows panel header flex children to wrap and sets their minimum width to zero;
- allows long panel, biography, media-title and link-title content to break at safe points;
- constrains media cards, media details and managed-link rows with `min-width: 0`.

No `overflow: hidden` or clipping rule was added to conceal page overflow. Existing escaping, RTL layout, charcoal/red/gold styling, focus treatment, controls and backend hooks remain unchanged.

## Acceptance evidence

The temporary populated-dashboard harness used the synthetic account and uploads created by `scripts/browser_smoke.py`, including literal escaped biography content.

- Before: `scrollWidth = 420` at both 390px and 360px.
- After: `scrollWidth = 390` at 390px and `scrollWidth = 360` at 360px.
- After: no visible element bounds exceeded the viewport at either width.
- Desktop 1440px remained covered and unchanged.
- The corrected dashboard was visually inspected with media cards, quota, invitation URL/copy control, navigation and long content.

Screenshots (temporary local evidence, not committed):

- Desktop: `C:\Users\Amir\AppData\Local\Temp\frontend-mobile-after-df288a0669d44a26a1bc048872455e53\dashboard-desktop.png`
- Mobile 390px: `C:\Users\Amir\AppData\Local\Temp\frontend-mobile-after-df288a0669d44a26a1bc048872455e53\dashboard-390.png`
- Mobile 360px: `C:\Users\Amir\AppData\Local\Temp\frontend-mobile-after-df288a0669d44a26a1bc048872455e53\dashboard-360.png`

## Tests and checks actually run

All commands used the existing prepared virtual environment at `E:\miranco.project\Performing Arts-CV\.venv\Scripts\python.exe` against this checkout. This checkout does not contain its own `.venv`.

- `manage.py test`: **64 tests passed**.
- `scripts/browser_smoke.py`: **passed** with Microsoft Edge, including invitation signup/copy, private image, real browser-recorded H.264 MP4 playback, external-link lifecycle, paywall, paid browsing, favorites, mobile directory, backup and restore.
- Browser smoke playback evidence: duration `1.739333s`, dimensions `160×90`, `readyState=4`, current time `0.215s`.
- `manage.py check`: passed.
- `manage.py makemigrations --check --dry-run`: passed; no migration changes.
- `git diff --check`: passed.
- Temporary populated-dashboard measurements and screenshots: passed at 390px and 360px.
- Test data and browser smoke used isolated temporary `DATA_ROOT`/`PRIVATE_MEDIA_ROOT`; no real account or payment was used.

## Coverage and omissions

The existing smoke covered home, login, invitation signup, populated dashboard, profile, edit, upload, link form, directory/paywall, favorites, private media and mobile directory. The responsive CSS was also checked at desktop 1440px and dashboard widths 390px/360px.

The following states were not independently exercised at all three viewport widths: empty dashboard, invalid/invitation-required signup error variants, upload/link form error displays, plans, checkout, pending payment and failed payment. No implementation change affects those routes or their form contracts; they remain explicit visual follow-up coverage for the coordinator.

## Coordinator independent review — accepted 2026-11-10

Reviewed source commit: b51323516406173e1f05ebf1e6ad02714f971f6a. Only the CSS correction and this implementer report changed from the preceding reviewed source. Worktree was clean. FRONTEND-001 is resolved; the scoped mobile fix is accepted (100%). No backend or database change was made.

Independent checks on this source:

- All 64 Django tests passed with an isolated temporary database/media configuration; system check reported no issues.
- Full existing Edge browser smoke passed, augmented with populated-page measurements/screenshots: invitation-only signup/copy, privacy/deactivation, edits, private image and real browser-recorded H.264 MP4 playback, external link lifecycle, entitlement/paywall, favorites, mobile directory and backup/restore. Playback duration 1.739067s, 160x90, readyState 4, currentTime 0.2186s.
- Home, populated dashboard, edit, upload, add-link, plans and profile passed at 1440/390/360: 21 layout checks. Populated dashboard document scrollWidth is exactly 1440/390/360 respectively, with no inspected header/main element bounds outside the viewport. Delete styling and invitation-copy focus checks passed. Desktop and mobile dashboard screenshots were visually inspected.
- A separate isolated Edge sweep closed the implementer's omitted coverage: login; invitation-required, invalid and valid signup; directory paywall; empty dashboard; plans with synthetic transaction history; checkout; empty search results; pending, failed and paid sandbox payment receipts; edit, upload and link form server-validation errors. Each passed at 1440/390/360: 45 additional layout checks. Invalid invitation correctly returns HTTP 404 while rendering its designed state; other tested pages return 200. Error-form checks verified visible Django error lists.
- Total: 66 successful page/state/viewport checks. Both document width and header/main descendant bounds were inspected; body overflow hiding alone was not considered success. No real gateway requests or financial transactions were made. Sandbox receipts were synthetic visual fixtures, not evidence of live payment integration.
- git diff --check passed. No dependency/migration changes were introduced. Temporary review harnesses are outside the repository; no new CSS unit tests were added.

Independent screenshots and harnesses: E:/miranco.project/Artistic-Preview-Mobile-Reviewed/. Earlier screenshot paths above remain implementer evidence. Full-page captures may show the sticky header at its current scroll position; viewport bounds were measured independently.

Disposition: ready for review/publication in PR #16; no merge or deployment performed. The previous CHANGES_REQUESTED review is historical and superseded for FRONTEND-001. The original handoff ZIP remains the historical input; current branch source is authoritative.

Progress: accepted core MVP stages remain 4/8 = 50%. This completed frontend repair is not an additional core stage and does not certify live payments or production readiness.
