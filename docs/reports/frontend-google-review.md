# Google Studio frontend review — 2026-11-10

Status: CHANGES_REQUESTED (FRONTEND-001).

## Received and applied

The actual delivery received was a pasted unified diff, not the ZIP, REPORT.md or Studio screenshots listed in the preceding message. It changes only static/app.css and templates/registration/signup.html. CSS adds 716 lines; signup is reformatted without changing its invitation branches, form fields or CSRF token.

Directory prefixes and hunk counts in the supplied diff were unsuitable for direct git apply. After git apply checks rejected it, the coordinator matched each complete old-text hunk exactly once against the handoff source and replaced it with its supplied new text. No CSS rules or application behavior were invented during application. git diff --check passed.

Base: local 8b97a83128d03e0d720579e60cc34339917f3139, corresponding to published cc3759a85b64eb40cd6caa1cb2a19a8cc75ab0fd. Backend remains the accepted issue-6 implementation. The handoff ZIP in docs/handoffs is the historical input package, not this completed delivery.

## Independent validation

- Django: all 64 tests passed; system check reported no issues. Isolated temporary database/media paths were used.
- Existing complete Edge browser smoke passed: invitation-only signup, clipboard, privacy/deactivation, profile editing, real private image and H.264 MP4 upload/playback, external link add/delete, paywall, paid browsing, favorites, mobile directory, backup/restore.
- Additional visual sweep used synthetic data and inspected element bounds as well as document scrollWidth, rather than relying on body overflow-x:hidden. It captured home, populated dashboard, profile edit, upload, add-link, plans and profile at widths 1440, 390 and 360.
- Home/edit/upload/add-link/plans/profile: no horizontal overflow in those 18 checks. Dashboard desktop: no overflow. Dashboard mobile: failed both checks (see below).
- Dashboard delete-button computed background was rgba(185, 28, 28, 0.12), matching the intended dark red treatment. Invitation copy retained a visible focus outline. Desktop and failing mobile screenshots were visually inspected.
- The supplementary visual sweep deliberately stopped after collecting its results; its nonzero exit is not a failed second functional smoke or an application crash.
- Checkout/payment states and every possible empty/error/account variant were not independently swept at all three widths; do not claim complete visual acceptance.

## FRONTEND-001 — dashboard exceeds mobile viewport

With the existing browser smoke's populated artist account (private image/video and long literal text used to check escaping), dashboard document.documentElement.scrollWidth is 420 at both viewport widths 390 and 360. Element-bound checks also find header/navigation and dashboard content outside the viewport. Desktop width 1440 passes. Screenshot confirms clipped content.

Reproduce by using scripts/browser_smoke.py's synthetic artist setup, opening /dashboard/ after media uploads, then checking both mobile widths. Check real content bounds, not just whether a scrollbar is hidden. Preserve literal escaping of user text. Investigate grid/flex intrinsic widths, long text/URLs and media sizing; the root cause has not been conclusively isolated.

Fix instructions: docs/handoffs/FRONTEND-MOBILE-FIX.md. Publication is for review; no merge or deployment is authorized by this report.

Local evidence: E:/miranco.project/Artistic-Preview-Google-Completed/ (home-*, dashboard-*, edit-*, upload-*, link-*, plans-*, profile-* screenshots). These screenshots and the temporary visual harness are outside the repository and not claimed to be part of the Studio delivery.

## Progress

Core accepted MVP stages remain 4/8 = 50% (equal stage weights). This UI follow-up does not complete another MVP stage. Frontend final acceptance remains pending FRONTEND-001 and remaining visual coverage.
