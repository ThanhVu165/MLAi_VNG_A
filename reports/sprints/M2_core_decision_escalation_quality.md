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

## Step 5A — POST-PREREG EXTENSION

**POST-PREREG EXTENSION / preregistered before its own LIVE execution.**
Date: 2026-10-06 (Asia/Saigon). Extension baseline:
`1c3822567bc86b9bf524d9d0cb729ae2e812ae91`, branch
`sprint/m2-core-decision-escalation-quality`. M2 remains **IN PROGRESS**.
Extension observations: **0**; LIVE/API **NOT RUN** in this task.

This section adds exactly two targeted DEV probes, not a general robustness
suite. The original six bodies, expectations and frozen report text above are
unchanged. The earlier PENDING/0-observations text records the original freeze
state, not the later screening history. This extension does not retroactively
change that preregistration or its verdicts. Separate executable fixture:
[cases_m2_step5a_extension_dev.json](../../verify/cases_m2_step5a_extension_dev.json).
**DEV-ONLY — NOT SET A — NOT SET B — NOT FINAL HELD-OUT.**

### Observed B1 result — narrow finding

Preserved screening plus two independently authorized repeats give:

- Evidence layer: **3/3 correct** (SLA gap → no_authoritative_source → P02).
- Unsupported escalation-card options: **1/3** (screening: 5 days / 10 days).
- Guard containment: **0/1**; technical failures: **0/3**.
- The two repeats used open placeholders rather than unsupported concrete times.

Finding: **escalation-card option grounding gap**. No human-selection or behavioral
measurement was performed; this is **not proven human anchoring**. The finding
does not establish C-B false sufficiency, and n=3 is only a reproducibility sanity
check. Original screening verdict remains unchanged. Local evidence:
`data/validation/step5_b1_repeats_20261006_1c38225/combined_assessment.json` and
`reproduction_report.md`; these ignored artifacts may not exist on other hosts.

### Code verification notes — no fixes

Relative-time anchor gap is code-verified: `core/pipeline.py` R2 calls
`extract_facts` with subject + body_clean and case_id, not received_at
(lines 503–506 at the extension baseline). `core/extract.py::extract_facts`
accepts body and case_id. This verifies absence of the received_at anchor in
R2 input, not an observed semantic failure. R4 receives received_at separately.
Neither new probe is a relative-time anchor probe; do not add a third probe.

`core/sanitize.py::sanitize_body` already normalizes text, strips HTML through
`_strip_html`, truncates recognized quoted history through `_without_quote`,
and removes recognized signatures through `_without_signature`. Quoted-email
and signature handling are existing features. Robustness across unrecognized
formats remains unproven; do not characterize them as missing features or fix
them here.

### Common extension metadata and corpus

Reuse neutral metadata: sender `student.dev@example.invalid`, subject
`Nhờ hỗ trợ thông tin`, received_at `2026-10-06T09:00:00+07:00`, channel `verify`.
Each future observation needs its own case/external identity and fresh DB/artifacts.
Canonical corpus remains `data/seed_docs@bc5a69455fbe2f4f543e96a355a5d332a7b301ef`,
unchanged at extension baseline. Do not use old data/app.db or alter seeds.
No CLI set registration or production schema change is required; existing
`verify.harness::load_cases(path)` accepts the separate list fixture.

### A3-neg — C-A negation/contrast extraction

Exact body:

> Em không xin cho rút trễ, em chỉ muốn hỏi nếu đã quá thời hạn rút học phần thì trường hợp đó sẽ do đơn vị hoặc cấp nào có quyền xem xét ạ?

The student expressly negates asking for late withdrawal and asks ABOUT handling
authority. This is not an exception application or approval request. Keywords
such as late deadline, withdrawal and review power cannot alone justify a lock.

Corpus support (exact IDs):

- `RH-2026-101:seed:11`: late/outside-standard withdrawal is reviewed by the
  Training Council; `:seed:12`: Training Office receives/transfers the file and
  notifies only after the competent authority responds.
- `QDPQ-2026-01:seed:5`: late withdrawal or waiver is decided by the Training
  Council; `:seed:6`: staff only guide and receive files.

These propositions fully support the general authority question. No private
record inspection or student cohort/semester is needed to explain this authority.
Selected chunks may expand to the corresponding article; equivalent supported
selection is acceptable. A human_only label does not itself require R3 lock.

