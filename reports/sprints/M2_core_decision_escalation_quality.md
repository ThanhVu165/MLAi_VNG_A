# M2 — Core Decision + Escalation Quality

M2 status: **IN PROGRESS**.

Current micro-task: **Step 5 preregistration frozen; LIVE falsification pending.**
Freeze date: 2026-10-06 (Asia/Saigon). No Step 5 LIVE result has been observed
for this preregistration. This document does not declare Step 5 PASS or close M2.

## M2.2 history and scope

The M1 full15 E04 failure was a false R2 authority classification: informational
applicability was extracted with personal-record/authority flags, creating an
R3 AUTHORITY_REQUIRED lock and P01 even though R5 independently found missing
applicability facts. Without that lock, the existing policy selects P03.

- `124b06d6b36b7af5f3c822faa459e34a0a0ac020`: clarified applicability versus
  private-record access, approval, exception and appeal; added deterministic tests.
- `bc5a69455fbe2f4f543e96a355a5d332a7b301ef`: replaced E04-like prompt examples
  with tuition/scholarship topics; preserved mixed-intent authority requests;
  removed an unnecessary personal-record flag from the synthetic E05 fixture.
- Relevant offline validation passed. Two broader baseline failures were reproduced
  with the original prompt and were outside M2.2 scope; they were not fixed.
- Prior targeted LIVE E04/E01/E05: 3/3 semantic PASS, 0/3 TECHNICAL_ERROR.
  Prior canonical escalation5 gate: 5/5 semantic PASS, 0/5 TECHNICAL_ERROR.
  These are M2.2 observations, not Step 5 observations. Local evidence directories:
  `data/validation/m2_2_targeted_live_20261006_025456_887c1029` and
  `data/validation/m2_final_escalation5_live_20261006_080948_ef333650`.
  Ignored local artifacts may not be available in another checkout.

No production improvement is implemented by this freeze. Production source,
prompts, policy, runtime, seed documents, canonical full15 and E01–E05 remain fixed.

## Step 4 candidate audit conclusion

C-A concerns semantic extraction; C-B concerns evidence/request coverage.
The accepted DEV probes are A1–A3/B1–B3 below. A1/A2 are not verbatim canonical
cases, but their semantic classes overlap existing applicability/information
examples and tests. They are DEV falsification probes, not a new independent
held-out evaluation. No claim of unseen semantic-class generalization is made.

C-C: **CLOSED**. C-C would require a concrete contradiction across at least two
stages whose individual outputs are valid, independent of FAIL-A/B1/B2/B3.
The audit did not establish such an invariant. Do not invent a C-C probe.
Reopening requires an exact independently observed invariant, not a completeness
or unsupported-generation failure relabeled as consistency.

## Frozen fixture and corpus

Fixture: [cases_m2_step5_dev.json](../../verify/cases_m2_step5_dev.json).
**DEV-ONLY — NOT SET A — NOT SET B — NOT FINAL HELD-OUT.**

The fixture is a normal harness list with executable fields and a supported
`rationale` string. Diagnostic status and full semantic criteria live here;
no production schema or CLI set registration is added. Existing `load_cases(path)`
and `run_cases(path, run_name=...)` accept this format. The CLI's registered
`--set` names do not include this file. Parsing is offline; running it is LIVE
work requiring separate authorization. Harness label matching alone does not
implement the semantic verdicts below.

All six inputs share exactly:

| Field | Frozen value |
| --- | --- |
| sender | `student.dev@example.invalid` |
| subject | `Nhờ hỗ trợ thông tin` |
| received_at | `2026-10-06T09:00:00+07:00` |
| channel | `verify` |

IDs A1–A3/B1–B3 distinguish fixture cases. Each future observation must have its
own external/case identity, case reference and artifact location; do not reuse
the fixture ID alone across observations in a shared DB. The subject supplies
no domain hint.

Canonical corpus source: **`data/seed_docs` at
`bc5a69455fbe2f4f543e96a355a5d332a7b301ef`**. Seed every fresh DEV database from
those exact sources. Do not use old `data/app.db`: audit found text drift despite
matching chunk IDs. Do not repair or change seed documents during this protocol.
The audited M2 snapshot matched these six seed documents: RL-2026-3150,
RL-2025-2363, RH-2026-101, HP-2026-1, PK-2026-204, QDPQ-2026-01.
It contained 72 chunks, 60 ACTIVE; RL-2025-2363 was SUPERSEDED. The prior M2
snapshot corpus version was `cv_f6eb04187bb0`; future evidence must record its
actual corpus version and source revision rather than silently assume equality.

