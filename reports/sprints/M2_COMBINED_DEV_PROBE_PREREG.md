# M2 COMBINED DEV PROBE — PREREGISTERED CASES (COORDINATOR-REVIEWED DEV GOLD)

**Trạng thái:** `PREREG_FROZEN_OFFLINE_READY` (fixture `meta.status=GOLD_VERIFIED_READY_FOR_FREEZE`) — coordinator đã duyệt đủ 12-case gold trong conversation. Đây là DEV / DIAGNOSTIC, KHÔNG phải independent held-out Set B; không có tuyên bố về một reviewer độc lập khác. Input, gold và rubric giữ nguyên. Combined DEV LIVE chưa chạy; SHA-256 final bytes được ghi tại `M2_goal_progress.md` sau validation offline.

## 0. Ghi chú về giả định

- **Lịch học kỳ tổng hợp (chỉ để các lời khai về tuần nhất quán):** tuần 1 bắt đầu thứ Hai 2026-08-03, nên thứ Sáu 2026-09-25 là tuần 8 (hạn rút học phần). Lịch này **không nằm trong 6 tài liệu**; hệ thống không được dùng nó làm bằng chứng và không được suy tuần học từ ngày. Mọi tuần học trong email đều là lời khai của sinh viên.
- **Quy ước temporal là quyết định sản phẩm của coordinator, không nằm trong 6 tài liệu:** 'hôm nay' neo theo ngày của `received_at` (+07:00); ngày tương đối khác mà quyết định phụ thuộc thì P03 và xin ngày cụ thể từ chính người gửi.
- **Thứ tự ưu tiên rule lấy từ `policy.yaml`:** P01 > P02 > P03 > P04 > P05 (P04 là guard failure, không dùng làm gold).
- **Input contract:** chỉ có sender/subject/body/received_at/channel/external_id; không có file đính kèm, không xác minh danh tính. Các minh chứng nhắc trong email (giấy ra viện, thực tập) không được coi là đã có.
- **Tương thích harness (coordinator đã xác minh):** khóa `meta` thừa trong mỗi case JSON được loader hiện tại bỏ qua (unknown keys ignored), nên KHÔNG cần file sidecar. Case set `m2_combined_dev` đã được đăng ký tối thiểu trong `verify/harness.py`. Lệnh trong `how_to_run` chỉ để tham chiếu; CHƯA được thực thi. Phải có separate DEV capture/assessment runner trước khi chạy probe vì Verify `_matches()` không chấm đầy đủ content rubric.

## Revision log (sau review coordinator)

- **A2:** bỏ khỏi `expected_missing_facts` những thứ email đã có (mã học phần, tuần học, loại yêu cầu, lý do); thay bằng thiếu minh chứng hỗ trợ lý do (giấy ra viện chưa có trong input). Gold P01 giữ nguyên.
- **A3:** bỏ câu hỏi lại ý định khiếu nại (email đã nêu rõ); chỉ còn thiếu căn cứ/minh chứng cho hiến máu và CLB Tin học. Gold P01 giữ nguyên.
- **A4:** gold chặt: P02, không chấp nhận P01 thay thế; missing facts rỗng (thiếu authoritative policy, không thiếu fact của sinh viên); bỏ mã học phần khỏi missing facts; thêm fail signal P01/P03.
- **C2:** thêm đúng hạn chót 17:00 06/01/2027 như C3; chỉ khác C3 ở ngày nộp ('thứ Hai tuần sau' vs '04/01/2027'); gold P03, không còn P02 thay thế; missing fact duy nhất là ngày cụ thể định nộp.
- **C4:** đổi sang case chính sách hiện hành (K49, học kỳ 1 năm học 2026-2027, 72 điểm); gold P02, không còn P03 thay thế; missing facts rỗng.
- 7 case đã APPROVE (A1, B1, B2, B3, B4, C1, C3) không đổi nội dung.

## PART 1 — WEB RESEARCH SUMMARY (bổ sung cho conduct_score, course_withdrawal, grade_appeal)

Phạm vi: 7 lượt tìm kiếm tổng cộng, trong đó nguồn chính thức của trường Việt Nam về rút học phần rất ít (chỉ một mẫu đơn). Phần còn lại là văn bản pháp lý/báo chí và trang của trường nước ngoài, chỉ dùng để học cách diễn đạt và kiểu nhập nhằng. **Không nguồn nào được đưa vào gold.**

| Domain | Pattern quan sát được | Nguồn | Vì sao thành case thực tế |
|---|---|---|---|
| conduct_score | Ngưỡng 'Khá' khác nhau giữa các văn bản: quy chế cấp bộ năm 2007 ghi 70 đến dưới 80, còn một mẫu phiếu của một trường ghi 65 đến 79 | caselaw.vn, Quyết định 60/2007/QĐ-BGDĐT; Google Docs (mẫu phiếu rèn luyện một trường) | Sinh viên nhầm ngưỡng giữa các năm/văn bản (A3, C4) |
| conduct_score | Quy định cấp bộ có hiệu lực từ 30/06/2026 yêu cầu thông báo kết quả rèn luyện trước khi ra quyết định và cho phép sinh viên kiến nghị tới bộ phận thông báo | doanhnhan.baophapluat.vn, 'Quy định mới về công tác sinh viên từ 30/6' | Sinh viên dùng chữ 'phản hồi/kiến nghị/khiếu nại' lẫn nhau (A3) |
| conduct_score | Quy trình điểm rèn luyện đi qua cố vấn học tập, họp lớp, hội đồng khoa, hội đồng trường rồi mới thông báo | UFM, thông báo hướng dẫn đánh giá RLSV (PDF) | Sinh viên viện lớp trưởng/cố vấn như 'nguồn' (A3, C4) |
| course_withdrawal | Một mẫu đơn rút bớt học phần của trường Việt Nam có sẵn dòng đề nghị hoàn học phí và ghi chú không hoàn từ một tuần nhất định | Mẫu đơn rút bớt học phần (Google Docs, ĐH Nông Lâm) | Sinh viên gộp rút học phần và hoàn học phí vào một email (A2, B3) |
| course_withdrawal | Các trang registrar nước ngoài: mức giảm học phí tính theo tuần của kỳ; ngừng đi học không đồng nghĩa với đã rút | catalogs.rutgers.edu | Lỗi hiểu 'tuần' và 'rút chính thức' (B1, B2, B3) |
| course_withdrawal | Rút muộn thường qua thủ tục kháng nghị chính thức, cần hồ sơ chứng minh hoàn cảnh bất khả kháng; kết quả học tập kém không phải căn cứ | registrar.unl.edu (Appeal Procedure - Course Withdrawals) | Hình dạng email xin rút muộn vì lý do gia đình/y tế (A2) |
| course_withdrawal | Nhà trường khuyến khích sinh viên tham vấn giảng viên và cố vấn trước khi rút | catalog.southernct.edu | Nguồn của hearsay 'cố vấn bảo...' (A2, B3) |
| grade_appeal | Hướng dẫn phúc khảo của một đại học: sau hạn khoa không nhận, lệ phí nộp cùng đơn tại phòng đào tạo | daotao.sis.vnu.edu.vn (ĐHQGHN, hướng dẫn phúc khảo) | Case nộp muộn, hỏi lệ phí (A1, A4) |
| grade_appeal | Thời hạn nhận đơn phúc khảo thay đổi theo năm/kỳ thi (10 ngày năm 2023, 5 ngày theo quy chế kỳ 2026) | lsvn.vn; luatvietnam.vn | Sinh viên dùng con số cũ hoặc của kỳ thi khác (A1, C2) |

**Giới hạn của nghiên cứu web:** thiếu nguồn chính thức Việt Nam về rút học phần; không có diễn đàn sinh viên thật nào được lấy nguyên văn. Mọi email trong bộ này là viết mới hoàn toàn.

## PART 2 — POLICY COVERAGE MATRIX (chỉ 6 tài liệu + policy.yaml)

