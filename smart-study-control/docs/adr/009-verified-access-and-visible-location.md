# ADR 009 — Verified staff access and visible device features
Status: accepted, 2026-11-05.

Staff accounts are created through super-admin-only APIs, with school-scoped staff views and forced temporary-password renewal. Epoch-bound JWTs and refresh revocation invalidate old credentials after password/state changes. Telegram identity linking requires an existing staff session and password proof; a separate browser-held verifier prevents a forwarded bot start link from authenticating its recipient. OTP hashes are HMAC-based, expire in five minutes, have a persisted five-attempt cap and are atomically consumed. Webhooks require a secret header and updates are deduplicated. Polling never deletes an existing webhook.

Face sign-in uses platform WebAuthn user verification rather than stored camera faces. The server verifies RP/origin/challenge/UV/signature/counter and credential ownership. Native staff OTP is implemented; passkey administration/sign-in uses the web panel. Modality is controlled by the OS and is never misrepresented as a guaranteed face match.

Photo alarm tasks run on device with a bundled image labeler and an explicit available-object set. Camera results are ephemeral, confidence-gated and not identity/anti-tamper evidence. Accessible dismissal and a bounded sound duration remain essential.

Location is student-initiated, guardian-approved and time bounded. The OS foreground service and stop notification stay visible. Only current linked guardians and the student can view the latest fresh point; no teacher or operational-admin bypass. Offline stop halts local GPS immediately and queues a user-partitioned server stop. No boot auto-start, background-location permission, route history or covert collection.

Provider selection is explicit. Groq strict structured output and a separate safety model form the working primary adapter. DeepSeek JSON mode still undergoes full local validation and Groq moderation. Keys stay on their respective provider endpoints. Failed availability/moderation/schema validation never becomes synthetic success, grades or device authority.
