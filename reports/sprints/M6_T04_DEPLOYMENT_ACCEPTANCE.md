# M6-T04 — Nghiệm thu triển khai và khả năng tái lập

> Checkpoint mới nhất: xem **Private container acceptance — 14/10/2026** ở cuối file.
> Railway private runtime/replay đã kiểm trực tiếp; public deployment vẫn BLOCKED.
> Toàn bộ image/test evidence phía dưới đến trước follow-up là historical checkpoint.
> Phase D recheck 15:12: deletion đã hủy; public-access finding được tái hiện trên SHA được duyệt.
> Phase D execution 15:18: Trello approval đã có; Apply/Deploy bị lớp xác nhận công cụ hủy, chưa build.
> Latest: private Docker build/health, container source/pack scan và critical replay/Verify PASS có giới hạn; public access và exact deployed SHA chưa đạt.

## Kết luận checkpoint

- **KẾT QUẢ: BLOCKED / PARTIAL ONLY**
- Nhánh local: `sprint/m6-t04-deployment-acceptance`
- Baseline được duyệt: `dev@eaaeea88a59618b49219a20ae01a3cf3227cec87`
- SHA dùng để build/test image: `81f340c72d9b75567920299a1761cf762311c233`
- Image: `exodia:m6-t04-81f340c`
- Image ID: `sha256:8e408bd7aa6462bb412a8211b12075c84abf795cc7d35462660c7d892b9e40b8`
- Remote branch: `https://github.com/ThanhVu165/MLAi_VNG_A/tree/sprint/m6-t04-deployment-acceptance`
- Draft PR: `https://github.com/ThanhVu165/MLAi_VNG_A/pull/51`
- Public hosting, LIVE LLM, API ngoài và email thật: **0**

Không được dùng image trên để triển khai hoặc làm image nghiệm thu. Container DEMO local đã
được dừng ngay sau khi phát hiện lỗi. Không tuyên bố Task DONE, M6 PASS, hosting PASS hoặc
fresh-clone PASS.

## Safety failure bắt buộc dừng

Clean build có network được Coordinator cấp quyền đã hoàn tất, nhưng bước quét image phát
hiện workspace tạm của pytest bị đóng gói vào `/app` vì `.dockerignore` chỉ loại
`.pytest_cache/`, chưa loại `.pytest-*`.

Ví dụ artifact được tìm thấy trong image:

- `/app/.pytest-anti-test-run/test_database_isolated_before_2/.env`
- `/app/.pytest-anti-test-run/test_database_isolated_before_2/data/app.db`
- nhiều file `*.db` khác dưới các thư mục `/app/.pytest-*`

Không đọc nội dung các file `.env`; chúng được xử lý như secret-risk theo nguyên tắc
fail-closed. Dù đường dẫn cho thấy đây là dữ liệu test/synthetic, image không đạt yêu cầu
secret hygiene và khả năng tái lập từ source sạch.

**PROBLEM:** build context chứa artifact pytest không được `.dockerignore` loại bỏ.

**IMPACT:** AC2 và AC7 không thể PASS; image không được push/deploy. Lượt clean build có
network duy nhất đã được sử dụng nên không được tự ý sửa rồi build lại.

**EVIDENCE:** lệnh quét read-only trong image bằng `find /app` trả về các file `.env` và
`*.db` dưới `.pytest-*`; container đang chạy được xác nhận dùng đúng image ID nêu trên.

**SOLUTION:** thêm mẫu loại trừ `.pytest-*/` vào `.dockerignore`, xóa/không đưa artifact
test vào build context, rồi chạy một clean build mới và lặp lại toàn bộ image scan,
runtime, replay/Verify, persistence/recovery và session checks.

**RESPONSIBLE:** implementer sửa build context sau khi Coordinator cấp quyền build lại;
reviewer kiểm tra image mới độc lập.

**COORDINATOR DECISION NEEDED:** cấp quyền cho **một clean Docker build có network bổ sung**
sau bản sửa `.dockerignore`. Quyền build một lượt trước đó đã được sử dụng.

## Build và môi trường đã quan sát

| Trường | Giá trị |
| --- | --- |
| Lệnh | `docker build --pull=false --no-cache -t exodia:m6-t04-81f340c .` |
| Kết quả build | PASS |
| Python trong image | `3.11.17` |
| Kích thước image | `569311354` byte |
| Docker / Compose | Engine `29.1.3`; Compose `v2.40.3-desktop.1` |
| Host Docker | Linux `x86_64`, 8 CPU, 8,218,968,064 byte RAM |
| Nguồn tải | Python/PyTorch package indexes đã cấu hình; không đổi version/source |

`requirements.txt` và CPU Torch được pin trực tiếp. Tuy nhiên một số dependency bắc cầu
vẫn được resolver chọn theo index tại thời điểm build; đây là rủi ro tái lập còn lại.

## Bằng chứng runtime đã thu trước safety gate

- DEMO chạy bằng Compose project `exodia-m6t02-validation-m6t04`, bind duy nhất
  `127.0.0.1:18513`, health trả `HTTP 200 / ok`.
- Cấu hình runtime: `/runtime/app.db`, `replay/openai/gpt-6-luna/none`, cache `0`,
  Streamlit usage telemetry `false`, `no-new-privileges:true`.
- Log có marker hai worker `email-processing` và `email-dispatch` hoạt động.
- Quan sát tài nguyên: khoảng `46.57 MiB`, 13 PID, 0.46% CPU tại một thời điểm.
- SQLite schema version `2`, 15 bảng, seed `6` sources / `72` chunks; chạy seed lần hai
  không tạo bản ghi lặp.
- Synthetic probe tồn tại sau restart đúng image và sau controlled `SIGKILL` + start.
- BASE24: 24/24 hash đúng, 0 mismatch.
- Critical + Verify: 7 luồng, 23 replay hit, 0 miss, LIVE 0; critical 4/4 và
  Verify V01–V04 4/4 đạt semantic expectation.
