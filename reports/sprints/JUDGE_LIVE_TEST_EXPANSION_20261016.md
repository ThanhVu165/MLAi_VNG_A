# JUDGE-LIVE-TEST-EXPANSION — USD 5 guard implementation — 2026-10-16

## Result

**RESULT: BLOCKED**

The Coordinator-approved USD 5 multi-case/multi-grant budget guard is implemented and its
dedicated safety regression passes locally. Production was intentionally not deployed or
activated in this handoff, so `LIVE_TEST_READY` is not claimed. Railway remains Replay/OFF
with no new grant, case, provider call, or email dispatch.

Activation remains blocked pending review/merge/deploy authorization and a verified
production database backup or an approved recoverable Railway volume-backup procedure.

## Authority and scope

- Task: `JUDGE-LIVE-TEST-EXPANSION`.
- Role/owner: Deployment / LIVE Activation Owner — Codex; Ponytail — Deployment Owner.
- Coordinator authorization: implement the code/contract change required to raise the
  cumulative LIVE TEST guard to USD 5, validate accounting, fail-closed behavior, session
  isolation and regressions; do not merge, deploy or enable LIVE in this implementation
  handoff.
- Production reference SHA: `6600588d796233c6f3ca845ab5bb1b5d14548377`.
- Branch baseline: `origin/dev` at `a572d4d62087f38691d9b7ff1f4585c3ed8e5a2a`.
- PR #76 is merged into that baseline and records the successful one-email LIVE smoke.
- Scope changed: `infra/judge_access.py`, `tests/test_judge_input_c2a.py`,
  `PROJECT_SPEC.md`, and this evidence report.
- Explicitly unchanged: provider/model adapter, gateway, policy/routing, SQLite schema,
  migrations, audit-action catalog, UI, dispatch/no-send path and production configuration.

## Preflight evidence

| Check | Result |
|---|---|
| Git baseline | `origin/dev` contains the production source SHA and merged PR #76 |
| Railway target | `exodia-restricted-demo / production / exodia-web` |
| Current deployment | `38e8efce-8824-4f16-8074-7d07f8f86a56` — `SUCCESS` |
| Current instance | `f7977cf6-01e8-44cd-bf14-5b8135a3b989` — `RUNNING` |
| Deployed source | Deployment message pins `6600588d796233c6f3ca845ab5bb1b5d14548377` |
| Public health | HTTP `200`, body `ok` |
| Volume | `/runtime` — `READY` |
| Database | `/runtime/app.db`; integrity `ok`; schema `user_version=2` |
| Current state | 43 cases, zero jobs, zero `SEND_DISPATCHED` |
| Judge ledger | One finished smoke case; one revoked grant; no active case/HOLD/pending attempt |
| Runtime backup | `/runtime/backups` absent; no application DB backup file observed |

Production PID 1 remains locked:

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

## Budget implementation

The prior runtime had cumulative hard limits of 20 cases, 600,000 reserved tokens and
200,000 micro-USD (USD 0.20). Both the deployed reference and current `origin/dev` had the
same limits, so production could not expose the approved USD 5 expansion honestly.

The candidate keeps the existing per-case and per-session safety boundaries and derives
the global token/cost ceilings from a single 500-case limit:

| Boundary | Candidate limit |
|---|---|
| Per provider attempt | 2,000 output tokens |
| Per case | 3 provider attempts; 24,000 input + 6,000 output tokens; USD 0.01 debit |
| Per grant | 3 cases / 600 seconds; maximum reserved debit USD 0.03 |
| Per session | 10 cases; 300,000 tokens; USD 0.10 |
| Concurrent | 2 global; 1 per session |
| Global | 500 cases; 15,000,000 reserved tokens; 5,000,000 micro-USD = USD 5.00 |

Reservations remain atomic in `BEGIN IMMEDIATE`, durable across grants/sessions/restarts,
and never refund `FINISHED`, `HOLD` or `RECOVERED` records. Existing production smoke
debit is USD 0.01, so after an approved deployment the application ledger would have
USD 4.99 remaining in the USD 5 envelope.

The official OpenAI model page observed on 2026-10-16 lists Standard short-context prices
for `gpt-6-luna` as USD 0.10/M input and USD 0.50/M output:
<https://developers.openai.com/api/docs/models/gpt-6-luna>. The code does not request a
non-default service tier, and the per-case token maxima are below the long-context
threshold. The resulting token-price maximum is USD 0.0054/case, below the conservative
USD 0.01 application debit. Provider invoice and refreshed project limit dashboard remain
NOT VERIFIED; pricing/tier must be rechecked before activation if configuration changes.

## Behavioral proof