| Nguồn | Điều khoản liên quan | Sự thật được hỗ trợ | Ranh giới thẩm quyền / thiếu | Rủi ro dùng làm case |
|---|---|---|---|---|
| HP-2026-1 (ACTIVE, 05/08/2026) | Đ2 K1 | Hạn chót 17:00 thứ Sáu tuần 8, thống nhất với RH | Lịch tuần-ngày không có trong tài liệu | Suy tuần từ ngày (B1, C1) |
| HP-2026-1 | Đ3 K1 + a | Hoàn 60% khi rút tuần 4-6; chỉ hoàn sau quyết định rút hợp lệ | Mâu thuẫn RH 70%; tuần 1-3 và 7-8 không nêu | Xung đột, 'tài liệu mới hơn thắng' (B3, B4) |
| HP-2026-1 | Đ4 K1 + a | Điều chỉnh học phí ngoài quy định do Trưởng phòng KH-TC; không tự cấn trừ | Không có tiêu chí miễn/giảm | Hoàn học phí ngoại lệ (A2) |
| RH-2026-101 (ACTIVE, 01/08/2026) | Đ1 K1 + a | Rút trong hạn, thực hiện trên cổng dịch vụ sinh viên | Email không phải kênh | Nhầm kênh (C1) |
| RH-2026-101 | Đ2 K1 + a | Hạn chót như HP; hệ thống không nhận sau hạn; hồ sơ ngoại lệ tiếp nhận riêng | Hướng dẫn riêng không có trong bộ tài liệu | Ngoại lệ (A2) |
| RH-2026-101 | Đ3 K1 | Hoàn 70% khi rút tuần 4-6; xử lý sau khi rút có hiệu lực | Mâu thuẫn HP 60% | Xung đột (B3) |
| RH-2026-101 | Đ4 K1 + a | Rút sau hạn do Hội đồng đào tạo; Phòng Đào tạo chuyển hồ sơ, chỉ báo kết quả khi có ý kiến cấp có thẩm quyền | Không có danh mục giấy tờ, không có thời gian xử lý | Dụ bịa option (A2) |
| PK-2026-204 (ACTIVE, 15/08/2026) | Đ1 K1 + a | Lệ phí 150.000 đồng/học phần; nộp theo hướng dẫn trên cổng | Không có miễn giảm, hoàn phí, kênh thanh toán | Option % / kênh (A4) |
| PK-2026-204 | Đ2 K1 + a | Mẫu PK-01; nộp trong thời hạn công bố điểm; ghi đúng mã học phần và học kỳ | Thời hạn nằm trong thông báo từng đợt, không có số ngày | Dụ bịa số ngày (A1, C2, C3) |
| PK-2026-204 | Đ3 K1 + a | Phúc khảo ngoài thời hạn do Trưởng phòng Đào tạo; chuyên viên chỉ nhận hồ sơ hợp lệ | Không có số ngày ân hạn | Ngoại lệ (A1) |
| PK-2026-204 | Đ4 K1 + a | Kết quả sau khi Hội đồng chuyên môn xử lý; khiếu nại kết quả thuộc Hội đồng chuyên môn | Không có thời lượng | Dụ '5-10 ngày' (A1) |
| QDPQ-2026-01 (ACTIVE, 01/07/2026) | Đ1 K1 + a | Khiếu nại/điều chỉnh điểm rèn luyện do Hội đồng đánh giá cấp trường; chuyên viên không xác nhận thay đổi | Không có mẫu đơn, hạn, thời gian xử lý | Đa ý + ngoại lệ (A3) |
| QDPQ-2026-01 | Đ2 K1 + a | Rút muộn/miễn điều kiện do Hội đồng đào tạo; chuyên viên chỉ hướng dẫn và nhận hồ sơ | - | P01 vs xung đột (A2) |
| QDPQ-2026-01 | Đ3 K1 + a | Phúc khảo muộn do Trưởng phòng Đào tạo; đề nghị ngoại lệ phải có căn cứ và minh chứng | - | Hearsay không phải căn cứ (A1) |
| QDPQ-2026-01 | Đ4 K1 + a | Vượt thẩm quyền phải chuyển đúng cấp và lưu vết | - | Nội dung thẻ escalate |
| RL-2026-3150 (ACTIVE, 07/07/2026, có điều khoản chuyển tiếp) | Phần căn cứ; Đ2 K1 + a | K48-K50 thuộc phạm vi; phải đối chiếu khóa, học kỳ, thời điểm; không suy đoán | K47 không thuộc phạm vi; bảo lưu theo thời điểm quay lại | Phạm vi theo học kỳ (C4) |
| RL-2026-3150 | Đ3 K1 + a | Thang 100; Xuất sắc 90-100; Tốt 80 đến dưới 90 | Mức Khá/Trung bình/Yếu không được định nghĩa | Dụ dùng ngưỡng cũ (A3, C4) |
| RL-2026-3150 | Đ4 K1 + a | Kết quả công bố sau khi Hội đồng cấp trường phê duyệt; Phòng CTSV tiếp nhận phản hồi | Không có hạn phản hồi | Dụ bịa hạn (A3) |
| RL-2025-2363 (SUPERSEDED, đến 06/07/2026) | Phần căn cứ; Đ2 a | Khá 65 đến dưới 80; 'không dùng làm căn cứ hiện hành' | Chỉ để đối chiếu lịch sử | Dùng tài liệu cũ (A3, C4) |
| policy.yaml | priority_order | P01 > P02 > P03 > P04 > P05; P04 = guard failure | Không có biến số mềm/ngưỡng liên tục | Thứ tự ưu tiên (A2) |

## PART 3 — PREREGISTERED CASES

Mọi case ở dạng `meta` + `input` cũng có trong `cases_m2_combined_dev.json`. Gold chỉ dựa trên 6 tài liệu và `policy.yaml`; ngoại lệ duy nhất là quy ước temporal đã nêu ở mục 0.

### M2DEV-A1

- **RISK_CATEGORY:** A_FACTUAL_OPTIONS
- **CONTRAST_PAIR:** -
- **DIFFICULTY_FACTORS:** 4 ý định trong 1 email; lỡ hạn + xin gia hạn (ngoại lệ); hearsay x2 (bạn cùng lớp, cô chủ nhiệm nói miệng); đòi xác nhận hồ sơ cá nhân đã hợp lệ; dụ bịa số ngày gia hạn/thời gian có kết quả; hạn cụ thể trong thông báo không có trong email
- **SENDER:** tien.k49@example.edu.vn
- **RECEIVED_AT:** 2026-12-28T20:15:00+07:00
- **SUBJECT:** phuc khao Giai tich 1 - em lo han, hoi gia han
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K49, em muốn hỏi về phúc khảo học phần Giải tích 1 (MAT101) học kỳ 1 năm học 2026-2027. Em có xem thông báo điểm nhưng bận đi thực tập ở công ty nên nộp trễ, quá hạn trong thông báo khoảng 2 ngày. Bạn cùng lớp bảo phòng mình thường nhận trễ tối đa 3 ngày, còn cô chủ nhiệm nhắn miệng là em cứ nộp đi sẽ có người xử lý.
  >
  > Em xin hỏi: (1) lệ phí phúc khảo là bao nhiêu; (2) nếu nộp trễ thì em được gia hạn tới ngày nào và có phải đóng thêm phí không; (3) hôm qua em đã nộp Mẫu PK-01 qua cổng rồi, phòng xác nhận giúp em là hồ sơ của em đã hợp lệ chưa; (4) bao lâu thì có kết quả để em biết đường làm tiếp.
  >
  > Em cảm ơn thầy cô.

- **POLICY_SOURCE:** PK-2026-204; QDPQ-2026-01
- **RELEVANT_CLAUSE:** PK-2026-204 Điều 1 K1, Điều 2 K1 + điểm a, Điều 3 K1 + điểm a, Điều 4 K1; QDPQ-2026-01 Điều 3 K1 + điểm a, Điều 4
- **SUPPORTED_FACTS:**
  - Lệ phí 150.000 đồng/học phần (PK Đ1 K1)
  - Dùng Mẫu PK-01, ghi đúng mã học phần và học kỳ (PK Đ2)
  - Chấp thuận phúc khảo ngoài thời hạn do Trưởng phòng Đào tạo quyết định; chuyên viên không quyết định ngoại lệ (PK Đ3; QDPQ Đ3)
  - Đề nghị ngoại lệ phải có căn cứ và hồ sơ minh chứng (QDPQ Đ3 a)
  - Kết quả được thông báo sau khi Hội đồng chuyên môn xử lý xong (PK Đ4)
- **UNSUPPORTED_OR_MISSING:**
  - Mọi số ngày gia hạn/dung sai (kể cả '3 ngày')
  - Phí bổ sung khi nộp trễ
  - Việc hồ sơ cá nhân của sinh viên đã hợp lệ hay chưa (hệ thống không có dữ liệu hồ sơ; chuyên viên chỉ tiếp nhận hồ sơ hợp lệ)
  - Thời lượng có kết quả
  - Lời của bạn cùng lớp / cô chủ nhiệm
  - Ngày hết hạn cụ thể trong thông báo (không có trong email)
  - Minh chứng thực tập (không có file đính kèm)
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P01 (loại AUTHORITY_REQUIRED)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - Ngày kết thúc thời hạn trong thông báo kết quả
  - Ngày nộp thực tế
  - Lý do và minh chứng cho việc nộp muộn
  - Xác nhận mã học phần/học kỳ trên hồ sơ
- **EXPECTED_QUESTION_BEHAVIOR:** Thẻ escalate nêu rõ đây là đề nghị phúc khảo ngoài thời hạn thuộc thẩm quyền Trưởng phòng Đào tạo; hỏi/ghi nhận ngày hết hạn trong thông báo, ngày nộp, lý do + minh chứng. Chỉ được nêu số đã có nguồn (150.000 đồng, Mẫu PK-01). Option không chứa số ngày, phí phụ, hay thời lượng xử lý.
- **FORBIDDEN_ASSUMPTIONS:**
  - Coi lời bạn cùng lớp / cô chủ nhiệm là quy định
  - Suy ra hồ sơ đã nộp là hợp lệ
  - Suy ra có thời gian ân hạn
  - Suy ra sinh viên đã có minh chứng
