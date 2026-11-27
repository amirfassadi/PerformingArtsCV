# Issue 7 follow-up — payment recovery and state consistency

Status: VERIFIED_COMPLETE for the technical correction, source 92fe61fa69fedf91b9f75b460f59b887d3bb1349 (2026-11-10). PAY-001/PAY-002 and the local concurrency evidence gap were independently resolved. Stage 5 overall remains incomplete pending product terms and real sandbox/live verification. See docs/reports/issue-007-review.md acceptance addendum. Instructions below are retained as the original task, not a request to repeat completed work.

Read docs/reports/issue-007-review.md, docs/reports/issue-007.md and docs/PAYMENTS.md first. Continue from the current codex/issue-7-payment-plans local branch in E:/miranco.project/PerformingArtsCV-artistic-review, including coordinator review documents. Preserve existing history and unrelated changes; do not reset or force-push. Do not start from main or revert the accepted frontend/mobile/media work.

## Required work

1. Reproduce PAY-001: pending authority-bearing order -> callback NOK -> callback OK -> owner retry -> reconciliation. Currently the mocked gateway verifier is never called and the order stays canceled even when its mocked authoritative response would confirm payment.
2. Separate browser callback indications from authoritative settlement. Keep unverified authority-bearing orders recoverable through an appropriately scoped owner/support verification path. A callback indication alone must neither grant access nor irreversibly block legitimate verification. Preserve receipt/amount/environment validation and all ownership checks; do not add a manual grant bypass.
3. Define and document consistent state transitions, including late/duplicate NOK or malformed callbacks after paid, cancellation then successful verification, transient timeouts, definitive gateway rejection and failed request without authority. Read fresh state under the transaction before granting; do not let stale objects or competing callbacks corrupt final state.
4. Update reconcile_payments and docs/PAYMENTS.md to match the repaired recovery model. Listing must remain read-only. Verification must not silently skip authority-bearing recoverable orders or report zero unresolved while hiding them. Do not send malformed/no-authority requests to the provider.
5. Fix PAY-002: failed/unknown/canceled messages and buttons must reflect the supported transition. No action should be rendered if its request is guaranteed to be rejected for that state. Preserve charcoal/red/gold styling, mobile layout, form CSRF and existing hooks.
6. Add meaningful regression tests for the exact sequence and late/conflicting callbacks. Exercise real local concurrency with separate SQLite connections/workers for callback, owner retry and reconciliation against the same order, using mocked gateway responses. Assert one entitlement, one receipt, stable paid state and handled contention, not merely sequential double calls. No merchant or live payment is needed for these corrections.

## Verification and delivery

Use E:/miranco.project/Performing Arts-CV/.venv/Scripts/python.exe. Run the full existing test suite, focused state/concurrency regressions, check/migration checks and existing Edge browser smoke. Use isolated temporary DATA_ROOT/PRIVATE_MEDIA_ROOT only. Check corrected payment status pages at desktop 1440 and mobile 390/360 without horizontal overflow. Report actual results, commands and omissions; mock responses are not live gateway evidence.

Update the fixed implementer report docs/reports/issue-007.md with technical findings and evidence, separating technical progress from external/product prerequisites. Keep the coordinator review file as historical review; do not overwrite its findings or mark your own work accepted. Do not fabricate prices, capacities, upgrade/refund/support policies. External merchant/public callback and product decisions can remain pending while technical work proceeds; do not stop all work merely because live testing is unavailable.

Do not migrate SQLite to PostgreSQL, change media/privacy/invitation behavior or redesign the frontend. No new dependencies unless technically necessary and explained. No real gateway transaction, credential request, key in Git, deployment, issue closure, merge or authentication/push attempt. Commit locally only; publication and independent review belong to the coordinator.

Final response: READY_FOR_REVIEW if the technical corrections are ready for independent review (explicitly retain incomplete live-payment criteria in the report), otherwise BLOCKED with a concrete technical blocker; include the full report path E:/miranco.project/PerformingArtsCV-artistic-review/docs/reports/issue-007.md, branch and local SHA. Publication: coordinator responsibility.
