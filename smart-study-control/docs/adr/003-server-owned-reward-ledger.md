# ADR 003: Server-owned reward ledger

Status: accepted

Server atomically reserves minutes and creates a pending lease; device confirms success or requests an idempotent refund. Offline devices cannot mint or spend credits. One reward origin is unique independently of HTTP idempotency keys.

Consequence: document limitations, test at the boundary, and avoid unsupported security claims.
