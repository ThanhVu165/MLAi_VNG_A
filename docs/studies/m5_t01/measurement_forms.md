# Biểu mẫu và định nghĩa đo — trống, chưa có kết quả

Đồng bộ với [protocol](study_protocol.md). Sao chép mẫu vào kho kết quả có kiểm
soát, không nhập dữ liệu người thật vào Git. Hậu kiểm Gold ở kho reviewer riêng
theo [quy trình Gold](gold_review.md); không phát phần chấm Gold cho participant.

## 1. Case observation form — moderator

Mỗi attempted case một bản; ghi UTC ISO-8601 và hiển thị +07:00. Trường chưa biết
dùng UNKNOWN; thiếu dùng MISSING; không áp dụng dùng NA; không điền 0 thay thiếu.

| Trường | Giá trị |
|---|---|
| session_id / participant_code / sequence | ____ / ____ / ____ |
| condition B0/B2 / set X/Y / case_id | ____ / ____ / ____ |
| product SHA / protocol-case SHA / corpus_version + manifest ID | ____ |
| synthetic received_at / runtime mode / Study DB reference | ____ |
| attempt status: COMPLETE / INCOMPLETE / WITHDRAWN | ____ |
| start_at / end_at / wall_time_s | ____ / ____ / ____ |
| pause intervals + reason / pause_s | ____ / ____ |
| system_wait intervals / system_wait_s hoặc UNKNOWN | ____ / ____ |
| final_decision: AUTO_REPLY / ESCALATE / MISSING | ____ |
| final response/escalation question + participant reason/source | ____ |
| AI_initial_route: AUTO_REPLY / ESCALATE / ERROR / UNKNOWN / NA | ____ |
| AI_action (B2; xem bên dưới) | ____ |
| edit_summary: route/content/both/none và chi tiết | ____ |
| technical_interruption: YES/NO + loại/thời điểm | ____ |
| restart_count (0/1) / recovered / evidence_ref | ____ / ____ / ____ |
| moderator_note / missing-data reason | ____ |

Giữ original route, cuối cùng và edits riêng. Thao tác có thể vừa sửa route vừa
sửa nội dung: chọn action chính theo thứ tự REJECT_ROUTE → REJECT_CONTENT →
ACCEPT_EDITED → ACCEPT_UNCHANGED và ghi mọi thay đổi trong edit_summary.

- ACCEPT_UNCHANGED: giữ route và nội dung gợi ý.
- ACCEPT_EDITED: giữ route, sửa nội dung để sử dụng.
- REJECT_ROUTE: final human route khác route AI có sẵn, dù có sửa nội dung thêm.
- REJECT_CONTENT: giữ route nhưng từ chối toàn bộ nội dung đề xuất, viết thay thế.
- NO_DECISION_TECHNICAL: chưa có final decision vì lỗi B2; không tính là từ chối AI.
- UNKNOWN: B2 có final decision nhưng chưa ghi đủ thao tác; NA cho B0 hoặc không
  có đề xuất để đánh giá. Ghi lỗi/thiếu riêng, không ép vào acceptance category.

Hậu kiểm riêng, không hiển thị khi participant làm case:

| Case row ref | Gold version | Gold decision | Gold rule | Gold signed? | correct_route | missed_escalation | unnecessary_escalation | scorer/date |
|---|---|---|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | UNKNOWN | UNKNOWN | UNKNOWN | ____ |

## 2. B0/B2 measurement form — một dòng mỗi condition

| session_id | participant_code | sequence | condition | set | attempted n | complete n | final-route available n | scored n | interrupted n | valid-time n | median wall_time_s | range wall_time_s | exclusions/reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ |

Lưu từng case observation làm nguồn; không chỉ ghi tổng. Nếu không đủ timestamps
thì time thiếu dù route có thể hợp lệ. Ghi số case chưa bắt đầu riêng, không tính
vào attempted. Time của attempt không hoàn tất chỉ là elapsed-to-stop, không
trộn với completed review time.

## 3. Feedback sau từng condition — participant tự viết

Mã participant: ____; condition: ____; set: ____; ngày/giờ: ____.

| Câu hỏi | Phản hồi |
|---|---|
| Hữu ích (1 hoàn toàn không – 5 rất hữu ích; có thể bỏ) | ____ |
| Tự tin quyết định (1 rất thấp – 5 rất cao) | ____ |
| Khối lượng thao tác (1 rất ít – 5 rất nhiều) | ____ |
| Điều gì làm bạn chậm hoặc khó hiểu nhất? | ____ |
| Bạn dựa vào thông tin nào để chốt quyết định? | ____ |
| B2: gợi ý nào bạn chấp nhận, sửa hoặc từ chối, và vì sao? | ____ |
| Khó khăn/lỗi hoặc điểm gây bất tiện khác? | ____ |

