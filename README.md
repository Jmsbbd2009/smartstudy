# Smart Study Control

Android app and FastAPI backend. Current Android source: **0.4.2**.

The root GitHub Actions workflow tests the API and Android modules, builds a debug-signed preview against the existing HTTPS Render API and publishes an installable prerelease only after both jobs pass.

There is no public website in the deployment configuration. Legacy React administration source is retained for reference; native staff authoring/administration is incomplete and tracked in [implementation progress](smart-study-control/IMPLEMENTATION_PROGRESS.md).

Deployment root: `smart-study-control`. Backend: `infrastructure/docker/backend.Dockerfile`. Existing database and private environment values must be preserved across updates.

See [setup](smart-study-control/README.md), [release limitations](smart-study-control/docs/BUILD_ARTIFACTS.md) and [device enrollment](smart-study-control/docs/DEVICE_OWNER_SETUP.md).
