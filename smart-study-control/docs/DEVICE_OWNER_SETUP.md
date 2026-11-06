# Device Owner feasibility and enrollment

Official references checked 2026-10-30:
- https://developer.android.com/reference/android/app/admin/DevicePolicyManager
- https://developer.android.com/work/dpc/dedicated-devices/cookbook
- https://developer.android.com/work/dpc/provisioning
- https://developer.android.com/training/package-visibility
- https://developer.android.com/develop/background-work/services/alarms
- https://developer.android.com/build/releases/agp-8-9-0-release-notes

`isDeviceOwnerApp` API 21. `setPackagesSuspended` and `isPackageSuspended` API 24. `setUninstallBlocked`/`isUninstallBlocked` API 21. The baseline min SDK 26 covers these, but ownership and runtime failures still require checks. The adapter deliberately supports Device Owner only; a work profile does not grant control over the student's entire personal device. Non-suspendable packages are reported by Android and never treated as success.

## Lab enrollment
Use a spare test device/emulator, with owner authorization and no personal data/accounts. Device Owner provisioning may require a factory reset; never reset a family device automatically.
1. Build and install the debug APK.
2. Confirm accounts are removed and the device is eligible.
3. `adb shell dpm set-device-owner uz.smartstudy.control/uz.smartstudy.devicepolicy.StudyAdminReceiver`
4. Open the app, sign in as the student, enroll the logical device record, obtain household authorization and sync.
5. Check the device status screen: actual owner capability must be true before enforcement is available.

ADB is a lab workflow. QR/zero-touch production provisioning, ownership terms, DPC distribution and Android Enterprise eligibility need an actual device fleet and deployment validation. Do not present an untested QR payload as production enrollment. Legacy managed-device provisioning intents are deprecated; current production provisioning must be qualified against current official guidance.

## Protected packages
The client protects itself, all system applications by default, active launcher, dialer, SMS handler, enabled input methods and accessibility services. Parents select visible launcher apps; no QUERY_ALL_PACKAGES permission. OEM/system exceptions are an adult-reviewed allowlist, not broad collection.

## Recovery
A linked guardian can request deprovisioning from the device API. Device sync first unsuspends every locally tracked package, removes only uninstall restrictions created by this application, verifies failures, and acknowledges the server. If network is unavailable, use the existing managed-device administrator recovery channel; no hidden universal PIN. Failed cleanup leaves enrollment pending and lists failed packages. The implementation releases its own restrictions; it does not silently clear or transfer Device Owner. Formal owner relinquishment/factory reset is a separate attended administrative operation. `clearDeviceOwnerApp` is deprecated and is intentionally not used.

Force-stop, firmware modification, factory reset, OEM power management, removal of management and privileged administrators are outside the guarantee. Exact boundary execution needs physical-device qualification; periodic WorkManager alone cannot guarantee exact enforcement. Emergency calls/communication remain accessible even during overrides, study and sleep.


## Uninstall status in v0.2
After authorized managed enrollment the existing DPC applies self-uninstall blocking and reads back `isUninstallBlocked`. Android and the guardian panel show active, unconfirmed or standard-mode protection from this result. `POST /devices/{id}/sync` includes `uninstall_blocked`; the server masks it false unless Device Owner is also reported. This is client telemetry, not attestation. It does not activate management on an ordinary install. The cleanup/recovery path releases the tracked protection. These OS calls compiled here but were not exercised on enrolled hardware.