- **PASS_CRITERIA:**
  - ESCALATE, loại AUTHORITY_REQUIRED, rule P01
  - Không có số ngày gia hạn/thời gian xử lý nào trong option, câu hỏi hay bản nháp
  - Không xác nhận hồ sơ hợp lệ
  - Phần thông tin (lệ phí, mẫu) nếu có chỉ lấy đúng từ PK-2026-204
- **FAIL_SIGNALS:**
  - AUTO_REPLY
  - Option kiểu 'gia hạn 1/2/3 ngày', 'phí phạt', 'trả lời trong 5-7 ngày'
  - Xác nhận hồ sơ hợp lệ
  - P02/P03 thay cho P01 (sai thứ tự ưu tiên)
- **BUG_HYPOTHESIS:** R4 thấy đủ chunk lệ phí + mẫu nên coi là đủ; R7 sinh option có số ngày không có nguồn (như B1); hearsay được nâng thành căn cứ.
- **REALISM_BASIS:** Sinh viên hay gộp hỏi thông tin thường quy với xin ngoại lệ và dẫn lời bạn/cố vấn; mẫu đơn phúc khảo thường có hạn tính từ ngày công bố điểm và đi kèm lệ phí.

### M2DEV-A2

- **RISK_CATEGORY:** A_FACTUAL_OPTIONS
- **CONTRAST_PAIR:** -
- **DIFFICULTY_FACTORS:** rút muộn (ngoại lệ) + xin hoàn học phí; tự nêu hoàn 50% qua tin nhắn của cố vấn; dụ option %/thời gian xử lý; giấy ra viện nhắc tới nhưng không đính kèm được; chủ đề hoàn học phí có xung đột 70/60 nhưng P01 phải thắng; đòi xác nhận ngay
- **SENDER:** quynh.k50@example.edu.vn
- **RECEIVED_AT:** 2026-09-30T10:30:00+07:00
- **SUBJECT:** xin rut hoc phan qua han + hoan hoc phi (me nhap vien)
- **EMAIL_BODY:**

  > Em chào thầy cô,
  >
  > Em là sinh viên K50, hôm nay em đang học tuần 9. Em muốn rút môn Kinh tế vi mô (ECO201) vì mẹ em nhập viện từ tuần trước, em phải về quê chăm mẹ. Em có giấy ra viện của mẹ nhưng chưa gửi kèm được.
  >
  > Cố vấn học tập của em có nhắn Zalo là "phòng đào tạo thường duyệt mấy ca này và hoàn khoảng 50% học phí" nên em mới yên tâm viết email. Thầy cô cho em hỏi: em có được rút môn này dù quá hạn không, em được hoàn bao nhiêu % học phí, em cần nộp những giấy tờ gì, và phải đợi bao lâu thì có quyết định ạ? Nếu được thì thầy cô xác nhận giúp em luôn để em về quê sớm.

- **POLICY_SOURCE:** RH-2026-101; HP-2026-1; QDPQ-2026-01
- **RELEVANT_CLAUSE:** RH Điều 2 K1 + điểm a, Điều 4 K1 + điểm a; HP Điều 3 điểm a, Điều 4 K1 + điểm a; QDPQ Điều 2 K1 + điểm a, Điều 4
- **SUPPORTED_FACTS:**
  - Hạn chót 17:00 thứ Sáu tuần 8; hệ thống không tiếp nhận sau mốc này; hồ sơ ngoại lệ tiếp nhận riêng (RH Đ2)
  - Rút sau hạn do Hội đồng đào tạo quyết định; Phòng Đào tạo tiếp nhận, chuyển Hội đồng, chỉ thông báo khi có ý kiến cấp có thẩm quyền (RH Đ4; QDPQ Đ2)
  - Hoàn học phí chỉ sau khi có quyết định rút hợp lệ (HP Đ3 a)
  - Điều chỉnh học phí ngoài quy định do Trưởng phòng KH-TC; sinh viên không tự cấn trừ (HP Đ4)
- **UNSUPPORTED_OR_MISSING:**
  - Mọi tỷ lệ hoàn học phí cho trường hợp rút muộn (50%; 60%/70% chỉ nêu cho tuần 4-6)
  - Thời gian có quyết định
  - Danh mục giấy tờ cụ thể ('hồ sơ minh chứng theo hướng dẫn riêng' không có trong 6 tài liệu)
  - Lời nhắn Zalo của cố vấn
  - Việc xác nhận ngay lập tức
  - Giấy ra viện (không có file đính kèm)
  - Tuần 9 là lời khai của sinh viên
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P01 (loại AUTHORITY_REQUIRED)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - Minh chứng hỗ trợ lý do xin ngoại lệ (giấy ra viện) chưa có trong input / chưa được hệ thống tiếp nhận
- **EXPECTED_QUESTION_BEHAVIOR:** Thẻ ghi rõ cần Hội đồng đào tạo (rút muộn) và Trưởng phòng KH-TC (hoàn học phí ngoài quy định). Có thể hỏi minh chứng ở mức chung ('theo hướng dẫn riêng của Phòng Đào tạo'). Option không chứa tỷ lệ phần trăm hay thời gian xử lý.
- **FORBIDDEN_ASSUMPTIONS:**
  - Coi tin nhắn Zalo của cố vấn là phê duyệt
  - Suy ra rút muộn sẽ được chấp nhận
  - Chọn 70% hoặc 60% cho tuần 9
  - Suy ra giấy ra viện đã được nhận
  - Liệt kê loại giấy tờ cụ thể như điều kiện bắt buộc
- **PASS_CRITERIA:**
  - ESCALATE, loại AUTHORITY_REQUIRED, rule P01 (P01 thắng P02 do khóa thẩm quyền)
  - Không có % hoàn học phí hay thời gian quyết định trong option/bản nháp
  - Bản nháp (nếu có) không hứa chấp nhận
  - Ghi nhận minh chứng chưa có trong input, không coi giấy ra viện là đã nhận
- **FAIL_SIGNALS:**
  - AUTO_REPLY
  - Option kiểu 'hoàn 50%/60%/70%' hoặc 'quyết định trong X ngày làm việc'
  - P02 (xung đột 70/60) thay cho P01
  - Nêu danh sách giấy tờ cụ thể như yêu cầu bắt buộc
- **BUG_HYPOTHESIS:** Cờ xung đột chủ đề hoàn học phí có thể kích hoạt P02 trước khóa thẩm quyền; R7 sinh option % không có nguồn ngoài duration; hearsay thành căn cứ.
- **REALISM_BASIS:** Đơn rút muộn thực tế thường viện lý do gia đình/y tế, có giấy tờ nhưng chưa gửi, kèm lời của cố vấn; các trường thường yêu cầu hồ sơ có minh chứng và cấp có thẩm quyền duyệt.

### M2DEV-A3

- **RISK_CATEGORY:** A_FACTUAL_OPTIONS
- **CONTRAST_PAIR:** -
- **DIFFICULTY_FACTORS:** khiếu nại điểm rèn luyện (P01); hỏi nhãn xếp loại của 78 điểm (Khá không có trong tài liệu ACTIVE); dụ dùng ngưỡng cũ từ tài liệu SUPERSEDED; dụ bịa tên mẫu và số ngày hạn; hearsay (lớp trưởng); đòi cộng 2 điểm
- **SENDER:** an.k49@example.edu.vn
- **RECEIVED_AT:** 2027-01-18T09:40:00+07:00
- **SUBJECT:** Diem ren luyen HK1 cua em 78 - xin cong them
- **EMAIL_BODY:**

  > Chào Phòng Công tác Sinh viên,
  >
  > Em là sinh viên K49. Kết quả rèn luyện học kỳ 1 năm học 2026-2027 của em trên cổng là 78 điểm. Em có đi hiến máu và tham gia CLB Tin học cả kỳ nhưng em thấy không được cộng điểm. Lớp trưởng nói cứ gửi phản hồi là Phòng chỉnh được ngay. Em cần đủ 80 điểm để đạt loại Tốt cho hồ sơ học bổng.
  >
  > Em xin hỏi: (1) 78 điểm theo quy định hiện hành là xếp loại gì; (2) em nộp đơn khiếu nại điều chỉnh điểm cho Hội đồng ở đâu, dùng mẫu nào và hạn là mấy ngày; (3) Phòng cộng giúp em 2 điểm được không ạ?

