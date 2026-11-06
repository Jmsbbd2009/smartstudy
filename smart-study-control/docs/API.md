# API contract

Canonical machine-readable contract: `openapi.json` in this directory; runtime `/openapi.json` and `/docs`. Version prefix `/api/v1`. JSON request bodies use Pydantic with unknown properties rejected. Core resource response models are typed. IDs are UUID strings. Datetimes are UTC unless a policy explicitly carries an IANA schedule zone. Entity timestamps are serialized explicitly as UTC with a `Z` suffix.

Use `Authorization: Bearer <access_token>`. Submit and redeem operations require `Idempotency-Key` (8–100 characters); retries must preserve body and key. Assignment earning is independently unique by origin. List assignments uses `limit_count` (1–100) and `offset` (>=0). Other narrow resource lists are bounded or scoped; fully uniform pagination is outstanding.

Errors: `{"error":{"code":403,"message":"..."}}`. Validation adds safe field locations/messages and never echoes submitted secrets. 401 authentication, 403 resource/role scope, 409 conflicts/budgets/stale versions, 413 upload size, 415 media type, 422 validation, 429 rate limit, 503 dependency/AI unavailability.

## Main flows
- Register STUDENT/PARENT → login/refresh/logout. Staff provisioned by CLI.
- Student `POST /families/invite` → guardian `POST /families/link-child` with code and explicit consent. The invite is single-use for 15 minutes.
- Teacher creates classroom → generates 24-hour classroom invite → student joins → teacher lists roster. Classroom invite is deliberately reusable until expiry; it never grants device control.
- Parent creates household assignment, or teacher creates classroom assignment with `reward_minutes=0`. Teacher-configured household screen time is rejected. A guardian may configure a task reward before it is credited using `PUT /assignments/{id}/reward-policy`; a credited origin cannot be edited.
- Owners may create a private DRAFT and publish it. A student may mark an assigned task IN_PROGRESS.
- Student submits immutable work → review/approve by owner or guardian → transactionally credit wallet once. Review history preserves feedback and AI model metadata.
- Student registers logical device → guardian authorizes management → guardian publishes policy with expected_version → student sync reports actual capability and applies the document.
- Student reserves reward → device applies allowance → ack active or failed/refunded → elapsed local expiry restores restrictions. One active/pending session per student, across devices.
- Parent requests deprovision → device restores tracked restrictions and acks cleanup → retired server record. This does not implicitly remove Device Owner.
- Private file upload and authorized download; quizzes conceal answer keys until completed; AI never directly approves work.

Refer to OpenAPI for every request/response field and path rather than duplicating a second drifting contract.


## v0.2 reading and automation

| Capability | Endpoints | Authorization |
|---|---|---|
| PDF upload/list/metadata | `POST/GET /books`, `GET /books/{id}` | Upload: parent/teacher; list: owned or currently assigned |
| Source | `GET /books/{id}/pages/{number}`, `GET /books/{id}/file` | Text restricted to assigned range; original file owner only |
| OCR | `POST /books/{id}/ocr` | Owner, explicit server OCR enablement, 1–3 pages |
| Lesson authoring | `GET/POST /books/{id}/lessons`, `POST /books/{id}/generate-lesson` | Owner writes; students see only assigned published lessons |
| Lesson revision/publication | `GET/PUT /reading/lessons/{id}`, `POST /reading/lessons/{id}/publish` | Owner, expected version, adult answer-key validation |
| Assignment | `POST /books/{id}/plans`, `GET /reading/plans`, `GET /reading/plans/{id}` | Current guardian or owned class roster; student own only |
| Reward policy | `PUT /reading/plans/{id}/reward-policy` | Linked guardian only |
| Self report | `POST /reading/plans/{id}/progress` | Assigned student; never credits wallet |
| Assessment | `POST /reading/plans/{p}/lessons/{l}/attempts`, `GET /reading/attempts/{id}`, `POST /reading/attempts/{id}/finish` | Student starts/finishes; Idempotency-Key for start; adults see completed results |
| History/manual credit | `GET /reading/plans/{id}/attempts`, `POST /reading/attempts/{id}/approve-reward` | Current scoped readers; credit guardian only |
| Bounded AI | `GET/PUT /automation/children/{id}`, `POST /automation/children/{id}/run`, `GET /automation/children/{id}/runs` | Linked guardian only; opt-in, bounded academic tasks |

All paths above are relative to `/api/v1`. OpenAPI contains validated input schemas. Reading attempt start returns only shuffled prompts/options; completion adds explanations. Auto reward requires guardian policy and enabled automation, limits apply even to manual credit. Missing AI or OCR configuration returns 503; no synthetic success. Request bodies are limited to 12 MiB before parsing, individual PDFs to 10 MiB. See BOOKS_AND_AI_UZ.md for the full operation and source/reward semantics.


## v0.3 access, staff, notifications and location

| Paths (relative to /api/v1) | Contract and scope |
|---|---|
| `POST /auth/login` | Backward-compatible `email` field accepts email or whitespace-normalized staff login; token user includes login and must_change_password. |
| `POST /auth/password` | Current password + new 12+ character password; renews session and revokes old epochs/refresh credentials. |
| `GET/POST /staff`, `GET /staff/schools`, `PUT /staff/{id}/state` | Super admin creates/enables staff; school admin reads its own school's staff. Public registration cannot grant staff roles. |
| `POST /staff/announcements` | Super/school admin, explicit authorized staff recipient IDs; creates real private notifications. |
| `POST /auth/telegram/{link,login}/{start,finish}`, `POST /auth/telegram/status` | Separate random state and browser-held verifier, 5-minute expiry; linking also requires current authenticated staff/password. Login finish consumes six-digit OTP once. |
| `POST /telegram/webhook` | Telegram secret header, private sender identity, update deduplication. Polling worker is an alternative. |
| `GET /auth/telegram/me`, `PUT /auth/telegram/notifications` | Current staff's linked status and explicit optional Telegram message consent. |
| `POST /auth/passkeys/{register,login}/{options,verify}`, `GET /auth/passkeys`, `DELETE /auth/passkeys/{id}` | Platform WebAuthn, origin/RP/UV/signature/counter checks; password proof for enrollment/removal. No face templates. |
| `GET /operations/integrations`, `POST /operations/integrations/check` | Super admin only; redacted configuration and live key/model-list connectivity diagnostics, never actual keys. |
| `GET/PUT /location/children/{id}/consent` | Student reads own, current linked guardian reads/updates; guardian consent record and bounded duration. |
| `POST /location/shares`, `POST /location/shares/{id}/{point,stop}` | Student only; explicit sharing consent, active guardian authorization, latest finite coordinate, expiry and stop. |
| `GET /location/children/{id}/latest` | Student/current guardian only; hides coordinates for stale/inactive shares. No staff bypass. |

Passwords that must be renewed can only reach password/logout/me until renewal. Input schemas are exported to OpenAPI. See ACCESS_ALARM_LOCATION_UZ.md for worker setup, deep links, provider boundaries and platform limitations.
