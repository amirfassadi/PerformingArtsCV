# Issue 8 — independent coordinator review

Reviewed source: eb18b141a926f679f5654d2d3c216eb512e6b7a6 (code commit 0e61cd464df3b34efa1eb0b2ac7c73703855a9e0). Base: fcf1beefb88659beaaf669611421e192437fdedc. Date: 2026-11-10. Initial worktree clean.

Historical disposition for eb18b141: CHANGES_REQUESTED. Update: ACCOUNT-001 and ACCOUNT-002 independently resolved in 95c8bfd4c40c79c4f6ecc95310c840dff10d2f75; see follow-up below. Stage 6 remains incomplete. Original review evidence follows: 76 Django tests and the existing Edge smoke passed, but did not cover the reproduced failures or all new UI states. No real email was sent and no deployment or live payment was performed.

## ACCOUNT-001 — empty POST at rate limit returns HTTP 500 (P1)

portfolio/views.py login_view constructs AuthenticationForm with data=request.POST or None. An empty POST therefore constructs an unbound form. Once the throttle denies the request, form.add_error on this unbound form raises instead of returning the intended 429 response. The same POST-or-None pattern exists in upload/support and should be checked rather than copying a narrow login-only correction.

Independent reproduction on isolated SQLite with LOGIN_RATE_LIMIT=1 and Client(raise_request_exception=False): POST /login/ with {} twice returns [200, 500]. A subsequent nonempty login POST returns 429 as intended. Empty/malformed requests must never turn the defensive response into an application error. Test all affected forms with exhausted throttles and preserve visible errors and Retry-After.

## ACCOUNT-002 — admin login bypasses application login throttle (P1)

config/urls.py applies the custom limiter only to /login/; /admin/login/ remains the Django admin authentication view without equivalent protection. After the same IP is already throttled at /login/, three invalid credential POSTs to /admin/login/ returned [200, 200, 200] and continued processing the authentication form. These are failed logins, not granted access; the finding is bypass of the attempt limit through another authentication endpoint.

Apply effective persistent, cross-worker login-attempt protection to all credential-entry paths including admin. Do not merely redirect or hide the admin form, trust arbitrary forwarding headers, bypass CSRF, break safe next handling or weaken Django model permissions. Verify the intended shared/separate limiter policy explicitly so switching endpoints cannot create an unlimited guessing path.

## Outstanding validation and prerequisites

The implementer explicitly did not independently inspect all new pages/states at 1440/390/360 or with keyboard navigation. This remains a review gap, not a passing visual result. Existing smoke coverage of old routes does not cover new password-reset/support/legal/429 states. Actual external email delivery and approved legal/support/contact/retention terms also remain unverified. Do not call email backend tests successful real delivery or drafts approved policies.

Full original six-item Issue 8 acceptance has not been awarded in this review: management-role matrix still needs independent checking; real email unavailable; request limiting has open findings; legal terms await approval; support process/contact awaits approval; full new-page usability coverage is pending. Partial implementation is acknowledged, but no new fully verified stage-6 checklist item is credited yet. Stage 6 accepted coverage: 0/6 for this review; overall accepted MVP remains 58.9% (four complete stages plus 5/7 of stage 5, across eight equal stage weights). This is acceptance coverage, not an estimate of implementation effort.

Next action is the corrective task docs/handoffs/ISSUE-008-ACCOUNT-FIX.md, to be executed by Copilot locally. Do not start deployment from this unaccepted account-security version. Missing SMTP infrastructure or legal approval should not stop these local technical corrections.

## Follow-up verification — 95c8bfd

Source: 95c8bfd4c40c79c4f6ecc95310c840dff10d2f75. All 81 Django tests independently passed on isolated temporary data/media roots, including the permission matrix and SQLite limiter concurrency tests. System check reported no issues; git diff whitespace check passed. Independent reproduction with LOGIN_RATE_LIMIT=1 now gives empty normal-login POST results [200,429] and a subsequent invalid admin-login POST returns 429. ACCOUNT-001 and ACCOUNT-002 are resolved. Reset requests now have a separate persistent limiter.

This follow-up did not independently repeat full Edge smoke or the implementer's new-page visual sweep; its claimed results remain implementer evidence rather than new coordinator evidence. In particular, new-page 429/reset visual feedback and complete keyboard/valid-reset browser coverage remain for final usability acceptance. External email delivery and legal/contact/support policy approvals remain unavailable.

Original Issue 8 six-item rubric, current acceptance: item 1 (model-scoped administration permissions) and item 3 (request attempt limits) accepted by source review and independent regression/concurrency tests. Item 2 needs real email delivery; item 4 needs approved legal/content/retention terms; item 5 needs approved contact/handling procedure; item 6 needs completed independent new-page usability verification. Current stage 6 = 2/6 = 33.3%; overall = (4 + 5/7 + 2/6)/8 = 63.1%. These percentages are acceptance coverage, not implementation effort or production readiness. Previous 58.9% was the pre-correction checkpoint.

Next parallel work may prepare Issue 9 deployment/backup artifacts and isolated recovery tests, but must not deploy to a real server, declare stages 5/6 complete or fabricate missing infrastructure/product decisions. No merge, external email or live transaction is authorized by this review.
