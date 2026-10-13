# M6-T04 — Deployment and reproducibility runbook

## Safety boundary

- This runbook is for a local, synthetic DEMO environment only.
- The application binds to `127.0.0.1`; do not expose port 8513 publicly.
- Replay mode is mandatory: `LLM_MODE=replay`, `LLM_CACHE=0`, provider `openai`, model
  `gpt-6-luna`, reasoning effort `none`.
- Do not add an API key, real student data, or email credentials.
- Public hosting and an independent fresh clone require separate Coordinator approval.

## Pinned inputs

- Authorized source baseline: `eaaeea88a59618b49219a20ae01a3cf3227cec87`.
- Python: `3.11` (`python:3.11-slim`; observed container version must be recorded).
- Dependencies: exact versions in `requirements.txt`; CPU Torch is pinned in `Dockerfile`.
- Replay pack: `reports/readiness/M6_T05_BASE24_RECORDED_PACK.json` and the read-only
  `tests/cassettes/` directory.

Before a build, verify the branch, source SHA, clean state, Docker engine, and Compose:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short --branch
docker version
docker compose version
docker compose --profile demo config --quiet
```

## Build authorization gate

The dependency layer may require downloads from the Python and PyTorch package indexes.
Do not grant build networking from an earlier task authorization. After the Coordinator
explicitly approves these dependency downloads, build and identify the image:

```powershell
$env:EXODIA_IMAGE = 'exodia:m6-t04-eaaeea8'
docker compose --project-name exodia-m6t04-validation --profile demo build --pull=false demo
docker image inspect $env:EXODIA_IMAGE --format 'ID={{.Id}} CREATED={{.Created}} SIZE={{.Size}} REPO_DIGESTS={{json .RepoDigests}}'
docker run --rm --network none --entrypoint python $env:EXODIA_IMAGE --version
```

If the source SHA changes, use a new tag and repeat all runtime checks. Do not reuse old
image evidence for a different source revision.

## Start and health

Use an isolated Compose project and non-conflicting loopback port:

```powershell
$env:EXODIA_IMAGE = 'exodia:m6-t04-eaaeea8'
$env:DEMO_HOST_PORT = '18513'
docker compose --project-name exodia-m6t04-validation --profile demo up -d --no-build demo
docker compose --project-name exodia-m6t04-validation --profile demo ps
Invoke-WebRequest http://127.0.0.1:18513/_stcore/health
docker compose --project-name exodia-m6t04-validation --profile demo logs demo
docker compose --project-name exodia-m6t04-validation exec -T demo python -c "import os; print({name: os.environ.get(name) for name in ('DATABASE_PATH','LLM_MODE','LLM_PROVIDER','OPENAI_MODEL','OPENAI_REASONING_EFFORT','LLM_CACHE')})"
```

Expected configuration is `/runtime/app.db`, replay/openai/gpt-6-luna/none/cache `0`.
Logs must include the two-worker startup marker and no provider, API, or email call.

## Replay and Verify

The image excludes `tests/`, so mount the accepted cassette pack read-only. Use a fresh
synthetic DB in `/tmp`, no network, a read-only container filesystem, and an evidence
directory created for this task:

```powershell
$repo = (Get-Location).Path
$image = 'exodia:m6-t04-eaaeea8'
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m --cap-drop ALL --security-opt no-new-privileges:true -e LLM_MODE=replay -e LLM_PROVIDER=openai -e OPENAI_MODEL=gpt-6-luna -e OPENAI_REASONING_EFFORT=none -e LLM_CACHE=0 -e DATABASE_PATH=/tmp/app.db --mount "type=bind,source=$repo\tests\cassettes,target=/app/tests/cassettes,readonly" --entrypoint python $image -m scripts.audit_runtime_replay --output-dir /tmp/m6-t04-replay
```

For persistent raw evidence, mount only a dedicated `data/validation/m6-t04` directory
at `/evidence` and write outputs there. Do not modify or re-record cassettes. Verify must
finish with 4/4 semantic matches, critical flows 4/4, zero replay misses, and zero LIVE
calls before AC5 can pass.

## Synthetic database, persistence, and recovery

Only use project `exodia-m6t04-validation`. Seed through the application entrypoint,
write a synthetic probe, restart, and confirm it persists:

```powershell
docker compose --project-name exodia-m6t04-validation exec -T demo python -c 'from infra.db import execute; execute("CREATE TABLE IF NOT EXISTS m6_t04_probe (value TEXT NOT NULL)"); execute("INSERT INTO m6_t04_probe VALUES (''synthetic'')")'
docker compose --project-name exodia-m6t04-validation restart demo
docker compose --project-name exodia-m6t04-validation exec -T demo python -c 'from infra.db import fetch_one; assert fetch_one("SELECT value FROM m6_t04_probe")[0] == "synthetic"'
```

For a controlled recovery check, stop and start the same service and re-run health and
probe checks. Do not reset ordinary DEV/STUDY/DEMO projects. The existing reset guard
only accepts M6-T02 validation project names; therefore M6-T04 cleanup must retain the
volume until a Coordinator-approved reset procedure is added or the project is reviewed
manually. Never use a wildcard, global prune, or an unverified `down --volumes` command.

## Concurrent sessions

Open the loopback URL in two or three genuinely independent browser contexts. In each,
select a different synthetic email/case, navigate between pages, and record the visible
case ID, decision, state, and audit history. Confirm that UI selections do not leak while
the shared database retains correct case associations and creates no duplicate action.
Multiple health requests are not session-isolation evidence.

If independent browser contexts are unavailable, record AC6 as `NOT VERIFIED`.

## Stop, restart, and rollback

Stop while retaining the database:

```powershell
docker compose --project-name exodia-m6t04-validation stop demo
docker compose --project-name exodia-m6t04-validation --profile demo up -d --no-build demo
```

Rollback uses the previous inspected image ID/tag with the same volume. Stop the service,
set `EXODIA_IMAGE` to that known-good tag, start with `--no-build`, then repeat health,
configuration, persistence, and replay checks. Never roll back the SQLite file in place;
follow `docs/RUNBOOK.md` and restore a backup to a new path first.

## Hosting decision packet

All options require authentication/access control in front of this app, loopback/private
container exposure, persistent single-writer storage for SQLite, health monitoring, logs,
backup/restore, and an image rollback mechanism.

| Option | Fit | Main risk | Decision still required |
| --- | --- | --- | --- |
| Single managed VM with Docker Compose | Closest to the validated architecture and simplest persistent disk model | OS patching, TLS, access proxy, backups, and uptime remain team responsibilities | Provider, region, VM/disk size, budget, VPN or identity-aware proxy |
| Managed container service with persistent volume | Managed rollout and health can be convenient | Many services use ephemeral filesystems or do not support a single attached SQLite volume as expected | Provider-specific volume semantics, scale fixed to one writer, private ingress, budget |
| Private institutional host/VPN | Strongest containment for an unauthenticated prototype | Availability and reviewer access depend on institutional operations | Host owner, VPN accounts, TLS, monitoring, backup and support window |

Current prices, quotas, credentials, region, data-retention policy, and exposure controls
must be verified by the Coordinator before choosing an option. No account or public URL is
created by this runbook.
