# M5-T03-HF1 — STUDY APP_MODE runtime pin

## Metadata

- Task ID: `M5-T03-HF1`
- Owner/Approver: Project Coordinator
- Baseline: `2ce699c6a0d5b3d4ac6252a394468fb2aab329cd`
- Final tested implementation SHA: `3b9983a57613d191d08f7082adadacb6d057cf9f`
- Docker-tested branch SHA: `d38eef59604dd9a55ef701728b13f0bb1dd8b8e9`
- Branch: `sprint/m5-t03-hf1-study-app-mode`
- Pull request: [#56](https://github.com/ThanhVu165/MLAi_VNG_A/pull/56)
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
| Docker build/start and health | PASS — image `sha256:76097d32161d6ab3083e0ff069081629e38e94c55869b7ea6a54d8d67d933376`; STUDY healthy; HTTP 200 `ok` |
| Container environment and loopback binding | PASS — exact four required values; `127.0.0.1:28512` → `8511` in the disposable validation project |
| Restart and persistence | PASS — STUDY returned healthy and retained the synthetic probe after restart |
| STUDY/DEMO DB isolation | PASS — distinct labeled volumes; DEMO never contained the STUDY probe |
| Restricted DEMO control | PASS — explicit restricted mode and direct privileged action denied |
| PRESTUDY-D01 container before/after | PASS — omitted mode reproduced restricted `ERROR/TECHNICAL_ERROR`; canonical STUDY reached `AWAITING_HUMAN/R1` |
| `git diff --check` | PASS |

The first broad targeted pytest invocation produced `31 passed, 17 errors` because
Windows denied access to the shared default `pytest-of-admin` directory. The unchanged
test selection passed completely when rerun with a fresh task-specific `--basetemp`;
no test or expected result was modified to hide the environment error.

## Docker validation

`PASS` on Docker Desktop Server `29.1.3`, Linux/WSL2 with `overlayfs` and Compose
`v2.40.3-desktop.1`.

Validation used only the fresh disposable Compose project
`exodia-m6t02-validation-m5t03hf1-20261015a`. It had no pre-existing container or
volume. The approved host-port override `28512` avoided unrelated environments while
retaining the canonical STUDY container port, service definition and `study_data`
mount.

- Exact HF1 source built image
  `sha256:76097d32161d6ab3083e0ff069081629e38e94c55869b7ea6a54d8d67d933376`.
- STUDY became healthy, returned HTTP `200`/`ok`, bound only to loopback and exposed
  `APP_MODE=private`, `DATABASE_PATH=/runtime/app.db`, `LLM_MODE=replay`,
  `LLM_CACHE=0` inside the running container.
- A synthetic row written only to STUDY remained after restart; the separate labeled
  DEMO volume never contained its probe table.
- DEMO became healthy with `APP_MODE=restricted_demo`; a direct privileged action
  raised `DemoAccessDenied`.
- The exact replay/human-resume audit ran in the STUDY container: 24 calls, 24 hits,
  0 misses/errors, R11 job `done`, final status `PENDING_APPROVAL`, one draft and
  LIVE/API `0`.
- The minimal image intentionally has no `git` executable, while the audit helper reads
  Git only to stamp metadata. The Docker audit therefore injected the already verified
  host HEAD for that metadata call; all pipeline, cassette, network guards and evidence
  generation remained unchanged. The direct helper failure is retained as evidence and
  is not presented as a product PASS.
- A precise STUDY log scan found no provider attempt, live-mode, OpenAI endpoint,
  traceback or `DemoAccessDenied` marker.

The original defect was also reproduced as a negative control in the same image. With
`APP_MODE` deliberately removed, the effective mode was `restricted_demo` and the
synthetic B2 intake returned `ERROR / TECHNICAL_ERROR` with `DemoAccessDenied`. Under
the canonical resolved STUDY environment, the same input resolved `private` and reached
`AWAITING_HUMAN / R1`.

## Defect disposition and residual risks

- `PRESTUDY-D01`: `FIXED` in resolved configuration, host replay and canonical Docker
  before/after validation.
- `PRESTUDY-D02`: `RESOLVED`; canonical Docker validation completed.
- The recorded replay pack still has unapproved provenance, so its audit intentionally
  exits `2` despite complete offline replay coverage.
- The audit helper's standalone image invocation depends on a Git executable that the
  minimal runtime image does not contain; validation required a metadata-only SHA shim.

Task disposition: `READY_FOR_COORDINATOR_REVIEW`. This report does not issue
GO-STUDY, start a participant session, authorize LIVE/API, merge the PR or mark the
task DONE.
