# PROJECT_SPEC.md — Escalation Referee · Sprint 1A

## 1. Hiệu lực đặc tả và trạng thái nghiệm thu

Bản này đồng bộ cấu trúc tái thiết kế đã được người dùng cho phép ngày 22/09/2026. Nó thay thế các chỉ dẫn cũ mâu thuẫn về quyền trả lời ở cấp đoạn, chặn email theo số từ, gộp lỗi kỹ thuật vào chuyển tiếp và bố cục sáu trang. Lịch sử thiết kế cũ được giữ trong Git, không duy trì hai bộ quy tắc song song.

Thứ tự áp dụng: yêu cầu trực tiếp mới nhất của người dùng → brief Đề A và yêu cầu tối thiểu Sprint 1 → đặc tả này → AGENT.md → TASKBOARD.md. Quyết định cho phép tái cấu trúc bao gồm thay đổi contract, schema và UI cần thiết; không cho phép sửa kỳ vọng kiểm thử để che lỗi.

**Chỉ đạo hiện hành: hoàn thành tái cấu trúc trước, nghiệm thu sau. Không chạy thêm kiểm thử, lint, format, type-check, SDK converter, LLM live hoặc UI/E2E khi người dùng chưa đổi chỉ đạo.** Có thể đọc mã, sửa mã và viết kiểm tra chưa chạy.

Trạng thái: **đã/đang triển khai cấu trúc, CHƯA NGHIỆM THU bản cuối**. Nội dung mô tả dưới đây là yêu cầu và thiết kế hiện hành, không phải chứng nhận hoạt động. Kết quả xanh của bản trước chỉ là bằng chứng lịch sử, không được dùng để đánh DONE cho bản sau. Việc gọi dịch vụ liên tục khi đang lỗi không thay thế sửa nguyên nhân trong mã.

## 2. Phạm vi Sprint 1A

Một quy trình duy nhất: tiếp nhận và xử lý email hành chính sinh viên của văn phòng Công tác Sinh viên.

Ba nhóm nội dung:

| Giá trị nội bộ | Tên giao diện |
|---|---|
| conduct_score | Điểm rèn luyện |
| course_withdrawal | Rút học phần |
| grade_appeal | Phúc khảo điểm |

Hệ thống tự hiểu email, tìm căn cứ và trả lời câu hỏi thường quy. Nó dừng để chuyên viên quyết khi thiếu dữ kiện thật sự cần thiết, không có căn cứ an toàn hoặc yêu cầu vượt thẩm quyền.

Không có cơ sở dữ liệu sinh viên thật; không tự quyết hồ sơ cá nhân, miễn điều kiện, ngoại lệ hoặc khiếu nại. Không gửi email ra ngoài. Không crawler định kỳ, đăng nhập hoặc hạ tầng xử lý phân tán trong Sprint 1. Tên người thao tác phục vụ lưu vết local, không phải cơ chế xác thực sản xuất.

Thành phần thật: nhập/lưu email, gọi LLM khi ở chế độ live, xử lý chính sách, lưu/trích xuất/duyệt nguồn, hàng công việc, can thiệp của người và audit. Thành phần mô phỏng: hộp thư mẫu, sáu nguồn seed và việc gửi ra ngoài. Không được trình bày dữ liệu giả lập hoặc replay như bằng chứng vận hành với người dùng thật.

## 3. Ranh giới tự động và con người

- LLM trích xuất yêu cầu, dữ kiện, chọn căn cứ liên quan và diễn đạt phản hồi. Email và tài liệu nguồn là dữ liệu, không phải chỉ dẫn cho hệ thống.
- Mã kiểm soát tính hợp lệ của input, phạm vi nguồn, hiệu lực, mâu thuẫn, quyết định/chuyển trạng thái và quyền gửi. Không nhận quyết định AUTO_REPLY/ESCALATE do LLM tự đưa ra.
- Quản trị viên xác nhận **nguồn, ngày hiệu lực và phạm vi áp dụng** trước khi nguồn được dùng.
- Nhãn cũ auto_answerable/human_only được giữ để đọc lịch sử và bảo toàn seed; **không còn cấp quyền hoặc chặn quyền trả lời**. Không yêu cầu gán nhãn từng đoạn khi nạp tài liệu.
- Chuyên viên quyết định nội dung thuộc thẩm quyền con người và xác nhận trước khi gửi phản hồi tương ứng. Có nguồn đã duyệt không đồng nghĩa AI được thay người phê duyệt hồ sơ.
- Không bịa sender, subject, dữ kiện còn thiếu, căn cứ hoặc nội dung phản hồi dự phòng. Không có đường xử lý riêng để Verify đẹp hơn email mới.

