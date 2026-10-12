# M6-T02 — Docker Foundation & Environment Isolation

## Task and baseline

- Owner: Nam — QA/Infrastructure
- Final reviewer: Vũ — Runtime/Persistence
- Repository: `ThanhVu165/MLAi_VNG_A`
- Baseline: `ffb7f79f827172537d731528394173f4ce4f8551` (`origin/dev`)
- Validation source: task branch working tree based on `e4fdef84be461092fad51296af4748ab81844924`, including the final Compose loopback-publishing correction.
- Task branch: `sprint/m6-t02-docker-foundation`
- LIVE/API calls: `0`

## Preflight

`STARTABLE` at implementation start.

- Trello card M6-T02 was in `IN PROGRESS`; it names Nam as Owner and Vũ as final reviewer.
- Local `dev`, `origin/dev`, and the checked baseline all resolved to `ffb7f79f827172537d731528394173f4ce4f8551` before creating the task branch.
- Docker Desktop Engine was available as Docker `29.8.2`.
- No existing `Dockerfile`, `.dockerignore`, `compose.yaml`, task branch, or M6-T02 PR was found.
- M3-T03 and M6-T01 evidence were read. Both are static audits and explicitly leave runtime Docker/isolation evidence unverified; this task does not inherit a runtime PASS.
- M6-T05 remains owned by Minh. No cassette or replay manifest is changed here.

## Files changed

- `Dockerfile`
- `.dockerignore`
- `compose.yaml`
- `docs/deploy/M6_T02_RUNBOOK.md`
- `reports/sprints/M6_T02_DOCKER_FOUNDATION.md`

## Design

- The image uses Python 3.11 and starts the established `run_local.py` entrypoint so seed initialization and background-worker startup are preserved.
- The repository leaves `torch` unpinned; the Docker image installs the pinned CPU wheel (`2.5.1+cpu`) before the existing requirements so a non-GPU container does not download CUDA runtime packages.
- DEV is the default Compose service; opt-in STUDY and DEMO profiles use separate named volumes and loopback-only host ports.
- The runtime database is always `/runtime/app.db`; `LLM_MODE=replay` and cache disabled keep M6-T02 smoke validation off the live-provider path. No API key is added to the image or Compose configuration.
- Destructive reset is limited to uniquely named disposable validation projects. Normal profile volumes are retained.

## Acceptance and validation

Validation used Docker Desktop `29.8.2`, image `sha256:ad4144ddbc644102357e4d2f7f688e31999e0e2e7735025ea09812c6e51af8b3` (2.60 GB), and the disposable Compose project `exodia-m6t02-validation`.

| Check | Result | Evidence |
| --- | --- | --- |
| AC1 — image build / Python 3.11 | PASS | `docker compose build` completed in 5m57s; `docker run --rm exodia:m6-t02 python --version` returned `Python 3.11.17`. |
| AC2 — startup / health / worker | PASS | DEV/STUDY/DEMO were `healthy`; host health endpoints `127.0.0.1:8511`, `:8512`, and `:8513` each returned `ok`. PID 1 command was `python run_local.py --server.address 0.0.0.0 --server.port 8511`, preserving the entrypoint that calls `start_worker()` before Streamlit. |
| AC3 — isolation | PASS | A synthetic `m6_t02_probe` row was inserted only in DEV. SQLite metadata checks in STUDY and DEMO confirmed the probe table did not exist. |
| AC4 — persistence | PASS | The DEV container was restarted; the synthetic row was still readable from its named volume. |
| AC5 — seed/reset safety | PASS | Startup created the expected application schema tables. Only the disposable `exodia-m6t02-validation_{dev,study,demo}_data` volumes were removed with `down --volumes`; a follow-up volume list was empty. |
| AC6 — safety | PASS | Bindings are loopback-only, Compose forces replay mode and adds no API key, logs contained only local Streamlit startup, and image/config inspection found no credential literal. LIVE/API calls: `0`. |
| AC7 — reproducibility | PASS | `docker compose config`, `docker compose --profile study config`, and `docker compose --profile demo config` passed before the successful disposable-project run. The runbook records the same commands and safe reset boundary. |

## Known limits and dependencies

- M6-T02 does not certify business E2E, fresh-clone acceptance, public deployment, replay coverage, or any milestone gate.
- A replay cassette miss belongs to M6-T05 and is not corrected in this branch.
- Coordinator acceptance and Vũ's final review are still required before the task can be marked DONE.

## Commit and PR

The implementation commit will be amended with this evidence, then pushed as `sprint/m6-t02-docker-foundation`; the PR target is `dev`.
