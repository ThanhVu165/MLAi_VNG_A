# P0 CORE-RELIABILITY-DIAGNOSTIC — evidence report

## Handoff metadata

- Work label: `P0 CORE-RELIABILITY-DIAGNOSTIC` (cardless).
- Authorization: Coordinator GO for read-only Core reliability investigation, isolated
  offline probes and this evidence report. No authorization to change Core, Policy, Guard,
  LLM/runtime contracts, evaluation data, LIVE configuration, deployment or merge.
- Owner: Trung Nam — Lenovo, Core Reliability Research–Review Owner.
- Repository: `ThanhVu165/MLAi_VNG_A`.
- Verified baseline: `dev@e57d04708f77afe7cbfc3493fd57fbdb3f8cdcbd`.
- Reference supplied in the clarified brief: the same SHA.
- Branch: `codex/core-reliability-diagnostic-cardless`.
- Mode: read-only source inspection plus synthetic offline probes against temporary SQLite.
- LIVE/API calls: **0**.

## Preflight

- The original investigation fetched `origin/dev` at
  `e57d04708f77afe7cbfc3493fd57fbdb3f8cdcbd`. Correction preflight on 2026-10-15
  fetched current `origin/dev@3a36a2fd1513a7c3afea0bb98c417aaceb1cb3d8`; the intervening
  change was only merged PR #66.
- PRs #63, #64, #65 and #66 were merged. PR #66 changed only
  `tests/test_judge_new_input_offline.py` and
  `reports/sprints/JUDGE_NEW_INPUT_CANDIDATE_20261015.md`; it did not own or modify a
  production Core/Infra file examined here.
- PR #67 remained open, mergeable, based on `dev`, and its remote head matched the reviewed
  head `a240a2f8cc1cd58d403783a6b91911d6a6b986d7`. The correction branch and working tree
  were clean before the probe was restored.
- The prior UI branch was clean. This branch was created directly from verified
  `origin/dev`; no reset, clean, stash, rebase, force-push, clone or worktree was used.
- Ignored local caches and the existing `.venv` were preserved. No M7 artifact was edited.
- Trello showed Trung Nam as final reviewer, not owner, on the in-progress M5-T03 study.
  This evidence-only diagnostic does not touch its study files, data or sessions.

## Method and evidence boundary

The investigation used the public sanitized M4-T02 report, the source at the verified
baseline, existing offline regression tests, and synthetic inputs. It did not read raw Set A,
Set B, private Gold, provider payloads, private ledgers or real email. Consequently, this
report can prove call-graph defects and deterministic routing behavior, but it cannot assign a
private semantic rationale to an individual M4 case.

Root-cause confidence is reported as:

- **VERIFIED:** reproduced or determined directly from source and an offline probe.
- **SUPPORTED, NOT VERIFIED PER CASE:** consistent with sanitized aggregate evidence and
  reproduction, but the private per-case terminal event was not read.
- **NOT VERIFIED:** would require a sanitized reproducer, private evidence authorization or a
  new scoped implementation investigation.

## AC1 — actual pipeline, timeout and retry trace