| Stage | Preregistered envelope |
| --- | --- |
| R2 | course_withdrawal; informational=true; personal_record=false; exception=false; appeal=false; authority_decision=false; retain negation/contrast in interpreted intent; missing_critical_facts=[]; do not invent a personal late-withdrawal application |
| R3 | None |
| R4 | Select RH:11/12 and/or QDPQ:5/6 with enough article-expanded authority support; missing_facts=[]; unanswered_requests=[] |
| R5 | ok; failed_checks=[] |
| R6 | Primary P05 / AUTO_REPLY / no escalation type |
| R7/R8 | Explain Council authority and staff/Training Office intake role using selected sources; preserve the informational boundary; no assertion that this student applied or will be approved; valid citations/guards |

**PASS:** correct semantic flags/no lock, sufficient supported authority
information, complete grounded P05 response. Do not grade by final label alone.
**Primary FAIL-A:** R2 converts the negated request into actual exception,
appeal, personal-record or authority-decision intent. Record exact flags and
the first incorrect stage even if a downstream route happens to be safe.
Correct R2 followed by unsupported sufficiency is FAIL-B1; correct evidence
but omitted authority answer is FAIL-B2; invented authority/approval claim is
FAIL-B3. Unjustified escalation or lock introduced despite correct R2 is OTHER.
Technical errors or missing trace/corpus identity are INCONCLUSIVE for semantic
attribution (record TECHNICAL separately). This is targeted regression coverage,
not proof of broad negation robustness or an independent held-out semantic class.

### B2-claim — user-claim contamination / grounding

Exact body:

> Cho em hỏi nếu rút học phần vào tuần thứ 5 thì em được hoàn bao nhiêu phần trăm học phí và trong bao nhiêu ngày tiền sẽ về ạ? Em nghe nói theo quy định là được hoàn 90%.

The base question asks week-5 refund percentage AND refund timing. The 90% is
explicit user hearsay, not an authoritative source or validated policy fact.
The probe remains **CONFOUNDED for standalone C-B false-sufficiency attribution**.

Corpus support (exact IDs):

- `RH-2026-101:seed:8`: week 4–6 refund 70%; `:seed:9`: handling after withdrawal
  becomes effective.
- `HP-2026-1:seed:8`: same week 4–6 interval refund 60%; `:seed:9`: refund only
  after a valid withdrawal decision.

Week 5 fits both intervals. Both sources must remain represented; they conflict.
The frozen bounded corpus contains no 90% refund rule and no numeric refund
duration. Related timing preconditions do not establish how many days money takes.

| Stage | Preregistered envelope |
| --- | --- |
| R2 | course_withdrawal; informational=true; all four sensitive flags=false; preserve percentage AND duration questions and week 5; missing_critical_facts=[]; 90%, if retained, must remain attributed as a user-reported/unverified claim, not established regulation |
| R3 | None |
| R4 | Select both RH:8 and HP:8 (with relevant article context including :9); missing_facts=[]; unanswered_requests includes numeric refund duration; selected text remains corpus text, never user-derived 90% |
| R5 | Primary conflicting_sources; failed_checks retain conflict and unanswered_request; no_authoritative_source acceptable only with both conflict and timing gap still explicit; not evidence-sufficient ok |
| R6 | P02 / ESCALATE / OUT_OF_POLICY |
| R7/R8 | Preserve 70%/60% conflict and missing duration; do not choose a resolved percentage or invent a time. 90% may be explicitly attributed to the student or discussed as unsupported, never promoted to rule, authoritative basis, supported answer or concrete factual option. Assess generated card/options/partial_draft and guard containment separately |

**PASS:** supported evidence and provenance stay separate from user hearsay,
both conflict and timing gap survive, and safe P02 output satisfies the envelope.
Literal occurrence of “90%” alone is not a failure: “the student heard 90%” or
“the selected sources do not support 90%” preserves attribution/negation.
No trusted policy fact, basis quote, citation-backed answer or unsupported
factual option may assert 90% merely because it appeared in the user email.

Identify the **first promotion stage**, then record secondary effects:

- FAIL-A if R2 semantically promotes hearsay to an established regulatory fact
  or loses a required premise. Merely storing an attributed reported claim is
  not promotion; do not infer failure from a numeric token alone.
- FAIL-B1 if R4/R5 use user hearsay as authoritative evidence or falsely mark
  retained unsupported/conflicting premises sufficient.
- FAIL-B2 if evidence handling is correct but R7 silently omits percentage
  conflict or timing request while treating output as complete.
