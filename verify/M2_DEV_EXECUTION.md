# M2 Combined DEV Execution Orchestrator — Hướng dẫn và Hợp đồng thực thi

**Phạm vi:** DEV / DIAGNOSTIC, NOT Set B, NOT final independent evaluation.
**Mặc định:** OFFLINE MOCK. API/CLI cũ giữ nguyên mock-only; entrypoint riêng `verify.m2_dev_live` đã triển khai nhưng chưa được chạy LIVE, đang chờ Independent Code Review và phê duyệt run riêng.
**Fixture:** `verify/cases_m2_combined_dev.json`
**Expected SHA-256 (final bytes):** `d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04`

---

## 1. Tải và xác minh Frozen Cases (`load_frozen_cases`)

Module `verify/m2_dev_execution.py` tải toàn bộ 12 frozen cases từ fixture preregistration:
- Đối chiếu chính xác SHA-256 final-bytes của fixture file. Mọi sai khác dù chỉ một byte đều kích hoạt fail closed: `BLOCKED_FIXTURE_HASH_MISMATCH`.
- Kiểm tra danh sách case IDs: đúng 12 ID duy nhất (`M2DEV-A1`..`A4`, `M2DEV-B1`..`B4`, `M2DEV-C1`..`C4`).
- Kiểm tra phân bổ expected gold: P01 = 3, P02 = 3, P03 = 2, P05 = 4; AUTO_REPLY = 4, ESCALATE = 8.
- Kiểm tra input schema: `sender`, `subject`, `body`, `received_at` (bắt buộc timezone-aware ISO-8601), `channel = "verify"`, `external_id = null`.
- Kiểm tra metadata: `status = "GOLD_VERIFIED_READY_FOR_FREEZE"`, danh sách `pass_criteria`, `fail_signals`, `forbidden_assumptions`.
- Không tự ý sửa đổi, phục hồi hay tái định dạng dữ liệu (no silent repair).

---

## 2. Hợp đồng Identity tại ranh giới gọi (`Invocation Boundary`)

Ranh giới gọi pipeline là điểm then chốt đảm bảo tính xác thực của dữ liệu:
1. **Khởi tạo payload gửi đi:** Tạo đối tượng `CaseInput` chuẩn từ dữ liệu case đã freeze (với `external_id=None` theo đúng fixture).
2. **Snapshot phòng vệ:** Tạo snapshot bản sao sâu (`deepcopy`), tính `submitted_input_sha256` qua `dev.input_hash(snapshot)`.
3. **Đối chiếu tiền thực thi:** Đối chiếu `submitted_input_sha256` với `expected_hash` từ fixture. Nếu sai lệch, fail closed ngay lập tức (`INPUT_IDENTITY_MISMATCH`).
4. **Gọi adapter:** Operational chỉ gọi built-in mock; injected adapter chỉ qua API test-only với socket/provider guards.
5. **Kiểm tra chống sửa đổi payload:** Tính lại `dev.input_hash(submitted_payload)` sau khi adapter hoàn thành. Nếu adapter làm biến đổi payload, kích hoạt `INPUT_IDENTITY_MUTATED`.
6. **Ràng buộc Execution Context:** Khởi tạo `dev.execution_context()` liên kết chặt chẽ payload snapshot, `PipelineResult`, case ID và observation ID. Context này kiểm tra:
   - `context.case_id == case_id`
   - `context.observation_id == observation_id`
   - `context.result_case_id == result.case_id`
   - `context.result_trace_id == result.trace_id`
   - `actual_hash == expected_hash`
7. **Bảo toàn dữ liệu:** Không suy diễn hay tự tái tạo email từ kết quả sau khi chạy xong.

---

## 3. Hợp đồng Execution Adapter và Chế độ Mock-Only

- Giao diện adapter tối giản:
  ```python
  class ExecutionAdapter(Protocol):
      adapter_id: str

      def __call__(
          self,
          case_spec: dict[str, object],
          submitted_input: CaseInput,
          observation_id: str,
          mode: str,
      ) -> PipelineResult | AdapterOutput: ...
  ```
- **DeterministicMockAdapter:**
  - Được dán nhãn rõ ràng là **SYNTHETIC**.
  - Không gọi `process_case()` thật, không gọi `infra.llm.call_json()`, không kết nối mạng.
  - Trả về `PipelineResult` hợp lệ kèm `AdapterOutput` mang nhãn config an toàn (`LLM_MODE: replay`).
  - Hỗ trợ các kịch bản mô phỏng lỗi kỹ thuật (`force_error`), exception của adapter (`force_adapter_exception`), và options chứa rủi ro (`unsupported_options`).
