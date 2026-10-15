# JUDGE-INPUT-LIVE — authorized one-email LIVE smoke — 2026-10-16

## Result

**RESULT: LIVE_SMOKE_PASS**

Exactly one synthetic email was processed through OpenAI LIVE on the approved production
deployment and model. The application produced a grounded preview, stayed within the
three-attempt and USD 0.01 application envelope, created no send job, and dispatched no
email. The single grant was revoked, the only browser session was closed, and production
was returned to Replay with both Judge switches OFF before this report was finalized.

This result is evidence for Coordinator review only. It does not mark the project DONE,
grant access to another operator, or authorize another LIVE case.

## Authority and exception

- Task ID: `JUDGE-INPUT-LIVE`.
- Role: Deployment / Judge LIVE Owner — Codex.
- Baseline/source SHA: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Coordinator authorized one internal synthetic email, model `gpt-6-luna`, at most three
  provider attempts, one operator/browser session, and USD 0.01 application budget.
- Coordinator reported approximately USD 9 available and explicitly accepted the risk
  that current project limits were not verified in the refreshed dashboard.
- The workflow and technical contract allow a Coordinator-authorized LIVE grant while
  preserving the in-application budget ledger, kill switches, model pin, audit, and
  no-send controls. No contract or runtime guard had to be bypassed.
- Billing/quota remains **NOT VERIFIED**; the exception does not convert it to VERIFIED.

## Production target and deployment

