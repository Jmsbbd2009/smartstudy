# Implementation progress

Updated: 2026-11-07, v0.4.2 GitHub release and Render deployment.

## v0.4.2 — Published Android preview

Completed:
- Supplied PNG brand asset, adaptive launcher icon, animated launch splash, login/dashboard branding and compressed student-reading illustration, including localized accessibility descriptions.
- Android versionCode/versionName 7/0.4.2; parent actions and student family/device-enrollment navigation restored. Preserved the previously fixed assignment repository references and corrected the Telegram help resource name.
- Bounded network timeouts now tolerate the free Render instance waking from idle. The built APK targets the existing HTTPS API, not an emulator address.
- Uploaded the updated source to `Jmsbbd2009/smartstudy`. The root Actions workflow tests the API and Android, then publishes immutable commit-specific preview releases. No public website build/deploy is configured; retained React source is not deployed.
- Render service `studycontrol-api` deployed source `b13b376d1b37322d1b6c969982b1d7b3f6cd85fa`; dashboard showed Live and `/health/ready` returned `{"status":"ready"}`. Existing super admin remained unchanged.

Verification:
- [GitHub Actions run](https://github.com/Jmsbbd2009/smartstudy/actions/runs/42365397958): Ruff passed; PostgreSQL Alembic upgrade/check passed with no schema drift; **62 backend tests passed**.
- Android `:domain:test testDebugUnitTest assembleDebug assembleDebugAndroidTest` completed successfully with JDK 17, SDK 35 and Gradle 8.11.1. Instrumentation APKs compiled; no emulator or physical-device test was run.
- First CI run exposed an unresolved Android string reference and two outdated test expectations; these were corrected and the entire CI rerun passed.
- [Published preview](https://github.com/Jmsbbd2009/smartstudy/releases/tag/v0.4.2-preview-b13b376), [APK](https://github.com/Jmsbbd2009/smartstudy/releases/download/v0.4.2-preview-b13b376/SmartStudy-0.4.2-test.apk), 59,209,011 bytes. SHA-256: `1d74db38335e4cbc9725206372b5f61c547de3b9de61c28364d73de1a57e9cb1`.

Known release gaps:
- APK is debug-signed, not a stable production-signing release. Installing over a previous separately signed APK may be rejected. Preserve existing data and obtain the original signing key before an in-place production update.
- Render currently has database/session variables but no AI provider key or Telegram bot token configured. AI and Telegram OTP remain unavailable until those server-only secrets and the Telegram delivery mode are securely configured. No real messages were sent in this deployment.
- Native Android PDF upload/lesson authoring and full staff administration remain incomplete; retained React code contains those authoring flows but no public website is deployed.
- Free Render upload storage is temporary; durable private object storage remains required. Real-device Device Owner, alarm/camera/location behavior, accessibility and recovery qualification remain outstanding. No claim of a defect-free or production-qualified product.

Updated: 2026-11-07, v0.4.1 book-specific quiz and page-read gate.

## v0.4.1 — Uploaded PDF based lesson

Completed:
- Reviewed the user-provided 87-page *Yoz yomg‘iri* PDF. Added an adult-editable, 10-question multiple-choice lesson draft for pages 1–5, with source page references, answer explanations, a concept card and a non-graded evidence prompt. The PDF itself is not bundled into the source archive; the teacher/superadmin uploads their copy through the existing secure book panel.
- Added a button to load the prepared lesson only when pages 1–5 are selected. The backend checks each source quote against the uploaded PDF page text; the lesson remains a draft until an adult validates the key and publishes it.
- Quiz start now requires the student to mark every page in the lesson range as read. This is explicitly recorded as student-reported progress, not proof. The randomized quiz assesses cited pages and summarizes which pages were checked by correct answers.
- Enabled SUPER_ADMIN to upload and own curriculum books; classroom assignment scope remains the teacher workflow.
- Added web fixture and backend gate/superadmin-upload integration tests.
- Android versionCode/versionName: 6/0.4.1. Admin web version: 0.4.1.

Verification in this workspace:
- PDF has 87 pages. First and fifth pages were visually inspected; all ten source snippets were checked against extracted text from their cited PDF pages.
- Backend `compileall` and Android string XML checks passed (static checks only).
- Automated pytest/web test suites remain unrun: this workspace lacks a runnable restored pytest environment and admin-web `node_modules`; Gradle 8.11.1 download is blocked and Android SDK is not present. No APK was built, and the attached PDF has not been uploaded to a deployed database because no API server credentials/endpoint are configured here.

Extra ideas included: chronology reconstruction, text-evidence reflection without grading, page-specific review explanations and adaptive practice for missed pages. These are suggestions in the book guide; only the evidence prompt is in this version's UI.

Updated: 2026-11-06, v0.4.0 source update based on the requested dark premium, phone/Telegram-first and book-first direction.

## v0.4.0 user-directed changes

Completed:
- Android Material 3 uses a consistent deep-navy dark palette with larger typography and rounded surfaces. Login prioritizes phone/login + Telegram OTP, retains password fallback/first student registration, hides parent signup, and checks a 12-character minimum before registration.
- Student dashboard opens on the book library, shows current assignment count and reward balance, and groups other study actions into larger tap targets. Staff dashboard actions are role-filtered. Admin web login presents Telegram before password fallback; teacher creation defaults to TEACHER. Passkey copy now correctly says device verification may use biometrics or PIN rather than claiming server-side face identification.
- Teacher location authorization and latest-location access are scoped to the teacher's current classroom roster; coordinate reads create audit events. Student starts each share from the visible Android foreground service with session consent, duration, notification and Stop action. Existing guardian access remains. Other staff and platform admins remain denied.
- Added a backend integration test for teacher roster scoping, per-session student initiation, unauthorized teacher/superadmin denial and revocation; updated Uzbek/English/Russian Android location copy and API/security setup docs.
- Android versionCode/versionName are 5/0.4.0; admin-web package version is 0.4.0.

Verification in this workspace:
- `python3 -m compileall -q backend/app backend/tests` passed.
- Android `strings.xml` resources parsed as XML and have no duplicate string names.
- Targeted pytest could not start: the restored virtualenv points to a missing Python executable and the active runtime has no pytest module. Gradle wrapper could not download pinned Gradle 8.11.1 (`Network is unreachable`); no Android SDK is available. Web `node_modules` is absent. Therefore the new backend test, web typecheck/build, Android compile, APK and device behavior are not verified in this turn. Historical test results below apply only to the named earlier source versions.

Known limitations: location sharing is bounded, student initiated and session scoped, but organizations must separately obtain guardian authorization where applicable law requires it. Standard Android mode cannot enforce restrictions across other apps; managed Device Owner enrollment is still required. The unlock flow does not yet automatically equate book reading with unsuspending packages, and teacher policy still needs physical Device Owner end-to-end qualification. No claim of a completed production deployment or new APK.

Updated: 2026-11-05, v0.3.1 source update.

Baseline v0.3.0 verification: **58 backend tests, 11 web unit/DOM tests, 10 Kotlin JVM tests, 2 real HTTP UI tests with 20 workflow checks**. Those results apply to v0.3.0. The v0.3.1 Android attachment upload and 2 new JVM tests have **not** been built or executed: this workspace lacks Gradle 8.11.1 and Android SDK 35, and network access blocked downloading them. The included APKs are clearly labeled historical v0.3.0. Delivery remains a working core with explicit release gaps, not completion of every feature/screen in the original specification.

| Phase | Implemented | Verification | Remaining / limitations |
|---|---|---|---|
| 1 Foundation | Monorepo, Gradle wrapper and modules, Compose/Hilt/navigation/theme, FastAPI auth, SQLAlchemy/Alembic, Docker Compose, React dashboard, CI definitions | Backend tests, web typecheck/build/unit tests; Android debug + instrumentation APK builds passed; 8 JVM tests passed | Docker runtime is unavailable here; CI has not been run on GitHub; release signing/deployment not performed |
| 2 Education | Student/parent signup, invite/consent, multiple guardian links, teacher classrooms, homework/submission history, review, objective quiz engine, private file API, Room cache/outbox; PDF reading plans and native reading/test flow; v0.3.1 parent assignment creation selects and uploads up to 5 PDF/JPEG/PNG files with a 10 MiB cap, local signature check and retry-safe partial sends | v0.3.0 API upload scope/type/size tests passed; v0.3.1 has 2 new JVM validation tests written but not run because Android toolchain is unavailable | Student photo/file submissions, downloaded offline quiz attempts, complete school-admin curriculum/user management, quiz short answers and AI draft generation are not yet implemented |
| 3 Device management | Owner detection, receiver, limited package discovery, suspension/readback, tracked uninstall protection and actual readback in Android/parent panel, persistent policies, schedule evaluator, versioned sync, guardian deprovision request and cleanup acknowledgment | Pure policy tests and Android build; server policy/version/scope tests | Real Device Owner provisioning and physical OEM qualification still required. Production QR/zero-touch fleet enrollment is not implemented. Device reports are untrusted self reports; no hardware attestation. Formal owner relinquishment is attended administration |
| 4 Rewards | Atomic ledger, origin uniqueness, credit/debit/revocation debt, budgets, pending reservations, ack/failure refund, bounded elapsed-time local leases, offline relock, duplicate spend protection; reading credits unique per learner/lesson, including repeated plan assignment | Concurrency/refund/revocation API tests pass | Spending requires network. Reward balance TTL and configurable streak/quiz/focus credit policies not implemented. Guardian reward mapping for teacher assignments is implemented through the API; full dashboard controls for that mapping remain. Actual foreground app consumption is not measured; budgets count reserved elapsed windows. Lost ack can require guardian support |
| 5 Productivity | Recurring offline Android alarms, exact-permission fallback, reboot/timezone restore, ringtone/vibration, dismiss/snooze, focus timer, focus API, household sleep windows, report aggregates, in-app notifications | Clock/policy unit tests; focus/report API tests | Physical alarm delivery not yet tested; custom sounds, volume ramp, optional challenges, morning checklist, scheduled report delivery and FCM are not implemented. Focus UI is local-first; failed online focus registration is shown as an error and does not earn reward |
| 6 AI | Server-side provider protocol, OpenAI-compatible JSON schema adapter, input/output moderation, rate limits, text review metadata, deterministic answer-key checks, human review, Uzbek tutor; PDF text extraction, opt-in local OCR, source-cited concept maps/cards, published answer keys, comprehension assessments and bounded guardian academic autopilot | Disabled-provider and deterministic grading tests pass | Groq is now configured and live public-sample tutor, source-grounded lesson and practice-plan probes passed. HF inference needs credits (402); the supplied DeepSeek key was rejected (401). General homework photograph OCR, personalized multi-session tutor plans, adaptive recommendations and provider-specific adapters beyond the compatible transport remain. Book OCR is local and marked unverified; adult answer-key validation is mandatory |
| 7 Hardening | Resource scopes, Argon2, JWT/refresh rotation, pre-parser request limits, upload limits/magic bytes, current reading-roster/guardian checks, audit, secret generation, nonroot container config, accessible controls, reduced CSS motion | Tests and dependency audits recorded in docs/TESTING.md | Independent security review, physical-device recovery exercise, accessibility audit, backup/restore exercise, legally reviewed consent/retention rules, complete multilingual copy, full 30/16/15 requested screen parity remain release gates |

## Files
- `android/{app,domain,data,devicepolicy,sync,core/designsystem}`: actual source modules. Features share the app navigation module until API flows stabilize; no empty feature modules are presented as implementations.
- `backend/app`: runtime API, models, contracts, AI provider, auth/resource scopes and reward transactions.
- `backend/migrations/versions`: initial static schema, role seed and additive reading/autopilot migration.
- `backend/tests`: real HTTP integration, security, race, quiz, policy and migration tests.
- `admin-web/src`: authenticated student/parent/teacher workflows, PDF lesson editor, concept maps, test/history, bounded AI controls and operations view.
- `infrastructure`: local Compose deployment and nonroot images.
- `docs`: ADRs, setup, API, schema, security, sync, test and release instructions.

## v0.2 components and files

- `backend/app/{api,services}/{reading,automation/autopilot}.py`: private PDF upload, page-range scopes, source-grounded lesson CRUD/publication, shuffled assessment snapshots, independent progress evidence, unique rewards and guardian opt-in automation.
- `backend/app/schemas/reading.py`, `models/entities.py`, `migrations/versions/0265d9853bd2_reading_and_bounded_autopilot.py`: validated reading/AI schemas and 8 new tables (50 total).
- `backend/app/workers/{pdf_extract,autopilot}.py`, `security/request_size.py`: bounded real parsing/OCR, scheduled practice and 12 MiB pre-parser request cap. Provider output token bound adapts to the declared schema.
- `admin-web/src/features/reading/{BooksPage,AutomationPage}.tsx`: working authoring/publication/assignment/test/history and opt-in controls. Binary uploads refresh expired credentials; critical request retries preserve their idempotency key.
- `android/app/src/main/kotlin/uz/smartstudy/control/BookLearningScreen.kt`: source reader, flip cards, self reports, real assessment and reward result. `android/data` caches opened reading documents by account and migrates Room 1→2 without destroying outbox rows.
- Android device readback and sync now report actual `isUninstallBlocked`; the parent panel shows the reported protection state without pretending standard mode is protected.
- Tests: `backend/tests/test_{reading,autopilot}.py`, request-size cases, web credential-retry tests, live HTTP UI harness, Android `ReadingMigrationTest.kt` (compiled only).
- `docs/BOOKS_AND_AI_UZ.md`, ADR 008, refreshed generated schema/OpenAPI, CI OCR/live-HTTP steps, container OCR dependencies and autopilot service. No remote CI or Docker execution claimed.

## v0.2 test record (historical)

Backend: **40 passed** on SQLite, including real PDF extraction, actual Poppler/Tesseract OCR, parallel finish credit, duplicate plan reward prevention, source/version expiry, reading privacy after guardian/roster revocation, automation bounds/idempotency/failure handling, and the previous auth/reward/device/API suite. Ruff passed. Fresh Alembic upgrade/check/downgrade/upgrade/check passed with no schema drift. PostgreSQL DDL exported; actual PostgreSQL tests remain a CI gate.

Web: **TypeScript + Vite production build passed; 8 unit/DOM tests passed**. A separate rendered jsdom UI test completed **13 checks against a real temporary FastAPI/SQLite server without mocked responses**: parent login/consent, PDF upload/source, unavailable AI, manual source-grounded lesson/SVG, adult publication, assignment, student assessment, real 15-minute wallet credit, parent history and teacher isolation. Chromium launch failed with socket EPERM in this environment; no native-browser execution or visual screenshot QA claimed. Browser scenario remains reproducible outside this environment.

Android: **clean BUILD SUCCESSFUL**, **8 JVM tests passed** (6 domain + 2 ViewModel); versionCode 2/versionName 0.2.0. Debug and instrumentation APK signatures verified. The first incremental rebuild encountered duplicate DEX intermediates; clean rebuild resolved it. Instrumentation tests including Room migration compiled but were not executed without an emulator/device. New APKs are in artifacts.

Dependency scans: npm audit and pinned runtime pip-audit each reported **0 known advisories**. Live AI credentials were not supplied; adapter/schema/moderation and unavailable states were tested, no real provider output quality claim. No Docker, production deployment, live Device Owner enforcement or alarm delivery test was possible here.

Machine-readable API: **76 paths, 72 schemas**. Database: **50 ORM tables**. See docs/TESTING.md, docs/BUILD_ARTIFACTS.md and docs/test-results/SUMMARY.json.

## Remaining release work

All prior phase-table gaps still apply. Book visualizations are source-text concept maps/cards, not generated video or page-layout preservation. Full-book comprehension is not inferred from dwell time. Quiz/reward writes remain online. AI never publishes answer keys, controls household/device policies or executes arbitrary commands. Parent reward mapping for teacher reading plans is API-only. Web extended copy is Uzbek; full English/Russian web translation is incomplete. Production requires isolated PDF workers/quarantine, verified guardian onboarding and retention/deletion execution, live provider validation, PostgreSQL contention/backup exercises, real-browser/accessibility QA, and physical managed-device/OEM recovery qualification.


## v0.3 access, safety and device workflows

Completed:
- Additive migration `763759b3cc97_staff_identity_telegram_passkeys_`: login alias, forced renewal and auth epochs; staff-school profiles; expiring auth challenges; Telegram identity/update/delivery records; passkey public credentials; bounded location consent and latest share (50 ORM tables total).
- `backend/app/{api/access.py,services/challenges.py,integrations/telegram.py,workers/telegram_bot.py,bootstrap.py}`: super-admin-only staff creation, school scopes, password/token revocation, direct bot deep links, current-user Telegram linking, HMAC OTP, verified webhook/private chat processing, bounded delivery and idempotent bootstrap. Passwords/keys remain private server configuration; no supplied secret is shipped.
- `backend/app/api/location.py`: explicit two-party consent, current guardian resource scope, student-only start/write/stop, max 240 minutes, 90-second freshness, latest-point-only data, revocation and cleanup. Teachers/school/platform admins have no coordinate access.
- `backend/app/ai/{hosted,huggingface}.py`: Groq/HF/DeepSeek adapters, strict/local JSON validation, separate input/output moderation, explicit configured provider and no hidden fallback. Real Groq tutor and book lesson tested; live ordinary practice planning tested with two tasks. DeepSeek remains disabled by a rejected key until a valid key is configured; HF needs credit.
- `admin-web/src/features/access`: working staff provisioning/state, forced renewal, platform passkeys, Telegram direct redirect/OTP/linking, announcements, real notification/read states, guardian location consent/latest signal and provider diagnostics.
- Android: optional available-object photo alarm with bundled ML Kit, fresh camera capture, confidence gate, accessible dismissal, bounded sound and local outcome history. Visible, explicitly started location foreground service with coarse/precise support, persistent Stop action and account-partitioned offline stop queue. Native Telegram sign-in/linking, password renewal, role-appropriate navigation, web passkey panel link and permission-gated OS message notifications.
- v0.3.1 Android source: assignment creation now invokes the system document picker and posts accepted PDF/JPEG/PNG content using authenticated multipart HTTP. It caps at five files and 10 MiB per file, checks actual file signatures locally (server independently revalidates), displays attached filenames, tracks successful files to avoid duplicate retries, and moves the historical APKs under an explicitly versioned v0.3.0 directory. Two JVM validation tests were added. Current SDK/wrapper download is blocked in this environment, so this delta is not yet compiled.
- Docker adds an explicit `telegram` profile; startup optionally bootstraps the initial super admin. Guides and API/schema exports updated. Telegram polling will not delete another webhook.

Executed:
- Backend full suite and raw XML updated for v0.3; new real signed WebAuthn, OTP, role/epoch, location, provider and opt-in delivery tests included.
- Web production build + 11 unit/DOM tests passed. Real HTTP jsdom workflows passed: 13 reading checks and 7 staff/password/notification checks. Direct Telegram redirect allowlist/pop-up fallback tested with isolated test doubles, no external messages.
- Android v0.3.0 debug and instrumentation APK compiled; 10 JVM tests passed. Clean rebuild resolved stale Kotlin intermediates; subsequent v0.3.0 source changes rebuilt successfully. Real camera/GPS/biometric/Device Owner/alarm delivery tests remain unexecuted. v0.3.1 attachment changes and their 2 new tests remain uncompiled/unexecuted here because Gradle/SDK are missing and downloading is network-blocked.
- Bot authentication passed. Real Groq structured tutor, separate safety passes, source-grounded 3-concept/3-question lesson and 2-task plan passed on public data. A transient lesson failure was shown as unavailable; retry passed. HF token accepted but inference returned 402; DeepSeek returned 401. No real Telegram recipient received OTP in this task.

Remaining:
- Deploy a durable HTTPS API/database/web panel; configure fresh server-only secrets and actual passkey RP/origin; link real staff Telegram identities and qualify live delivery.
- On real hardware qualify photo-label accuracy, camera intents, exact/inexact alarm delivery, foreground location/stop while offline and after process death, notification permission denial, Device Owner suspension/uninstall/recovery and Room instrumentation.
- Passkey face/fingerprint/PIN authentication is in the web panel. Native staff login supports Telegram OTP; no native camera-face identity matcher is claimed.
- Location is opt-in and bounded, not 24/7 hidden tracking or guaranteed anti-spoof positioning. Reading credit still requires the existing separate access reservation/OS acknowledgment; credit alone does not automatically unlock arbitrary apps.
- Student photo/file submissions, full 30/16/15 original-screen parity, complete school curriculum administration, FCM, legal guardian verification, automatic retention/deletion execution, independent security/accessibility review, release signing and PostgreSQL deployment qualification remain release gates. Rebuild v0.3.1 with Android SDK 35 and Gradle 8.11.1 to confirm the current Android delta.

Current machine-readable evidence is docs/test-results/SUMMARY.json. Earlier phase records above describe the v0.2 baseline and must be read alongside this v0.3 record; no old successful build is substituted for the new APK.