| Stage | Actual implementation | Provider use and failure behavior |
|---|---|---|
| R0 Intake | `core/pipeline.py:489-501` | Validates and persists intake; no provider call. |
| R1 Sanitization | `core/pipeline.py:502-526` | Input guard may route unsupported language to `OUT_OF_POLICY`; no provider call. |
| R2 Extraction | `core/pipeline.py:527-536`, `core/extract.py:280-368` | One provider call normally; domain validation retries once, so up to two successful provider responses may be consumed. Provider or validation failure becomes technical error. |
| R3 Decision lock | `core/prepolicy.py:16-28` | Deterministic lock from extracted authority flags. |
| R4 Retrieval/selection | `core/pipeline.py:550-561`, `core/retrieval.py:53-112` | A provider call selects evidence when candidate chunks exist. Invalid IDs/shape raise technical errors. |
| R5 Evidence validation | `core/evidence.py:39-86` | Deterministic checks collapse failures to one `EvidenceStatus`, using the first failure. |
| R6 Policy | `core/pipeline.py:574-597`, `core/policy_engine.py:187-212` | Deterministic first-match YAML decision; policy/config errors become `TECHNICAL_ERROR`. |
| R7 Output | `core/pipeline.py:598-613,685-690` | One reply or escalation-card call. Multi-intent uses reply **and** card calls (`core/question_gen.py:185-247`). Invalid card basis requests one additional repair call (`core/question_gen.py:140-163`). |
| R8 Guard | `core/pipeline.py:616-662,692-710` | Ground Guard downgrades an unsafe draft to P04/`FACT_UNRESOLVED`. Question Guard can regenerate once, then uses deterministic fallback (`core/question_guard.py:226-275`). |
| R9–R14 | `core/pipeline.py:663-725` | Queue/send state and persisted final result; no additional processing provider call. R11 is a separate resume lifecycle. |
| Worker | `core/worker.py:267-310` | Calls the same `process_case`; `ERROR` marks the job failed. It does not retry mutations or silently turn technical failure into business escalation. |

### Budget and timeout mechanics

- `process_case` opens `case_call_budget(LLM_PROCESSING_MAX_ATTEMPTS)` at
  `core/pipeline.py:460`; settings define processing=3, resume=1, maximum=4 and case
  deadline=60 seconds at `infra/settings.py:64-72`.
- The context stores an attempt counter and a monotonic deadline
  (`infra/llm.py:42-65`). Before each provider request, `_attempt_timeout` truncates the
  remaining wall time to an integer, decrements one attempt, and caps the request at 30
  seconds (`infra/llm.py:68-76`).
- `_call_live` permits at most one retry and disables SDK retries
  (`infra/llm.py:224-226,456-460`). Successful requests, transient retries, R2 validation
  retries, basis repair and question regeneration all consume the same counter.
- Attempt exhaustion and wall-clock exhaustion both raise `TimeoutError` with the same text
  at `infra/llm.py:72-74`. Telemetry records both as
  `stop_reason="case_budget_or_deadline"` (`infra/llm.py:271-279,388`). The returned user-safe
  error says the provider did not respond even when no request started
  (`infra/llm.py:281-309`).
- A pre-request budget/deadline block is classified transient, but `will_retry` is false
  because no request started. The loop nevertheless makes a second skipped iteration before
  returning. The probe observed two skipped records and zero additional provider calls.

## Findings

| ID | Severity | Status / confidence | Evidence and impact | Minimal direction |
|---|---|---|---|---|
| F-01 | P0 | **VERIFIED / high** | The normal processing cap is three, while a valid multi-intent path requires R2 + R4 + R7 partial reply + R7 escalation card. The fourth call is blocked before the provider; the whole case becomes `ERROR/TECHNICAL_ERROR`. Offline probe reproduced this with three successful provider calls and 59.7 seconds still remaining. New emails combining routine information with an authority request are affected. | Make the required processing path fit the approved lifecycle budget; do not merely relabel the error or retry the case mutation. |
| F-02 | P0 | **VERIFIED / high** | An R2 semantic-validation retry consumes a second successful provider response (`core/extract.py:290-353`). R4 then consumes the third attempt and mandatory R7 generation is blocked. Probe reproduced `TECHNICAL_ERROR` after three successful calls. | Reserve capacity for the mandatory terminal step or remove a provider-dependent intermediate/retry. This touches the call-budget contract and needs Coordinator/Core-owner approval. |
| F-03 | P1 | **VERIFIED / high** | A valid R7 card response with an invalid/non-verbatim `basis` starts repair (`core/question_gen.py:149-163`). After R2 and R4 there is no processing attempt left. Probe observed the primary R7 provider success, no repair provider request and a propagated `ValueError`. | Use a deterministic safe card/basis fallback when the optional repair cannot run, or redesign the budget. Preserve the original policy decision and expose degraded-card telemetry. |
| F-04 | P1 | **VERIFIED / high** | Budget exhaustion and true 60-second deadline exhaustion share `TimeoutError`, user text and telemetry reason. A pre-request block also produces two skipped attempt records although `will_retry=false`. This prevents precise attribution of the five M4 failures from the public evidence. | Split attempt-exhausted and deadline-exhausted reason codes/exceptions and terminate immediately when no request started. |
| F-05 | P0 safety | **VERIFIED mechanics; semantic cause NOT VERIFIED** | M4A-PT-012 reached P05/AUTO_REPLY. Code can reach P05 only when R3 has no authority lock and R5 supplies no earlier P02/P03 condition (`policies/policy.yaml:3-30`). Ground Guard can reject unsupported output claims, but it does not reconstruct a missing authority/out-of-policy/fact classification (`core/ground_guard.py:188-234`). Therefore the deterministic route is explained; whether R2, R4 or the Gold expectation caused this specific miss cannot be determined without prohibited private rationale. | HOLD policy/prompt tuning. First create an approved sanitized synthetic reproducer for the same decision boundary, then fix the earliest verified semantic stage. |
| F-06 | P1 quality | **VERIFIED structure; per-case mapping NOT VERIFIED** | `validate_evidence` chooses one status from the first failed check (`core/evidence.py:39-70`). Policy P02 groups no source, authority content, conflict and unsupported domain ahead of P03 fact/scope failures (`policies/policy.yaml:3-29`). This architecture can collapse distinct stop rationales into `OUT_OF_POLICY`, consistent with M4A-PT-009/013/017/018 actual P02 mismatches. Public evidence does not reveal which competing condition applied to each case. | Require a Coordinator-approved stop-precedence matrix and synthetic cases before changing P02/P03 priority or evidence status representation. |

