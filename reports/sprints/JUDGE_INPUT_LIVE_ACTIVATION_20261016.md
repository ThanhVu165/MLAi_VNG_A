# JUDGE-INPUT-LIVE — GO-LIVE activation evidence — 2026-10-16

## Result

**RESULT: BLOCKED**

The authorized activation stopped during provider-access preflight. A read-only model
metadata request using the Railway service's configured `OPENAI_API_KEY` returned HTTP
`401 Unauthorized` for `GET /v1/models/gpt-6-luna`. This is an explicit Stop Condition.
No completion was requested, Judge LIVE was not enabled, no grant was issued, and no
synthetic email was submitted.

## Task and authority

- Task ID: `JUDGE-INPUT-LIVE`.
- Owner: Deployment / Judge LIVE Activation Owner — Codex, confirmed by the Coordinator
  authorization supplied for this run.
- Authorized boundary: one synthetic email, at most three application provider attempts,
  USD 0.01 application envelope, internal testing only, one operator/browser session.
- Restrictions observed: no Git checkout/reset, no source or SQLite schema change, no new
  Railway service, no public access, no email dispatch.
- Activation timestamp: 2026-10-16 00:46 ICT (`+07:00`).

## Revalidated baseline

| Control | Evidence |
|---|---|
| Railway target | `exodia-restricted-demo / production / exodia-web` |
| Deployment | `a570476e-969a-4503-ae42-fb333d08db8b`, `SUCCESS`, one active service/replica |
| Railway deployment message | Pins source `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| Runtime source | Normalized SHA-256 for `Dockerfile`, Judge access/gateway/operator, LLM adapter and email page matched the same files at the pinned Git SHA |
| Health | `https://exodia-web-production.up.railway.app/_stcore/health` returned HTTP 200, body `ok`, before and after the access probe |
| Database | `/runtime/app.db`; `PRAGMA integrity_check=ok`; `user_version=2`; 724,992 bytes; mounted under `/runtime` |
| Backup/rollback | Prior pre-cutover evidence records the recoverable source archive `fe8c2dbca013e9344a678ba52f70588495c897ef` and SQLite backup outside Git. Their contents were not restored or mutated in this run. |
| Replica | Railway status showed one linked online service; no scaling change was made |

The current database contained 34 pre-existing cases, zero `case_jobs`, and zero Judge
ledger/settings rows. It contained 17 historical `SEND_SCHEDULED` audit events and zero
`SEND_DISPATCHED` events; because no Judge case was created in this run, none is attributable
to this activation attempt.

## Model, price, and API access

- Approved model: `gpt-6-luna`; no substitute was selected.
- Official model documentation confirms Chat Completions and Structured Outputs support:
  <https://developers.openai.com/api/docs/models/gpt-6-luna>.
- Official Standard short-context rates at validation time were USD 0.10/M input tokens
  and USD 0.50/M output tokens:
  <https://developers.openai.com/api/docs/pricing>.
- The 24,000 input + 6,000 output application envelope therefore remains below USD 0.01
  at those rates.
- `OPENAI_API_KEY`: present in Railway; value never printed or stored in evidence.
- Access probe: `GET /v1/models/gpt-6-luna` with the configured Railway key.
- Provider response metadata: HTTP `401 Unauthorized`; response body and credentials were
  not persisted. Completion requests: 0. Billable token usage: 0. Application ledger debit:
  0.
- Decision: **STOP** under the explicit 401 condition. The key/model access is not usable
  for this activation.

## LIVE configuration and grant

Configuration was re-read after the failed probe and remained unchanged:

```text
APP_MODE=restricted_demo
LLM_MODE=replay
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-6-luna
JUDGE_INPUT_ENABLED=0
JUDGE_LIVE_ENABLED=0
LLM_CACHE=0
DATABASE_PATH=/runtime/app.db
JUDGE_LIVE_MODEL=MISSING
JUDGE_ISSUER_SECRET=MISSING
JUDGE_GATEWAY_SOCKET=MISSING
OPENAI_API_KEY=PRESENT (REDACTED)
```