- **An toàn thực thi offline:**
  - `orchestrate_m2_dev_run()` chỉ nhận exact type `DeterministicMockAdapter`, không nhận subclass hoặc `custom_result_factory`. Default tự tạo built-in mock. Custom adapter dù tự khai `is_offline_mock=True` vẫn bị reject trước khi gọi.
  - `orchestrate_m2_dev_test_run()` là boundary **TEST-ONLY** để simulate mutation, malformed output, exception; caller tests phải chặn socket/provider/pipeline thật. CLI không gọi boundary này, không có module/plugin/adapter loading.
  - Thuộc tính Python không chứng minh network isolation. Built-in source là trust boundary; đây không phải sandbox chống code Python có quyền monkeypatch hoặc gọi trực tiếp test API.
  - Mọi yêu cầu chạy ở chế độ `LIVE` (qua CLI `--live` hoặc tham số `mode="LIVE"`) đều bị từ chối dứt khoát với:
    `LIVE_EXECUTION_NOT_ENABLED`

---

## 4. Tích hợp Capture và Assessment

- Mỗi lượt chạy hợp lệ được đưa qua:
  1. `dev.execution_context(...)`
  2. `dev.capture_result(...)`
  3. `dev.write_artifacts(...)`
- Không bao giờ gán nhãn lại kết quả âm thầm để làm cho kết quả khớp với expected gold.
- Capture giữ nguyên vẹn kết quả thô, telemetry sẵn có (attempts, logical calls, cost đều là `null` nếu không đo được).
- Đánh giá rubric tự động 10 dimensions. Mọi ca chuyển tiếp ngữ nghĩa khi chưa có human review schema v2 đều dừng ở verdict:
  `REVIEW_REQUIRED` (không bao giờ tự ý cho full `PASS`).
- Các ca có options chứa dữ liệu không có căn cứ (ví dụ: *"gia hạn 3 ngày"*, *"hoàn 50%"*) được ghi nhận rõ trong `risk_findings` và giữ ở `REVIEW_REQUIRED` hoặc `FAIL`.

---

## 5. Cấu trúc Artifacts và Bảo vệ đường dẫn (`Path Traversal`)

Mỗi lần chạy tạo một thư mục độc lập dưới `data/validation/` (hoặc do caller chỉ định qua `--output-dir`):
```text
<output_dir>/
├── run_summary.json       # Báo cáo tổng hợp JSON cho toàn bộ 12 cases
├── run_report.md          # Báo cáo tổng quan Markdown
└── cases/
    ├── M2DEV-A1/
    │   ├── capture.json
    │   ├── assessment.json
    │   └── report.md
    ├── ...
    └── M2DEV-C4/
        ├── capture.json
        ├── assessment.json
        └── report.md
```
- **Chống ghi đè:** Nếu thư mục đích đã tồn tại, orchestrator từ chối thực thi với `FileExistsError("ARTIFACT_DIRECTORY_EXISTS")`.
- **Chống Path Traversal:** Case IDs, Observation IDs và Run IDs đều được xác thực qua regex `^[A-Za-z0-9_-]+$`. Mọi đường dẫn con đều được kiểm tra `resolve().is_relative_to(output_dir)`.
- **Bảo mật:** Không lưu API keys, tokens, Authorization headers hay raw request/response bodies vào artifacts.

---

## 6. Kiểm soát Ngân sách (`Live Budget Controls`)

Nguồn authoritative duy nhất: structured ledger `reports/sprints/M2_live_budget.json`.
Progress log append-only chỉ là lịch sử, **không có fallback** lấy match đầu/cuối.
Task 1 đã tạo ledger được Coordinator xác nhận: **BUDGET_VERIFIED**, baseline3/45,
remaining42 (nguồn xác nhận hiện tại ở mục 10, không suy từ progress cũ).

Ledger schema v1 (một JSON object, không duplicate keys):
- `schema_version`: 1.
- `baseline`: `total`=45, `consumed` integer 0..45, `confirmed_by`,
  timezone-aware `confirmed_at`, `reconciliation_reference` không rỗng.