## AC2 — classification of the five M4 technical errors

The sanitized report identifies the five cases and states that all recorded provider attempts
were successful. It does not publish each case's terminal step or skipped-attempt event.

| Case | Reported latency | Safe classification | Exact terminal cause |
|---|---:|---|---|
| M4A-PT-004 | 13,136.742 ms | `ERROR / TECHNICAL_ERROR`; provider-started attempts succeeded; business route/stop/rule correctly excluded from scoring | **NOT VERIFIED per case** |
| M4A-PT-005 | 13,752.271 ms | same | **NOT VERIFIED per case** |
| M4A-PT-006 | 13,416.484 ms | same | **NOT VERIFIED per case** |
| M4A-PT-015 | 10,674.150 ms | same | **NOT VERIFIED per case** |
| M4A-PT-016 | 8,406.311 ms | same | **NOT VERIFIED per case** |

All five reported latencies are far below the configured 60-second case deadline. Together
with 52/52 provider successes and the three reproductions, attempt-cap exhaustion after a
successful upstream response is the best-supported explanation. It remains
**SUPPORTED, NOT VERIFIED PER CASE** because the private provider-attempt ledger was not read.
The public label “case deadline” cannot distinguish counter exhaustion from elapsed-time
exhaustion in the current implementation.

## AC3 — escalation correctness without private Gold inference

### Deterministic route table

Policy is first-match:

1. P01: any extracted authority lock → `ESCALATE/AUTHORITY_REQUIRED`.
2. P02: no authoritative source, authority-only content, conflicting sources or unsupported
   domain → `ESCALATE/OUT_OF_POLICY`.
3. P03: fact missing or scope mismatch → `ESCALATE/FACT_UNRESOLVED`.
4. P04: content guard failure → `ESCALATE/FACT_UNRESOLVED`.
5. P05: everything else → `AUTO_REPLY`.

Technical LLM/parse/timeout inputs bypass these business routes and return
`Decision.ERROR`, `rule_id=TECHNICAL_ERROR` (`core/policy_engine.py:176-191`). Pipeline
exceptions are persisted fail-safe as `CaseStatus.ERROR` (`core/pipeline.py:726-770`).

### What the M4 aggregate supports

- M4A-PT-012 proves that upstream structured inputs presented “no authority lock + acceptable
  evidence” to R6, because P05 is otherwise unreachable. It does not prove why those inputs
  were semantically wrong.
- The four reported stop/rule mismatches with actual P02 are consistent with the broad P02
  bucket and first-failure evidence reduction. Their expected private rationale is not inferred.