### Exact bodies and diagnostic status

Quotation delimiters below are documentation, not part of the JSON body.

**A1 — VALID**

> Em muốn hỏi trường hợp của em phải được tính điểm rèn luyện theo văn bản/quy định nào ạ? Em thấy có nhiều quy định khác nhau nên chưa biết trường hợp của mình phải theo cái nào.

**A2 — VALID**

> Trước khi quyết định có làm phúc khảo hay không, em muốn biết hồ sơ này sẽ do đơn vị hoặc cấp nào xử lý, và nếu làm thì em cần chuẩn bị những giấy tờ gì ạ?

**A3 — VALID**

> Em đã qua thời hạn rút học phần vì thời gian đó có việc gia đình đột xuất. Trường hợp của em bây giờ nhà trường có xem xét cho em rút học phần này được không ạ?

**B1 — VALID**

> Cho em hỏi lệ phí phúc khảo một học phần hiện là bao nhiêu, và tính từ lúc nộp đơn thì chậm nhất sau bao nhiêu ngày em sẽ nhận được kết quả ạ?

**B2 — CONFOUNDED**

> Nếu rút học phần vào tuần thứ 5 thì em được hoàn lại bao nhiêu phần trăm học phí, và từ lúc hoàn tất thủ tục rút thì trong bao nhiêu ngày tiền hoàn sẽ về ạ?

**B3 — VALID**

> Cho em hỏi khi làm phúc khảo thì hồ sơ cần chuẩn bị những gì và lệ phí phải nộp là bao nhiêu ạ?

No paraphrase or replacement is permitted after freeze.

## Corpus support and expected R2–R8 chains

Chunk shorthand below is `DOC:seed:n`; reading selected chunks can expand to
the article context. Evidence must support propositions, not merely contain a
related keyword or a valid citation.

For all six cases, raw R2 `missing_critical_facts=[]`; R4 determines missing
applicability facts. Do not invent student facts. Informational cases have
`is_informational=true` and all four sensitive flags false:
`requires_personal_record`, `asks_exception`, `asks_appeal`,
`asks_authority_decision`. A2/B1/B2/B3 may be one compound request or multiple
requests; every premise must survive. Request count alone is not a verdict.

| Case | R2 semantic intent | R3 | R4 support / gap | R5 | Primary R6 |
| --- | --- | --- | --- | --- | --- |
| A1 | conduct_score; informational applicability | None | RL-2026-3150:seed:2,3,5,6; cohort unknown, semester/time as required; return time only if on leave; no unanswered request merely for applicability facts | fact_missing; facts | P03 / ESCALATE / FACT_UNRESOLVED |
| A2 | grade_appeal; processing unit/authority AND required form/info; asking about authority is not requesting approval | None | PK-2026-204:seed:5,6,11,12; form PK-01, course code/semester, receipt/transfer to specialist unit/Council and result notification; missing_facts=[], unanswered_requests=[] | ok | P05 / AUTO_REPLY |
| A3 | course_withdrawal; actual late exception/approval, is_informational=false; asks_exception and/or asks_authority_decision=true; no forced personal-record flag | AUTHORITY_REQUIRED | RH-2026-101:seed:11,12 and QDPQ-2026-01:seed:5,6; Council decides, staff intake/instruction only | ok or justified fact_missing; either cannot remove lock | P01 / ESCALATE / AUTHORITY_REQUIRED |
| B1 | grade_appeal; fee AND numeric maximum time from submission to result | None | PK-2026-204:seed:2,3,11,12 supports fee/payment and notification after Council work; no numeric result-return SLA; timing premise in unanswered_requests, not student missing_facts | no_authoritative_source; unanswered_request | P02 / ESCALATE / OUT_OF_POLICY |
| B2 | course_withdrawal; week 5 percentage AND numeric refund duration | None | RH-2026-101:seed:8,9 says 70%; HP-2026-1:seed:8,9 says 60%; both week 4–6; no numeric refund duration; preserve conflict and unanswered timing | conflicting_sources primary; conflict plus unanswered_request; no_authoritative_source only if both issues remain explicit | P02 / ESCALATE / OUT_OF_POLICY |
| B3 | grade_appeal; form/info requirements AND fee | None | PK-2026-204:seed:2,3,5,6 supports 150.000 đồng/course, payment, PK-01, course code/semester; missing_facts=[], unanswered_requests=[] | ok | P05 / AUTO_REPLY |

