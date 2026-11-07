# Security and privacy

## Trust boundaries
Students can read their own tasks and devices, submit immutable attempts, reserve existing credits, and acknowledge their own device state. They cannot authorize devices, publish household policies, approve homework or grant credits. Parent access requires an active parent-child link; teacher access requires owned classroom/assignment resources. Platform admin is operational, without a blanket student-data bypass. Public signup never creates teachers or admins; an attended CLI provisions those roles.

A child invite is possession-based pairing, not legal guardian identity verification. Production needs an appropriate guardian verification and consent process. Consent events are versioned records and revocation removes that guardian's API access. Multiple guardians remain independent authorized links. A previously published household device policy is device-scoped and is not silently deleted when one guardian unlinks; remove the device before unlinking if restrictions should stop.

## Identity
Argon2id passwords. 15-minute HS256 JWTs with issuer, audience and explicit type. 30-day opaque refresh secrets are stored only as SHA-256 digests. Rotation consumes tokens once; reuse revokes the family. Access tokens remain valid until expiry after logout, unless the account is disabled. The web holds credentials only in memory and requires login after reload. Android encrypts credential JSON with an AES-GCM Keystore key. Keystore invalidation requires sign-in again. Android backups are disabled.

Redis rate limits are shared and fail closed when Redis is configured but down. Development without Redis uses a per-process limiter; it is not multiworker protection. Production configuration requires Redis and PostgreSQL. Never trust forwarded client identities unless a separately validated ingress has sanitized them. Current auth limit is peer-based; production ingress must apply an appropriate client-aware rate limit too.

## Transactions
Wallet writes serialize on the student's wallet row. Unique reward origin enforces assignment earning once, independently of repeated submission or approval events. Reservation is atomic with the spend ledger row. Failure refunds are unique by session. Approval revocation reclaims available minutes and records a debt for already consumed credit; reapproval does not mint another reward. Existing granted access expires at its original deadline; revocation is not an unbounded remote kill switch.

## Uploads
Authenticated and authorized downloads only, outside public roots, opaque storage keys, max 10 MiB, matching PDF/PNG/JPEG magic and content type, no inline execution, no-sniff responses. Magic bytes alone do not make files safe: antivirus/content-disarm scanning, decompression/image-bomb protection and quarantine are required before broad production use. Assignment attachments are not parsed. Books are parsed in a resource-limited child process; see the PDF-specific boundary below. Use encrypted persistent volumes/object storage and key management. Crash/transaction-orphan file cleanup is an operational task; a failure after file save is not reported as successful metadata storage.

## Device management
Only actual Android Device Owner can suspend or protect packages. Client compliance and acknowledgment are self reported; a compromised client can lie. No claim of hardware attestation or tamper-proof operation. After explicit guardian device authorization, the app may share at most 100 eligible launcher-app names/package IDs for guardian app selection; system/essential apps are filtered locally. Teachers cannot read this inventory. It contains no message contents or usage history and is cleared on acknowledged removal. Essential applications are protected locally regardless of household policy. A visible device register screen does not itself activate OS administration. Do not distribute a debug build as a production controller.

## AI
Keys are server-side. Prompts are single-turn and bounded; conversation text is not stored by the backend. Provider input and structured output are both moderated. Invalid, uncertain, subjective or disabled-provider results do not grant credit and require adult review. Submitted text may be sent to a configured provider: obtain appropriate consent and configure provider retention/region before enabling AI. Book-page OCR is an explicit owner action in a local worker; no hidden content collection.

## Deletion and retention
`POST /privacy/deletion-request` records a request for verified administrative processing. It does not falsely claim immediate erasure. A production operator must verify authority, deprovision devices, honor lawful retention holds, remove attachments and student data, revoke sessions, and record the minimal completion audit. Automated deletion execution and timed retention workers are outstanding release work. Do not enable production for children until retention and deletion procedures are implemented and reviewed.

## Deployment controls
Use HTTPS ingress, a strong generated secret, strict CORS origins, private PostgreSQL/Redis, managed secret injection, encrypted backups, restore tests, minimal telemetry without homework/credential content, and dependency updates. Local Compose is a development configuration. Images are tag-pinned; supply-chain digest pinning/SBOM and release signing remain deployment gates.


## PDF, reading and bounded AI
Book uploads are limited to 10 MiB/300 pages; all request bodies are capped at 12 MiB before multipart parsing. Encrypted and invalid PDFs fail. Processing has memory/CPU/deadline limits and receives no AI credentials. Poppler/Tesseract OCR accepts at most three pages; OCR output is unverified. This child process is not an OS security sandbox and still needs isolated production workers, scanning/quarantine and current OS/parser updates. Private source text is shared only in an assigned range; original files are owner-only downloads.

Source quotes must be present on cited pages. This check does not establish factual accuracy. Adult answer-key publication is mandatory. Version changes invalidate active tests; student responses cannot modify keys. Per-student wallet serialization and unique learner/lesson origin prevent duplicated reading rewards, including duplicate assignments. Current guardian links/current teacher roster are checked for result access; authorship alone does not preserve access after unlink/removal.

Autopilot is a strict academic output schema, not an agent with arbitrary tools. It cannot change roles, enroll devices, publish policies, spend minutes or grant itself privileges. The worker only creates 0–3 zero-reward practice tasks after rechecking opted-in guardian authority. Runs are unique per child/day with at most three failed attempts. Provider moderation/consent/retention qualification is still required before enabling it for children.


## v0.3 trust additions
Platform WebAuthn verifies user verification and cryptographic proof; the server does not infer which physical person or biometric modality the OS used. Registration/removal requires account password proof. OTPs are HMAC-hashed and atomically consumed with expiry and failure caps; browser verifiers never enter Telegram links. Staff password/state changes increment JWT epochs and revoke refresh credentials. Initial bootstrap requires server secrets and forced renewal; no known production credential is embedded.

Location requires a current linked-guardian authorization or authorization from the student's assigned classroom teacher, plus explicit student initiation for every session. Teacher authorization is limited to their current roster; teacher coordinate reads are audited. A visible foreground-service notification, bounded expiry and Stop remain central. Only latest coordinates are retained; old signal coordinates are hidden from API responses, and stop/revocation/expiry clear stored fields. Other teachers, school admins and platform admins have no coordinate scope. Offline cached last points cannot be recalled from a user who already viewed them; no anti-spoof/hardware attestation claim. Deployments must separately obtain guardian authorization where applicable law requires it.

Alarm object photos stay ephemeral and on device. Recognition is a voluntary educational aid, not identity proof, liveness verification or unbreakable alarm enforcement. Groq/DeepSeek/HF credentials remain distinct server-only values; provider choice is explicit. DeepSeek moderation uses Groq, so both receive relevant text when that adapter is selected and consent/provider retention must reflect this. No provider receives device policy authority or arbitrary executable tools.
