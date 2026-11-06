# ADR 001: Modular monolith

Status: accepted

Use a single FastAPI deployment and relational transaction boundary. One approval and its credit must commit together. Redis is infrastructure, not the source of wallet truth.

Consequence: document limitations, test at the boundary, and avoid unsupported security claims.
