# Issue 7 — coordinator review

Reviewed implementation: 6f0cb5f4fca9c73e90634720439a88830172a272 (implementation commit 43cd6fa20db31c17a43d367d8496b0278ca01ca9). Base: ca0fa823fea5a155b4e108a83d31dfdbf1fae331. Date: 2026-11-10.

Historical disposition for 6f0cb5f: CHANGES_REQUESTED. Update: technical correction 92fe61fa69fedf91b9f75b460f59b887d3bb1349 independently accepted; PAY-001/PAY-002 resolved. Current progress is Stage 5 5/7 = 71.4%, overall 58.9%; see the acceptance addendum below. Product decisions and external sandbox/live-payment prerequisites remain outstanding. The original findings/rubric below are retained as historical evidence.

## Independent verification

All 67 Django tests passed with isolated temporary data/media roots; system check passed and makemigrations --check --dry-run reported no missing changes. The complete existing Edge browser smoke independently passed (invitations/clipboard, privacy, edits, private image and recorded H.264 playback, external links, paywall/paid browsing, favorites, mobile, backup/restore). Playback duration was 1.735167s at 160x90, readyState 4. This smoke does not exercise a real bank transaction. Additional isolated adversarial verification reproduced the two findings below without any network gateway request. Passing existing checks does not resolve these adversarial failures.

## PAY-001 — callback cancellation prevents authoritative recovery (P1)

Locations: portfolio/payment_views.py callback NOK branch; portfolio/billing.py verify_payment canceled guard; portfolio/management/commands/reconcile_payments.py pending/unknown-only filter.

A browser-supplied callback with the matching order authority and Status=NOK changes a pending order to canceled. Canceled orders are then rejected before server-to-server verification, omitted from reconciliation and have no owner retry button. A later successful callback cannot resolve the order, even if the gateway would return a valid receipt. Matching authority alone does not make the browser's Status an authoritative settlement result.

Independent reproduction, temporary SQLite and mocked Zarinpal.verify(return_value='918273'):

1. Create a pending synthetic order with an authority.
2. GET callback with matching Authority and Status=NOK: status becomes canceled.
3. GET callback with Status=OK, then authenticated owner POST retry, then reconcile_payments --verify.
4. Observed: status still canceled, gateway verify called zero times, zero entitlements, command prints 'Reconciled 0 payment(s); 0 still unresolved.'

No assertion is made that a real bank transaction occurred in this experiment. It demonstrates that the implementation blocks authoritative verification of this event sequence. Preserve a safe recovery/reconciliation path for authority-bearing unverified orders; grant access only after valid verification. A late NOK must also never downgrade a paid order. Fix instructions: docs/handoffs/ISSUE-007-PAYMENT-FIX.md.

## PAY-002 — failed-order UI offers an unusable retry (P2)

templates/portfolio/payment.html groups failed into the generic unknown branch and renders the retry form when authority exists. billing.verify_payment rejects failed immediately. Independently rendering a synthetic failed order with authority confirms the retry URL is present in the HTML. Align the displayed message/action with whether authoritative verification is supported; distinguish definitive rejection from uncertain outcome and from request failure without authority. Keep the approved artistic theme and mobile behavior.

## Concurrency evidence still needed

The added tests cover sequential repetition; the delivered evidence does not establish actual simultaneous callback/owner-retry/reconciliation execution. Exercise separate database connections/workers on isolated SQLite. Verify exactly one grant and stable final status after conflicting/duplicate events, without leaking database lock/integrity exceptions. This is an evidence gap, not a reproduced duplicate-grant claim.

## Progress rubric — seven original Issue 7 checklist items

Only completely verified items count; partially implemented items remain open. This rubric will be reused for subsequent reviews.