- `attempts`: danh sách unique observation_id; mỗi event có `case_id`,
  `started_at` timezone-aware, `status` và `internal_retries` integer >=0.
- `current`: `total`, `consumed`, `remaining` phải khớp baseline + số attempted IDs.
  Không chấp nhận nhiều current/baseline records, duplicate IDs, bool thay integer,
  totals khác 45, negative/over-total hoặc consistency mismatch.

Baseline chỉ được tạo trong task được coordinator cấp phép sau khi reconcile
**mọi observation M2 Goal thuộc contract**, gồm technical attempts, với artifacts.
`confirmed_by` và reference là evidence metadata, không phải chữ ký số hay xác thực
coordinator. Không copy một historical line vào ledger rồi coi là verified.
Task 1 tạo ledger authoritative theo xác nhận mới; không debit ngân sách thật.
Các ledger tests chỉ ở tmp_path và được đánh dấu synthetic.

`verify_live_budget(ledger_path)` fail closed khi thiếu/hỏng/chưa confirmed.
`check_budget_authorization(..., is_live=True)` đọc lại ledger, không nhận dataclass
budget_info tự khai hoặc progress_path. Mock có thể chạy với ledger unavailable,
nhưng summary phải ghi unverified/null counts và `live_consumed_this_run=0`;
không suy unknown consumed thành zero. Ledger hợp lệ chỉ xác nhận quota, không bật LIVE.

Future accounting interface `record_live_observation()`:
1. Trước invocation, persist `ATTEMPTED` cho fresh observation_id: debit đúng 1.
   Nếu ledger/lock/write/validation fail, caller **không được gọi pipeline**.
2. Sau result hoặc exception, finalize cùng ID thành `SEMANTIC_RESULT` hoặc
   `TECHNICAL_FAILURE`; count không đổi. Crash chưa finalize vẫn giữ debit.
3. Internal technical retries ghi vào `internal_retries`, không tạo independent IDs.
   Một lần chạy độc lập tiếp theo mới có fresh ID và debit mới.
4. Không giảm/release consumption vì không có semantic result. Duplicate start,
   finalize ID chưa start hoặc re-finalize bị reject. Mock không gọi API accounting.

Writer dùng exclusive lock file, validates dưới lock, flush/fsync temporary file
cùng directory rồi atomic replace ledger. Stale lock sau crash cần coordinator
reconcile, không tự unlock để chạy. File trust vẫn cần bảo vệ bên ngoài: không phát
hiện rollback/tampering bởi người có quyền ghi toàn bộ ledger; không bảo đảm transaction
xuyên host hoặc disk durability tuyệt đối. Entrypoint riêng ở mục 10 sử dụng writer này trước invocation.

---

## 7. Phân loại lỗi kỹ thuật và Fail-Safe

Orchestrator phân định rõ ràng các loại lỗi:
1. **Lỗi kỹ thuật pipeline (`Decision.ERROR` hoặc `CaseStatus.ERROR`):** Giữ nguyên verdict là `TECHNICAL_ERROR`. Tuyệt đối không biến thành chuyển tiếp nghiệp vụ P01/P02/P03.
2. **Exception tại Adapter:** `execution_failure.json` chỉ có `case_id`, `observation_id`,
   `timestamp`, `technical_status="ADAPTER_EXCEPTION"`, `error_category`,
   `error_code="ADAPTER_INVOCATION_FAILED"` và optional allowlisted `exception_class`.
   Exact built-in RuntimeError/TypeError/ValueError/TimeoutError/OSError map sang mã
   chuẩn; subclass/unknown type thành `UNCLASSIFIED_ADAPTER_ERROR`, không lưu tên class.
   Không đọc/lưu `str(exc)`, `repr(exc)`, traceback, raw request/provider response hay
   email body từ exception. Aggregate chỉ giữ trạng thái/IDs, không mang error message.
   Không bịa PipelineResult; adapter exception vẫn riêng với Decision.ERROR.
3. **Lệch định danh (`Identity Mismatch`):** Báo lỗi và dừng/khóa case, không ghi capture thành công giả tạo.
4. **Lỗi ghi đĩa / Assessment:** Giữ capture thô, báo cáo lỗi và fail closed.
5. **Chưa có Human Review:** Giữ nguyên trạng thái `REVIEW_REQUIRED`, không tự động đánh dấu PASS.

---

## 8. Giới hạn tin cậy (`Trust Limitations`)

