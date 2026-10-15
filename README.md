# Escalation Referee

Trợ lý tiếp nhận và xử lý email hành chính của sinh viên. LLM, quy định, quyết định,
phê duyệt và lưu trữ chạy thật; hộp thư ngoài chưa kết nối, gửi email đang mô phỏng.

**Trạng thái Sprint 2:** M1 `CLOSED`; M2 `M2_CONDITIONAL_CLOSEOUT`; M3
`M3_AUTHORIZED_WITH_CARRYOVER`. Trạng thái và giới hạn chi tiết nằm trong
[STATUS.md](STATUS.md). Việc M3 được phép bắt đầu không đổi verdict M2 thành PASS.

Thành viên mới đọc [TEAM_HANDOFF.md](docs/TEAM_HANDOFF.md) và
[TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md) trước khi nhận Task Contract trên Trello.

## Cài đặt

Python **3.11** là phiên bản chuẩn; `.python-version` là nguồn khai báo phiên bản.
Dependencies giữ nguyên trong `requirements.txt`. Cài Python 3.11 kèm Windows `py`
launcher trước, rồi chạy từ thư mục repo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
.\.venv-bootstrap\Scripts\Activate.ps1
python --version
```

Script tạo venv riêng `.venv-bootstrap`, kiểm tra đúng Python 3.11 và cài các
requirements đã pin; không sửa `.venv` cũ. Dependencies gián tiếp chưa có lock file.
Trên Linux/macOS:

```bash
python3.11 -m venv .venv-bootstrap
source .venv-bootstrap/bin/activate
python -m pip install -r requirements.txt
```

Tạo `.env` từ `.env.example`, rồi cấu hình `OPENAI_API_KEY` riêng trên máy,
`LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-6-luna` và
`OPENAI_REASONING_EFFORT=none` để chạy ứng dụng. OpenAI là provider duy nhất;
provider khác bị từ chối, không có fallback. Chế độ
`replay` chỉ dùng khi kho đã có cassette được ghi bằng `LLM_MODE=record`; không dùng
replay cho demo sạch nếu chưa có cassette.
Các lệnh kiểm tra nằm trong RUNBOOK; chọn phạm vi validation theo Task Contract.
LIVE/API chỉ được chạy khi Project Coordinator cấp quyền cụ thể.

## Chạy local

```powershell
python run_local.py --server.address 127.0.0.1
```

Giữ tiến trình này chạy để xử lý và gửi mô phỏng trong nền, kể cả khi đóng tab.
Hướng dẫn vận hành, sao lưu và kiểm chứng: [RUNBOOK.md](docs/RUNBOOK.md).
Không coi kiểm thử offline xanh là bằng chứng mô hình live đã trả lời đúng.
