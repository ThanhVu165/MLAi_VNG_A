# P0-CORE-RELIABILITY-FIX — implementation evidence

## Current disposition — resumed on integrated baseline

Coordinator supplied the official implementation AC1–AC7 and **RESUME IMPLEMENTATION
AFTER UPDATED PREFLIGHT** authorization in chat. The prior ownership STOP below is
historical and superseded. No Trello READY or new Task ID is required.

- Owner: Acer. Work label: `P0-CORE-RELIABILITY-FIX`.
- Current baseline: `dev@534064f88b2851febc762fcdd0d376a2f0b76cd6`.
- PR #68 is MERGED at that exact SHA. Task branch was fast-forwarded without rewriting history.
- Updated fetch and open-PR file inventory found no active Core/Infra ownership overlap.
  Remaining open PRs #51 and #55 concern deployment/study artifacts.
- Reviewed merged C1 changes in pipeline, LLM replay-budget enforcement, judge facade,
  grant reservations/ownership and existing C1 regressions before implementation.
- Status: **READY_FOR_REVIEW** — implementation, validation and self-review handed off. No DONE claim.

### Change and safety boundary

F-01/F-02: reuse the existing structured Question Guard fallback to render an already-decided
ESCALATE without another provider request when attempts are consumed. Multi-intent keeps its
grounded partial draft if generated. If R2 validation retry consumed that capacity, it omits
the optional partial draft and includes **all** requests in the human card. It does not drop
the routine request or present ungenerated text as an answer.

F-03: an otherwise valid successful card with invalid basis can use that same deterministic
card if repair has no attempt available. Its basis copies selected evidence verbatim, never
the invalid quote. Other primary fields are validated before choosing this fallback. Actual
provider/repair failure, invalid primary structure and expired deadline remain technical errors.

F-04: distinct `CaseAttemptsExhausted` and `CaseDeadlineExhausted` TimeoutError subclasses,
safe error messages and telemetry stop reasons `case_attempts_exhausted` /
`case_deadline_exhausted`. One pre-request block emits one skipped record and returns without
retry. Pipeline preserves these safe local reasons rather than replacing both with its
generic failure text. Deadline takes precedence if both limits have expired.

The existing `QUESTION_GENERATED` action records deterministic/degraded card generation;
there is no new audit action, persisted field or LLM response schema. `has_call_capacity`
checks deadline and active judge authorization without resetting or consuming attempts.
No fallback grants AUTO_REPLY, hides an actual provider failure, changes an R6 decision,
or accesses a different source set.

**Explicit F-02 limit:** a routine P05 path after two successful R2 responses and one R4
selection has no attempt left to generate a reply. It still returns ERROR/TECHNICAL_ERROR,
with no business escalation, draft or dispatch. AC2 requires a safe result without fail-open;
this implementation does not claim successful AUTO_REPLY recovery for that path. Guaranteeing
that recovery would need a separate approved call-graph design. An already-decided escalation
can finish deterministically, including after an R2 retry.

### Files and callers reviewed

Production changes:

- `core/question_gen.py`: capacity-aware card rendering, optional partial draft, provenance.
- `infra/llm.py`: capacity check, distinct local exhaustion exceptions/messages and single skip.
- `core/pipeline.py`: retain only the two new safe local failure-message prefixes.

Tests:

- `tests/test_core_reliability.py`: new synthetic wrapper/pipeline/worker/C1 regressions.
- `tests/test_guards.py`, `tests/test_semantic_validator_compat.py`: replace expectations of
  the repaired exhaustion bug with exact deterministic provenance or deadline-error assertions.
- `tests/test_provider_observability.py`: require one skipped record and distinct stop reasons.

Searched all callers of card generation, retrieval, budget context and attempt timeout across
Core/Infra/tests. Reviewed pipeline R2–R8, worker submit/tick persistence, R11 budget isolation,
Question Guard fallback and C1 replay/grant scope. Existing New-Input and C1 expected results
are unchanged. Black also normalized two pre-existing wrapping differences in `test_guards.py`.

### Test method and before-fix evidence

