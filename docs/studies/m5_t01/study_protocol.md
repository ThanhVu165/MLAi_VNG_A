# Protocol B0/B2 — Owner draft v1

Independent review và Coordinator approval: **PENDING**. Protocol này chưa cho phép
chạy study hoặc LIVE LLM/API. [Nguồn và baseline](README.md),
[form và metric definitions](measurement_forms.md), [consent](recruitment_consent.md).

## Mục tiêu, thiết kế và cân bằng

Đo review time, final human decision, thao tác chấp nhận/sửa/từ chối đề xuất AI
và phản hồi khi xử lý email hành chính synthetic. B0 là xử lý thủ công bằng tài
liệu; B2 là sử dụng Exodia. Không so B0 với replay rồi gọi đó là hiệu quả AI live.

Within-participant crossover: mỗi người xử lý 4 email B0 và 4 email khác B2.
Không ai thấy cùng email ở cả hai điều kiện. Giữ chia X/Y của Trello, thứ tự trong
bộ là 1→4; cùng chính sách thứ tự cho cả hai condition. Mỗi bộ có 4 email,
7 request, 3 case đa ý định. X gồm conduct 2 / grade 1 / withdrawal 1;
Y gồm grade 2 / conduct 1 / withdrawal 1. Owner đã kiểm phân bố route/rule trên
Trello; bảng Gold và cân bằng nhãn lưu riêng theo [Gold review](gold_review.md).

Độ khó chỉ là nhận định Owner, chưa có reviewer/pilot xác nhận. Số email/request
cân bằng không chứng minh độ khó bằng nhau; lượng đọc và khó tra cứu vẫn có thể
khác. Giữ X4 mới có K49. Reviewer phải đánh giá lại tương đương sau kiểm soát
ACTIVE-only, nhất là ảnh hưởng bỏ yêu cầu lọc nguồn cũ ở B0. Báo set/condition và
sequence để thấy imbalance; không tạo điểm độ khó hoặc kết quả participant giả.

| Sequence | Condition đầu | Condition sau |
|---|---|---|
| S1 | B0-X | B2-Y |
| S2 | B2-Y | B0-X |
| S3 | B0-Y | B2-X |
| S4 | B2-X | B0-Y |

Với 4 người, phân ngẫu nhiên mỗi sequence một người. Với 3 người, chọn ngẫu nhiên
sequence bỏ trước session đầu, ghi cách bốc thăm và thứ tự ba sequence còn lại
trong allocation log; Coordinator xác nhận trước chạy. Người thứ tư nếu có dùng
sequence còn thiếu. Không đổi allocation vì thấy kết quả. Không thể cân bằng
hoàn hảo n=3; phải báo sequence/condition order imbalance và giới hạn học tập.
Nghỉ 5 phút giữa điều kiện; dự kiến mỗi session 45–60 phút, không ép case timeout
để tạo kết quả đẹp. Nếu phải dừng vì lịch, ghi incomplete và lý do.

## Corpus và công bằng quyền truy cập

B0/B2 pin cùng snapshot sáu JSON baseline, metadata và hash. Tập căn cứ dùng cho
cả hai chỉ gồm năm nguồn ACTIVE: RL-2026-3150, RH-2026-101, HP-2026-1,
PK-2026-204, QDPQ-2026-01. Kiểm tra effective date, cohort và phạm vi theo cùng
quy tắc của spec; không mặc định metadata trong DB đã khớp seed.

RL-2025-2363 SUPERSEDED chỉ có trong reviewer archive, không đưa vào bộ tài liệu
tra cứu B0 hoặc kênh tra cứu B2 trong session. B2 không dùng quản trị/history
để mở nguồn cũ. B0 có toàn văn năm nguồn ACTIVE read-only, cùng metadata; cho phép
search văn bản. B2 được phép mở cùng bộ read-only ngoài citations của Exodia.
Không Internet, tài liệu cá nhân, công cụ AI khác, Gold, Trello hay GitHub khi làm
case. Không bỏ nguồn ACTIVE khó hoặc thêm căn cứ để cứu một condition.