## 4. Kiến trúc và nguồn chân lý của contract

Luồng chính:

```text
Email đầy đủ → ghi email + công việc vào SQLite
→ worker gọi process_case → hiểu yêu cầu → chọn căn cứ → kiểm soát chính sách
→ thường quy: soạn + kiểm tra → chờ gửi → worker gửi mô phỏng
→ cần người: lưu thẻ → người quyết định + lý do → xếp việc soạn tiếp
  → worker diễn đạt lại → người xem trước/duyệt gửi
→ lỗi kỹ thuật: giữ email và lỗi để thử lại, không biến thành thiếu dữ kiện
```

Không chép lại enum/dataclass/chữ ký API trong tài liệu vì sẽ tạo contract thứ hai. Khi tích hợp, đọc định nghĩa thực tại:

| Ranh giới | File nguồn chân lý |
|---|---|
| Enum và dataclass trao đổi dữ liệu | core/types.py |
| Pipeline dùng chung, kể cả tham số nhận case đã có trong hàng công việc | core/pipeline.py |
| Tiếp nhận, chạy lại, hàng soạn sau quyết định và worker | core/worker.py |
| Lưu/khôi phục kết quả cùng căn cứ đã sử dụng | core/results.py |
| Phản hồi sau quyết định, gửi và can thiệp | core/resume.py, core/dispatch.py, core/controls.py |
| Đọc nguồn đã duyệt, lấy đầy đủ căn cứ theo phạm vi | corpus/api.py |
| Nạp/chuẩn bị/duyệt nguồn | corpus/intake.py, corpus/workflow.py, corpus/lifecycle.py |
| Kiểu nguồn và bản gốc, lưu trữ corpus | corpus/store.py |
| Schema SQLite và giao dịch | infra/migrations/001_init.sql, infra/migrations/002_workflow.sql, infra/db.py |
| Gọi LLM, ngân sách gọi, audit | infra/llm.py, infra/audit.py |
| Dữ liệu và tiêu chí so kết quả kiểm thử | verify/cases_*.json, verify/harness.py |

Phân công: A — core/ và policies/; B — corpus/, trang Quy định và kiểm thử nguồn; C — infra/, UI còn lại, Verify và tích hợp. core/types.py và tài liệu chung phải được điều phối trước khi sửa. Corpus có thể dùng kiểu chung trong core/types.py, không gọi pipeline hoặc UI. Runtime đọc corpus qua corpus/api.py. Worker thuộc core/, không đặt logic nghiệp vụ vào infra/.

Python 3.11 và các phụ thuộc trong requirements.txt là môi trường dự án. Không thêm dependency, adapter hoặc dịch vụ chỉ để giải quyết việc vài dòng stdlib/phụ thuộc sẵn có đã làm được.

## 5. Email, hiểu yêu cầu và chọn căn cứ

### 5.1 Tiếp nhận

Email bắt buộc có người gửi, tiêu đề, nội dung và received_at có múi giờ. Luồng dán nhập đúng dữ liệu người dùng; thời điểm tiếp nhận được tạo ở UTC. Hộp thư mô phỏng dùng timestamp và external_id của email mẫu, không thay bằng thời gian bấm nút.

UI không cho gửi thiếu trường vào pipeline. Bộ Verify vẫn được phép đưa input bất hợp lệ vào pipeline thật để kiểm tra hành vi từ chối; không sửa case rỗng thành một email hợp lệ.

Không loại email có nghĩa vì ít từ hoặc thiếu dấu hỏi. R0/R1 chặn trường bắt buộc rỗng và xử lý ngôn ngữ chắc chắn ngoài vi/en. INVALID_INPUT không vào hàng chuyên viên và không tính như chuyển tiếp.

Cùng email hộp thư không được tạo lại do bấm nút/rerun giao diện. Chạy lại một lần xử lý tạo case mới liên kết lịch sử, không ghi đè lần trước.