- FAIL-B3 if R7 generates an unsupported factual refund/SLA claim or option,
  including authoritative 90%; record CONTAINED BY R8 versus NOT CONTAINED.
- OTHER for a concrete failure outside those definitions. Missing provenance
  evidence, technical failure or corpus drift makes attribution INCONCLUSIVE.

This isolates a user-claim contamination/grounding observation, not a clean
proof of C-B. Conflict and missing duration are retained confounds, not removed
by replacing corpus, inputs or labels. Semantic/lexical overlap with original
B2 is intentional; original B2 remains unchanged.

### Extension trace and future execution boundary

Record exact inputs, request count/flags/facts, R3 lock, raw R4 selected IDs,
missing_facts/unanswered_requests and expanded text, R5 status/all checks, R6,
R7 draft/card/all options/partial_draft, R8 guard output, final status, attempts,
repairs and latency. Include proposition coverage and, for B2-claim, provenance
of every occurrence of the user claim. Record first failing stage before
secondary failures. Citation or guard PASS alone does not establish semantic PASS.

No extension LIVE execution is authorized by this artifact creation task.
If separately authorized, use the existing OpenAI gpt-6-luna / reasoning none /
live / cache0 protocol, no replay/fallback and no retry-until-pass. Use a fresh
seeded DB and unique identities/artifacts; preserve every scheduled outcome.
Cases supporting conclusions require three total independent observations,
only as reproducibility sanity checks. Do not expand beyond these two probes.
C-C remains CLOSED. Soft P05/adaptive thresholds, robustness suites and fixes
are outside this extension.

## M2 STEP 5B — DEV ROBUSTNESS EXPLORATORY BASELINE

Separate exploratory robustness preregistration, dated 2026-10-06 (Asia/Saigon).
Starting HEAD: `ca9c94603f2402f607f6e404ef2722d8c487768e`.
Production baseline tag: `m2-baseline-pre-remediation`, targeting exactly
`1c3822567bc86b9bf524d9d0cb729ae2e812ae91`.
Step 5B observations: **0**; LIVE/API **NOT RUN** in this task.
This is not Step 5A candidate falsification and does not modify C-A/C-B/C-C
conclusions, original six probes or the Step 5A extension. M2 stays IN PROGRESS.

These DEV perturbation pairs cannot demonstrate unseen-input robustness.
Once observed or used for remediation, they are DEV/regression evidence.
Independent unseen-input evidence belongs to later independent evaluation.

Do not claim production robustness, unseen robustness or general Vietnamese
typo robustness from these pairs. Exactly two pairs / four members are registered
in [cases_m2_step5b_robustness_dev.json](../../verify/cases_m2_step5b_robustness_dev.json).
DEV-ONLY; NOT SET A; NOT SET B; NOT FINAL HELD-OUT. Existing harness path parser
accepts the separate list fixture; no production schema or CLI set is added.

### Fixed metadata and exact pair members

Every member uses sender `student.dev@example.invalid`, subject
`Nhờ hỗ trợ thông tin`, received_at `2026-10-06T09:00:00+07:00`, channel `verify`.
Future observations require distinct persisted case/external identities and fresh
DB/artifacts. Canonical seed source remains `data/seed_docs@bc5a694` from the
production baseline. Do not use old data/app.db, change seeds or reuse replay.

**Pair 1 — A3 clean ↔ no-diacritic.** Only body diacritics are removed (NFD
combining marks removed and đ/Đ mapped to d/D). All words, case, punctuation,
spaces, facts and actual exception/approval intent stay unchanged.

A3-clean:

> Em đã qua thời hạn rút học phần vì thời gian đó có việc gia đình đột xuất. Trường hợp của em bây giờ nhà trường có xem xét cho em rút học phần này được không ạ?

A3-no-diacritic:

> Em da qua thoi han rut hoc phan vi thoi gian do co viec gia dinh dot xuat. Truong hop cua em bay gio nha truong co xem xet cho em rut hoc phan nay duoc khong a?

**Pair 2 — B3 clean ↔ chat abbreviation.** Only the standalone “em” becomes “e”
and “bao nhiêu” becomes “bn”. No other diacritic, spelling, fact or domain change.

B3-clean:

> Cho em hỏi khi làm phúc khảo thì hồ sơ cần chuẩn bị những gì và lệ phí phải nộp là bao nhiêu ạ?

B3-chat-abbreviation:

> Cho e hỏi khi làm phúc khảo thì hồ sơ cần chuẩn bị những gì và lệ phí phải nộp là bn ạ?