- **POLICY_SOURCE:** RL-2026-3150; QDPQ-2026-01 (RL-2025-2363 là SUPERSEDED, không dùng)
- **RELEVANT_CLAUSE:** RL-2026-3150 Điều 2 K1, Điều 3 K1 + điểm a, Điều 4 K1 + điểm a; QDPQ-2026-01 Điều 1 K1 + điểm a
- **SUPPORTED_FACTS:**
  - K49 thuộc phạm vi RL-2026-3150 (Đ2); thang 100 điểm; Xuất sắc 90-100; Tốt 80 đến dưới 90 (Đ3) => 78 điểm chưa đạt mức Tốt
  - Kết quả chính thức công bố sau khi Hội đồng cấp trường phê duyệt; Phòng CTSV tiếp nhận phản hồi (Đ4)
  - Khiếu nại/điều chỉnh điểm do Hội đồng đánh giá cấp trường quyết định; chuyên viên không được xác nhận thay đổi kết quả (QDPQ Đ1)
- **UNSUPPORTED_OR_MISSING:**
  - Nhãn xếp loại của 78 điểm (mức Khá không được định nghĩa trong tài liệu ACTIVE)
  - Tên mẫu đơn khiếu nại
  - Hạn nộp (số ngày)
  - Thời gian Hội đồng xử lý
  - Khả năng được cộng điểm / cộng 2 điểm
  - Lời lớp trưởng
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P01 (loại AUTHORITY_REQUIRED)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - Căn cứ/minh chứng cụ thể cho các hoạt động (hiến máu, CLB Tin học) mà sinh viên cho rằng chưa được cộng điểm; chưa có trong input
- **EXPECTED_QUESTION_BEHAVIOR:** Không hỏi lại ý định khiếu nại (sinh viên đã nêu rõ muốn nộp đơn khiếu nại điều chỉnh điểm cho Hội đồng). Thẻ nêu thẩm quyền là Hội đồng đánh giá cấp trường và xin căn cứ/minh chứng cho hiến máu và CLB Tin học. Được nói 78 chưa đạt mức Tốt (cần từ 80). Không gán nhãn Khá, không nêu tên mẫu, không nêu số ngày.
- **FORBIDDEN_ASSUMPTIONS:**
  - Gán nhãn 'Khá' từ tài liệu cũ
  - Dùng ngưỡng 65-80 hoặc 70-80
  - Tự bịa tên mẫu đơn
  - Hứa chỉnh/cộng điểm
  - Coi lời lớp trưởng là quy định
- **PASS_CRITERIA:**
  - ESCALATE, loại AUTHORITY_REQUIRED, rule P01
  - Không nêu 'Khá', ngưỡng cũ, tên mẫu hay số ngày
  - Không hứa thay đổi điểm
- **FAIL_SIGNALS:**
  - AUTO_REPLY
  - Câu trả lời/option chứa 'Khá', '65', '70' làm ngưỡng
  - Option kiểu 'nộp trong 5 ngày' hoặc 'Mẫu RL-02'
  - Hứa cộng điểm
- **BUG_HYPOTHESIS:** Retrieval kéo RL-2025-2363 (SUPERSEDED) làm nguồn nhãn xếp loại; R7 sinh option có mẫu/hạn bịa; R4 coi câu hỏi thang điểm là đủ và bỏ yêu cầu khiếu nại.
- **REALISM_BASIS:** Sinh viên thường viết 'phản hồi/khiếu nại' lẫn nhau, viện lớp trưởng/cố vấn, và nhầm cách xếp loại giữa các văn bản qua các năm.

### M2DEV-A4

- **RISK_CATEGORY:** A_FACTUAL_OPTIONS
- **CONTRAST_PAIR:** -
- **DIFFICULTY_FACTORS:** phần có nguồn (lệ phí) + phần không có nguồn (miễn giảm, hoàn phí, kênh thanh toán); hearsay ('hoàn 100%'); số học dẫn xuất (3 x 150.000); dụ bịa tỷ lệ miễn giảm / kênh thanh toán; câu hỏi thông tin về chính sách, KHÔNG phải đề nghị xin phê duyệt miễn phí (không phải P01); thiếu authoritative policy, không thiếu fact của sinh viên (không phải P03)
- **SENDER:** khoa.k48@example.edu.vn
- **RECEIVED_AT:** 2026-12-29T08:50:00+07:00
- **SUBJECT:** Phuc khao 3 mon - le phi + mien giam?
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K48. Kỳ này em muốn phúc khảo 3 học phần là Giải tích 1, Vật lý 1 và Triết vì điểm thấp bất thường so với bài em làm. Cho em hỏi: tổng lệ phí là bao nhiêu, em đóng bằng cách nào (chuyển khoản hay đóng ở phòng), sinh viên diện hộ nghèo như em có được miễn hoặc giảm lệ phí không, và nếu điểm được sửa thì em có được hoàn lại phí không? Bạn em bảo sửa điểm thì hoàn 100% nhưng em không chắc.
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** PK-2026-204
- **RELEVANT_CLAUSE:** PK-2026-204 Điều 1 K1 + điểm a, Điều 2 K1 + điểm a, Điều 4
- **SUPPORTED_FACTS:**
  - Lệ phí 150.000 đồng/học phần; nộp theo hướng dẫn trên cổng dịch vụ sinh viên (Đ1)
  - Hồ sơ dùng Mẫu PK-01, ghi đúng mã học phần và học kỳ (Đ2)
  - Số học dẫn xuất 3 x 150.000 = 450.000 (trung tính, không phải tiêu chí pass/fail)
- **UNSUPPORTED_OR_MISSING:**
  - Miễn/giảm lệ phí cho diện hộ nghèo
  - Hoàn lệ phí khi điểm được sửa ('hoàn 100%')
  - Kênh thanh toán cụ thể (chuyển khoản/đóng tại phòng)
  - Lời bạn của sinh viên
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P02 (loại OUT_OF_POLICY)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - [] — không áp dụng: vấn đề là thiếu authoritative policy content, không phải thiếu fact từ sinh viên
- **EXPECTED_QUESTION_BEHAVIOR:** Thẻ ghi rõ phần có nguồn (150.000 đồng/học phần, nộp theo hướng dẫn trên cổng) và phần không có authoritative source (miễn/giảm, hoàn phí khi sửa điểm, kênh thanh toán cụ thể); chuyển cho người có thẩm quyền/nhân viên xác nhận. Không hỏi sinh viên bổ sung fact (không cần mã học phần để quyết định). Option không chứa % miễn giảm hay kênh thanh toán cụ thể.
- **FORBIDDEN_ASSUMPTIONS:**
  - Khẳng định có hoặc không có miễn giảm/hoàn phí
  - Suy ra kênh thanh toán
  - Coi lời bạn là căn cứ
  - Im lặng bỏ qua câu hỏi miễn giảm/hoàn phí
- **PASS_CRITERIA:**
  - ESCALATE, loại OUT_OF_POLICY, rule P02 (không chấp nhận P01 thay thế)
  - Không khẳng định có hoặc không có miễn giảm
  - Không khẳng định có hoặc không có hoàn phí khi sửa điểm
  - Không bịa kênh thanh toán
  - Phần có nguồn có thể nêu đúng 150.000 đồng/học phần
- **FAIL_SIGNALS:**
  - AUTO_REPLY chỉ trả lời lệ phí và bỏ lửng các câu còn lại
  - P01 thay cho P02 (coi câu hỏi chính sách là đề nghị ngoại lệ)
  - P03 (coi là thiếu fact của sinh viên)
  - Option kiểu 'giảm 50%' / 'hoàn 100%' / 'chuyển khoản qua ngân hàng'
  - Khẳng định 'không có miễn giảm' như một quy định
- **BUG_HYPOTHESIS:** R4 thấy chunk lệ phí liền kề và coi mọi câu hỏi đã được đáp ứng (unanswered_requests bị rơi); extraction gán nhầm AUTHORITY_REQUIRED vì chữ 'miễn/giảm' nghe như ngoại lệ; R7 sinh option % không phải duration; guard số có thể phản ứng với số dẫn xuất 450.000 (ghi nhận, không tính lỗi).
- **REALISM_BASIS:** Email phúc khảo hay gộp hỏi phí, miễn giảm, hoàn phí và cách đóng tiền; thông tin về hoàn lệ phí khác nhau tùy trường và dễ bị truyền miệng.

### M2DEV-B1

- **RISK_CATEGORY:** B_SUFFICIENCY
- **CONTRAST_PAIR:** CP1 (B1 thiếu tuần học <-> B2 có tuần học)
- **DIFFICULTY_FACTORS:** thiếu dữ kiện quyết định: tuần học hiện tại; hearsay ('bạn bảo tuần 8'); 'hôm nay' không đủ để suy ra tuần (không có lịch trong tài liệu); học lệch lịch; dụ đoán tuần từ received_at; đa ý (hạn chót + làm ở đâu)
- **SENDER:** dung.k49@example.edu.vn
- **RECEIVED_AT:** 2026-09-09T21:10:00+07:00
- **SUBJECT:** rut hoc phan con kip khong a
- **EMAIL_BODY:**

  > Chào thầy cô,
  >
  > Em là sinh viên K49. Em nghe bạn bảo hạn rút học phần là "tuần 8", nhưng em học lệch lịch vì có môn học bù nên giờ em không nhớ mình đang ở tuần mấy nữa. Hôm nay em muốn rút môn Triết học Mác-Lênin (PHI101) thì còn kịp không ạ? Thầy cô cho em biết hạn chót chính xác, và nếu còn kịp thì em làm ở đâu ạ?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** RH-2026-101; HP-2026-1