### 5.2 R2 — Hiểu toàn bộ email

Tiêu đề và nội dung sau xử lý an toàn cùng đi vào bước hiểu yêu cầu. Mỗi ý định được phân biệt giữa hỏi thông tin và xin một quyết định áp dụng cho hồ sơ cá nhân.

Ví dụ: hỏi lệ phí phúc khảo là thông tin, không tự động biến thành khiếu nại; xin cho phép nộp phúc khảo trễ là yêu cầu thẩm quyền. Thiếu mã học phần/học kỳ/khóa chỉ được coi là thiếu dữ kiện khi câu hỏi thực sự cần dữ kiện đó để áp dụng căn cứ.

### 5.3 R4 — LLM chọn căn cứ, mã kiểm soát phạm vi

corpus.api.available_evidence cung cấp các đoạn nguồn ACTIVE theo domain, thời điểm nhận và dữ kiện phạm vi đã biết. Nó không lọc theo nhãn chunk cũ.

core/retrieval.py dùng lượt LLM chọn ID căn cứ trực tiếp liên quan cho từng yêu cầu, các điều cần đọc cùng nhau, dữ kiện còn thiếu và yêu cầu chưa có nguồn. Mọi ID trả về phải nằm trong tập ứng viên thực, không chấp nhận ID tự tạo. Khi chọn đoạn, đọc thêm ngữ cảnh cùng Điều mà vẫn giữ ID/breadcrumb truy vết.

Không để Điều hoàn học phí mâu thuẫn làm hỏng câu hỏi chỉ hỏi hạn rút. Cờ mâu thuẫn dùng cho email phải xét đối phương còn thuộc cùng phạm vi ngày/khóa/đối tượng. Nguồn đa domain không được biến mất chỉ vì trường domain lịch sử của đoạn là domain đầu tiên.

Indexer hybrid vẫn là thành phần tìm kiếm hiện có; khóa cache bao gồm nội dung và metadata ảnh hưởng kết quả. Đường runtime hiện hành chọn từ tập căn cứ nhỏ bằng R4, không tuyên bố mọi yêu cầu đều đi qua tìm kiếm vector. Khi corpus lớn vượt context, thiết kế truy xuất phân tầng là việc sau Sprint 1, không tạo nhánh riêng cho Verify.

### 5.4 Phân loại quyết định

| Trường hợp | Kết quả |
|---|---|
| Hồ sơ cá nhân, kháng nghị, xin ngoại lệ hoặc cần phê duyệt | ESCALATE / AUTHORITY_REQUIRED, P01 |
| Ngoài domain, không có nguồn ACTIVE phù hợp, hoặc căn cứ mâu thuẫn | ESCALATE / OUT_OF_POLICY, P02 |
| Thiếu dữ kiện áp dụng hoặc phạm vi không khớp | ESCALATE / FACT_UNRESOLVED, P03 |
| Guard nội dung không xác minh được bản nháp | Nhánh P04 theo policies/policy.yaml, không đồng nhất với lỗi dịch vụ |
| Câu hỏi thường quy có căn cứ an toàn | AUTO_REPLY, P05 |
| Input thiếu/rỗng | INVALID_INPUT, không phải một trong ba loại chuyển tiếp |
| Ngôn ngữ ngoài vi/en được chặn ở R1 | ESCALATE / OUT_OF_POLICY, R1 |
| Lỗi mạng, SDK/schema/parse, timeout, hết ngân sách, dịch vụ hoặc persistence | Decision.ERROR / CaseStatus.ERROR khi có thể lưu; không có escalation_type nghiệp vụ |

Danh mục enum cũ như AUTHORITY_CONTENT có thể còn tồn tại để đọc lịch sử; không được tái đưa nhãn human_only thành guard cấp quyền. Chính sách thực nằm trong policies/policy.yaml và core/policy_engine.py.

Lỗi kỹ thuật trong bước soạn tiếp sau quyết định của người giữ quyết định đã lưu; job báo lỗi và cho phép yêu cầu soạn lại. Không buộc người quyết định lại, không tự gửi và không giả thành FACT_UNRESOLVED.

### 5.5 Sinh phản hồi và câu hỏi chuyển tiếp

