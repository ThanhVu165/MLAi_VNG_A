# Exodia Sprint 2 — LIVE full15 baseline — 2026-10-02

**Baseline: NOT EVALUATED. PASS: N/A. FAIL: N/A. Core Gate: CLOSED — chưa có bằng chứng để PASS.**

No suite or individual case was executed. No API calls were made. No application code, prompts, policy, retrieval, model, expected labels, harness matching, timeout, or retry policy was changed. No database initialization/migration was performed. No commit was created.

## Git safety

- Repository: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A`
- Initial branch: `main`; initial `git status --short`: empty; working tree clean.
- HEAD: `803d28b8c33be7c53198d75f6c088ada73c28022`.
- Local `dev` did not exist. Created `dev` from current HEAD and switched, as authorized.
- Current branch: `dev`; `main...dev` ahead/behind: 0/0; identical code.
- Worktree OFF; no task branch created.
- Branch strategy: main stable; dev Sprint integration; task/* isolated implementation.

## Runtime preflight

- GOOGLE_API_KEY available: YES
- GEMINI_MODEL explicitly configured: NO (after the application's local .env loader).
- Resolved API model argument: `gemini-3.6-flash`, from `infra.llm.DEFAULT_MODEL`; `call_json()` reads `os.getenv("GEMINI_MODEL", DEFAULT_MODEL)`, and `_request_gemini()` forwards it to `client.models.generate_content(model=model, ...)`.
- Actual runtime model sent to API: N/A — no API call; resolution is verified, execution is unverified.
- RUNBOOK and harness metadata fallback say `gemini-3.5-flash-lite`; these do not override the runtime default. Harness metadata could therefore be cosmetic/inaccurate when GEMINI_MODEL is unset.
- Effective LLM_MODE: `live` (default); effective LLM_CACHE: `1` (default). The live path can return SQLite cache entries before calling Gemini. Fresh LIVE execution is not established; no settings were changed.
- `tests/cassettes` does not exist.
- Intended Python 3.11 .venv cannot launch: its base interpreter `C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe` is missing. `py` is unavailable on PATH.
- Bundled Python 3.12.14 used only for read-only preflight and report writing; `google.genai` is unavailable there. The project .venv has legacy google_generativeai, but no google_genai distribution was observed.
- Database: `data/app.db`; schema user_version=0; six sources (5 ACTIVE, 1 SUPERSEDED), 72 chunks. Missing `source_contents`, `case_results`, and `case_jobs`; current schema target is 2. Corpus/database not yet ready for the current pipeline.
- Standard documented initialization is `py -3.11 -c "from corpus.seed import ensure_seeded; ensure_seeded()"`; the database layer normally migrates with a backup. It was not attempted because execution preflight is blocked.
- Exact documented full15 command: `py -3.11 -m verify.harness --set full15 --output data/validation/full15.json`.
- RUNBOOK live setup uses DATABASE_PATH=data/validation/manual-live.db, LLM_MODE=live, LLM_CACHE=0, and GEMINI_MODEL=gemini-3.5-flash-lite. That model override was not applied because this task forbids changing the effective model.
- Effective timeout: LLM_TIMEOUT_S=30 seconds; API HttpOptions timeout is min(call timeout, 30) * 1000 ms, further limited by remaining whole seconds of the case budget.
- Case budget: 60 seconds and at most four API attempts, shared across steps/retries. This bounds LLM attempts, not necessarily total pipeline wall time (e.g. retrieval loading). Full15 has no harness total time limit; the 90-second harness check applies only to escalation5.
- Retry: LLM_RETRIES=1; wrapper clamps retry count to at most one for transient TimeoutError/ConnectionError and named timeout, connection, service, quota, or server exceptions. Other errors return failure immediately. R2 has two structured-extraction parse attempts; Question Guard may regenerate once, within the same case budget. No retry settings changed.
- Harness `_matches()` requires decision, type, exact expected rule_id (when specified), active citations for AUTO_REPLY, and a nonempty question/options card for ESCALATE. Expected P03 versus actual P04 FAILS.

## Complete case inventory

N/A means unobserved, not PASS or FAIL. P04 involvement is unknown because no case ran.

| case_id | Expected decision | Expected escalation type | Expected rule_id | Actual decision | Actual escalation type | Actual rule_id | Harness PASS/FAIL | Latency | API/LLM error | P04 involved YES/NO |
|---|---|---|---|---|---|---|---|---|---|---|
| V01 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| V02 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| V03 | ESCALATE | AUTHORITY_REQUIRED | P01 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| V04 | ESCALATE | OUT_OF_POLICY | P02 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| E01 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| E02 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| E03 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| E04 | ESCALATE | FACT_UNRESOLVED | P03 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| E05 | ESCALATE | AUTHORITY_REQUIRED | P01 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| F01 | INVALID_INPUT | — | R0 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| F02 | ESCALATE | OUT_OF_POLICY | R1 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| F03 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| F04 | ESCALATE | AUTHORITY_REQUIRED | P01 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| F05 | ESCALATE | OUT_OF_POLICY | P02 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |
| F06 | AUTO_REPLY | — | P05 | N/A | N/A | N/A | NOT RUN | N/A | N/A — not called | N/A — not run |

## Summary

- Executed: 0/15; NOT RUN: 15/15.
- PASS: N/A; FAIL: N/A. Baseline: NOT EVALUATED — all 15 cases were not run.
- Actual P01/P02/P03/P04 counts: N/A (no observations).
- API/timeout case count: N/A; other technical failure case count: N/A.
- Total suite wall-clock time, median latency, max latency: N/A — suite never started.
- Actual runtime Gemini model: N/A; verified resolved model argument: gemini-3.6-flash.
- Rule mismatches: none observed; all 15 actual rules unknown.
- Technical case failures: none observed because no case ran. Preflight blockers: missing intended Python interpreter, missing SDK in the available fallback, unmigrated database, and cache-enabled live path lacking confirmed fresh API execution.

## Correct-rule evidence and Core Gate

| Requirement | Evidence | Result |
|---|---|---|
| TECHNICAL_FAILURE <= 1/15 | No completed LIVE suite; count unknown | Not established |
| >=1 FACT_UNRESOLVED/P03 PASS | E04 expected; not run | Not established |
| >=1 OUT_OF_POLICY/P02 PASS | V04, F05 expected; not run | Not established |
| >=1 AUTHORITY_REQUIRED/P01 PASS | V03, E05, F04 expected; not run | Not established |

P04 does not count as P03 evidence. F02's expected OUT_OF_POLICY/R1 would not establish correct-rule P02 evidence.

**Core Gate: CLOSED — chưa có bằng chứng để PASS.** Baseline: NOT EVALUATED; this is not a measured conclusion about application correctness.

## Final Git state

`git diff --stat`: empty (no tracked-file changes).

`git status --short` after report creation:

```text
?? reports/
```

The only new nonignored artifact is `reports/baseline_full15_live_2026-10-02.md`. Uncommitted. Stopped without fixes or reruns.