- Việc `PipelineResult` mang đúng `case_id` và `trace_id` chưa phải là bằng chứng tuyệt đối chứng minh model đã thực sự đọc email đó nếu adapter không được kiểm chứng độc lập.
- Kết quả chạy OFFLINE MOCK chỉ chứng minh tính toàn vẹn của đường ống tích hợp và hợp đồng dữ liệu, không chứng minh chất lượng quyết định của mô hình LLM.
- Toàn bộ kết quả trong chế độ mock đều mang nhãn **SYNTHETIC** và không được dùng để nghiệm thu tiêu chí M2 Goal.

---

## 9. Các bước bắt buộc trước khi thực hiện lượt chạy LIVE trong tương lai

Trước khi tiến hành lượt chạy LIVE (sẽ được phê duyệt trong task riêng):
1. Coordinator independent integration review corrective patch và offline evidence mới.
2. Xác nhận môi trường OpenAI provider và khóa API hợp lệ trong môi trường chạy được cấp phép.
3. Kiểm tra tính sẵn sàng của 6 tài liệu quy định seed (72 chunks) trong cơ sở dữ liệu kiểm thử.
4. Kiểm ledger authoritative và quota đủ cho đúng danh sách cases được cấp phép, không suy từ progress lịch sử.
5. Chỉ chạy entrypoint riêng khi có phê duyệt run; API/CLI mock cũ tiếp tục reject LIVE.

## 10. Entrypoint LIVE riêng — triển khai offline, chưa thực thi LIVE

`verify/m2_dev_live.py` tái sử dụng frozen loader, budget ledger, capture và assessment;
không thay đổi production rules, fixture/gold hoặc test-only injection boundary.

- `run_live_cases()` mặc định `enabled=False`. Cần `LiveRunAuthorization` chứa run ID,
  đúng tuple case IDs, max cases, positive finite max cost USD và approval reference.
- CLI mặc định offline một case A1, kể cả môi trường `LLM_MODE=live`. LIVE cần
  `--execute-live`, từng `--case`, `--run-id`, `--authorize-run` trùng run ID,
  `--approval-reference`, `--max-cases`, `--max-cost-usd`, `--output-dir` mới.
  Không có mặc định all12, custom adapter loading hay gold-driven output.
- Các trường authorization ghi nhận quyết định của Coordinator qua trusted caller;
  không phải chữ ký số hoặc xác minh danh tính người phê duyệt. Task này chỉ cho phép
  triển khai offline, không cấp phép một run LIVE cụ thể.
- Ledger `reports/sprints/M2_live_budget.json` schema v1: total45, baseline3,
  remaining42, attempts[]. Nguồn là xác nhận trực tiếp của Coordinator ở task hiện tại,
  reconciliation report và việc Anti review hoàn tất **theo attestation Coordinator**;
  không tự tuyên bố đã đọc một Anti artifact chưa được cung cấp. Timestamp là lúc
  ghi nhận xác nhận hiện tại, không backdate thời điểm của observations lịch sử.
- Verify toàn bộ quota yêu cầu trước run; durable ATTEMPTED trước adapter; finalize
  cùng ID. Technical/exception vẫn debit1; retry metadata không tạo observation mới.
  Nếu finalize lỗi/crash, ATTEMPTED còn nguyên để reconcile, không tự refund/rerun.
- `LivePipelineAdapter.invoke()` đặt default DB vào một fresh per-observation DEV DB,
  initialize rồi mới import pipeline/corpus (corpus import có auto-seed). Seed canonical
  six documents/72 chunks; không dùng `data/app.db`. Khôi phục DB/env trong finally.
  Đây là standalone sequential runner, không chạy cùng process app/threads khác.
- Payload frozen được snapshot/hash trước invocation và kiểm mutation sau invocation.
  `process_case(payload, actor="SYSTEM", case_id=observation_id)` giữ ID thực cùng
  trace thực. Capture/assessment cũ nhận execution context thật; chưa review giữ
  REVIEW_REQUIRED. LIVE manifest phân biệt `is_synthetic_execution=False`; seed vẫn
  là synthetic corpus, không đồng nghĩa dữ liệu production.
- Provider cố định OpenAI/gpt-6-luna, reasoning none, live/cache0: replay/record OFF,
  không fallback. Runtime limits lấy production hiện tại, không override.