Sinh câu trả lời phải nhận **email + yêu cầu/dữ kiện đã hiểu + căn cứ đã chọn**, không chỉ tóm tắt các đoạn nguồn. Phản hồi đúng vi/en của email, trả lời đúng các ý được giao, có citation và không cam kết thay người có thẩm quyền.

Guard kiểm tra nguồn/citation, giá trị nêu ra, tỷ lệ câu có căn cứ và lời cam kết vượt quyền. Không sửa âm thầm nội dung sai thành câu trả lời có vẻ hợp lệ.

Thẻ chuyên viên có bốn phần: tóm tắt, dữ kiện, căn cứ, một câu hỏi đóng kèm phương án. Email đa ý định vẫn là một case; phần thường quy có thể có bản nháp riêng, phần xin quyết định phải chuyển người. Không để phần không được hỗ trợ làm mất căn cứ đã tìm thấy cho phần được hỗ trợ.

## 6. LLM và lỗi dịch vụ

Mọi lời gọi qua infra.llm.call_json. Không dùng replay/câu trả lời dựng sẵn làm runtime mặc định hoặc phương án che lỗi live. Chế độ replay chỉ phục vụ kiểm tra offline và phải được ghi nhận rõ trong bằng chứng.

Ngân sách và timeout lấy từ infra/settings.py và infra/llm.py: hiện tại tối đa bốn attempt và 60 giây cho một lượt xử lý, kể cả retry; mỗi call có timeout hữu hạn. Lỗi tạm thời chỉ thử lại tối đa một lần trong ngân sách. Lỗi cấu hình/schema không được retry vòng lặp. Không giữ giao dịch ghi SQLite qua call LLM.

Schema gửi Gemini phải đúng dạng SDK đang dùng: type đơn, nullable khi cần, enum phù hợp. Không đưa JSON Schema union dạng type: [string, null] vào SDK không hỗ trợ. Ngày tiếp tục được kiểm tra trong mã, content_hash do hệ thống tính; đề xuất metadata không tự kích hoạt nguồn.

Khi dịch vụ đang trả 503 hoặc lỗi cấu hình, lưu rõ vấn đề và ngừng vòng gọi lặp. Hướng khắc phục phải phân biệt thử lại sau với sửa cấu hình/mã; không khẳng định lỗi nhà cung cấp đã được sửa chỉ vì unit test xanh.

## 7. Vòng đời nguồn quy định

```text
Nạp tệp/văn bản → giữ bản gốc → trích xuất → chia đơn vị pháp lý
→ đề xuất thông tin nguồn → người đối chiếu nguồn/ngày/phạm vi
→ giao dịch duyệt: lưu metadata + đoạn căn cứ + ACTIVE + thay thế nguồn cũ
  + tính conflict + phiên bản + audit/case cần xem lại
→ nguồn được dùng; chỉ mục làm mới theo khóa dữ liệu
```

- PDF/DOCX/văn bản mới được chia theo nội dung thật, không bắt buộc 12 đoạn. PDF ảnh không đọc được phải báo rõ để nạp bản văn bản, không kích hoạt nguồn rỗng.
- source_contents giữ byte gốc, văn bản đã trích xuất và tên tệp. Nội dung đã duyệt không được sửa âm thầm bằng form hoặc dataclass cũ.
- Chuẩn bị/duyệt đọc lại nguồn theo ID từ DB. Từ chối dùng điều kiện trạng thái còn chờ xác nhận. UI lưu ID chọn, không giữ SourceRecord cũ trong lựa chọn.
- Duyệt bắt buộc xác nhận tên nguồn, đơn vị ban hành, ngày hiệu lực, lĩnh vực và đối tượng; nguồn chuyển tiếp cần thông tin khóa áp dụng. Người thực hiện và lý do được lưu vết.
- approve_source, activate_source, reject_source và rollback_source dùng infra.db.transaction. Thay thế nguồn, conflict, phiên bản và audit liên quan nằm trong cùng giao dịch. Worker chỉ được thấy trạng thái đã commit đầy đủ; lỗi giữa chừng rollback thay đổi và nhật ký của giao dịch.
- LLM đề xuất nằm **ngoài** giao dịch ghi. Không khóa DB trong lúc đợi mạng.
- Conflict không dựa vào trùng số Điều/Khoản: phải cùng nội dung liên quan, giá trị khác nhau và phạm vi ngày/đối tượng/khóa giao nhau. Thuật toán hiện tại là heuristic số/chủ đề, không phải bộ chứng minh mâu thuẫn pháp lý tổng quát.
- UI hiện không mở nạp URL. Backend tải URL thủ công có chặn HTTPS/địa chỉ nội bộ/redirect và giới hạn kích thước, nhưng chưa có DNS pinning; không trình bày nó như bộ crawler an toàn sản xuất.
- Nguồn cũ thiếu bản gốc không được gán một văn bản seed mới khác hash vào lịch sử. Chỉ bổ sung bản gốc seed khi hash khớp chính xác; nội dung ghép từ đoạn lưu cũ phải được ghi rõ là bản tái dựng.