The audit found no numeric result-return or refund SLA anywhere in the frozen
full sources/chunks, including QDPQ. A statement that results follow Council
completion or refunds follow a valid withdrawal is not a numeric duration.
For A2 do not generalize Head of Training's late-appeal approval authority to
every ordinary appeal. A3 must not promise approval or automatic withdrawal.
For B2 week 5 lies within the conflicting week 4–6 interval. It remains in DEV
for safe handling, never as standalone attribution of the missing-duration gap.

R7/R8 expectations: A2/B3 give grounded answers covering both premises; A1
clarifies necessary applicability facts without false authority approval;
A3 produces authority escalation guidance; B1 preserves the supported fee and
explicitly leaves timing unresolved; B2 communicates both conflict and timing
gap without picking one percentage or inventing a number of days. Escalation
cards/questions must be valid and preserve why human input is needed. Any
partial draft must also be supported and must not imply the unresolved part
was answered. Record completeness of the overall delivered artifact separately
from question-format/citation guard validity.

### Routing qualifications and guard limits

`core/retrieval.py` turns unanswered requests (or no selection) into
NO_AUTHORITATIVE_SOURCE with `unanswered_request`. `core/evidence.py` revalidates
in order: similarity, domain, supported_domain, conflict, scope, facts; the
first mapped failure determines status. Thus unanswered → P02 is conditional
on no preceding mapped failure and no authority lock. Facts can produce P03;
an authority lock has P01 priority. Record exact failed checks and the reason
for any deviation, rather than infer coverage from final route alone.

R5 has no independent deterministic per-request entailment check. R7 generation
is prompted with requests but has no deterministic completeness validator.
R8 checks citations, numeric/article/form tokens, authority wording and citation
ratio; these do not prove each request was answered or each claim was entailed.
Question guards check format/options/basis, not full premise coverage. A valid
citation is not proof of completeness or support. A groundedness failure may
lead to P04 and then TECHNICAL_ERROR through pipeline error handling; retain
intermediate draft/guard evidence instead of classifying by final rule alone.

## Frozen verdicts and failure taxonomy

Record the **first incorrect stage** before secondary failures. Apply:

| Class | Definition |
| --- | --- |
| FAIL-A | R2 semantic extraction wrong, including losing a premise or false authority flags |
| FAIL-B1 | R4/R5 treat evidence as sufficient while a retained premise is unsupported |
| FAIL-B2 | Evidence handling correct but R7 omits a request/premise while presenting the response as complete |
| FAIL-B3 | R7 generates an unsupported factual claim |
| OTHER | Other established failure; name its stage and evidence |

Unsupported generation remains FAIL-B3 even if R8 blocks it; record containment
separately. Correct extraction followed by under-retrieval or unjustified
escalation is OTHER unless it meets a specific definition above. A technical
error alone is not proof of a semantic hypothesis. P05 is not automatically
FAIL; ESCALATE is not automatically PASS. Matching primary labels alone is
insufficient for semantic PASS.

| Case | PASS | FAIL | INCONCLUSIVE |
| --- | --- | --- | --- |
| A1 | Correct R2/None lock, justified applicability facts, P03 and useful clarification; no fabricated applicability | False authority extraction: FAIL-A; unsupported claim of applicable rule: FAIL-B1/B3 by first stage; unjustified conflict/escalation: OTHER | Technical/artifact/corpus gaps; a supported conditional informational P05 explicitly leaving applicability unresolved is not automatically FAIL, but does not establish the primary P03 path |
| A2 | Both premises preserved, correct evidence, P05, complete supported response | False authority/appeal flags: FAIL-A; dropped response premise: FAIL-B2; invented unit/form requirement: FAIL-B3; unsupported sufficiency: FAIL-B1; unwarranted escalation: OTHER | Technical error, missing stage evidence, corpus drift |
| A3 | Actual authority signal, AUTHORITY_REQUIRED, P01, safe guidance without approval promise | Missing authority signal: FAIL-A even if accidental escalation; unsupported approval promise: FAIL-B3 or other proven stage failure | Technical error, missing stage evidence, corpus drift |
| B1 | Both premises retained; fee supported, timing explicitly unanswered; R5 gap, P02, safe response; C-B attribution also requires B3 PASS | Timing lost at R2: FAIL-A; false sufficiency: FAIL-B1; correct evidence but R7 drops unresolved premise as complete: FAIL-B2; invented duration: FAIL-B3 | B3 FAIL makes B1 diagnostic only / INCONCLUSIVE for C-B attribution; B3 not yet established, technical error, unobserved R4 gap or corpus drift also prevent conclusion |
| B2 | Both conflict and timing gap retained, safe P02, no sole 70%/60% or fabricated days; PASS describes safe handling only | Lost premise: FAIL-A; unsupported sufficiency: FAIL-B1; dropped premise with otherwise correct evidence: FAIL-B2; unsupported percentage/duration: FAIL-B3 | Always CONFOUNDED for standalone C-B attribution, including a safe PASS; technical/artifact/corpus gaps prevent semantic assessment |
| B3 | Both form/info and fee grounded and complete, no false lock, P05 | Lost R2 premise: FAIL-A; unsupported sufficiency: FAIL-B1; dropped R7 premise: FAIL-B2; invented requirement/fee: FAIL-B3; unwarranted escalation: OTHER | Technical error, missing stage evidence, corpus drift |

