# Project instructions

Product: «درباره‌ی من», PerformingArtsCV. Read `docs/BACKEND_IMPLEMENTATION.md`, `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/FRONTEND_BACKEND_CONTRACT.md` and `docs/VPS_PREPARATION.md` before implementation.

- Extend the existing Django application and server-rendered Persian RTL frontend. Preserve subscriptions, private media, server-calculated storage quota, CSRF, sessions and signed checkout quotes.
- `FRONTEND_BACKEND_CONTRACT.md` contains proposals, not working endpoints. Verify against views/models/URLs. `BACKEND_IMPLEMENTATION.md` resolves ambiguities in that proposal.
- Phone verification must precede saving artist details and publishing. Verification is proof of phone control, not professional identity or endorsement of work history.
- Email verification is a later phase and must not gate profile completion. Keep account email/phone private and separate from user-selected professional contact.
- No hard-coded OTP, fabricated successful SMS, fake payment or production bypass. Development test adapters must be isolated and disabled in production.
- Education, experience, collaborators and attached works must enforce ownership on every read/write. Viewing other profiles requires an active browsing subscription and a published profile.
- Free quota defaults to 100 decimal MB and is admin-configurable. Storage purchases and browsing purchases remain independent.
- Prefer small reviewable commits and meaningful tests of authorization, state transitions, expiration, concurrency and rollback. Keep existing tests passing; don't weaken them to hide regressions.
- Do not commit databases, user uploads, backups, credentials or local archives. Do not rewrite Git history or merge to main automatically.
- No VPS or domain has been provisioned. Prepare deployment configuration and documentation locally; no purchase or live deployment is authorized by these instructions.
- Report the actual checks run and remaining limitations. Screens containing forms or a timer are not proof of a working feature.