## 8. Lưu trữ, snapshot và xử lý nền

SQLite schema v2 là phần mở rộng bảo toàn các bảng v1, không tạo DB mới đè dữ liệu cũ.

| Dữ liệu | Nơi lưu |
|---|---|
| Email gốc, thời điểm, trạng thái hiện tại, liên kết lần chạy | cases |
| Trích xuất, quyết định, bản nháp, thẻ và quyết định người | extractions, decisions, drafts, escalations, human_decisions |
| Nguồn, đơn vị căn cứ, phiên bản | sources, chunks, corpus_versions |
| Byte gốc và nội dung đã trích xuất | source_contents |
| Snapshot kết quả gồm căn cứ tại lần xử lý | case_results |
| Hàng việc, trạng thái và lease xử lý | case_jobs |
| Lưu vết, thời gian từng bước và thiết lập | audit_events, step_latencies, settings |

Migration chính xác nằm trong hai file SQL và infra/db.py, bao gồm bổ sung external_id cùng chỉ mục chống nhận trùng. DB hiện hữu được backup trước nâng schema; kiểm tra phiên bản/cấu trúc không hợp lệ phải báo lỗi, không xóa hoặc seed đè.

Runtime, worker, corpus và indexer phải dùng cùng DATABASE_PATH. Thời gian sự kiện lưu UTC ISO-8601; hiển thị giờ Việt Nam +07:00, ngày quy định theo DD/MM/YYYY. Nội dung gốc được giữ riêng, văn bản phục vụ xử lý chuẩn hóa NFC, audit/hiển thị xử lý PII theo boundary đang có.

core/worker.py lưu công việc trước khi xử lý và gọi đúng process_case, kể cả khi người dùng đổi trang. Worker còn xử lý job của case HUMAN_DECIDED bằng quyết định đã lưu rồi đưa bản nháp về PENDING_APPROVAL. Dispatch có vòng nền riêng, không phụ thuộc timer/rerun của trang.

Job có claim/lease, ngăn xử lý lại do rerun; việc bị gián đoạn có trạng thái/hướng chạy lại rõ, không lặp gửi. Lỗi soạn tiếp giữ HUMAN_DECIDED và cho phép xếp lại việc, không mất lựa chọn/lý do của người.

Kết quả và căn cứ lịch sử đọc từ snapshot trong core/results.py; trạng thái/decision/draft mới nhất được đồng bộ từ DB. Khi nguồn bị thay thế, không dùng get_chunk của corpus hiện hành để giả làm nguyên văn căn cứ cũ. Trước quyết định/gửi phải kiểm tra sự thay đổi phiên bản, hiệu lực và điều kiện gửi; không lấy snapshot lịch sử làm giấy phép gửi ở hiện tại.

Phiên bản corpus hiện hành tính từ nguồn ACTIVE thực, không tin giá trị cached setting còn cũ trong khoảng cập nhật. Việc so phiên bản, audit và trạng thái phải nhất quán với giao dịch nguồn; đây là mục cần nghiệm thu cùng worker, không chỉ kiểm thử hàm riêng.

## 9. UI năm mục

1. **Email** — dán đủ trường hoặc chọn email mô phỏng, xem trạng thái và kết quả từ DB.
2. **Cần chuyên viên xử lý** — xem thẻ/bản nháp, nhập lựa chọn và lý do, xếp việc soạn tiếp, xem trước và duyệt gửi.
3. **Quy định** — nạp, xác nhận ở cấp nguồn, đọc toàn văn/tải bản gốc; không có bảng gán nhãn từng đoạn.
4. **Lịch sử xử lý** — mở lại case/snapshot, căn cứ và thao tác, giải thích dễ hiểu.
5. **Kiểm tra hệ thống** — lựa chọn các bộ ca tách biệt, kết quả/chi tiết/xuất JSON.