- Question Guard changes card wording/options, not the policy decision or escalation type.
  Ground Guard can downgrade an AUTO_REPLY draft only after R6/R7 and only for its four content
  checks. Neither guard repairs an incorrect R2 authority flag or R5 evidence status.
- Existing `test_no_over_escalation` and `test_no_fail_open` passed in the focused suite. The
  ordinary-path and technical fail-safe invariants therefore remain intact at this baseline,
  while M4 shows a narrower semantic boundary remains unresolved.

## Offline Probe Reproducibility & Evidence

### Common execution boundary

The correction restored the exact temporary driver from the original Codex execution record,
added only an outbound `socket.create_connection` failure guard, and reran it. The driver SHA-256
was `D33EFF3BC5FABA816C4634515DC644B8857440F31CCF0AF486EDD88B19934BFA`.
It remained under ignored `.codex_tmp/` and was removed after evidence checks; it is not a
production test or tracked artifact.

- Runtime: Windows PowerShell, repository `.venv`, Python 3.11, UTF-8 mode.
- Exact executed command:
  `$env:PYTHONPATH='.'; .venv\Scripts\python.exe -X utf8 .codex_tmp\core_reliability_probe.py 2>&1 | Tee-Object -FilePath .codex_tmp\core_reliability_probe.log`.
- Environment set by the driver: `APP_MODE=private`, `LLM_MODE=live`, `LLM_CACHE=0`,
  `LLM_PROVIDER=openai`, `OPENAI_MODEL=offline-model`, and a non-secret placeholder API key.
  The configured case deadline was 60 seconds, request timeout cap 30 seconds, processing
  attempt budget 3, and wrapper retry limit 1.
- This was deliberately `LLM_MODE=live`, not cassette replay. `call_json()` therefore entered
  `_run_mode()` and `_call_live()`. Every allowed provider response came from a
  `unittest.mock.patch.object(llm, "_request_openai", ...)` double. The double returned
  `LLMResult` objects via `llm._success`; the OpenAI client was never invoked. The socket guard
  would fail an attempted outbound connection. Cache was disabled, data used
  `synthetic@example.invalid`, and pipeline probes used a seeded temporary SQLite file.
- Evidence was counted from the emitted `provider_attempt` records: an
  `llm_provider_attempt` means a request crossed the `_request_openai` boundary; an
  `llm_provider_attempt_skipped` means `_attempt_timeout()` blocked it before that boundary.
  A successful request is therefore distinct from a skipped logical retry.

### Probe 1 — Multi-intent budget exhaustion

- **Objective and path:** reproduce the four-call multi-intent path through
  `process_case()` → `extract_facts()` → `retrieve_evidence()` →
  `generate_multi_intent_card()` → `generate_reply()` → `generate_escalation_card()`.
- **Double:** returned valid synthetic R2 extraction, R4 chunk selection and R7 partial reply.
  A fourth response for the escalation card existed in the double but was unreachable.
- **Expected / actual:** expected three provider requests to start and the fourth logical call
  to be blocked. Actual telemetry was 3 started, 3 successful, 2 skipped wrapper iterations.
  Started steps were `R2_extract`, `R4_select`, `R7_generate`; both skipped records were
  `R7_question`, with attempt counter `0 → 0` and
  `stop_reason=case_budget_or_deadline` while about 59.7 seconds remained.
- **Observed result:** pipeline fail-safe returned `status=ERROR`, `decision=ERROR`,
  `rule_id=TECHNICAL_ERROR`, and no card. This is attempt exhaustion after successful provider
  requests, not a business escalation and not a wall-clock deadline.
- **Evidence reference:** driver SHA and exact command above; source paths
  `core/pipeline.py:460,598-613,685-710`, `core/question_gen.py:185-247`, and
  `infra/llm.py:68-76,224-313`.
- **Conclusion:** **VERIFIED** synthetic reproduction.

### Probe 2 — R2 validation retry exhaustion

- **Objective and path:** show that local R2 validation can consume another logical provider
  call before R4 and mandatory R7: `process_case()` → `extract_facts()` validation loop →
  `retrieve_evidence()` → `generate_reply()`.
