# Project Status

Roadmap: [docs/SPRINT_ROADMAP.md](docs/SPRINT_ROADMAP.md)

Current Sprint: **M1 — Runtime & LLM Reliability**

Current Micro-task: **M1.5 — Evidence-driven reliability fix**

M1 Gate: **TECHNICAL_FAILURE <= 1/15 on full15 LIVE**

M1 Gate Status: **NOT PASS YET**; targeted validation không thay thế full15 LIVE Gate.

Sprint transition rule: **Only Gate PASS allows moving to the next mini-sprint.**

## Progress

- M1.1 DONE
- M1.2 DONE — provider observability
- M1.3 DONE — offline verification/review
- M1.4 DONE — targeted LIVE diagnosis
- M1.5 IN PROGRESS
- M1.6 NOT STARTED

## Current Evidence

- Python 3.11.9 verified.
- Gemini credential/auth fixed; R2 diagnostic probe PASS.
- Historical POST-AUTH full15 = 4 PASS / 11 FAIL; 11 FAIL đều TECHNICAL_ERROR.
- M1.4 targeted LIVE confirmed Gemini HTTP 503 / UNAVAILABLE / high demand.
- M1.5 current local, uncommitted patch: bounded 1-second backoff before existing transient retry.
- Targeted LIVE after patch: E01 503 → 1s → 503 → TECHNICAL_ERROR;
  V01 503 → 1s → success → PASS/P05; V02 503 → 1s → 503 → TECHNICAL_ERROR.
- Historical ClientError vẫn chưa exact-classified bằng observability mới.

Detailed sprint report: [reports/sprints/M1_runtime_reliability.md](reports/sprints/M1_runtime_reliability.md)
