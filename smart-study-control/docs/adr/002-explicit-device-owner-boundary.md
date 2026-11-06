# ADR 002: Explicit Device Owner boundary

Status: accepted

Separate a pure deterministic policy evaluator from Android Enterprise operations. Only the signed app that is actually Device Owner calls suspension and uninstall APIs. Ordinary installs report voluntary mode. No accessibility/overlay/VPN substitute.

Consequence: document limitations, test at the boundary, and avoid unsupported security claims.