- Hai kiểm thử AppTest độc lập trong chính image, `--network none`, read-only filesystem,
  cap-drop và no-new-privileges: **2 passed**; xác nhận hai session không gửi lặp và reload
  không tạo case lặp. Đây không thay thế bằng chứng hai browser context thật.

Aggregate runner mở rộng dừng ở nhánh UI R11 với `KeyError choice_<case>` sau khi bảy
luồng mục tiêu đã chạy. Bằng chứng AC5 chỉ dựa trên scope critical 4/4 + V01–V04 4/4,
không nhận R11.

## Sự cố thủ tục đã được cô lập

Trong một shell kiểm tra restart, biến `EXODIA_IMAGE` và `DEMO_HOST_PORT` chưa được export
lại nên Compose tạm recreate service bằng image mặc định `exodia:m6-t02` tại cổng 8513.
Sai lệch được phát hiện ngay bằng `docker inspect`; kết quả đó không được dùng làm bằng
chứng. Service sau đó được force-recreate bằng đúng image M6-T04 và cổng 18513, giữ nguyên
volume synthetic. Runbook phải yêu cầu export lại biến ở mỗi PowerShell mới.

## AC1–AC8

| AC | Trạng thái | Bằng chứng / phần còn thiếu |
| --- | --- | --- |
| AC1 — Deployment | NOT RUN / BLOCKED | Chưa có quyền hosting/public URL; không tạo URL. |
| AC2 — Reproducibility | FAIL / BLOCKED | Build chạy được nhưng image chứa `.pytest-*`, `.env`, `*.db`; cần image sạch mới. |
| AC3 — Fresh Clone | NOT VERIFIED | Chưa có nghiệm thu fresh clone độc lập của reviewer. |
| AC4 — Data | PARTIAL PASS | Migration/seed/idempotence/persistence/recovery đạt trên image hiện tại; reset cuối chưa chạy vì safety STOP. |
| AC5 — Runtime | PASS có giới hạn | Critical 4/4, Verify 4/4, 23/23 replay hit, miss 0, LIVE 0 trên SHA/image nêu trên. |
| AC6 — Sessions | NOT VERIFIED | AppTest hai session đạt 2/2; browser thật không chạy được vì Computer Use kernel lỗi trước khởi tạo. |
| AC7 — Safety | FAIL / BLOCKED | Loopback/replay/network-disabled đạt, nhưng image secret hygiene thất bại. |
| AC8 — Evidence | PARTIAL | Config/runbook/report đã publish qua Draft PR #51; evidence cuối vẫn thiếu do safety gate. |

## Validation log

| Kiểm tra | Kết quả |
| --- | --- |
| Trello authorization và dependency state | PASS |
| Live GitHub `dev` đúng SHA được duyệt | PASS |
| Clean network build được cấp quyền | PASS; quyền một lượt đã dùng |
| Image identity / Python | PASS |
| Startup / health / worker / loopback | PASS |
| Migration / seed / restart / crash recovery | PASS |
| BASE24 integrity | PASS 24/24 |
| Critical + Verify offline | PASS 7 luồng, 23/23 hit, LIVE 0 |
| AppTest hai session | PASS 2/2 |
| Hai browser context thật | NOT VERIFIED — kernel lỗi `failed to write kernel assets: The system cannot find the path specified. (os error 3)` |
| Quét secret/artifact trong image | **FAIL — safety stop** |
| Reset/recreate cuối | NOT RUN — dừng theo Coordinator gate |
| Push / PR | PASS — Draft PR #51, chỉ publish checkpoint BLOCKED, không phải nghiệm thu |

## Thay đổi local và self-review

- `compose.yaml`: chọn image qua `EXODIA_IMAGE`, chốt replay identity và tắt Streamlit
  usage telemetry.
- `docs/deploy/M6_T04_RUNBOOK.md`: runbook local, recovery, rollback và hosting decision
  packet; chưa được nghiệm thu cuối.
- `reports/sprints/M6_T04_DEPLOYMENT_ACCEPTANCE.md`: report này.

Không sửa production logic, policy, Gold, cassette, schema hoặc dependency version.
Không force-push, merge, rewrite history, public deploy, gọi LIVE/API/email hay đọc nội
dung artifact `.env`. Image lỗi và volume synthetic vẫn được giữ local để điều tra; chỉ
container đã dừng. Git chỉ chứa config/runbook/report; Docker image, DB, raw log và
artifact `.pytest-*` không được đưa vào commit.

## Quyền còn cần xin

1. Quyền sửa `.dockerignore` và chạy thêm một clean Docker build có network từ đúng các
   package index đã duyệt.
2. Sau khi image mới pass safety: quyền tiếp tục reset/recreate cuối và browser-context
   nghiệm thu nếu công cụ GUI hoạt động.
3. Quyết định riêng cho hosting/provider/budget/access để thực hiện AC1.
4. Quyền fresh clone độc lập cho reviewer để thực hiện AC3.

## Public deployment follow-up — 14/10/2026, 14:49 UTC+07

### RESULT / TASK STATUS

**BLOCKED / PARTIAL — PUBLIC_URL_READY chưa đạt; M6-T04 CHƯA DONE.**
Checkpoint mới này không thay thế historical image evidence phía trên.
Execution Owner theo Trello: **Project Coordinator, tiếp nhận từ Nam**.
Vũ vẫn là Final Reviewer; Codex hỗ trợ kỹ thuật, không đăng quyết định thay các vai trò.

### Authorization và dependencies