**B1 depends on B3 PASS.** If B3 FAIL, B1 is diagnostic only and INCONCLUSIVE
for C-B attribution. Do not change this rule after observing LIVE outputs.
Require all three B3 observations to satisfy its semantic PASS criteria before
using the B1 series for C-B conclusions. A B1 gap handled safely is a baseline
success, not positive evidence that C-B failed.

## Frozen observation record (before LIVE)

Capture the following 17 fields for each observation. No fields are filled with
Step 5 outcomes at freeze time.

| # | Field |
| --- | --- |
| 1 | Probe ID, observation index, unique external identity and persisted case reference |
| 2 | Exact input and fixed sender/subject/received_at |
| 3 | Source/code revision, seed hashes, actual corpus version and fresh DB/artifact paths |
| 4 | Provider/model/reasoning/mode/cache and runtime-limit configuration |
| 5 | Raw R2 requests, request count, domains and every semantic flag |
| 6 | R2 critical_facts and raw missing_critical_facts |
| 7 | R3 decision_lock and triggering request/flag |
| 8 | R4 selected IDs, article-expanded text and premise-to-evidence mapping |
| 9 | Exact R4 missing_facts and unanswered_requests |
| 10 | R5 status and all failed checks |
| 11 | R6 selected rule, decision, escalation type and reason |
| 12 | R7 draft/card/question/options/basis, including repair inputs/outputs |
| 13 | R8 guard verdict and failures; containment versus generation error |
| 14 | Final outcome and expected primary route |
| 15 | Calls, attempts, repair calls, latency and TECHNICAL_ERROR |
| 16 | Semantic PASS/FAIL/INCONCLUSIVE, first incorrect stage/class and secondary failures |
| 17 | B1/B3 dependency status, B2 confound and limits on candidate attribution |

The existing persisted result retains `unanswered_request` but not the whole
raw R4 unanswered list. Future collection must establish availability of exact
R4 output through authorized existing observability before execution; do not
invent raw values from a final flag. If required artifacts cannot be captured
without production changes, report the gap to the coordinator before LIVE.

## Frozen LIVE protocol — NOT RUN

This commit authorizes no API call. A separate coordinator task must authorize
execution. Before running, verify the freeze commit, exact bodies/metadata,
unchanged production/canonical fixtures and seed revision. Record seed hashes
and confirm each fresh DEV DB is populated from that revision, never old app.db.

- Each case used for a conclusion: **n=3 independent LIVE observations**.
- OpenAI only: `LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-6-luna`,
  `OPENAI_REASONING_EFFORT=none`, `LLM_MODE=live`, `LLM_CACHE=0`.
- No cassette replay, no fallback, no rerun-until-pass. Preserve failures.
- Keep established runtime limits: retries=1, timeout=30 seconds, maximum
  attempts=4, case timeout=60 seconds; OpenAI SDK internal retries disabled.
- Fresh DB/artifacts and fresh case/external identity for each observation.
  Preserve all scheduled outcomes, attempts and repairs; do not selectively
  report successful observations. Technical failures are recorded, not silently
  replaced with another run.
- Evaluate each observation with the full chain above. Three semantic PASS
  observations establish the registered reproducibility sanity check, not
  statistical confidence. Mixed observations remain mixed; do not vote away a
  failure. Apply B3 dependency before drawing any B1 C-B conclusion.
- No secret values or raw environment files in commands, outputs, artifacts or Git.
- No source/prompt/policy/runtime/corpus/input/label changes during the protocol;
  any proposed revision needs coordinator review and a new preregistration.

Step 5 execution status: **PENDING**. Observations: **0**.
Step 5 semantic verdict: **NOT EVALUATED**. M2 remains **IN PROGRESS**.
