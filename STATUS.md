# Project Status

Roadmap: [docs/SPRINT_ROADMAP.md](docs/SPRINT_ROADMAP.md)

Current Sprint: **M1 — Runtime & LLM Reliability**

M1 Overall: **IN PROGRESS**

Next Micro-task: **M1.6 — Full15 Gate + Sprint Review (NOT STARTED)**

M1 Gate: **TECHNICAL_FAILURE <= 1/15 on full15 LIVE**

M1 Gate Status: **NOT PASS YET / NOT EVALUATED AFTER CURRENT RELIABILITY FIX**; targeted validation không thay thế full15 LIVE Gate.

Sprint transition rule: **Only Gate PASS allows moving to the next mini-sprint.**

## Progress

- M1.1 DONE
- M1.2 DONE — provider observability
- M1.3 DONE — offline verification/review
- M1.4 DONE — targeted LIVE diagnosis
- M1.5 DONE — config-driven OpenAI provider + production adapter smoke
- M1.6 NEXT / NOT STARTED

## Current Evidence

- Python 3.11.9 verified.
- Gemini credential/auth fixed; R2 diagnostic probe PASS.
- Historical POST-AUTH full15 = 4 PASS / 11 FAIL; 11 FAIL đều TECHNICAL_ERROR.
- M1.4 targeted LIVE confirmed Gemini HTTP 503 / UNAVAILABLE / high demand.
- M1.5 code checkpoint: `c4d2f8d`; bounded 1-second transient backoff and config-driven OpenAI provider path committed.
- Targeted LIVE after patch: E01 503 → 1s → 503 → TECHNICAL_ERROR;
  V01 503 → 1s → success → PASS/P05; V02 503 → 1s → 503 → TECHNICAL_ERROR.
- Targeted Gemini diagnosis confirmed HTTP 429 / RESOURCE_EXHAUSTED / quota exceeded; không gán ngược lỗi này cho mọi historical ClientError.
- OpenAI R2/R4/R7 compatibility probe: HTTP 200, existing validators PASS; adapter-side schema normalization required.
- OpenAI provider: no automatic fallback, SDK max_retries=0, provider/model-aware cache/cassette identity và OPENAI_API_KEY redaction.
- Canonical `.venv-bootstrap`: Python 3.11.9, openai 3.24.0, google-genai 2.25.0; targeted offline tests **77 PASS / 0 FAIL**.
- Production OpenAI adapter smoke do coordinator chạy: gpt-6-luna, reasoning_effort=none, temperature=0.0; một provider attempt, latency 4007 ms, extraction validator PASS, result PASS.
- Compatibility probe và một smoke PASS không chứng minh full reliability hoặc OpenAI luôn đáng tin cậy hơn Gemini. full15 M1 Gate chưa chạy sau fix; M1.6 chưa bắt đầu.

Detailed sprint report: [reports/sprints/M1_runtime_reliability.md](reports/sprints/M1_runtime_reliability.md)
