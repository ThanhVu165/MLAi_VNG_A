# README refresh — 16/10/2026

- Phạm vi: tài liệu giới thiệu dự án; không đổi hành vi ứng dụng.
- Người thực hiện: Codex theo yêu cầu trực tiếp của người dùng.
- Authorization: “Sửa readme lại vì readme kia đã cũ và không thể hiện đc dự án của chúng tôi”.
- Không tự gán Task ID hoặc tuyên bố Coordinator acceptance.
- Baseline local `dev` và ref `origin/dev` tại lúc kiểm tra:
  `4914f893756b3f7e52819538387625fdb1b02653`.
- Branch làm việc: `codex/readme-project-overview`.
- Trạng thái bàn giao: `READY_FOR_REVIEW`; chưa commit/push/merge.

## Thay đổi

Viết lại `README.md` để giới thiệu Exodia / Escalation Referee, bài toán email
sinh viên, ba nhóm nghiệp vụ, sơ đồ xử lý, vai trò của chuyên viên, các chế độ
chạy, kiến trúc và cách chạy demo replay không cần API key. Bỏ đoạn trạng thái
M3 cũ ở đầu README; chỉ rõ ngày checkpoint của `STATUS.md` khi dẫn chiếu.

Đối chiếu với `PROJECT_SPEC.md`, entrypoint, policy, cấu hình mẫu, kiểm soát demo,
adapter replay và RUNBOOK tại baseline. Số liệu dẫn từ báo cáo M1, Set A và Judge
LIVE smoke; ghi rõ đây là kết quả được báo cáo tại các phiên bản lịch sử.
Không truy cập dữ liệu Gold riêng hoặc suy diễn hiệu quả nghiên cứu người dùng.

## Validation

- PASS: kiểm tra chỉ đọc bằng Python trong `.venv`, đọc UTF-8/NFC, cân bằng code
  fence, số cột bảng Markdown và 20 liên kết nội bộ đều có đích tồn tại.
- PASS: block cấu hình có cùng tập biến với `.env.example`; các giá trị giữ nguyên
  ngoại trừ điền model replay `gpt-6-luna`. API key trống, replay, hai Judge switch tắt.
- PASS: phiên bản Python tài liệu khớp `.python-version`; quét mẫu API key và đường
  dẫn máy cá nhân trong README không có kết quả.
- PASS: `git diff --check`; self-review toàn bộ diff README.
- NOT RUN: cài lại dependencies, khởi động app/browser, full suite, Docker và LIVE/API.
  Đây là thay đổi tài liệu; kiểm tra trên không xác nhận runtime hoặc deployment.

## Phạm vi dữ liệu và giới hạn

Chỉ sửa README và thêm báo cáo này. Giữ nguyên file có sẵn chưa được Git theo dõi
`data/uiux-local.db`; không đọc/ghi DB, sửa `.env`, gọi provider hoặc thay cấu hình
deployment. LIVE/API trong công việc này: **0**. Không thay milestone acceptance.
