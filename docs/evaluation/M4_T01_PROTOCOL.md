# M4-T01 — Independent Evaluation Protocol v1 (review candidate)

Owner: Minh — Evaluation/Logic. Final reviewer: Thư. Approver: Project Coordinator.
Task: [M4-T01](https://trello.com/c/7EhgcMDv). Date: 14/10/2026 (Asia/Saigon).
Baseline: `eaaeea88a59618b49219a20ae01a3cf3227cec87`.
Status: **PARTIAL_ONLY / NOT AUTHORIZED FOR OFFICIAL EXECUTION**.

## 1. Objective, authority and evidence levels

Measure selective automation, three business stop reasons and supporting evidence on
an eligible independent population. This document prepares M4-T02; it does not run it,
accept a gate, approve a model, change production contracts or establish dataset eligibility.
Sources: [spec](../../PROJECT_SPEC.md), [roadmap M4](../SPRINT_ROADMAP.md#m4--evaluation-set-a--final-sealed-set-b),
[workflow](../TEAM_WORKFLOW.md), [readiness report](../../reports/evaluation/M4_T01_PROTOCOL_READINESS.md).

| Mode | Permitted inference | Additional requirements |
|---|---|---|
| OFFLINE_UNIT | Arithmetic/schema/adapter correctness only | Synthetic labels; no provider or app run |
| SYNTHETIC_DEV | Behavior on declared DEV/synthetic inputs | Frozen DEV expectations; disclose stubs |
| REPLAY | Reproduction of recorded responses on exact configuration | Authorized provenance, cassette hashes, zero misses, cache disabled, isolated DB |
| LIVE | Observed provider behavior at run time | Separate Coordinator authorization, provider/model/config, attempt/cost budget |
| INDEPENDENT_HELD_OUT | Independent results for this dataset/revision only | Verified eligibility, frozen protocol/Gold, integration/safety gate, explicit GO |

Execution mode and independence are separate axes: LIVE does not imply held-out;
replay requires a justified independent recording history before any held-out claim.
Unit tests, Verify/full15, M2 captures, and M5 B0/B2 Gold cannot substitute for Set A/B.
Current work uses OFFLINE_UNIT only. LLM/provider/email calls = 0.

## 2. Dataset eligibility and disclosure

Custodian supplies a signed, sanitized metadata attestation without exposing cases/Gold:
author and source roles; independent Gold author/reviewer; creation/finalization timestamps
with timezone; original dataset/Gold version and historical immutable hashes; timestamped
receipt/registry; earliest relevant M2 tuning event; access/exposure log (including prompts,
captures, cassettes, study, demo and reviewers); DEV/REGRESSION family overlap assessment.
Document provenance uncertainty, rather than assigning a fabricated creation time.
Git commit times are corroborating metadata, not proof of creation or historical secrecy.

Set A requires author/Gold/hash fixed **before M2 tuning** per roadmap. Obtain the actual
earliest tuning cutoff; a later M2 report or LIVE date is not a substitute. Never hash a
new file and call that historical preregistration. Cases already used for tuning/testing,
including full15, remain DEV/REGRESSION. Once Set A results are opened it becomes
DEV/diagnostic and cannot provide final held-out evidence again.

| Disposition | Rule |
|---|---|
| ELIGIBLE | Authorized evidence verifies every independence/preregistration requirement |
| NOT VERIFIED | Evidence/access/cutoff insufficient; no inferred contamination |
| NOT ELIGIBLE | Affirmative evidence of an independence violation; Coordinator disposition required |

Set B is for one frozen-revision M7 run. Inspect only permitted seal/access metadata:
custodian attestation, seal registry receipt, creation/Gold commitment, independent roles,
ACL/version/access log and evidence no tuning exposure. Do not list private locations,
read files, inspect Gold, decrypt, or open sealed archives. A sealed filename, absence of
reads in this session or a claimed hash alone does not verify a seal. Missing attestation
means NOT VERIFIED. Revoke unauthorized access and stop the affected work if exposure
is suspected; preserve evidence without copying sensitive payloads into public artifacts.

Current Set A: **NOT VERIFIED**. Current Set B seal: **NOT VERIFIED**.
Private artifact access method: **PENDING AUTHORIZATION**; no task attachments supplied it.

## 3. Case and Gold contract

Machine-readable candidate: [schema](M4_T01_SCHEMA.json). It is an evaluation artifact,
not a new public runtime interface. One case has `id`, `is_synthetic`, `gold_version`,
`input` (`sender`, `subject`, `body`, timezone-aware `received_at`), `expected_decision`,
`expected_type`, `expected_rule_id`. These five harness keys map unchanged to
`verify.harness._case_from_payload`; channel is `verify`, external_id is `id`.
Synthetic sender uses a reserved example domain. Real PII is forbidden.

Gold route is AUTO_REPLY or ESCALATE. Gold AUTO_REPLY has null stop and P05.
Gold ESCALATE has one of the three stops and the approved P01/P02/P03/P04 rule.
Gold rule/type pairs follow the table below. Ambiguous cases, multi-intent precedence,
applicability masks (citation/groundedness), domain/family strata and allowed evidence
references must be adjudicated and frozen by authorized reviewers before execution.
An ambiguous Gold blocks the run; never remove a case because its output is inconvenient.
Gold INVALID_INPUT cases, if approved for another protocol, form a separate population;
they do not enter this two-route business population.

## 4. Rubric and runtime reconciliation

Authoritative source: [types](../../core/types.py), [policy](../../policies/policy.yaml),
[engine](../../core/policy_engine.py), [pipeline](../../core/pipeline.py),
[ground guard](../../core/ground_guard.py). Read-only baseline inspected.

| Runtime result | Evaluation rule |
|---|---|
| AUTO_REPLY / null / P05 | Routine informational request, sufficient applicable ACTIVE evidence, no authority boundary; check draft/citations/grounding separately |
| ESCALATE / AUTHORITY_REQUIRED / P01 | Personal record, exception, appeal or authority decision; do not approve on behalf of a human |
| ESCALATE / OUT_OF_POLICY / P02 | No authoritative source, authority-content, conflicting sources or unsupported domain |
| ESCALATE / FACT_UNRESOLVED / P03 | Missing critical fact or scope mismatch |
| ESCALATE / FACT_UNRESOLVED / P04 | Content/ground/question guard stop; different rule from P03 |
| ERROR / null / TECHNICAL_ERROR | Technical failure, never a business escalation |
| INVALID_INPUT | Nonbusiness response to a business case; count separately, not as ERROR or a guessed route |

P01 precedes P02, P03, P04, P05 in policy. Technical flags short-circuit to ERROR;
later guards can downgrade a draft to P04. Freeze expected results against the complete
pipeline, not YAML precedence alone. Policy's P04 reason and an engine docstring mention
generic failures, but the actual technical fallback returns ERROR/TECHNICAL_ERROR.
Source behavior and spec prevail; do not rewrite production or expected labels.

Score independently:

1. Route: exact AUTO_REPLY/ESCALATE match.
2. Stop: exact three-class match; P03/P04 share a stop but rule mismatch still fails rule.
3. Rule/policy: exact frozen rule and policy precedence/applicability. A known but wrong
   rule/type pairing is a semantic mismatch; retain its valid route in routing metrics.
4. Citation: each material claim has a resolvable cited chunk, ACTIVE/effective at the
   case time, appropriate scope/cohort and supports that claim; fabricated, stale,
   contradictory or irrelevant citations fail. ACTIVE IDs alone are insufficient.
5. Groundedness: all factual/material claims, numbers, dates, conditions and authority
   statements follow the frozen input and approved evidence; no invented missing facts.
   A runtime `grounded=true` or fluent explanation is not independent adjudication.
6. Card/content: clear decision question, feasible options, no fabricated authority or
   assumptions. Existing Verify's nonempty checks are a structural smoke only.

Each content judgment is PASS/FAIL/NOT_REVIEWED/NOT_APPLICABLE with scorer, rubric
version, sanitized evidence reference and rationale retained privately. Applicability
is frozen independently of output; an absent required draft/citation is FAIL, not N/A.
Disagreements remain NOT_REVIEWED pending authorized adjudication; keep both originals.

An absent row is MISSING (not attempted/partial artifact reason recorded separately).
An exception/timeout/ERROR is TECHNICAL_ERROR. Unknown decision/stop, missing required
fields, invalid AUTO stop or missing ESCALATE stop is MALFORMED technical output.
Duplicate/foreign case IDs or contradictory artifacts invalidate the run for reconciliation;
never silently choose a row. A valid route with wrong stop, rule or content remains a
business result with the corresponding failed criterion. Preserve sanitized raw artifact
hash/reference; never invent a business decision from an error.

## 5. Metrics, population and denominators

Freeze ordered unique case IDs and Gold before run. S = all planned eligible business
cases; V = cases with a structurally valid AUTO_REPLY/ESCALATE result. ERROR, malformed,
INVALID_INPUT and MISSING remain in S but not V. Publish counts by Gold route, stop,
domain/family and failure category; never silently shrink S. One primary result per case;
all attempts/retries retained, no best-of selection. Preregister repeat/family handling;
do not treat correlated variants or retries as independent samples.

In V: TP = Gold ESCALATE/pred ESCALATE; FN = Gold ESCALATE/pred AUTO_REPLY;
FP = Gold AUTO_REPLY/pred ESCALATE; TN = Gold AUTO_REPLY/pred AUTO_REPLY.
Publish this 2x2 confusion matrix with labeled axes and a separate Gold-by-outcome table
including ERROR, MALFORMED, INVALID_INPUT, MISSING. Sum check: TP+FN+FP+TN = count(V).

| Metric | Numerator / denominator | Inclusion/exclusion and missing handling |
|---|---|---|
| MER (conditional) | FN / (TP+FN) | Gold ESCALATE in V; excludes nonbusiness outputs, always show their class counts |
| OER (conditional) | FP / (TN+FP) | Gold AUTO_REPLY in V; same exclusions |
| Escalation precision | TP / (TP+FP) | Valid predicted ESCALATE, regardless of stop correctness |
| Escalation recall | TP / (TP+FN) | Valid Gold ESCALATE; 1-MER on the same denominator |
| Route correctness | (TP+TN) / count(V) | Conditional; never describe as full-population held-out accuracy without qualification |
| Decision coverage | count(V) / count(S) | All planned cases, including technical/missing/invalid |
| Technical failure | (ERROR+MALFORMED) / count(S) | Disjoint categories; report ERROR and malformed subtotals |
| Missingness | MISSING / count(S) | Expected IDs without output, including aborted/unattempted cases |
| Invalid-input response | INVALID_INPUT / count(S) | Separate nonbusiness category for this business population |
| End-to-end route success | (TP+TN) / count(S) | All planned cases, with nonbusiness outputs contributing no success |
| Stop correctness | exact stop / Gold ESCALATE in V | Gold stop vs predicted three stops plus AUTO_REPLY column; route miss is not excluded |
| Conditional stop correctness | exact stop / TP | Gold and pred ESCALATE only; publish alongside previous metric |
| Rule correctness | exact rule / count(V) | Wrong known rules counted as FAIL; report independently of route |
| Citation/groundedness | PASS / applicable planned cases | Freeze applicability; technical/missing/no required draft cannot PASS |
| Content review coverage | (PASS+FAIL) / applicable planned cases | NOT_REVIEWED shown explicitly; also PASS/(PASS+FAIL) as reviewed-only diagnostic |

All proportions show raw integer n/N, rate and Wilson 95% CI; N=0 yields null rate/CI
and `UNDEFINED`, never zero/PASS. Counts themselves have no proportion CI. No acceptance
thresholds are invented: sample size, strata minimums, acceptable MER/OER, technical and
coverage gates are **PENDING AUTHORIZATION**. Do not compare quality while hiding failure
coverage. Show conditional MER/OER beside sensitivity bounds FN/S_ESC to
(FN+nonbusiness_ESC)/S_ESC, and FP/S_AUTO to (FP+nonbusiness_AUTO)/S_AUTO. These are
missing-outcome bounds, not new business classifications or confidence intervals.

[M3-T02 design](../../reports/sprints/M3_T02_FEASIBILITY_REPORT.md) uses total expected-class
denominators for its adaptation design. It is not a locked M4 definition. Preserve it:
M4 explicitly names its valid-decision conditional estimates and additionally reports the
full-planned counts/bounds above. No frozen definition in spec/roadmap was found to conflict.
Coordinator review must resolve any other approved definition before protocol freeze.

Latency: retain monotonic elapsed_ms per attempted case, including failures, and full-run
wall time with attempts count and observation coverage. Report count, median and nearest-rank
p95 (sorted index ceil(.95*N)-1), success and failure strata separately. Missing durations
are null with reason, never zero; timeouts give a lower bound/censor flag. Replay timing
is local replay timing only. No Wilson CI for latency; no runtime latency claimed here.

Wilson: p=n/N, z=1.959963984540054; d=1+z²/N;
center=(p+z²/(2N))/d; half=z*sqrt(p*(1-p)/N+z²/(4N²))/d;
CI=[max(0,center-half), min(1,center+half)]. Use integer 0<=n<=N, no rounding before
calculation; display percentages with consistent precision plus raw counts. Reference:
[NIST Wilson method](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
Synthetic cases are descriptive arithmetic checks only. Wilson's independent Bernoulli
sampling interpretation requires justified sampling; small curated/synthetic/family-dependent
sets do not establish population representativeness. No pooling runs or multiple-testing claims.

## 6. Immutable manifest and evidence schema

[JSON schema](M4_T01_SCHEMA.json) defines case, result and manifest records.
[Offline validator](protocol_validation.py) checks cross-field/ID/hash invariants;
[tests](test_protocol.py) include positive and deliberately rejected records.
Every helper entry point validates the corresponding schema before semantic checks:
cases/manifest violations raise ValueError; identifiable invalid result records count as
MALFORMED, including contradictory outcome tags, missing/extra fields and invalid timings.
Schema-valid records retain their declared outcome; finite elapsed_ms is checked separately
because Python's JSON tools can represent NaN/Infinity outside strict JSON. None means an
absent output. Records without a reconcilable case_id abort reconciliation; unknown or
duplicate IDs are never silently dropped. A complete normalized result is required even
in synthetic tests; a four-field harness projection is not the result envelope.
Known wrong rule/type/route combinations remain semantic errors with valid business routing.
JSON Schema handles shape; semantic checks handle calendar/timezone, Gold mapping,
finite timing, identity and aggregate counts. Neither layer establishes provenance.

Before authorized run, freeze a manifest containing:

- Protocol/rubric/Gold version and SHA-256 of exact bytes (no newline/encoding normalization).
- Dataset opaque public ID, private custodian receipt/commitment, historical preregistration
  evidence, current integrity digest, eligibility and access authorization.
- Ordered case IDs/count, per-case hashes in restricted registry, partition/family/strata.
- Full runtime Git SHA, dependency/environment versions and artifact/image digest.
- Corpus snapshot version/hash, ACTIVE scope/effective-date configuration, policy/config hash,
  prompt/schema versions, adaptation state/version (frozen, no feedback updates during run).
- Mode, provider, model identity, reasoning/temperature/structured-output/retry/timeout,
  attempt/cost budget, cache disabled, replay pack identity/hashes if applicable.
- Authorization receipt, reviewer/custodian roles, freeze time (UTC), stop/retry/abort rules.

Use a separate receipt for manifest's own SHA-256; do not put a self-referential digest
inside the file it hashes. Authorized reviewer signs that receipt before first run.
Use append-only artifacts/new run IDs, never overwrite results/Gold/receipts. A newly
computed digest proves integrity from that point only. Public packet holds sanitized
opaque references; case IDs/hashes/count strata may also be restricted if disclosure-sensitive.
Keep private manifests and runtime output access-controlled; public aggregation only after review.

Result schema records case ID, actual decision/type/rule, elapsed_ms or null, outcome,
error code and sanitized artifact reference. Raw error payload is private; no secrets
or private paths. The complete private evidence envelope additionally binds run ID,
manifest receipt hash, case/Gold version, attempt ordinal, start/end UTC, terminal status,
PipelineResult reference/hash, citations/draft/evidence references, independent criterion
judgments and adjudication history. These are required before official scoring; the
minimal result schema alone is not a sufficient official evidence envelope.

Every planned case gets a normalized row including MISSING; the collector may initially
omit an absent row, which scoring reconciles against manifest IDs. Keep original evidence.
`validate_manifest(manifest, case_bytes, protocol_bytes, runtime_sha=expected_sha)` binds
exact case bytes, count/IDs, Gold version, protocol bytes and the expected runtime SHA.
The expected SHA must come from the independently reviewed freeze receipt, not be copied
from the manifest being checked; this helper does not inspect Git or approve that receipt.
Schema validation requires the literal boolean false for execution_authorized; null/0,
extra properties and missing fields are rejected. It is an offline
preparation check, not an eligibility/seal/authorization verifier or official runner.
The synthetic manifest in tests explicitly has `execution_authorized=false`, null official
configuration and pending decisions. This is valid preparation metadata, never a GO receipt.

## 7. Harness compatibility and reproduction

[Verify harness](../../verify/harness.py) accepts the compatible input fields and returns
VerifyResult containing expected/actual decision/type, rule, passed, elapsed_ms, timestamp,
corpus_version, case_ref, subject and question. `_matches` combines route/type/rule,
ACTIVE citation IDs for AUTO and nonempty card question/options for ESCALATE. It does not
score full grounding, material-claim citation support, immutable manifests, private evidence
or missing-output reconciliation. Do not use its single `passed` as M4 quality score.
Its public JSON output includes input-derived text and expected labels: **do not publish it
for private evaluation cases**. Its CLI uses registered DEV sets; do not register Set A/B
or invoke it on them in T01. No production adapter modification is authorized.

Safe commands from repository root (Python 3.11, installed environment):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s docs/evaluation -p test_protocol.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_harness.py::test_paste_inbox_and_verify_share_the_same_pipeline verify/test_harness.py::test_same_escalation_type_with_wrong_rule_does_not_pass -q
git diff --check
```

Unit tests use only newly constructed synthetic metadata and read source definitions;
they block network and do not execute a model. Targeted existing pytest tests use the
repository's network/provider guard and isolated temporary DB with test doubles. This
is harness contract validation, not product replay or independent model evidence.
`jsonschema` is present in the validation environment; no dependency was added. If absent,
report schema validation NOT RUN and supply the approved environment before official use.

Official procedure (intentionally no executable run command until approved): verify
entry checklist → privately validate original commitments and hash receipts → freeze
exact runtime/config/corpus → obtain GO-A (or separate M7 GO-B) and mode authorization →
invoke approved collector through the ordinary process_case path with isolated DB and
private outputs → preserve every attempt/failure → reconcile all IDs → adjudicate content →
compute predeclared metrics → independent review → release sanitized report. No extra
retry after protocol budget and no choosing a better run. If collection aborts, preserve
partial evidence and mark remaining cases MISSING; rerun needs a new explicit disposition.

## 8. Review checklist and official stop conditions

- Owner understands diff; Thư independently reviews methodology and evidence boundaries.
- Coordinator accepts exact protocol/Gold version; metadata proves eligibility and seal.
- Actual earliest M2 cutoff, dataset authorship and exposure have authorized evidence.
- Case count/IDs/hashes, Gold/applicability, provider/config, corpus/policy/adaptation locked.
- Full official envelope/collector and privacy controls approved and tested offline.
- M3 safety and Stable Integration evidence matches selected runtime, not just Trello status.
- Metrics/denominators/uncertainty, sample design and numeric gates explicitly accepted.
- Separate GO, mode/LIVE scope and budget granted; no Set B access in M4-T02.

Stop affected official work for unverified preregistration/permissions, contamination,
hash/version mismatch, changed runtime/config/Gold, duplicate/unknown IDs, unsafe output,
insufficient evidence/ambiguous labels, need to change frozen rubric, network authorization
or budget breach, ownership conflict or unexpected technical pattern. Record failures,
do not tune or erase them; Coordinator decides disposition and any new authorized run.
Technical failures alone are recorded as failures; abort threshold remains pending review.
Preparation can continue safely without opening private sets. M4-T02 is **NOT READY**
until missing decisions/evidence in the readiness report are resolved. T01 acceptance is
not GO-A, evaluation PASS or permission to run Set B.
