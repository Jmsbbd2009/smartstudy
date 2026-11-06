# Android source layout

| Module | Responsibility |
|---|---|
| app | Application, Compose routes, MVVM state, local alarm receiver/service/scheduler, localized strings |
| domain | Pure Kotlin policy precedence, overnight windows, elapsed lease validity, next alarm occurrence |
| data | Retrofit/OkHttp, rotating authentication, Keystore token vault, Room cache/outbox, DataStore preferences |
| devicepolicy | DeviceAdminReceiver, owner capability guards, package application, persistence/journaling and recovery |
| sync | Hilt WorkManager jobs, policy version reconciliation and reward reservation/ack |
| core/designsystem | Material 3 light/dark theme |

Min SDK 26; compile/target SDK 35. Separate feature Gradle modules are deferred until the flows stabilize; real files are grouped by responsibility, without dozens of empty modules. Navigation exposes implemented screens only. Parent/teacher full administration is primarily on the React dashboard. The complete original 30/16/15-screen specification remains broader than this delivery.

Stable baseline compatibility verified against official AGP 8.9 documentation: Gradle 8.11.1, JDK 17, SDK Build Tools 35.0.0. Kotlin and Compose compiler plugins use the same 2.1.20 version. SDK/Gradle/JDK need network on first build; no machine-specific paths are committed. The Gradle wrapper is included. Release signing keys are never generated or hardcoded.
