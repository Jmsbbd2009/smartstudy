# Verification record — v0.3.0, 2026-11-05

| Area | Executed | Result / boundary |
|---|---|---|
| Android | Gradle 8.11.1 / full JDK 17 / SDK 35, `testDebugUnitTest :domain:test assembleDebug assembleDebugAndroidTest` | Debug app and instrumentation APK compiled. 10 JVM tests (8 domain including photo decisions, 2 ViewModel). No emulator/device execution. |
| Backend | FastAPI integration, authorization, transactions, concurrency, PDF/OCR, staff provisioning/password epochs, Telegram OTP/replay/attempt caps, WebAuthn signatures/origin/UV, location consent/scope/expiry/stop, provider moderation and Telegram delivery | 58 passed; full suite in `test-results/backend.xml`. SQLite; PostgreSQL execution remains a CI gate. |
| Web | TypeScript/Vite production build + Vitest | 11 unit/DOM tests including redirect allowlist/popup fallback. 2 live HTTP workflow tests are separately enabled by the harness. |
| Real HTTP UI | `python admin-web/tests/run_e2e.py` using disposable migrated FastAPI/SQLite and rendered real React app | 13 reading checks + 7 staff/password/notification checks, no mocked HTTP responses. jsdom; native browser layout/WebAuthn hardware not exercised. |
| Live Groq | Public arithmetic, public three-page facts, anonymous practice planning, input/output safety passes | Tutor JSON, source-validated 3-concept/3-question lesson and 2-task practice plan passed using real provider requests. One lesson request initially returned 503, then passed on retry; no availability/semantic-accuracy guarantee. No student data sent. |
| Other external services | Telegram getMe; HF whoami/catalog/inference; DeepSeek models | Bot authentication passed. HF token accepted but inference 402; DeepSeek key rejected 401. Groq's initial generic urllib request was blocked, while the actual application HTTP client authenticated and completed the pipeline. No live Telegram OTP recipient was linked. |
| Migrations | Fresh upgrade/check/downgrade/upgrade/check and automated round trip | Static migrations include staff/login/passkey/Telegram/location additions. Alembic no-drift verification. |
| Audits | npm audit + pinned runtime pip-audit | Zero known advisories in recorded scans. Not an independent security review. |

## Reproduce

Create `.venv`, install `backend/requirements-dev.txt`, then run `cd backend && ../.venv/bin/pytest -q`. Run `npm ci && npm run build && npm test` in admin-web. For the live UI harness run `.venv/bin/python admin-web/tests/run_e2e.py` from project root. It creates isolated random test credentials, PDF and database/uploads, invokes real API endpoints, then deletes temporary state. It does not load the production `.env` or call configured AI/Telegram services. JSON evidence is `test-results/dom-live-e2e.json` and `access-live-e2e.json`.

For Android use the Gradle command above. The debug APK and instrumentation APK are included in artifacts; `BUILD_ARTIFACTS.md` contains hashes. For device tests, use a disposable emulator/device and `adb shell am instrument -w uz.smartstudy.control.test/androidx.test.runner.AndroidJUnitRunner`. Device Owner tests require separate authorized provisioning. Instrumentation sources compiled here but were not executed.

The native-browser script is retained under `admin-web/tests/reading-e2e.mjs`; it was not re-executed in v0.3. Prior Chromium startup hit socket EPERM in this environment. No screenshots or browser visual-QA success are claimed. Passkey tests construct genuine signed P-256 WebAuthn credentials/assertions to exercise server cryptographic verification; they do not claim a face sensor was used.

## Critical outcomes

- Repeated homework approval, concurrent redemption and concurrent reading completion cannot mint or spend duplicate credit. Duplicate reading-plan assignment cannot re-award the same learner/lesson.
- Published sources and lesson versions serialize edits/publication; old tests fail after edits or expiry. Page marking never grants reward or claims full-book comprehension.
- Teacher/guardian history access is lost after roster removal/unlink. Teachers and operational admins cannot read location or personal app inventory.
- Staff temporary credentials cannot access protected management. Password changes invalidate prior JWT epochs and refresh tokens. Super admin provisions staff; school admin is school-scoped.
- OTPs are HMAC-hashed, expire, have a persisted five-attempt cap, are bound to linked Telegram identity and are one-time consumed. Forwarded links and replayed webhook updates do not authenticate another identity.
- Passkey signatures, origin, RP, UV and challenge/replay are checked. Invalid signature inputs never create sessions.
- Location requires both current guardian consent and explicit student start. Stop/expiry/revocation clears the latest coordinate; stale points are hidden. Multiple current guardians are supported, staff access is denied.
- Only opted-in active staff receive new Telegram copies; successful delivery deduplicates, failure attempts cap at three. Ambiguous external-network delivery can still duplicate a message.
- Photo tasks reject unrelated/low-confidence labels. Real image inference, sound, camera permissions, Doze, coarse-only GPS, foreground stop behavior, OEM constraints and Device Owner OS calls remain physical-device tests.

## Known verification boundaries

Docker image/runtime and remote CI were not executed. The new ML Kit model is bundled in the APK but prediction quality on real household photos was not tested. Telegram delivery to a real person was not exercised. HTTPS origin configuration, platform face/fingerprint/PIN prompts and passkey enrollment require a compatible real browser/device. Live AI probes used only small public samples; adult answer-key review remains mandatory. Broader release gaps remain in IMPLEMENTATION_PROGRESS.md.