The initial nine synthetic tests ran against unmodified `dev@534064f`:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_core_reliability.py --basetemp=.codex_tmp/core-reliability-before-20261015 --tb=short
```

Result: **8 failed, 1 passed**. Multi-intent direct/worker paths (with/without R2 retry),
single-intent R2 retry escalation and invalid-basis repair returned the erroneous technical
failure; both exhaustion tests observed two skips. Routine retry fail-safe already passed.
The first invocation without explicit basetemp had nine fixture setup errors from a Windows
Temp-directory permission error; those were not counted as bug reproductions.

All tests use synthetic `.invalid` addresses and temporary seeded SQLite. Private-mode
probes set `LLM_MODE=live` only to execute the real budget/retry wrapper with `_request_openai`
patched to an in-memory provider double. This is **not an external LIVE call**. C1 tests use
replay doubles with the real C1 attempt counter. `tests/conftest.py` blocks sockets, DNS and
OpenAI clients before collection. No private evaluation input, Gold or historical result is read.

### Validation commands

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
.venv/Scripts/python.exe -m pytest -q tests/test_core_reliability.py tests/test_llm_budget.py tests/test_guards.py tests/test_semantic_validator_compat.py tests/test_provider_observability.py tests/test_judge_new_input_offline.py tests/test_judge_input_c1.py tests/test_runtime_worker.py tests/test_m3_t06_human_control.py tests/test_runtime_replay_audit.py tests/test_policy_engine.py tests/test_r2_validation_diagnostics.py --basetemp=.codex_tmp/core-reliability-handoff-20261015 --tb=short --show-capture=no --junitxml=.codex_tmp/core-reliability-handoff.xml
.venv/Scripts/python.exe -m black --check --line-length 100 core/question_gen.py core/pipeline.py infra/llm.py tests/test_core_reliability.py tests/test_guards.py tests/test_provider_observability.py tests/test_semantic_validator_compat.py
.venv/Scripts/python.exe -m ruff check core/question_gen.py core/pipeline.py infra/llm.py tests/test_core_reliability.py tests/test_guards.py tests/test_provider_observability.py tests/test_semantic_validator_compat.py
.venv/Scripts/python.exe -m mypy --ignore-missing-imports core corpus
.venv/Scripts/python.exe -m mypy --ignore-missing-imports --follow-imports=silent core/question_gen.py infra/llm.py core/pipeline.py
git diff --check
```

Final integrated run: **335 passed in 101.21s**, including 13 new reliability cases.
Five warnings concern existing `record_property` tests with JUnit xunit2 output; there were
no test failures. An intermediate run passed 335 tests in 95.77s. UTF-8 process settings in
the final command avoided the earlier Windows subprocess decoding warnings.

Black, Ruff, whitespace checks and UTF-8/NFC readback: **PASS** on changed files.
Scoped credential-pattern scan of all eight handoff files: **PASS, zero matches** for
OpenAI/GitHub/Google/AWS credential formats and private-key headers. Placeholder credentials
in synthetic tests are intentionally nonfunctional; `.env` was not read or included.

Full mypy (`core corpus`): **FAIL — 20 errors in three files**. Scoped mypy on the three
production files: **FAIL — four errors in the unchanged OpenAI SDK request/usage code** of
`infra/llm.py`. The remaining full-check errors are in unchanged `infra/judge_access.py` and
`infra/demo_access.py`. No suppressions or unrelated typing fixes were added. The same full
check with baseline `534064f` shadow files also returns **20 errors**. AST comparison proves
`_request_openai` and `_response_usage` are unchanged; the other two flagged modules have no
diff. Mypy is not claimed PASS.

Baseline type-check method: materialize only the three changed Python modules from
`git show 534064f:<path>` under `.codex_tmp/core-reliability-baseline-<path>.py`, then run
the same full command with `--shadow-file <path> <baseline-file>` for each module. This
does not switch/reset the checkout or create a second repository. Diagnostic logs stay under
`.codex_tmp/core-reliability-mypy-{baseline,current}.log`. Compare error messages after
removing shifted line numbers: **baseline_equals_current=True**, 20 errors on each side.

Secret-scan reproduction: `.venv/Scripts/python.exe .codex_tmp/core-reliability-secret-scan.py`
checks the exact staged eight-file allowlist, reads staged UTF-8 content, verifies NFC and
checks the credential/private-key patterns listed above. It never reads `.env` or prints
matched credential content. The scanner and local test/type-check artifacts are not committed.

