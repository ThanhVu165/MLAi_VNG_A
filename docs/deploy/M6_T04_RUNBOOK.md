# M6-T04 — Deployment and reproducibility runbook

> **Latest private runtime checkpoint — 14/10/2026:** Railway deployment
> `c8930474-219b-4d9f-b736-2f0803888cb9` is SUCCESS; Docker build, startup and internal
> health passed. No public domain exists. Current OCI image digest is
> `sha256:1611638a236fc6299b321ae0bfca9f0c966a42557441d9c6df9385a2f773a585`.
> Source-config pin is b7a0658; deployment metadata says 61e31e8 (excluded report-only
> difference). Exact revision acceptance and container replay/data/image scans remain
> pending. The rejected image warning below is historical and still applies to that image.

> **BLOCKED CHECKPOINT:** Không dùng hoặc phân phối image
> `sha256:8e408bd7aa6462bb412a8211b12075c84abf795cc7d35462660c7d892b9e40b8`.
> Image này chứa artifact `.pytest-*`, gồm `.env` và `*.db`. Owner tiếp theo phải sửa
> `.dockerignore`, được cấp quyền cho một clean network build mới và lặp lại toàn bộ
> security/runtime checks. Các lệnh dưới đây chỉ là kế hoạch tiếp tục, không phải bằng
> chứng nghiệm thu image hiện tại.

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
$env:EXODIA_IMAGE = 'exodia:m6-t04-<source-sha>'
docker compose --project-name exodia-m6t02-validation-m6t04 --profile demo build --pull=false demo
docker image inspect $env:EXODIA_IMAGE --format 'ID={{.Id}} CREATED={{.Created}} SIZE={{.Size}} REPO_DIGESTS={{json .RepoDigests}}'
docker run --rm --network none --entrypoint python $env:EXODIA_IMAGE --version
```

If the source SHA changes, use a new tag and repeat all runtime checks. Do not reuse old
image evidence for a different source revision.

## Start and health

Use an isolated Compose project and non-conflicting loopback port:

```powershell
$env:EXODIA_IMAGE = 'exodia:m6-t04-<source-sha>'
$env:DEMO_HOST_PORT = '18513'
docker compose --project-name exodia-m6t02-validation-m6t04 --profile demo up -d --no-build demo
docker compose --project-name exodia-m6t02-validation-m6t04 --profile demo ps
Invoke-WebRequest http://127.0.0.1:18513/_stcore/health
docker compose --project-name exodia-m6t02-validation-m6t04 --profile demo logs demo
docker compose --project-name exodia-m6t02-validation-m6t04 exec -T demo python -c "import os; print({name: os.environ.get(name) for name in ('DATABASE_PATH','LLM_MODE','LLM_PROVIDER','OPENAI_MODEL','OPENAI_REASONING_EFFORT','LLM_CACHE','STREAMLIT_BROWSER_GATHER_USAGE_STATS')})"
```

Expected configuration is `/runtime/app.db`, replay/openai/gpt-6-luna/none/cache `0`.
Logs must include the two-worker startup marker and no provider, API, or email call.

## Replay and Verify

The image excludes `tests/`, so mount the accepted cassette pack read-only. Use a fresh
synthetic DB in `/tmp`, no network, a read-only container filesystem, and an evidence
directory created for this task:

```powershell
$repo = (Get-Location).Path
$image = 'exodia:m6-t04-<source-sha>'
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m --cap-drop ALL --security-opt no-new-privileges:true -e LLM_MODE=replay -e LLM_PROVIDER=openai -e OPENAI_MODEL=gpt-6-luna -e OPENAI_REASONING_EFFORT=none -e LLM_CACHE=0 -e DATABASE_PATH=/tmp/app.db --mount "type=bind,source=$repo\tests\cassettes,target=/app/tests/cassettes,readonly" --entrypoint python $image -m scripts.audit_runtime_replay --output-dir /tmp/m6-t04-replay
```

For persistent raw evidence, mount only a dedicated `data/validation/m6-t04` directory
at `/evidence` and write outputs there. Do not modify or re-record cassettes. Verify must
finish with 4/4 semantic matches, critical flows 4/4, zero replay misses, and zero LIVE
calls before AC5 can pass.

## Synthetic database, persistence, and recovery

Only use project `exodia-m6t02-validation-m6t04`. Seed through the application entrypoint,
write a synthetic probe, restart, and confirm it persists:

```powershell
docker compose --project-name exodia-m6t02-validation-m6t04 exec -T demo python -c 'from infra.db import execute; execute("CREATE TABLE IF NOT EXISTS m6_t04_probe (value TEXT NOT NULL)"); execute("INSERT INTO m6_t04_probe VALUES (''synthetic'')")'
docker compose --project-name exodia-m6t02-validation-m6t04 restart demo
docker compose --project-name exodia-m6t02-validation-m6t04 exec -T demo python -c 'from infra.db import fetch_one; assert fetch_one("SELECT value FROM m6_t04_probe")[0] == "synthetic"'
```

For a controlled recovery check, stop and start the same service and re-run health and
probe checks. Do not reset ordinary DEV/STUDY/DEMO projects. After verifying the exact
project labels, use the existing guarded reset only for
`exodia-m6t02-validation-m6t04`. Never use a wildcard, global prune, or an unverified
`down --volumes` command.

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
docker compose --project-name exodia-m6t02-validation-m6t04 stop demo
docker compose --project-name exodia-m6t02-validation-m6t04 --profile demo up -d --no-build demo
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

## Follow-up Railway readiness — 14/10/2026

Provider access is now connected. The observed project is `sweet-perfection`, service
`invigorating-fascination`, environment `production`. Configuration remains staged;
there is no new build, running service or public URL at this checkpoint.

The context fix excludes `.pytest-*/` and permits `tests/cassettes/` while excluding
other test directories. Verify the directory contains exactly the 24 canonical BASE24
files and every SHA-256 matches the manifest before any build. The old rejected image
remains unusable. Source checks do not replace an image filesystem scan.

Prepared settings use the root Dockerfile and its existing CMD/8511, replay identity
from BASE24, `PORT=8511`, health `/_stcore/health`, and a dedicated 500 MB DEMO volume at
`/runtime` with `DATABASE_PATH=/runtime/demo.db`. No API/email key is configured.

Before applying the Railway environment patch, inspect all staged changes. A deletion
of the old `MLAi_VNG_A` service was already staged when this session started; applying
the patch would also delete that service. The project admin must remove that pending
deletion or authorize it separately. Do not apply a destructive batch as a deploy shortcut.

Coordinator must approve project/access/safety, candidate SHA and build networking;
the user must verify available Free/Trial credit without activating paid billing.
After those gates, pin the published candidate commit, build privately and inspect logs
for Dockerfile usage. Scan the actual image, test startup and critical replay/Verify,
then create a domain targeting port 8511 only after the exposure decision. Verify HTTPS
health and Streamlit UI from outside the container before declaring PUBLIC_URL_READY.

Current results, three retained fixture-hash failures and AC1–AC8 are in
`reports/sprints/M6_T04_DEPLOYMENT_ACCEPTANCE.md`. Fresh clone and browser acceptance
remain the reviewer's separately authorized steps.

## Inspect the private Railway container

Current Service Instance ID is `f6d42f27-6b73-4336-a477-a4d413c1c779`. It identifies
the private SSH target; it is not the Service ID or Deployment ID. A corresponding
local private key must be available and its public key registered on Railway. Keep
private keys outside the repository and do not disable SSH host verification.

After SSH authentication/host identity are established, the first read-only probe is:

```powershell
ssh f6d42f27-6b73-4336-a477-a4d413c1c779@ssh.railway.com 'python --version'
```

Then verify actual environment identity, cassette bytes, `/app` artifact hygiene and
SQLite metadata before running critical replay/Verify on a temporary test DB. Do not
reset or use the live DEMO volume for destructive probes. See the latest report for
completed checks, the source-SHA discrepancy and remaining access gates.

The SSH path works without creating a public domain:
[Railway SSH documentation](https://docs.railway.com/cli/ssh).
