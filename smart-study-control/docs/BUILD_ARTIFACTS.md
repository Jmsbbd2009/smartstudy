# Build artifacts — v0.3.1 source

This source snapshot is versionCode 4/versionName 0.3.1. **The included APKs are historical v0.3.0 (versionCode 3) builds and do not include the new native assignment attachment flow.** Rebuild locally with the documented Android SDK/Gradle toolchain before installing v0.3.1. The current workspace used to prepare this snapshot does not contain Gradle 8.11.1 or Android SDK 35, and network policy prevented downloading them; no v0.3.1 compile or test is claimed.

The v0.3.0 APKs were previously built with versionCode 3/versionName 0.3.0, min SDK 26, target/compile 35, Gradle 8.11.1, full JDK 17 (Corretto), and Build Tools 35.0.0. Both v2 signatures were verified with SDK apksigner. No release signing, store publication or device execution is claimed. The universal debug APK includes bundled ML Kit and native libraries for several ABIs. Camera/GPS/OS enforcement are not qualified on physical hardware. No real API key or password is embedded in either historical APK.

Server/backend and web panel run separately. Debug defaults use emulator 10.0.2.2:8000 and 10.0.2.2:5173; passkeys require matching secure web origin and may not work at the debug IP URL. Camera/GPS/OS enforcement were compiled in v0.3.0, not qualified on physical hardware. No real API key or password is embedded in the APKs.

| File | Bytes | SHA-256 |
|---|---|---|
| artifacts/v0.3.0/smart-study-control-debug.apk | 59031719 | 4c3b3a2214f28664d7349536ad530b5ade20fda569f8a5b771f7c8c368b328d2 |
| artifacts/v0.3.0/smart-study-control-instrumentation-debug.apk | 1100518 | 9d27cb0263c8d5a066cd8f5b0b0d902f80f7564ba3419c487d2ae3810f67f4a5 |