- `JUDGE_ISSUER_SECRET` was not generated because provider access failed first.
- Gateway/socket was not enabled.
- Operator/browser grant: not provisioned.
- Grant revoked: not applicable; no grant ever existed. Judge ledger rows remained zero.
- No Railway variables, deployment, replica count, database schema, or application source
  were changed.

## Synthetic case, Audit, and no-send

- Synthetic case result: not run.
- Route (`AUTO_REPLY` / `ESCALATE`): not produced.
- Draft/citations: not produced.
- Structured output: not requested.
- Usage/cost ledger: no Judge reservation or LIVE-attempt row; zero completion tokens and
  zero application cost.
- Audit: no Judge case/audit trail was created; production audit was left unchanged by the
  activation flow.
- No-send: zero `case_jobs`, zero `SEND_DISPATCHED`, Judge switches disabled, Replay mode
  retained. The database's 17 historical `SEND_SCHEDULED` events predate and are unrelated
  to this blocked run.

## Risks and required next step

- Blocking risk: the configured Railway key is rejected with 401. It may be invalid,
  expired, revoked, malformed, or scoped to a different API endpoint/project.
- Backup availability is supported by the immediately preceding deployment evidence, but
  no destructive restore drill was performed during this activation attempt.
- Do not retry this key, change model, activate the Judge switches, issue a grant, or submit
  an email under the current authorization.
- Coordinator must replace or repair the dedicated Railway `OPENAI_API_KEY`, independently
  verify project billing/quota and `gpt-6-luna` access, then issue a new explicit GO-LIVE.
  The next run must restart from preflight and is still limited to one synthetic email.

## Required output summary

- Railway deployed SHA: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Model: `gpt-6-luna` (documented compatible; no substitution).
- API access: **BLOCKED — HTTP 401**.
- LIVE configuration: unchanged, disabled, Replay retained.
- Operator/session grant: not created.
- Synthetic case result: not run.
- AUTO_REPLY / ESCALATE: not produced.
- Draft/citations: not produced.
- Usage/cost: 0 completion tokens; USD 0 application ledger debit.
- Audit: no Judge case or Judge ledger rows created.
- No-send: PASS for this run; no case/job/dispatch created.
- Grant revoked: N/A; never issued.
- Risks: invalid/unusable provider credential; backup not restore-tested in this run.
- NEXT STEP: repair the dedicated key and obtain a new Coordinator GO-LIVE; do not proceed
  on the current authorization.

## Resume after API key rotation — 2026-10-16 00:54 ICT

Coordinator supplied a new one-email GO-LIVE and stated that `OPENAI_API_KEY` had been
rotated. The activation owner repeated preflight from the disabled Replay state.

**Resume result: BLOCKED.** The configured Railway key again returned HTTP `401
Unauthorized` for `GET /v1/models/gpt-6-luna`. This request used the value injected by
`railway run`; the key was not printed, logged in this report, or copied to a file. No
completion request was made and the failed metadata request was not retried.

### Resume preflight evidence