- **Double:** first R2 response contained conflicting duplicate `cohort` facts and was rejected
  locally with `FACT_DUPLICATE_CONFLICT`; the second R2 response and R4 selection were valid.
- **Expected / actual:** expected R2 + R2 retry + R4 to start, then R7 to be blocked. Actual
  telemetry was 3 started, 3 provider successes, 2 skipped wrapper iterations. Started steps
  were `R2_extract`, `R2_extract`, `R4_select`; both skipped records were `R7_generate`, with
  attempt counter `0 → 0` and `stop_reason=case_budget_or_deadline` while about 59.8 seconds
  remained. The first provider request succeeded even though domain validation failed later.
- **Observed result:** `ERROR/TECHNICAL_ERROR`; no business route replaced the technical
  failure. This is attempt exhaustion caused by a validation retry, not provider failure.
- **Evidence reference:** driver SHA and exact command above; source paths
  `core/extract.py:280-368`, `core/pipeline.py:527-536,550-561,598-613`, and
  `infra/llm.py:68-76,224-313`.
- **Conclusion:** **VERIFIED** synthetic reproduction.

### Probe 3 — R7 basis repair exhaustion

- **Objective and path:** exercise `generate_escalation_card()` with a successful primary
  response whose `basis` quote is not a substring of its evidence, forcing
  `R7_question_repair` through `call_json()` and `_call_live()`.
- **Double:** two explicit preliminary calls consumed two attempts; the third request returned
  an otherwise valid card with an invalid synthetic quote. No repair response could be
  requested.
- **Expected / actual:** expected 3 started requests and a pre-request repair block. Actual
  telemetry was 3 started, 3 successful, 2 skipped wrapper iterations. Started steps were
  `pre-0`, `pre-1`, `R7_question`; both skips were `R7_question_repair`, with attempt counter
  `0 → 0` and `stop_reason=case_budget_or_deadline` while about 59.9 seconds remained.
- **Observed result:** `generate_escalation_card()` raised `ValueError` after the wrapper
  returned its safe timeout failure. This direct function probe did not create a
  `PipelineResult`, so it makes no claim of a business escalation or `TECHNICAL_ERROR` result;
  `process_case()` would be the layer that maps such propagation to its fail-safe.
- **Evidence reference:** driver SHA and exact command above; source paths
  `core/question_gen.py:98-163` and `infra/llm.py:68-76,224-313`.
- **Conclusion:** **VERIFIED** synthetic reproduction.

### Probe 4 — Attempt cap vs wall-clock deadline

- **Objective and path:** distinguish true deadline exhaustion from the attempt-cap cases by
  executing `case_call_budget(3)` and `call_json()`/`_call_live()`, then moving only the
  in-memory monotonic deadline into the past before a second logical call.
- **Double:** the first request returned success. The deadline was then forced expired; the
  second request could not cross `_request_openai`.
- **Expected / actual:** expected 1 started successful request, 2 attempts still available,
  and two skipped wrapper iterations for the expired second call. Actual telemetry matched:
  1 started, 1 successful, 2 skipped; attempt counter was `3 → 2` for the first request and
  remained `2 → 2` for both skips. Both skips nevertheless used
  `stop_reason=case_budget_or_deadline`.
- **Observed result:** first `LLMResult.ok=True`, second `False`, provider request count stayed
  1. This is wall-clock deadline exhaustion with remaining attempts, proving the shared reason
  code cannot distinguish it from attempt exhaustion.
- **Evidence reference:** driver SHA and exact command above; source paths
  `infra/llm.py:42-76,200-313,338-407`.
- **Conclusion:** **VERIFIED** synthetic reproduction.

These probes establish reproducible mechanics only. They do not identify the terminal branch
of any individual M4 case, do not use held-out evaluation data, and do not change the historical
findings or their per-case confidence limits.

## AC5 — proposed minimal remediation plan (maximum three changes)

### 1. Make required R7 completion fit the approved attempt budget

- Root cause: F-01/F-02/F-03; required and optional calls compete inside a three-attempt
  processing budget.