Đây là làm rõ khác biệt với câu “B0 dùng cả 6 văn bản” trên Trello: sáu nguồn là
snapshot kiểm kê/reviewer, năm ACTIVE là corpus sử dụng cho **cả hai** condition.
Không thay email/Gold/policy; reviewer xác nhận fairness trước GO.

Moderator ghi trong session manifest: product SHA, protocol/case Git SHA,
corpus_version thực từ Study DB, hash sáu nguồn, danh sách ACTIVE, runtime mode,
model/provider nếu áp dụng, Study DB path, UTC received_at và display +07:00.
Received_at là timestamp synthetic đã chọn trước và nhất quán giữa input thủ công
và B2, nằm trong phạm vi snapshot được duyệt; không dùng ngày bấm UI làm thay
dữ kiện. X/Y không được tự bổ sung thông tin nghiệp vụ còn thiếu. Nếu UI cần sender,
dùng `study-x1@example.invalid` theo case ID, không dùng email thật; metadata này
không thêm cohort/học kỳ hoặc căn cứ. Chưa chuẩn bị/chạy ingestion trong task này.

## Script participant (đọc nguyên văn)

“Bạn sẽ xử lý email synthetic như trong công việc hành chính. Với mỗi email,
hãy chọn AUTO_REPLY nếu có thể trả lời thường quy bằng nguồn hiện hành; chọn
ESCALATE nếu cần người có thẩm quyền, nguồn không an toàn/mâu thuẫn hoặc thiếu
dữ kiện cần thiết. Ở B0, bạn dùng tài liệu được cung cấp. Ở B2, bạn có thể chấp
nhận, sửa hoặc từ chối đề xuất của Exodia. Hãy đưa ra quyết định bạn thực sự tin
là an toàn; đây là đánh giá công cụ, không phải đánh giá năng lực cá nhân.
Không dùng dữ liệu thật. Hãy ghi quyết định cuối cùng, nội dung phản hồi hoặc
câu hỏi chuyển tiếp và lý do/căn cứ bạn dựa vào. Bạn có thể nghỉ hoặc dừng.”

## Moderator run sheet

1. Trước session: kiểm unlock bên dưới, eligibility, exposure, consent, allocation,
   manifest và snapshot sạch. Consent lưu riêng khỏi results.
2. Đọc cùng script, walkthrough B0/B2 với ví dụ trung tính ngoài X/Y đã được duyệt,
   cùng thời lượng hướng dẫn. Không dùng case học thuộc/Gold hoặc Set A/Set B.
3. Phát từng email đúng bộ/condition, chỉ rõ tài liệu được phép. Không giải thích
   Gold, rule hay gợi ý route. Không đưa bộ thứ hai trước lúc bắt đầu condition.
4. Hỏi sẵn sàng, mở đầy đủ email, nói “Bắt đầu”; ghi timestamp. Quan sát trung tính,
   không yêu cầu think-aloud bắt buộc làm lệch thời gian.
5. Khi participant muốn chốt, chỉ hỏi “Bạn có muốn chốt quyết định này không?”
   Ghi final route, nội dung cuối và căn cứ/lý do. B2 ghi AI route/action và edits.
   Nếu route thay đổi nhưng UI không cho lưu, ghi lựa chọn bằng form và UI friction;
   không lấy AI route thay final human decision hoặc sửa DB để hợp thức hóa.
6. Sau condition thu feedback; nghỉ 5 phút; sau condition sau thu session feedback.
7. Kiểm completeness, không điền thay participant. Hậu kiểm Gold ở kho riêng sau
   session; không trả lời đúng/sai giữa các case để tránh learning contamination.

## Timer và final decision

Start: toàn bộ email xuất hiện và moderator nói “Bắt đầu”. End: participant chốt
AUTO_REPLY/ESCALATE và lưu/đọc lại nội dung cuối, hoàn tất accept/edit/reject ở B2
hoặc ghi lựa chọn qua form nếu UI cản. Không chờ gửi mô phỏng/countdown sau chốt.