| Check | Result |
|---|---|
| Railway target | VERIFIED `exodia-restricted-demo / production / exodia-web` |
| Active deployment | `a570476e-969a-4503-ae42-fb333d08db8b`, `SUCCESS` |
| Production source | Deployment message still pins `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| Restart/deployment after rotation | **NOT VERIFIED** — Railway deployment history exposed no newer deployment ID than the active deployment created on 2026-10-16 00:05 ICT |
| Health | PASS before and after the probe: HTTP 200, body `ok` |
| Database | PASS: `/runtime/app.db`, integrity `ok`, schema version 2, 34 cases, zero jobs, zero Judge ledger rows |
| Backup | Prior pre-cutover backup evidence remains the rollback reference; no restore drill or backup mutation was performed in this blocked resume |
| API key presence | PRESENT in Railway; value redacted |
| API authentication | **FAIL — HTTP 401** |
| Model access | **FAIL — access to `gpt-6-luna` not established** |
| Billing/quota | **NOT VERIFIED**; authentication failed first and production has no `OPENAI_ADMIN_KEY` for the documented Administration APIs |

OpenAI's current Administration API documentation states that organization cost and hard
spend-limit endpoints require a separate Admin API key. A normal project inference key is
not sufficient evidence for those controls:

- <https://developers.openai.com/api/docs/guides/admin-apis>
- <https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs>

### Resume stop and no-mutation proof

The 401 and missing billing/quota verification each independently require STOP. The owner
therefore did not configure `JUDGE_LIVE_MODEL`, create `JUDGE_ISSUER_SECRET`, enable the
gateway, issue an operator grant, or submit a synthetic email. Post-check remained:

```text
APP_MODE=restricted_demo
LLM_MODE=replay
OPENAI_MODEL=gpt-6-luna
JUDGE_INPUT_ENABLED=0
JUDGE_LIVE_ENABLED=0
JUDGE_LIVE_MODEL=MISSING
JUDGE_ISSUER_SECRET=MISSING
JUDGE_GATEWAY_SOCKET=MISSING
DATABASE_PATH=/runtime/app.db
```

- Synthetic result, route, draft and citations: not produced.
- Provider completion attempts/tokens/application cost: `0 / 0 / USD 0`.
- Audit: no Judge case or Judge ledger row created.
- No-send: zero jobs and zero `SEND_DISPATCHED`; historical `SEND_SCHEDULED=17` unchanged.
- Grant revoked: N/A; no grant was issued.
- Trello handoff: skipped at the user's explicit instruction during this resume.
- Required next step: confirm the rotated value was applied to this exact Railway
  project/environment/service and caused a restart, then validate the key outside LIVE.
  Billing/quota evidence and a new Coordinator GO-LIVE are still required before activation.

## Read-only authentication recheck — 2026-10-16 01:09 ICT

Coordinator confirmed another key update and authorized one authentication-only metadata
request after Railway deployment completion. This authorization did not include Judge LIVE
activation, a completion request, a grant, or a synthetic case.

**Authentication result: AUTH_PASS.** Production PID 1 called
`GET /v1/models/gpt-6-luna` once and received HTTP `200` with model ID
`gpt-6-luna`. OpenAI request ID: `a58b3da9-84c4-404b-8716-7689ebf94ba8`.

### Recheck validation

| Acceptance criterion | Result |
|---|---|
| AC1 deployment/target/health | PASS — `exodia-restricted-demo / production / exodia-web`; deployment `2317dbc5-75bc-46d8-9080-9992dd373c4e` is `SUCCESS`; health HTTP 200 `ok` |
| Source provenance | PASS — deployment message pins `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| AC2 runtime key | PASS — control-plane key and production PID 1 key were present and their in-memory SHA-256 fingerprints matched; neither fingerprint nor key was printed or stored |
| AC3 model metadata | PASS — one request, HTTP 200, exact model ID `gpt-6-luna` |
| Billing/quota | **NOT VERIFIED** — the metadata response exposed no rate-limit quota headers and production has no `OPENAI_ADMIN_KEY`; this gate is not waived |
| AC4 Judge state | PASS — `APP_MODE=restricted_demo`, `LLM_MODE=replay`, `JUDGE_INPUT_ENABLED=0`, `JUDGE_LIVE_ENABLED=0`; no issuer secret or gateway socket |
| AC5 no completion/no-send | PASS — zero completion calls; zero jobs; zero `SEND_DISPATCHED`; no grant |
| Database/no mutation | PASS — integrity `ok`, schema version 2, 42 existing cases, 21 historical `SEND_SCHEDULED`, zero Judge ledger rows |

### Self-review

- Exactly one OpenAI metadata request was made from the credential in production PID 1.
- No response body beyond the model ID, no key and no fingerprint entered evidence.
- No completion, Judge case, reservation, ledger debit, grant, email, configuration write,
  deployment action, restart action, code change or SQLite write was performed.
- This result establishes API authentication and model visibility only. It does not prove
  billing headroom, project hard limits, structured-output behavior or LIVE pipeline safety.
- Result for this task: `AUTH_PASS`; activation remains unauthorized and blocked on a new
  Coordinator decision packet that explicitly addresses billing/quota.
