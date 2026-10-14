# M6-T04-HF1 — Restricted Public DEMO Access Hotfix

Ngày xác minh: 2026-10-14
Kết quả self-review của Coordinator/Owner: **READY_FOR_COORDINATOR_ACCEPTANCE** — chưa merge, chưa deploy public, chưa đánh DONE.

## Security remediation

- `SECRET_EXPOSED_KEY`: **REVOKED** — Coordinator xác nhận.
- `USABLE_LOCAL_API_KEY`: **ABSENT / NOT USED**.
- `LIVE_AUTHORIZED`: **NO**.
- `EXPECTED_LIVE_CALLS`: **0**.
- LIVE/API thực tế: **0**; email thật: **0**; chi phí: **$0**.
- Secret scan trên diff: 0 chuỗi dạng API key, 0 Authorization header, 0 private-key block.

## Baseline, branch và tested SHA

- Baseline: `origin/dev@eaaeea88a59618b49219a20ae01a3cf3227cec87`.
- Branch: `sprint/m6-t04-restricted-demo`.
- Tested code SHA: `4af03638faabe59d6f8da15e0f418c76a77e8906`.
- Hai commit local-only `f3cb74b` và `1b64c49` vẫn được giữ nguyên trên branch cũ; không cherry-pick, rebase, reset hoặc squash vào hotfix.

## Thiết kế authorization

- `APP_MODE` là cấu hình phía server; mặc định `restricted_demo`, giá trị ngoài `private|restricted_demo` fail closed.
- Restricted mode bắt buộc `LLM_MODE=replay`; `live` và `record` bị chặn trước provider. Worker nền không khởi động; gọi trực tiếp worker/dispatch cũng bị deny.
- Actor của canonical DEMO và Verify bị ép thành `SYSTEM` phía server. Chuỗi actor do client cung cấp không cấp quyền.
- `schedule_auto_reply()` yêu cầu object capability có identity do module server tạo và chỉ pipeline truyền. `ADMIN:*`, `HUMAN:*`, `SYSTEM` hoặc actor tùy ý không thể tái tạo capability bằng chuỗi; guard chạy trước kiểm tra decision, deadline, transaction và audit.
- `authorize_demo_action()` đặt trước side effect tại admin controls, dispatch, worker/R11, corpus intake/workflow/lifecycle và các SQL mutation trực tiếp của trang hàng duyệt.
- Không dùng SQLite authorizer: connection factory dùng chung cho startup/seed và pipeline được phép; authorizer ở đây dễ phá các luồng hợp lệ nhưng vẫn không thay thế service authorization. Không đổi schema.
- Ownership public dùng danh sách case ID trong Streamlit session. Recent list, `?case_id=`, audit và raw case chỉ đọc case thuộc session hiện tại; audit chỉ hiển thị dữ liệu masked/synthetic cho phép.

## Public capabilities

Guest được phép chạy ba canonical sample, Verify4, giữ form nhập tự do, xem kết quả/evidence/audit của case thuộc phiên. Guest không được mở hàng duyệt, đo lường toàn cục, pause/resume, retry, cancel/escalate thủ công, correction/override, approve/reject hoặc mutation corpus.

Do schema hiện tại không có durable session ownership, safe cancel/escalate cũng bị deny trong HF1. Đây là lựa chọn fail closed; không thêm migration trái contract.

## Canonical DEMO

Ba sample dùng payload recorded cố định, gồm `received_at`, và chạy qua pipeline dùng chung:

| Sample | Kết quả replay |
|---|---|
| Hỏi lệ phí phúc khảo | `AUTO_REPLY / P05` |
| Xin phúc khảo trễ | `ESCALATE / P01 / AUTHORITY_REQUIRED` |
| Văn bản rèn luyện áp dụng | `ESCALATE / P03 / FACT_UNRESOLVED` |

Không sửa cassette, prompt/schema/model, policy hoặc expected labels.

## AC1–AC7

