# Phase 5 privacy leakage evaluation

- Synthetic sensitive spans checked: 32
- Sensitive spans still present after Redact & Continue: 0
- Observed leakage rate on this fixture: 0.000
- Block Request and Gemini non-invocation are exercised by automated tests; see `tests/test_privacy_evaluation.py`.
- Live Gemini calls were **not** made. Gemini success/quota/timeout behavior is covered with mocked responses only.
- Synthetic identifiers and names are used only in the fixture; reports omit matched values.
- This test does not establish secure deletion, OCR coverage, or complete privacy protection.
