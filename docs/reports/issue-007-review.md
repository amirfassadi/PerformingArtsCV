# Issue 7 — coordinator review

Reviewed implementation: 6f0cb5f4fca9c73e90634720439a88830172a272 (implementation commit 43cd6fa20db31c17a43d367d8496b0278ca01ca9). Base: ca0fa823fea5a155b4e108a83d31dfdbf1fae331. Date: 2026-11-10.

Disposition: CHANGES_REQUESTED for technical issues, plus separate outstanding product decisions and external live-payment prerequisites. The implementer's BLOCKED report is accurate about missing external verification, but those prerequisites are not the only remaining work. No real payment, credentials, deployment or merge is part of this review.

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