Full repository suite, official evaluation and external provider quality are not claimed.

### AC1–AC7 implementation mapping

| AC | Result | Evidence |
|---|---|---|
| AC1 F-01 | PASS | Four direct/worker multi-intent regressions, with/without R2 validation retry. Normal multi-intent retains grounded partial draft; all paths start at most three requests. Baseline failures recorded above. |
| AC2 F-02 | PASS, safe-result boundary | Successful R2 retry reaches a P01 human card without a fourth request; routine retry stays TECHNICAL_ERROR with no draft/escalation/send. No claim of routine AUTO_REPLY recovery. |
| AC3 F-03 | PASS | Invalid basis uses exact selected source text when optional repair has no capacity; invalid primary structure, expired deadline and actual provider/repair failure remain technical errors. Policy enum/rule unchanged. |
| AC4 F-04 | PASS | Attempt exhaustion with time left and deadline exhaustion with attempts left each emit one skip, no provider call, no retry, distinct reason/message. Real transient retry regressions remain passing. |
| AC5 Core/worker/Human Control | PASS offline | Policy/guards, worker persistence, runtime replay/audit, Human Control and R11 budget suites in final 335-test run; no-fail-open and no-over-escalation retained. |
| AC6 New-Input/C1 | PASS offline | Unmodified `test_judge_new_input_offline.py` and `test_judge_input_c1.py` pass, including PREVIEW_READY, capability defaults, forged/expired/replayed grant, ownership and no-dispatch; additional real-budget C1 retry/fallback test. |
| AC7 evidence/handoff | PASS implementation handoff | Final commands/results, self-review, scoped secret scan and verified Git/PR references below. External LIVE/provider/API calls: 0. Independent review/Coordinator acceptance pending. |

### Self-review

Checked: budget remains 3 processing + 1 resume, 60-second deadline / 30-second request cap;
successful-provider/failed-validation accounting; no invented basis; all requests retained when
partial draft is omitted; no fallback on transport failure/invalid primary/deadline; decision
and persistence consistency; safe messages without prompt or credentials; active C1 grant
check before fallback. Policy, `core/types.py`, settings, C1 authorization, PREVIEW_READY,
dispatch guards, SQL schema and frozen evaluation files have no diff.

Independent safety review and Coordinator acceptance are still required. No merge, deploy or
DONE declaration is authorized by this evidence.

### Git and review handoff