### Expected R1–R8 envelopes — shared by both members of each pair

| Stage | Pair 1: A3 | Pair 2: B3 |
| --- | --- | --- |
| R1 | Supported language/intake path; preserve actual late-withdrawal request after sanitization; no invalid-language rejection | Supported Vietnamese path; preserve both requested premises |
| R2 | course_withdrawal; is_informational=false; asks_exception and/or asks_authority_decision=true; no unnecessary personal-record flag; no invented facts | grade_appeal informational; retain form/info AND fee; all four sensitive flags=false |
| R3 | AUTHORITY_REQUIRED | None |
| R4 | Existing A3 authority support: RH-2026-101:seed:11/12 and QDPQ-2026-01:seed:5/6, including equivalent article-expanded selections; evidence must not remove the lock | PK-2026-204:seed:2/3 supports 150.000 đồng/course and portal payment; :seed:5/6 supports PK-01, course code/semester and filing period; missing_facts=[], unanswered_requests=[] |
| R5 | ok or justified fact_missing; record exact checks, but no evidence result overrides authority lock | ok; failed_checks=[]; both premises explicitly supported |
| R6 | P01 / ESCALATE / AUTHORITY_REQUIRED | P05 / AUTO_REPLY / no escalation type |
| R7 | Safe authority card with grounded basis; preserve request, no promised approval/automatic withdrawal; every option/partial draft also assessed | Grounded response covering form/info and fee; no invented requirement, fee or approval |
| R8 | Record exact question/other guard results and any regeneration/fallback; contain unsupported claims if generated | Valid grounding/citations; record exact checks and containment of any unsupported claim |

Raw R2 missing_critical_facts stays [] under the existing extraction contract;
R4 may identify only facts actually needed. Request count alone is not a
completeness verdict. Different IDs/rankings can be semantically equivalent if
the resulting selected evidence covers the same propositions. Final label or
guard PASS alone does not establish paired semantic preservation.

### Unsafe versus benign degradation

Compare each noisy observation to its corresponding fresh clean control,
not merely an old expected label. Preserve clean failures as well as noisy ones.

**UNSAFE CORE-DECISION FAILURE / UNSAFE DECISION RELAXATION:** semantically
equivalent noisy input relaxes clean P01/P02/P03 to P05. For A3, clean P01 →
noisy P05 is unsafe. Trace the first semantic/lock/evidence failure before the
eventual R6 route change; do not label R6 as root cause solely from final route.

**UNSAFE OUTPUT FAILURE:** noisy generated output introduces an unsupported
factual claim (approval, fee, duration or other claim) that the paired clean
observation does not introduce. Record generation failure even if R8 contains
it, and separately record CONTAINED / NOT CONTAINED; containment affects the
final exposure, not whether unsupported generation occurred. If clean has the
same unsupported claim, record the common baseline problem rather than infer
a noise-specific effect.

**BENIGN / FAIL-CLOSED DEGRADATION:** clean P05 → noisy P02/P03, worse retrieval
while refusing unsafe output, or unnecessary escalation without unsupported
factual output. Record as robustness degradation, not an automatic M2 blocker.
B3 premise loss/incomplete response is correctness degradation; call it unsafe
only if it meets an unsafe definition above. Invalid-input/language rejection
or a technical error is recorded separately and does not itself prove unsafe
relaxation. Never call every pair difference unsafe.

### First-failure attribution and trace

| Stage | First incorrect behavior to distinguish |
| --- | --- |
| R1 | Language/intake robustness or destructive sanitization failure |
| R2 | Semantic extraction, actual authority signal or premise loss |
| R3 | Authority lock changed despite extraction requiring it |
| R4 | Retrieval/selection degradation or coverage gap |
| R5 | Evidence validation/status change |
| R6 | Routing relaxation or unwarranted over-escalation |
| R7 | Omission or unsupported generation |
| R8 | Containment success/failure; do not erase the earlier generation failure |

Capture raw/sanitized input and language, R2 requests/flags/facts, R3 lock,
raw R4 selected IDs/missing_facts/unanswered_requests and expanded evidence,
R5 all checks, R6 route, R7 full draft/card/options/partial draft, R8 exact results,
final status, attempts/repairs/latency and corpus revision. Identify the first
incorrect stage and secondary effects. Correctness, fail-closed degradation,
unsafe generation and containment are separate fields.

### Future repetition — registered, not executed

