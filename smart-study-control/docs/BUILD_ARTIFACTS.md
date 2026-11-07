# Build artifacts — Android 0.4.2 preview

[Download APK](https://github.com/Jmsbbd2009/smartstudy/releases/download/v0.4.2-preview-b13b376/SmartStudy-0.4.2-test.apk) · [Release](https://github.com/Jmsbbd2009/smartstudy/releases/tag/v0.4.2-preview-b13b376) · [Successful CI](https://github.com/Jmsbbd2009/smartstudy/actions/runs/42365397958)

Source commit: `b13b376d1b37322d1b6c969982b1d7b3f6cd85fa`. Android versionCode 7, versionName 0.4.2. Actual CI unit tests, debug APK and instrumentation APK builds passed; instrumentation was not executed on an emulator/device.

APK size: **59,209,011 bytes**. SHA-256: `1d74db38335e4cbc9725206372b5f61c547de3b9de61c28364d73de1a57e9cb1`.

This is an installable debug-signed preview using `https://studycontrol-api.onrender.com/api/v1/`. Its signing certificate may differ from older installed APKs. Do not uninstall an existing app just to force an update without preserving its data. Production update signing and physical-device qualification remain incomplete.

## Historical artifacts

The v0.3.0 APKs were previously built with versionCode 3/versionName 0.3.0, min SDK 26, target/compile 35, Gradle 8.11.1, full JDK 17 (Corretto), and Build Tools 35.0.0. Both v2 signatures were verified with SDK apksigner. No release signing, store publication or device execution is claimed. The universal debug APK includes bundled ML Kit and native libraries for several ABIs. Camera/GPS/OS enforcement are not qualified on physical hardware. No real API key or password is embedded in either historical APK.

The Android app connects to the separately hosted API. Its debug default is emulator-only `10.0.2.2:8000`; provide an HTTPS API_URL for a deployable phone build. There is no public website in this release. Camera/GPS/OS enforcement were compiled in v0.3.0, not qualified on physical hardware. No real API key or password is embedded in the APKs. To install an update over an existing app without clearing its data, preserve the same application ID and signing certificate; this workspace has no production signing keystore.

| File | Bytes | SHA-256 |
|---|---|---|
| artifacts/v0.3.0/smart-study-control-debug.apk | 59031719 | 4c3b3a2214f28664d7349536ad530b5ade20fda569f8a5b771f7c8c368b328d2 |
| artifacts/v0.3.0/smart-study-control-instrumentation-debug.apk | 1100518 | 9d27cb0263c8d5a066cd8f5b0b0d902f80f7564ba3419c487d2ae3810f67f4a5 |