- Tested implementation commit: `5e0ffe8a3dac3fa51ca77c62c2f8f754a6b1e036`.
- Pushed branch: `codex/p0-core-reliability-fix`.
- [PR #71](https://github.com/ThanhVu165/MLAi_VNG_A/pull/71) is OPEN, targets `dev`, and was
  verified MERGEABLE after creation. PR is attached to this chat.
- Remote branch matched the implementation commit; remote `dev` remained
  `534064f88b2851febc762fcdd0d376a2f0b76cd6`. No merge/deploy occurred.
- This evidence-only follow-up records the implementation SHA and PR URL. The final report
  commit/head is provided in chat and by the PR branch; no runtime code changed after validation.
- Handoff to Coordinator/independent reviewer: review the three production-file changes,
  deterministic-card safety/provenance, F-02 safe-result limitation, C1 grant checks, unchanged
  mypy debt and AC1–AC7 evidence. Acceptance and integration remain Coordinator decisions.
- Existing `.codex_tmp/` and `outputs/` remain untracked; no local artifact or credential was
  included. Secret scan/whitespace checks were repeated for the evidence follow-up.

---

## Historical initial preflight STOP — superseded by resume authorization

- Date: 2026-10-15 (Asia/Saigon).
- Owner: Acer — Core Reliability Implementation.
- Historical status: **STOP — resolved by PR #68 merge and official resume authorization.**
- Authorization: Coordinator amendment in this chat, “AUTHORIZATION: GO IMPLEMENTATION — CARDLESS APPROVED”.
- Exact implementation authorization: “Cho phép Codex **thực hiện sửa code F-01–F-04** theo Task Contract đã cung cấp.”
- Exact cardless amendment: “Bỏ yêu cầu Task ID chính thức và Trello READY đối với nhiệm vụ này.” / “Không cần tạo Trello card trước khi triển khai.”
- Exact stop condition: “Nếu gặp conflict ownership hoặc cần CONTRACT-CHANGE, STOP và báo Coordinator.”
- No Task ID or Trello card was created or requested. Repository evidence and chat replace card handoff.

## Verified baseline and working tree

`git fetch origin dev` and `git ls-remote origin refs/heads/dev refs/heads/codex/judge-input-c1`
both verified remote `dev` at `11bd04205e560e489203da43874e332505727a2a`.
Initial branch was `codex/ux-responsive-cardless`, HEAD
`974c5709a08a9e99fae20d96ea0142156eeeaea2`. No tracked changes were present;
existing untracked `.codex_tmp/` and `outputs/` were preserved without inspecting their data.
Task branch `codex/p0-core-reliability-fix` was created from verified `origin/dev`.
No worktree, reset, clean, stash, rebase or force-push was used.

Read `AGENT.md`, `docs/TEAM_WORKFLOW.md`, Ponytail and GitHub workflow skills, and
`reports/sprints/CORE_RELIABILITY_DIAGNOSTIC_20261015.md` from verified `origin/dev`.
The diagnostic identifies F-01–F-04 but its AC1–AC7 describe the diagnostic and evidence
correction, not an implementation Task Contract. The implementation AC1–AC7 and exact
approved file list referenced by the amendment were not found in available chat or tracked
repository evidence. Do not substitute diagnostic acceptance criteria for implementation AC.

## Ownership conflict evidence

`gh pr list --repo ThanhVu165/MLAi_VNG_A --state open --json number,title,headRefName,files --limit 30`
and `gh pr view 68 --repo ThanhVu165/MLAi_VNG_A` verified:

- [PR #68](https://github.com/ThanhVu165/MLAi_VNG_A/pull/68), OPEN, targets `dev`.
- Branch: `codex/judge-input-c1`.
- Remote head: `129f106f53b8ed4da1991e19fbcdd6c2ffb65368`.
- Title: `contract: add controlled offline judge capability and PREVIEW_READY`.
- Its file list includes `core/pipeline.py`, `infra/llm.py`, `core/types.py`,
  `core/worker.py`, `core/dispatch.py` and `PROJECT_SPEC.md`.
- Its description reports GO-C1 OFFLINE CONTRACT-CHANGE authorization and requires
  independent security review before Coordinator acceptance.

F-04 directly requires `infra/llm.py`; F-01/F-02 concern the processing call graph rooted
in `core/pipeline.py`. These overlap the open judge C1 implementation. The diagnostic
only cleared the earlier, merged PR #66; that does not clear ownership against PR #68.
The C1 work is the relevant visible candidate for Mac Phase C; its exact mapping to that
phase needs Coordinator confirmation. File overlap itself is verified. No textual merge
conflict or authorization to resolve ownership is claimed.

## Coordinator handoff

Problem: active ownership overlap in shared Core/Infra files, plus unavailable implementation
AC1–AC7. Impact: code changes and complete acceptance validation cannot safely proceed under
the explicit STOP condition.

Coordinator action needed: assign the overlapping files or provide an integration order with
Mac Phase C/PR #68, and supply the referenced implementation Task Contract with file scope
and AC1–AC7. Trello approval is already waived and is not a dependency.

After resolution, resume F-01/F-02 before F-03/F-04, add synthetic regressions, run the
approved validation, self-review and secret scan, then commit/push and open a PR to `dev`.
Do not increase processing budget, change policy/schema/runtime contract, access or modify
Set A/B or Gold/historical evaluation, call application LIVE/provider APIs, merge, deploy,
or mark DONE.

## Validation and limits

- Preflight: remote SHA, branch, tracked working tree and open PR file lists verified.
- Production code/tests: unchanged; implementation and AC1–AC7 validation **NOT RUN**.
- Application LIVE/provider calls: **0**. Git/GitHub metadata reads only.
- Evaluation inputs, Gold and historical evaluation: not read or modified.
- Self-review: report records a preflight STOP, not implementation success or acceptance.
- Commit/push/PR: not performed; authorization makes these conditional on passing validation
  and a clean secret scan. This local report is the handoff artifact pending resolution.