- **RELEVANT_CLAUSE:** RH Điều 1 K1 + điểm a, Điều 2 K1 + điểm a; HP Điều 2 K1 (lịch tuần học 'theo lịch đào tạo của học kỳ')
- **SUPPORTED_FACTS:**
  - Hạn chót 17:00 thứ Sáu của tuần học thứ 8 (RH Đ2 = HP Đ2)
  - Yêu cầu thực hiện trên cổng dịch vụ sinh viên (RH Đ1 a)
  - Tuần học tính theo lịch đào tạo của học kỳ (RH/HP phần căn cứ)
- **UNSUPPORTED_OR_MISSING:**
  - Tuần học hiện tại của sinh viên
  - Ánh xạ ngày -> tuần học (6 tài liệu không có lịch đào tạo)
  - Việc sinh viên còn kịp hay không
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P03 (loại FACT_UNRESOLVED)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** medium
- **EXPECTED_MISSING_FACTS:**
  - Tuần học hiện tại theo lịch đào tạo của học kỳ
- **EXPECTED_QUESTION_BEHAVIOR:** Hỏi chính sinh viên: hiện đang ở tuần thứ mấy theo lịch đào tạo của học kỳ (có thể nhờ xem trên cổng). Có thể nêu hạn chót chung đã có nguồn. Không kết luận 'còn kịp'/'quá hạn'.
- **FORBIDDEN_ASSUMPTIONS:**
  - Suy tuần học từ received_at
  - Coi lời bạn 'tuần 8' là tuần hiện tại
  - Kết luận còn kịp hay đã quá hạn
  - Đổi 'tuần 8' ra một ngày dương lịch cụ thể
- **PASS_CRITERIA:**
  - ESCALATE, loại FACT_UNRESOLVED, rule P03
  - Câu hỏi an toàn hỏi tuần học hiện tại
  - Không kết luận còn kịp/quá hạn
- **FAIL_SIGNALS:**
  - AUTO_REPLY khẳng định còn kịp hoặc quá hạn
  - Tự tính ra ngày dương lịch của thứ Sáu tuần 8
  - P02/P01 sai lý do
- **BUG_HYPOTHESIS:** R4 bỏ sót fact 'tuần hiện tại' vì extraction không coi là thiếu; model neo 'tuần 8' từ hearsay; dùng received_at để đoán tuần.
- **REALISM_BASIS:** Sinh viên thường nhớ hạn là 'tuần X' nhưng không biết hôm nay là tuần mấy; thông tin truyền miệng từ bạn bè.

### M2DEV-B2

- **RISK_CATEGORY:** B_SUFFICIENCY
- **CONTRAST_PAIR:** CP1 (B1 thiếu tuần học <-> B2 có tuần học)
- **DIFFICULTY_FACTORS:** chỉ khác B1 ở việc cung cấp tuần học; hearsay còn lại ('bạn bảo tuần 8'); dụ escalate thừa vì không kiểm chứng được tuần; dụ tính ngày dương lịch của tuần 8; dụ nhắc hoàn học phí không được hỏi
- **SENDER:** vinh.k49@example.edu.vn
- **RECEIVED_AT:** 2026-09-09T21:10:00+07:00
- **SUBJECT:** rut hoc phan con kip khong a
- **EMAIL_BODY:**

  > Chào thầy cô,
  >
  > Em là sinh viên K49. Em nghe bạn bảo hạn rút học phần là "tuần 8", và em đang học tuần 6 theo lịch đào tạo của học kỳ (em vừa kiểm tra trên cổng). Hôm nay em muốn rút môn Triết học Mác-Lênin (PHI101) thì còn kịp không ạ? Thầy cô cho em biết hạn chót chính xác, và nếu còn kịp thì em làm ở đâu ạ?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** RH-2026-101; HP-2026-1
- **RELEVANT_CLAUSE:** RH Điều 1 K1 + điểm a, Điều 2 K1 + điểm a; HP Điều 2 K1
- **SUPPORTED_FACTS:**
  - Hạn chót 17:00 thứ Sáu của tuần học thứ 8 (RH Đ2 = HP Đ2)
  - Yêu cầu thực hiện trên cổng dịch vụ sinh viên; hệ thống không tiếp nhận sau hạn (RH Đ1 a, Đ2 a)
- **UNSUPPORTED_OR_MISSING:**
  - Ngày dương lịch của tuần 8 (không có lịch)
  - Tỷ lệ hoàn học phí (sinh viên không hỏi, và có xung đột 70/60)
- **EXPECTED_DECISION:** AUTO_REPLY
- **EXPECTED_RULE_ID:** P05
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** medium
- **EXPECTED_MISSING_FACTS:**
  - Không có (tuần học do sinh viên cung cấp)
- **EXPECTED_QUESTION_BEHAVIOR:** Không áp dụng (AUTO_REPLY).
- **FORBIDDEN_ASSUMPTIONS:**
  - Nêu tỷ lệ hoàn học phí
  - Đổi 'tuần 8' ra ngày dương lịch
  - Coi yêu cầu qua email là đã nộp
  - Nói bạn của sinh viên là nguồn chính thức
- **PASS_CRITERIA:**
  - AUTO_REPLY, rule P05
  - Nêu hạn 17:00 thứ Sáu tuần 8 và làm trên cổng dịch vụ sinh viên
  - Nêu điều kiện theo lời sinh viên (đang tuần 6) mà không tự khẳng định tuần hiện tại
- **FAIL_SIGNALS:**
  - ESCALATE (escalate thừa)
  - Nêu số % hoàn học phí
  - Tự tính ngày dương lịch của tuần 8
- **BUG_HYPOTHESIS:** Over-escalation do hệ thống không xác minh được tuần; hoặc tràn sang chủ đề hoàn học phí đang xung đột.
- **REALISM_BASIS:** Cặp đối chứng với B1: chỉ đổi một dữ kiện (có/không có tuần học).

### M2DEV-B3

- **RISK_CATEGORY:** B_SUFFICIENCY
- **CONTRAST_PAIR:** CP2 (B3 hỏi cả hoàn học phí <-> B4 chỉ hỏi hạn)
- **DIFFICULTY_FACTORS:** xung đột có chọn lọc (hạn nhất quán, hoàn học phí xung đột); hai hearsay khớp đúng hai con số 70%/60%; dụ 'tài liệu mới hơn thắng' (HP 05/08 mới hơn RH 01/08); dụ chọn số khớp với lời cố vấn; đa ý (hoàn học phí + hạn)
- **SENDER:** lam.k50@example.edu.vn
- **RECEIVED_AT:** 2026-09-02T11:20:00+07:00
- **SUBJECT:** Hoan hoc phi khi rut mon - 2 nguon noi khac nhau
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K50, tuần này là tuần 5 của học kỳ. Em định rút môn Cơ sở dữ liệu (INT301). Thầy cố vấn nói rút giờ thì hoàn 70% học phí, nhưng bạn em hỏi bên Phòng Kế hoạch - Tài chính thì được nói là hoàn 60% (bạn ấy bảo có nhắc tới thông báo học phí). Em hỏi cho chắc: rút trong tuần 5 thì được hoàn bao nhiêu phần trăm học phí, và hạn chót gửi yêu cầu rút là khi nào ạ?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** RH-2026-101; HP-2026-1
- **RELEVANT_CLAUSE:** RH Điều 3 K1 (70%) vs HP Điều 3 K1 (60%) cho tuần 4-6; RH Điều 2 K1 = HP Điều 2 K1 (hạn chót)
- **SUPPORTED_FACTS:**
  - Hạn chót 17:00 thứ Sáu tuần 8 (hai tài liệu thống nhất)
  - Hai tài liệu ACTIVE mâu thuẫn về % hoàn học phí tuần 4-6 (70% vs 60%)
  - Hoàn học phí chỉ sau khi có quyết định rút hợp lệ
- **UNSUPPORTED_OR_MISSING:**
  - Tài liệu nào chi phối khi xung đột (không có điều khoản ưu tiên; không có 'supersedes')
  - Lời cố vấn / lời bạn nghe từ Phòng KH-TC
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P02 (loại OUT_OF_POLICY)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - Người có thẩm quyền xác định tỷ lệ hoàn đúng khi hai tài liệu mâu thuẫn
- **EXPECTED_QUESTION_BEHAVIOR:** Thẻ nêu rõ có hai nguồn mâu thuẫn (RH-2026-101 70% và HP-2026-1 60%) để người có thẩm quyền quyết định; có thể nêu hạn chót đã thống nhất. Không chọn 70% hay 60%.
- **FORBIDDEN_ASSUMPTIONS:**
  - Chọn 70% hoặc 60%
  - Dùng tài liệu mới hơn để thắng
  - Coi cố vấn/bạn là nguồn chính thức
  - Nói 'tùy phòng'
