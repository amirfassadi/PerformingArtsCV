# Copilot task: artistic frontend polish and complete UI-state review

Act as a senior UI/UX designer and frontend engineer working with Persian, RTL, server-rendered Django templates. Inspect the existing implementation first, then improve the complete user-facing frontend of «درباره‌ی من» while retaining its approved cinema/theater visual identity and working backend integration. Implement the changes in this repository; do not merely print suggested replacement files.

## Workspace and baseline

- Repository checkout: E:/miranco.project/PerformingArtsCV-artistic-review.
- Reviewed application baseline: 86aae12485d4ac5d2248f1503a9debdacd2b9f51, plus the coordinator documentation commit containing this task.
- Check the branch/worktree first; preserve unrelated changes. Create codex/frontend-artistic-polish from the current reviewed clean HEAD. Do not start from old main, reset history or discard newer work.
- Read docs/handoffs/GOOGLE-STUDIO.md for approved visual/product constraints and the current reports for issues 7, 8 and 9. Its ZIP is a historical input package, not the latest application source. Use current branch templates/static as the source of truth.

## Strict boundaries

Application edits may touch only static/ and templates/. One explicit documentation exception is the required docs/reports/frontend-polish.md report. Do not edit Python, settings, dependencies, migrations, routes, forms, validators, tests, deploy files, existing coordinator reports or other documentation. Temporary visual/test harnesses and screenshots may live outside the repository.

Keep native Django rendering. Preserve all template logic and context semantics, named URLs, conditions/loops/blocks, escaping, CSRF, form method/action/enctype, input names/IDs/values, hidden signed payment quote, redirect fields, private-media URLs and invitation behavior. HTML layout may be reorganized without changing those contracts. Do not introduce |safe for user content, fabricated routes/data/features, fake OTP/account settings or unsupported structured education/experience forms.

## Visual direction

- Keep the existing artistic homepage/hero composition, cinema texture, editorial cards and brand «درباره‌ی من», subtitle «رزومه و نمونه‌کار اهالی سینما و تئاتر». Improve consistency and usability rather than replacing the approved design with a new concept.
- Preserve charcoal #0c0d0e, crimson #b91c1c/#dc2626, gold #d4af37 and warm light text #f4f3ef. Reuse existing root tokens; reconcile duplicates and maintain readable contrast, including muted/error text. Keep Vazirmatn with correct weights and reliable fallbacks; avoid duplicate font imports or requiring font availability for usable layout.
- Use RTL appropriately, but keep URLs, tokens, technical IDs and relevant email/file fields readable in LTR. Persian numeral presentation must not rewrite submitted numeric values, prices, URLs, tokens or IDs.
- Remove unstyled white surfaces from application-owned controls: delete/copy actions, selects, checkboxes and file-selector buttons. Preserve keyboard focus, disabled/error states and native video controls. Place any reset before component styles; avoid blanket late overrides or widespread !important patches.
- Navigation may gain an accessible mobile disclosure/menu if needed: real button, aria-expanded/aria-controls, keyboard and Escape support, visible focus and usable navigation when JavaScript is unavailable. No overlay may obstruct content or leave hidden links focusable.

## Complete real page/state coverage

Review homepage, login, valid/invalid/invitation-required signup; password-reset request/done/valid confirm/invalid-expired-used token/completion; dashboard/media/link management and invitation; profile/directory/search/favorites/paywall; plans/checkout/payment; support/content report/account-deletion request; and legal draft pages.

- Quota must use actual server/context values, not a hardcoded 100 MB. Keep above-quota and expired-access states accurate.
- Preserve #invitation-url, #copy-invitation, #invitation-copy-status, #invitation-heading, invite_count/invitees semantics and existing .media-card, .storage-panel, .link-row and .prose test hooks. Copy feedback must accurately reflect success/failure.
- Media layouts may distinguish video/image presentation using existing context, but should not crop or distort required content. Keep video controls usable, use suitable aspect ratios/object-fit and support long titles/URLs, empty grids and slow loading. Preserve the prior mobile overflow fix.
- Plans show only actual server-provided name/amount/duration/capacity. Do not invent monthly/annual tiers, discounts, prices, upgrade rules, refund promises or automatic renewal. Preserve the independence of browse and storage subscriptions and one-time purchase disclosure.
- Payment states paid/pending/unknown/canceled/failed and sandbox indicators must remain truthful. Preserve retry availability exactly as supported by existing template/backend logic. No claim that live payment or external email is enabled without evidence.
- Keep legal drafts visibly marked as drafts and support/deletion limitations accurate. Remove obsolete public-template branding where it exists, but do not erase required draft/sandbox/unconfigured warnings or modify backend-generated branding outside the allowed scope.
- Cover errors, non-field errors, empty states, validation help, rate-limit responses and form labels. If an existing plain-text 429 or backend-generated page cannot be styled within templates/static, report that exact constraint instead of editing Python, inventing an unused error template or claiming it was fixed.

## Independent evidence required from the executor

Use E:/miranco.project/Performing Arts-CV/.venv/Scripts/python.exe. Run all existing Django tests and scripts/browser_smoke.py with isolated temporary DATA_ROOT/PRIVATE_MEDIA_ROOT. Do not weaken assertions, application rate-limit defaults, security or payment behavior to pass tests. Explicit test-only fixture overrides must be documented and kept separate from limiter evidence. Do not add implementation-mirroring unit tests for cosmetic CSS changes.

Use Edge/Playwright to inspect real rendered pages at 1440, 390 and 360 pixels with synthetic accounts, orders and files. Check document scrollWidth AND visible content bounds (overflow:hidden alone is not success), long literal user text/URLs, navigation/menu, focus order, labels, clipboard, video controls and form errors. Exercise valid/used/invalid reset flows using a local test email backend or synthetic local tokens; send no external email. Use mock/sandbox fixtures only; no real gateway transactions.

Capture desktop and both mobile screenshots of homepage, populated dashboard and representative new account/support/payment/error states. Report which states were actually checked and which were unavailable. Do not call browser/server tests successful without running them; broken existing functional tests must be investigated without changing protected backend/test files.

## Delivery

Write E:/miranco.project/PerformingArtsCV-artistic-review/docs/reports/frontend-polish.md with status, reviewed baseline, changed file list, visual changes, preserved contracts, actual commands/results, page/state/viewport coverage, screenshot paths, backend-only limitations and omissions. State clearly that stages 5/6/7 still have unresolved product/external acceptance prerequisites.

Commit changed templates/static and this report locally on codex/frontend-artistic-polish. Do not push, authenticate GitHub, create/update PRs, merge, deploy, close issues, change DNS/accounts, send external mail or request credentials. Publication and acceptance belong to the coordinator.

Final response only: READY_FOR_REVIEW (or a concrete BLOCKED reason), full report path, branch and local commit SHA. Publication: coordinator responsibility.
