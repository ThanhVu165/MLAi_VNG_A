# Project Status

Roadmap: [docs/SPRINT_ROADMAP.md](docs/SPRINT_ROADMAP.md)

Current Sprint: **M1 — Runtime & LLM Reliability (CLOSED)**

M1 Overall: **PASS**

M1.6: **DONE**. Next sprint: **M2 — Core Decision + Escalation Quality (NEXT; chưa bắt đầu)**.

M1 Gate: **TECHNICAL_FAILURE <= 1/15 on full15 LIVE**

M1 Gate Status: **PASS — TECHNICAL_FAILURE = 0/15 on final full15 LIVE** (06/10/2026, Asia/Saigon).

Sprint transition rule: **Only Gate PASS allows moving to the next mini-sprint.**

## Progress

- M1.1 DONE
- M1.2 DONE — provider observability
- M1.3 DONE — offline verification/review
- M1.4 DONE — targeted LIVE diagnosis
- M1.5 DONE — config-driven OpenAI provider + production adapter smoke
- M1.6 DONE — final Gate + reviews; coordinator authorized closure

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
- Compatibility probe và một smoke PASS không chứng minh full reliability hoặc OpenAI luôn đáng tin cậy hơn Gemini. Subsequent M1.6 evidence: final verify4 **4/4 PASS**; escalation5 **4/5 semantic PASS**, **44.48s <=90s**; full15 **14/15 semantic PASS**, **0/15 TECHNICAL_ERROR**, **M1 Gate PASS**.
- Final Code Review: **PASS**, no blocker/high/medium; independent Anti: **PASS WITH DOCUMENTED DEBT**, theo closure decision của coordinator.
- E04 known M2 issue: expected **ESCALATE / FACT_UNRESOLVED / P03**, actual **ESCALATE / AUTHORITY_REQUIRED / P01** trên final OpenAI path. Investigate in M2; expected label giữ nguyên. Đây là provider/model-sensitive correctness issue; exact non-regression against the old Gemini/dev path has not been proven.
- Curated final JSON/logs, SHA-256 và source local paths: [M1 evidence manifest](reports/evidence/m1/README.md). Không archive DB; sáu LOW debts và tracked `.pyc` hygiene debt ghi trong living report. Không khoản debt nào làm M1 Gate mất hiệu lực.

Detailed sprint report: [reports/sprints/M1_runtime_reliability.md](reports/sprints/M1_runtime_reliability.md)