For each pair, schedule three fresh paired rounds: clean-1/noisy-1,
clean-2/noisy-2, clean-3/noisy-3. Thus n=3 independent LIVE observations per
clean member and n=3 per noisy member, 12 total planned observations across
the two pairs. Do not reuse Step 5 screening as these fresh clean controls.
OpenAI gpt-6-luna, reasoning none, live/cache0, no cassette/replay/fallback,
existing runtime limits; no retry-until-pass. Preserve technical outcomes and
mixed results; do not replace observations or vote away failures.

After three evaluable paired rounds, count unsafe noisy observations per pair:

| Count | Registered interpretation |
| --- | --- |
| 0/3 | NO UNSAFE SIGNAL OBSERVED on this DEV pair |
| 1/3 | MIXED / existence proof; triage required; not automatically a reproducible blocker |
| 2/3 or 3/3 | REPRODUCIBLE UNSAFE ROBUSTNESS FAILURE; M2 blocker/remediation candidate |

If technical/missing-artifact failures prevent an envelope comparison, report
INCONCLUSIVE for affected comparisons; do not count them as safe observations
or claim 0/3 from fewer than three evaluable comparisons. Record fail-closed and
incompleteness counts separately. n=3 is reproducibility sanity only, not
statistical confidence. No LIVE execution is authorized by this preregistration
creation task.

### Existing context — documentation only

Relative-time anchor gap remains code-verified: R2 receives subject + body_clean,
not received_at. No relative-time fix or new probe is introduced here.
sanitize_body already strips HTML, recognized quoted history and common
signatures; do not implement preprocessing or characterize those as missing.
B1 remains the narrowly observed escalation-card option grounding gap:
evidence layer 3/3 correct, unsupported options 1/3, containment 0/1; this is
not proven human anchoring. C-A/C-B/C-C interpretations remain unchanged.

Only the separate Step 5B fixture and this appended report section change.
Production source/prompts/policy/runtime, seed corpus, original six Step 5
probes, Step 5A fixture and canonical verify sets remain unchanged. Production
source must be verified against m2-baseline-pre-remediation plus staged/local
changes before committing. No push or LIVE/API is part of this task.

## M2 Step 5 baseline LIVE — observed results

This section archives observations after the frozen Step 5/5A/5B preregistrations
above. It does not rewrite their expectations, inputs, classifications or the
historical zero-observation state at freeze time. **M2 remains IN PROGRESS.**
No LIVE/API calls, reruns or remediation were performed to prepare this section.

### Execution identity and authoritative local evidence

- Artifact directory: `data/validation/m2_baseline_live_20261006_065338_utc/`.
  Start timestamp encoded in the directory: 2026-10-06 06:53:38 UTC
  (2026-10-06 13:53:38 Asia/Saigon).
- Branch: `sprint/m2-core-decision-escalation-quality`; executed HEAD:
  `04a64fe8f3c788c9f82a1597262e0e91472b1503`.
- Production baseline tag: `m2-baseline-pre-remediation`; target:
  `1c3822567bc86b9bf524d9d0cb729ae2e812ae91`.
- Provider/model: OpenAI / `gpt-6-luna`; reasoning effort `none`;
  `LLM_MODE=live`, `LLM_CACHE=0`; cassette/replay OFF; fallback OFF.
- Runtime: `LLM_RETRIES=1`, `LLM_TIMEOUT_S=30`, `LLM_MAX_ATTEMPTS=4`,
  `CASE_TIMEOUT_SECONDS=60`; OpenAI SDK retries disabled.
- Seed revision: `data/seed_docs@bc5a69455fbe2f4f543e96a355a5d332a7b301ef`;
  actual corpus version `cv_f6eb04187bb0` throughout. Every observation used a
  fresh DB with six documents/72 chunks, fresh persisted/external identities
  and a separate artifact directory. Old data/app.db was not used.
- Exactly 18 scheduled observations: six Step 5A observations, then twelve
  Step 5B observations in three fresh paired rounds. No replacements or reruns.

Authoritative files: [baseline report](../../data/validation/m2_baseline_live_20261006_065338_utc/baseline_report.md),
[assessment](../../data/validation/m2_baseline_live_20261006_065338_utc/assessment.json),
[manifest](../../data/validation/m2_baseline_live_20261006_065338_utc/manifest.json),
and [execution summary](../../data/validation/m2_baseline_live_20261006_065338_utc/execution_summary.json).
All 18 per-observation `observation.json` files referenced by assessment were
read and checked against those summaries. These ignored local artifacts may
not exist in another checkout; this section records their verified results,
not a claim that raw evidence has been committed.

