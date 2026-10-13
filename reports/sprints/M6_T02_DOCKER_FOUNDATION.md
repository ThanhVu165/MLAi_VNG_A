# M6-T02 — Nền tảng Docker và cách ly môi trường

## Correction F01–F04 — 2026-10-14

### Metadata

- Task ID: `M6-T02`
- Executor: Project Coordinator trực tiếp thực hiện correction thay Owner
- Owner ghi nhận: Nam — QA/Hạ tầng; reviewer cuối: Vũ — Runtime/Persistence
- Branch: `sprint/m6-t02-docker-foundation`
- Starting SHA: `6126811c965341a615de9dfb26c8717dc06e65dd`
- Tested state/provenance: working tree correction dựa trên
  `6126811c965341a615de9dfb26c8717dc06e65dd`; image runtime
  `sha256:07f9280f84d38ea25c425683e63b9dfd983de29a3e024cea401fd0a91d32c9fc`.
  Final commit SHA được xác minh trong handoff sau commit/push.
- Target: `dev`; `origin/dev` tại preflight: `9dfb33494cbf28e05651508ecfed145e5cc70fe7`
- PR: [#45](https://github.com/ThanhVu165/MLAi_VNG_A/pull/45)
- Environment: Windows, Docker Desktop Linux containers; Engine `29.1.3`; Compose `v2.40.3-desktop.1`
- LIVE/API calls: `0`

Preflight bắt đầu với branch đúng, HEAD đúng và working tree sạch. Không checkout,
worktree, clone, merge hoặc rebase. Không thay đổi cassette/manifest M6-T05.

### Implementation mapping

| Finding | Implementation |
| --- | --- |
| F01 — Safe Reset Guard | Thêm `scripts/m6_t02_safe_reset.py`. Guard chỉ nhận `exodia-m6t02-validation` hoặc suffix rõ ràng, tìm volume bằng label Compose project chính xác, inspect toàn bộ label trước khi gọi scoped `docker compose --project-name ... down --volumes`. Guard fail trước bước xóa. Không wildcard/prune. |
| F02 — Background Worker Evidence | `core/worker.py` ghi startup marker không chứa PII/secret sau khi hai daemon thread `email-processing` và `email-dispatch` đã start và còn alive. Không đổi loop, business logic hoặc public interface. |
| F03 — Validation Traceability | Section correction này ghi exact command, environment, PASS/FAIL/SKIP/NOT RUN, AC mapping, self-review và phân biệt evidence cũ/mới. |
| F04 — Validation Port Conflict | `compose.yaml` cho override `DEV_HOST_PORT`, `STUDY_HOST_PORT`, `DEMO_HOST_PORT`; default vẫn `8511`, `8512`, `8513`, container port vẫn `8511`. |

### Validation correction

| Command | Purpose | Environment | Result | Important output/evidence |
| --- | --- | --- | --- | --- |
| `git branch --show-current; git rev-parse HEAD; git status --short --branch` | Preflight contract | Host | PASS | Branch `sprint/m6-t02-docker-foundation`; HEAD `6126811c...`; clean at start. |
| `git fetch origin --prune` | Refresh baseline | Host | PASS | `origin/dev=9dfb33494cbf28e05651508ecfed145e5cc70fe7`; task remote remains `6126811c...`. |
| `docker version; docker compose version` | Runtime preflight | Docker Desktop Linux | PASS | Client/server `29.1.3`; Compose `v2.40.3-desktop.1`. |
| `docker compose config` | Default DEV config | Host/Compose | PASS | `127.0.0.1:8511 -> 8511`. |
| `docker compose --profile study config` | Default STUDY config | Host/Compose | PASS | `127.0.0.1:8512 -> 8511`. |
| `docker compose --profile demo config` | Default DEMO config | Host/Compose | PASS | `127.0.0.1:8513 -> 8511`. |
| `$env:DEV_HOST_PORT='18511'; docker compose config` | F04 override resolution | Host/Compose | PASS | `127.0.0.1:18511 -> 8511`. |
| `python -m py_compile core/worker.py scripts/m6_t02_safe_reset.py` | Syntax | Host/Python 3.11 | PASS | Exit `0`. |
| `docker compose --project-name exodia-m6t02-validation-correction build dev` | Build corrected image | Docker Desktop Linux | PASS | Image `exodia:m6-t02`; manifest/image ID `sha256:07f9280f...`. |
| `$env:DEV_HOST_PORT='18511'; docker compose --project-name exodia-m6t02-validation-correction up -d --no-build dev` | F04 runtime on non-conflicting port | Docker Desktop Linux | PASS | `127.0.0.1:18511->8511`; container reached `healthy`. |
| `Invoke-WebRequest http://127.0.0.1:18511/_stcore/health` | F04 overridden-port health | Host loopback | PASS | HTTP `200`, body `ok`. |
| `docker logs exodia-m6t02-validation-correction-dev-1` | F02 worker startup | Docker container | PASS | `Background workers started and alive: email-processing, email-dispatch`. |
| `docker exec ... python -c "... glob('/proc/1/task/*') ..."` | F02 alive after startup | Docker container | PASS | PID 1 had `13` tasks while container was `running=true`, `health=healthy`; Python `3.11.17`. |
| `docker volume inspect ... --format ...` | F01 exact ownership | Docker Desktop Linux | PASS | Target/control volumes each had exact `com.docker.compose.project` and `com.docker.compose.volume=dev_data` labels. |
| `python scripts/m6_t02_safe_reset.py mlai_vng_a` | F01 invalid target, resources preserved | Host + Docker | PASS | Exit `2`; target remained running, control remained created, both volumes unchanged. |
| `python scripts/m6_t02_safe_reset.py exodia-m6t02-validation-correction` | F01 valid scoped reset | Host + Docker | PASS | Guard listed exact target volume, removed target container/network/volume; control container/volume remained. |
| `python scripts/m6_t02_safe_reset.py exodia-m6t02-validation-control` | Cleanup disposable control | Host + Docker | PASS | Removed only control resources; pre-existing containers/volumes remained present. |
| `docker run --rm --entrypoint python exodia:m6-t02 -m black --check --line-length 100 scripts/m6_t02_safe_reset.py` | Format script mới | Corrected image | PASS | `1 file would be left unchanged`. Không mass-format toàn bộ worker legacy ngoài scope. |
| `docker run --rm --entrypoint python exodia:m6-t02 -m ruff check core/worker.py scripts/m6_t02_safe_reset.py` | Targeted lint | Corrected image | PASS | `All checks passed!` |
| `docker run --rm --mount type=bind,source=<tests>,target=/app/tests,readonly ... -m pytest tests/test_runtime_worker.py -q` | Targeted worker regression | Corrected image + tests read-only | PASS | `34 passed in 12.79s`. |
| `git diff --check` | Whitespace/self-review | Host | PASS | Không có output. |

Không validation nào gọi LIVE/provider/API. Không dùng global prune.

### AC mapping correction

| AC | Status | Evidence classification |
| --- | --- | --- |
| AC1 — build/Python 3.11 | PASS — NEWLY RERUN | Corrected image build PASS; runtime trả `Python 3.11.17`. |
| AC2 — startup/health/worker | PASS — NEWLY PROVEN | Overridden-port container healthy; worker marker có hai thread alive; PID 1 còn 13 tasks sau startup. |
| AC3 — isolation | RETAINED PREVIOUS | Mount, database path, network, profiles không đổi. |
| AC4 — persistence | RETAINED PREVIOUS | Volume/persistence behavior không đổi. |
| AC5 — safe reset | PASS — NEWLY PROVEN | Invalid target không xóa gì; valid guard xóa đúng target; control và resources có sẵn được giữ. |
| AC6 — safety/replay/no LIVE | PASS — RERUN/RETAINED | Loopback, replay, zero LIVE/API; không credential/public deployment/prune. |
| AC7 — reproducibility | PASS — NEWLY RERUN | Default/profile/override config, build, health, reset guard và runbook đều được kiểm chứng. |

Evidence chức năng cũ về isolation và persistence bên dưới được giữ nguyên, không gắn
nhãn thành test mới. Correction run này chứng minh mới F01 safe reset, F02 worker runtime
và F04 overridden-port health; không chạy lại isolation/persistence vì source liên quan
không đổi.

### Correction self-review and disposition

- Full diff: PASS; đã review toàn bộ tracked diff và script mới sau evidence update.
- Scope: `compose.yaml`, permitted instrumentation in `core/worker.py`,
  `scripts/m6_t02_safe_reset.py`, runbook and this report.
- Sensitive-data/credential scan: PASS; không phát hiện credential-like value trong 5 file.
- M6-T05 cassette/manifest, SQLite schema, routing/policy/approval/audit semantics: unchanged.
- Public deployment: none; bindings remain loopback-only. LIVE/API: `0`.
- Disposition: F01–F04 và self-review PASS; đủ điều kiện commit/push để chuyển
  `READY_FOR_VU_FINAL_REVIEW`.

## Thông tin task và baseline

- Chủ sở hữu: Nam — QA/Hạ tầng
- Người duyệt cuối: Vũ — Runtime/Persistence
- Repository: `ThanhVu165/MLAi_VNG_A`
- Baseline: `ffb7f79f827172537d731528394173f4ce4f8551` (`origin/dev`)
- Nguồn đã kiểm chứng: working tree của nhánh task, bắt đầu từ commit `e4fdef84be461092fad51296af4748ab81844924` và bao gồm bản sửa cuối cho việc publish cổng loopback của Compose.
- Nhánh task: `sprint/m6-t02-docker-foundation`
- Commit triển khai: `d008a2e57d3f00147ae74992258b03947a6c5385` — `deploy(m6-t02): thiết lập Docker foundation`
- PR: [#45 — M6-T02 Docker Foundation & Environment Isolation](https://github.com/ThanhVu165/MLAi_VNG_A/pull/45), đích `dev`
- Lời gọi LIVE/API: `0`

## Preflight

Trạng thái khi bắt đầu triển khai: `STARTABLE`.

- Thẻ Trello M6-T02 ở trạng thái `IN PROGRESS`, ghi Nam là Owner và Vũ là người duyệt cuối.
- `dev` cục bộ, `origin/dev` và baseline đã cùng trỏ đến `ffb7f79f827172537d731528394173f4ce4f8551` trước khi tạo nhánh task.
- Docker Desktop Engine khả dụng, phiên bản Docker `29.8.2`.
- Chưa có `Dockerfile`, `.dockerignore`, `compose.yaml`, nhánh task hay PR M6-T02 nào trước đó.
- Đã đọc bằng chứng M3-T03 và M6-T01. Cả hai chỉ là audit tĩnh và chưa xác nhận Docker/cách ly ở runtime; M6-T02 không kế thừa trạng thái runtime PASS từ các task này.
- M6-T05 vẫn thuộc quyền sở hữu của Minh. Task này không thay đổi cassette hoặc replay manifest.

## Tệp được thay đổi

- `Dockerfile`
- `.dockerignore`
- `compose.yaml`
- `docs/deploy/M6_T02_RUNBOOK.md`
- `reports/sprints/M6_T02_DOCKER_FOUNDATION.md`

## Thiết kế triển khai

- Image sử dụng Python 3.11 và khởi chạy entrypoint hiện hữu `run_local.py`, do đó vẫn giữ bước seed dữ liệu và khởi động background worker.
- Repository không pin `torch`; Docker image cài CPU wheel đã pin (`2.5.1+cpu`) trước requirements hiện có, tránh tải CUDA runtime trong container không dùng GPU.
- DEV là service Compose mặc định. STUDY và DEMO là profile bật thêm; mỗi môi trường có named volume riêng và chỉ bind host port vào loopback.
- Database runtime luôn là `/runtime/app.db`. `LLM_MODE=replay` và cache bị tắt để smoke test không đi theo luồng gọi live provider. Không có API key trong image hoặc Compose.
- Reset có tính phá hủy chỉ được phép với Compose project validation có tên riêng. Volume DEV/STUDY/DEMO thông thường được giữ nguyên.

## Tiêu chí chấp nhận và bằng chứng kiểm thử

Validation sử dụng Docker Desktop `29.8.2`, image `sha256:ad4144ddbc644102357e4d2f7f688e31999e0e2e7735025ea09812c6e51af8b3` (2,60 GB) và Compose project tạm `exodia-m6t02-validation`.

| Tiêu chí | Kết quả | Bằng chứng |
| --- | --- | --- |
| AC1 — build image / Python 3.11 | PASS | `docker compose build` hoàn tất trong 5 phút 57 giây; `docker run --rm exodia:m6-t02 python --version` trả về `Python 3.11.17`. |
| AC2 — khởi động / health / worker | PASS | DEV/STUDY/DEMO đều ở trạng thái `healthy`; health endpoint host `127.0.0.1:8511`, `:8512`, `:8513` đều trả `ok`. Lệnh PID 1 là `python run_local.py --server.address 0.0.0.0 --server.port 8511`, giữ entrypoint gọi `start_worker()` trước Streamlit. |
| AC3 — cách ly | PASS | Chỉ DEV được chèn dòng dữ liệu giả `m6_t02_probe`. Kiểm tra metadata SQLite ở STUDY và DEMO xác nhận bảng probe không tồn tại. |
| AC4 — persistence | PASS | Restart container DEV xong vẫn đọc được dòng dữ liệu giả từ named volume của DEV. |
| AC5 — seed/reset an toàn | PASS | Startup tạo các bảng schema ứng dụng mong đợi. Chỉ ba volume tạm `exodia-m6t02-validation_{dev,study,demo}_data` bị xóa bằng `down --volumes`; lệnh liệt kê volume sau đó rỗng. |
| AC6 — an toàn | PASS | Chỉ bind loopback, Compose ép replay mode và không thêm API key, log chỉ có Streamlit startup cục bộ; kiểm tra image/config không phát hiện credential literal. Lời gọi LIVE/API: `0`. |
| AC7 — tái lập | PASS | `docker compose config`, `docker compose --profile study config` và `docker compose --profile demo config` đều pass trước khi chạy disposable project thành công. Runbook ghi lại các lệnh tương tự và ranh giới reset an toàn. |

## Giới hạn và phụ thuộc đã biết

- M6-T02 không xác nhận business E2E, acceptance trên fresh clone, public deployment, replay coverage hoặc bất kỳ milestone gate nào.
- Cassette replay bị thiếu thuộc phạm vi M6-T05 và không được xử lý trong nhánh này.
- Cần Coordinator chấp nhận và Vũ review cuối trước khi task có thể được đánh dấu DONE.

## Commit và Pull Request

- Branch đã được push: `sprint/m6-t02-docker-foundation`.
- Pull Request: [#45](https://github.com/ThanhVu165/MLAi_VNG_A/pull/45), đích `dev`.
- Sau khi `dev` có thêm commit tài liệu `1251c3c`, nhánh task đã merge commit này bằng merge thông thường (không force-push) trước khi tạo PR.
