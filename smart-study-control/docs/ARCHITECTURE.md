# Architecture

FastAPI modular monolith → SQLAlchemy unit of work → PostgreSQL. Redis provides shared rate limits. Private upload volume is outside the web root. Stateless access JWTs, database-backed refresh token families, resource-level authorization and audit records protect mutations. OpenAPI is generated from the running application at `/openapi.json` and exported to docs/openapi.json.

Android: Compose → StateFlow ViewModel → repositories → Room cache/outbox; Retrofit is the remote adapter. Hilt composes dependencies. DataStore persists local preferences. Keystore encrypts refresh/access credentials. WorkManager retries queued immutable writes. The deterministic pure-Kotlin policy engine is independent of DevicePolicyManager. The DPC adapter checks owner capability and applies only selected eligible packages; essential packages win over all other rules.

Admin web: React + TypeScript + Vite, TanStack Query for server state, React Hook Form + Zod for forms, Tailwind and accessible primitive components. Parent and teacher views use real API resources and display authorization errors.

## Boundaries
identity/users/families/schools/classrooms/devices/policies/assignments/submissions/ai/quizzes/rewards/alarms/focus/reports/notifications/audit are one deployable, with shared transactions for approval + ledger credit and redemption + reservation. Do not split services until scale or isolation needs justify it. AI provider code lives behind an independent protocol.

## Core invariants
- Parent-child links require a child-generated short-lived single-use code and recorded guardian consent. School enrollment alone grants no device control.
- Teachers create assignments only for their own classroom members; parents only for linked children. Reviews require assignment owner or linked parent.
- One earning event per assignment/student, even after multiple submissions or revoke/reapprove. Immutable ledger, conditional wallet updates, bounded budgets, and unique idempotency keys.
- A pending unlock is charged once; a device acknowledges application before activation. Failures refund once. Leases are bounded by server duration, client monotonic time, policy priority and package result. Failed/missed acknowledgement is recoverable.
- Policies have monotonically increasing versions. Students cannot publish policies. Stale writes return 409.
- No invented offline reward credit. Previously downloaded tasks may be submitted offline; spending requires a live server reservation. Active acknowledged leases survive network loss on the same boot and expire locally. Reboot invalidates monotonic leases until verified again.
- Unsupported hardware is a visible reduced-capability mode.

## Implementation order
1. Runtime, secrets, migrations, auth, CI, API contract.
2. Consent, membership, assignments, immutable submissions, authorized review, objective quizzes.
3. Policy precedence and DPC capability guard, policy sync, persistence, recovery.
4. Ledger, budgets, reservation/ack/refund, version reconciliation.
5. Alarm scheduling, focus, sleep windows, reports.
6. Provider-gated AI, structured reviews, privacy controls.
7. Tests, operational checks, device/emulator qualification and release signing.


## Reading extension
Private PDFs add source pages, versioned source-cited lesson content, reading plans, progress and server-private assessment snapshots. Source mutations and lesson publication serialize on the book row. Per-learner wallet locks serialize unique lesson rewards. Current guardian/classroom membership gates academic history. PDF/OCR child processes have explicit resource limits; production process isolation is a separate release gate.

The guardian opt-in worker uses the same provider interface to propose bounded zero-reward academic practice. The provider has no arbitrary command/device tool surface. A run is unique per child/day, task creation is atomic and authority is checked again after provider latency. Room v2 caches opened reading content without changing submission-outbox ownership.
