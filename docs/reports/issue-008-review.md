# Issue 8 — independent coordinator review

Reviewed source: eb18b141a926f679f5654d2d3c216eb512e6b7a6 (code commit 0e61cd464df3b34efa1eb0b2ac7c73703855a9e0). Base: fcf1beefb88659beaaf669611421e192437fdedc. Date: 2026-11-10. Initial worktree clean.

Disposition: CHANGES_REQUESTED. Existing 76 Django tests independently passed with isolated temporary database/media roots and system check reported no issues. The complete existing Edge smoke independently passed (invited registration/copy/privacy, profile edits, private image and recorded H.264 video playback, links, paywall/access/favorites/mobile, backup/restore; video 1.738s at 160x90, readyState 4). Those checks do not cover the reproduced failures below or all new UI states. No real email was sent and no deployment or live payment was performed.

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
