# Deployment and operation

## Development
Generate `.env` with `python scripts/configure.py`. Use `docker compose up --build -d` when Docker is available. API startup runs `alembic upgrade head`; `/health/live` is process liveness and `/health/ready` checks schema presence and configured Redis connectivity. Compose publishes API/UI only on localhost. Use `python -m app.cli create-user --email ... --name ... --role TEACHER` inside the API container for attended staff onboarding. Password is prompted without echo; no default privileged credentials.

For a phone on your LAN, use `-PDEBUG_API_URL=http://127.0.0.1:8000/api/v1/` and `adb reverse tcp:8000 tcp:8000` over USB, or configure an authorized LAN endpoint; the packaged default points to emulator `10.0.2.2`, not an actual hosted backend. Never ship a hardcoded local endpoint. A release build requires `-PAPI_URL=https://your-host/api/v1/` and forbids cleartext traffic.

## Production gates
Set APP_ENV=production, PostgreSQL DATABASE_URL, REDIS_URL, a new JWT_SECRET and HTTPS CORS_ORIGINS. Provide a TLS ingress. Configure web build VITE_API_URL and the Nginx connect-src CSP to that exact origin. Docker Compose here is local development, not a hardened production deployment. Run migrations once per release before horizontally scaling workers. Use a separate least-privilege migration role if enforcing table-level permissions. Back up PostgreSQL and private uploads as a coherent unit and rehearse restores.

No remote service has been deployed in this task. No GitHub Actions run, device fleet enrollment or app-store submission has occurred. Docker image build cannot be verified without a Docker daemon. Static CI and Compose definitions are reproducible inputs, not evidence that those environments passed.

## Monitoring
Probe health, request error rates, p95 latency, Redis availability, database locks, stale pending unlocks, policy failures and outbox rejections. Do not log authorization headers, homework contents, refresh credentials or private upload names. Audit entries record actor/action/resource and policy version, not private app usage for teachers.

## Recovery
For failed policy application, inspect per-package failures and actual Device Owner status. For stale policy version, reload and reapply guardian changes. Request device cleanup before deleting an account or revoking the final guardian link. For exact-alarm denial, show degraded clock timing and request the Android permission through a user action; never silently activate alternative powers. See DEVICE_OWNER_SETUP.md.


## Reading and scheduled AI
Upgrade existing databases with `alembic upgrade head` after a coherent backup. The reading migration is additive; rolling back drops reading/automation history and must be planned. Runtime lock now includes pypdf. Backend image installs Poppler/Tesseract English tools; OCR remains off until `OCR_ENABLED=true`. Additional language packages and `OCR_LANG` must match. Run PDF processing on Linux; for broad uploads isolate processing in dedicated workers and quarantine files. No executable PDF preview is served to students.

Compose adds an `autopilot` service, which starts after API health and runs only explicitly opted-in child settings. Outside Compose run `python -m app.workers.autopilot` (or `--once`). Provider, model, moderation URL and keys stay server-side. One completed run/child/day and three failed attempts bound the loop. Practice tasks never mint rewards. Reading automatic rewards separately require a validated published lesson and guardian reward consent. Monitor failed runs, parser rejection/latency, current roster scopes and reading-credit contention. Node >=22.19 is required for the HTTP UI integration test's Undici transport.


## v0.3 access and bot deployment
Set a bootstrap login and private temporary password before first startup. The API entrypoint runs migrations and idempotent bootstrap only when those variables are present. Force renewal is enforced at protected APIs, not just in UI. Remove the bootstrap password from long-lived secret configuration after initial account setup; idempotence never overwrites an existing account.

For Telegram polling use `docker compose --profile telegram up --build -d`, one poller per bot. A preexisting webhook is never silently removed. For webhook mode configure the real HTTPS endpoint and header secret as described in ACCESS_ALARM_LOCATION_UZ.md; polling and webhook must not compete. Opt-in message delivery uses per-notification leases and three-attempt caps, with normal external-network ambiguity. Use the worker's delivery routine in a separate scheduled process if webhook mode is used.

Passkey RP_ID and ORIGIN must exactly match the deployed HTTPS web origin. Android ADMIN_WEB_URL points to that panel; native staff sign-in also supports Telegram. New Android permission declarations include foreground location and a typed visible service, never ACCESS_BACKGROUND_LOCATION. Photo ML Kit is bundled; Android build requires its additional Google Maven dependencies.

Groq is the qualified primary text provider in this revision. Fresh server keys are required; none are shipped. HF needs funded inference access and the supplied DeepSeek token was not accepted. Production deployment and live student/provider data processing still require operator consent/retention/region qualification and real hardware/browser testing.