| AC | Kết quả | Bằng chứng |
|---|---|---|
| AC1 — Guest Authorization | PASS | Fake `ADMIN:fake`, `HUMAN:fake`, `SYSTEM` và actor tùy ý không schedule được; query-param case spoof bị từ chối. |
| AC2 — Backend Enforcement | PASS | Direct `schedule_auto_reply`, admin/dispatch/worker/R11 và SQL helper bị deny trước side effect; status, deadline và `SEND_SCHEDULED` không đổi. |
| AC3 — Corpus Safety | PASS | Direct ingest và lifecycle mutation bị deny; trang corpus restricted chỉ đọc. |
| AC4 — Public Demo Workflow | PASS | Canonical sample hit replay; Verify4 chạy; free-form UI còn nguyên; arbitrary input báo lane chưa bật và không persist. |
| AC5 — Regression | PASS có ghi chú | Verify4 4/4, BASE24 24/24 hit, targeted 180/180. Full suite có đúng 16 drift-lock fail lịch sử; 703 test còn lại PASS, real regression = 0. |
| AC6 — External Effects | PASS | Network/provider bị chặn trong test; LIVE/API/email thật = 0; cost = $0; rejected actions không đổi DB. |
| AC7 — Evidence | PASS | Report, tested SHA, commands/results, limitations và self-review trên PR #53 đã có. Coordinator xác nhận single-operator mode. |

## Verify và replay

- Verify4 trong `restricted_demo`: **4/4 PASS**, 0,86 giây.
- BASE24 replay audit: **24 cassettes, 24 logical calls, 0 replay failure, LIVE=0**.
- BASE24 manifest vẫn `NOT_APPROVED` vì provenance/authorization của recorded pack là `MISSING`; HF1 không sửa provenance hoặc cassette. Audit exit code thực tế là **2**: coverage 24/24 thành công nhưng pack chưa được phê duyệt.
- Escalation5 có ba trạng thái riêng: public restricted UI **không expose**; restricted CLI bị whitelist deny trước replay và trả 0/5 `TECHNICAL_ERROR`; private replay **0/5** vì thiếu 5 cassette R2. Không có business escalation giả và không record cassette.

## Input và security validation

- Body public tối đa 5.000 ký tự, text-only, reject trường rỗng/NUL/oversized trước persistence.
- Arbitrary input khi LIVE chưa được cấp quyền bị từ chối trung thực trước khi tạo case ở UI/worker.
- Gọi pipeline trực tiếp với replay miss trả `ERROR / TECHNICAL_ERROR`, không tạo business escalation và không persist case rác.
- Upload file, ingest URL, source metadata/activation, privileged human decision, approve-send và global controls không khả dụng trong restricted mode.
- Test kiểm tra cross-session query trên cả trang email và audit; session khác không đọc được case đã tồn tại.
- Direct scheduling spoof test snapshot `status`, `send_deadline` và số event `SEND_SCHEDULED`; cả bốn actor đều bị deny và snapshot không đổi. Canonical routine chứng minh pipeline nội bộ vẫn tạo `PENDING_SEND`, deadline và event với actor server `SYSTEM`.

## Validation

Mọi lệnh chạy với Python 3.11, `OPENAI_API_KEY` rỗng, `LLM_MODE=replay`, `LLM_CACHE=0`; test suite chặn socket/provider. Không command nào in giá trị secret.

| Lệnh / nhóm kiểm tra | Kết quả |
|---|---|
| `pytest tests/test_restricted_demo.py -q` | PASS — 23/23 |
| Targeted regression gồm email UI, worker, M3 human-control/atomicity/fail-safe, corpus workflow, UI baseline/cleanup và harness | PASS — 180/180, 1 warning Altair |
| `python -m verify.harness --set verify4` trong restricted mode | PASS — 4/4 |
| `python -m scripts.audit_runtime_replay` | Replay coverage PASS 24/24, 0 miss, LIVE=0; process exit **2** vì pack provenance `NOT_APPROVED` |
| Escalation5 restricted CLI / private replay | FAIL dự kiến — lần lượt whitelist deny 0/5 và thiếu R2 cassette 0/5; cả hai exit 1; không record |
| Full `pytest -q` | **703 PASS, 16 FAIL, 1 warning**; toàn bộ FAIL là recording readiness drift-lock trên 5 file runtime được hotfix sửa có chủ ý |
| `black --check`, `ruff check`, targeted `mypy --follow-imports=skip` trên 4 file HF1 follow-up | PASS |
| Full touched-file mypy | Không sạch do lỗi typing SDK/provider có sẵn trong `infra/llm.py` và typing dependency cũ; các lỗi tại vùng không đổi |
| `git diff --check` | PASS |
| Secret/config metadata scan | PASS — usable key absent, LIVE không được cấp quyền |