| Check | Result |
|---|---|
| Project / environment / service | `exodia-restricted-demo / production / exodia-web` — PASS |
| LIVE deployment | `9264b511-452d-414e-b3a7-85e268e47f79` — `SUCCESS` |
| LIVE instance | `e11da587-0cef-4215-b344-d8607f33ccd2` — `RUNNING` during smoke |
| Rollback deployment | `38e8efce-8824-4f16-8074-7d07f8f86a56` — `SUCCESS` |
| Rollback instance | `f7977cf6-01e8-44cd-bf14-5b8135a3b989` — `RUNNING` |
| Source provenance | Both deployment messages pin `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| Post-rollback health | HTTP `200`, body `ok` |

The Railway target and active deployment were re-read with
`npx --yes @railway/cli@latest` before final verification.

## Synthetic input and outcome

- Case ID: `c_01M50D10N2Q0VW99R6VSZNGP90`.
- Channel: paste.
- Sender: `judge-new@example.invalid`.
- Subject: `Hỏi lệ phí phúc khảo học phần`.
- Body: a synthetic Vietnamese question about the fee and procedure for a course grade
  review; it contained no real personal data.
- Final status: `PREVIEW_READY`; `send_deadline=NULL`.
- Route: `AUTO_REPLY` under policy rule `P05`; no escalation.
- Reason: routine information request with current authority and no decision by an
  authorized human required.

Draft subject: `Lệ phí và hướng dẫn phúc khảo học phần`

Draft body:

> Lệ phí phúc khảo là 150.000 đồng cho mỗi học phần; sinh viên nộp lệ phí theo hướng dẫn
> trên cổng dịch vụ sinh viên. [PK-2026-204:seed:2]
>
> Hồ sơ phúc khảo sử dụng Mẫu PK-01 và cần nộp trong thời hạn công bố điểm; hồ sơ phải ghi
> đúng mã học phần và học kỳ liên quan. [PK-2026-204:seed:5]

- Retrieved evidence: `PK-2026-204:seed:2`, `PK-2026-204:seed:3`,
  `PK-2026-204:seed:5`.
- Draft citations: `PK-2026-204:seed:2`, `PK-2026-204:seed:5`.
- Grounding: PASS; guard failures: none.

## Usage and budget reconciliation

| Control | Observed result |
|---|---|
| Provider/model | OpenAI / `gpt-6-luna`; no model substitution |
| Provider attempts | `3 / 3`; no attempt beyond the approved cap |
| Provider usage | 6,362 input tokens; 328 output tokens |
| LIVE attempt ledger | `pending=false`, `blocked=false`; 6,000 output tokens reserved across three attempts |
| Application reservation | 24,000 input + 6,000 output tokens; 10,000 micro-USD = USD 0.01 |
| Usage-priced estimate | USD 0.0008002 using USD 0.10/M input and USD 0.50/M output |
| C2 request phase | `FINISHED` |
| Unresolved reservations/HOLD | none (`RESERVED=0`, `PROCESSING=0`, `HOLD=0`) |

The USD 0.0008002 figure is an application-side estimate from provider-reported token
usage, not an independently verified provider invoice. The conservative USD 0.01 debit
remains recorded and was not refunded during revocation or rollback.

## Audit, no-send, and access closure

The case audit sequence is complete and ordered:

1. `CASE_RECEIVED`
2. `CASE_SANITIZED`
3. `FACTS_EXTRACTED`
4. `PREPOLICY_LOCKED`
5. `EVIDENCE_RETRIEVED`
6. `EVIDENCE_VALIDATED`
7. `POLICY_DECIDED`
8. `DRAFT_GENERATED`
9. `CASE_RESOLVED`

- Case jobs: `0`.
- Case `SEND_DISPATCHED`: `0`.
- Global production `SEND_DISPATCHED`: `0` after rollback.
- No real email address or real email content was used; no email was sent.
- C1 ledger: one request, one grant, one session, no active case.
- C2 ledger: one provisioning record, one request, one revocation record.
- The only grant is present in the durable revocation list; all recorded grants are
  revoked.
- Exactly one browser session was used and closed after the case.

## Rollback and final production state

Production PID 1 on rollback deployment `38e8efce-8824-4f16-8074-7d07f8f86a56`
reported:

```text
APP_MODE=restricted_demo
LLM_MODE=replay
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-6-luna
OPENAI_REASONING_EFFORT=none
LLM_CACHE=0
JUDGE_INPUT_ENABLED=0
JUDGE_LIVE_ENABLED=0
DATABASE_PATH=/runtime/app.db
```

The grant was revoked before rollback. The OFF switches and Replay mode prevent another
Judge submission or LIVE provider call without a new explicit configuration change and
authorization.

## Validation and self-review

- PASS: exact Railway project/environment/service, deployment status, active instance,
  source SHA, and public health were revalidated after rollback.
- PASS: production PID 1, not only the control plane, reports Replay and both Judge
  switches OFF.
- PASS: SQLite was opened read-only with `query_only=ON`; `PRAGMA integrity_check=ok` and
  `user_version=2`.
- PASS: the final case snapshot, audit sequence, zero jobs, zero dispatches, C1/C2
  ledgers, revocation, and LIVE-attempt ledger reconcile.
- PASS: no reservation or HOLD remains unresolved; no retry was made after the third
  provider attempt.
- PASS: no API key, issuer secret, grant token, hash/fingerprint, private project ID,
  provider request ID, payment detail, or raw provider header is included here.
- PASS: no source code, database schema, Judge case, ledger, or configuration was edited
  after the one authorized case except the required production rollback variables.
- Required repository handoff checks: `git diff --check`, secret-pattern scan,
  exact-file staging, commit/push, and PR #76 read-back.

## Risks and next step

- Project billing/rate/spend limits remain **NOT VERIFIED** against a refreshed dashboard;
  this smoke relied on the Coordinator's one-case exception and reported balance.
- Three attempts consumed the full provider-attempt allowance even though token usage and
  the usage-priced estimate remained below the application envelope.
- The smoke proves this one controlled path only; it does not authorize another case,
  operator, or browser session.
- Coordinator should review this evidence and decide whether to accept the smoke. Any
  subsequent LIVE use requires a separate explicit grant/authorization; keep production
  in Replay/OFF meanwhile.

## Deliverable summary

- Result: `LIVE_SMOKE_PASS`.
- LIVE deployment / rollback deployment: `9264b511-452d-414e-b3a7-85e268e47f79` /
  `38e8efce-8824-4f16-8074-7d07f8f86a56`.
- Source SHA: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Billing/quota: Coordinator reported about USD 9; project limits **NOT VERIFIED** under
  the approved one-case exception.
- Model / provider attempts: `gpt-6-luna` / `3`.
- Usage / cost: 6,362 input, 328 output; USD 0.0008002 usage-priced estimate; USD 0.01
  conservative application debit.
- Audit/no-send: complete case audit; zero jobs; zero `SEND_DISPATCHED`.
- Grant revoked: yes; no active reservation/HOLD.
- Final state: `LLM_MODE=replay`, `JUDGE_INPUT_ENABLED=0`, `JUDGE_LIVE_ENABLED=0`.
- Evidence PR: #76 (`codex/final-deploy-closeout`).
- Next step: Coordinator review; do not run another LIVE case or mark DONE.