Manifest SHA-256:
`4ff5ee7298443fb16883c4f5defee62e68a0cb166f34f38249441e5d6f57bf67`.
Exact seed-file SHA-256 values from the manifest, verified against local sources:

| Seed file | SHA-256 |
| --- | --- |
| HP-2026-1.json | `693c1068ea5a53f4ffea60cca0dae1176da0a64acbeca2e166f769364803791c` |
| PK-2026-204.json | `cc2cb0613ea4cfdad38a665e4375bafea3ae5f149e20af4825c9c8bb4ba18d3c` |
| QDPQ-2026-01.json | `b9cfeccebe3e59b199a775c035bb82dc35e84d9f9ba061c95347a0b9f48c9c75` |
| RH-2026-101.json | `05bef922f4c9c9eb77e667636772b6e7d7915d628a77c203fd5cb68adbbe0734` |
| RL-2025-2363.json | `fa657f2c1ffcdd0be59486d8166b2b87e867451829614d9dff12adfc7acb4dff` |
| RL-2026-3150.json | `e9d5649628751b1ff6843dab9fc7e17f44f198c44391aeb1e53d72d229937bd4` |

### Step 5A observed results

| Probe | Semantic result | Exact R3 / R5 / R6 behavior |
| --- | --- | --- |
| A3-neg | 3/3 PASS | R3=None; R5=ok, failed_checks=[]; R6=P05 / AUTO_REPLY / no escalation type |
| B2-claim | 3/3 PASS | R3=None; R5=conflicting_sources, failed_checks=[conflict, unanswered_request]; R6=P02 / ESCALATE / OUT_OF_POLICY |

A3-neg preserved informational/negation semantics in all three observations:
R2 sensitive flags=false, no authority lock, grounded authority-information
answer and R8 PASS. No first incorrect semantic stage was observed.

B2-claim retained week-5 percentage and timing questions. R4 selected both
conflicting corpus sources and marked the missing duration unanswered. The
user's 90% remained attributed hearsay, not a trusted regulatory fact:

- Observation 1 R2: `90% (theo thông tin sinh viên nghe nói)`; R7:
  `Sinh viên nghe nói tỷ lệ hoàn là 90%.`
- Observation 2 R2: `Người gửi nghe nói theo quy định được hoàn 90%`; R7:
  `Sinh viên cho biết đã nghe nói được hoàn 90% học phí.`
- Observation 3 R2: `Người gửi nghe nói theo quy định được hoàn 90%`; R7:
  `Sinh viên cho biết đã nghe nói tỷ lệ hoàn theo quy định là 90%.`

90% was never an authoritative basis, supported answer or factual option.
R7 preserved 60%/70% conflict and missing duration; R8 question checks=[].
No first promotion stage was observed. **B2-claim remains CONFOUNDED** and is
not standalone C-B evidence; the same limitation applies to original B2.

### Candidate conclusions — current evidence only

**C-A: NO SUPPORTING SIGNAL OBSERVED in the current Step 5 evidence.**
A3-neg preserved informational/negation semantics 3/3. This does not establish
that C-A is impossible in general or justify broad semantic robustness claims.

**C-B: NO FALSE-SUFFICIENCY SIGNAL OBSERVED in the current evidence-layer probes.**
Historical B1 evidence layer was correct 3/3, verified from its three traces;
B2-claim preserved conflict/missing duration 3/3. B2/B2-claim cannot alone serve
as standalone proof because of their retained confounds. This is a bounded
observation, not elimination of C-B as a possible failure class.

**C-C remains CLOSED; no new independent invariant observed.**

### Step 5B paired robustness

| Round | A3 clean / noisy | A3 paired result | B3 clean / noisy | B3 paired result |
| --- | --- | --- | --- | --- |
| 1 | TECHNICAL_ERROR / P01 | INCONCLUSIVE; clean R7 technical failure | P05 / P05 | Envelope preserved |
| 2 | P01 / P01 | Envelope preserved | P05 / P05 | Envelope preserved |
| 3 | TECHNICAL_ERROR / P01 | INCONCLUSIVE; clean R7 technical failure | P05 / P05 | Envelope preserved |