`wall_time_s = end_at - start_at`, bao gồm system wait và pause nếu có. Đây là
primary review time (giữ nguyên định nghĩa Trello). `pause_s` và `system_wait_s`
ghi riêng theo timestamp/quan sát, không tự trừ; không biết ghi UNKNOWN.
Gián đoạn thì đánh dấu pause nhưng giữ timestamp start/end gốc, báo interrupted
cases riêng; không lẫn adjusted time với primary. Final route là lựa chọn cuối
của người, không phải đề xuất ban đầu, dispatch status hoặc lỗi kỹ thuật của AI.

## Gián đoạn và lỗi

- Gián đoạn ngoài tác vụ: ghi pause start/end, nguyên nhân; tiếp tục cùng case
  nếu participant đồng ý. Nếu dừng, ghi incomplete, không suy diễn route.
- Exodia lỗi: ghi technical interruption, loại lỗi, system wait và evidence đã
  loại định danh. Moderator được restart tối đa một lần theo runbook Study đã
  duyệt; trước restart bảo toàn evidence và kiểm tra duplicate/không gửi thật.
  Không restart/reset DEV/Demo, không tự đổi mode sang replay hoặc gọi provider.
- Không phục hồi: dừng case, final_decision=MISSING nếu chưa chốt,
  AI_action=NO_DECISION_TECHNICAL ở B2; không biến lỗi thành P03 hoặc quyết định
  ESCALATE của participant. Nếu người đã chốt qua form, giữ quyết định đó và đánh
  dấu lỗi. Giữ attempted cases trong completion/technical denominator.
- Không tự thay case hoặc rerun để chọn kết quả tốt. Rút khỏi session theo consent.
  Ghép phân tích within-person chỉ khi cả hai condition có dữ liệu hợp lệ tương
  ứng cho metric; báo mọi loại trừ, n và case/set khác nhau, không gọi là cặp cùng email.

## Điều kiện mở khóa study thật — tất cả còn cần xác nhận thực tế

- [ ] Minh review protocol, form, source control, equivalence và Gold độc lập.
- [ ] Coordinator duyệt protocol/case/Gold version, owner, sequence và lịch/due.
- [ ] Gold storage/access được kiểm chứng; không lộ đáp án cho participant.
- [ ] >=3 người ngoài team phù hợp, chưa thấy case/Gold, xác nhận lịch và consent.
- [ ] Storage custodian, location, access, retention và quyền rút/xóa đã điền.
- [ ] M3-T03/Coordinator cung cấp runtime proof trên revision được chọn: DEV/Study/
  Demo DB path riêng; seed/reset trên DB tạm; Verify không ghi chéo; approval/audit
  cách ly; quyền truy cập; worker/dispatch không đụng DB khác. Bản bàn giao Trello
  trước đó ghi BLOCKED; task này không xác nhận lại runtime hoặc coi dependency PASS.
- [ ] Revision B2 có human control/approval đã kiểm chứng; corpus DB và hash khớp;
  B0/B2 cùng nguồn ACTIVE/received_at/access rule; manifest và backup/reset được duyệt.
- [ ] Exact runtime mode/provider được duyệt; LIVE cần authorization riêng về
  run/case/budget. Replay nếu được duyệt phải công bố rõ giới hạn, không gọi là LIVE.
- [ ] Coordinator có Task Contract thực hiện study riêng và quyết định GO.

## Phân tích và giới hạn

Dùng raw n/N và median/range với n theo [form](measurement_forms.md). Route accuracy
không đồng nghĩa nội dung trả lời đúng hoàn toàn. N>=3 vẫn exploratory/convenience
sample, không claim significance, causal superiority, automation-bias prevalence
hay đại diện cho mọi chuyên viên. X/Y khác email, domain lệch và order imbalance
phải công bố. Ghi cả phản hồi trái chiều/negative impact. Cải tiến sản phẩm chỉ
chọn sau feedback thật và có Coordinator decision + commit evidence, ngoài task này.