Tên trạng thái, lỗi và thao tác phải tự nhiên bằng tiếng Việt. Mã enum/rule/chunk không phải ngôn ngữ chính của màn hình; vẫn giữ ID và chi tiết kỹ thuật trong dữ liệu xuất/audit khi cần truy vết. Chọn case/tài liệu bằng ID rồi đọc DB mới.

Chỉ báo cố định nêu rõ hệ thống không gửi email thật. Điều khiển tạm dừng/hủy/can thiệp phải thay đổi trạng thái thật trong DB, có lý do và audit. Bản tự động chờ 60 giây trước gửi mô phỏng; bản chuyển tiếp luôn cần người duyệt gửi. Đổi trang, tải lại hoặc đóng tab không được làm mất công việc đã nhận.

Nguồn chân lý điều hướng là streamlit_app.py; trang con không tự dựng thêm hệ thống điều hướng hoặc worker.

## 10. Dữ liệu demo và kỳ vọng không được thay đổi

### 10.1 Sáu nguồn seed

Giữ sáu ID, trạng thái/phạm vi, is_synthetic=true và ý nghĩa đã duyệt. 72 đoạn là kích thước **fixture seed**, không phải số bắt buộc cho mọi quy chế mới.

| Nguồn | Ý nghĩa phải bảo toàn |
|---|---|
| RL-2026-3150 | Rèn luyện hiện hành, chuyển tiếp; thang 100 điểm, công bố sau phê duyệt |
| RL-2025-2363 | Bản đã thay thế, chỉ giữ lịch sử |
| RH-2026-101 | Rút học phần: hạn 17 giờ thứ Sáu tuần 8; hoàn 70% ở tuần 4–6 |
| HP-2026-1 | Cùng hạn rút, nhưng hoàn 60% ở tuần 4–6 |
| PK-2026-204 | Lệ phí 150.000 đồng, mẫu PK-01; phúc khảo trễ thuộc thẩm quyền |
| QDPQ-2026-01 | Phân cấp thẩm quyền; nhãn human_only cũ vẫn giữ, quyết định thẩm quyền dựa nội dung yêu cầu/quy định |

Xung đột cố ý chỉ ở tỷ lệ hoàn 70%/60%, không ở hạn rút. Rút sau hạn, miễn điều kiện và phúc khảo quá hạn cần người có thẩm quyền. Không bịa tên trường thật, URL thật, văn bản pháp lý thật hoặc phản hồi người dùng.

### 10.2 Mười lăm ca chuẩn

Dữ liệu thực thi là verify/cases_full15.json; bản đọc tại docs/bo_15_ca_kiem_thu.md phải khớp nguyên văn. Hai tập con verify4/escalation5 vẫn giữ ý nghĩa riêng, không đổi expected theo lỗi hiện tại.

| Ca | Kỳ vọng nghiệp vụ |
|---|---|
| V01, V02 | Thông tin rèn luyện/rút học phần có căn cứ; V02 trả lời tiếng Anh |
| V03 | Xin phúc khảo trễ → AUTHORITY_REQUIRED |
| V04 | Ký túc xá ngoài phạm vi → OUT_OF_POLICY |
| E01, E02, E03 | Thang điểm, hạn rút, lệ phí → AUTO_REPLY |
| E04 | Hỏi quy định áp dụng cho mình nhưng thiếu khóa/học kỳ → FACT_UNRESOLVED |
| E05 | Xin miễn điều kiện rút → AUTHORITY_REQUIRED |
| F01 | Email rỗng → INVALID_INPUT |
| F02 | Tiếng Nhật → OUT_OF_POLICY ở R1 |
| F03 | Tước injection, trả lời câu hỏi hạn rút còn lại |
| F04 | Đa ý định có xin ngoại lệ → AUTHORITY_REQUIRED ở cấp case |
| F05 | Tỷ lệ hoàn học phí mâu thuẫn → OUT_OF_POLICY |
| F06 | Hỏi điều kiện rút thường quy → AUTO_REPLY |

