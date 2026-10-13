# M6-T02 — Nền tảng Docker và cách ly môi trường

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
