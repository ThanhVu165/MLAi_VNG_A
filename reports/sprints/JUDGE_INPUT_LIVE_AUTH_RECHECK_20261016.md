# JUDGE-INPUT-LIVE — OpenAI authentication recheck — 2026-10-16

## Result

**RESULT: AUTH_PASS**

The production PID 1 credential matches the current Railway control-plane value, and
exactly one read-only `GET /v1/models/gpt-6-luna` request from the production container
returned HTTP `200` with model ID `gpt-6-luna`. Authentication and model access pass.
Billing/quota remains **NOT VERIFIED**. Judge LIVE remains OFF; this run created no grant,
case, ledger row, database/configuration change, completion request, or email send.

## Task and authority

- Task ID: `JUDGE-INPUT-LIVE`.
- Role: Deployment / LIVE Preflight Owner — Codex.
- Mode: read-only authentication preflight under the Coordinator request supplied for
  this run; no authority to enable LIVE or call a completion.
- Repository: `ThanhVu165/MLAi_VNG_A`.
- Required reference source: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Reviewed before execution: `AGENT.md`, `docs/TEAM_WORKFLOW.md`, `PROJECT_SPEC.md`, and
  PR #76 including `reports/sprints/JUDGE_INPUT_LIVE_ACTIVATION_20261016.md`.
- Recheck completed at 2026-10-16 01:09 ICT (`+07:00`).

## Production target and deployment

| Check | Result |
|---|---|
| Railway project | `exodia-restricted-demo` — VERIFIED |
| Environment | `production` — VERIFIED |
| Service | `exodia-web` — VERIFIED |
| Deployment ID | `2317dbc5-75bc-46d8-9080-9992dd373c4e` |
| Deployment status | `SUCCESS` |
| Active instance | `a45cfbad-3d36-4642-be12-d93b64143e72` — `RUNNING` |
| Source SHA | Deployment message pins `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| Health before request | HTTP `200`, body `ok` |
| Health after request | HTTP `200`, body `ok` |

The new successful deployment was created at `2026-10-15T18:03:43.692Z`
(`2026-10-16 01:03:43 ICT`), after the two blocked 401 checks recorded in PR #76.
No deployment or restart was initiated in this recheck.

## Credential validation

- Railway control-plane `OPENAI_API_KEY`: PRESENT.
- Production PID 1 `OPENAI_API_KEY`: PRESENT.
- PID 1 command: `python run_local.py --server.address 0.0.0.0 --server.port 8511`.
- Control-plane/runtime equality: **MATCH**.
- Comparison method: the control-plane value was passed over the authenticated Railway
  SSH session on stdin and compared in memory with `/proc/1/environ`; the command emitted
  only presence and equality booleans.
- The key, redacted key, hash, fingerprint, prefix, suffix, and response headers were not
  printed or stored.

## OpenAI metadata request

- Origin: active production container instance listed above.
- Request count: exactly `1`.
- Method and path: `GET /v1/models/gpt-6-luna`.
- HTTP status: `200`.
- Sanitized response validation: `object=model`, `id=gpt-6-luna`.
- Authentication: **PASS**.
- Model access: **PASS**.
- Completion requests: `0`.
- Provider input/output tokens: `0 / 0` for this preflight.

No retry, alternate model, completion endpoint, application adapter, Judge case, or send
path was used.

## Billing/quota

**NOT VERIFIED.** Production has no `OPENAI_ADMIN_KEY`. Official OpenAI documentation
states that organization cost, usage, spend-limit, and related administrative evidence
requires an Admin API key; the normal project inference key used for the model metadata
request does not establish those controls:

- <https://developers.openai.com/api/docs/guides/admin-apis>
- <https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs>

The HTTP 200 metadata response proves authentication and access to the named model only.
It does not prove completion quota, available credit, hard spend limit, or that a future
billable completion will succeed.

## Judge and no-mutation post-check

The production PID 1 state after the metadata request remained:

```text
LLM_MODE=replay
JUDGE_INPUT_ENABLED=0
JUDGE_LIVE_ENABLED=0
JUDGE_LIVE_MODEL=MISSING
JUDGE_ISSUER_SECRET=MISSING
JUDGE_GATEWAY_SOCKET=MISSING
```

- Judge LIVE: OFF.
- Grant: not created.
- Synthetic case: not created or submitted.
- Judge ledger / SQLite database: not read or modified in this run.
- Railway variables/configuration: not modified.
- Deployment: not initiated or modified.
- Email: no real or synthetic email sent.
- Provider completion calls: `0`.

## Validation and self-review

- PASS: exact project/environment/service selected explicitly for every Railway command.
- PASS: latest deployment is `SUCCESS`, one instance is `RUNNING`, and source message pins
  the required SHA.
- PASS: public health returned `200 ok` before and after the provider request.
- PASS: PID 1 key is present and exactly matches the control-plane value without exposing
  the credential or a fingerprint.
- PASS: the sole provider request was metadata-only and returned HTTP 200 for the exact
  approved model.
- PASS: post-check confirms Replay and both Judge switches remain disabled.
- PASS: `git diff --check` and an evidence secret-pattern scan are required before handoff.
- SELF-REVIEW: no Stop Condition occurred; no scope expansion, completion, retry, model
  substitution, deployment, configuration write, database write, grant, or send occurred.

## Risks and next step

- Residual gate: billing/quota is not verified and must not be inferred from metadata
  success.
- Metadata access does not guarantee that a structured completion will be accepted under
  the account's current quota or spend controls.
- Coordinator may prepare a decision packet for a separately authorized GO-LIVE limited
  to one synthetic email. That packet should either include independent billing/quota
  evidence or explicitly disposition the unresolved gate; this report does not waive it.
- STOP after this report. Do not enable LIVE, issue a grant, submit a case, or call a
  completion under this authentication-recheck authorization.

## Required output summary

- Production deployment ID: `2317dbc5-75bc-46d8-9080-9992dd373c4e`.
- Source SHA: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Health: PASS — HTTP `200`, body `ok` before and after.
- Runtime key match: PASS.
- HTTP status: `200`.
- Model access: PASS — `gpt-6-luna`.
- Billing/quota: NOT VERIFIED.
- Judge switches: OFF (`0 / 0`), Replay retained.
- Provider completion calls: `0`.
- Evidence PR: #76 (`codex/final-deploy-closeout`).
- Risks: billing/quota and future completion acceptance remain unverified.
- Next step: Coordinator decision packet for a separately authorized, one-email
  synthetic GO-LIVE; do not activate under this task.
