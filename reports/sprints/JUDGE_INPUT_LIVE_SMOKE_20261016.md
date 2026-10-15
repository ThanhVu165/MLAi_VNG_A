# JUDGE-INPUT-LIVE — authorized LIVE smoke preflight — 2026-10-16

## Result

**RESULT: BLOCKED**

The production deployment, health, database, authentication, and disabled safety state
passed read-only preflight. The LIVE smoke did not start because current project limits
could not be tied to the newly rotated production credential using current authoritative
evidence. This is the Coordinator's explicit HOLD condition. No LIVE configuration,
gateway, grant, Judge case, completion request, database write, or email send occurred.

## Task and authority

- Task ID: `JUDGE-INPUT-LIVE`.
- Role: Deployment / Judge LIVE Owner — Codex.
- Baseline: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Authorization: prepare one internal synthetic LIVE smoke, but execute only after project
  limits are verified; otherwise HOLD.
- Approved envelope if the gate passes in a later run: one synthetic email, at most three
  provider attempts, and USD 0.01 application budget.
- Restrictions observed: no model substitution, code/schema change, merge, extra case, or
  email dispatch.
- Preflight completed at 2026-10-16 01:16 ICT (`+07:00`).

## Railway and runtime preflight

| Check | Result |
|---|---|
| Project / environment / service | `exodia-restricted-demo / production / exodia-web` — PASS |
| Deployment | `2317dbc5-75bc-46d8-9080-9992dd373c4e` — `SUCCESS` |
| Active instance | `a45cfbad-3d36-4642-be12-d93b64143e72` — `RUNNING` |
| Source | Deployment message pins `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| Health | HTTP `200`, body `ok`, before and after limits investigation |
| OpenAI authentication | HTTP `200` for metadata `GET /v1/models/gpt-6-luna` |
| Model | `gpt-6-luna`; no substitute selected |

The metadata request was read-only and was not a completion. It returned no project
identity or rate-limit headers that could bind the current credential to project-limit
evidence.

## Database and no-send preflight

- Database: `/runtime/app.db`, opened read-only with `PRAGMA query_only=ON`.
- `PRAGMA integrity_check`: `ok`.
- `user_version`: `2`.
- Size at observation: `860160` bytes.
- Current rows: 42 cases, 394 audit events, zero `case_jobs`.
- Judge settings/ledger rows: zero C1, zero C2-A, zero LIVE-attempt rows.
- Current audit totals: `SEND_SCHEDULED=21`, `SEND_DISPATCHED=0`.

The existing case/audit totals are production state observed read-only; none was created
or modified by this blocked preflight. No Judge case exists for this task.

## Safety configuration

Production PID 1 remained:

```text
APP_MODE=restricted_demo
LLM_MODE=replay
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-6-luna
OPENAI_REASONING_EFFORT=none
LLM_CACHE=0
JUDGE_INPUT_ENABLED=0
JUDGE_LIVE_ENABLED=0
JUDGE_LIVE_MODEL=MISSING
JUDGE_ISSUER_SECRET=MISSING
JUDGE_GATEWAY_SOCKET=MISSING
DATABASE_PATH=/runtime/app.db
```

The gateway was not configured, no issuer secret was created, no browser session was
provisioned, and no grant was issued. Grant revocation is therefore not applicable.

## Billing and project-limit evidence

### Evidence available

- Coordinator reported approximately USD 9 available for this authorization. No raw
  payment or account data is reproduced here.
- Repository evidence from the authenticated OpenAI dashboard on 2026-10-13 records the
  then-current Default project at Build tier with `gpt-6-luna` allowed, Standard service,
  5,000 RPM, 2,000,000 TPM, 20,000,000 TPD, and a configured project spend limit.
- That private dashboard record was about 49.9 hours old at this preflight and recorded
  zero settings changes and zero provider attempts during its own observation.
- Official OpenAI documentation states that limits are organization- and project-level,
  model-dependent, and that the approved monthly usage limit is separate from configurable
  organization/project spend limits:
  <https://developers.openai.com/api/docs/guides/rate-limits>.
- The official Administration API exposes project rate limits and project spend limits,
  but requires administrative access:
  <https://developers.openai.com/api/reference/python/resources/admin/subresources/organization/subresources/projects>.

### Blocking gap

- The Railway credential was rotated after the 2026-10-13 dashboard observation.
- The current production key does not match the credential recorded in that dashboard
  evidence. No key or fingerprint was printed or stored during this comparison.
- Production has no `OPENAI_ADMIN_KEY`, `OPENAI_PROJECT_ID`, or `OPENAI_ORG_ID` variable.
- The current metadata response did not include project identity or rate-limit headers, so
  it cannot prove that the rotated key belongs to the project whose limits were recorded.
- The reported balance establishes Coordinator-provided billing headroom, but does not by
  itself establish the current credential's project rate/spend controls.

**Project limits: NOT VERIFIED for the current production credential.** The condition for
LIVE execution is therefore unmet.

## Stop disposition

- LIVE smoke: not run.
- Provider completion attempts: `0 / 3`.
- Synthetic email: not submitted.
- Route: not produced.
- Draft: not produced.
- Citations: not produced.
- Provider token usage: `0 input / 0 output` for completions.
- Application cost: USD `0.00`; no application reservation or ledger debit.
- Audit for Judge case: not created.
- Email dispatch: none; current global `SEND_DISPATCHED=0`.
- Grant revoked: N/A; grant was never issued.
- Rollback: not required because no production mutation occurred.

## Validation and self-review

- PASS: exact Railway project/environment/service and active deployment revalidated.
- PASS: source message pins the required SHA and health remains `200 ok`.
- PASS: database integrity/schema/path and zero-job/no-dispatch state checked read-only.
- PASS: disabled Replay/Judge configuration confirmed before and after limits investigation.
- PASS: no secret, key fingerprint, payment detail, private project identifier, response
  request ID, or raw provider header is included in this report.
- PASS: no completion endpoint, gateway/session, grant, case, audit write, configuration
  write, deployment, or send path was invoked.
- BLOCKED: current project rate/spend limits are not authoritatively bound to the rotated
  production credential.
- Required handoff checks: `git diff --check`, secret-pattern scan, exact-file staging,
  commit, push, and PR read-back.

## Risks and next step

- Do not infer current project limits from a successful model metadata request.
- Do not reuse the pre-rotation dashboard credential binding as proof for the rotated key.
- Coordinator must provide a fresh authenticated Developer Console capture or approved
  sanitized evidence that identifies the current production key's project and shows
  applicable `gpt-6-luna` rate limits plus project hard-spend headroom above USD 0.01.
- After that evidence is accepted, issue a new explicit resume instruction. Restart from
  preflight and run at most the already authorized one synthetic email; do not run an extra
  metadata or completion probe merely to manufacture limit evidence.

## Deliverable summary

- Result: `BLOCKED`.
- Deployment ID / SHA: `2317dbc5-75bc-46d8-9080-9992dd373c4e` /
  `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Billing/quota evidence: Coordinator reports about USD 9 available; project limits for
  the rotated credential are NOT VERIFIED.
- Model / provider attempts: `gpt-6-luna` / `0` completion attempts.
- Route / draft / citations: not produced.
- Token usage / application cost: `0 / 0` completion tokens; USD `0.00`.
- Audit/no-send: no Judge audit; zero Judge ledger rows; `case_jobs=0`;
  `SEND_DISPATCHED=0`.
- Grant revoked: N/A; never issued.
- Evidence PR: #76 (`codex/final-deploy-closeout`).
- Next step: fresh current-project limits evidence, then explicit Coordinator resume.
