# Escalation Referee

Trợ lý tiếp nhận và xử lý email hành chính của sinh viên. LLM, quy định, quyết định,
phê duyệt và lưu trữ chạy thật; hộp thư ngoài chưa kết nối, gửi email đang mô phỏng.

**Trạng thái:** đã ghép phần mã tái cấu trúc, chưa nghiệm thu Sprint 1A.
Theo yêu cầu mới nhất, hoàn tất tái cấu trúc trước rồi mới kiểm thử end-to-end;
không lấy kết quả kiểm tra trước đợt sửa làm chứng nhận cho mã hiện tại.

## Cài đặt

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

Tạo `.env` từ `.env.example`, rồi điền `GOOGLE_API_KEY` để chạy ứng dụng. Chế độ
`replay` chỉ dùng khi kho đã có cassette được ghi bằng `LLM_MODE=record`; không dùng
replay cho demo sạch nếu chưa có cassette.
Các lệnh kiểm tra được tách sang RUNBOOK để chạy ở giai đoạn nghiệm thu sau tái cấu trúc.

## Chạy local

```powershell
py -3.11 run_local.py --server.address 127.0.0.1
```

Giữ tiến trình này chạy để xử lý và gửi mô phỏng trong nền, kể cả khi đóng tab.
Hướng dẫn vận hành, sao lưu và kiểm chứng: [RUNBOOK.md](docs/RUNBOOK.md).
Không coi kiểm thử offline xanh là bằng chứng mô hình live đã trả lời đúng.
