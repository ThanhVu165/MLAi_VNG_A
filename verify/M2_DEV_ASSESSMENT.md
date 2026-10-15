# M2 Combined DEV capture & assessment — OFFLINE interface

Phạm vi DEV / DIAGNOSTIC, NOT Set B. Module này không có LIVE orchestrator,
không gọi pipeline/provider, không sửa `harness._matches()` hoặc production guards.
Fixture phải giữ SHA-256 final bytes:
`d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04`.
Mọi capture/assessment đều kiểm hash này; sai hash thì fail closed.

## Interface cho task execution tương lai

Caller phải ghép đúng submitted payload với `PipelineResult` tại ranh giới gọi
pipeline trong task tương lai. `PipelineResult` không chứa email gốc; module kiểm
binding được cung cấp, không tự quan sát hay chứng minh invocation thực tế.
Không dùng ví dụ dưới đây để tạo/chạy observation trong task offline:

```python
from pathlib import Path
from verify.m2_dev_assessment import (
    CaptureDiagnostics, execution_context, capture_result, write_artifacts,
)

context = execution_context(
    actual_submitted_input,             # payload thực đã gửi; KHÔNG thay bằng fixture
    existing_pipeline_result,
    case_id="M2DEV-A1",
    observation_id="observation-1",
)

captured = capture_result(
    existing_pipeline_result,
    case_id="M2DEV-A1",                 # frozen fixture ID
    observation_id="observation-1",     # fresh identity do caller cung cấp
    execution=context,
    config={"LLM_PROVIDER": "openai", "OPENAI_MODEL": "gpt-6-luna"},
    diagnostics=CaptureDiagnostics(),
)
assessment = write_artifacts(Path("fresh-assessment-directory"), captured)
```

### Contract identity và canonical input

`ExecutionContext` chứa case/observation IDs, result case/trace IDs, submitted input,
submitted-input hash và frozen-input hash. Module tự tính lại cả hai hash từ hai
payload riêng, đối chiếu claimed hashes, so input hashes và result IDs trước capture
và khi reassessment. Thiếu context/payload, sai hash/ID/input đều fail closed.
Capture cũ không có identity không được chấm PASS.

Canonical input gồm đúng `sender`, `subject`, `body`, `received_at`, `channel`,
`external_id` (mặc định null); field khác bị reject. Text chuẩn hóa Unicode NFC,
giữ nguyên case, whitespace và line breaks. Timestamp phải timezone-aware, chuyển
UTC ISO với microseconds sáu chữ số. Serialize JSON UTF-8, không escape Unicode,
sort keys, separators compact; SHA-256 trên bytes này. `external_id` được tính vào
hash, không loại trừ như metadata: fixture null thì submitted payload phải null.
Fresh observation/result IDs cung cấp execution identity riêng.

Fixture hash xác định toàn bộ frozen file bytes; input hash xác định canonical
business payload; observation ID phân biệt lần quan sát; result IDs liên kết result;
capture hash bind toàn bộ capture **bao gồm identity** với review. Canonicalization
chấp nhận NFC tương đương và cùng instant khác timezone, không phải byte-for-byte
equality của raw email. Caller vẫn có thể khai sai payload/result; module không
authenticate caller và không chứng minh một result thực sự do payload đó tạo ra.

Capture giữ result ID/trace ID/status, full decision/rule/type/reason/evidence IDs,
selected chunk IDs/doc IDs/text/phạm vi, extraction (trừ raw provider JSON),
full card summary/facts/basis/question/options/partial draft, draft subject/body/
citations/grounded/guard failures, corpus version và thời gian/stage latency có sẵn.
Không thay đổi result gốc. Config chỉ nhận allowlist nhãn, không đọc environment.
Các token/key patterns được redact; telemetry chỉ nhận metadata allowlist,
không nhận prompt/body. Dữ liệu này chỉ dùng cho frozen synthetic DEV cases.

Diagnostics do caller cung cấp khi thực sự có: provider attempts, logical calls,
cost, source status snapshot, guard failures, sanitized error class/stop reason.
`null` nghĩa là **UNAVAILABLE**, khác `[]` nghĩa đã đo và không có event.
Không suy attempt/cost/guard success từ số stage hoặc final card. EvidenceChunk
không chứa source status; không tra corpus hiện tại để giả làm status lịch sử.

## Automatic checks và review

