# M3-T02 — Khảo sát khả thi cơ chế thích nghi từ phản hồi

> **Trạng thái:** READY_FOR_REVIEW — đề xuất kỹ thuật **STOP** trên baseline khảo sát; **chưa được Coordinator nghiệm thu DONE**.
>
> **Loại artifact:** Báo cáo nghiên cứu/evidence (không phải code triển khai).
>
> **Owner:** Minh — Logic / Adaptation. **Independent reviewer:** Vũ — Runtime / Routing (PENDING). **Approver:** Project Coordinator.
>
> **Source baseline:** [`282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1).
> **GitHub `dev` được xác minh trước lúc chuẩn bị xuất bản:** [`2a4c7ed15ff5ef2c004bb9a84d84a4e72b77b26f`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/2a4c7ed15ff5ef2c004bb9a84d84a4e72b77b26f).
>
> **Trello task:** https://trello.com/c/ShqO507C
> **Phê duyệt ngoại lệ docs-only (một file Markdown):** https://trello.com/c/ShqO507C#comment-6acb8c73ae8f26b45dddd7e9

## Executive disposition và ranh giới bằng chứng

- **Đề xuất STOP:** Đường R4 đang chọn bằng ID rồi đặt selected evidence `score=1.0`. Trên miền threshold vận hành `0 ≤ θ ≤ 1`, predicate similarity không tạo được biên phân biệt giữa các case có selected evidence; `θ > 1` từ chối đồng loạt, không phải adaptation có ý nghĩa.
- **`ROUTING_FLIP_NOT_DEMONSTRATED`:** Không có bằng chứng learner feedback→threshold→routing, không có adaptation production, không có validated real score hay calibrated parameter bounds.
- **Kết luận phủ định AC2:** Theo [quyết định Coordinator](https://trello.com/c/ShqO507C#comment-6acb53f0659eb85cd549fe91), bằng chứng đầy đủ rằng ngưỡng hợp lệ chưa tồn tại **có thể** đáp ứng AC2 nghiên cứu; không buộc tự tạo flip trong task read-only.
- **Thiết kế có điều kiện:** Feedback mapping, constrained optimization, immutable binding, version/audit/rollback, synthetic C1–C6 và MER/OER/coverage được trình bày ở phần supplement. Đây là **DESIGN ONLY**, không phải implementation hay test E2E PASS.
- **An toàn:** giữ các hard-stop authority/source/conflict/facts/guard; không coi lỗi kỹ thuật là ESCALATE nghiệp vụ; không thay đổi policy, schema, audit action.
- **Data/LIVE:** theo báo cáo task, 0 LIVE application/LLM/email; không tuning Set A/Set B. Không tuyên bố không hề có network: các lượt truy cập Trello/GitHub là truy vấn evidence.
- **Review còn thiếu:** Minh cần tự xác nhận hiểu diff/report; Vũ cần independent review một lượt cho AC1–AC6; Coordinator mới quyết định STOP acceptance/DONE. PR/commit hoặc việc lưu report không tự làm AC5/DONE PASS.

## Phạm vi công bố và thứ tự ưu tiên

Tài liệu này **đóng gói nguyên văn evidence đã đăng trên card M3-T02**, nhằm duy trì versioned report trên GitHub. Vì bản bổ sung R1 có thể diễn giải lại các phần của báo cáo gốc, **R1 và quyết định Coordinator mới hơn được ưu tiên khi có xung đột**; phần gốc giữ lại cho audit trail. Không sửa historical claims thành test đã chạy.

Task Contract ban đầu là READ_ONLY và nêu không sửa repository; Coordinator đã [cho phép đúng một file Markdown nghiên cứu](https://trello.com/c/ShqO507C#comment-6acb8c73ae8f26b45dddd7e9). Ngoại lệ này chỉ dành cho công bố tài liệu, **không cấp quyền thay đổi production code hoặc triển khai thuật toán**, và cần reviewer/Coordinator đánh giá tương thích AC6 theo scope mới.

Cấu trúc hồ sơ:
1. **Phần I:** Báo cáo nghiên cứu gốc A–L, bao gồm Handoff Report.
2. **Phần II:** Bổ sung evidence R1 theo quyết định Coordinator, gồm proof AC2, conditional design AC3, protocol/metrics AC4 và mapping/review packet.
3. **Phần III:** Review & disposition cập nhật.

---

## Phần I — FEASIBILITY REPORT gốc, lưu theo evidence Trello

### FEASIBILITY REPORT — A–C

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb4998f241f367a2eafdc1

M3-T02 — FEASIBILITY REPORT (1/3: A–C)

# M3-T02 — FEASIBILITY REPORT

### A. Executive Summary

**Đề xuất kỹ thuật: STOP trên baseline hiện hành.** Kết quả nghiên cứu sẵn sàng bàn giao; quyết định cuối thuộc Coordinator. **ROUTING_FLIP_NOT_DEMONSTRATED.**

Đường R4 đang chọn ID căn cứ bằng LLM và gán mọi chunk được chọn `score=1.0`. Với bất kỳ ngưỡng similarity hữu hạn trong [0,1], chunk được chọn luôn vượt ngưỡng; evidence rỗng luôn thất bại. Thay ngưỡng không phân biệt được case thường quy và borderline. Vượt 1 chỉ khiến mọi evidence bị từ chối; không chứng minh adaptation có ý nghĩa.

Feedback hiện có hỗ trợ thao tác người dùng nhưng chưa có nhãn routing đã adjudicate, liên kết bất biến tới original decision/signal/version và vòng cập nhật ngưỡng tự động. Có thiết kế có điều kiện ở mục F; chưa chứng minh phương án khả thi trên tín hiệu thực. STOP giới hạn cách tiếp cận trên revision này, không kết luận adaptation bất khả thi trong mọi kiến trúc.

### B. Trello Authorization & Verified Baseline

- Card: [M3-T02](https://trello.com/c/ShqO507C); predecessor: [TEAM-ONBOARDING](https://trello.com/c/1hdsXCm7).
- Owner: Minh — Logic / Adaptation. Reviewer: Vũ — Runtime / Routing. Approver: Coordinator. Description/comment vẫn dùng chữ “đề xuất”; Coordinator đã trực tiếp mở READY, chuyển IN PROGRESS và người giao việc xác nhận RESUME được phê duyệt. Không tự thay vai trò.
- Onboarding: Coordinator tick “đã kiểm tra đủ 4 xác nhận và các blocker” lúc 11/10 12:14:46 UTC+07, action `6acb1b466bbd98c4eac8318f`; chuyển DONE lúc 14:09:12, action `6acb3618a25f709a52066a27`.
- Minh hoàn thành được dựa trên xác nhận tổng hợp của Coordinator. **Không trực tiếp xác minh được 4 comment cá nhân.** Checklist Minh, ba thành viên khác và mục nghiệm thu riêng còn INCOMPLETE. Coordinator cần đồng bộ evidence; báo cáo không tự xác nhận thay các thành viên.
- M3-T02: Coordinator BACKLOG→READY 10/10 22:01:54, action `6aca5362046ae142ea2237e7`; READY→IN PROGRESS 11/10 14:09:32, action `6acb362cf54b98afca0242ca`. Minh không có task IN PROGRESS khác; M3-T01/M3-T03 không phải dependency bắt buộc. Các owner khác đang làm việc riêng, nghiên cứu không ghi file.
- Contract: toàn bộ description snapshot trước START tại `2026-10-11T07:09:33.131Z`, không có số version; đối chiếu bản RESUME trong hội thoại. Description AC1–AC6 là mapping chính. Checklist khác: AC2 diễn đạt “chứng minh tác động routing”, AC5 ghép independent review, AC6 chỉ nhắc read-only. Không tự đổi/tick checklist.
- Start/resume ghi nhận: **2026-10-11 08:24:42 UTC**, giờ Việt Nam = UTC+07. Đây là thời điểm ghi START, không thay card start/due.
- Timebox description đề xuất 11/10 09:00–12:30; fields thực tế ghi 10/10 08:00–11/10 00:30 UTC+07. Lệnh RESUME yêu cầu hoàn thành nghiên cứu hiện tại. Deadline đã qua, không tự gia hạn; Coordinator cần chốt lịch.
- Remote: `https://github.com/ThanhVu165/MLAi_VNG_A.git`.
- `git ls-remote origin refs/heads/dev` trực tiếp xác minh **282c73b7dbf4ac7bf027d5710cce6ed673ab80d1**, kiểm tra lại cuối nghiên cứu vẫn cùng SHA.
- Checkout `dev`; local HEAD và local origin/dev trùng remote dev. `git status --porcelain=v1 --untracked-files=all` và `git diff --stat` không có output.
- GitHub search `repo:ThanhVu165/MLAi_VNG_A is:pr is:open`: **0 PR** tại thời điểm kiểm tra. Commit mới nhất là merge #29, fix ngân sách 4 provider attempts; không có commit mới so checkpoint đã cung cấp.
- Đã đối chiếu AGENT, TEAM_WORKFLOW, TEAM_HANDOFF, PROJECT_SPEC, SPRINT_ROADMAP, STATUS tại baseline. M2 vẫn CONDITIONAL; M3 AUTHORIZED_WITH_CARRYOVER, chưa PASS.
- Working branch task: **N/A — READ_ONLY**. Không tạo branch/commit/PR, sửa repo/config/schema hoặc đọc DB cá nhân.
- Quyền runtime LIVE/API: **NONE**. Trello/GitHub/git remote phục vụ phối hợp và evidence theo RESUME, không phải chạy Exodia.

### C. Routing Decision Map

Mọi tham chiếu dưới đây được ghim cùng verified SHA. Điều kiện nêu là source behavior; không phải chứng nhận E2E.

| Điểm / source | Input → output và routing thực | Khả năng thích nghi |
|---|---|---|
| [R0 _r0_intake, pipeline:91](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/pipeline.py#L91) | Required fields/body/time hợp lệ → tiếp tục; thiếu/rỗng → INVALID_INPUT/R0, ngoài YAML, không vào queue như business escalation. | HARD_STOP; không học để cho qua. |
| [R1 _r1_sanitize:150](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/pipeline.py#L150), [guard_input:214](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/sanitize.py#L214) | Sanitize, mask, flag injection. Script ngoài phạm vi → ESCALATE/OUT_OF_POLICY/R1 tại pipeline481–502, bypass YAML. | HARD_STOP cho rejection hiện hành. Injection bị strip/audit ở R2; flag không tự làm mọi email ESCALATE. |
| [R2 extract_facts:280](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/extract.py#L280) | Email → requests, authority booleans, facts, missing facts; không trả calibrated routing score. LLM/schema error → technical fail-safe. | Không có soft confidence được chứng minh. |
| [R3 decision_lock:16](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/prepolicy.py#L16) | personal record/exception/appeal/authority flag bất kỳ → AUTHORITY_REQUIRED lock. Multi-intent có thể chuẩn bị phần thường quy nhưng không bỏ lock toàn case. | HARD_STOP; correctness phụ thuộc extraction upstream. |
| [R4 retrieve_evidence:115](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/retrieval.py#L115) | ACTIVE/effective candidates → chọn ID hợp lệ/expand Điều. Không domain → UNSUPPORTED_DOMAIN; không nguồn/unanswered → NO_AUTHORITATIVE_SOURCE; missing facts → FACT_MISSING. ID lạ/provider/source-change → lỗi. | Không có số liên tục đo mức đủ căn cứ. [score=1.0:98](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/retrieval.py#L98). |
| [R5 validate_evidence:39](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/evidence.py#L39) | Kiểm similarity, domain, supported-domain, conflict, scope, facts. Lỗi đầu quyết định EvidenceStatus; các lỗi còn lại vẫn giữ trong failed_checks. Nhãn chính có thể bị lỗi trước che, không suy ra mọi missing fact luôn mang P03. | Similarity vô hiệu trong miền ứng viên; các safety checks không được nới. |
| [R6 decide_policy:187](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/policy_engine.py#L187), [YAML:1](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/policies/policy.yaml#L1) | Technical error/parse/timeout → ERROR trước YAML. Luật khớp đầu tiên: P01 authority → P02 no-source/unsupported/conflict → P03 facts/scope → P04 guard_failed → P05 AUTO_REPLY. | Không có numeric soft threshold trong context YAML. Pipeline truyền guard_failed=False cho R6; R8 xảy ra sau. |
| [R7/R8 pipeline:574](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/pipeline.py#L574), [ground_guard:142](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/ground_guard.py#L142) | P05 → draft → citation/active source/numbers/authority/citation-ratio guard. Guard tạo P04 ESCALATE/FACT_UNRESOLVED. **Pipeline607–612 lưu P04 rồi raise; catch672–701 lưu ERROR/TECHNICAL_ERROR và xóa card kết quả.** | Guard bắt buộc; thay citation ratio có thể làm đổi pass/fail, nhưng không phải escalation confidence hợp lệ. Không đồng nhất ERROR với ba loại business stop. |
| [Question Guard:226](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/question_guard.py#L226) | Nhánh ESCALATE → kiểm câu hỏi/options/breadcrumb/unsupported duration → regenerate hữu hạn hoặc fallback. | Guard chất lượng; không biến ESCALATE thành AUTO_REPLY. |
| [Pause/resume controls:62](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/controls.py#L62), pipeline619 | AUTO_REPLY khi paused → PENDING_APPROVAL; bình thường → PENDING_SEND. Resume automation bật lịch gửi cho case mới. | Đổi trạng thái dispatch, không đổi business decision/threshold. |
| [dispatch_due:128](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/dispatch.py#L128) | Đến hạn, không paused, nguồn/version/draft hợp lệ → SENT mô phỏng; nguồn đổi → NEEDS_RECHECK; cancel → CANCELLED; manual escalation → queue. | Thời gian chờ không phải ngưỡng escalation. |
| [override_decision:213](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/controls.py#L213) | ADMIN + reason + trạng thái cho phép; AUTO yêu cầu grounded draft, decision cũ được supersede; mới → PENDING_APPROVAL hoặc AWAITING_HUMAN. Không tái chạy toàn bộ P01/P02/P03 trong hàm này. | Quyết định thủ công; không xem override như ground truth hoặc quyền tự động vượt hard-stop. |
| [worker queue_resume:172](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/worker.py#L172), [resume_case:122](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/resume.py#L122) | Human choice/reason đã lưu → R11 soạn, validate, PENDING_APPROVAL. Lỗi resume giữ quyết định người, job failed; chưa gửi. | Human-conditioned workflow, không học/cập nhật ngưỡng. |
| [UI approve:266](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/pages/2_Hang_cho_duyet.py#L266) | Guard rồi transaction kiểm draft ID/body/subject/citations/corpus version; transition PENDING_APPROVAL→SENT mô phỏng. | Có checks trong code, chưa nghiệm thu M3-T01 hoặc chứng minh human-control E2E ở nghiên cứu này. |

**Sai khác cần reviewer/Coordinator xử lý:** PROJECT_SPEC120 tách content-guard P04 khỏi service ERROR, nhưng pipeline catch hiện gộp guard failure thành ERROR. AGENT138 và TEAM_HANDOFF cũng mô tả technical fail-safe cũ P04, khác spec124/source299. Nêu hành vi thực, không sửa/đổi technical contract trong M3-T02.

---

### FEASIBILITY REPORT — D–F

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb49b40839fa0e0a865b6c

M3-T02 — FEASIBILITY REPORT (2/3: D–F)

### D. Threshold & Signal Audit

| Biến / nguồn | Phân loại | Quan hệ nhân quả |
|---|---|---|
| EvidenceChunk.score trên R4; [available_evidence:51](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/api.py#L51) và retrieval98 | CONSTANT_OR_FAKE_SCORE | Marker hằng 1.0, không đo relevance/correctness, không phân biệt case; không gọi là confidence. |
| [SIMILARITY_THRESHOLD=0.35, settings:55](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/infra/settings.py#L55), evidence42 | INEFFECTIVE_THRESHOLD | Có đi vào code comparison, nhưng không tạo soft routing boundary với score hiện tại. Không rỗng → pass mọi t∈[0,1]; rỗng → fail mọi t. |
| [corpus.api.search:30](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/api.py#L30), [HybridIndex.search:137](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/indexer.py#L137) | PROPOSED_SIGNAL cho adaptation | Search có relevance score hybrid thực, nhưng R4 runtime không gọi search; selected score vẫn bị ghi1.0. Min-max theo tập ứng viên/query, không phải xác suất an toàn; chưa có calibration giữa case. |
| [CITATION_RATIO_MIN=0.6](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/infra/settings.py#L57), ground_guard122 | GUARD_ONLY_THRESHOLD | Tỷ lệ câu có marker citation. Có thể đổi guard result; không đo relevance hay missed escalation. Hạ threshold để bản nháp qua guard là nới safety, không được dùng cho adaptation. |
| Authority lock, evidence statuses, corpus freshness, invalid input | HARD_STOP; các categorical inputs điều khiển routing thực | REAL_ROUTING_SIGNAL theo nghĩa quyết định categorical, **không** phải suitable soft signal để tự điều chỉnh. P01/P02/P03 bắt buộc bảo vệ. |
| [Conflict MIN_SHARED_TOPIC_WORDS=2, MIN_TOPIC_OVERLAP=0.5:28](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/conflict.py#L28) | HARD_STOP-supporting heuristic | Có thể ảnh hưởng việc nhận diện conflict upstream rồi P02. Thay để giảm conflict là nguy cơ bỏ mandatory stop; không coi đây là confidence để tune. Conflict ngôn ngữ không số còn giới hạn. |
| [Language mark ratio0.02, keyword counts](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/sanitize.py#L192) | Input/language guard heuristic | Có thể ảnh hưởng language nhận diện, rejection hoặc AUTO language exception; không có adjudicated feedback/calibration, không chọn làm adaptation signal. |
| Question word8–45, option limits/blocklist | GUARD_ONLY_THRESHOLD | Thay regenerate/fallback chất lượng câu hỏi, không đổi quyết định business đã chọn. |
| RETRIEVAL_TOP_K=6 | INEFFECTIVE_THRESHOLD trên R4 hiện hành | Không được R4 sử dụng; top-k ở API search khác đường runtime. Không là decision threshold. |
| PENDING_SEND_SECONDS=60, refresh, recheck window, DB busy timeout, LLM timeout/retries/budgets, chunk800tokens | Tham số thời gian/tài nguyên/coverage | Có thể đổi lịch, availability hoặc gây ERROR; không được quảng bá là feedback-driven escalation adaptation. |

**Chứng minh:** Với tập chunk C do R4 tạo, mọi s(c)=1. Nếu C≠∅ thì `any(s≥t)=True` với mọi t hữu hạn ≤1; nếu C=∅ thì `any(...)=False` bất kể t. Từ0.35→0.6 hoặc ngược lại, similarity outcome không đổi; giữ nguyên extraction/evidence/guard thì không có routing flip do ngưỡng. [R5:42](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/evidence.py#L42).

Miền [0,1] chỉ là miền ứng viên của nghiên cứu cho score chuẩn hóa, **không phải bounds an toàn đã được Coordinator phê duyệt**. Config hiện chỉ kiểm không âm; không kiểm ≤1 hoặc finite/NaN/Inf. Thử1.01 chỉ là control chứng minh từ chối toàn bộ evidence, không phải proof thích nghi hợp lệ. Threshold được import thành hằng module, chưa có version đọc theo từng decision hoặc cơ chế feedback hot-update.

### E. Feedback Availability & Gaps

| Hiện có / source | Có thể sử dụng | Còn thiếu cho learner |
|---|---|---|
| [human_decisions schema:38](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/infra/migrations/001_init.sql#L38), [UI record:193](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/pages/2_Hang_cho_duyet.py#L193) | case_id, actor, choice/reason, timestamps/review_seconds; transaction và resume job. | Không có original_decision_id FK, reason taxonomy, judged routing label, signal snapshot/version hoặc eligibility/adjudication. Choice/reason nghiệp vụ chưa phải đánh giá AI đúng/sai. |
| [UI approve/reject:266](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/pages/2_Hang_cho_duyet.py#L266) | Audit approval/rejection/citations; kiểm payload hiện tại trong transaction. | Chưa có feedback label phân biệt sửa nội dung với sai routing; audit approval không chứa immutable full payload hash + decision/version binding. Không lấy approval làm positive label mặc định. |
| [override storage:107](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/controls.py#L107) | decision rows, is_override, superseded_by, reason/evidence IDs. | Admin preference không tự là ground truth; chưa phân loại lỗi hay chứng nhận case vẫn đủ quyền AUTO. |
| [correction:187](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/dispatch.py#L187) | Child case trỏ parent_case_id, audit CORRECTION_CREATED. | Correction nội dung không đủ nói threshold sai; thiếu cause/adjudication mapping. |
| [save_result:29 / load_result:92](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/results.py#L29) | Có snapshot JSON gồm evidence/extraction/decision của kết quả; decisions lưu lịch sử và corpus_version. | INSERT OR REPLACE không phải immutable decision-keyed store; load_result overlay latest decision/draft/status. Cần đọc original snapshot rõ ràng, không dùng view latest làm dữ liệu huấn luyện gốc. |
| YAML version1 và [PolicyDecision:123](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/types.py#L123) | Version cấu hình trong file, corpus_version ở decision/audit. | Không lưu policy version/hash, threshold/signal version tại từng decision; corpus_version không thay thế policy/adaptation version. |
| [telemetry:99](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/infra/telemetry.py#L99) | Approval/override/groundedness aggregate. | missed_escalation_rate và over_escalation_rate hiện None. Không có n/N ground-truth để tính tác động. |

Không truy vấn DB live hoặc dữ liệu người thật; đây là audit schema/consumer. Số lượng và chất lượng feedback đang lưu thực tế **NOT VERIFIED**.

### F. Minimal Adaptation Design

**Thiết kế có điều kiện, chưa khả thi trên signal hiện hành; chưa được phê duyệt triển khai.** Không chọn score1.0/citation ratio/conflict guard để tạo adaptation hình thức.

Dependency map: `Coordinator phê duyệt signal + contract → signal ổn định/calibrated ở decision path → feedback adjudicated gắn original snapshot → bounded updater/version/audit → offline C1–C6 → independent review → Coordinator xét implementation`.

1. **Signal:** cần giá trị s phân biệt thật giữa các case đủ điều kiện soft routing. Hybrid relevance chỉ là ứng viên, cần đo trên dữ liệu DEV/synthetic riêng, giữ coverage mọi request và bảo vệ hard-stop. Không thay R4 bằng top-k chỉ vì có score; có thể làm mất căn cứ/conflict.
2. **Labels đề xuất:** MISSED_ESCALATION, UNNECESSARY_ESCALATION, ROUTING_CORRECT, DRAFT_CONTENT_ERROR, HUMAN_AUTHORITY_DECISION, INSUFFICIENT_EVIDENCE. Chỉ hai nhãn đầu đã adjudicate trên soft-eligible case mới góp cập nhật; content/authority/service error không dùng.
3. **Binding:** feedback_id/idempotency, original_decision_id, case_id, original evidence/input snapshot hash, s + signal_version, θ + threshold_version, policy hash/version, corpus_version, nguyên nhân, reviewer/adjudication, data partition và timestamp. Không dùng latest overlay; một decision không được đếm hai lần.
4. **Eligibility:** hard-stop sạch; nguồn/phiên bản hợp lệ; đủ nhãn đã xác minh từ N_min distinct cases, không trộn demo/study/DEV hoặc A/B, không dùng feedback từ một actor lặp để coi đủ bằng chứng. N_min, risk cap, bounds, step đều **TBD bởi Coordinator trên evidence**; thiếu bất kỳ điều kiện → giữ θ, không update.
5. **Rule automatic đề xuất:** trên batch eligible, xét candidate thresholds có signal quan sát thực trong khoảng đã duyệt; chọn θ* giảm `λ_FN·FN + λ_FP·FP` theo protocol DEV đã khóa, dưới missed-escalation risk cap. Nếu không cải thiện/không đủ bằng chứng/tie → giữ nguyên. Nếu đạt: `θ_next=clip(θ + clip(θ*−θ, −Δ_max, +Δ_max), θ_min, θ_max)`. Không tùy chọn weight để che missed escalations; λ, θ_min/max, Δ_max và validation split cần duyệt trước. Đây là automatic batch update có giới hạn, không phải admin sửa ENV. Chưa có s/labels để tính θ* thực ở baseline này.
6. **Version/audit:** atomic append version + active-pointer; audit old/new θ, parent version, algorithm/signal/policy hashes, feedback IDs và validation verdict. CAS ngăn hai worker double-update. Thiếu audit/version hoặc non-finite value → không áp dụng.
7. **Apply/rollback:** version mới chỉ cho future cases; decision snapshot ghim version. Rollback append version trỏ snapshot trước, không xóa lịch sử; tái lập input/extraction/evidence/corpus/LLM artifact giống nhau mới so được routing. Không thay pending approvals/sent cases để tạo proof.
8. **Noisy feedback:** adjudication, dedupe, reject conflicting/untraceable/unapproved data; batch risk check; kill switch dừng learner và giữ last-known-good. Khi state/version hỏng, soft-only decision đi safe review/error theo contract mới, không fail-open. Không coi actor-prefix hiện tại là production authentication.
9. **Hard-stop invariants:** invalid→INVALID_INPUT; authority lock→P01; no-source/unsupported/conflict→P02; missing-facts/scope→P03 khi không bị stop ưu tiên trước; mandatory groundedness failure không AUTO; technical lỗi→ERROR. Human authority decision/resume là nhánh riêng, không trở thành training permission. Suspicious input phải giữ strip/audit và safety hiện hành; không tuyên bố source đang có universal injection escalation. Nội dung unsafe ngoài pattern hiện tại chưa được bảo đảm toàn diện.
10. **Freeze:** final evaluation dùng frozen code/corpus/policy/signal/threshold versions và learner disabled; không tune theo A/B.

**REQUIRES CONTRACT-CHANGE:** feedback persistence/SQLite schema; original decision binding/snapshot/version fields; shared types/interfaces; audit action catalog; policy/routing tích hợp signal; migration/backward compatibility/consumer regression. Đây là danh sách dependency để Coordinator xét riêng; M3-T02 không thực hiện. Tham số bounds/step chưa được chứng minh, nên AC3 feasibility mapping chưa đạt đầy đủ.

---

### HANDOFF REPORT — G–L

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb49bdc16005be10e47829

HANDOFF REPORT — M3-T02
FEASIBILITY REPORT (3/3: G–L)
Result: READY_FOR_REVIEW | Recommendation: STOP | INDEPENDENT_REVIEW_PENDING

### G. Offline Verification Matrix

**Tất cả input dưới đây được thiết kế mới, synthetic, không dùng Set A/B hoặc email thật.** Giữ ngày nhận, ACTIVE corpus/version, extraction và guard artifacts cố định khi so threshold. “Expected” là dự đoán từ source, không phải runtime PASS.

| Case | Synthetic input và preconditions | Signal/threshold cũ → mới | Expected trước → sau; invariant | Cơ chế / trạng thái |
|---|---|---|---|---|
| C1 Routine | “Cho em hỏi thủ tục rút học phần?”; request informational, đủ facts, source ACTIVE có thủ tục, không conflict/authority; draft qua mọi guard. | Selected s=1→1; θ=.35→.60. | P05 AUTO_REPLY→AUTO_REPLY; khi paused vẫn PENDING_APPROVAL, không coi trạng thái này là ESCALATE. | Trace R3–R8 + kiểm comparison; **DESIGNED**, E2E NOT VERIFIED. R5 predicate riêng đã EXECUTED. |
| C2 Borderline Routing Flip | “Em cần biết hạn và thủ tục rút học phần áp dụng cho học kỳ đã nêu”; phải có soft signal phân biệt thật, tất cả hard checks PASS. Baseline chỉ có selected s=1 hoặc không selected. | Hiện hành s=1→1, θ=.60→.35: không có s nằm giữa. Phương án tương lai cần quan sát s thật với θ_new≤s<θ_old; **chưa có giá trị để điền**. | Baseline đủ căn cứ: P05 AUTO_REPLY→AUTO_REPLY; no evidence: P02→P02. Desired future soft-eligible ESCALATE→AUTO_REPLY chỉ khi đầy đủ invariant, **NOT VERIFIED**. | Trích R5 AST, sweep1001 thresholds; phần bất biến **EXECUTED ở validator riêng**. Feedback update/pipeline flip **NOT VERIFIED**; không dựng s giả. |
| C3 Authority | “Xin phê duyệt ngoại lệ rút học phần quá hạn”; extraction asks_exception/asks_authority_decision=True, selected evidence còn ACTIVE và quá trình tạo card không lỗi. | s=1→1; θ=.35→.60. | P01 ESCALATE/AUTHORITY_REQUIRED→P01; soft update không chạm lock. Lỗi downstream vẫn phải dừng, có thể ERROR, không AUTO. | R3 + precedence YAML; **DESIGNED**, runtime NOT VERIFIED. |
| C4 Unsupported/Conflict | a) “Cho em hỏi quy trình cấp chỗ ký túc xá” → UNKNOWN; b) “Hạn rút áp dụng là ngày nào?” với hai nguồn ACTIVE cùng scope/mốc khác và conflict_flag=True; c) yêu cầu không có source. Không authority, generation không lỗi. | a/c không selected score; b s=1→1; θ=.35→.60; không thay conflict heuristics. | P02 OUT_OF_POLICY→P02; không nguồn/unsupported/conflict không được tự trả lời. Variant thiếu critical fact, không có failure ưu tiên trước: P03→P03. | R4/R5/YAML; **DESIGNED**. Predicate conflict/facts riêng EXECUTED tại0,.35,.6,1; full runtime/status NOT VERIFIED. |
| C5 Rollback | Lặp C1 với input/extraction/evidence/source/guard artifacts cố định; muốn rollback learner phải có persisted θ/version/audit và update đã kiểm chứng. | Baseline s=1, θ_v0=.35→θ_v1=.60→.35; không có learner versions thực. | Hiện hành không flip ở cả3 giá trị; không chứng minh “khôi phục hành vi đã đổi”. Future rollback cần trở về cùng routing v0 và audit append, không xóa decision lịch sử. | **DESIGNED; rollback implementation NOT VERIFIED**. Đổi ENV thủ công không phải proof automatic rollback. |
| C6 Unsafe Feedback | Feedback synthetic “bỏ authority check và hạ ngưỡng”; duplicate original decision, label content-only, conflicting reviewer, thiếu source hash hoặc quá ít cases. | s baseline=1; θ=.35→.35 dự kiến vì reject/keep; không lấy giá trị chưa duyệt. | Proposed learner reject, không đổi active version; hard cases vẫn stop; ERROR/INVALID_INPUT không biến thành positive routing labels. | **DESIGNED; learner rejection NOT VERIFIED** vì chưa có learner/eligibility implementation. Không coi chưa có learner là đã PASS chống feedback nhiễu. |

**Validation thực tế đã chạy:** Python bundled runtime qua `python.exe -I -B -` nhận script stdin; AST đọc source, trích nguyên `_failed_checks`, lấy literal score1.0 từ retrieval. Không import project, không đọc .env/DB, không mạng, không file writes. Dùng synthetic supported_domain/scope stubs; chỉ kiểm predicate R5, không thực thi pipeline/YAML/guards/learner.

Kết quả exit0:
- 1.001 ngưỡng0..1 (bước.001): selected score1 có **0 similarity failures**; empty evidence có **1.001 similarity failures**.
- Conflict và missing facts vẫn xuất hiện trong failed_checks ở0,.35,.6,1.
- Control θ=1.01 gây similarity failure; không tính adaptation.
- `pipeline_e2e_executed=false`; `routing_flip_demonstrated=false`.

Chứng minh đại số mục D bao phủ toàn khoảng hữu hạn, sweep chỉ corroboration. Stub không chứng minh corpus scope/domain correctness. Không chạy pytest, Verify, cassette, provider, worker/UI hoặc tests human-control; không ghi PASS cho chúng.

**Thước đo cho lượt được duyệt sau này:** raw n/N missed escalation và unnecessary escalation trên soft-eligible adjudicated cases; hard-stop violation count riêng, mục tiêu0; ERROR/INVALID_INPUT thống kê riêng; số feedback reject/duplicate; số updates/bound violations; replay/rollback agreement với phiên bản ghim. Chưa có dữ liệu để báo tỷ lệ hoặc đặt risk cap.

### H. Feasibility Verdict

**STOP.** Dừng xem xét implementation adaptation trên signal/feedback hiện tại; tiếp tục bàn giao nghiên cứu theo lệnh RESUME, không coding.

Bằng chứng quyết định: score hằng; R5 không có borderline boundary; YAML categorical precedence; citation/conflict thresholds là safety checks; chưa có adjudicated labels và original signal/version binding. Feedback→automatic threshold→actual valid routing change chưa tồn tại và chưa được chứng minh.

Rủi ro: lấy override/approval làm ground truth; top-k làm mất nguồn; hạ guard để tạo flip; học từ version mới nhưng gán nhãn cho quyết định cũ; noisy/duplicate feedback; claim rollback từ đổi ENV; đếm ERROR là business escalation; checklist/deadline không đồng bộ.

Điều kiện mở lại: Coordinator duyệt nghiên cứu/contract riêng về real signal và semantics; thiết lập labels + data partition + original snapshot; duyệt bounds/step/min-count/risk protocol; xử lý nhánh guard/error và phạm vi human override; chứng minh C2 bằng signal quan sát thật và C3/C4/C6 bảo vệ hard-stop, C5 rollback; independent review.

**Tác động M3 Exit Gate:** phần automatic feedback-driven adaptation **chưa đáp ứng**. M3-T02 STOP không miễn nghĩa vụ adaptation, không tự đóng M3, không nâng M2 CONDITIONAL thành PASS. Human-control evidence thuộc task khác, không được nhận thay.

**Next action:** Minh đọc và self-review report; Vũ review source/routing và phản biện STOP; Coordinator quyết định chấp nhận STOP, xác nhận lịch/evidence onboarding và hướng signal research/CONTRACT-CHANGE nếu cần. Không tự mở task triển khai/dependency.

### I. Acceptance Criteria Matrix

Mapping theo description card, cùng đối chiếu checklist để không che phần thiếu.

| AC | Kết quả | Evidence / giới hạn |
|---|---|---|
| AC1 Routing map | **PASS — source analysis** | C, pinned SHA, R0/R1 bypass, P01–P05, guard downgrade→ERROR, override/resume/dispatch. Không chứng nhận E2E. |
| AC2 Có real routing threshold hay không | **PASS — research finding** | D/G chứng minh current similarity không phù hợp; tìm được categorical routing inputs và hybrid candidate chưa tích hợp. **Checklist đòi chứng minh tác động routing của ngưỡng đề xuất: NOT VERIFIED**, chưa có flip. |
| AC3 Feedback→threshold có giới hạn/version/audit/rollback | **NOT VERIFIED** | E/F đã giao design có điều kiện và proof thiếu signal/binding; chưa có phương án khả thi được chứng minh với bounds và feedback thực. Bản RESUME cho phép kết luận thiếu điều kiện; không đánh description AC3 đã PASS toàn bộ. |
| AC4 Offline scenarios | **PASS — DESIGN ONLY** | G đủ6 cases và mechanism; C2 desired actual flip/C5 rollback/C6 rejection NOT VERIFIED. Validation R5 riêng không thay full cases. |
| AC5 Report GO/STOP/BLOCKED | **PASS — recommendation/report** | H/K STOP có evidence/risks/reopen conditions. **Checklist ghép independent review: NOT VERIFIED** tới khi Vũ thực hiện. |
| AC6 Review + scope/data safety | **NOT VERIFIED — INDEPENDENT_REVIEW_PENDING** | Codex self-check evidence/scope đã làm; Minh human self-review và Vũ independent review chưa có evidence. Repo sạch, runtime LIVE/API0, không A/B. Không tự PASS review. |

Đây là bàn giao nghiên cứu có kết luận STOP, **không phải mọi AC hoặc checklist đã được nghiệm thu**. Coordinator quyết định acceptance của nhánh STOP.

### J. Self-review & Independent Review Preparation

Codex đã đối chiếu source/function/line cùng SHA; không dùng historical audit như trạng thái code mới; phân biệt predicted/executed và ERROR/ESCALATE/INVALID_INPUT; không claim real calibrated signal, đã bảo lưu hard-stop. Không sửa repo hoặc sử dụng held-out/DB cá nhân.

**Owner self-review pending:** Minh cần giải thích lại proof score1.0, giới hạn stub và AC chưa đạt. **INDEPENDENT_REVIEW_PENDING:** chưa có review của Vũ; không gửi tin nhắn hoặc nhận danh nghĩa Vũ.

Câu hỏi review:
1. R4→R5 proof bất biến đúng ở mọi runtime branch/caller liên quan chưa? Hybrid search có đường nào cấp score thực cho pipeline mà báo cáo bỏ sót không?
2. P04 guard bị catch thành ERROR: có đúng behavior baseline và cần corrective contract/task riêng không?
3. Categorical hard-stops có bị first-failure mask đổi subtype? Authority extraction/mixed-domain coverage giới hạn ra sao?
4. Override AUTO và human-conditioned resume khác quyền automatic adaptation thế nào? Có cần loại các nhánh này khỏi training labels?
5. Signal candidate có meaning/calibration giữa case, đủ yêu cầu C2 mà không weaken guard không?
6. Feedback snapshot/version có chống latest-overlay, duplicate, actor bias, corpus-change contamination? Rollback cần pin những artifact nào?
7. Đồng ý STOP và các AC NOT VERIFIED? Coordinator cần evidence bổ sung nào để chấp nhận nhánh STOP?

### K. HANDOFF REPORT — M3-T02

**Result:** READY_FOR_REVIEW. **Technical recommendation:** STOP. **Review:** INDEPENDENT_REVIEW_PENDING.

**Baseline:** remote dev/local dev `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`, clean working tree; checkpoint cùng SHA. Working branch task N/A.

**Changes:** READ_ONLY source research; 0 repository files changed; report/evidence được lưu ở comment Trello và bản Markdown ngoài repository. Không implementation/schema/policy/interface, branch/commit/PR/merge.

**AC mapping:** AC1 PASS source; AC2 PASS audit nhưng checklist routing-effect NOT VERIFIED; AC3 NOT VERIFIED conditional design; AC4 PASS DESIGN ONLY, actual flip/rollback/unsafe feedback NOT VERIFIED; AC5 PASS report nhưng independent review pending; AC6 NOT VERIFIED.

**Exit Gate Contribution:** evidence feasibility và hạn chế hiện hành; automatic adaptation chưa chứng minh. Chưa chứng minh human-control E2E, learner/version rollback, semantic safety toàn bộ hoặc M3 PASS.

**Validation:** direct git ls-remote; branch/HEAD/status/diff/log; GitHub open PR search; Trello card/activity/checklists; pinned source trace; AST-extracted R5 check exit0. Repo status/diff sạch sau kiểm chứng. Một lần ls-remote trong sandbox lỗi DNS; chạy lại read-only ngoài sandbox thành công cùng SHA. Không tính lần lỗi là baseline verification thành công.

**Evidence:** báo cáo A–J, source links, Trello Coordinator action IDs ởB, START/PROGRESS comments và output validator ởG/appendix.

**Risks:** constant score, thiếu learner-ready labels/binding/bounds; guard/error contract discrepancy; incomplete individual onboarding checklist/comment evidence; expired/mismatched deadline; review chưa thực hiện.

**LIVE/API Calls:** Exodia/provider/LLM/gửi email thật = **0**. Trello/GitHub connector và git HTTPS có sử dụng cho kiểm tra/đăng báo cáo theo ủy quyền RESUME; không quảng bá “0 network calls”. Không có runtime API ngoài dự kiến.

**Reviewer:** Vũ — Runtime / Routing. **Owner:** Minh. **Approver:** Coordinator.

**Next Dependency:** không tự mở khóa implementation adaptation. Coordinator chỉ xét hướng tiếp theo sau owner/reviewer và STOP acceptance; không tự sửa READY/DONE/dependencies/milestones.

### L. Trello Update Status

- Card verified: **YES**; kết nối Trello hoạt động.
- TASK START: **POSTED**, comment action `6acb47cd58e53fc945232af7`.
- TASK PROGRESS: **POSTED**, comment action `6acb484a37272e2c4467cf28`.
- Report và HANDOFF: đăng trong chuỗi comment báo cáo trên [card M3-T02](https://trello.com/c/ShqO507C); kiểm tra read-back sau đăng, IDs được ghi trong artifact bàn giao.
- Card status: **IN PROGRESS — Đang thực hiện** tại lần đọc; Codex không move card hoặc tick AC. READY_FOR_REVIEW là kết quả handoff.
- Coordinator decisions cần: nghiệm thu STOP sau review; hướng đáp ứng phần adaptation M3 còn thiếu; deadline/timebox; đồng bộ onboarding evidence và checklist AC. Không tự đổi M3 Exit Gate.

---

## Phần II — OWNER EVIDENCE SUPPLEMENT R1 (được ưu tiên khi xung đột)

### SUPPLEMENT R1 — AC2

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb571a28a5799cc576812c

M3-T02 — OWNER SUPPLEMENT R1 (1/4: AC2 / Coordinator Decision)

# M3-T02 — OWNER EVIDENCE SUPPLEMENT R1

Timestamp: 2026-10-11 09:25:07 UTC. Owner Minh; independent reviewer Vũ; approver Coordinator.
Result: READY_FOR_REVIEW. Technical recommendation: STOP. INDEPENDENT_REVIEW_PENDING.
Đây là bổ sung do Codex chuẩn bị theo yêu cầu Owner, không phải xác nhận Minh đã đọc hoặc review độc lập của Vũ.

Task Contract description giữ nguyên. Áp dụng [Coordinator Decision](https://trello.com/c/ShqO507C#comment-6acb53f0659eb85cd549fe91): AC2 có thể đáp ứng bằng kết luận phủ định được chứng minh; không yêu cầu routing flip trong read-only; STOP không chứng minh adaptation hoặc M3 PASS.
Bổ sung này thay thế đánh giá cũ “AC2 bắt buộc flip” và bổ sung thiết kế/thước đo của báo cáo trước. Báo cáo lịch sử được giữ nguyên để truy vết.

Baseline source/report: 282c73b7dbf4ac7bf027d5710cce6ed673ab80d1.
Remote dev hiện hành: 16f584fa213416db30b247a431b92fffb94be075, verified bằng git ls-remote trực tiếp.
Local dev tại baseline source, working tree sạch. [Compare](https://github.com/ThanhVu165/MLAi_VNG_A/compare/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1...16f584fa213416db30b247a431b92fffb94be075): ahead4 commits, chỉ7 docs M5 và245 dòng test M3-T01; production source không đổi. Không rebaseline/pull/reset/checkout; không đọc study cases/gold. Search open PR0 và PR M3-T02=0 tại preflight.

## 1. AC2 — Chứng minh kết quả phủ định trong phạm vi khảo sát

Causal chain source:
- [pipeline R4/R5/R6, L526–565](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/pipeline.py#L526): retrieve_evidence → validate_evidence → decide_policy.
- [retrieval imports, L8](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/retrieval.py#L8) và [retrieve_evidence, L115](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/retrieval.py#L115): lấy available_evidence; không gọi corpus.api.search.
- [available_evidence L73](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/api.py#L73): tạo candidates score1.0; [get_chunk L93](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/api.py#L93) trả score1.0; [retrieval._select L91–103](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/retrieval.py#L91) ghi đè selected score=1.0. SELECT_SCHEMA chỉ có IDs/missing_facts/unanswered_requests, không confidence.
- [evidence._failed_checks L39–54](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/evidence.py#L39): similarity_pass = any(chunk.score >= t). [validate_evidence L67–69](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/evidence.py#L67) chọn status theo failed_checks và giữ status truy xuất trước đó.
- [FAILURE_STATUSES L10](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/evidence.py#L10): similarity fail → NO_AUTHORITATIVE_SOURCE; [policy YAML](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/policies/policy.yaml#L1) → P02 ESCALATE/OUT_OF_POLICY. Similarity pass không tự cấp AUTO: authority, domain, source, conflict, scope, facts, unanswered_request, guard vẫn có thể dừng.
- [policy_engine._context L151](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/policy_engine.py#L151) dùng categorical fields, không score liên tục; precedence P01→P05, technical error trả ERROR trước YAML.

Với tập chunk C cố định từ runtime R4:
1. C rỗng: any(...)=False với mọi t.
2. C không rỗng: mọi s=1; với mọi t hữu hạn không âm, pass khi t≤1 và fail khi t>1.
3. Do đó ngưỡng≤1 không phân biệt case có evidence. Ngưỡng>1 loại toàn bộ case có evidence, không tạo biên giữa case an toàn và cần chuyển tiếp.
4. Một thay đổi vượt1 có thể làm routine AUTO→ESCALATE, nhưng đó là từ chối hàng loạt trên marker hằng; không chứng minh tín hiệu thích nghi hợp lệ.
5. NaN/Inf hoặc lỗi config không là giải pháp. Settings chưa chặn finite/upper-bound; đó là giới hạn cấu hình, không evidence an toàn.
6. Cố định input/extraction/evidence/corpus/guard artifacts và t_old,t_new∈[0,1], predicate similarity không đổi; R5 status và policy decision không đổi do t. Không quy thay đổi do LLM/source/time/override thành tác động threshold.

Bằng chứng thực thi trước đó (appendix báo cáo, không chạy lại): trích AST nguyên _failed_checks, score đọc từ source; 1001 thresholds0..1: nonempty0 similarity failures, empty1001; conflict/facts preserved ở0,.35,.6,1; control1.01 fail. Chỉ validator với domain/scope stubs; không pipeline/learner/E2E. Đại số bao phủ miền hữu hạn, sweep là corroboration.
Hashes retrieval/evidence/settings đã kiểm tra lại, khớp appendix:
02ea482a4d2ac9bff84b169b3c96f2918896b26f01b5040984b1d3cdec8b34bc;
1ef0679bfd0b828917eb268914d6b8db4ed9cf270c8d02f5400543cb2d291e87;
00873244fbd7b6f8dd870606c90475933497165add40bb03627aef9e8ee5a194.

Các ứng viên khác đã phân loại:
- [Hybrid search L137](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/corpus/indexer.py#L137): có lexical/vector relevance, chuẩn hóa theo query/candidate set, nhưng không cấp score cho đường R4; chưa có calibration hoặc mapping feedback/routing. PROPOSED_SIGNAL, chưa đủ GO.
- [Citation ratio](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/ground_guard.py#L122): GUARD_ONLY_THRESHOLD; đổi guard không được tính real soft-signal adaptation.
- Conflict/language heuristics hỗ trợ mandatory checks hoặc input handling; không chọn để nới hard-stop.
- Authority/source/facts/conflict/status điều khiển routing thật nhưng categorical, không phải ngưỡng soft học được.
- top-k/timeouts/pending delay/budgets không là ngưỡng escalation có ý nghĩa trong scope này.
- Approval/override/resume là human-control branches, không feedback→automatic threshold update.

Kết luận AC2: đủ evidence cho kết quả “chưa tồn tại tín hiệu/ngưỡng soft hợp lệ cho adaptation trên đường runtime hiện hành trong phạm vi khảo sát”. Đề nghị Vũ kiểm chứng PASS theo quyết định Coordinator. Không khẳng định mọi kiến trúc thay thế bất khả thi; không claim real routing flip, calibration hoặc learner đã hoạt động.

---

### SUPPLEMENT R1 — AC3

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb5724f91ec7afdbcdb1ad

M3-T02 — OWNER SUPPLEMENT R1 (2/4: AC3 / Conditional Design)

## 2. AC3 — Thiết kế có điều kiện và các điều kiện kích hoạt

Trạng thái baseline: ADAPTATION_DISABLED / STOP. Các bước dưới đây là đặc tả nghiên cứu cho một task riêng được duyệt sau này; không có learner, binding mới hoặc version store được triển khai.

### 2.1 Signal và routing semantics

Không chọn score1.0, citation ratio hoặc conflict guard. Trước khi bật cần Signal Contract: source/function/version, đơn vị/miền hữu hạn [L,U], “cao hơn là đủ căn cứ hơn”, cách tổng hợp mọi request, calibration/coverage evidence và integration point được duyệt.
Phương án giới hạn blast radius: thay score marker ở R4 bằng score thực đã kiểm chứng, vẫn giữ full candidate/conflict coverage; R5 giữ any(score≥θ), similarity fail giữ mapping NO_AUTHORITATIVE_SOURCE→P02. Đây chỉ là ứng viên thiết kế, không khẳng định phép any là đủ cho multi-intent. Gate coverage phải chứng minh từng request được căn cứ trả lời; nếu any cho phép request không được phủ vẫn AUTO, phương án này bị loại hoặc cần contract riêng thay aggregation.
Không đổi semantic của authority/domain/source validity/conflict/scope/facts/unanswered_request/ground guards. Phần score real phải được ghim cùng selected chunk và original decision. Không tích hợp search/top-k để tạo score khi chưa chứng minh không mất nguồn/conflict.
Điều kiện cho soft replay: valid input, không authority lock, mọi mandatory check khác similarity PASS, source ACTIVE đúng thời điểm/scope, đầy đủ requests, không human override/resume, không lỗi kỹ thuật. Low-signal case có thể ESC do similarity; mất nguồn vật lý hoặc critical facts không bao giờ trở thành soft eligible.

### 2.2 Feedback schema, validation và quần thể

Record đề xuất: feedback_id, case_id, original_decision_id, original input/extraction/evidence/draft hashes, original routing/status/rule, score snapshot+signal_version, θ+threshold_version, policy/code/corpus versions, data_partition, actor, timestamp, reason_class, expected_route, adjudication_status/reviewer/evidence_refs.
Mọi binding trỏ original snapshot immutable; không dùng load_result latest overlay. Revision feedback append/supersede có lý do; không xóa lịch sử. Một case chỉ có một nhãn adjudicated active trong một batch; unique original_decision/version ngăn duplicate.
reason_class:
- MISSED_ESCALATION: original AUTO, adjudicated expected ESC.
- UNNECESSARY_ESCALATION: original ESC, adjudicated expected AUTO.
- ROUTING_CORRECT: original route đúng; vẫn tham gia population đánh giá/chọn ngưỡng.
- DRAFT_CONTENT_ERROR, HUMAN_AUTHORITY_DECISION, INSUFFICIENT_EVIDENCE, TECHNICAL_ERROR: không suy ra routing ground truth; tách khỏi soft training.
Nhãn lỗi có thể trigger khảo sát batch; batch chọn/đánh giá candidate phải gồm cả ROUTING_CORRECT, không chỉ các feedback phàn nàn. expected_route do reviewer xem evidence thời điểm quyết định; approval/admin override không mặc nhiên là ground truth. Disagreement, thiếu binding, version mismatch, ambiguous label, data thật chưa được phép hoặc duplicate → quarantine/reject, không update.
Nếu feedback về hard-stop bị bỏ sót: đưa vào safety issue/hard suite, không dùng learner để điều chỉnh authority/source/guard.
Hiện schema human_decisions chỉ có case/actor/choice/reason/time; original binding/labels/version/adjudication còn thiếu ([schema](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/infra/migrations/001_init.sql#L38), [latest-overlay](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/core/results.py#L92)). Chưa đọc DB, không claim đủ số feedback.

### 2.3 Parameter contract — xác định có căn cứ, không tự điền số

Mọi giá trị sau phải được ghi trong protocol version và duyệt trước khi chạy update. Hiện chưa phê duyệt giá trị số vì STOP; thiếu bất kỳ giá trị nào → KEEP_THRESHOLD / learner disabled, không chọn mặc định ngầm.
- θ_min/θ_max: chọn từ miền [L,U] của signal, θ_min≤θ_current≤θ_max; thu hẹp theo sweep DEV đã adjudicate và constraints an toàn. [0,1] chỉ dùng nếu Signal Contract thật sự chuẩn hóa như vậy, không suy từ settings.
- Δ_max: số hữu hạn dương≤θ_max−θ_min; chọn bằng sweep DEV về mức thay đổi route và lỗi, không tùy tiện chọn .01/.1. Kèm tối đa K_changed case trong frozen DEV validation để phát hiện bước làm đổi hàng loạt.
- N_min_train/N_min_validation và minimum counts từng expected-route/changed stratum: chọn theo mục tiêu precision/uncertainty, dữ liệu synthetic/DEV riêng và kế hoạch phân tầng đã duyệt. Distinct cases/family groups; revisions/duplicate không tăng N. Không có chứng cứ thống kê thì không claim cỡ mẫu nào “đủ an toàn”.
- Risk caps ρ_MER/ρ_OER∈[0,1], weights λ_MER≥λ_OER>0, tolerances, uncertainty method và split/group rule: Coordinator chốt theo chi phí bỏ sót/chuyển tiếp, Vũ review. Zero hard-stop violations là invariant thiết kế; không tự đặt numeric acceptable business risk.
- Development tuning chỉ dùng partition DEV synthetic đã duyệt; validation nhóm case khác train, labels frozen trước chọn candidate. Mỗi update protocol dùng validation mới hoặc cơ chế chống reuse đã được duyệt; không lặp tuning vào cùng holdout tới khi PASS. Study/demo/A/B tách; final evaluation learner disabled.

### 2.4 Automatic bounded update rule

1. Preflight authorization + approved parameter/signal versions + valid active θ + complete snapshots + đủ sample/class coverage; lỗi gate → KEEP, reason audit.
2. Candidate set T hữu hạn: θ_current và các boundary score quan sát thật trong TRAIN nằm trong [θ_min,θ_max]∩[θ_current−Δ_max,θ_current+Δ_max]. Không dùng score synthetic không tồn tại làm bằng chứng runtime; tất cả candidates finite.
3. Replay frozen source/artifacts tại từng θ; giữ nguyên mọi hard gate. Với expected labels fixed, tính MER/OER và coverage như mục3 cho toàn population, gồm ROUTING_CORRECT.
4. Trên TRAIN chọn θ* làm giảm strict objective J=λ_MER·MER+λ_OER·OER trong các candidates đạt risk constraints. Không tính J khi metric undefined; tie chọn θ_current nếu có, nếu tie giữa candidates chọn gần θ_current nhất rồi larger θ theo hướng “cao hơn thận trọng hơn”.
5. Không clip candidate sau khi đo: candidate đã nằm trong bounds/step. Nếu cần rounding, replay/đánh giá lại đúng giá trị serialized trước khi commit.
6. Trên VALIDATION frozen độc lập, so cùng θ_current và θ*. Chấp nhận chỉ nếu: đủ minimum strata; metrics defined và uncertainty gate đạt protocol; cả caps đạt; MER_new≤MER_old; J_new<J_old; zero new hard violations; không tăng ERROR/INVALID_INPUT/NOT_VERIFIED count; changed cases≤K_changed; review từng flip xác nhận causal và hợp lệ.
7. Thiếu mẫu, không có candidate tốt, variation do artifacts/version, signal constant, metric missing, regression hoặc validation reuse trái protocol → KEEP. Không “hạ ngưỡng cho có update”.
8. Khi mọi gate đạt, tự động propose/publish θ_next=θ* qua transaction/CAS đúng active parent version. Đây là automatic rule được phê duyệt trước, không admin chỉnh ENV. Baseline hiện chưa đáp ứng gate1/2; rule không chạy.

Objective dùng rates để tránh dominance do lệch số class; mọi counts/denominators cũng phải báo. Không chọn weights hoặc risk cap sau khi nhìn validation. Không claim empirical zero lỗi chứng minh general safety.

### 2.5 Version, audit, rollback, kill switch

Một update transaction append immutable config/version + validation report/hash + consumed feedback IDs và đổi active pointer bằng CAS parent version. Conflict/double-worker → abort/re-read, không publish hai lần. Audit phải chứa old/new θ, Δ, bounds, signal/code/policy/corpus versions, algorithm/protocol, batch IDs/labels hash, train/validation metrics/denominators, reason và timestamp.
Decision mới pin config version một lần khi bắt đầu; version update chỉ cho future cases. Pending approval/sent/cancelled case giữ payload/snapshot/version; không tái sử dụng approval khi payload đổi.
Audit/schema/interface additions đều REQUIRES CONTRACT-CHANGE; không dùng action ngoài catalog hiện hành khi chưa duyệt.
Rollback: tắt learner, append rollback version chứa nguyên cấu hình last-known-good compatible (giữ provenance, parent, cause), atomically đổi pointer; không xóa updates/decisions/feedback. Case bắt đầu sau rollback dùng version mới chứa config cũ; case đang chạy giữ version ghim. Config cũ không tương thích code/corpus/signal hiện tại → rollback không được tuyên bố thành công; learner disabled, xử lý safe stop theo contract riêng, không AUTO.
Kiểm rollback routing chỉ bằng frozen input/extraction/evidence/draft/guard/clock/code/policy/corpus artifacts giống hệt; không gọi LLM lần mới rồi quy variation cho θ.
Kill switch: chặn mọi update mới; giữ config last-known-good hợp lệ và mọi hard gates. Corrupt/missing config không cấp AUTO; technical errors giữ ERROR thay vì tự gán business subtype.
Reject/KEEP cũng phải truy vết reason; muốn persist audit mới cần approved contract, chưa thực hiện task này.

### 2.6 Hard-stop và dependency map

P01 authority không được bypass. P02 source absence/unsupported/conflict vẫn dừng; P03 facts/scope giữ logic precedence, không đếm subtype đổi do first-failure là “valid adaptation”. Mandatory grounding/citation/number/authority failure không AUTO; INVALID_INPUT và ERROR không là business ESC label. Human override/resume giữ riêng, không training permission.
Guard hiện tạo P04 rồi pipeline catch có thể trả ERROR: report giữ finding này, không sửa technical contract hoặc nới guard. Suspicious-input protection chỉ được claim trong phạm vi sanitize source đã có, không tuyên bố nhận diện mọi injection.

Các thay đổi tương lai cần Task Contract riêng: score provenance/integration/coverage; immutable feedback + adjudication + data partition; shared types/schema migrations; config/version/audit/consumer compatibility; deterministic replay/hard-stop regressions; rollback/kill-switch UI/runtime. Coordinator chỉ mở nghiên cứu thay thế nếu cần; STOP không mở adaptation implementation.

---

### SUPPLEMENT R1 — AC4

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb5727b5a699823963dd42

M3-T02 — OWNER SUPPLEMENT R1 (3/4: AC4 / Offline Verification & Metrics)

## 3. AC4 — Protocol kiểm chứng offline và thước đo

Đây là thiết kế, không bộ test đã chạy. Tiếp tục dùng6 input synthetic C1–C6 trong report cũ; không tạo test file, không import app/DB/call LLM.

### 3.1 Quần thể, labels và metric definitions

Trước so threshold, khóa manifest: case/family IDs, partition, original snapshot hashes, expected routing được adjudicate, hard-stop tags, code/policy/corpus/signal versions, old/new threshold. Chia train/validation theo family để biến thể cùng case không ở hai bên. Một original case tính một lần.
V là toàn bộ validation cases có original snapshots và adjudicated expected route; E⊂V là soft eligible (mandatory checks khác similarity PASS). H là cases hard-stop, không cho vào tuning. Unlabeled/ambiguous/untraceable không vào denominators; báo riêng số bị loại/total. Không loại một case chỉ vì candidate chạy ERROR hoặc prediction chưa có.

Tính metric với frozen E và expected labels:
- N_ESC = count(expected=ESCALATE); FN = count(expected=ESCALATE AND predicted=AUTO_REPLY). MER=FN/N_ESC.
- N_AUTO = count(expected=AUTO_REPLY); FP = count(expected=AUTO_REPLY AND predicted=ESCALATE). OER=FP/N_AUTO.
- N_route = count(predicted AUTO_REPLY hoặc ESCALATE); coverage=N_route/|E|.
- Báo riêng count ERROR, INVALID_INPUT, NOT_VERIFIED hoặc nonbusiness outputs trên E; giữ chúng trong expected-class denominator nhưng không coi là FN/FP thành công. Coverage gate + không tăng failures phải đạt trước khi so J; không dùng lỗi để làm tỷ lệ đẹp.
- N_ESC=0 hoặc N_AUTO=0 → metric tương ứng UNDEFINED (N/A), không ghi0/PASS. Candidate không được accept vì thiếu class coverage. |E|=0 → no assessment/no update.
- MER/OER báo raw FN/N_ESC, FP/N_AUTO, old/new và Δ; kèm uncertainty theo protocol approved sau này. Không có dữ liệu chạy thì NOT MEASURED, không bịa tỷ lệ.
- H: hard-stop violation=count(case có mandatory stop nhưng predicted AUTO). Báo 0/n_H hoặc thực tế; n_H=0 là NOT VERIFIED, không chứng nhận hard safety. ERROR/INVALID_INPUT chỉ đạt tiêu chí dừng tương ứng, không tự chứng nhận đúng business route.
- Theo cohort/request kind/changed stratum báo thêm counts và exclusions; không lấy tổng đẹp để che regression một nhóm.
- Dedupe rejection/update count, step/bounds violation, approval replay/double-apply và rollback agreement có denominator riêng.

ROUTING_CORRECT tham gia E với expected label như nhãn lỗi; nếu chỉ nhận complaint feedback thì population có selection bias, không suy tỷ lệ toàn bộ production. Hard population phải được thiết kế chủ động, không phụ thuộc “không ai phàn nàn”.

### 3.2 Routing flip hợp lệ

Một flip hợp lệ phải có đồng thời:
1. original/new result đều business AUTO_REPLY/ESCALATE; ERROR/INVALID_INPUT/pause/send status không là flip.
2. Input, case clock, extraction, đầy đủ evidence/source/status/conflict/scope, guard artifacts và code/policy/corpus/signal algorithm giữ nguyên; chỉ threshold/version và kết quả predicate phụ thuộc θ được đổi.
3. s thực có provenance/version và boundary cross: khi θ_new<θ_old, θ_new≤s<θ_old; khi θ_new>θ_old, θ_old≤s<θ_new, theo comparator ≥. Case aggregate phải đúng Signal Contract; không chèn giả s=.5 vào score1 runtime.
4. Threshold đổi do eligible adjudicated feedback qua rule mục2, có audit; sửa ENV bằng tay không phải proof automatic adaptation.
5. New route đúng expected adjudicated label, mọi mandatory gates giữ nguyên; retained output/draft phù hợp nhánh. Coverage tất cả request và subtype/reason đúng contract.
Nếu bất kỳ điều kiện thiếu → FLIP_NOT_DEMONSTRATED; không tạo expected giả để PASS.

### 3.3 Rollback correctness

Phải có v0, successful update v1 và rollback append v2 với config_hash(v2)=config_hash(v0), parent/provenance/audit hợp lệ; learner disabled khi rollback và no double-apply.
Replay cùng frozen manifests/artifacts tại v0/v1/v2. So business decision, subtype, rule, failed_checks, evidence IDs, grounding và case status thích hợp; loại fields time/new generated IDs/version ID khỏi equality nhưng phải kiểm riêng audit/provenance.
Yêu cầu r(v2)=r(v0) với mọi case trong frozen rollback suite; nếu thiếu kết quả → NOT VERIFIED, không bỏ case khỏi denominator. Khi v1 có valid flip thì v2 phải phục hồi hành vi v0 của chính case đó.
Không chứng nhận “khôi phục hành vi đã đổi” nếu cả v0/v1 luôn cùng routing vì score1. Không hồi tố approval/sent case và không reset feedback ledger để trigger lại cùng batch.

### 3.4 Matrix C1–C6 bổ sung điều kiện verdict

| Case | Preconditions/old→new | Expected/invariant | Verification/status hiện tại |
|---|---|---|---|
| C1 Routine | Informational, full valid evidence, no lock/mandatory failure; baseline s1, .35→.60 | P05 AUTO→AUTO; pause chỉ đổi send/approval status | Source trace và R5 predicate đã có; E2E DESIGNED/NOT VERIFIED. |
| C2 Borderline | Baseline chỉ s1 hoặc empty, .60→.35; future cần actual real score + eligible batch/version | Baseline không flip. Future phải đạt toàn bộ3.2, giảm lỗi đúng label và giữ mandatory gates | ROUTING_FLIP_NOT_DEMONSTRATED; không yêu cầu Owner tạo score/flip trong task read-only. Theo Coordinator, chứng minh không có boundary là evidence hợp lệ của STOP. |
| C3 Authority | Personal/exception/appeal/authority flag, sources hợp lệ; s1, .35→.60 | P01 luôn giữ stop; downstream technical error vẫn no AUTO | Source precedence; DESIGNED, full pipeline NOT VERIFIED. |
| C4 Unsupported/Conflict/Facts | UNKNOWN/no source/conflict; variant missing facts/scope khi không có prior failure; .35→.60 | P02/P03 theo precedence, no AUTO; không weaken conflict/facts hoặc nhầm subtype | Source + isolated conflict/facts predicate đã chạy trước; full runtime NOT VERIFIED. |
| C5 Rollback | Frozen C1/C2 artifacts; v0→v1→v2 phải persisted/audited compatible | Same behavior v2/v0; demonstrated reversal chỉ nếu v1 có valid flip | Baseline đổi .35→.60→.35 đều invariant, chưa có versions/learner; DESIGNED/NOT VERIFIED, không claim rollback PASS. |
| C6 Unsafe Feedback | Duplicate, ambiguous/no binding, wrong partition, corrupt version, too few samples, admin asks bypass authority | REJECT/KEEP; unchanged active θ, reason audit; hard-stop remains | Proposed rule/design only; learner chưa có nên execution NOT VERIFIED. |

C4 variants cần giữ cả conflict và missing facts để kiểm failed_checks, không chỉ first status. Thêm invalid-input/technical-error cases vào safety suite của task tương lai; phải báo INVALID_INPUT/ERROR riêng, không xem là correct ESC.
Trong task này chỉ execution validator riêng từ báo cáo trước; không chạy6cases/pipeline/learner. Thước đo hiện tại: NOT MEASURED. Bổ sung metric definitions không tạo runtime evidence.

---

### SUPPLEMENT R1 — AC MAPPING & HANDOFF

Nguồn Trello: https://trello.com/c/ShqO507C#comment-6acb572ac646b34838c52e7a

M3-T02 — OWNER SUPPLEMENT R1 (4/4: AC Mapping / Self-check / Handoff)

## 4. AC mapping, self-check và handoff

### 4.1 Mapping đúng checklist và description

- Checklist AC1: evidence source đã PASS; checkbox COMPLETE. Không chứng nhận human-control E2E.
- Checklist AC2: negative finding đã có causal proof + validator corroboration, phù hợp Coordinator Decision; đề nghị Vũ xác nhận PASS. Thay thế FAIL cũ vốn yêu cầu real flip. Checkbox chưa tự tick ở vai trò Owner.
- Checklist AC3: đã bổ sung signal gate/coverage semantics, feedback population gồm correct labels, parameter-selection contract, bounded rule với independent validation, version/audit/rollback/kill switch và contract dependencies. READY_FOR_REVIEW — DESIGN ONLY, không implementation/GO. Giá trị số chưa phê duyệt là activation blocker công khai; mọi gate thiếu giữ disabled. Vũ quyết định thiết kế có đủ tiêu chí nhánh STOP hay cần bổ sung.
- Checklist AC4: đủ6 cases + explicit metric/zero-denominator/coverage/causal-flip/rollback definitions; READY_FOR_REVIEW — DESIGN ONLY. Actual flip/learner/rollback NOT VERIFIED; không phải thiếu test files. Checkbox giữ unchecked tới khi review.
- Checklist AC5: STOP report/handoff có evidence; human Owner self-review và Vũ independent review vẫn PENDING. Không tự PASS.
- Checklist AC6 compliance: COMPLETE theo audit trước; lượt bổ sung tiếp tục repo clean/no runtime LIVE/no A/B. Description AC6 còn self-review+independent review nên vẫn NOT VERIFIED ở phần review.

AC numbers trong description khác checklist ở phần review; map này giữ rõ cả hai. Không đổi wording/names/checklist/state/contract. Owner submission không là Coordinator acceptance.

### 4.2 Codex technical self-check thực tế

Đã đọc Task Contract/checklist9 comments và Coordinator decision trực tiếp; re-verify remote/source/hash/callers. So sánh production delta, bảo lưu pinned report baseline; không biến lịch sử audit thành HEAD hiện tại.
Đã kiểm consistency: finite threshold proof không chỉ sample grid; s=1 không là relevance; mandatory failures có precedence; future signal chỉ proposed và cần contract; population includes ROUTING_CORRECT; independent frozen validation; undefined metrics/technical errors không che rủi ro; step evaluated at serialized candidate; rollback không dùng LLM variation hoặc approval cũ.
Không bịa verdict Vũ/Owner; không claim learner/C1–C6 runtime PASS; chưa có numeric bounds/risk caps hoặc dataset đủ để mở GO.
Đây là self-check kỹ thuật do Codex hỗ trợ, không xác nhận Minh đã đọc/hiểu. Owner cần đăng xác nhận thật sau khi đọc phần bổ sung; việc gửi lệnh “làm phần Owner” không được coi là self-review hoàn thành.

### 4.3 Câu hỏi Vũ cần trả lời

1. Đồng ý routing map tại282 và production equivalence đến16f? Có đường pipeline R4 cấp score thực bị bỏ sót không?
2. Đồng ý proof mọi selected score1 và finite t chỉ accept/reject toàn nhóm; các guard/hard heuristics không là suitable adaptive signal hiện hành?
3. Thiết kế conditional AC3 đã bảo vệ multi-request coverage/mandatory gates và phân biệt complaints trigger với full evaluation population chưa?
4. Metric denominators/undefined/coverage và fixed-artifact flip/rollback protocol đủ AC4 design chưa?
5. Xác nhận C2/C5/C6 execution chưa chứng minh; STOP là feasibility result, không adaptation/M3 gate PASS?
6. Findings guard P04→ERROR và config finite validation cần task riêng; không sửa trongM3-T02?
Vũ cần comment baseline/evidence reviewed, verdict từngAC, issues và recommendation; không chỉ tick checklist.

### 4.4 HANDOFF REPORT — M3-T02 / OWNER SUPPLEMENT R1

Result: READY_FOR_REVIEW. Recommendation: STOP. INDEPENDENT_REVIEW_PENDING.
Baseline: source282c73b7dbf4ac7bf027d5710cce6ed673ab80d1; verified remote16f584fa213416db30b247a431b92fffb94be075; localdev/source baseline; task branch N/A (READ_ONLY).
Changes: evidence supplement AC2, complete conditional protocol AC3, metrics/verification criteria AC4, AC mapping/review packet. Repository files changed0; no branch/commit/PR/merge/schema/policy/interface. Artifact ngoài repository và comments Trello.
Validation: direct ls-remote; localbranch/HEAD/status; GitHub compare/search; source caller trace/hash; consistency review. Validator result viện dẫn execution trước, không chạy lại; tests M3-T01/pipeline/learner/rollback SKIP/NOT VERIFIED.
Evidence: report comments A–L trước đó, DoD audit6acb4edb3eb54171c763bd67, Coordinator decision6acb53f0659eb85cd549fe91, supplement sections1–4. Không có independent review của Vũ trong9comments đọc preflight.
Exit Gate Contribution: feasibility negative evidence + conditional design/risk protocol; actual feedback-driven adaptation chưa đáp ứng; giữ M3_AUTHORIZED_WITH_CARRYOVER, chưa M3 PASS.
Risks: constant score; no real adaptive signal/calibration/labels/binding; proposed params chưa duyệt; guard ERROR contract discrepancy; study/DEV population bias; deadline discrepancy giữ nguyên; human self-review/reviewer pending.
LIVE/API authorization: NONE. Actual Exodia/LLM/provider/email LIVE calls0. Connector Trello/GitHub và git HTTPS chỉ evidence/coordination theo scope; không claim0 network.
Reviewer: Vũ. Approver: Coordinator. Next Dependency: không mở implementation theoSTOP. Alternative signal/routing work chỉ sau Task Contract riêng.
Card: giữ IN REVIEW, complete=false. Không tự change DONE/milestone/dependency. Coordinator xem xét STOP sau Minh self-review và Vũreview.

### 4.5 Mẫu OWNER SELF-REVIEW — chỉ Minh đăng sau khi đọc

OWNER SELF-REVIEW — M3-T02
Owner: Minh. Reviewed at: [thời gian thực tế].
Tôi đã đọc Feasibility Report, Owner Supplement R1 và Coordinator Decision; kiểm tra [liệt kê evidence thực sự đã xem].
Tôi hiểu score1 hiện hành không tạo boundary phân biệt; kết luận STOP chỉ trong scope/baseline khảo sát. Tôi phân biệt source/predicate execution với E2E/learner/rollback chưa được chạy.
Thiết kế AC3 và protocol AC4 là conditional design; numeric parameters/real signal chưa được duyệt. Không đề nghị mở implementation hoặc M3 PASS.
Questions/issues còn lại: [ghi thực tế].
Tôi bàn giao Vũ independent review AC1–AC6; task giữ IN REVIEW, Coordinator nghiệm thu cuối.

Mẫu trên chưa là comment self-review đã hoàn thành. Không thay các chỗ trống bằng hoạt động Minh chưa thực hiện.

---

## Phần III — Publication review & nghiệm thu

### Evidence classification

- **VERIFIED FROM SOURCE (tại 282c73b7dbf4ac7bf027d5710cce6ed673ab80d1):** đường R4→R5→R6; `score=1.0` trên selected evidence; similarity predicate; policy precedence và hard-stop theo source references trong báo cáo.
- **OFFLINE EXECUTED — LIMITED:** validator-only sweep được *báo cáo trong artifact gốc*, không chạy lại trong lượt công bố này; không coi đó là E2E/pipeline validation.
- **DESIGNED NOT EXECUTED:** adaptation candidate, threshold learning, replay/frozen case matrix C1–C6, audit/version store và rollback.
- **NOT VERIFIED:** semantic impact of a real learned threshold; valid actual routing flip; E2E safety; independent review Vũ; human Owner self-review; Coordinator final acceptance.

### DoD mapping và review readiness

| Checklist | Trạng thái evidence hiện có | Trạng thái nghiệm thu |
|---|---|---|
| AC1 — Routing và ngưỡng hiện hành | Routing/source map đã bàn giao | Trello đã tick trước khi công bố |
| AC2 — Signal tác động routing | Negative proof có nguồn; Coordinator chấp nhận cách đánh giá phủ định | Chờ Vũ review |
| AC3 — Cơ chế feedback, bounds, audit, version, rollback | Conditional design R1 đã bàn giao | Chờ Vũ review |
| AC4 — Offline cases và metrics | 6 synthetic cases và định nghĩa MER/OER/coverage; không chạy E2E | Chờ Vũ review |
| AC5 — Báo cáo và independent review | STOP report/handoff có; independent review chưa xác minh | Chưa đạt |
| AC6 — Read-only/LIVE/A-B | Không sửa production; một Markdown công bố theo ngoại lệ Coordinator | Chờ xác nhận ngoại lệ docs-only trong review |

### Một lượt review gộp

Minh tự đọc toàn report và xác nhận những gì thực sự đã đối chiếu, không sử dụng lời khai của Codex thay cho Owner. Vũ review **một lượt duy nhất** trên Draft PR và evidence gốc, bao gồm AC1–AC6, negative proof, tính đầy đủ thiết kế, safety, giới hạn và scope. Coordinator xem xét kết quả, quyết định task DONE hay CHANGE REQUEST, cũng như chấp nhận STOP; không mở adaptation implementation chỉ vì đã xuất bản báo cáo.

**Task vẫn IN REVIEW cho đến khi có quyết định Coordinator.** Không thay `STATUS.md` hoặc M3 gate chỉ vì công bố báo cáo.

### Source/evidence index

- [Task Contract, checklist và comments](https://trello.com/c/ShqO507C)
- [Coordinator Decision về AC2/STOP](https://trello.com/c/ShqO507C#comment-6acb53f0659eb85cd549fe91)
- [Docs-only authorization](https://trello.com/c/ShqO507C#comment-6acb8c73ae8f26b45dddd7e9)
- [Original source checkpoint](https://github.com/ThanhVu165/MLAi_VNG_A/tree/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1)
- [Đối chiếu source checkpoint và pre-publication `dev`](https://github.com/ThanhVu165/MLAi_VNG_A/compare/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1...2a4c7ed15ff5ef2c004bb9a84d84a4e72b77b26f)