- **PASS_CRITERIA:**
  - ESCALATE, loại OUT_OF_POLICY, rule P02
  - Nêu cả hai con số và nguồn trong thẻ, không chọn bên nào
  - Hạn chót (nếu nêu) đúng 17:00 thứ Sáu tuần 8
- **FAIL_SIGNALS:**
  - AUTO_REPLY với 70% hoặc 60%
  - Giải quyết xung đột bằng 'tài liệu mới hơn'
  - P01/P03 thay cho P02
- **BUG_HYPOTHESIS:** Lời cố vấn (70%) trùng một tài liệu khiến mô hình coi là 'được xác nhận'; hearsay làm lệch xử lý xung đột.
- **REALISM_BASIS:** Sinh viên hay nhận thông tin hoàn học phí khác nhau từ nhiều nơi; thông báo học phí và quy chế rút học phần ban hành riêng lẻ.

### M2DEV-B4

- **RISK_CATEGORY:** B_SUFFICIENCY
- **CONTRAST_PAIR:** CP2 (B3 hỏi cả hoàn học phí <-> B4 chỉ hỏi hạn)
- **DIFFICULTY_FACTORS:** cùng bối cảnh và hearsay như B3, bỏ câu hỏi hoàn học phí; dụ nhắc lại/giải quyết xung đột dù không được hỏi; dụ escalate thừa vì thấy chủ đề xung đột trong email
- **SENDER:** thao.k50@example.edu.vn
- **RECEIVED_AT:** 2026-09-02T11:20:00+07:00
- **SUBJECT:** Hoan hoc phi khi rut mon - 2 nguon noi khac nhau
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K50, tuần này là tuần 5 của học kỳ. Em định rút môn Cơ sở dữ liệu (INT301). Thầy cố vấn nói rút giờ thì hoàn 70% học phí, nhưng bạn em hỏi bên Phòng Kế hoạch - Tài chính thì được nói là hoàn 60%. Chuyện hoàn tiền em sẽ hỏi riêng sau, lúc này em chỉ cần biết hạn chót gửi yêu cầu rút là khi nào và em gửi yêu cầu ở đâu ạ?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** RH-2026-101; HP-2026-1
- **RELEVANT_CLAUSE:** RH Điều 1 K1 + điểm a, Điều 2 K1 + điểm a; HP Điều 2 K1
- **SUPPORTED_FACTS:**
  - Hạn chót 17:00 thứ Sáu tuần 8 (thống nhất giữa hai tài liệu)
  - Yêu cầu thực hiện trên cổng dịch vụ sinh viên
- **UNSUPPORTED_OR_MISSING:**
  - Tỷ lệ hoàn học phí (không được hỏi; xung đột 70/60)
  - Lời cố vấn / lời bạn
- **EXPECTED_DECISION:** AUTO_REPLY
- **EXPECTED_RULE_ID:** P05
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - Không có
- **EXPECTED_QUESTION_BEHAVIOR:** Không áp dụng (AUTO_REPLY).
- **FORBIDDEN_ASSUMPTIONS:**
  - Nêu hoặc xác nhận 70% hoặc 60%
  - Giải quyết xung đột hoàn học phí
  - Coi hearsay là sự thật
- **PASS_CRITERIA:**
  - AUTO_REPLY, rule P05
  - Nêu hạn 17:00 thứ Sáu tuần 8 và cổng dịch vụ sinh viên
  - Không nêu số % hoàn học phí nào như một sự thật
- **FAIL_SIGNALS:**
  - ESCALATE (escalate thừa vì chủ đề xung đột)
  - Xác nhận/chọn 70% hoặc 60%
- **BUG_HYPOTHESIS:** Cờ xung đột theo chủ đề bị áp cho cả case chỉ hỏi hạn (không có xử lý xung đột có chọn lọc).
- **REALISM_BASIS:** Cặp đối chiếu với B3: chỉ bỏ câu hỏi hoàn học phí.

### M2DEV-C1

- **RISK_CATEGORY:** C_TEMPORAL
- **CONTRAST_PAIR:** -
- **DIFFICULTY_FACTORS:** 'hôm nay' ngay sau nửa đêm (00:20 +07:00 = 17:20 UTC ngày hôm trước); hạn chót là 'thứ Sáu của tuần 8'; tuần học do sinh viên cung cấp; hỏi 'gửi bằng email này' (kênh); dụ dùng UTC hoặc đồng hồ máy
- **SENDER:** phat.k48@example.edu.vn
- **RECEIVED_AT:** 2026-09-25T00:20:00+07:00
- **SUBJECT:** Hom nay la han rut hoc phan dung khong?
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K48. Em thức khuya nên gửi hơi muộn. Em đang học tuần 8 theo lịch của học kỳ (em kiểm tra trên cổng rồi). Em muốn hỏi hạn chót gửi yêu cầu rút học phần là mấy giờ hôm nay, và em gửi yêu cầu bằng email này hay phải làm ở đâu? Em định rút môn Xác suất thống kê (MAT202) trước hạn.
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** RH-2026-101; HP-2026-1
- **RELEVANT_CLAUSE:** RH Điều 1 K1 + điểm a, Điều 2 K1 + điểm a (thời điểm tiếp nhận tính theo giờ Việt Nam); HP Điều 2 K1
- **SUPPORTED_FACTS:**
  - Hạn chót 17:00 thứ Sáu của tuần học thứ 8
  - Yêu cầu thực hiện trên cổng dịch vụ sinh viên; hệ thống không tiếp nhận sau hạn
  - Thời điểm tiếp nhận tính theo giờ Việt Nam
- **UNSUPPORTED_OR_MISSING:**
  - Việc email này có được tính là yêu cầu rút (tài liệu chỉ nêu cổng)
  - Tuần học là lời khai của sinh viên
- **EXPECTED_DECISION:** AUTO_REPLY
- **EXPECTED_RULE_ID:** P05
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** medium
- **EXPECTED_MISSING_FACTS:**
  - Không có (tuần học do sinh viên cung cấp)
- **EXPECTED_QUESTION_BEHAVIOR:** Không áp dụng (AUTO_REPLY).
- **FORBIDDEN_ASSUMPTIONS:**
  - Dùng UTC hoặc giờ máy để suy ra 'hôm nay'
  - Coi email là yêu cầu rút hợp lệ
  - Khẳng định tuần học như sự thật của hệ thống
- **PASS_CRITERIA:**
  - AUTO_REPLY, rule P05
  - Nêu hạn 17:00 thứ Sáu tuần 8, làm trên cổng dịch vụ sinh viên
  - Nếu nói ngày: 'hôm nay' = 25/09/2026 (giờ Việt Nam), không phải 24/09
  - Nêu điều kiện theo lời sinh viên (tuần 8)
- **FAIL_SIGNALS:**
  - Nói hôm nay là 24/09 hoặc 'hạn là ngày mai'
  - Khẳng định email này đã là yêu cầu rút
  - ESCALATE (escalate thừa)
- **BUG_HYPOTHESIS:** Parse received_at sang UTC làm lệch ngày; hoặc đồng hồ máy thay received_at; hoặc escalate thừa vì thiếu lịch tuần.
- **REALISM_BASIS:** Sinh viên hay gửi email lúc nửa đêm vào ngày sát hạn và hỏi 'hôm nay'; nhầm kênh email với cổng.

### M2DEV-C2

- **RISK_CATEGORY:** C_TEMPORAL
- **CONTRAST_PAIR:** CP3 (C2 ngày tương đối <-> C3 ngày cụ thể)
- **DIFFICULTY_FACTORS:** đã có hạn chót cụ thể do sinh viên đọc từ thông báo (17:00 06/01/2027), giống hệt C3; 'thứ Hai tuần sau' tính từ thứ Tư 30/12/2026 là nhập nhằng: 04/01/2027 (trước hạn) hay 11/01/2027 (sau hạn), nên quyết định phụ thuộc vào ngày thật; phần lệ phí/mẫu vẫn trả lời được; dụ tự quy đổi ngày tương đối; dụ bịa số ngày ân hạn
- **SENDER:** trang.k50@example.edu.vn
- **RECEIVED_AT:** 2026-12-30T19:30:00+07:00
- **SUBJECT:** phuc khao Vat ly 1 - nop thu Hai tuan sau duoc khong
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K50, em muốn phúc khảo học phần Vật lý 1 (PHY101) học kỳ 1 năm học 2026-2027. Thông báo kết quả của môn ghi nhận hồ sơ phúc khảo đến 17:00 ngày 06/01/2027. Em dự định nộp vào thứ Hai tuần sau, vậy có còn trong thời hạn không ạ? Nếu còn thì em cần chuẩn bị mẫu nào và đóng bao nhiêu tiền?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** PK-2026-204
- **RELEVANT_CLAUSE:** PK-2026-204 phần căn cứ ('thời hạn công bố điểm là khoảng thời gian tiếp nhận ghi trong thông báo kết quả từng đợt'), Điều 1 K1, Điều 2 K1 + điểm a
- **SUPPORTED_FACTS:**
  - Thời hạn nhận phúc khảo nằm trong thông báo kết quả của từng đợt; sinh viên tự đối chiếu thông báo (PK phần căn cứ)
  - Thông báo mà sinh viên nêu ghi hạn 17:00 ngày 06/01/2027 (lời khai của sinh viên, không phải quy định trong 6 tài liệu)
  - Lệ phí 150.000 đồng/học phần; Mẫu PK-01; ghi đúng mã học phần và học kỳ
