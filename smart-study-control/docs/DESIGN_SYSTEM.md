# Design system

| Token | Value |
|---|---|
| Navy | #101C35 |
| Blue | #477BFF |
| Mint | #37CFA2 |
| Yellow | #FFC857 |
| Background | #F8FAFF |
| Slate | #8490A7 |

Material 3 Compose theme, system light/dark, 16dp rounded cards, 8dp spacing grid, minimum 48dp touch targets, scalable system typography. Status uses text plus color. Mint/slate are accents, not low-contrast body text. Focus is keyboard-visible on web. Error messages announce the actual failed operation. Motion is optional and never necessary to understand state.

Uzbek Latin is the default. Android uses string resources with Uzbek/English/Russian reading copy; the web has a translation dictionary for core navigation. New web authoring copy is Uzbek; full web English/Russian translation remains a release gate. Do not store secrets or backend details in user-visible copy. Extended screen parity and translation coverage are release gates, not silently replaced by dead buttons.


The reading workspace uses a real SVG concept map with accessible title/text, citation-bearing flip cards, an adult answer-key editor and radio-group assessments. Source text is rendered as text; provider HTML/scripts are never injected. Correct-answer coverage and self reports have separate labels. Async PDF/OCR/AI actions show working/error states and disable conflicting submissions. Guardian automation is off until explicitly configured.