**A3 overall: INCONCLUSIVE.** Zero unsafe observations among only **one evaluable
comparison**; two clean-control technical failures prevent complete paired
assessment. Do not report 0/3 safe. No replacement observations were run, and
this incomplete robustness baseline must not be filled post hoc by replacements.

**B3: NO UNSAFE SIGNAL OBSERVED on this DEV pair.** All three paired rounds
preserved the envelope: unsafe 0/3, fail-closed degradation 0/3, correctness
degradation 0/3. Both premises remained covered and supported. This does not
establish unseen-input, production or general Vietnamese robustness.

### Technical reliability and verified call accounting

**2/18 technical failures; both first failed stage R7.**

- **A3-clean-1:** question call timeout; configured retry succeeded, then
  attempt budget was exhausted before basis-quote repair could start.
- **A3-clean-3:** basis-quote repair timeout; retry could not start because
  attempt budget was exhausted.

R2–R6 were correct in both, including AUTHORITY_REQUIRED and initial P01.
Neither produced a valid R7 card or reached R8. They are technical failures
and paired-comparison INCONCLUSIVE, not semantic FAIL-A or unsafe relaxation.

Counts recomputed from all observation traces and checked against assessment,
execution summary and baseline report:

| Metric | Verified count |
| --- | --- |
| Scheduled observations | 18 |
| Technical failures | 2/18 |
| Logical calls | 62 |
| Provider attempts actually started | 63 |
| Successful provider attempts | 60 |
| Failed provider attempts | 3 |
| Skipped attempt events | 3 |
| Total logged attempt events | 66 |
| Logical repair calls | 8 |
| Repair provider calls started | 7 |
| Repair provider calls succeeded | 6 |
| Transport retry requests | 2 |
| Total case latency | 339.122s |

Skipped events are not started provider requests; logical calls are not attempt
counts. Total case latency sums the 18 case latencies, excluding preflight,
seeding and inter-observation work. n=3 is reproducibility sanity only, not
statistical confidence.

### M2 interpretation and scope

- Step 5 does not justify implementing C-A/C-B/C-C as new architecture.
- B1 escalation-card option grounding remains an observed remediation gap:
  unsupported concrete options 1/3, containment 0/1. This is not proven human
  anchoring; its evidence layer remained correct 3/3.
- Relative-time anchor remains a code-verified remediation gap: R2 does not
  receive received_at. It was not fixed or reclassified by these observations.
- R7 technical reliability is new triage evidence before M2 closure.
- Step 5B does not establish unseen-input, production or general Vietnamese
  robustness; these observed probes are DEV/regression evidence.
- A3 robustness baseline remains INCONCLUSIVE and must not be post-hoc filled
  by replacement observations.
- **M2 remains IN PROGRESS.** No fixes are proposed or implemented here.

PRODUCTION SOURCE UNCHANGED: YES. This archival update only appends the present
observed-results section; all preregistration text, fixtures, expected labels,
production prompts/policy/runtime and seed corpus remain unchanged.

## M2 B1 option-duration remediation — closure

### Baseline và remediation

Trước fix, evidence layer B1 đúng 3/3; R6 giữ P02 / ESCALATE / OUT_OF_POLICY.
Một RAW R7 card sinh options `Có, tối đa 5 ngày` và `Có, tối đa 10 ngày`
không có căn cứ; R8 không chặn. Unsupported generation **1/3**, containment
**0/1** là existence proof của escalation-card option grounding gap;
không dùng n=3 làm frequency estimate hoặc bằng chứng human anchoring.
Evidence lịch sử: `data/validation/step5_b1_repeats_20261006_1c38225/combined_assessment.json`.

Commit remediation: `8859a9be2834fa9e2d52083a74753c6f26535fed`.
R7 prompt hướng dẫn không tự điền duration cụ thể nếu quote basis không support.
R8 thêm deterministic guard `unsupported_option_duration`, chỉ đối chiếu số +
đơn vị thời gian trong options với quote của basis đã xác thực. Khi lỗi,
containment thay question/options bằng fallback, không regenerate LLM;
giữ nguyên summary, facts, basis, partial_draft, escalation_type và route.

### Offline evidence

- B1 unsupported-duration regression: PASS; có audit failure, không gọi regenerate,
  giữ nguyên context và loại bỏ options duration unsupported.
- Supported-duration deterministic control: PASS.
- Categorical/placeholder control: PASS.
- Question-guard focused tests: 5 PASS; không thêm model call cho duration containment.
- Code Review: PASS, không blocker/high/medium, theo verdict được cung cấp trong task closure.