| Original item | Accepted | Evidence / remaining work |
|---|---|---|
| Approved prices, durations, capacities and upgrade rules | No | Product decisions absent; no invented values allowed. |
| Independence and clear display of browse/storage, validity/history, both allowed | Yes | Models/plan UI, entitlement isolation tests and previously reviewed plans/history states. |
| Server-side amount and stable order snapshot | Yes | Existing and delivered BillingTests including changed-plan confirmation and saved snapshot passed. |
| Request/callback/verify with correct unsuccessful/canceled/unknown behavior | No | PAY-001/PAY-002 remain. |
| Verified activation and duplicate prevention under simultaneous events | No | Sequential tests pass; simultaneous evidence and repaired state transitions required. |
| Recovery/reconciliation and support guide | No | New command/guide exist but PAY-001 excludes a recoverable event sequence. |
| Real sandbox then controlled live purchase/receipt reconciliation | No | Merchant/public HTTPS and live exercise unavailable. |

Stage 5: 2/7 = 28.6%. Overall eight equally weighted stages: (4 + 2/7)/8 = 53.6%. First four core stages remain accepted; other future stages have no accepted credit in this calculation. These percentages describe acceptance coverage, not production readiness or time spent. Stage 5 must stay open.

## Acceptance addendum — corrected source 92fe61f

Implementation reviewed: 92fe61fa69fedf91b9f75b460f59b887d3bb1349 (code commit 079885e782112731a6bd57d2e27c591150497a19). Date: 2026-11-10. Worktree was clean at review start. Changes were confined to payment logic/tests/docs and the payment status template; approved homepage/theme/mobile CSS and media/invitation implementation were preserved.

Independent validation:

- All 70 Django tests passed, system check reported no issues, migration check reported no missing migration, and diff whitespace checks passed.
- Existing full Edge browser smoke passed: invited signup/copy/privacy, profile editing, private image and real recorded H.264 playback (1.7368s, 160x90, readyState 4), link lifecycle, paywall/access/favorites/mobile and backup/restore. This is application-flow coverage, not a real gateway purchase.
- Repeated the prior PAY-001 sequence with an isolated on-disk SQLite database and mocked positive gateway verification: NOK remains unknown; subsequent OK verifies and creates one grant; owner retry is idempotent; late NOK and malformed callback leave paid unchanged. Verifier called once for that sequence.
- Ran three distinct actual application entry points simultaneously against one separate order, using separate worker database connections and a barrier inside the mocked gateway response: anonymous callback OK, authenticated owner retry POST, and reconcile_payments --verify. Both HTTP responses were 302, reconciliation completed, no worker errors occurred, final status was paid, and exactly one entitlement and one matching receipt were stored for that order. This supplements the delivered test, which invokes verify_payment from three workers rather than exercising the three wrappers.
- Previously canceled and failed orders with authority were independently recovered by reconciliation with distinct synthetic receipts. Failed orders without authority rendered no retry URL. No gateway network requests were made.
- Additional Edge bounds checks for pending/failed/paid/canceled/unknown synthetic receipt pages with authority passed at 1440, 390 and 360 (15 checks); empty dashboard passed at the same widths (3 more). Both document scrollWidth and header/main descendant bounds were inspected. Rendering checks do not demonstrate settlement.

PAY-001 and PAY-002 are resolved in reviewed local behavior. The local concurrent-activation evidence gap is closed for the exercised SQLite scenario. This does not claim exhaustive load, other database engines or provider-side concurrency verification.

Updated original seven-item rubric: items 2 (independent subscriptions), 3 (server amount/snapshot), 4 (payment state handling), 5 (verified/idempotent activation with local concurrency) and 6 (technical reconciliation/support workflow) accepted. Item 1 (approved commercial prices/durations/capacities/upgrade policy) remains unapproved. Item 7 (real sandbox and controlled live purchase with receipt reconciliation) remains unexecuted.

Current Stage 5: 5/7 = 71.4%. Current overall MVP: (4 + 5/7)/8 = 58.9%. Stage 5 and Issue #7 remain incomplete. Payment production readiness is not granted. Technical implementation can be reviewed as ready; no merge, deployment or live transaction has been performed. Next required inputs are product-approved plan terms and an appropriately prepared merchant/public HTTPS callback environment; no credentials belong in repository reports or chat.
