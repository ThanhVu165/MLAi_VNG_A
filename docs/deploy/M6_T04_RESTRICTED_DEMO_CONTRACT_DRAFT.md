# Restricted DEMO Hotfix — Task Contract DRAFT

**RESULT:** CONTRACT_DRAFT_READY. **STOP:** AWAITING_COORDINATOR_CONTRACT_APPROVAL.
Prepared under M6-T04 D3; this is not an officially assigned hotfix Task ID or READY card.
See [team handoff](M6_T04_TEAM_HANDOFF.md) for verified Git/Railway/evidence context.

## 1. Assignment, objective và baseline

- Task ID: **PENDING COORDINATOR ASSIGNMENT**.
- Owner / Independent Reviewer: **PENDING COORDINATOR APPROVAL**.
- Approver: Project Coordinator.
- Objective: anonymous visitor can use approved synthetic DEMO workflows and Verify;
  cannot mint ADMIN/APPROVER, alter corpus, approve/correct/override or write unapproved data.
- Proposed implementation baseline: verified remote
  `dev@eaaeea88a59618b49219a20ae01a3cf3227cec87`; verify again before READY.
- Private 61e31e8 is ACCEPT LIMITED evidence only. PR #51 is separate deployment work,
  not automatic implementation baseline/merge authorization or changed frozen artifact.
- Branch / report path: assigned after formal Task ID; PR base `dev`. No branch created
  or Owner assigned by this draft. One Owner receives explicit cross-module scope.

## 2. Coordinator decisions preserved

