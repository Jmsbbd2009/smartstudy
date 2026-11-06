# ADR 008: Source-grounded reading and bounded automation
Status: accepted, 2026-10-30.

Books remain private to the uploading adult, with text-range sharing through current guardian/classroom authority. The parser is resource-limited and OCR is explicitly opt-in. Every concept and objective question cites an exact quote from the selected pages; source hashes and lesson versions prevent stale publication. An adult validates all answer keys before publication. Quotes establish source presence, not factual correctness or entailment.

Reading progress distinguishes self-reported page marking from correct-answer evidence. Neither is represented as proof of reading a complete book. Quizzes use server-private shuffled answer snapshots, 30-minute expiry and immutable completed answers. A wallet-row lock plus unique learner/lesson origin makes repeated approvals and duplicate assignments incapable of minting repeated credit. Automatic credit requires guardian opt-in and a bounded policy; app access still uses the existing reservation/OS acknowledgment flow.

Autopilot can create bounded, zero-reward academic practice only. It has no arbitrary tool execution or device-policy capability. Its output passes strict structured validation and moderation; it rechecks active authority after provider calls. One completed run per child/local day and at most three failed provider attempts bound autonomous cost and duplicate tasks. Live provider qualification remains a release gate.

Source changes, lesson revisions and publication serialize on the book row, with lesson state refreshed after acquiring the lock. Concurrent edit/publication therefore cannot publish an unreviewed version or race a source OCR replacement.
