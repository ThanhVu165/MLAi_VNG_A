# FINAL Railway Deploy Closeout & Judge LIVE Preflight — 2026-10-16

## Task and authorization

- Task IDs: `FINAL-RAILWAY-DEPLOY` evidence closeout; `JUDGE-INPUT-LIVE` read-only preflight.
- Owner: Deployment / Judge LIVE Activation Owner — Codex, acting under the Coordinator request supplied on 2026-10-16.
- Repository: `ThanhVu165/MLAi_VNG_A`.
- Baseline and deployed source: `6600588d796233c6f3ca845ab5bb1b5d14548377` (`origin/dev`, merge commit of PR #74).
- Restrictions observed: no production mutation, deployment, grant, provider call or email dispatch in this closeout task.

## Deployment evidence closeout

| Evidence | Result |
|---|---|
| Railway target | `exodia-restricted-demo / production / exodia-web` — VERIFIED |
| Current deployment | `a570476e-969a-4503-ae42-fb333d08db8b` — `SUCCESS`, one running replica |
| Source provenance | Deployment message pins `6600588d796233c6f3ca845ab5bb1b5d14548377`; current runtime hashes for `Dockerfile`, Judge gateway/access/operator, LLM adapter and email page match the source tree at `origin/dev` |
| Public URL | `https://exodia-web-production.up.railway.app/` |
| Health | `/_stcore/health` returned HTTP 200 and `ok` on 2026-10-16 |
| Persistent database | `/runtime/app.db` on mounted `/runtime`; `PRAGMA integrity_check=ok`, schema `user_version=2`, current size 724992 bytes |
| Operator filesystem | Runtime UID 0; `/app/.judge-ipc` exists with mode `0700`; socket absent while gateway is disabled |
| Rollback | Previous source archive SHA `fe8c2dbca013e9344a678ba52f70588495c897ef` and verified pre-cutover SQLite backup remain outside Git; old/new schema compatibility was checked during deployment |

Read-only closeout commands included:

```text
git rev-parse origin/dev
npx @railway/cli status --json
Invoke-WebRequest https://exodia-web-production.up.railway.app/_stcore/health
npx @railway/cli variable list ... --json   # parsed locally; secret values never emitted
npx @railway/cli ssh ... python -c <read-only SQLite/file-hash probe>
gh pr view 74 --repo ThanhVu165/MLAi_VNG_A --json ...
```

The deployment smoke was not rerun merely to manufacture evidence. Preserved results from the authorized deployment run are:

- Build/health: PASS.
- Volume restore and restart persistence: PASS.
- Canonical synthetic email: PASS — `ESCALATE / AUTHORITY_REQUIRED`, rule `P01`, status `AWAITING_HUMAN`.
- Verify4 Replay: 4/4 PASS in 2.41 seconds.
- Audit: PASS — `VERIFY_RUN_STARTED` and `VERIFY_RUN_FINISHED`; 318 events after smoke.
- No-send: PASS — zero `SEND_DISPATCHED`, zero SMTP egress on ports 25/465/587 during the recorded smoke window.
- OpenAI LIVE/provider calls: 0.

## Judge LIVE configuration preflight

Secret values were not read into this report.

| Variable/control | Current status | Required for GO-LIVE |
|---|---|---|
| `APP_MODE` | VERIFIED `restricted_demo` | Keep unchanged |
| `LLM_MODE` | VERIFIED `replay` | Change to `live` only after GO-LIVE |
| `LLM_PROVIDER` | VERIFIED `openai` | Keep |
| `OPENAI_MODEL` | VERIFIED `gpt-6-luna` | Coordinator must approve exact model |
| `JUDGE_LIVE_MODEL` | MISSING | Set equal to approved `OPENAI_MODEL` |
| `JUDGE_INPUT_ENABLED` | VERIFIED `0` | Set `1` only after GO-LIVE |
| `JUDGE_LIVE_ENABLED` | VERIFIED `0` | Set `1` only after GO-LIVE |
| `LLM_CACHE` | VERIFIED `0` | Keep |
| `OPENAI_API_KEY` | PRESENT; value not exposed | Account/model access NOT VERIFIED without a provider call |
| `JUDGE_ISSUER_SECRET` | MISSING | Add a server secret of at least 32 characters; never pass via argv or browser |
| `JUDGE_GATEWAY_SOCKET` | MISSING | Set `/app/.judge-ipc/operator.sock` |
| `DATABASE_PATH` | VERIFIED `/runtime/app.db` | Keep |

The deployed adapter uses Chat Completions with strict JSON Schema `response_format`, `temperature=0` when reasoning effort is `none`, no SDK retries, and a 30-second attempt timeout. Official OpenAI documentation identifies `gpt-6-luna` as supporting Chat Completions and Structured Outputs, at Standard short-context rates of USD 0.10/M input tokens and USD 0.50/M output tokens:

- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://developers.openai.com/api/docs/pricing

This verifies documented API compatibility, not access by the configured key. Real key access, account quota, response behavior and organization-side budget enforcement remain NOT VERIFIED until a separately authorized provider call.

The current database contains no Judge grant, case, C2 reservation or LIVE-attempt ledger rows. This is consistent with LIVE never having been activated.

## Operator and grant procedure

Readiness: code and private directory are deployed, but the gateway is not operational until the missing socket/issuer variables are added and the authorized LIVE configuration is deployed.

After GO-LIVE only:

1. The authorized operator opens the production page on the designated browser/device and copies the displayed 16-hex session reference. The reference is not a capability.
2. The same named operator opens an interactive Railway SSH terminal to the active instance.
3. List server sessions with `python scripts/judge_operator.py --socket /app/.judge-ipc/operator.sock sessions`; enter the issuer secret only at the hidden TTY prompt.
4. Provision once with `python scripts/judge_operator.py --socket /app/.judge-ipc/operator.sock provision --reference <reference> --request-id <unique-16-to-128-char-id>`.
5. Run the single approved synthetic case in that browser session.
6. Revoke immediately with `python scripts/judge_operator.py --socket /app/.judge-ipc/operator.sock revoke --reference <reference>` and confirm the browser can no longer submit/read the Judge case.
7. Inspect `holds`; use `recover` only when a terminal snapshot can be reconciled. Never retry an ambiguous provider request.

Binding and quotas verified from deployed source and merged offline tests:

- Binding uses server Streamlit session ID plus a hash of the current WebSocket key; URL/query/session-state values do not grant access.
- Reconnect or changed connection fingerprint invalidates the binding and requires a new operator approval.
- Grant lifetime: 600 seconds; three requests per grant; ten per session; twenty globally; two concurrent globally and one per session.
- Provisioning IDs are single-use. Revocation is durable and does not refund quota.
- Per case: maximum three provider attempts, 2,000 output tokens per attempt, 24,000 total input tokens and 6,000 total output tokens reserved.
- Missing/invalid provider usage poisons the case closed; crash or ambiguous state remains `HOLD`.

## Proposed bounded LIVE smoke

Coordinator approval requested for exactly one case and at most three provider attempts.

Synthetic input:

```text
Sender: judge-new@example.invalid
Subject: Hỏi lệ phí phúc khảo học phần
Body: Cho em hỏi lệ phí phúc khảo của một học phần là bao nhiêu và em cần làm theo hướng dẫn nào? Đây là email thử nghiệm, không chứa dữ liệu cá nhân thật.
Channel: paste
```

Expected validation:

- One new Judge-owned case only.
- Expected route: `AUTO_REPLY`, rule `P05`, terminal status `PREVIEW_READY` with grounded active citations. A different safe business route is evidence to stop and review, not permission to rerun.
- `send_deadline` remains null; no `case_jobs`, `SEND_SCHEDULED` or `SEND_DISPATCHED` record.
- Audit contains intake, sanitation, evidence, policy, draft and terminal-resolution events without raw secret/grant data.
- Provider usage is present and within the attempt/token ledger; no pending or blocked attempt remains.
- Grant is revoked immediately after evidence capture.

Maximum application envelope for this one case is 24,000 input plus 6,000 output tokens. At the documented Standard `gpt-6-luna` rates, the calculated maximum is about USD 0.0054; the application reserves a more conservative USD 0.01 estimate per case. Recommended Coordinator cap: one case, three attempts, USD 0.01 application envelope. Before activation, use a dedicated OpenAI project/API key and configure the lowest practical organization-side project budget/alert; whether that external setting is a hard stop is NOT VERIFIED and must not replace the in-app ledger and kill switches.

## Safeguards and Stop Conditions

No-send safeguards:

- Judge terminal states are `PREVIEW_READY`, `AWAITING_HUMAN`, `ERROR` or `INVALID_INPUT`.
- Judge cases have no worker job and the recovery check rejects any `SEND_SCHEDULED`/`SEND_DISPATCHED` evidence.
- Public canonical samples and Verify4 remain routed to Replay even when Judge LIVE is configured.

Stop immediately, revoke the grant and set `JUDGE_LIVE_ENABLED=0` plus `JUDGE_INPUT_ENABLED=0` if any of these occur:

- Model mismatch, missing variable, health failure or SQLite integrity/mount failure.
- 401/403/404 access failure, 429 quota failure, timeout/5xx after the single built-in retry, refusal, incomplete or invalid structured output.
- Missing/invalid usage accounting, ledger `pending`, `blocked` or `HOLD`, token/attempt/budget limit reached, or any ambiguous provider outcome.
- Unexpected route/result, missing grounded citation, missing Audit event, cross-session visibility, any case job/send deadline, any `SEND_*` event or SMTP activity.
- More than one case, more than three attempts or projected cost above USD 0.01.

If disabling the two Judge switches does not restore a healthy Replay-only service, restore `LLM_MODE=replay` and use the verified previous deployment/source rollback plan. Do not retry the LIVE case during rollback diagnosis.

## Owner self-review

- Scope: only this report is changed; no source, schema, Railway variable or production data changed.
- Provenance: source SHA, deployment ID, runtime file hashes, health and SQLite were revalidated on 2026-10-16.
- Evidence labels: current read-only facts are VERIFIED; historical smoke is explicitly preserved rather than rerun; account/model access is NOT VERIFIED.
- Secret/data review: no secret value, grant, database or email containing real personal data is included.
- LIVE/API calls in this task: 0.
- Trello handoff: SKIPPED at the user's explicit request; Coordinator acceptance is still required.
- Commit / PR: pending creation on `codex/final-deploy-closeout`, targeting `dev`; no merge authorization implied.

## Remaining risks and decisions

- The configured key's access to `gpt-6-luna`, actual rate limit and strict structured-output behavior are NOT VERIFIED.
- Railway CLI-upload deployments do not expose a native Git SHA field; provenance is established by the exact deployment message plus matching runtime/source hashes.
- Operator identity/device is not yet named by the Coordinator.
- `JUDGE_ISSUER_SECRET`, `JUDGE_LIVE_MODEL` and `JUDGE_GATEWAY_SOCKET` are absent; LIVE cannot pass the runtime guard.
- Coordinator must approve the exact model, one-case/USD 0.01 limit (or another explicit bound), authorized operator/device and a separate `GO-LIVE` before any activation.