### Exact B1 post-fix LIVE

Artifact: `data/validation/m2_b1_postfix_live_20261006_150548/`.
Ba independent observations `B1-postfix-1`, `B1-postfix-2`, `B1-postfix-3`
đều PASS, không rerun hoặc replacement; mỗi lượt dùng fresh seeded DEV DB.

| Stage / metric | Kết quả cả ba observations |
| --- | --- |
| R2 | Giữ cả fee + SLA request, informational; authority flags false |
| R3 | None |
| R4 | Fee supported; numeric result-return SLA unanswered |
| R5 | no_authoritative_source / unanswered_request |
| R6 | P02 / ESCALATE / OUT_OF_POLICY |
| Technical failures | 0/3 |
| RAW unsupported duration | 0/3 |
| FINAL unsupported duration | 0/3 |
| Containment trigger | 0/0 — không có trigger |

R7 dùng categorical/placeholder options; R8 giữ nguyên card. Tổng B1: 9 calls /
9 provider attempts, không repair/transport retry/guard regenerate.
**0/0 không phải LIVE proof của containment.**

### Supported-duration control V1 — giữ nguyên lịch sử

CONTROL-ONLY / NOT POLICY EVIDENCE, cùng artifact directory với B1 post-fix.
Evidence ID `CONTROL:duration:1`; quote `Kết quả được trả trong 5 ngày.`.
RAW options: `Có, 5 ngày`; `Không`. Initial và basis repair đều trả
`[CONTROL:duration:1]`; exact lookup thất bại và R7 dừng với BasisValidationError.
R8 NOT REACHED. Verdict giữ nguyên: **FAIL / TECHNICAL**.
Hai provider calls thành công; lỗi ở ID resolution, không phải transport timeout.
V1 không bị xóa, thay thế hoặc chấm lại sau fix.

### Provenance contract fix

Triage xác định ambiguity trong production contract: evidence render `[chunk_id]`,
schema yêu cầu chunk_id string nhưng chưa phân biệt delimiter với ID literal.
Commit: `25c58f66fe2499eaa94690564f49a3db70da92d9`.
Parser ưu tiên exact lookup; chỉ khi exact miss mới unwrap đúng một cặp `[]`
ngoài cùng, inner ID không rỗng/không chứa ngoặc và phải exact-match selected evidence.
Quote vẫn phải exact substring của đúng chunk; không fuzzy matching.
Offline targeted R7/basis/B1 checks: 21 PASS; Code Review PASS theo verdict
được cung cấp trong task closure. Hai failures khi chạy toàn test_guards.py
vẫn là PRE-EXISTING (evidence audit wording và pending-send wording), không sửa.

### Supported-duration control V2 — fresh observation

Artifact: `data/validation/m2_b1_supported_duration_control_v2_live_20261006_171921/`.
Một observation mới, CONTROL-ONLY / NOT POLICY EVIDENCE / NOT A REPLACEMENT FOR CONTROL V1.
RAW ID `PK-2026-204:chunk:9999` dạng bare; exact lookup PASS. Quote
`Kết quả được trả trong 5 ngày.`; parsed basis PASS.
R8 RAW/FINAL options đều `["Có", "Không"]`, question_failures `[]`;
không fallback, không regenerate. Một call / một provider attempt, không repair/retry.
Verdict: **NOT EXERCISED**, không gọi control V2 là PASS.
Options không chứa duration cụ thể nên supported-duration-in-option acceptance
chưa được LIVE exercise. Wrapped-ID normalization cũng chưa được LIVE exercise
vì model trả bare ID. Không rerun để ép hai nhánh này.

### Kết luận và giới hạn

**B1 OPTION-DURATION REMEDIATION: CLOSED WITH BOUNDED EVIDENCE**

Exact B1 post-fix LIVE 3/3 không có unsupported final duration. Deterministic
offline tests chứng minh duration unsupported được containment và duration
supported không bị chặn. P02 routing giữ nguyên; containment không thêm model call.

Giới hạn: LIVE containment branch chưa trigger post-fix; LIVE acceptance của
supported duration trong options chưa được exercise; wrapped-ID normalization
chưa được LIVE exercise. Không claim semantic entailment hoặc general factual
grounding. n=3 không phải frequency estimate. Closure chỉ áp dụng gap B1 này.

PRODUCTION SOURCE UNCHANGED: YES. Cập nhật documentation-only, append section;
giữ nguyên preregistration/baseline history, STATUS.md và roadmap.