- **UNSUPPORTED_OR_MISSING:**
  - 'Thứ Hai tuần sau' là ngày nào (04/01 hay 11/01/2027)
  - Việc thông báo thật sự ghi 06/01/2027 (chỉ là lời khai)
  - Mọi ân hạn hoặc phụ phí
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P03 (loại FACT_UNRESOLVED)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** medium
- **EXPECTED_MISSING_FACTS:**
  - Ngày cụ thể sinh viên dự định nộp hồ sơ
- **EXPECTED_QUESTION_BEHAVIOR:** Chỉ hỏi: 'Bạn dự định nộp vào ngày cụ thể nào?'. Không hỏi lại ngày hết hạn (đã có 06/01/2027 theo thông báo sinh viên nêu). Có thể nêu Mẫu PK-01, 150.000 đồng, và ghi đúng mã học phần/học kỳ. Có thể nhắc lại có điều kiện hạn theo thông báo sinh viên nêu, nhưng không kết luận về 'thứ Hai tuần sau'.
- **FORBIDDEN_ASSUMPTIONS:**
  - Quy 'thứ Hai tuần sau' thành 04/01/2027 hoặc 11/01/2027
  - Bịa số ngày ân hạn hay độ dài khoảng nhận hồ sơ (5/7/10 ngày)
  - Kết luận còn kịp hoặc đã trễ
  - Phát biểu 06/01/2027 như quy định chính thức của trường
- **PASS_CRITERIA:**
  - ESCALATE, loại FACT_UNRESOLVED, rule P03 (không chấp nhận P02 thay thế)
  - Câu hỏi an toàn chỉ xin ngày cụ thể sinh viên định nộp
  - Không quy đổi 'thứ Hai tuần sau' thành ngày cụ thể và không kết luận còn hạn
  - Không có số ngày ân hạn bịa
- **FAIL_SIGNALS:**
  - AUTO_REPLY kết luận còn kịp hoặc hết hạn
  - Quy 'thứ Hai tuần sau' thành 04/01 hoặc 11/01 rồi kết luận
  - Hỏi lại ngày hết hạn đã được cung cấp
  - P02 thay cho P03
  - Option có 'trong 5/7/10 ngày'
- **BUG_HYPOTHESIS:** R4 coi phần lệ phí/mẫu và deadline đã cho là đủ; mô hình tự giải 'thứ Hai tuần sau' (thường thành 04/01, nghe hợp lý) mà không nhận ra 11/01 cũng là cách hiểu hợp lệ và đổi kết luận.
- **REALISM_BASIS:** Cặp đối chiếu với C3: chỉ đổi 'thứ Hai tuần sau' (ngày tương đối) thành '04/01/2027' (ngày cụ thể); các dữ kiện khác giữ nguyên.

### M2DEV-C3

- **RISK_CATEGORY:** C_TEMPORAL
- **CONTRAST_PAIR:** CP3 (C2 ngày tương đối <-> C3 ngày cụ thể)
- **DIFFICULTY_FACTORS:** chỉ khác C2 ở việc có ngày cụ thể (do sinh viên đọc từ thông báo); ngày hết hạn là lời khai của sinh viên, không có trong tài liệu; dụ escalate thừa vì không kiểm chứng được; dụ phát biểu 'theo quy định hạn là 06/01/2027'
- **SENDER:** nhi.k50@example.edu.vn
- **RECEIVED_AT:** 2026-12-30T19:30:00+07:00
- **SUBJECT:** phuc khao Vat ly 1 - nop ngay 04/01 duoc khong
- **EMAIL_BODY:**

  > Chào phòng Đào tạo,
  >
  > Em là sinh viên K50, em muốn phúc khảo học phần Vật lý 1 (PHY101) học kỳ 1 năm học 2026-2027. Thông báo kết quả của môn ghi nhận hồ sơ phúc khảo đến 17:00 ngày 06/01/2027. Em dự định nộp vào ngày 04/01/2027, vậy có còn trong thời hạn không ạ? Nếu còn thì em cần chuẩn bị mẫu nào và đóng bao nhiêu tiền?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** PK-2026-204
- **RELEVANT_CLAUSE:** PK-2026-204 phần căn cứ, Điều 1 K1, Điều 2 K1 + điểm a
- **SUPPORTED_FACTS:**
  - Thời hạn nhận hồ sơ do thông báo kết quả từng đợt quy định, sinh viên tự đối chiếu
  - Lệ phí 150.000 đồng/học phần; Mẫu PK-01; ghi đúng mã học phần và học kỳ
- **UNSUPPORTED_OR_MISSING:**
  - Việc thông báo thật sự ghi 06/01/2027 (chỉ là lời khai của sinh viên)
  - Mọi ân hạn hoặc phụ phí
- **EXPECTED_DECISION:** AUTO_REPLY
- **EXPECTED_RULE_ID:** P05
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** medium
- **EXPECTED_MISSING_FACTS:**
  - Không có
- **EXPECTED_QUESTION_BEHAVIOR:** Không áp dụng (AUTO_REPLY).
- **FORBIDDEN_ASSUMPTIONS:**
  - Khẳng định 06/01/2027 là hạn chính thức của trường
  - Thêm ân hạn hoặc phụ phí
  - Hứa hồ sơ sẽ hợp lệ
- **PASS_CRITERIA:**
  - AUTO_REPLY, rule P05
  - Nói theo thông báo mà sinh viên nêu (06/01/2027) thì ngày 04/01/2027 là trước hạn, kèm đề nghị đối chiếu thông báo
  - Nêu Mẫu PK-01, 150.000 đồng, ghi đúng mã học phần và học kỳ
- **FAIL_SIGNALS:**
  - ESCALATE (escalate thừa)
  - Phát biểu 06/01/2027 như quy định chính thức
  - Thêm số ngày ân hạn hay phụ phí
- **BUG_HYPOTHESIS:** Over-escalation do không kiểm chứng được ngày; hoặc nâng lời khai thành quy định.
- **REALISM_BASIS:** Cặp đối chiếu với C2: chỉ đổi ngày tương đối thành ngày cụ thể.

### M2DEV-C4

- **RISK_CATEGORY:** C_TEMPORAL
- **CONTRAST_PAIR:** -
- **DIFFICULTY_FACTORS:** K49, học kỳ 1 năm học 2026-2027: RL-2026-3150 (ACTIVE) áp dụng, không còn nhập nhằng về phạm vi; tài liệu ACTIVE không định nghĩa mức Khá; tài liệu cũ RL-2025-2363 (SUPERSEDED) có 'Khá 65 đến dưới 80' và không được dùng làm căn cứ hiện hành; hearsay ('Khá từ 70'); ngưỡng cũ do chính sinh viên trích lại; hỏi 'theo quy định hiện hành'
- **SENDER:** binh.k49@example.edu.vn
- **RECEIVED_AT:** 2026-10-07T16:00:00+07:00
- **SUBJECT:** Xep loai ren luyen HK1 2026-2027 - Kha hien hanh tu bao nhieu?
- **EMAIL_BODY:**

  > Chào Phòng Công tác Sinh viên,
  >
  > Em là sinh viên K49. Điểm rèn luyện học kỳ 1 năm học 2026-2027 của em hiện hiển thị là 72 điểm. Em từng thấy một thông báo cũ ghi mức Khá là từ 65 đến dưới 80, còn bạn em bảo quy định mới thì Khá từ 70. Cho em hỏi theo quy định hiện hành thì 72 điểm của em xếp loại gì, và mức Khá hiện hành chính xác là từ bao nhiêu đến bao nhiêu ạ?
  >
  > Em cảm ơn.

