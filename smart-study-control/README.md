# SMART STUDY CONTROL
Learn. Achieve. Unlock.

v0.3.1 adds native Android assignment attachment upload for PDF/JPEG/PNG, bounded to 10 MiB with local file-signature validation and retry-safe partial uploads. v0.3.0 adds staff provisioning, forced initial password renewal, Telegram OTP/deep links, verified WebAuthn passkeys, notification delivery, photo alarms and visible bounded family location sharing. See [new Uzbek guide](docs/ACCESS_ALARM_LOCATION_UZ.md).

v0.2.0 added private PDF books, source-grounded visual lessons, adult-validated comprehension tests, reading progress, one-time learning rewards and guardian-controlled academic autopilot. Usage: [PDF and AI guide (Uzbek)](docs/BOOKS_AND_AI_UZ.md).

Production-oriented reference implementation, not a certified or production-ready MDM product. See IMPLEMENTATION_PROGRESS.md for exact delivery and verification status. The included APKs are historical v0.3.0 builds; rebuild from source for v0.3.1 before installation. Start with `BOSHLASH_UZ.md` for Uzbek instructions.

## Quick start
1. Run `python scripts/configure.py` to create a new `.env` with generated development secrets.
2. Fill the server-only provider/bot keys and bootstrap password in `.env`. With Docker installed: `docker compose --profile telegram up --build -d`.
3. Run `docker compose exec api python -m app.cli create-user --help` to create authorized teacher/admin accounts. Public registration only permits parent/student roles.
4. Run admin web locally: `cd admin-web && npm ci && npm run dev`. API URL defaults to `http://localhost:8000/api/v1`.
5. Android: open `android` in Android Studio with JDK 17, Android SDK 35, Build Tools 35.0.0. Run `./gradlew testDebugUnitTest assembleDebug`. Android emulator connects to `http://10.0.2.2:8000/api/v1/` in debug only. Release requires an HTTPS API_URL Gradle property.
6. Register a student and parent, student creates a family invite, parent accepts it, parent assigns homework, student submits, parent approves, student enrolls a device, parent sets policy, student redeems a reward on that device.

## Local backend without Docker
`python -m venv .venv && .venv/bin/pip install -r backend/requirements.lock.txt`
`cd backend && DATABASE_URL=sqlite:///./development.db JWT_SECRET=<at-least-32-random-characters> ../.venv/bin/alembic upgrade head`
`DATABASE_URL=sqlite:///./development.db JWT_SECRET=<same-secret> ../.venv/bin/uvicorn app.main:app --reload`
SQLite is a developer/test fallback; PostgreSQL is the deployment target. Production explicitly rejects SQLite and requires Redis. See docs/DEPLOYMENT.md.

## Verification
`cd backend && ../.venv/bin/pytest -q`
`cd admin-web && npm ci && npm run build && npm test`
`cd android && ./gradlew testDebugUnitTest assembleDebug`

## Product boundary
Essential communication never requires a reward. Only appropriately enrolled devices can suspend packages. A normal install stays voluntary. Teachers have academic access, never household device-policy access. AI uses the configured server-side provider; Groq includes a separate safety classifier, DeepSeek uses Groq moderation, and the generic compatible adapter needs a moderation endpoint. AI is unavailable if keys, moderation or credits fail; the app shows an explicit unavailable error. Subjective reviews always require an adult. All reward minutes are elapsed access windows, not a claim of measured foreground usage.

See docs/ARCHITECTURE.md, docs/DEVICE_OWNER_SETUP.md and docs/TESTING.md before deploying. Full requested screen/feature parity is tracked honestly, including outstanding work, in IMPLEMENTATION_PROGRESS.md.