Đã đọc trực tiếp [Task Contract](https://trello.com/c/MENWGSkO), bao gồm comment
`[M6-T04] COORDINATOR AUTHORIZATION` ngày 14/10/2026, 06:01 UTC+07:

> Hosting: NOT SELECTED.
> Public deployment / LIVE LLM / API / email: NOT AUTHORIZED.
> Phase D: chỉ triển khai sau khi Coordinator duyệt hosting, access policy và safety.

Comment cho phép phase A–C offline readiness trên verified baseline
`eaaeea88a59618b49219a20ae01a3cf3227cec87`.
User yêu cầu hỗ trợ public deployment từ đúng task branch và đã cài/kết nối Railway
trong phiên này. Chưa có quyết định mới về access policy, quota/billing hoặc quyền
áp dụng lệnh xóa đang staged. Vì vậy chưa trigger provider build/deploy hoặc tạo domain.

M6-T02, M6-T03, M6-T05 đều nằm trong list **Done - Đã nghiệm thu** khi đọc Trello.
M6-T03 comment xác nhận M6-T02/M6-T05 được nghiệm thu; Git history hiện hành chứa
integration M6-T03 (PR #48). Không dùng số tests/cassette trong memory làm current evidence.

### HOSTING / PUBLIC URL

| Trường | Kết quả quan sát |
| --- | --- |
| Provider | Railway — connected; hosting approval chưa được xác minh |
| Workspace | Thành Vũ's Projects (personal) |
| Project | sweet-perfection — `445f0a61-eff6-4f86-a83b-5ca7ef4a0e4c` |
| Environment | production — `04b4c112-4685-44a3-921a-5f3fdd45c596` |
| Prepared service | invigorating-fascination — `589b10fc-df1b-4c0b-82f8-8d5e5139c6f3` |
| Service state | staged-create, chưa có deployment |
| Builder | DOCKERFILE trong staged config; path `Dockerfile` |
| Start command | Không override; giữ Docker CMD `python run_local.py ... --server.port 8511` |
| Health | Configured `/_stcore/health`, timeout 120s; HTTP chưa chạy |
| Public HTTPS URL | Không có; không tạo domain |
| Billing | Không kích hoạt/nâng plan/thêm payment; actual plan/quota NOT VERIFIED |
| DEMO storage | `m6-t04-demo`, 500 MB, mount `/runtime`; staged, chưa provision |
| Runtime DB | `/runtime/demo.db`; chưa tạo DB trên hosting |

Old service `MLAi_VNG_A` (`2077676c-af59-4a45-8bdc-a20e9cafb8df`) có deployment
`c551b9f4-d172-4202-8db3-6a89153cf81c` FAILED.
Build logs 14:41 UTC+07 ghi `using build driver railpack-v0.40.1` và
`No start command detected`; old service source là `main`.
Đây là deployment có sẵn trước khi Codex kiểm tra; không phải Docker build của M6-T04.
Không áp dụng hướng dẫn đoán start command từ log; service mới giữ Dockerfile.

### GIT REVISION / BUILD

- Repo xác minh: `https://github.com/ThanhVu165/MLAi_VNG_A.git`.
- Verified remote dev: `eaaeea88a59618b49219a20ae01a3cf3227cec87`.
- Verified remote task head trước thay đổi: `212fc622031e6dfa48c01b7e242155df144eb847`.
- Checkout đầu phiên: `sprint/m3-t06-human-control-e2e@eaaeea8`, working tree sạch.
- Đã checkout cùng repository sang task branch bằng tracking ref đã tồn tại;
  không ghi đè remote branch, clone/worktree, reset/stash/rebase/merge/force-push.
- PR [#51](https://github.com/ThanhVu165/MLAi_VNG_A/pull/51): OPEN, DRAFT, base `dev`.
- GitHub account có permission `admin`; quyền repository không thay thế Coordinator approval.
- Host-tested SHA: `eaaeea88a59618b49219a20ae01a3cf3227cec87`.
  `core corpus infra pages policies ui verify tests` không có diff với task head `212fc62`.
- Deployed SHA / new image tag / new digest: **không có**.
- New Docker build / container startup / public HTTP / application UI: **NOT RUN** từng bước.
- Python host và .venv: **3.11.9**; Python image mới: **NOT VERIFIED**.
- Docker/Railway CLI không nằm trong PATH; không tìm thấy Docker ở default Program Files path.
- Image cũ `sha256:8e408bd7...40b8` vẫn **không được dùng**. Chưa inspect lại image đó.
- Dockerfile Git blob SHA-256: `324dcfcce544b69a5893970034eb1c2085a26196473ee1766cc658ddb0bd5128`.

### Thay đổi và cấu hình đã chuẩn bị

1. `.dockerignore`: thêm `.pytest-*/`; thay `tests/` bằng `tests/*` +
   `!tests/cassettes/` để Docker context có accepted replay pack, giữ phần test code khác ngoài image.
   Không sửa bytes/provenance của cassette hoặc manifest.
2. Railway staged source: `ThanhVu165/MLAi_VNG_A@sprint/m6-t04-deployment-acceptance`.
   Pin source commit sau khi publish checkpoint; phải đọc lại source trước accept-deploy.
3. Railway staged config: Dockerfile path, health và ON_FAILURE/max retries=3.
4. Railway staged variables: toàn bộ identity/config từ canonical BASE24,
   override `LLM_MODE=replay`, `LLM_CACHE=0`, `DATABASE_PATH=/runtime/demo.db`,
   `PORT=8511`, usage telemetry=false. Không set API key hoặc email credential.
5. Railway staged volume: 500 MB, chưa provision hoặc chạy workload.

`LLM_MODE=replay` đơn lẻ chưa đủ: source cần OPENAI_MODEL và đúng cassette path.
Folder `tests/cassettes` hiện chỉ có đúng 24 file canonical, không có extra file.
Source fix chưa chứng minh actual Docker context/image sạch.

[Docker docs](https://docs.docker.com/build/concepts/context/) mô tả exclusion/exception
trong .dockerignore. [Railway Dockerfiles](https://docs.railway.com/builds/dockerfiles)
xác nhận root Dockerfile detection; [domain docs](https://docs.railway.com/networking/domains/working-with-domains)
có target-port mapping. Port dự kiến 8511; chưa có domain được cấu hình.
[Railway Free Trial](https://docs.railway.com/pricing/free-trial) không chứng minh
tài khoản hiện hành có quota khả dụng; không tự nâng Hobby/paid plan.

### Validation commands và kết quả mới

Chạy bằng PowerShell tại repo root; `PYTHONDONTWRITEBYTECODE=1` được set trước pytest.
`tests/conftest.py` tạo fresh absolute temporary SQLite DB trước import,
ép replay và deny socket/provider constructors. Các runner tên LIVE trong tests dùng mocks.

```powershell
git remote -v
git ls-remote origin refs/heads/dev refs/heads/sprint/m6-t04-deployment-acceptance
git diff --name-only HEAD origin/sprint/m6-t04-deployment-acceptance -- core corpus infra pages policies ui verify tests

.\.venv\Scripts\python.exe -m pytest tests/test_m3_t06_human_control.py tests/test_r2_validation_diagnostics.py tests/test_guards.py::test_extraction_schema_normalizes_for_openai_without_mutation tests/test_guards.py::test_extract_retries_invalid_payload_once_then_records_error tests/test_guards.py::test_extract_timeout_is_fail_safe_and_records_error tests/test_telemetry.py -q --tb=short

.\.venv\Scripts\python.exe -m pytest tests/test_workflow_migrations.py tests/test_seed_fidelity.py tests/test_runtime_worker.py -q --tb=short

git diff --check
Get-FileHash -LiteralPath data/app.db -Algorithm SHA256
```

| Check | Fresh result |
| --- | --- |
| Human Control/R2/extraction/telemetry suite | **33 PASS / 3 FAIL / 3 SKIP**, exit 1, 19.61s |
| Migration/seed/worker suite | **42 PASS**, exit 0, 23.93s |
| BASE24 inventory/hash check | **24/24 matches, 0 extra files, 0 mismatches**, assert-based check exit 0 |
| Six source seed metadata | **6/6 is_synthetic=true** |
| .dockerignore config/entrypoint checks | PASS for source configuration only; real Docker matcher/image NOT VERIFIED |
| Tracked text secret patterns | 0 credential-literal/private-key-marker findings; narrow automated scan only |
| Existing local DB | Same SHA-256 before/after checks: `7c1b78dba687a7780b71a2300dbcc8d416e64cb6b1aa62adf953eb6054de5752` |
| Public/UI/browser sessions/fresh clone | NOT RUN |
| LIVE LLM/provider/email operations in this session | **0 / 0 / 0**; GitHub/Trello/Railway connector calls did occur |

Three failures:
`test_r2_logger_to_live_capture_and_summary[invalid_invalid]`,
`[invalid_valid]`, `[provider_failure]`.
All stop at `verify/m2_dev_execution.py:107` with
`ValueError: BLOCKED_FIXTURE_HASH_MISMATCH`, before mocked artifact capture.
Không sửa frozen fixture, expected/hash hoặc business logic.
Ba SKIP ghi rõ historical LIVE artifacts local không phải required CI fixtures.
Không dùng historical 39 PASS để thay current result.

Manifest SHA-256:
`2a3c80855923010e3ead807424bc1d2e904c01422ab08eade7655fe30aa280c8`.
Hash verification chỉ chứng minh bytes khớp accepted manifest, không phải fresh image replay.
Test outputs được ghi trong tool transcript và bảng trên; không có new build/startup logs.

### ACCEPTANCE CRITERIA — checkpoint mới

| AC | Status | Evidence / còn thiếu |
| --- | --- | --- |
| AC1 Deployment | BLOCKED / NOT RUN | Service/config chỉ staged; chưa URL/health/uptime |
| AC2 Reproducibility | PARTIAL | Python 3.11 host, pin deps, corrected context config; image mới chưa build/scan |
| AC3 Fresh Clone | NOT VERIFIED | Reviewer chưa có authorization hoặc run độc lập |
| AC4 Data | PARTIAL | 42 host migration/seed/worker tests PASS; provider reset/restart/persistence chưa chạy |
| AC5 Runtime | PARTIAL / NOT RUN in new image | 24/24 pack integrity; historical critical/Verify được giữ phía trên; new-image replay chưa chạy |
| AC6 Sessions | NOT VERIFIED | Worker tests không thay 2–3 real browser sessions |
| AC7 Safety | PARTIAL / BLOCKED | Narrow source scan PASS; old image rejected; new image/public access chưa kiểm chứng |
| AC8 Evidence | PARTIAL | Report/runbook/PR có checkpoint; chưa build/image/public/reviewer evidence |

### BLOCKERS / NEXT ACTION / RECOVERY

- **B1 — Public gate:** Trello chưa có quyết định provider/access/safety mới.
  Impact: không tạo domain hoặc gọi deploy thay approval.
  Coordinator cần duyệt Railway project/service, candidate SHA, synthetic-only data,
  thời hạn exposure và quyền dùng UI quản trị/phê duyệt chưa có authentication.
- **B2 — Destructive pending batch:** Patch `bad1524b-b52c-4fc0-a82c-568a908590b0`
  đã có lệnh **delete MLAi_VNG_A** trước khi Codex staging config.
  Impact: accept-deploy áp dụng cả deletion, không chỉ service mới.
  User/project admin cần bỏ lệnh xóa khỏi pending changes hoặc duyệt riêng việc xóa;
  Codex chưa accept hoặc xóa resource nào. Phải đọc lại get-staged-changes sau disposition.
- **B3 — Billing/quota:** Connected tools đã xác minh project nhưng không trả actual plan/quota.
  User/Coordinator cần xác nhận Free/Trial credit có sẵn, không payment/paid upgrade.
  Build network cho candidate mới cần đúng phạm vi duyệt; quyền build cũ đã dùng.
- **B4 — Image acceptance:** Source config đã sửa; Docker local unavailable và provider chưa trigger.
  Execution Owner build candidate sạch, scan image, then startup/replay/Verify/DB recovery.
  Không phân phối old image hoặc gọi LIVE khi miss.
- **B5 — Regression failure:** 3 hash-mismatch failures giữ nguyên để Runtime/fixture Owner xử lý
  theo scope riêng; không đổi contract/hash từ M6-T04.

Safe work completed: target checkout, minimal context fix, canonical pack checks, host
regressions, secret-pattern scan, prepared Railway staged config/storage/source, report/runbook.
Staged resource chưa provision; không commit environment patch, tạo domain, đổi payment,
đăng comment/message, merge PR hoặc cập nhật Trello/DONE.

Rollback: revert checkpoint config commit nếu cần; không reset DB/cassette.
Giữ local DB và historical evidence nguyên vẹn. Khi candidate được deploy, recovery cần
DB backup + inspected known-good image; image bị từ chối ở historical checkpoint không
được dùng làm rollback image.

Agent self-review: chỉ .dockerignore và docs/deploy/report, không business/schema/policy,
không secret/DB/cache trong diff. Owner self-review/handoff và Vũ final review vẫn pending.
Commit checkpoint theo task contract; Git SHA/status cuối phải xác minh sau commit/push.

## Phase D recheck — 14/10/2026, 15:12 UTC+07

### Approval và resolved blocker

Trong chat, Coordinator đã duyệt **build/public DEMO có điều kiện** cho exact SHA
`b7a0658ded496a0b88938f79da32da526ca5dc53`, Free/Trial only, Dockerfile, replay/offline,
synthetic DEMO và không cho khách thao tác đặc quyền ngoài scope demo.
Quyết định cũng yêu cầu đối chiếu bản ghi Trello trước triển khai; nếu chưa có thì yêu cầu
Coordinator cập nhật, và chỉ build riêng nếu public UI chưa đạt giới hạn an toàn.

- Railway pending changes kiểm lại: **destructive=false**. Lệnh delete service
  `MLAi_VNG_A` đã được hủy trước lượt kiểm này; Codex không xóa service.
- Prepared service vẫn staged-create; chưa có deployment/domain.
- Source pin và builder khớp approved SHA/branch, `DOCKERFILE`, path `Dockerfile`.
- Trello get + list_comments trả đúng một comment A–C cũ, pagination không còn trang;
  chưa có bản ghi Phase D mới tại thời điểm kiểm. Đã yêu cầu Coordinator cập nhật.
- Tools Railway hiện không có billing/credit reader; browser-control attempt vào tab
  project timeout. Không suy ra credit bằng số project hoặc trạng thái REGISTERED.
  Đã hỏi người dùng actual plan/remaining credit/paid billing, không yêu cầu credential.
- Chưa apply environment patch hoặc trigger private build do hai xác minh trên còn thiếu.
  Public-access finding dưới đây chỉ chặn domain; không tự cấm private build sau khi
  Trello/credit đủ.

### Public access finding — reproduced, exact approved source

**PUBLIC_ACCESS_GATE_BLOCKED.** Trang quản trị cho phép khách tự nhập tên để có actor
`ADMIN:<name>`. Không có authentication hay kiểm tra vai trò; nút nạp quy định được bật.
`corpus.intake._ingest` tạo SourceRecord mà không set `is_synthetic`, nên default là
`false`; đường nạp không giới hạn vào accepted synthetic sources.

Evidence source:
`pages/3_Quan_tri_quy_dinh.py:124` (_upload),
`:256` (tên quản trị tự nhập), `corpus/intake.py:96` (SourceRecord),
`corpus/store.py:28` (is_synthetic default false).
Chỉ thị nhắc người dùng dùng dữ liệu synthetic không phải enforcement của public access.

Một isolated AppTest của chính trang quản trị được chạy trên SHA b7a0658:
fresh temporary absolute DB, seed 6 synthetic sources, replay config,
socket connect/connect_ex/sendto/DNS và `llm._call_live` đều bị deny.
Không đổi production, không đưa dữ liệu thật, không bấm nạp tài liệu hoặc phê duyệt.

| Observation | Actual |
| --- | --- |
| Chưa nhập tên: nút Nạp và đọc tài liệu disabled | true |
| Nhập tên synthetic-public-visitor: cùng nút disabled | false |
| Credential/authentication cần để bật nút | Không |
| Exceptions trong AppTest | 0 |
| Seed trước/sau | 6 sources / 6 synthetic |
| Source upload clicked / LIVE provider calls | false / 0 |
| Assertion probe | exit 0 — tái hiện access finding, không phải safety PASS |

Raw observation:
`data/validation/m6-t04/20261014-phase-d-access-check.json` (ignored local evidence).
Lượt này là host AppTest về quyền giao diện; không chứng minh container/UI public,
browser sessions hoặc runtime acceptance trên Railway.
DB local vẫn có hash `7c1b78dba687a7780b71a2300dbcc8d416e64cb6b1aa62adf953eb6054de5752`.

### Updated acceptance / next action

- **AC1: BLOCKED**, chưa domain/health/uptime.
- **AC2: PARTIAL**, source prepared; image build/scan NOT RUN.
- **AC3: NOT VERIFIED**.
- **AC4/AC5: PARTIAL**, không có new container evidence.
- **AC6: NOT VERIFIED**.
- **AC7: FAIL cho anonymous public-access boundary hiện tại**;
  replay/DB isolation không thay thế authentication/synthetic-only intake.
- **AC8: PARTIAL**, report có approval trong chat, resolved deletion và exact-source finding.

Coordinator cần ghi Phase D decision lên Trello; user xác minh Free/Trial credit.
Sau đó được tiếp tục **private Docker build** đúng b7a0658 và kiểm image/startup/replay/DB,
nhưng **không tạo public domain** trên giao diện hiện tại.
Trước public exposure cần access control ở deployment layer chỉ cho người được duyệt,
hoặc một demo-restriction revision được Coordinator duyệt riêng rồi build/verify lại;
không chỉ ẩn trang/nút và không tự sửa UI/business logic trong lượt này.

Deployment source vẫn pin approved b7a0658; commit report sau đó không thay image target.
Không bật billing, không LIVE/email, không merge PR #51 hoặc đánh DONE.

## Phase D execution attempt — 14/10/2026, 15:18 UTC+07

- Trello đã có decision mới **PHASE D PUBLIC DEPLOYMENT AUTHORIZED**,
  action `6acf3a401409fc9f84f4dc87`, timestamp `2026-10-14T08:16:00.261Z`.
  Decision khớp repo/branch, exact SHA b7a0658, Railway project/service/environment,
  Dockerfile/8511/health, replay/offline và isolated `/runtime/demo.db`.
- User xác nhận account là **Trial, còn $5 credit**. Đây là account observation do user
  cung cấp; không phải independent billing read qua connector. Không bật paid billing.
- Staged patch đọc lại **destructive=false**, chỉ create service DEMO + volume riêng;
  không có delete resource và không có public domain.
- Codex đã gọi Railway accept-deploy cho environment production,
  commit message `M6-T04: private Docker build approved b7a0658, replay synthetic DEMO; no public domain`.
- **Tool action CANCELLED**. Full tool result:
  `Cancelled — the user did not approve this action. No changes were made.`
  Structured error `INVALID_ARGUMENT`; không kết luận đây là lỗi config Docker.
- Readback sau cancellation: patch vẫn **STAGED**, destructive=false;
  list-deployments của intended service trả `[]`. Không retry bằng đường khác để
  vượt qua lớp xác nhận; không create service/source live hoặc gọi redeploy thay thế.

### Current status

Approval Coordinator đã được xác minh, không còn blocker “thiếu bản ghi Trello”.
Credit: USER-CONFIRMED Trial/$5, được giới hạn trong Free/Trial theo authorization.
Execution blocker mới là **connector action confirmation cancelled**.
Private Docker build/startup/replay/Verify/DB health vẫn **NOT RUN**; chưa có image/build ref.
Public domain vẫn bị chặn độc lập bởi admin-access finding đã tái hiện ở mục trước.

Next: user chấp thuận thao tác Apply/Deploy tại lớp xác nhận thực thi của Railway,
hoặc tự apply đúng non-destructive pending patch trên dashboard và báo deployment ID
để Codex kiểm logs. Đây không phải yêu cầu Coordinator duyệt lại Task Contract.
Không tạo public domain khi access boundary chưa đáp ứng.

AC1 BLOCKED; AC2 PARTIAL; AC3 NOT VERIFIED; AC4/AC5 PARTIAL;
AC6 NOT VERIFIED; AC7 PUBLIC_ACCESS_GATE_BLOCKED; AC8 PARTIAL.
Không build PASS từ trigger bị hủy, không startup PASS từ staged config.
LIVE LLM/email=0, không billing upgrade, không merge/DONE.

### Retry after explicit user confirmation — 15:25 UTC+07

User chọn “Gọi lại để tôi xác nhận”. Codex kiểm lại pending patch destructive=false,
đúng task branch và source pin b7a0658, rồi gọi accept-deploy lần thứ hai.
Tool lại trả `Cancelled — the user did not approve this action. No changes were made.`
với structured error `INVALID_ARGUMENT`. Readback: patch STAGED, destructive=false,
intended service deployments=[]; build/startup/health vẫn NOT RUN.

Không quy kết lỗi cho Dockerfile hoặc credit. Không lặp thêm hay dùng một live source/
deployment API khác để né cancellation. User cần tự apply đúng pending changes trên
Railway dashboard rồi cung cấp deployment ID hoặc báo đã apply; Codex tiếp tục đọc
build/startup logs. Giữ service private, chưa tạo public domain.

## Private Railway deployment — manual apply, 14/10/2026

**RESULT: PARTIAL — PRIVATE_BUILD_AND_STARTUP_PASS; PUBLIC_URL_NOT_READY.**

User tự bấm Deploy trên Railway. Readback xác nhận staged patch đã được áp dụng,
service và volume hiện live; không có domain được tạo.

| Field | Evidence thực tế |
| --- | --- |
| Deployment ID | `c8930474-219b-4d9f-b736-2f0803888cb9` |
| Snapshot ID | `e03c8df7-7308-4bc2-830a-eea5c7c174c3` |
| Branch trong deployment metadata | `sprint/m6-t04-deployment-acceptance` |
| Authorized/source-config pin | `b7a0658ded496a0b88938f79da32da526ca5dc53` |
| Actual deployment metadata commit | `61e31e8db1784fb2f387efceaaf013a45401204e` |
| Builder | DOCKERFILE; log load build definition from Dockerfile |
| Base image resolved | `python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce` |
| New OCI image digest | `sha256:1611638a236fc6299b321ae0bfca9f0c966a42557441d9c6df9385a2f773a585` |
| Image config digest | `sha256:337ca9414a2d26e6c62152e846b3284bc936354508b17d3e3084a3ae3e23908a` |
| Deployment status | **SUCCESS**, 15:33:43 UTC+07 |
| Container startup | **PASS**, Streamlit URL in container `http://0.0.0.0:8511` |
| Background workers | **PASS**, email-processing + email-dispatch startup/alive marker |
| Internal provider healthcheck | **PASS**, log `[1/1] Healthcheck succeeded!` at 15:33:41 UTC+07 |
| Replica observation | 1 running / 0 crashed, no active warnings/criticals |
| Volume | m6-t04-demo, 500 MB, iad, mounted at /runtime |
| Memory sample | ~0.060 GB current; single observation, not load-test evidence |
| Public HTTPS / external health / browser UI | **NOT RUN**; serviceDomains=[] and customDomains=[] |

### Revision discrepancy

Railway source config pin đọc lại là b7a0658 nhưng deployment metadata commitHash là
61e31e8. Không coi source config riêng lẻ là chứng minh checkout SHA.
Git diff hai SHA chỉ có `reports/sprints/M6_T04_DEPLOYMENT_ACCEPTANCE.md`;
`reports/` bị loại trong Docker context. Source/runtime bytes trong Git giống nhau
cho phần ứng dụng và pack, nhưng **exact commit identity vẫn NOT VERIFIED**.
Cần provider proof/Owner giải quyết mismatch hoặc Coordinator disposition trước
exact-revision acceptance. Không đổi branch, rewrite history hoặc tự chấp nhận SHA khác.

### Limits của các check đã thực hiện

- Logs chứng minh Docker build/image export/push, startup và internal health.
  `containerimage.digest` là OCI manifest digest, không phải local Docker image ID.
- Python base là 3.11-slim; exact Python patch chưa chạy `python --version` trong image.
- Direct requirements/CPU Torch không đổi; build log lưu resolved transitive versions.
- Log marker worker bị Railway gắn severity=error vì stderr; message nói workers alive,
  không có startup exception trong retrieved deploy logs. Không gọi mọi error-level row
  là lỗi runtime, cũng không tuyên bố full log sạch.
- Credential-literal/private-key-marker scan trên retrieved build/deploy messages:
  **0 findings**. Không thay thế filesystem scan hoặc PII review.
- Config prepared giữ replay/openai/gpt-6-luna/none/cache0, keyless và DB /runtime/demo.db.
  OAuth tools chỉ cho đọc variable names; actual env/path/seed readback trong container
  vẫn pending. Không phát sinh synthetic business input hay LIVE/email trong lượt theo dõi.
- DB local hash vẫn unchanged; remote DB migration/seed/reset/persistence chưa đo trực tiếp.
- Build response có 501 entries khi request limit=500; raw log là provider-limited response,
  không chứng nhận full build-log completeness.

### SSH / container verification access

User cung cấp Service Instance ID `f6d42f27-6b73-4336-a477-a4d413c1c779`.
Kết nối SSH với StrictHostKeyChecking=yes dừng ở host-key verification trước authentication.
Không hạ host verification để tiếp tục.

Kiểm tra vị trí thông thường: Windows không có .ssh/default Ed25519/RSA key,
ssh-agent stopped; Downloads/Documents/Desktop/OneDrive và hai thư mục .ssh trên F:
không tìm thấy file key theo mẫu tên đã kiểm. WSL Ubuntu-24.04 user vu không có
/home/vu/.ssh hoặc Railway CLI config. Đây là bounded search, không chứng minh mọi vị trí
trên máy đều không có key. Không đọc hoặc hiển thị private key.

Tools không có container exec. Local Railway CLI/auth cũng chưa có. Đã hỏi user chỉ ra
key hiện có hoặc cho phép tạo key riêng ngoài repository để đăng ký public key.
Theo [Railway SSH docs](https://docs.railway.com/cli/ssh), service private có thể truy cập
bằng Service Instance ID, không cần public domain. Không cài CLI, tạo key hay đăng ký
quyền SSH mới trong checkpoint này.

Raw local evidence (ignored):
`data/validation/m6-t04/20261014-1538-private-runtime.json` và
`20261014-1538-provider-build-log.json`.

### AC1–AC8 tại private deployment checkpoint

| AC | Current status |
| --- | --- |
| AC1 Deployment | PARTIAL — private online/internal health; public URL và external UI chưa có |
| AC2 Reproducibility | PARTIAL — real image digest/build PASS; commit mismatch + Python/fs scan pending |
| AC3 Fresh Clone | NOT VERIFIED |
| AC4 Data | PARTIAL — dedicated volume mounted; container DB readback/reset/recovery pending |
| AC5 Runtime | NOT VERIFIED in new image — cassette integrity host PASS, container critical replay/Verify pending |
| AC6 Sessions | NOT VERIFIED |
| AC7 Safety | PUBLIC_ACCESS_GATE_BLOCKED; image filesystem scan pending; no domain/key/LIVE/email |
| AC8 Evidence | PARTIAL — actual build/startup/health evidence recorded; acceptance evidence incomplete |

Next technical work: establish approved SSH access, inspect actual image/env/pack/DB,
then isolated critical replay/Verify and recovery. Public domain remains STOP until
access control/restricted demo policy is enforced; do not infer PUBLIC_URL_READY from SUCCESS.
Không bật billing, không merge PR #51, không tự DONE.

## SSH key registration recheck — 14/10/2026, 16:06 UTC+07

User authorized a dedicated local Ed25519 key and confirmed registration on Railway.
Private key remains outside Git; public/private match and owner-only Windows file ACL
were verified. No private-key contents were displayed or committed.

SSH server `ssh.railway.com` accepted the key and authenticated using publickey.
Initial host identity was recorded using OpenSSH `accept-new` in a dedicated local
known-hosts file; a subsequent `StrictHostKeyChecking=yes` probe matched the recorded
ED25519 key. This is first-use trust, not an independently published host fingerprint.

The authenticated probe returned `No active deployment` for supplied target
`f6d42f27-6b73-4336-a477-a4d413c1c779`; no container command executed.
Provider readback still shows deployment `c8930474-219b-4d9f-b736-2f0803888cb9`
SUCCESS, one running replica, zero crashed, no pending changes and no public domains.
The subsequent supplied ID `22f7733a-4341-41b5-b0af-a6a4ae3a08fa` was independently
identified as the personal workspace, so was not used as an SSH target.

Await the current Service Instance ID from the approved service's command palette.
Image filesystem, container replay/Verify and remote DB checks remain NOT VERIFIED.
AC1–AC8 statuses above remain unchanged; public domain remains STOP at the access gate.

## Private container acceptance — 14/10/2026, 16:19 UTC+07

**RESULT: PRIVATE_RUNTIME_PASS có giới hạn; PUBLIC_URL_NOT_READY; M6-T04 NOT DONE.**

User cung cấp Service Instance ID đúng `19c74e1f-de9a-4833-9854-a73a11f50a95`.
SSH với task key riêng, IdentitiesOnly và StrictHostKeyChecking=yes vào được container.
Actual service/environment/deployment env khớp đúng service đã duyệt, không tạo domain.

| Check trực tiếp trong container | Actual result |
| --- | --- |
| Python | 3.11.17 |
| Actual environment | replay/openai/gpt-6-luna/none/cache0; PORT=8511 |
| Runtime DB | /runtime/demo.db; SQLite quick_check=ok |
| Demo seed | 6 sources, 6 synthetic, 72 chunks, 6 original source contents; 0 cases / 0 audit events |
| Internal HTTP health | 200, body `ok` |
| API/email credential presence | OPENAI_API_KEY, ANTHROPIC_API_KEY, SMTP_PASSWORD, GMAIL_TOKEN absent; values never displayed |
| Artifact scan /app | 0 findings for .env/.env.*, DB/key/bytecode/vector-cache patterns, .git/.venv/.pytest*/secrets.toml |
| Credential-literal/private-key-marker scan | 0 findings in text files under /app, size below 2 MB; narrow automated scan, not complete PII/security certification |
| Source identity comparison | 72/72 application/config files checked match Git bytes at approved b7a0658; scope core/corpus/infra/ui/pages/policies/verify plus Dockerfile/requirements/entrypoints |
| Accepted BASE24 pack | Exactly 24 files; 24/24 SHA-256 match manifest, no extra cassette |
| Actual runtime commit environment | **61e31e8db1784fb2f387efceaaf013a45401204e**, matching deployment metadata, differing from approved b7a0658 |

The application-byte comparison supports content equivalence in the checked scope;
it does not satisfy the exact-SHA deployment requirement. No new source/build was staged.

### Real replay, Verify and human resume

Fresh temporary DB under `/tmp`, configured before infra/corpus imports; live DEMO DB
was read-only during the probe. Socket connect/connect_ex/sendto/DNS and `_call_live`
were denied; `_load_cache` was denied by the existing audit observer. No cassette bytes,
business functions, schema, policy or expected Verify labels were changed.

| Flow | Actual result | Replay hits |
| --- | --- | --- |
| DEV_ROUTINE | AUTO_REPLY / PENDING_SEND | 3 |
| DEV_AUTHORITY | ESCALATE / AUTHORITY_REQUIRED / AWAITING_HUMAN | 4 |
| DEV_FACT | ESCALATE / FACT_UNRESOLVED / AWAITING_HUMAN | 4 |
| Verify V01–V04 | 4/4 semantic matches; V04 supplies OUT_OF_POLICY critical path | 12 |
| DEV_HUMAN_R11 | Real AppTest decision + worker; PENDING_APPROVAL, 1 draft, job state `done` | 1 |

Critical decision paths AUTO_REPLY/AUTHORITY_REQUIRED/FACT_UNRESOLVED/OUT_OF_POLICY:
4/4 observed. Total replay **24/24 hit, 0 miss, LIVE=0**. Eight observed flows persisted
to the isolated DB, SQLite quick_check=ok. DEMO DB before/after hash unchanged:
`57560fde0eae79f68974325ccda8d33185f02efc6af9b0f4023963cd89ba8561`;
still 0 cases / 0 audit events and 6/6 synthetic sources. Temp DB removed afterward.

Probe corrections are disclosed: the initial scratch seed assertion used wrong dataclass
fields, then assumed seed insertion happened after corpus import (corpus.__init__ seeds
on import). The existing audit human helper also assumed its case was already selected;
the current UI shows a selected case. The task-local probe explicitly selected the actual
human case via `selected_case_id_select` before its real decision widgets. A scratch
assertion initially expected uppercase DONE, while core/worker.py stores lowercase `done`;
the pre-correction JSON is retained. Only the validation driver was corrected, then the
complete probe reran; no production code or response was substituted to obtain PASS.

### Isolated volume data checks

A newly created `m6-t04-validation-*` directory under the approved `/runtime` volume
held disposable synthetic test databases. Seed initialized to 6 synthetic sources/72
chunks. A synthetic settings marker survived reopening in a separate Python process;
SQLite backup and restore to a new path preserved the marker and corpus. A separate
fresh DB had no marker/cases and seed remained idempotent. All assertions PASS.
The exact temporary directory was removed; live DEMO DB hash remained unchanged.
**Service restart/volume persistence across container replacement and live DEMO reset
remain NOT RUN**; process reopening is not evidence for those gates.

Raw evidence retained locally under ignored `data/validation/m6-t04/`:
`20261014-container-readback.json`, `20261014-container-source-check.json`,
`20261014-container-runtime.json`, `20261014-container-runtime.stderr.log`,
`20261014-container-runtime-before-assertion-correction.json`,
`container_runtime_probe.py`, `20261014-container-recovery.json`.
No private key, credential or DB is committed. Local data/app.db remains unchanged.

### Updated AC1–AC8 and handoff

| AC | Current status |
| --- | --- |
| AC1 Deployment | PARTIAL — private SUCCESS/health 200; public HTTPS/external browser/uptime acceptance missing |
| AC2 Reproducibility | PARTIAL — real image/source/pack scan and Python measured; exact deployed SHA mismatches approval |
| AC3 Fresh Clone | NOT VERIFIED — independent reviewer run remains pending |
| AC4 Data | PARTIAL — actual isolated DEMO seed + disposable reopen/backup/restore PASS; service restart/reset gate pending |
| AC5 Runtime | PASS in observed private scope — critical 4/4, Verify 4/4, human R11, 24/24 replay hit, LIVE 0 |
| AC6 Sessions | NOT VERIFIED — AppTest is not 2–3 independent browser sessions |
| AC7 Safety | PARTIAL / PUBLIC_ACCESS_GATE_BLOCKED — artifact scan/keyless replay/data isolation PASS; anonymous privileged intake still unsafe |
| AC8 Evidence | PARTIAL — actual container evidence/report/PR updated; final acceptance evidence incomplete |

Coordinator/Reviewer next actions: resolve exact-SHA disposition and select an authorized
access-control or restricted-demo revision before public exposure. Then verify the new
accepted deployment/domain from an external browser, real independent sessions, and
remaining restart/reset/fresh-clone gates. Current public URL: **none**.
No paid billing, LIVE/email, merge of PR #51 or DONE action was performed.