B0: câu B2=NA. Moderator ghi ai viết/chép lại và xác nhận participant nếu chép;
không biến nhận xét moderator thành lời participant.

## 4. Feedback cuối session — participant tự viết

Mã participant: ____; sequence: ____; ngày/giờ: ____.

- Điểm hữu ích nhất và hạn chế lớn nhất của Exodia: ____.
- Có lúc nào AI làm bạn bớt kiểm tra hoặc khiến bạn nghi ngờ đúng chỗ: ____.
- So với B0, điều gì dễ/khó hơn ở B2; có ảnh hưởng do thứ tự/làm quen: ____.
- Thay đổi cụ thể nào nên làm trước; lý do hoặc ví dụ: ____.
- Tác động tiêu cực/rủi ro/nhận xét trái chiều: ____.
- Cho dùng trích dẫn đã loại định danh: [ ] Có [ ] Không (đối chiếu consent).
- Có muốn rút hoặc yêu cầu xóa theo consent: ____.

## 5. Evidence aggregation template và denominator

Chỉ chấm sau Gold sign-off; scorer đọc lựa chọn cuối, không tự suy diễn ý định.

| Metric | n (tử số) | N (mẫu số) |
|---|---|---|
| Completion | Attempt COMPLETE | Tất cả attempted cases của condition |
| Correct route | Final route = Gold decision | Case có final AUTO_REPLY/ESCALATE và Gold đã xác nhận |
| Missed escalation | Gold ESCALATE, final AUTO_REPLY | Case có Gold ESCALATE đã xác nhận và final route hợp lệ |
| Unnecessary escalation | Gold AUTO_REPLY, final ESCALATE | Case có Gold AUTO_REPLY đã xác nhận và final route hợp lệ |
| Technical interruption | Attempt có >=1 lỗi kỹ thuật | Tất cả attempted cases; một case chỉ đếm một lần |
| Mỗi AI action quyết định | Số action tương ứng | B2 có đề xuất, final route và action đã ghi hợp lệ |
| NO_DECISION_TECHNICAL | B2 không chốt vì lỗi | Tất cả attempted B2 cases |

AI action quyết định gồm bốn loại ACCEPT/REJECT, báo riêng từng n/N và số UNKNOWN/
NA/thiếu đề xuất. Acceptance gộp = ACCEPT_UNCHANGED + ACCEPT_EDITED trên cùng N;
rejection gộp = REJECT_ROUTE + REJECT_CONTENT trên cùng N. Không suy rejection
thành sai route, không tính technical failure là missed escalation.

`wall_time_s=end_at-start_at` là primary review time, bao gồm wait/pause; median
và min–max cho completed cases có timestamp hợp lệ, kèm n. Báo cả toàn bộ completed
và nhóm không interruption nếu có; n nhỏ giữ raw time từng case trong kho riêng.
Không tự trừ wait/pause, không dùng elapsed-to-stop như completed time.

| Condition / set / sequence | Metric | n | N | n/N | Missing/excluded + lý do | Evidence refs |
|---|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | ____ | ____ |

| Condition | Time n | Median s | Min–max s | Interrupted completed n | Notes |
|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | ____ |

N=0 báo NA (0 eligible), không báo 0% hoặc điền giả. Báo condition riêng rồi tổng
theo tổng n/tổng N, không trung bình các tỷ lệ có denominator khác. Within-person
comparison dùng participant có hai condition hợp lệ cho metric; ghi paired n,
case counts/sets và loại trừ. Đây không phải cặp cùng email. Không loại kết quả xấu
hoặc technical attempt khỏi completion/technical rate để làm số đẹp.

| Theme | Observation refs | Participant n/N trả lời câu này | Quote đã opt-in | Counter-evidence/negative impact | Interpretation/limitation |
|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | ____ |

Theme n đếm participant duy nhất, không đếm số câu nhắc; denominator là người có
phản hồi hợp lệ cho câu tương ứng. Giữ quan sát trái chiều, không claim prevalence
hoặc statistical significance từ mẫu nhỏ. Không publish raw consent/result.

## 6. Product improvement trace template — chỉ dùng sau study thật

| Improvement ID | Feedback/case refs | Raw n/N hoặc quote được phép | Problem + negative/counter evidence | Proposed change | Coordinator decision/date | Commit/PR | Before/after validation | Remaining risk |
|---|---|---|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ |

Chưa chọn trước cải tiến. M5 Exit Gate yêu cầu >=1 thay đổi cụ thể từ feedback
thật kèm commit evidence; mẫu trống không chứng minh yêu cầu đó đã đạt.
