# M6-T04 — Deployment & Reproducibility Acceptance

## Checkpoint result

- **RESULT: BLOCKED / PARTIAL ONLY**
- Task: `M6-T04`
- Execution Owner: Project Coordinator (authorized on the official Trello card)
- Reviewer: Vũ per Task Contract
- Authorized baseline / tested SHA: `eaaeea88a59618b49219a20ae01a3cf3227cec87`
- Branch: `sprint/m6-t04-deployment-acceptance`
- Final SHA / PR: pending this partial checkpoint
- Public hosting, LIVE LLM, external API and email: **not authorized; actual calls 0/0/0**
- Fresh clone: not authorized for this implementer; reviewer authorization remains separate

This checkpoint does not claim task DONE, M6 PASS, a live deployment, or a reproducible
exact image. Offline execution stopped when the exact-image build proved that external
package downloads were required and no M6-T04 network authorization existed.

## Preflight

Preflight was `STARTABLE` for offline Phases A–C before the build stop condition:

- Official Trello card is in `IN PROGRESS` and contains a Coordinator authorization for
  offline Phases A–C. Hosting, public exposure, LIVE/API/email and fresh clone are withheld.
- Live GitHub `dev` was verified identical to `eaaeea88a59618b49219a20ae01a3cf3227cec87`.
- M6-T02, M6-T03 and M6-T05 cards are in `Done - Đã nghiệm thu`.
- No existing M6-T04 branch or PR was found. The starting working tree was clean.
- Host Python is `3.11.9`.
- Docker Desktop/Engine is `29.1.3`, Compose `v2.40.3-desktop.1`, Linux `x86_64`,
  `overlayfs`, 8 CPUs and 8,218,968,064 bytes memory.
- Existing accepted reference image `exodia:m6-t03-7801eab` has ID
  `sha256:34fb7d38e8464ff54a72756f29cf1864770fdb2c9eebfa208dd94182b0369940`.
  It is reference evidence only, not claimed as the M6-T04 exact-image build.

## Completed safe work

- Compose still uses the M6-T02 architecture and loopback bindings.
- Compose now makes provider/model identity explicit and accepts an exact image tag through
  `EXODIA_IMAGE`; defaults remain backward compatible.
- `docker compose config --quiet` and `docker compose --profile demo config --quiet`
  passed after the replay identity correction.
- A clean-run runbook now records the authorization gate, exact image identity, local
  start/health, replay mounts, synthetic persistence, concurrency, recovery, rollback,
  safety boundary and hosting decision packet.
- No production logic, policy, Gold, cassette, schema or dependency was changed.

## Build stop condition

| Field | Evidence |
| --- | --- |
| Command | `docker build --pull=false --network=none -t exodia:m6-t04-eaaeea8 .` |
| Result | FAIL, exit 1; no M6-T04 image was created |
| Failure | Uncached dependency layer attempted to resolve `torch==2.5.1+cpu` from the pinned PyTorch index; DNS/network was denied by `--network=none` |
| External downloads | 0 completed; no network-enabled retry was made |
| Impact | Exact-source image ID, startup, health, DB runtime, replay/Verify and browser concurrency cannot be accepted on this checkpoint |

**PROBLEM:** exact image build requires external package downloads.

**IMPACT:** Phase A cannot complete and Phases B/C cannot produce evidence on the intended
image.

**EVIDENCE:** failed offline BuildKit step 4/5 for pinned CPU Torch; image inspect returned
`No such image`.

**SOLUTION:** Coordinator authorizes one scoped Docker build with network access to the
PyTorch/Python package indexes, retaining pinned dependencies and recording the resulting
image ID; then resume the runbook from build through Phases A–C.

**RESPONSIBLE:** Project Coordinator for authorization; implementer for rerun/evidence.

**COORDINATOR DECISION NEEDED:** approve or deny the scoped dependency download.

## BASE24 and source/image provenance

- Canonical manifest: `reports/readiness/M6_T05_BASE24_RECORDED_PACK.json`.
- Manifest SHA-256 recorded by accepted M6-T03 evidence:
  `2a3c80855923010e3ead807424bc1d2e904c01422ab08eade7655fe30aa280c8`.