- Passive observer chỉ giữ allowlisted provider_attempt metadata; không format log
  message hoặc exception. Adapter failure dùng allowlisted category của orchestrator
  cũ, không đọc/lưu str/repr/traceback. Không ghi env/credentials vào manifest.
- Production telemetry hiện không có billed USD: `cost=null`. Runner dừng trước
  case kế tiếp với COST_TELEMETRY_UNAVAILABLE, không giả định 0. Khi có cost hợp lệ,
  cumulative cost >= approved cap dừng trước lượt tiếp theo. Đây không phải hard
  billing cap cho một observation đang chạy; không tự suy giá từ tài khoản ~10 USD.
- Artifacts: live_manifest.json, cases/<case>/capture.json và assessment files theo
  runner cũ, databases/<case>.db, progress_<n>.json, run_summary.json; adapter exception
  có execution_failure.json. Directory/observation ID không được reuse.

Validation Task 1: 116 PASS / 0 FAIL / 0 SKIP (24 LIVE-boundary offline tests,
43 orchestrator, 48 assessment, 1 frozen harness manifest). Guards chặn socket,
provider và production process_case; adapter integration chỉ dùng test monkeypatch.
Không dùng kết quả fake để khẳng định LIVE model adherence. LIVE/API calls = 0.

## 11. Task 2 — correction telemetry/cost (chỉ validation offline)

Phần mô tả thiếu usage/cost trong Task 1 ở trên là baseline trước correction này.
Không cập nhật lại artifacts hoặc verdict Probe 01.

- Emitter/observer dùng UUID correlation ngẫu nhiên qua ContextVar theo đúng case;
  raw case ID vẫn đi qua sanitizer cũ. UUID không được tính từ credential hoặc case ID.
  Context được reset trong finally; event case khác/correlation khác không được nhận.
- `_request_openai` chỉ trích input/output counts, optional cached/cache-write counts,
  model và service tier từ response; không serialize response, headers hoặc payload.
  Missing/malformed usage giữ null. Usage accessor lỗi không thay đổi business result.
- Provider attempts chỉ đếm `llm_provider_attempt`; `llm_provider_attempt_skipped`
  không phải API call hoặc transport retry. Logical calls nhóm theo `call_id`, kể cả
  skipped; latency logical là tổng attempt elapsed + backoff đã ghi, không phải toàn
  wrapper latency. Retries là started attempts có `attempt_index>1`.
- Giá xác minh ngày 2026-10-09 từ
  https://developers.openai.com/api/docs/models/gpt-6-luna và
  https://developers.openai.com/api/docs/pricing. Chỉ exact model gpt-6-luna,
  response service_tier=default, global text endpoint hiện tại. Không suy giá cho
  snapshot/tier/model khác hoặc regional premium; trường không rõ giữ unavailable.
- Standard USD/1M: input0.10, cached0.01, cache-write0.125, output0.50. Estimate
  thận trọng dùng **toàn input × cache-write rate**, không trừ cache discount;
  long context >272000 input tokens nhân input2 và output1.5 cho cả request.
  Với input I, output O: `(I*0.125 + O*0.50)/1e6` ở short context.
- Pricing metadata ghi source, verified_on, phạm vi áp dụng. Guard local chỉ cho
  phép bảng giá từ 2026-10-09 đến hết 2026-10-16; đây là hạn revalidation tự đặt,
  không phải OpenAI cam kết giữ giá đến ngày đó. Hết hạn giữ UNAVAILABLE.
- Tổng estimate cộng **mọi started attempt**, không bỏ retry thất bại. Nếu bất kỳ
  started attempt thiếu usage (timeout/refusal/parse failure có thể không giữ usage),
  hoặc không có events đáng tin cậy, cost=null và dừng trước observation tiếp theo.
- `diagnostics.cost` và aggregate `observed_cost_usd` là **ESTIMATED_USD**, không
  billed cost; metadata và `cost_kind` ghi rõ. Estimate >= approved cap dừng lượt tiếp
  theo; không bảo đảm hard cap cho invocation đang chạy, không áp token/attempt limit mới.
- Nếu future observation vẫn thiếu telemetry, chỉ chạy tuần tự từng observation
  theo Coordinator approval; không tiếp tục batch, không tự gọi billing API.

Correction tests mock SDK, chặn socket/provider/pipeline thật; không LIVE/API.
Frozen fixture/gold/rubric và ledger4/45 remaining41 không đổi.
