# ADR 007: Pinned Android baseline

Status: accepted

Use AGP 8.9.2, Gradle 8.11.1, JDK 17, compile/target SDK 35 and min SDK 26; Kotlin/Compose compiler plugin 2.1.20. These are an intentional stable baseline, not a claim of latest versions. Store submission target SDK requirements must be rechecked before release.

Consequence: document limitations, test at the boundary, and avoid unsupported security claims.