16 full-suite failures đều bắt đầu từ `PRODUCTION_OR_CORPUS_DRIFT` trong `scripts/runtime_recording_readiness.py`, vì evidence cũ ghim hash của `infra/llm.py`, `core/pipeline.py`, `core/resume.py`, `core/worker.py`, `pages/2_Hang_cho_duyet.py`. Không cập nhật fingerprint vì việc đó thuộc recording/provenance và bị cấm trong HF1.

Failed IDs cuối: 15 variants/tests trong `tests/test_guarded_runtime_recording.py` (`test_go_metadata_cannot_bypass_pins_caps_or_full_cost` ×5; `test_assumed_thousand_output_tokens_is_not_a_provider_bound`; `test_documented_worst_case_calculation_is_not_account_authorization`; `test_cost_bound_requires_verified_standard_global_project` ×2; `test_cited_r11_requires_explicit_scope_and_matching_24_attempt_budget`; `test_failed_attempt_keeps_reservation_and_next_call_never_delegates`; `test_sdk_metadata_bytes_preserved_before_rejecting_missing_origin`; `test_nonstandard_response_tier_stops_after_preserving_original`; `test_same_hash_conflicting_unit_metadata_cannot_replace_file`; `test_effective_config_drift_stops_before_reservation_or_delegate`) và `tests/test_runtime_recording_readiness.py::test_preparation_preserves_base_cap_and_requires_supplemental_cited_r11_approval`.

## Files changed

- Ranh giới mode/replay: `.env.example`, `infra/demo_access.py`, `infra/llm.py`, `run_local.py`, `streamlit_app.py`.
- Backend guards: `core/controls.py`, `core/dispatch.py`, `core/pipeline.py`, `core/resume.py`, `core/worker.py`.
- Corpus guards: `corpus/intake.py`, `corpus/workflow.py`, `corpus/lifecycle.py`.
- Public presentation/isolation: `pages/1_Xu_ly_email.py` đến `pages/5_Verify.py` trong các đường liên quan.
- Replay harness: `scripts/audit_runtime_replay.py` sửa chọn đúng case trước thao tác R11.
- Tests: `tests/conftest.py`, `tests/test_restricted_demo.py`.

## Known limitations và rủi ro

1. HF1 không triển khai controlled LIVE lane hoạt động; arbitrary new-input chỉ giữ UI và fail closed. Rate limit/quota/budget cho LIVE chưa cần vì LIVE không thể bật trong hotfix này.
2. Session ownership không durable và không chia sẻ giữa process; restart làm mất quyền xem case cũ (fail closed). Isolation bền vững cần authentication/ownership schema, ngoài contract.
3. Safe cancel/escalate của guest bị deny vì chưa có durable ownership để chứng minh an toàn.
4. Escalation5 chưa có replay coverage: 0/5.
5. BASE24 hit đủ nhưng recorded pack chưa có provenance authorization đầy đủ.
6. Python không phải security boundary giữa các module tin cậy; capability là private server object. Threat model được kiểm là external/client-controlled actor không thể forge identity này.

## Owner self-review

- Rà call graph của mutation thực tế; guard nằm trước transaction/provider/network khi restricted.
- Xác nhận không đổi `policy.yaml`, P01–P05, R0–R14, schema, expected labels, cassette hoặc audit action catalog.
- Xác nhận technical failure vẫn là `ERROR / TECHNICAL_ERROR`.
- Xác nhận worker restricted không xử lý job cũ và direct dispatch không thể bypass bằng actor giả.
- Đọc lại final diff: `schedule_auto_reply()` authorize trước mọi side effect; chỉ pipeline truyền capability nội bộ; direct spoof tests kiểm DB/audit bất biến.
- Xác nhận public list/query/audit không lộ case session khác trong presentation layer.
- Secret scan sau cùng không phát hiện secret-shaped content.

## Commit / PR / handoff

- Implementation commit: `b56f6f8b1e215995ff6dcbe8238e18087460a77a`.
- Dispatch authorization commit/tested SHA: `4af03638faabe59d6f8da15e0f418c76a77e8906`.
- Report commit ban đầu: `b85184d74e6b602be15e12a4760de66ad2dddadd`.
- PR nhắm `dev`: [#53](https://github.com/ThanhVu165/MLAi_VNG_A/pull/53) — OPEN, merge state `CLEAN` tại lúc kiểm tra.
- Acceptance recommendation: **ACCEPT**. Coordinator/Owner đã self-review trong single-operator mode. Không merge, không deploy public, không đánh M6-T04 hoặc HF1 DONE trước quyết định acceptance riêng.
