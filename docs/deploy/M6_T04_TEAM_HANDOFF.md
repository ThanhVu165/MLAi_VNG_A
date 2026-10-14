# M6-T04 — Bàn giao private deployment và Restricted DEMO preflight

**Ngày:** 14/10/2026, Asia/Saigon. **Result:** PARTIAL / PUBLIC_GATE_HOLD.
Tài liệu này bàn giao phiên bản đã kiểm tra và phần việc còn lại; không cấp quyền
implementation, public deployment, merge hoặc DONE cho người nhận.

## 1. Đọc trước và nhận việc

- Repository: [ThanhVu165/MLAi_VNG_A](https://github.com/ThanhVu165/MLAi_VNG_A).
- PR hiện có: [#51](https://github.com/ThanhVu165/MLAi_VNG_A/pull/51), base `dev`.
- Branch bàn giao: `sprint/m6-t04-deployment-acceptance`.
- Task Contract M6-T04: [Trello MENWGSkO](https://trello.com/c/MENWGSkO).
- [AGENT.md](../../AGENT.md), [TEAM_WORKFLOW](../TEAM_WORKFLOW.md),
  [PROJECT_SPEC](../../PROJECT_SPEC.md), [STATUS](../../STATUS.md),
  [roadmap](../SPRINT_ROADMAP.md): ranh giới workflow và kỹ thuật.
- [Báo cáo đầy đủ](../../reports/sprints/M6_T04_DEPLOYMENT_ACCEPTANCE.md):
  đọc mục Private container acceptance; các mục trước giữ historical failures.
- [Runbook](M6_T04_RUNBOOK.md): local Compose và các gate deployment.
- [Restricted DEMO contract draft](M6_T04_RESTRICTED_DEMO_CONTRACT_DRAFT.md):
  dự thảo để Coordinator duyệt, chưa phải task READY.

Trong checkout hiện có, kiểm working tree trước; nếu dirty thì dừng việc chuyển branch
và bảo toàn thay đổi. Không reset/stash/clean/force-push/rebase để nhận bàn giao.

```powershell
git status --short --branch
git remote -v
git ls-remote origin refs/heads/dev refs/heads/sprint/m6-t04-deployment-acceptance
git fetch origin
git switch sprint/m6-t04-deployment-acceptance
git pull --ff-only origin sprint/m6-t04-deployment-acceptance
git rev-parse HEAD
```

Nếu branch local chưa có, sau khi fetch dùng
`git switch --track origin/sprint/m6-t04-deployment-acceptance` thay lệnh switch trên.
Đây là hướng dẫn cho checkout được phép dùng; clone/fresh-clone độc lập vẫn cần quyền
Coordinator theo Task Contract. Không tự tạo worktree/backup checkout.

## 2. Các SHA khác nhau có ý nghĩa gì

| Identity | SHA |
| --- | --- |
| Verified remote dev tại preflight | `eaaeea88a59618b49219a20ae01a3cf3227cec87` |
| Candidate được Phase D duyệt ban đầu / Railway source-config pin | `b7a0658ded496a0b88938f79da32da526ca5dc53` |
| Actual deployed SHA, metadata và container env | `61e31e8db1784fb2f387efceaaf013a45401204e` |
| Checkpoint báo cáo container trước bàn giao | `d37a38df41df2f587f82d68de44853770b2b7e98` |

HEAD PR sẽ tăng sau commit bàn giao; lấy SHA chính xác từ PR/Git, không gọi HEAD tài liệu
là SHA đang chạy Railway. Commit bàn giao chỉ sửa tài liệu/artifact kiểm tra ngoài Docker
context, không phải hotfix ứng dụng mới.

App source/UI/policy/schema/cassette của deployed SHA giống verified dev.
Diff dev → deployed SHA chỉ gồm `.dockerignore`, `compose.yaml`, runbook và report.
Diff b7a0658 → 61e31e8 chỉ có report bị loại khỏi Docker context. Container comparison:
72/72 application/config files match b7a0658; BASE24 24/24 file hashes match.
Content equivalence không chứng minh exact-SHA deployment PASS.

## 3. Coordinator decision hiện hành và ownership

[D1–D4](https://trello.com/c/MENWGSkO#comment-6acf4ca53a2061bfdcd91356),
14/10/2026 16:34:29 UTC+07, là quyết định mới nhất đã đọc lại khi bàn giao:

- D1: **ACCEPT LIMITED** 61e31e8 cho private runtime checkpoint; không thay frozen
  baseline, không exact-SHA deployment PASS, không public authorization.
- D2: Restricted DEMO được chấp thuận về phương án; guest chỉ dùng synthetic workflows
  được duyệt, không tự nhận ADMIN/APPROVER, phải chặn đặc quyền tại tầng xử lý.
- D3: **separate hotfix contract required**; Coordinator chốt Task ID, Owner, reviewer,
  baseline, files, AC1–AC7, validation/Stop Conditions và READY trước implementation.
- D4: **PUBLIC GATE HOLD** đến hotfix acceptance, approved exact deploy SHA, security/
  replay/Verify, image/browser/concurrency/persistence và independent review.

M6-T04 card mô tả Nam là Owner, Vũ Final Reviewer; comment authorization A–C đã chuyển
Execution Owner sang Project Coordinator. Người nhận không tự thay Owner dựa trên tên
branch/PR. Hotfix Owner/Reviewer/Task ID đều PENDING COORDINATOR APPROVAL.
Không tìm thấy contract hotfix riêng trong 27 open cards của board tại preflight.

## 4. Railway hiện tại

| Field | Value |
| --- | --- |
| Provider / project | Railway / sweet-perfection |
| Project ID | `445f0a61-eff6-4f86-a83b-5ca7ef4a0e4c` |
| Environment / ID | production / `04b4c112-4685-44a3-921a-5f3fdd45c596` |
| Service / ID | invigorating-fascination / `589b10fc-df1b-4c0b-82f8-8d5e5139c6f3` |
| Deployment / snapshot | `c8930474-219b-4d9f-b736-2f0803888cb9` / `e03c8df7-7308-4bc2-830a-eea5c7c174c3` |
| OCI manifest digest | `sha256:1611638a236fc6299b321ae0bfca9f0c966a42557441d9c6df9385a2f773a585` |
| Image config digest | `sha256:337ca9414a2d26e6c62152e846b3284bc936354508b17d3e3084a3ae3e23908a` |
| Builder / entrypoint | Root Dockerfile; existing CMD run_local.py / 0.0.0.0:8511; no Railpack/start override |
| Python / health | 3.11.17; `/_stcore/health`, HTTP 200 / `ok`, timeout 120s |
| Volume / ID | m6-t04-demo / `5716d341-9768-4be6-9091-8f56429c3596`, 500 MB, iad, `/runtime` |
| Database | `/runtime/demo.db` |
| Last provider readback | SUCCESS, one replica; no public/custom domain or staged changes |
| Public URL | **NONE** |

Actual safe runtime configuration, measured inside container:

```text
LLM_MODE=replay
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-6-luna
OPENAI_REASONING_EFFORT=none
LLM_CACHE=0
LLM_TIMEOUT_S=30
LLM_RETRIES=1
SIMILARITY_THRESHOLD=0.35
CITATION_RATIO_MIN=0.6
RETRIEVAL_TOP_K=6
QUESTION_WORDS_MIN=8
QUESTION_WORDS_MAX=45
PENDING_SEND_SECONDS=60
PENDING_STATUS_REFRESH_SECONDS=1
DATABASE_PATH=/runtime/demo.db
PORT=8511
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

Readback measured the core identity/DB/port fields; remaining thresholds were also
asserted against CONFIG by the successful replay probe. Telemetry-disable setting was
configured on Railway; it is not independently shown in the published readback JSON.
No OpenAI/Anthropic/email credentials were configured in the checked fields.
User reported Trial/$5 credit before the build; **current balance is not verified**.
Check credit before any authorized new build; do not enable billing/payment/paid plan.
The old MLAi_VNG_A service was not deleted; do not apply unrelated destructive patches.

## 5. Kiểm tra đã hoàn thành và giới hạn

| Check | Result / scope |
| --- | --- |
| Root Docker build/export/push, startup | PASS, actual deployment/image above |
| Internal health and worker marker | PASS; email-processing/email-dispatch alive; no real email connected |
| /app artifact and credential-pattern scan | 0 matching findings; narrow scan, not complete security/PII certification |
| Actual DB | 6/6 synthetic sources, 72 chunks, 6 originals, 0 cases/audit; quick_check=ok |
| Critical decision paths | 4/4: AUTO_REPLY, AUTHORITY_REQUIRED, FACT_UNRESOLVED, OUT_OF_POLICY |
| Verify V01–V04 | 4/4 semantic matches |
| Human R11 | Real UI decision/worker, PENDING_APPROVAL, one draft, job `done` |
| Replay | 24/24 hits, zero misses, LIVE=0; provider/cache/socket/DNS denied in probe process |
| Isolated volume DB | Separate-process reopen, backup/restore to new path, fresh seed/idempotence PASS |
| Data preservation | Live demo hash/counts and local data/app.db unchanged; temp test DBs removed |
| Service restart / container replacement persistence | NOT RUN |
| Live DEMO reset | NOT RUN |
| External public HTTPS / real browser concurrency | NOT RUN |
| Independent fresh clone | NOT VERIFIED |
| Restricted DEMO hotfix | NOT IMPLEMENTED |

Prior host targeted tests remain scoped history: 33 PASS / 3 FAIL / 3 SKIP in the selected
39-test run; three R2 logger/live-capture checks retained FIXTURE_HASH_MISMATCH. Another
42 migration/seed/worker checks passed. Do not change fixture hashes/expected results
from this task or claim the full suite passed. See report for commands and attribution.

## 6. Portable evidence và cách kiểm lại khi cần

Public-safe observations are now included in this PR, byte-for-byte copies from the
successful private checkpoint, not new runs:

- [Container readback](validation/20261014-container-readback.json).
- [Source/pack comparison](validation/20261014-container-source-check.json).
- [Replay/Verify/human results](validation/20261014-container-runtime.json).
- [Disposable-volume recovery](validation/20261014-container-recovery.json).
- [Executed task-local replay driver](validation/private_runtime_probe.py).

Driver SHA-256: `009616dca910362f0e72dc0acb62e2ec72b9f82039cc3b9b40df549fd0cddbfd`.
It reads live DEMO metadata in read-only mode, configures a fresh /tmp DB before corpus
imports, denies network/provider/cache, explicitly selects the human case in AppTest,
and compares demo before/after. It does not implement application authorization.

Original failed validation-driver assertions and stderr/provider logs stay in ignored
local `data/validation/m6-t04/`; they are not required for access to the published result
and are not claimed to be available on a teammate's machine. Report discloses the seed
field/import, selected-case and lowercase job-state corrections. No business output or
fixture was edited to make the replay pass.

SSH requires the teammate's own registered key and Railway account/project permission.
Do not copy another person's private key. The known working instance ID was
`19c74e1f-de9a-4833-9854-a73a11f50a95`; obtain the current value from the service command
palette after any restart/replacement. Workspace ID and Service ID are not SSH targets.
Establish host trust through the team's SSH procedure; do not disable host checking.

After that prerequisite, example PowerShell on a machine with OpenSSH:

```powershell
$taskKeyPath = '<your-local-private-key-path>'
$taskInstanceId = '19c74e1f-de9a-4833-9854-a73a11f50a95'
$taskHostFile = '<your-verified-known-hosts-file>'
ssh -i $taskKeyPath -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$taskHostFile" "$taskInstanceId@ssh.railway.com" 'python --version'
Get-Content -LiteralPath docs/deploy/validation/private_runtime_probe.py -Raw | ssh -i $taskKeyPath -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$taskHostFile" "$taskInstanceId@ssh.railway.com" 'python -'
```

The driver expects this exact private checkpoint's /app paths, /runtime/demo.db and
BASE24 config. Do not run it blindly against a new Restricted DEMO revision: privileged
guest actions should be denied there, so its private human-R11 driver needs an approved
trusted validation context. Review intended mode/identity/DB before execution.
JSON `passed=true` plus 24 hits/0 misses/unchanged demo is the measured criterion;
successful SSH exit alone is not a replay PASS.

Local build/start commands remain in the runbook and require their build authorization;
Compose uses `/runtime/app.db`, Railway uses `/runtime/demo.db`. Keep this distinction.

## 7. Blocker và phần việc cần người nhận làm

1. **D3 contract chưa READY:** Coordinator assigns hotfix Task ID/Owner/Reviewer,
   baseline, cross-module file ownership, authorization contract and AC1–AC7.
   Use the linked draft; do not implement merely because PR #51 is ready for review.
2. **Public privileged access unsafe:** see the draft's full action map. It includes
   admin intake/store/lifecycle, human approval SQL helpers, sidebar pause/resume,
   audit-page override, cancel/correction/retry/resume and unrestricted pasted inputs.
   Hiding pages/buttons or checking actor prefixes is insufficient.
3. **Judge workflows need decision:** proposed guest access is fixed synthetic samples
   plus Verify4/read-only results; anonymous human approval/R11 is not yet approved.
   Coordinator must decide the effect on human-control demo requirements.
4. **New deployment revision:** after hotfix acceptance/integration disposition, obtain
   approved exact SHA; do not reuse b7a0658 pin, private 61e31e8 acceptance or documentation
   HEAD as permission to build/expose another revision.
5. **Remaining M6 gates:** new image/env/source/pack/security/replay checks; actual
   private browser sessions, container restart/persistence/reset on an approved disposable
   synthetic environment; independent fresh clone; then public gate and external HTTPS.

Dependency chain:

```text
Contract APPROVED / READY
→ Hotfix implementation + AC1–AC7 evidence
→ Independent review + Coordinator acceptance
→ Approved integration/deploy exact SHA
→ Private redeploy + new-image safety/runtime/browser/concurrency/persistence
→ Public gate decision
→ Public HTTPS URL + external browser/health
→ M6-T04 final review / Coordinator acceptance
```

Do not re-run historical checks just to populate reports. On a changed accepted image,
checks are new-image evidence and must identify its SHA/digest/config/DB/pack and limits.
Keep local historical evidence and rejected images quarantined.

## 8. AC1–AC8 khi bàn giao

| AC | Status |
| --- | --- |
| AC1 Deployment | PARTIAL, private SUCCESS only; public URL/uptime missing |
| AC2 Reproducibility | PARTIAL; digest/config/source/pack evidence; exact-SHA public gate pending |
| AC3 Fresh Clone | NOT VERIFIED |
| AC4 Data | PARTIAL; seed/reopen/backup/restore PASS, container restart/reset pending |
| AC5 Runtime | PASS within observed private critical/Verify/R11/replay scope |
| AC6 Sessions | NOT VERIFIED, no real independent browser concurrency |
| AC7 Safety | PARTIAL / PUBLIC_ACCESS_GATE_BLOCKED; current app authorization unsafe |
| AC8 Evidence | PARTIAL; portable handoff available, final reviewer/deployment evidence pending |

## 9. Recovery và nguyên tắc không vượt quyền

Do not use rejected image
`sha256:8e408bd7aa6462bb412a8211b12075c84abf795cc7d35462660c7d892b9e40b8`.
It contained pytest .env/DB artifacts and was quarantined. The current accepted-limited
private image is not a safe public rollback target. Any rollback stays private and uses
an explicitly approved inspected image with backups; restore DB to a new path, not over
live data. Stop on unsafe exposure, replay/security failure, dirty/conflicting work,
unapproved schema/audit/policy changes, insufficient Trial credit or new source mismatch.

No LIVE/record/API/email, real PII, paid billing, destructive Railway batch, merge PR #51,
frozen-baseline change or M6-T04 DONE is authorized by this handoff. Private-key/token
provisioning and Owner/Reviewer/Coordinator decisions remain human controlled.