[D1–D4](https://trello.com/c/MENWGSkO#comment-6acf4ca53a2061bfdcd91356): private SHA
accept limited; Restricted DEMO proposal approved; separate contract/ownership/READY
required; public gate HOLD until accepted hotfix/new exact SHA and full safety evidence.
No LIVE/API/email, paid billing, merge PR #51, frozen-baseline change or DONE authorization.

## 3. Findings và action classification

These are static source findings except the previously reproduced admin-name finding.
Direct-call bypass tests below are required future validation, not new preflight PASS.

| Class | File / functions / write path | Required enforcement |
| --- | --- | --- |
| PRIVILEGED | pages/3_Quan_tri_quy_dinh.py _upload/_prepare/_review → corpus.intake ingest_file/ingest_text/ingest_url/recheck_url_sources | Current name creates ADMIN actor; deny intake/recheck before upload persistence, provider proposal or URL fetch |
| PRIVILEGED | corpus.workflow materialize_source/prepare_source/approve_source; metadata.save_metadata; lifecycle reject_source/request_change/approve_for_activation/activate_source/rollback_source/flag_cases_for_recheck; conflict/version effects | Deny before source/chunk/state/version/audit changes; actor prefix is not authorization |
| PRIVILEGED | corpus.store source/chunk/content/version create/update/delete/bump functions | Lower-level guard prevents bypassing intake/lifecycle; canonical seed initialization needs a validated internal exception |
| PRIVILEGED | pages/2_Hang_cho_duyet.py _open_decision/_record_decision/_save_draft/_approve_send/_return_to_queue | HUMAN:local is not authenticated; opening a card itself inserts human_decisions; guest read must avoid that write |
| PRIVILEGED | streamlit_app.py sidebar → core.controls pause_automation/resume_automation; pages/4_Nhat_ky_kiem_toan.py → override_decision/retry_case; core.controls rerun_case | ADMIN:local or startswith ADMIN guard is forgeable; deny service mutation independent of UI state |
| PRIVILEGED | core.dispatch cancel_send/escalate_from_pending/create_correction_email; core.worker retry_case/queue_resume; core.resume resume_case | Status checks or HUMAN actor prefix are insufficient; block guest mutation and untrusted resume jobs |
| PUBLIC_SAFE, conditional | Fixed approved samples → core.worker submit_case → core.pipeline process_case → normal persistence/scheduling/dispatch | Server reconstructs canonical input, validates case/job and controls actor; caller-supplied SYSTEM does not authorize forged decisions or case IDs |
| PUBLIC_SAFE, conditional | pages/5_Verify.py → verify.harness run_cases | Only verified server path/input set V01–V04; deny alternate paths/sets before audit or pipeline writes |
| PUBLIC_SAFE, conditional | Results/corpus/audit/metrics view; core.explain explain_plainly writes EXPLAIN_REQUESTED | Read only approved synthetic DB/case associations; guard explain before its audit; query/session state supplies selection, not authority |
| UNDECIDED | Anonymous human R11/approval, cancel/correction, arbitrary pasted emails and additional sample/Verify sets | Coordinator explicitly chooses permitted judge workflows; no automatic permission from synthetic label |

CaseInput has no trusted is_synthetic field. Pasted email is persisted raw at submit_case;
masking PII later is not a synthetic boundary. SourceRecord defaults is_synthetic=False;
setting it true from client input also is not proof of approved content. Tests must cover
direct calls and internal worker paths, not just hidden navigation/disabled widgets.

## 4. Design options và recommendation

| Dimension | A — Restricted application/service mode | B — Authenticated proxy |
| --- | --- | --- |
| Judge first access | No account for approved demo operations | Whole-site authentication requires credentials |
| Privileged protection | Guards before effects in all relevant service/SQL helper paths | Protects ingress, does not itself implement in-app role/action boundaries |
| Modules/files | Infra + Runtime + Corpus + UI/Verify, listed below | Proxy/Docker/config and credential operations; granular public/admin separation needs app work |
| Contract | New authorization/mode boundary; CONTRACT-CHANGE REQUIRED | Access/login behavior differs from current no-login demo contract |
| Regression | Seed/worker/pipeline must stay valid | Origin bypass, WebSocket routing/timeouts and authentication scope |
| Railway/cost | Existing service; no added dependency/service proposed | Private origin plus proxy possible; added service credit/cost not approved |
| Timebox estimate | 6–8h implementation + checks | 2–4h for whole-site gate; does not fulfill anonymous demo alone |
| Rollback | Keep private; approved previous image/config with backups | Withdraw proxy ingress; keep origin private |

Recommend A as smallest complete anonymous-demo solution. Whole-site proxy authentication
is a possible fallback only if Coordinator changes judge-access requirements. Filtering
only named Streamlit page URLs is not treated as sufficient: source uses one st.navigation
app, and Streamlit interactions use browser WebSocket sessions.

References: [Streamlit architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture),
[NGINX HTTP authentication](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html),
[WebSocket proxying](https://nginx.org/en/docs/http/websocket.html),
[Railway private networking](https://docs.railway.com/networking/private-networking).
No provider auth feature, price/credit or proxy runtime was tested in this preflight.

## 5. Proposed authorization contract — approval needed

**CONTRACT-CHANGE REQUIRED:** define shared authorization guard/interface and mode
semantics across modules; obtain approval before code. Do not change existing public
function signatures, dataclasses, SQLite schema, audit action catalog, routing or policy.
If implementation requires those changes, STOP for a separately approved precise contract.

1. Server mode `restricted_demo` defaults safe; explicit local/private mode preserves
   trusted local workflow. Invalid mode stops startup. Guests cannot select mode via
   request, query, widget, actor, session state or a caller-provided privilege boolean.
2. Deny public admin/human mutations even with forged ADMIN/HUMAN/SYSTEM actors;
   use existing actor types only for trace, assigned by server, not authorization.
3. Fixed public sample ID resolves to approved canonical input/hash on server. No free
   email text, source upload/URL, human reason or client is_synthetic assertion accepted.
4. Proposed public set: DEV_ROUTINE, DEV_AUTHORITY, DEV_FACT and Verify V01–V04,
   based on approved recorded inputs; read results/escalation cards/corpus/audit/metrics.
   Existing UI sample texts and inbox entries are not automatically accepted replay inputs.
5. Guest human R11/approval/correction/cancel/retry/pause/override/source mutations are
   DENY in this first proposal. Private R11 validation remains. Coordinator must confirm
   this judge-flow limitation before READY or precisely authorize a bounded alternative.
6. Lower-level corpus guards retain trusted canonical seed initialization: exactly the
   approved six source IDs/hash/bytes. The exception must not be minted by client values
   or a generic actor prefix. Test import-time seed and original restoration explicitly.
7. Startup checks replay configuration, keyless runtime and synthetic DB contents.
   Invalid corpus/input/jobs stop safely; no silent wipe, reset, relabeling or seed overwrite.
8. Input guard occurs before raw persistence and cached-result lookup; do not use unknown
   case_id to read another case. process_case preserves its fail-safe result contract.
9. Allow normal pipeline/worker persistence only for validated canonical cases; manual
   controls and forged schedule/dispatch/resume calls cannot bypass that validation.
10. Deny before business audit/DB/network/provider side effects. Safe diagnostic logs
    omit denied payloads/PII; no new audit action is proposed. UI explains restricted mode
    in Vietnamese; hidden buttons are only presentation of the backend denial.

## 6. Scope, ownership và exclusions

Coordinator confirms every file below before READY. One hotfix Owner is authorized
across Runtime/Corpus/UI/Infra; independent security/runtime reviewer is assigned.

| Ownership domain | Proposed editable files |
| --- | --- |
| Infra / startup | infra/demo_access.py (new small standard-library guard), infra/settings.py, infra/llm.py, run_local.py |
| Runtime | core/worker.py, core/pipeline.py, core/controls.py, core/dispatch.py, core/resume.py, core/explain.py |
| Corpus Admin | corpus/intake.py, corpus/workflow.py, corpus/lifecycle.py, corpus/metadata.py, corpus/store.py, corpus/seed.py |
| UI / Verify | streamlit_app.py, pages/1_Xu_ly_email.py, pages/2_Hang_cho_duyet.py, pages/3_Quan_tri_quy_dinh.py, pages/4_Nhat_ky_kiem_toan.py, pages/5_Verify.py, verify/harness.py |
| Public synthetic manifest | data/restricted_demo_inputs.json (new, Coordinator-approved inputs/hashes only, no answers or private evaluation data) |
| Validation / evidence | tests/test_restricted_demo.py (new), mode/runbook documentation, report under assigned Task ID |
| Technical contract | PROJECT_SPEC.md, only approved authorization/mode section |

Read-only: seed bytes, existing tests/expected labels, BASE24 manifest/cassettes, policy,
existing types/schema/audit catalog. pages/6 metrics remains read-only unless investigation
proves a new write or non-demo data path requiring Coordinator scope amendment.

Out of scope: policy/decision/routing edits, schema/migrations, core/types.py, new audit
actions, Gold/Set A/Set B, record/LIVE/email, cassette provenance, authentication subsystem,
UI redesign/refactor, unrelated remediation, Railway/domain/billing, frozen baseline,
PR #51 merge and task DONE. Keep guards small; do not introduce general RBAC framework.

## 7. Dependencies và acceptance criteria

Dependencies: D1–D4; formal contract/ownership/CONTRACT-CHANGE READY; approved public
input/workflow manifest; M6-T02/T03/T05 evidence/BASE24. M6-T04 deployment context fixes
in PR #51 require their own integration/disposition before the new image build.

- AC1 Guest Authorization: fake names/actors/query/session state cannot gain role/action.
- AC2 Server-side Enforcement: direct privileged service/SQL-helper calls denied before
  DB/corpus/version/audit/job/provider/network effects, even if bypassing UI.
- AC3 Synthetic Boundary: arbitrary input/upload/URL, modified samples, invalid IDs/paths
  and caller is_synthetic flags denied; canonical seed remains valid/idempotent.
- AC4 Allowed Workflows: Coordinator-approved public set uses real shared pipeline/
  harness; read-only human queue creates no decision records.
- AC5 Regression: same tested revision retains private offline critical 4/4, Verify 4/4,
  BASE24 replay 24/24 with zero miss. Restricted mode validates public subset separately
  and denies privileged mutations. Do not claim private R11 as guest R11 acceptance.
- AC6 No External Effects: live/record/wrong config or checked credentials rejected in
  restricted mode; network/provider/email denied in tests; LIVE=0; no denied raw PII stored.
- AC7 Evidence: .md report, baseline/tested SHA, diff, commands/logs, AC results, known
  limits, PR, Owner self-review and independent review on the exact tested revision.

## 8. Required validation

Use fresh isolated synthetic DB before import and network/provider deny guards. No new
tests execute against live DEMO or developer DB. Preserve unrelated dirty files/evidence.

1. Matrix for forged ADMIN/APPROVER, ADMIN:local, HUMAN:local, SYSTEM and role/state flags.
2. Direct backend calls: intake text/file/URL/recheck, metadata/workflow/lifecycle/store;
   page decision/draft/approval helpers; controls/dispatch/retry/resume/queue operations.
3. Snapshot DB/corpus/version/audit/jobs before–after rejection; confirm zero side effect
   and no provider/cache/network call. No request payload in error/audit logs.
4. Whitelist input/hash and Verify path bypass; canonical seed auto-import/restoration,
   fresh DB/idempotence; client synthetic flag and corrupted/non-demo DB rejected safely.
5. Relevant existing suites: tests/test_runtime_worker.py, test_m3_t06_human_control.py,
   test_m3_atomicity.py, test_m3_failsafe.py, test_source_workflow.py,
   test_database_isolation.py, test_runtime_replay_audit.py and direct controls/dispatch/
   store/lifecycle coverage selected by discovered callers. Verify filenames before run.
   Retain known failures; do not edit expected/fixtures to reach green.
6. Same-revision private BASE24/critical/Verify/R11 and restricted guest subset/denials.
   Checks are new revision evidence, not a re-label of old private 61e31e8 results.
7. Authorized private image/env/pack/secret scan/startup/health; browser outside container
   over approved private route and 2–3 sessions; persistence across actual restart on an
   approved disposable DB. Public external HTTPS is verified only after public gate release.

## 9. Deliverables, timebox và Stop Conditions

Deliverables: scoped code/tests + approved public input manifest; report .md under actual
Task ID; runbook/mode contract; tested SHA/diff/commands/logs/limitations; PR to dev;
Owner self-review and independent reviewer verdict. No rollout/domain is performed by
the hotfix merely because its tests pass; M6-T04 owns later approved deployment acceptance.

Timebox proposal: 6–8h implementation/validation + 45m self-review + 90m independent
review. Coordinator sets actual dates/cap/buffer; estimates are not approval.

STOP on missing READY/ownership/contract/input decisions; baseline drift/conflict;
required schema/type/audit/policy/interface change outside precise approval; blocked
seed/worker regression, replay miss/security failure, LIVE/email/PII risk, possible data
loss, unapproved resource/billing, timebox overrun or changed frozen revision. Report
problem, impact, evidence and needed decision; do not expand scope or repair baselines.

## 10. Continuation chain

Contract READY → hotfix → tests/evidence → independent review/Coordinator acceptance
→ approved integration/deploy exact SHA → private redeploy → new-image safety/runtime/
browser/concurrency/persistence → public gate decision → HTTPS URL → M6-T04 final acceptance.

Current blockers: assignment/contract approval, accepted guest/judge workflow list,
authorization contract approval and later exact deployment/public gates. No implementation
has been performed. Coordinator must create/approve the official card; this document does
not create or edit Trello tasks or grant a teammate production access.
