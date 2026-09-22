# Nhật ký tái cấu trúc — Sprint 1A

## 22/09/2026 — phạm vi đã duyệt

Giữ Streamlit, SQLite, Gemini và ba nhóm nghiệp vụ. Tiếp nhận nguyên email bằng biểu mẫu;
chưa tích hợp hộp thư ngoài và thao tác gửi ra ngoài. Không có câu trả lời chuẩn bị sẵn trong luồng vận hành.
Mốc kế hoạch đã ghi ở commit `cec2fb2`; các thay đổi triển khai sau mốc này chưa commit hoàn tất.

## Những nhóm mã đã thay đổi

- Runtime: LLM đọc tiêu đề/nội dung, chọn điều khoản đang hiệu lực theo từng yêu cầu,
  trả lời từ email + dữ kiện + căn cứ. Nhãn đoạn cũ không cấp quyền trả lời.
  Lỗi kỹ thuật không tự biến thành thiếu dữ kiện; retry hữu hạn, giữ email để chạy lại.
- Công việc: nhận email và lưu job cùng giao dịch, kết quả có ảnh chụp căn cứ;
  xử lý lại giữ lịch sử, không tạo nhiều lần chạy từ cùng một nút bấm lặp.
  Quyết định chuyên viên và yêu cầu soạn lưu trước, worker diễn đạt trong nền, người duyệt gửi sau.
- Quy định: lưu bản gốc, trích xuất, chia theo cấu trúc thực, đề xuất và duyệt ở cấp nguồn.
  Kích hoạt/thay thế/khôi phục và phát hiện mâu thuẫn được gom giao dịch.
  Giữ nguyên ý nghĩa sáu seed và kỳ vọng 15 tình huống; không ghi đè nguồn đã duyệt bằng seed mới.
- Hạ tầng/UI: migration SQLite v2 có sao lưu; năm mục tiếng Việt, thời gian Việt Nam,
  giây xử lý, lời giải thích và việc cần làm tiếp. Trạng thái gửi đọc từ DB;
  giữ 60 giây hủy và chống ghi đè email đã gửi khi thao tác đồng thời.
- Verify: dùng cùng process_case; so cả quyết định, loại chuyển tiếp, quy tắc và căn cứ,
  không cho qua chỉ vì cùng loại chuyển tiếp. Có tập năm email mới và xuất báo cáo.

## Bằng chứng có trước yêu cầu dừng kiểm thử

Baseline trước tái cấu trúc: 94 pytest passed. Một lượt toàn bộ trung gian có 118 passed,
1 lỗi UI; sau đó sửa tiếp nên không được dùng số đó để gọi bản cuối xanh.
Giao diện từng ghi nhận email ngắn đúng đầu vào và hiển thị lỗi dịch vụ riêng, không chuyển chuyên viên giả.
Gemini live gặp quá tải/hết thời gian: full15 từng có 2/15 đạt (hai chốt không cần LLM),
năm email mới 0/5; lượt escalation bị dừng trước khi hoàn tất. Chưa có bằng chứng đáp ứng bài 90 giây.

## Thay đổi thứ tự theo người dùng

Hoàn thành tái cấu trúc trước, kiểm thử end-to-end sau. Từ thời điểm này không chạy thêm
test, lint, typecheck, gọi LLM thử hay bấm E2E; chỉ sửa mã và viết regression để chạy sau.
Chưa công bố hoàn tất nghiệm thu Sprint 1A, chưa đánh các task triển khai DONE.
Không xóa DB/lịch sử/bản nháp, không đưa bí mật hoặc bộ nhớ đệm vào Git.
Hướng dẫn khởi động và ma trận nghiệm thu tiếp theo: `docs/RUNBOOK.md`.