Harness gọi pipeline thật, kiểm decision, escalation_type, rule_id; nhánh auto cần citation ACTIVE, nhánh chuyển tiếp cần thẻ/câu hỏi. Có timestamp, thời gian và corpus_version thực trong kết quả đầy đủ. Bộ escalation5 phải có **ba tự động, hai chuyển tiếp đúng và hoàn thành trong 90 giây**; 5/5 nhưng quá 90 giây vẫn chưa đạt bài này.

verify/cases_fresh5.json là dữ liệu bổ sung để phát hiện học thuộc đường demo; không thay thế hoặc chỉnh 15 ca chuẩn. Input mới và nguồn mới phải đi đúng đường vận hành chung, không gọi lookup theo ID/nội dung case.

## 11. Nghiệm thu và điều kiện DONE

Sau khi hoàn thành tái cấu trúc và người dùng cho phép kiểm chứng lại:

- Kiểm tra format/lint/type/unit trên **trạng thái mã cuối**, ghi lệnh, môi trường, exit code và phạm vi; không đổi code chỉ để làm xanh expected sai.
- Chạy riêng verify4, escalation5 và full15 bằng đường chung. Báo từng kết quả/rule/căn cứ, tổng thời gian và nhánh lỗi; giữ tiêu chí 90 giây.
- Kiểm chứng LLM live với email mới và nguồn mới: nạp → đề xuất → xác nhận nguồn → hỏi được từ nguồn đó. Không dùng replay/cache cũ để tuyên bố đã gọi dịch vụ thật.
- Kiểm chứng thiếu trường, injection, đa ý định, thiếu fact, ngoài phạm vi, ngoại lệ, lỗi SDK/dịch vụ và hồi phục; lỗi kỹ thuật không lọt vào ba nhóm nghiệp vụ.
- Thao tác thật: tạm dừng, hủy, chuyên viên quyết định/soạn lại/duyệt gửi, đổi trang/tải lại, worker bị gián đoạn, nguồn đổi trong lúc xử lý/chờ gửi.
- Kiểm chứng DB cũ qua migration có backup, seed không ghi đè, snapshot không mất căn cứ, lỗi giữa giao dịch nguồn rollback toàn bộ và không lộ nguồn duyệt dở cho worker.

Local đạt mới là cơ sở triển khai public; không suy ra URL công khai, trải nghiệm điện thoại/ẩn danh hay yêu cầu hồ sơ nộp đã đạt từ unit test. Các mục live URL, repo/lịch sử phát triển, slide/video/build log, phương pháp đo và người dùng thực tế tiếp tục đối chiếu brief, TASKBOARD và RUNBOOK; chưa có bằng chứng thì ghi chưa hoàn tất.

Chỉ ghi DONE khi đủ kết quả nghiệm thu và tài liệu trạng thái đúng sự thật. Không bịa số liệu tác động, người dùng hoặc ý kiến phản hồi. Danh sách hạn chế nuôi docs/known_failures.md và phần giới hạn của bài thi; không xóa lịch sử thất bại sau khi sửa.

## 12. Giới hạn hiện hành cần công bố

Corpus giả lập, corpus nhỏ, đánh giá nguồn/chọn căn cứ có sai số LLM; conflict heuristic không hiểu mọi mâu thuẫn bằng ngôn ngữ; tài liệu ảnh có thể không trích xuất được. Đề xuất metadata hiện dùng đoạn đầu tài liệu và vẫn cần người đối chiếu.

Chưa có cơ sở dữ liệu sinh viên, xác thực/phân quyền sản xuất, gửi email thật hoặc xử lý phân tán. Worker nền tồn tại trong tiến trình ứng dụng, không phải dịch vụ độc lập luôn sống khi host dừng. Ngân sách timeout/retry hữu hạn không cam kết nhà cung cấp sẽ đáp ứng SLA của cuộc thi.

Dữ liệu legacy có thể thiếu raw source/snapshot; phải thông báo giới hạn thay vì dựng bằng chứng. Các kiểm tra mới viết trong đợt cuối **chưa được chạy theo chỉ đạo hiện hành**; không dùng bất kỳ câu “đã an toàn/đã xanh toàn hệ thống” nào trước nghiệm thu.
