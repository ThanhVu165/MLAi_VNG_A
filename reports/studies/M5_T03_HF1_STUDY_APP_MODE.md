# M5-T03-HF1 — STUDY APP_MODE runtime pin

## Metadata

- Task ID: `M5-T03-HF1`
- Owner/Approver: Project Coordinator
- Baseline: `2ce699c6a0d5b3d4ac6252a394468fb2aab329cd`
- Final tested implementation SHA: `PENDING_COMMIT`
- Branch: `sprint/m5-t03-hf1-study-app-mode`
- Pull request: `PENDING_PR`
- LIVE/API calls: `0`

## Problem and reproduction

`compose.yaml` previously resolved STUDY with `DATABASE_PATH=/runtime/app.db`,
`LLM_MODE=replay` and `LLM_CACHE=0`, but without `APP_MODE`. The application safely
defaults a missing mode to `restricted_demo`, so the legitimate private B2 flow was
denied.

Before the fix, `docker compose --profile study config --format json` returned no
`APP_MODE` for STUDY. Running the offline replay audit without `APP_MODE` reproduced
the original failure in `DEV_HUMAN_R11`: the intake was denied and the audit stopped
at the assertion requiring `AWAITING_HUMAN` (exit `1`).

## Root cause and change

Compose inherited one shared environment mapping that did not identify the intended
runtime privilege boundary. Because YAML mapping inheritance is not a deep merge,
adding only `APP_MODE` under STUDY would also discard the shared DB/replay/cache keys.

The hotfix introduces one reusable environment anchor, then resolves service-specific
environments explicitly:

- STUDY adds `APP_MODE=private` while retaining every shared runtime key.
- DEMO explicitly pins `APP_MODE=restricted_demo`.
- DEV remains without an explicit `APP_MODE` and therefore retains the documented
  fail-closed application default `restricted_demo`.

Changed files:

- `compose.yaml`
- `tests/test_compose_runtime_config.py`
- `reports/studies/M5_T03_HF1_STUDY_APP_MODE.md`

No routing, policy, persistence schema, Gold, Set A/B, cassette or study protocol was
changed.

## Before and after

| Runtime | Before | After |
| --- | --- | --- |
| STUDY | missing `APP_MODE`; effective default `restricted_demo` | explicit `private` |
| DEMO | missing `APP_MODE`; effective default `restricted_demo` | explicit `restricted_demo` |
| DEV | missing `APP_MODE`; effective default `restricted_demo` | unchanged |

Resolved STUDY environment after the fix:

```text
APP_MODE=private
DATABASE_PATH=/runtime/app.db
LLM_MODE=replay
LLM_CACHE=0
```

Resolved boundaries also retain loopback port `127.0.0.1:8512` and named volume
`study_data`; DEMO retains loopback port `127.0.0.1:8513`, `demo_data`, replay mode
and explicit restricted mode.

## Validation

| Command/check | Result |
| --- | --- |
| Preflight fetch/status/branch/HEAD/origin-dev | PASS — clean; exact required baseline |
| `docker compose --profile study --profile demo config --format json` | PASS — exact STUDY/DEMO modes and shared keys resolved |
| New Compose regression plus restricted access, offline isolation and human-control tests | PASS — `48 passed in 22.07s` with isolated `--basetemp` |
| Focused mode/replay/privilege tests | PASS — `6 passed in 1.36s` |
| `black --check` on new test | PASS |
| `ruff check` on new test and relevant access modules | PASS |
| Private replay audit using resolved STUDY values | PASS — 24 calls, 0 misses/errors, human R11 completed, LIVE=0; exit `2` only because pack provenance is not approved |
| `git diff --check` | PASS |

The first broad targeted pytest invocation produced `31 passed, 17 errors` because
Windows denied access to the shared default `pytest-of-admin` directory. The unchanged
test selection passed completely when rerun with a fresh task-specific `--basetemp`;
no test or expected result was modified to hide the environment error.

## Docker validation

`BLOCKED_ENVIRONMENT — Docker daemon unavailable`.

Docker CLI `29.1.3` and static Compose resolution were available. The Docker Desktop
Linux engine pipe was absent, so image build/start, health, restart, persistence and
container-level volume isolation were not run and are not claimed PASS.

## Defect disposition and residual risks

- `PRESTUDY-D01`: `FIXED` in static resolved configuration and safe host replay.
- `PRESTUDY-D02`: `BLOCKED_ENVIRONMENT`; canonical Docker runtime evidence remains.
- The recorded replay pack still has unapproved provenance, so its audit intentionally
  exits `2` despite complete offline replay coverage.
- Exact Docker startup/health/restart/persistence and private B2 smoke must be rerun
  after Docker Desktop is available.

Task disposition: `READY_FOR_RUNTIME_REVALIDATION`. This report does not issue
GO-STUDY, start a participant session, authorize LIVE/API, merge the PR or mark the
task DONE.