- Proposed scope: `core/pipeline.py`, `core/extract.py`, `core/question_gen.py`,
  `core/question_guard.py`, `infra/llm.py`, targeted new tests. No schema/Gold change unless a
  persisted lifecycle budget is chosen.
- Design constraint: preserve “technical failure is not business escalation” and never
  auto-reply from a fallback. A deterministic card fallback may preserve an R6 escalation only
  when R6 already made that business decision; this needs explicit safety review.
- AC: every allowed call path has a documented worst-case attempt count; multi-intent,
  R2-validation-retry and invalid-basis synthetic cases terminate predictably; no fourth
  provider request occurs under a cap of three; `test_no_fail_open` and
  `test_no_over_escalation` pass.
- Tests: call-path matrix at `process_case`, successful-provider/failed-validation cases,
  multi-intent, basis repair, question fallback, worker persistence and R11 reservation.
- Effort/risk: medium; high safety impact because routing output and lifecycle budgeting meet.
- Suggested owner: Runtime/Core owner, with independent safety reviewer.
- Contract: **Coordinator GO required.** Increasing attempts or changing the 3+1 allocation is
  a runtime-contract change; a provider-free fallback design may avoid a contract change but
  still changes Core behavior after freeze.

### 2. Separate attempt exhaustion from wall-clock deadline exhaustion

- Root cause: F-04.
- Proposed scope: `infra/llm.py`, `infra/provider_observability.py`, provider/budget tests.
- AC: distinct safe reason codes for attempt cap and deadline; `will_retry=false` returns after
  one skipped iteration; no provider call starts; client text remains safe; telemetry contains
  no prompt/PII/secret.
- Tests: exhausted counter with positive remaining time, expired deadline with remaining
  attempts, real transient timeout/retry, sanitized observability.
- Effort/risk: small; low business risk, medium diagnostics compatibility risk.
- Suggested owner: Infra/Runtime owner.
- Contract: no `core/types.py` change is inherently required, but Coordinator GO is required
  because post-freeze runtime behavior and telemetry semantics change.

### 3. Reproduce the semantic decision boundary before any P01/P02/P03/P05 change

- Root cause: F-05/F-06 is not established per case.
- Proposed scope for the next investigation: new synthetic regression tests first; only the
  earliest proven source among extraction, evidence classification or policy priority may be
  changed. Do not use raw M4 Gold/payload.
- AC: sanitized cases reproduce one false P05 and each disputed stop boundary; authority,
  no-source, unsupported-domain, conflict, missing-fact and scope-mismatch remain distinct;
  routine inputs still AUTO_REPLY; technical faults remain ERROR.
- Tests: decision-lock matrix, evidence multi-failure precedence, Ground/Question Guard
  invariants and new-input E2E regression.
- Effort/risk: investigation small, implementation unknown; high safety and evaluation risk.
- Suggested owner: Core/Policy owner with independent evaluation reviewer.
- Contract: **HOLD implementation** until Coordinator supplies/approves sanitized non-Gold
  reproducers and explicit policy/routing scope. Any priority/contract change requires GO.

## Dependency with Mac New-Input candidate

PR #66 is evidence/tests only and has no current file conflict with this report. Its 12
controlled new-input tests are relevant downstream regression evidence, but they must not be
edited or treated as accepted until that PR is reviewed/merged. A Core remediation should rebase
on the then-current `dev` and run the accepted new-input suite. This diagnostic neither blocks
nor approves public new-input capability.

## Validation

Environment: Windows and Python 3.11 `.venv`. Historical regression tests used
`LLM_MODE=replay`, `LLM_CACHE=0` and an empty API key. The corrected probes separately used
`LLM_MODE=live`, cache disabled, a placeholder key, a patched `_request_openai`, an outbound
socket guard and temporary SQLite, as documented above. Replay did not produce the probe
evidence.