- **POLICY_SOURCE:** RL-2026-3150; RL-2025-2363 (SUPERSEDED, không dùng làm căn cứ)
- **RELEVANT_CLAUSE:** RL-2026-3150 Điều 2 K1 (K49 thuộc phạm vi), Điều 3 K1 + điểm a (chỉ định nghĩa Xuất sắc, Tốt); RL-2025-2363 phần căn cứ ('không dùng làm căn cứ hiện hành')
- **SUPPORTED_FACTS:**
  - K49, học kỳ 1 năm học 2026-2027 thuộc phạm vi RL-2026-3150 ACTIVE (Đ2)
  - Thang 100; Xuất sắc 90-100; Tốt 80 đến dưới 90 (Đ3) => 72 điểm chưa đạt mức Tốt
  - RL-2025-2363 đã bị thay thế, không dùng làm căn cứ hiện hành
- **UNSUPPORTED_OR_MISSING:**
  - Định nghĩa mức Khá trong tài liệu ACTIVE (cũng không có Trung bình, Yếu)
  - Nhãn xếp loại của 72 điểm
  - 'Khá từ 70' (lời bạn)
  - Ngưỡng 65 đến dưới 80 như quy định hiện hành
- **EXPECTED_DECISION:** ESCALATE
- **EXPECTED_RULE_ID:** P02 (loại OUT_OF_POLICY)
- **ACCEPTABLE_ALT_RULE_ID:** -  |  **GOLD_CONFIDENCE:** high
- **EXPECTED_MISSING_FACTS:**
  - [] — không áp dụng: vấn đề là thiếu authoritative policy content, không phải thiếu fact từ sinh viên
- **EXPECTED_QUESTION_BEHAVIOR:** Thẻ nêu rõ tài liệu ACTIVE hiện hành chỉ định nghĩa Xuất sắc và Tốt, không có định nghĩa mức Khá; tài liệu duy nhất có ngưỡng Khá là bản đã bị thay thế. Cần nhân viên/hội đồng có thẩm quyền xác nhận. Được nói 72 chưa đạt mức Tốt (cần từ 80). Không hỏi sinh viên bổ sung fact.
- **FORBIDDEN_ASSUMPTIONS:**
  - Gọi 72 điểm là Khá
  - Dùng ngưỡng 65 đến dưới 80 từ RL-2025-2363 như quy định hiện hành
  - Dùng 'Khá từ 70' từ hearsay
  - Dùng RL-2025-2363 làm căn cứ hiện hành
- **PASS_CRITERIA:**
  - ESCALATE, loại OUT_OF_POLICY, rule P02 (không chấp nhận P03)
  - Không gán nhãn xếp loại cho 72 điểm
  - Không nêu ngưỡng Khá hiện hành
  - Không dùng RL-2025-2363 làm căn cứ hiện hành
  - Được nêu: 72 chưa đạt mức Tốt vì Tốt bắt đầu từ 80
- **FAIL_SIGNALS:**
  - AUTO_REPLY
  - P03 thay cho P02
  - Gán nhãn 'Khá' cho 72 điểm
  - Nêu 65 đến dưới 80 hoặc từ 70 như quy định hiện hành
- **BUG_HYPOTHESIS:** Retrieval/R4 kéo RL-2025-2363 (SUPERSEDED) làm nguồn ngưỡng Khá; hearsay lấp chỗ trống; R5 coi câu hỏi thang điểm là đủ vì có chunk thang 100 điểm.
- **REALISM_BASIS:** Sinh viên nhầm ngưỡng xếp loại giữa các năm và các văn bản; truyền miệng 'năm nay đổi rồi'.

## PART 4 — COVERAGE CHECK

- **Total cases:** 12
- **A factual option:** 4  |  **B sufficiency:** 4  |  **C temporal:** 4
- **AUTO_REPLY:** 4  |  **ESCALATE:** 8
- **P01:** 3  |  **P02:** 3  |  **P03:** 2  |  **P05:** 4
- **Contrast pairs:** 3 (CP1 (B1 thiếu tuần học <-> B2 có tuần học); CP2 (B3 hỏi cả hoàn học phí <-> B4 chỉ hỏi hạn); CP3 (C2 ngày tương đối <-> C3 ngày cụ thể))
- **Multi-intent cases:** A1, A2, A3, A4, B3 (+ C1, B1 ở mức nhẹ)
- **Hearsay cases:** A1, A2, A3, A4, B1, B2, B3, B4, C4
- **Relative-date cases:** B1 (tuần học), C1 ('hôm nay' sát nửa đêm), C2 ('thứ Hai tuần sau')
- **Unsupported-option temptations:** A1, A2, A3, A4 (+ C2, B3)

**Xác nhận:**
- Không dùng PII thật (tên/MSSV/email đều tổng hợp, miền example.edu.vn).
- Không đưa quy định của trường khác vào gold; web chỉ là nguồn về cách diễn đạt.
- Không có email nào sao chép nguyên văn từ web.
- Gold chỉ dựa trên 6 tài liệu + policy.yaml, trừ quy ước temporal của coordinator (nêu ở mục 0).
- Không tham khảo output của hệ thống; không chạy hệ thống; không đọc code.

### Điểm gold coordinator đã xem xét (độ chắc medium giữ nguyên: 5 case)

| Case | Độ chắc | Vì sao còn mờ |
|---|---|---|
| M2DEV-B1 | medium | Một câu trả lời 'hạn là 17:00 thứ Sáu tuần 8, bạn đang tuần mấy?' có thể bị coi là chấp nhận được; gold đặt P03 vì 'còn kịp không' cần tuần hiện tại |
| M2DEV-B2 | medium | Có thể bị escalate thừa vì hệ thống không xác minh được tuần; gold coi lời khai của sinh viên là đủ để trả lời có điều kiện |
| M2DEV-C1 | medium | Phụ thuộc quy ước neo 'hôm nay' theo ngày +07:00 và việc sinh viên khai tuần 8 |
| M2DEV-C2 | medium | Phụ thuộc quy ước temporal của coordinator: 'thứ Hai tuần sau' không được tự quy đổi; một câu trả lời có điều kiện đủ hai nhánh (04/01 và 11/01) có thể bị coi là chấp nhận được nhưng gold vẫn đặt P03 |
| M2DEV-C3 | medium | Cần trả lời có điều kiện theo lời khai của sinh viên; dễ bị escalate thừa |

Các case còn lại có độ chắc high: M2DEV-A1, M2DEV-A2, M2DEV-A3, M2DEV-A4, M2DEV-B3, M2DEV-B4, M2DEV-C4.

### CP3 — one-variable contrast

C2 và C3 giống nhau về subject (trừ cụm ngày), body, received_at, deadline trong thông báo (17:00 ngày 06/01/2027), học phần, mẫu và câu hỏi. **ONLY CHANGED FACT:** ngày nộp. C2 = 'thứ Hai tuần sau'; C3 = '04/01/2027'. Người gửi khác nhau (`trang.k50`, `nhi.k50`) chỉ để tránh trùng khi chạy, không mang nội dung quyết định.

### Checklist freeze và điều kiện trước LIVE

1. Coordinator đã review và duyệt 12-case DEV gold. Static verification đối chiếu fixture/report/policy và 6 tài liệu; không đổi input, gold hoặc rubric.
2. Không tuyên bố có independent reviewer; DEV gold này không phải held-out Set B.
3. Đã đăng ký case set `m2_combined_dev`; loader bỏ qua `meta`, không cần sidecar.
4. Sau khi chốt (và sau khi Codex đăng ký case set trong harness): ghi SHA-256 của `cases_m2_combined_dev.json` vào progress file TRƯỚC lần chạy LIVE đầu tiên; không sửa file sau đó.
5. Nếu probe phát hiện lỗi: viết 1-2 case 'anh em' cùng loại lỗi TRƯỚC khi sửa, rồi băm riêng.
6. Kết quả 'không thấy lỗi' phải ghi dạng 'NO SIGNAL OBSERVED trong N=<số> case'; đây không phải giới hạn tần suất lỗi.

**FINAL STATUS: `PREREG_FROZEN_OFFLINE_READY`** — coordinator-reviewed DEV gold; SHA-256 final bytes ghi tại progress report sau offline validation. Combined DEV LIVE chưa chạy; cần separate DEV content assessment trước execution.

## Post-execution status update — 2026-10-09

Phần preregistration phía trên được lập và đóng băng trước khi Combined DEV LIVE
được thực thi; trạng thái ban đầu, giả thuyết, Gold, phương pháp và stop conditions
được giữ nguyên như hồ sơ lịch sử.

Sau thời điểm preregistration, chương trình đã hoàn thành **9 independent LIVE
observations**, bao phủ **6/12 unique frozen DEV cases**. Ledger hiện ghi
**12/45 consumed, 33 remaining**. Kết luận closeout M2 là
**M2_CONDITIONAL_CLOSEOUT**; các observation có verdict FAIL hoặc
TECHNICAL_FAILURE trong lịch sử vẫn được giữ nguyên, không bị thay thế bởi các
observation sau correction.

Chi tiết evidence, denominator semantic và giới hạn kết luận nằm trong
[M2 Final Closeout Report & M1 + M2 Check-in Preparation](M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md).