| Dimension | Tự động | Còn cần người đối chiếu |
| --- | --- | --- |
| decision/type/rule match | So exact với frozen gold | Không được override |
| case status consistency | Route so với status tại completion | Không được override |
| technical error | ERROR decision/status hoặc TECHNICAL_ERROR rule | Tách khỏi semantic escalation |
| grounding/citation | FAIL nếu thiếu auto draft, guard xác nhận draft không grounded, thiếu citation hoặc citation ngoài selected evidence | Entailment, coverage, approval, current policy, user claim vs fact |
| question/options | FAIL nếu thiếu/question không có `?` cuối hoặc options rỗng | Câu hỏi đúng đối tượng, factual option vs placeholder/quotation |
| temporal safety | Cung cấp ngày Việt Nam từ frozen received_at (+07:00) | B1/B2 tuần học, C1 hôm nay, C2/C3 ngày tương đối/explicit, C4 nguồn cũ |
| selective conflict | Route correctness đã kiểm riêng | A2 P01 priority; B3 giữ 70/60; B4 không trả lời refund không được hỏi |

Keyword/numeric findings chỉ đánh dấu vị trí cần đọc. Không có match không chứng
minh PASS; quotation, hearsay, source comparison hoặc tentative wording không bị
auto FAIL chỉ vì có số. Một approved refund claim unsupported chỉ thành definitive
FAIL khi guard evidence hoặc human review xác lập rõ, không do regex đơn lẻ.
Source SUPERSEDED được đưa cho review để phân biệt historical comparison với
current authoritative basis. Các dimension không áp dụng ghi NOT_APPLICABLE.

## Human review riêng, không ghi đè raw capture

Bundle mới gồm `capture.json`, `assessment.json`, `report.md`; có review thì thêm
`human_review.json`. Không overwrite directory đã tồn tại. Reassessment tạo bundle
mới; capture cũ không bị sửa. `capture_sha256` là hash canonical JSON của capture
(sort keys, indent 2, UTF-8; không gồm newline cuối file), không phải hash file bytes.

`HumanReview` schema v2 có reviewer, reviewed_at timezone-aware, capture_sha256,
`criteria` và optional `dimension_reviews`. Mỗi CriterionReview chứa criterion_id
và `judgments`: từng judgment có dimension, PASS/FAIL, rationale không rỗng và
evidence (`path`, `quote`). Không còn `criteria_refs` tùy ý. CLI reject schema cũ
có `decisions` hoặc thiếu schema_version=2/criteria; không nâng cấp ngầm.

`verify/m2_dev_rubric.py` định nghĩa mapping tường minh cho toàn bộ 12 cases.
Mỗi tuple theo đúng index frozen `pass_criteria`, `fail_signals`,
`forbidden_assumptions`; key criterion là `group:index`. Mã D/E/R tương ứng
decision/type/rule; G grounding/citation/claim/coverage; Q question; O options;
T temporal/current policy; S selective conflict. Multi-code yêu cầu judgment cho
**tất cả** dimensions đó. Mapping không suy từ nhãn reviewer, không đổi frozen rubric.
Ví dụ A1 `pass_criteria:1` yêu cầu G/Q/O, không thể cover bằng rule_id.

Evidence phải thuộc roots cho dimension và quote exact substring tại JSON pointer
trong capture. PASS còn yêu cầu các full-scope quotes do `review_scope()` cung cấp:
G/S toàn card/draft và selected evidence; T toàn card/draft và submitted input;
Q toàn question; O toàn options; D/E/R exact decision field. Evidence thiếu scope
giữ REVIEW_REQUIRED; một câu summary chung không chứng minh tất cả claims/options.
FAIL được dẫn exact snippet của vi phạm. PASS ở fail/forbidden criterion nghĩa
reviewer xác nhận condition đó **không xảy ra**, không phải condition xảy ra.

Mỗi criterion PASS chỉ khi mọi required judgment PASS; thiếu judgment/criterion
giữ REVIEW_REQUIRED; bất kỳ judgment FAIL tạo criterion FAIL. Unknown/duplicate
criterion, sai/duplicate dimension, contradictory automatic verdict, sai capture
hash, quote/pointer sai, thiếu rationale/evidence bị reject. Automatic PASS/FAIL/N/A
không bị override. Supplemental `dimension_reviews` chỉ chấm dimension không được
mapping dùng; không cover criterion. Full PASS cần tất cả applicable checks và
mọi criterion PASS; technical error vẫn ưu tiên TECHNICAL_ERROR.

Ba loại evidence khác nhau: automatic checks chứng minh điều kiện cấu trúc;
pointer/quote và full-scope validation chứng minh integrity/coverage của text;
PASS/FAIL semantic là **judgment của reviewer**. Full-scope quotes vẫn không chứng
minh entailment hoặc reviewer hiểu đúng. Không authenticate reviewer hay gọi
đây là independent evaluation. Synthetic full-PASS test kiểm contract schema,
không chứng minh semantic truth của 12 frozen probes.

```text
python -m verify.m2_dev_assessment --capture old-bundle/capture.json --review review.json --output new-bundle
```

CLI chỉ assessment từ file; không có chế độ execute/live. Overall precedence:
TECHNICAL_ERROR → FAIL → REVIEW_REQUIRED → PASS. Correct route một mình không đủ PASS.
Điều kiện trước DEV LIVE: coordinator review runner này trong task riêng.
