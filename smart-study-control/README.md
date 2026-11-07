# SMART STUDY CONTROL
Learn. Achieve. Unlock.

v0.4.2 adds the supplied brand PNG, a subtly animated Android launch splash, matching launcher icon, and a student-reading home illustration. The API is the only deployed service target; no public website is configured. Android versionCode/versionName are 7/0.4.2.

v0.4.1 adds a ready-to-review ten-question lesson for pages 1–5 of the supplied *Yoz yomg‘iri* PDF in the teacher book panel. It requires each lesson page to be marked as read before the test can start; that mark is explicitly a student report, not proof of reading. Every quiz question is linked to a source page and the server validates the page quote against the uploaded PDF text. v0.4.0 adds a premium dark Android UI, phone/login-first sign-in, student book-first dashboard, role-filtered staff navigation, and visible location sharing authorized for a student's assigned teacher or linked guardian. The student starts each bounded session; teacher reads are audited and limited to their class roster. v0.3.1 adds native Android assignment attachment upload for PDF/JPEG/PNG, bounded to 10 MiB with local file-signature validation and retry-safe partial uploads. v0.3.0 adds staff provisioning, forced initial password renewal, Telegram OTP/deep links, verified WebAuthn passkeys, notification delivery and photo alarms. See [book and AI guide](docs/BOOKS_AND_AI_UZ.md) and [access guide](docs/ACCESS_ALARM_LOCATION_UZ.md).

v0.2.0 added private PDF books, source-grounded visual lessons, adult-validated comprehension tests, reading progress, one-time learning rewards and guardian-controlled academic autopilot. Usage: [PDF and AI guide (Uzbek)](docs/BOOKS_AND_AI_UZ.md).

Production-oriented reference implementation, not a certified or production-ready MDM product. See IMPLEMENTATION_PROGRESS.md for exact delivery and verification status. The included APKs are historical v0.3.0 builds; v0.4.2 has not been compiled in this environment and requires Android SDK/Gradle. There is no public website in the deployment; the Android app uses the FastAPI service. The PDF is not bundled, and native Android book upload/authoring is still a release gap. Start with `BOSHLASH_UZ.md` for Uzbek instructions.

## Quick start
1. Run `python scripts/configure.py` to create a new `.env` with generated development secrets.
2. Fill the server-only provider/bot keys and bootstrap password in `.env`. With Docker installed: `docker compose --profile telegram up --build -d`.
3. Run `docker compose exec api python -m app.cli create-user --help` to create authorized teacher/admin accounts. Public registration only permits parent/student roles.
4. The app connects directly to FastAPI; there is no public web site. Authorized staff provisioning currently uses the documented backend CLI.
5. Android: open `android` in Android Studio with JDK 17, Android SDK 35, Build Tools 35.0.0. Run `./gradlew testDebugUnitTest assembleDebug`. Android emulator connects to `http://10.0.2.2:8000/api/v1/` in debug only. A release build requires an HTTPS API_URL Gradle property.
6. Register a student and parent, student creates a family invite, parent accepts it, parent assigns homework, student submits, parent approves, student enrolls a device, parent sets policy, student redeems a reward on that device.

## Local backend without Docker
`python -m venv .venv && .venv/bin/pip install -r backend/requirements.lock.txt`
`cd backend && DATABASE_URL=sqlite:///./development.db JWT_SECRET=<at-least-32-random-characters> ../.venv/bin/alembic upgrade head`
`DATABASE_URL=sqlite:///./development.db JWT_SECRET=<same-secret> ../.venv/bin/uvicorn app.main:app --reload`
SQLite is a developer/test fallback; PostgreSQL is the deployment target. Production explicitly rejects SQLite and requires Redis. See docs/DEPLOYMENT.md.

## Verification
`cd backend && ../.venv/bin/pytest -q`
`cd android && ./gradlew testDebugUnitTest assembleDebug`

## Product boundary
Essential communication never requires a reward. Only appropriately enrolled devices can suspend packages. A normal install stays voluntary. Teachers have academic access, never household device-policy access. AI uses the configured server-side provider; Groq includes a separate safety classifier, DeepSeek uses Groq moderation, and the generic compatible adapter needs a moderation endpoint. AI is unavailable if keys, moderation or credits fail; the app shows an explicit unavailable error. Subjective reviews always require an adult. All reward minutes are elapsed access windows, not a claim of measured foreground usage.

See docs/ARCHITECTURE.md, docs/DEVICE_OWNER_SETUP.md and docs/TESTING.md before deploying. Full requested screen/feature parity is tracked honestly, including outstanding work, in IMPLEMENTATION_PROGRESS.md.