The new boundary regression builds a consistent ledger with 498 completed cases across
distinct grants/sessions, admits exactly two concurrent reservations (the contract's
global concurrency limit), reaches exactly 500 cases / USD 5 / 15,000,000 tokens, then
proves request 501 is denied and both C1/C2 ledgers remain byte-equivalent at the parsed
state level. This exercises the real transactional reservation path rather than only
asserting `500 × USD 0.01` constants.

Existing dedicated tests additionally prove:

- concurrent reservations across grants cannot cross cost or token limits;
- a new grant cannot reset a session budget;
- process crash/restart never refunds or replays reservations;
- missing/corrupt usage and ledger corruption fail closed;
- reservation/store failure rolls back or preserves debit for recovery;
- guest, forged, cross-session, expired and revoked grants are denied;
- browser sessions remain isolated and operator provisioning is single-use;
- kill switches/model mismatch stop before the next provider call;
- successful LIVE preview and escalation paths create no job or send event.

## Validation

| Validation | Result |
|---|---|
| New cap/boundary/concurrency tests | PASS — `4 passed in 3.24s` |
| Required accounting/restart/isolation/fail-closed/no-send selection | PASS — `33 passed in 45.88s` |
| Full C2-A/C2-B/LIVE targeted suite | PARTIAL — `87 passed, 3 failed in 144.53s` |
| Black, touched Python files | PASS |
| Ruff, touched Python files | PASS |
| `git diff --check` | PASS |
| Mypy, `infra/judge_access.py` | BASELINE FAIL — 24 pre-existing type errors outside changed lines |

The three targeted-suite failures are classified **ENVIRONMENT / BASELINE**, not patch
regressions. The untouched `tests/test_judge_input_c2b.py` expects POSIX behavior:

1. Windows `asyncio` needs an internal localhost socket pair, but the offline fixture
   blocks all network sockets.
2. Windows has no `os.getuid()`.
3. Windows has no `/private/tmp`.

The initial pytest run also hit an unreadable system temp directory
(`C:\Users\admin\AppData\Local\Temp\pytest-of-admin`). Subsequent commands used a fresh
workspace `--basetemp`; no fixture was modified to force PASS. Therefore no full-suite PASS
is claimed. The mypy errors reproduce in unchanged code regions; the patch changes only
numeric limits and derived expressions in that module.

## Self-review

- PASS: the three caps cannot drift independently: token and micro-USD globals derive
  from `GLOBAL_REQUEST_LIMIT` and unchanged per-case reservations.
- PASS: boundary behavior was tested through concurrent transactional reservations and a
  rejected request 501 with unchanged ledgers.
- PASS: per-grant, per-session, concurrency, attempt, usage, crash/HOLD, revoke and kill
  semantics are unchanged.
- PASS: no SQLite schema/migration, audit action, provider, model, route, UI or dispatch
  source was changed.
- PASS: production remained Replay/OFF throughout; no grant, case, provider request,
  configuration write, deployment or email send was performed.
- PASS: no credential, grant token, hash/fingerprint, provider request ID or payment data
  is included in this report.
- BLOCKED: application-level DB backup evidence is absent and this candidate is not yet
  reviewed, merged or deployed.

## Handoff and next step

1. Independent reviewer checks the money/security diff and the 500-case boundary test.
2. Coordinator reviews and authorizes merge; Codex must not merge it.
3. Before deployment, create/verify a recoverable production DB or Railway volume backup,
   record rollback deployment `38e8efce-8824-4f16-8074-7d07f8f86a56`, and recheck current
   model pricing/project limits.
4. Deploy the reviewed SHA while Judge remains Replay/OFF; verify health, PID 1, SQLite and
   migration-free compatibility with the existing USD 0.01 smoke debit.
5. Only under a separate activation instruction, enable LIVE and issue a distinct grant
   per tester/session. Do not reuse the revoked smoke grant.

## Required output snapshot

- Result: `BLOCKED`.
- Production deployment: `38e8efce-8824-4f16-8074-7d07f8f86a56` (unchanged).
- Source SHA: `6600588d796233c6f3ca845ab5bb1b5d14548377` (production); implementation
  commit `ed2a82599ccde4e59c74c41f88b860d3b330966b`.
- LIVE switches: Replay / input OFF / LIVE OFF.
- Model: `gpt-6-luna`.
- Total / remaining application budget after reviewed deployment: USD 5.00 / USD 4.99.
- Per-case limit: USD 0.01; 24,000 input + 6,000 output; 3 attempts.
- Authorized testers/grants: none issued in this handoff.
- Runtime health/database: `200 ok`; SQLite integrity `ok`, schema v2.
- Audit/no-send: zero new activity; global `SEND_DISPATCHED=0`.
- Risks: backup absent; project limits/provider invoice NOT VERIFIED; three POSIX-only tests
  fail on this Windows environment; mypy baseline debt remains.
- Website test instructions: not released while BLOCKED; website remains Replay/OFF.
- Next step: independent review and Coordinator merge/deploy authorization after backup.