| Command/check | Result |
|---|---|
| Exact isolated probe command and SHA documented above | **PASS (correction rerun)** — four scenarios reproduced; 10 mocked provider-boundary requests succeeded, 8 pre-request attempts were skipped, external provider/network calls 0 |
| `.venv\Scripts\python.exe -m pytest -q tests/test_llm_budget.py tests/test_policy_engine.py tests/test_provider_observability.py tests/test_semantic_validator_compat.py tests/test_guards.py` | **NOT RUN for correction** — no production code changed; preserve historical result at previous SHA: 183 passed in 5.66s |
| Existing `test_no_over_escalation` / `test_no_fail_open` (included above) | **HISTORICAL PASS at previous SHA; NOT RUN for correction** |
| Static file/function/line inspection at baseline SHA | **PASS** |
| Official Set A rerun | **NOT RUN — prohibited; no private payload or Gold accessed** |
| Set B access/evaluation | **NOT RUN — prohibited and preserved for M7** |
| External LIVE/API/provider execution | **PASS — 0** |

Correction report checks performed before handoff: report consistency against the captured
provider-attempt records, command/configuration cross-check, `git diff --check`, report-only
scope, scoped credential/private-key and PII scan, private-evaluation marker scan, UTF-8/NFC
readback and owner self-review.

## AC1–AC7

| AC | Result | Evidence |
|---|---|---|
| AC1 pipeline/deadline/retry trace | **PASS** | Actual R0–R14 and 3+1/60s/30s mechanics traced with lines above. |
| AC2 five technical errors classified | **PASS with explicit limitation** | All five classified as technical/non-business; aggregate cause supported; exact per-case terminal step marked NOT VERIFIED. |
| AC3 route/stop/rule analysis | **PASS** | Deterministic mechanics and structural ambiguity recorded without private Gold inference. |
| AC4 offline probes | **PASS** | Four isolated synthetic scenarios with exact rerun command, environment, boundary counts, stop reasons and evidence references; no network or production data. |
| AC5 maximum three minimal fixes | **PASS** | Three scoped proposals with AC/tests/risk/owner/dependency/approval. |
| AC6 no production/evaluation change | **PASS** | Only this report is tracked; probe was temporary and ignored. |
| AC7 evidence, validation, self-review, handoff | **PASS candidate** | Evidence correction and self-review complete; correction commit, PR head and final SHA are supplied in handoff. |

### Evidence-correction AC1–AC7

| Correction AC | Result | Evidence |
|---|---|---|
| AC1 four-probe evidence | **PASS** | All four probes rerun and marked VERIFIED with actual outcomes. |
| AC2 command/environment/isolation accuracy | **PASS** | Exact command, Python/runtime settings, `LLM_MODE=live`, cache state, provider double and socket guard recorded. |
| AC3 count provenance | **PASS** | Started/successful/skipped counts, attempt counters and stop reasons came from emitted `provider_attempt` records. |
| AC4 preserve historical findings | **PASS** | F-01–F-06 conclusions and confidence were not expanded. |
| AC5 evidence-only scope | **PASS** | Only this report changed; temporary probe/log removed; source, tests, fixtures, contracts, Gold and evaluation untouched. |
| AC6 per-case attribution boundary | **PASS** | Exact terminal causes for the five M4 cases remain NOT VERIFIED per case. |
| AC7 correction handoff | **PASS candidate** | Validation and owner self-review complete; correction commit SHA and updated PR head are supplied in handoff. |

## Self-review, remaining uncertainty and recommendation

Self-review checked source references, provider-attempt arithmetic, distinction between
reproduction and M4 attribution, fail-safe semantics, Gold/privacy boundary, PR #66 dependency,
file scope and credential exposure.

Remaining uncertainty:

- Exact terminal step and exhaustion type for each of the five M4 cases remain unavailable in
  public evidence.
- The semantic reason M4A-PT-012 should have escalated is intentionally not inferred.
- Which precedence should resolve simultaneous evidence failures is a policy decision, not a
  diagnostic fact.

Recommendation: **GO, conditionally, for a separately authorized Core reliability
implementation addressing F-01–F-04; HOLD policy/routing changes for F-05–F-06 until sanitized
reproducers and explicit Coordinator scope exist.** Do not rerun official Set A, read Set B,
increase limits, merge or deploy from this diagnostic.