- Accepted pack integrity: 24/24 hashes, zero mismatch; scope
  `BASE_PACK_V1_PLUS_DELTA_REPAIR_V1`.
- Accepted M6-T03 runtime evidence: critical flows 4/4, Verify V01–V04 4/4,
  23/23 replay hits, zero misses, zero LIVE calls on image
  `sha256:34fb7d38e8464ff54a72756f29cf1864770fdb2c9eebfa208dd94182b0369940`.
- These are dependency/reference results. They were not relabeled as M6-T04 execution.

## Hosting decision packet

No provider, budget, credential, region, access policy or public exposure is approved.
The runbook compares: (1) a single managed VM with Docker Compose, (2) a managed container
service with verified persistent-volume semantics and one SQLite writer, and (3) a private
institutional/VPN host. Every option needs an authentication/access layer because the app
has no built-in accounts, private ingress, persistent storage, monitoring, backup/restore,
and image rollback. Current price/quota assumptions must be verified before selection.

AC1 requires an approved live URL plus health/uptime evidence. AC3 requires a separately
authorized independent reviewer fresh clone. Neither can be completed offline by this owner.

## AC1–AC8 matrix

| AC | Status | Evidence / remaining work |
| --- | --- | --- |
| AC1 — Deployment | NOT RUN / BLOCKED | Hosting and public exposure not authorized; no URL created. |
| AC2 — Reproducibility | PARTIAL | Python 3.11, pinned inputs, explicit config and runbook present; exact image build blocked on dependency-download authorization. |
| AC3 — Fresh Clone | NOT VERIFIED | Reviewer clone authorization absent. |
| AC4 — Data | NOT RUN | No migration/seed/reset/persistence run on an M6-T04 exact image. |
| AC5 — Runtime | NOT RUN | Accepted M6-T03 reference retained; no M6-T04 image replay/Verify rerun. |
| AC6 — Sessions | NOT VERIFIED | Browser-based independent sessions were not started after the build stop. |
| AC7 — Safety | PASS for checkpoint boundary | Loopback-only config; replay/cache-off identity explicit; no public exposure, secret, PII, LIVE/API/email call. |
| AC8 — Evidence | PARTIAL | Report/runbook/config checkpoint present; image/log/runtime/PR final evidence pending. |

## Validation log

| Check | Result |
| --- | --- |
| Trello authorization and dependency state | PASS |
| Live GitHub `dev` vs authorized SHA | PASS — identical |
| Local fetch and branch creation | PASS |
| Initial working tree | PASS — clean |
| Python/Docker/Compose/resources | PASS |
| Default and DEMO Compose config | PASS |
| Offline exact-image build | FAIL closed; dependency download authorization required |
| Exact image inspect / Python in new image | NOT RUN — image absent |
| Startup / health / logs | NOT RUN |
| Synthetic migration/seed/reset/restart/recovery | NOT RUN |
| Critical replay and Verify V01–V04 | NOT RUN on M6-T04 image |
| 2–3 independent browser sessions | NOT VERIFIED |
| Public deployment / fresh clone | NOT AUTHORIZED |

## Files changed and self-review

- `compose.yaml`
- `docs/deploy/M6_T04_RUNBOOK.md`
- `reports/sprints/M6_T04_DEPLOYMENT_ACCEPTANCE.md`

Self-review scope: deployment config and evidence only. The change is backward compatible,
keeps loopback bindings and existing volumes, and introduces no secret or credential. No
database was deleted or modified. Rollback is a revert of this checkpoint; no schema/data
migration is involved.

## Required decisions and next step

1. Coordinator approves or denies a single scoped dependency-enabled Docker build.
2. Coordinator later selects hosting, budget, credentials and access/exposure policy for AC1.
3. Coordinator separately authorizes Vũ's independent fresh clone for AC3.

After decision 1, resume with the runbook: build and pin image ID, start isolated DEMO,
health/config/secrets checks, synthetic persistence/recovery, exact-image replay/Verify,
real 2–3 browser-session smoke, then update this report and PR as `PARTIAL ONLY` until
AC1 and AC3 have their external evidence.
