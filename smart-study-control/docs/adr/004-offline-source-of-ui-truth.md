# ADR 004: Offline source of UI truth

Status: accepted

Room emits cached resources. Outbox writes keep original idempotency keys. Policy versions never go backward. Wall-clock schedules and elapsed-clock reward duration are distinct; boot identity changes invalidate leases.

Consequence: document limitations, test at the boundary, and avoid unsupported security claims.
