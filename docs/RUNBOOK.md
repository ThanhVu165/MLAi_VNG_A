# Vận hành local — Sprint 1A

> Trạng thái bàn giao mã ngày 22/09/2026: tái cấu trúc trước, nghiệm thu sau theo yêu cầu người dùng.
> Không chạy thêm test, kiểm tra định dạng/kiểu dữ liệu, LLM live hay thao tác E2E trong đợt chốt mã này.
> Các lệnh ở mục Kiểm chứng dành cho giai đoạn tiếp theo, không phải kết quả đã đạt.

## Khởi động

Python 3.11, các thư viện trong `requirements.txt`, Streamlit và SQLite hiện có.
Tạo `.env` theo `.env.example`; điền `GOOGLE_API_KEY` riêng trên máy, không đưa vào Git.
Giữ `GEMINI_MODEL=gemini-3.5-flash-lite` theo lựa chọn của người dùng.

```powershell
cd F:\PLSRUN\MLAi_VNG_A
py -3.11 -m pip install -r requirements.txt
py -3.11 run_local.py --server.address 127.0.0.1 --server.port 8511
```

Mở `http://127.0.0.1:8511`. Đây là ứng dụng local, không có xác thực phân quyền tài khoản;
không mở cổng public hoặc đưa dữ liệu sinh viên thật vào bản kiểm chứng này.
Không cần cài thêm hàng đợi hoặc dịch vụ nền: hai luồng trong tiến trình ứng dụng xử lý
email và gửi mô phỏng. Tiến trình phải còn chạy; đóng tab không làm dừng công việc.
Trình khởi động bật các luồng xử lý trước máy chủ web: khởi động lại không cần mở tab để tiếp tục công việc.
Chạy trực tiếp bằng lệnh `streamlit run` vẫn được nhưng chỉ bật luồng nền khi có phiên giao diện đầu tiên;
không dùng cách này khi kiểm chứng xử lý độc lập trình duyệt.

## Công việc hàng ngày

1. **Email:** nhập nguyên người gửi, tiêu đề, nội dung; thời điểm tiếp nhận được lưu.
   Bấm xử lý để lưu công việc trước. Có thể đổi trang hoặc tải lại để xem trạng thái.
2. **Cần chuyên viên xử lý:** đọc câu hỏi, dữ kiện, căn cứ; ghi quyết định và lý do cụ thể.
   Quyết định và yêu cầu soạn được lưu cùng giao dịch. AI diễn đạt lại trong nền, không cần giữ trang mở.
   Đọc bản phản hồi rồi bấm duyệt; sửa nội dung phải lưu và kiểm tra trước.
3. **Quy định:** nạp văn bản, đọc bản gốc/điều khoản, kiểm tra thông tin AI đề xuất,
   xác nhận nguồn, hiệu lực và phạm vi rồi đưa vào sử dụng. Không gán quyền cho từng đoạn.
4. **Lịch sử xử lý:** chọn email theo tiêu đề/thời điểm; xem ai làm gì và vì sao.
   Tải dữ liệu kiểm tra khi cần mã máy và toàn bộ chi tiết.
5. **Kiểm tra hệ thống:** chạy bộ tình huống đã duyệt qua cùng `process_case()`.

Phản hồi tự động có khoảng chờ 60 giây. Có thể hủy hoặc chuyển chuyên viên trong thời gian chờ.
Tạm dừng gửi ở thanh bên giữ nguyên thư đã chuẩn bị; chuyên viên vẫn có thể duyệt gửi chủ động.
Nguồn thay đổi hoặc hết hiệu lực trước khi gửi sẽ buộc đối chiếu lại, không gửi theo nguồn cũ.
Một email từ hộp thư có cùng mã bên ngoài chỉ được tiếp nhận một lần. Thử lại tạo lần xử lý
mới liên kết với lần cũ, không ghi đè lịch sử và không tự gửi lại email đã gửi.
Bấm chạy lại nhiều lần từ cùng email cũ chỉ mở lần chạy mới đã tạo; nếu lần đó vẫn lỗi,
hãy bấm thử lại trên chính lần chạy mới. Quyết định của chuyên viên không cần nhập lại khi chỉ lỗi soạn thư.

## Khi có lỗi

- **Chưa xử lý được:** lỗi dịch vụ hoặc xử lý kỹ thuật, không phải chuyển chuyên viên nghiệp vụ.
  Kiểm tra kết nối/cấu hình rồi bấm thử lại. Không có câu trả lời giả được gửi.
- **Dịch vụ quá tải / hết thời gian:** thử lại tối đa một lần cho lỗi tạm thời, tối đa bốn
  lần gọi dịch vụ trong một lượt xử lý và ngân sách chờ 60 giây. Hạn mức API phụ thuộc dự án;
  không tự đổi mô hình khi quá tải. Không có lịch thử lại vô hạn.
