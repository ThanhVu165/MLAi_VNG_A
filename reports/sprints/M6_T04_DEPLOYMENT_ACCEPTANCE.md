# M6-T04 — Nghiệm thu triển khai và khả năng tái lập

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
