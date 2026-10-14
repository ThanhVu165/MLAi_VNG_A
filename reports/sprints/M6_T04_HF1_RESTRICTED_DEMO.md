# M6-T04-HF1 — Restricted Public DEMO Access Hotfix

Ngày xác minh: 2026-10-14  
Kết quả của Owner: **READY_FOR_REVIEW** — chưa merge, chưa deploy public, chưa đánh DONE.

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
- Tested code SHA: `b56f6f8b1e215995ff6dcbe8238e18087460a77a`.
- Hai commit local-only `f3cb74b` và `1b64c49` vẫn được giữ nguyên trên branch cũ; không cherry-pick, rebase, reset hoặc squash vào hotfix.

## Thiết kế authorization

- `APP_MODE` là cấu hình phía server; mặc định `restricted_demo`, giá trị ngoài `private|restricted_demo` fail closed.
- Restricted mode bắt buộc `LLM_MODE=replay`; `live` và `record` bị chặn trước provider. Worker nền không khởi động; gọi trực tiếp worker/dispatch cũng bị deny.
- Actor của canonical DEMO và Verify bị ép thành `SYSTEM` phía server. Chuỗi actor do client cung cấp không cấp quyền.
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
| AC1 — Guest Authorization | PASS | Fake `ADMIN:fake`, `HUMAN:fake`, `SYSTEM` đều không vượt guard; query-param case spoof bị từ chối. |
| AC2 — Backend Enforcement | PASS | Direct admin/dispatch/worker/R11 và SQL helper của trang duyệt bị deny trước side effect; snapshot DB không đổi. |
| AC3 — Corpus Safety | PASS | Direct ingest và lifecycle mutation bị deny; trang corpus restricted chỉ đọc. |
| AC4 — Public Demo Workflow | PASS | Canonical sample hit replay; Verify4 chạy; free-form UI còn nguyên; arbitrary input báo lane chưa bật và không persist. |
| AC5 — Regression | PASS có ghi chú | Verify4 4/4, BASE24 24/24 hit, targeted 174/174. Full suite có 16 drift-lock fail do chính source hash thay đổi; 697 test còn lại PASS. |
| AC6 — External Effects | PASS | Network/provider bị chặn trong test; LIVE/API/email thật = 0; cost = $0; rejected actions không đổi DB. |
| AC7 — Evidence | PASS chờ independent review | Report, baseline/tested SHA, commands, limitations và Owner review có trong tài liệu này; PR được bổ sung sau khi mở. |

## Verify và replay

- Verify4 trong `restricted_demo`: **4/4 PASS**, 0,83 giây.
- BASE24 replay audit: **24 cassettes, 24 logical calls, 0 replay failure, LIVE=0**.
- BASE24 manifest vẫn `NOT_APPROVED` vì provenance/authorization của recorded pack là `MISSING`; HF1 không sửa provenance hoặc cassette. Exit code của audit là 1 vì trạng thái pack này, không phải replay miss.
- Escalation5 read-only replay: **0/5**, cả 5 fail-safe thành `ERROR / TECHNICAL_ERROR` do thiếu cassette tương ứng. Không có business escalation giả, không record cassette. Cần task/provenance authorization riêng nếu muốn bổ sung coverage.

## Input và security validation

- Body public tối đa 5.000 ký tự, text-only, reject trường rỗng/NUL/oversized trước persistence.
- Arbitrary input khi LIVE chưa được cấp quyền bị từ chối trung thực trước khi tạo case ở UI/worker.
- Gọi pipeline trực tiếp với replay miss trả `ERROR / TECHNICAL_ERROR`, không tạo business escalation và không persist case rác.
- Upload file, ingest URL, source metadata/activation, privileged human decision, approve-send và global controls không khả dụng trong restricted mode.
- Test kiểm tra cross-session query trên cả trang email và audit; session khác không đọc được case đã tồn tại.

## Validation

Mọi lệnh chạy với Python 3.11, `OPENAI_API_KEY` rỗng, `LLM_MODE=replay`, `LLM_CACHE=0`; test suite chặn socket/provider. Không command nào in giá trị secret.

| Lệnh / nhóm kiểm tra | Kết quả |
|---|---|
| `pytest tests/test_restricted_demo.py -q` | PASS — 19/19 |
| Targeted regression gồm email UI, worker, M3 human-control/atomicity/fail-safe, corpus workflow, UI baseline/cleanup và harness | PASS — 174/174, 1 warning Altair |
| `python -m verify.harness --set verify4` trong restricted mode | PASS — 4/4 |
| `python -m scripts.audit_runtime_replay` | Replay PASS 24/24, 0 miss, LIVE=0; process exit 1 vì pack provenance `NOT_APPROVED` |
| `python -m verify.harness --set escalation5` | FAIL dự kiến — 0/5, thiếu cassette; không record |
| Full `pytest -q` | 697 PASS, 16 FAIL, 1 warning; toàn bộ FAIL là recording readiness drift-lock trên 5 file runtime được hotfix sửa có chủ ý |
| `black --check` và `ruff check` trên 20 file Python thay đổi | PASS |
| Targeted `mypy --follow-imports=skip` trên 19 file | PASS |
| Full touched-file mypy | Không sạch do lỗi typing SDK/provider có sẵn trong `infra/llm.py` và typing dependency cũ; các lỗi tại vùng không đổi |
| `git diff --check` | PASS |
| Secret/config metadata scan | PASS — usable key absent, LIVE không được cấp quyền |

16 full-suite failures đều bắt đầu từ `PRODUCTION_OR_CORPUS_DRIFT` trong `scripts/runtime_recording_readiness.py`, vì evidence cũ ghim hash của `infra/llm.py`, `core/pipeline.py`, `core/resume.py`, `core/worker.py`, `pages/2_Hang_cho_duyet.py`. Không cập nhật fingerprint vì việc đó thuộc recording/provenance và bị cấm trong HF1.

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
6. Cần independent security review trước public deployment.

## Owner self-review

- Rà call graph của mutation thực tế; guard nằm trước transaction/provider/network khi restricted.
- Xác nhận không đổi `policy.yaml`, P01–P05, R0–R14, schema, expected labels, cassette hoặc audit action catalog.
- Xác nhận technical failure vẫn là `ERROR / TECHNICAL_ERROR`.
- Xác nhận worker restricted không xử lý job cũ và direct dispatch không thể bypass bằng actor giả.
- Xác nhận public list/query/audit không lộ case session khác trong presentation layer.
- Secret scan sau cùng không phát hiện secret-shaped content.

## Commit / PR / handoff

- Implementation commit: `b56f6f8b1e215995ff6dcbe8238e18087460a77a`.
- Report commit: sẽ ghi sau khi commit tài liệu.
- PR nhắm `dev`: sẽ bổ sung sau khi mở PR.
- Handoff: yêu cầu independent review tập trung vào authorization bypass, session isolation, worker/dispatch và corpus mutation. Không merge, không deploy public, không đánh M6-T04 hoặc HF1 DONE.