- **Đã có quyết định nhưng chưa có phản hồi:** quyết định người được giữ trong hàng chờ;
  bấm thử soạn lại khi dịch vụ phục hồi, không nhập quyết định lần nữa.
- **Tiến trình bị ngắt:** công việc chưa bắt đầu được tiếp tục sau khi mở ứng dụng;
  công việc đã chạy nhưng không kết thúc được đánh lỗi sau khi hết hạn giữ công việc 120 giây.
  Nếu đã có quyết định của chuyên viên, giữ quyết định đó và chỉ đánh lỗi công việc soạn thư.
- **Không đọc được tài liệu:** bản gốc vẫn được giữ, nguồn chưa được sử dụng; thay bằng tệp đọc được.
- **Nguồn cũ thiếu bản gốc:** UI báo rõ. Không tự lấy nội dung seed mới gắn vào nguồn cũ nếu mã kiểm tra nội dung không khớp.

## Dữ liệu và sao lưu

Mặc định `data/app.db`; có thể đặt `DATABASE_PATH` để kiểm chứng bằng DB riêng.
Schema phiên bản 2 bổ sung bản gốc nguồn, kết quả xử lý, công việc nền và mã email ngoài.
Giao dịch duyệt/kích hoạt/thay thế/khôi phục nguồn bao gồm nội dung, trạng thái, mâu thuẫn,
phiên bản và nhật ký; lỗi ở giữa phải hoàn tác cả giao dịch. Không giữ khóa dữ liệu khi gọi AI.
DB cũ được sao lưu bằng SQLite Backup API vào thư mục `backups/` cạnh DB trước khi nâng cấp.
Không xóa DB hoặc khởi tạo đè để sửa lỗi. File bản sao lưu không chứa các thao tác phát sinh sau thời điểm nâng cấp.
Muốn phục hồi: dừng ứng dụng, giữ lại DB hiện tại cùng các file WAL/SHM, sao chép bản sao lưu
thành một **đường dẫn mới**, đặt `DATABASE_PATH` trỏ đến bản đó rồi kiểm tra trước khi dùng.

## Kiểm chứng — thực hiện sau khi hoàn tất tái cấu trúc

```powershell
py -3.11 -m black --check --line-length 100 .
py -3.11 -m ruff check .
py -3.11 -m mypy --ignore-missing-imports .
$env:LLM_MODE='replay'
py -3.11 -m pytest -q
```

Kiểm thử offline thay dịch vụ AI ở ranh giới hoặc dùng dữ liệu cố định để phát hiện lỗi lặp lại.
Chúng không chứng minh LLM live đúng. Để kiểm tra live bằng DB riêng:

```powershell
$env:DATABASE_PATH='data/validation/manual-live.db'
$env:LLM_MODE='live'
$env:LLM_CACHE='0'
$env:GEMINI_MODEL='gemini-3.5-flash-lite'
$env:PYTHONIOENCODING='utf-8'
py -3.11 -c "from corpus.seed import ensure_seeded; ensure_seeded()"
py -3.11 -m verify.harness --set full15 --output data/validation/full15.json
py -3.11 -m verify.harness --set escalation5 --output data/validation/escalation5.json
```

Phải đối chiếu quyết định, loại chuyển tiếp, quy tắc, trích dẫn, câu hỏi và thời gian.
Bộ năm tình huống chỉ đạt khi ba tự động, hai chuyển tiếp đúng và toàn bộ chạy không quá 90 giây.
Thêm năm email mới và một nguồn mới ngoài seed; kiểm tra câu trả lời thay đổi phù hợp sau khi nguồn được duyệt.
Nếu API quá tải hoặc một điều kiện chưa đạt, ghi **chưa đạt**, không dùng cache hoặc đổi kỳ vọng để làm xanh.
Lượt E2E tiếp theo phải dùng đúng bản mã đã chốt, lưu mã commit, cấu hình không chứa bí mật,
đường dẫn DB kiểm tra, thời điểm, đầu vào mới, trạng thái cuối và căn cứ quan sát được.
Phải thử hủy, tạm dừng, duyệt/sửa, chuyển trang, tải lại và khởi động lại; không chỉ chạy harness.

## Giới hạn đã chủ động giữ

- Nhận thư ngoài và gửi qua nhà cung cấp email chưa tích hợp; gửi hiện là ghi nhận mô phỏng trong SQLite.
- Corpus nhỏ được lọc theo nhóm/hiệu lực rồi LLM chọn căn cứ. Chưa tối ưu cho kho hàng nghìn văn bản;
  cần giới hạn ngữ cảnh/tìm kiếm nhiều tầng trước khi mở rộng quy mô.
- Chưa phát hành public, chưa xác thực người dùng, chưa có dịch vụ giám sát tiến trình của hệ điều hành.
- URL nhập tài liệu không mở trên UI; dùng dán nội dung hoặc tệp. Không coi kiểm tra URL backend là chống DNS rebinding đầy đủ.
