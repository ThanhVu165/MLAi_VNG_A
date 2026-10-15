# P0-JUDGE-C1 — Preflight và amendment no-dispatch

## Trạng thái bàn giao

- RESULT: READY_FOR_REVIEW cho candidate offline, chờ independent security review;
  gate ban đầu đã được Coordinator duyệt bên dưới.
- Owner: Coordinator vận hành Mac cùng Codex.
- Cardless; Trello SKIP theo yêu cầu.
- Authorization nhận trực tiếp trong chat: `GO-C1 OFFLINE CONTRACT-CHANGE`.
- Baseline: `dev@3a36a2fd1513a7c3afea0bb98c417aaceb1cb3d8`.
- Branch: `codex/judge-input-c1`, tạo từ verified `origin/dev`.
- PR #66: GitHub xác nhận merged, merge commit đúng baseline trên.
- LIVE/API provider calls: 0. Merge/deploy: NOT RUN.
- Implementation SHA: `c810f5b5ea86b209662c1c6a1048022f202146bc`.
- PR C1: [#68](https://github.com/ThanhVu165/MLAi_VNG_A/pull/68), open, nhắm `dev`.

## Preflight

Tracked tree sạch trước task. Hai artifact untracked M7 được giữ nguyên, không stage:

- `reports/evaluation/M7_SET_B_PREPARATION_20261015.md`:
  SHA-256 `7a37ba82d7126ed9c617c28b00c72f8c3de08f23087ec17d870e836c55a8f3d1`.
- `outputs/m7_blind_private_work/render_blank.mjs`:
  SHA-256 `55eab88ec53e0c5a3814555d7e00c347160f35d6616b9de5e119bb11b93bdbe4`.

Remote dev đã fetch; PR #63/#65 đã có trong baseline. Chưa sửa file Lenovo,
Windows/Dell hoặc bất kỳ module runtime/security nào. Không reset, clean, stash,
force-push, clone, worktree phụ hoặc merge.

## Vấn đề cần amendment cụ thể

Prompt C1 mục 4F yêu cầu: nếu cần đổi status semantics hoặc audit action thì STOP;
mục 5 yêu cầu STOP nếu cần sửa `core/types.py` hoặc chữ ký interface chung.

Code hiện tại:

- `core/pipeline.py:663-684`: AUTO_REPLY kết thúc ở `PENDING_APPROVAL` khi automation
  paused, hoặc `PENDING_SEND` khi không paused.
- `core/pipeline.py:355-385`: `_finalize()` gọi `schedule_auto_reply()` khi status là
  `PENDING_SEND`, sau khi lưu result snapshot trong giao dịch.
- `core/dispatch.py:51-87`: schedule tạo send_deadline và audit `SEND_SCHEDULED`.
- `core/types.py:36-50`: chưa có trạng thái terminal dành cho draft chỉ xem.

Giữ `PENDING_SEND` nhưng bỏ schedule sẽ để case mang ý nghĩa chờ gửi mà không có
deadline. Dùng `PENDING_APPROVAL` cho judge chỉ xem sẽ mang ý nghĩa chờ phê duyệt
trong khi judge không có quyền human. Cả hai cần quyết định status contract rõ ràng.
Không dùng global pause vì ảnh hưởng canonical/private workflow ngoài judge lane.

## Amendment đề nghị Coordinator duyệt

Cho phép thêm `CaseStatus.PREVIEW_READY` vào `core/types.py`, chỉ cho kết quả judge
AUTO_REPLY đã qua guards; giữ `Decision.AUTO_REPLY` hiện hành. Status này không lên lịch
gửi, không tạo deadline/job dispatch và không có human approval action. Canonical,
Verify4 và private lane giữ nguyên các trạng thái hiện hành.

Mở rộng scope đúng các consumer cần xử lý trạng thái mới:

- `core/types.py`: enum status mới.
- `core/pipeline.py`, `core/dispatch.py`: kết thúc preview, chặn dispatch judge.
- `pages/1_Xu_ly_email.py`: render preview như kết quả hoàn tất chỉ xem.
- `ui/presentation.py`: chỉ thêm nhãn trạng thái tiếng Việt; cần phối hợp Owner
  Windows/Dell, không sửa CSS hoặc App Shell.
- `PROJECT_SPEC.md`: cập nhật contract trạng thái được duyệt.
- Tests và báo cáo C1 tương ứng.

Không đề nghị audit action mới. Trạng thái mới và Audit phải được lưu cùng giao dịch,
dùng action hiện có phù hợp sau review. Nếu cần action mới, xin amendment tiếp thay vì
tự thêm. Chưa xin/triển khai SQLite migration; durable store sẽ được quyết định trong
phạm vi được cấp, không tự tạo bảng.

## AC và validation tại checkpoint trước amendment (lịch sử)

| AC | Trạng thái C1 | Evidence |
|---|---|---|
| AC1 disabled default | NOT VERIFIED | Chưa sửa hoặc chạy test C1. |
| AC2 controlled acceptance | BLOCKED | Cần chốt no-dispatch status contract. |
| AC3 authorization security | NOT VERIFIED | Chưa triển khai grants/quota. |
| AC4 isolation | NOT VERIFIED | Chưa triển khai ownership store. |
| AC5 no privileged/no dispatch | BLOCKED | Gate nêu trên. |
| AC6 result semantics | BLOCKED | Cần amendment PREVIEW_READY. |
| AC7 compatibility | NOT VERIFIED | Không suy từ tests Phase A/B thành C1 evidence. |
| AC8 evidence | PARTIAL | Có report/preflight; chưa implementation/tests/SHA/PR. |

Commands đã chạy: `git status --short --branch`, `git fetch origin dev`,
`git log -5 --oneline origin/dev`, đọc metadata PR #66, SHA-256 M7 và đọc code
pipeline/dispatch/types/migrations/audit. Baseline và artifact checks PASS.

Tests, Black/Ruff C1: NOT RUN vì chưa có implementation. Report whitespace check
được chạy riêng. Không có provider, official evaluation hoặc dữ liệu Gold được chạy.

## Self-review và bước tiếp

Tại checkpoint ban đầu chỉ tạo report này. Gate sau đó đã được duyệt như mục bên dưới.
Independent security review vẫn bắt buộc trên SHA implementation cuối; test PASS không thay acceptance.

## COORDINATOR-APPROVED AMENDMENT — PREVIEW_READY

Coordinator xác nhận trực tiếp trong chat: cho phép bổ sung CaseStatus.PREVIEW_READY,
pipeline/persistence, Email/Audit và shared status labels; Mac được sửa core/types.py,
ui/presentation.py là ngoại lệ ownership. Không cấp audit action mới, migration, LIVE/API,
merge/deploy. Quyền GO-C1 OFFLINE CONTRACT-CHANGE đã nhận trước đó vẫn áp dụng.

Reference dev khi tiếp tục: `11bd04205e560e489203da43874e332505727a2a`, fetch đã xác minh;
delta từ baseline branch `3a36a2f...` chỉ thêm report CORE_RELIABILITY_DIAGNOSTIC, không đổi
runtime/ownership. Giữ branch C1 hiện tại theo yêu cầu; không merge/rebase/reset lịch sử.

### Implementation thực tế

- infra/judge_access.py: issuer yêu cầu secret operator phía server (ít nhất 32 ký tự),
  grant opaque hash, session binding, expiry, nonce chống replay, reservation nguyên tử,
  durable quota và ownership dùng bảng settings hiện có; không migration.
- core/judge_input.py: facade đồng bộ gọi đúng process_case(); không queue/worker API mới.
- infra/demo_access.py: chỉ bypass canonical whitelist khi context server có reservation
  hợp lệ và payload khớp; case ID/session list không cấp quyền đọc judge case.
- infra/llm.py: context judge chỉ replay/offline, recheck grant/kill switch trước provider
  step, consume ngân sách 3 attempts/60 giây hiện có. LIVE/record vẫn bị chặn.
- core/pipeline.py: PREVIEW_READY chỉ sau guards; status, deadline NULL, snapshot và event
  CASE_RESOLVED cùng transaction. Persistence fault trả TECHNICAL_ERROR khi có thể lưu.
- core/types.py: chỉ thêm enum PREVIEW_READY; không đổi Decision/EscalationType/interfaces cũ.
- core/worker.py, core/dispatch.py: từ chối queue/retry/schedule judge và không dispatch.
- pages/1_Xu_ly_email.py, pages/4_Nhat_ky_kiem_toan.py: nhận grant được provision từ server,
  không UI phát grant; kiểm ownership từ ledger, nhãn preview, Audit giữ cùng session UI-01.
- ui/presentation.py: chỉ thêm status label/badge; không sửa CSS/App Shell.
- PROJECT_SPEC.md: ghi contract amendment theo AGENT.md.
- tests/test_judge_input_c1.py: integration/negative tests, provider double tại replay adapter.

### Limits và thực thi

Flag chỉ bật khi bằng chính xác chuỗi "1"; thiếu/sai thì deny. Grant hết hạn sau 600 giây,
tối đa 3 request/grant, 10/session qua nhiều grant, toàn ledger tối đa 20 request và 20 grants.
Toàn DB tối đa 2 reservation đồng thời, 1/session. Các limit reserve/consume cùng BEGIN
IMMEDIATE, không hoàn lại quota cho failed case và không tự refresh sau restart/session mới.
Crash để lại reservation sẽ block slot; C1 ưu tiên fail-closed, chưa có control tự recovery.
Không dùng giới hạn bộ nhớ có thể bị bypass bằng nhiều process/session.

Sender tối đa 254, subject 300, body 5000, tổng 6000 ký tự; Unicode NFC, không NUL/control/
surrogate; sender chỉ .invalid/.test. Trường thiếu/malformed bị từ chối trước persistence;
body rỗng sau sanitize vẫn qua pipeline và được lưu INVALID_INPUT, không provider call.

Không claim hard USD cap: C1 chặn provider LIVE/record hoàn toàn, chi phí API=0. Rate/cost
parameters tham khảo trong report #66 không tự cấp quyền chi tiêu. Corpus/generation semantics
đều dùng double; không có semantic/provider quality evidence mới.

### Ownership/restart

Ledger chỉ lưu SHA-256 grant/session/nonce, không raw secret/token hoặc email. Mapping case
→ grant hash cũng lưu trong settings; đọc case judge cần grant đúng và session đúng, grant còn
hiệu lực. Grant/session mất thì deny; DB/ledger lỗi thì fail closed. Fresh-process test dùng
DB tạm xác nhận PREVIEW_READY và ownership còn đúng khi context runtime đã mất; đây không
phải cơ chế đăng nhập hoặc tự khôi phục danh tính. Ledger mất nhưng còn case markers sẽ chặn
cấp ngân sách mới. Tắt flag không xóa cases/Audit; việc đọc judge cũng bị deny khi flag tắt.

### Evidence đã có trước lượt cuối

- C1 35 tests, bao gồm provider/timeout/parse/persistence failure, grant giả/hết hạn/replay,
  kill switch, concurrent quota, global/session limit, ledger loss, fresh-process restart,
  UI submit, preview/Audit/cross-session và INVALID_INPUT. Kết quả cập nhật sau lượt cuối.
- Suite C1 trước bổ sung cuối + runtime_worker + llm_budget: 73 passed in 5.69s.
- Suite candidate/restricted/UI-01/Email/pre-M4/runtime replay/Audit trước bổ sung cuối:
  98 passed in 7.88s. Không dùng các số checkpoint này thay kết quả cuối.

### Rủi ro / gate còn lại

Independent security reviewer chưa đối chiếu SHA cuối, Coordinator chưa acceptance.
Không có gateway/authenticated principal hoặc UI phát grant; operator provisioning là server-only
foundation. Không bật feature trên public. Ledger toàn DB cố ý không tự reset; crash recovery,
retention, mở lại quota và rollout multi-host cần C2/review riêng. Không gọi API thật, không
đo semantic correctness từ mock, không dùng Gold/Set A/B. Không thêm schema hay action audit.

## Validation cuối trên implementation C1

Môi trường `.venv` Python 3.11, temporary SQLite synthetic corpus. Test harness chặn socket,
DNS và OpenAI SDK; provider double chỉ thay `_replay`, không thay pipeline/policy/guards/DB.
Fresh-process test chỉ đọc DB và ownership, không gọi pipeline/provider.

Lệnh:

```text
.venv/bin/python -m pytest -q tests/test_judge_input_c1.py tests/test_judge_new_input_offline.py tests/test_restricted_demo.py tests/test_audit_navigation_session.py tests/test_email_input_ui.py tests/test_pre_m4_ux.py tests/test_runtime_replay_audit.py tests/test_audit_coverage.py tests/test_audit_details.py tests/test_runtime_worker.py tests/test_llm_budget.py tests/test_ux_responsive_cardless.py
```

Kết quả **144 passed in 10.59s** (exit 0), gồm **35 C1 tests**. Black --check --line-length
100 và Ruff trên 12 Python files thay đổi: PASS. `git diff --check`: PASS. Hai SHA-256 artifact
M7 được đối chiếu lần cuối, khớp nguyên vẹn fingerprint preflight. Không stage artifact M7.

| Original C1 AC | Kết quả | Evidence |
|---|---|---|
| AC1 default disabled | PASS | Thiếu flag, 0, true, garbage và " 1" bị deny; restricted canonical regression. |
| AC2 offline acceptance | PASS | Form restricted có grant server → facade → pipeline thật → PREVIEW_READY. |
| AC3 authorization/quota | PASS | Fake/expired/wrong-session/replay; 8 threads consume quota atomic; global concurrency 2; session budget qua grant mới; ledger reload/loss. |
| AC4 isolation | PASS | Khác session/grant hoặc mất grant bị deny; UI/Audit/query/session-list spoof; fresh process đọc đúng quyền; store failure fail closed. |
| AC5 privilege/no dispatch | PASS | Admin/human restricted regression; queue/retry/schedule guard; worker/dispatch không đổi preview. |
| AC6 result semantics | PASS (offline flow) | AUTO_REPLY, P01/P02/P03, INVALID_INPUT sau sanitize, provider/timeout/parse/persistence ERROR; provider semantics NOT VERIFIED. |
| AC7 compatibility | PASS | Canonical/Verify4 4/4, UI-01, private worker/dispatch, Email/Audit/replay/responsive. |
| AC8 evidence | PASS | Report, tests, self-review, implementation commit và PR handoff; independent review còn pending. |

| Amendment AC | Kết quả | Evidence |
|---|---|---|
| AC-C1A Judge Preview | PASS | Grounded draft/citations/Audit + PREVIEW_READY. |
| AC-C1B No Dispatch | PASS | deadline NULL, không SEND_SCHEDULED/SEND_DISPATCHED; worker/private dispatcher chạy không chuyển SENT. |
| AC-C1C Persistence | PASS | cases.status=snapshot; load_result; fresh Python process đọc lại. |
| AC-C1D Existing Flows | PASS | Canonical, Verify4, private worker và UI-01 trong suite 144. |
| AC-C1E Authorization | PASS | Flag, capability, payload/case binding, quota/ownership/privileged negative tests. |
| AC-C1F UI/Audit | PASS | Form → preview; nhãn đúng, không countdown; switch_page giữ case/session; foreign Audit denied. |
| AC-C1G Technical Failure | PASS | Provider, timeout, parse, one-shot persistence fault đều ERROR, không false preview/escalation. |
| AC-C1H Evidence | PASS | Scoped report/tests/commit/PR; independent security acceptance chưa thực hiện. |

Migration/rollback schema: NOT APPLICABLE, không đổi schema. LIVE/provider semantics,
browser-server smoke, public rollout và independent review: NOT RUN/NOT VERIFIED.

## Owner self-review cuối

Đọc diff và rà các boundary: grant issuance không có UI caller; context/payload binding tại
pipeline; quota/nonce/ownership cùng transaction; không ghi grant thô/issuer secret vào DB/log;
provider C1 không có LIVE path; no-dispatch cả schedule và dispatcher; transaction preview
rollback khi snapshot lỗi; case ID/list không cấp quyền judge; chỉ shared label/badge được sửa.
Không đổi SQLite, audit ACTIONS, Decision/EscalationType hoặc interface hiện hữu. PROJECT_SPEC
chỉ cập nhật phần contract được duyệt. Không chỉnh test/fixture expected cũ hoặc evidence lịch sử.

Rollback đề xuất sau Coordinator approval: revert candidate commit để trở về code baseline;
giữ nguyên DB/Audit/settings judge namespace. Trước rollback tắt flag; bản code baseline không
biết PREVIEW_READY, nên không chạy ứng dụng cũ trên DB có preview cho tới khi có kế hoạch đọc
lịch sử tương thích. Không xóa dữ liệu để làm rollback. Chưa chạy revert/merge/deploy.

Quyết định C2 cần: independent security review đúng SHA; gateway/principal provisioning;
operational recovery/retention; authorization LIVE cụ thể về provider/budget/case; token/USD
reservation thực trước khi claim hard cost cap. Offline tests chỉ chứng minh flow/control và
security trong điều kiện mô tả, không phải semantic quality hoặc public acceptance.

## Handoff

READY_FOR_REVIEW: implementation commit `c810f5b5ea86b209662c1c6a1048022f202146bc`,
PR #68 nhắm dev `11bd04205e560e489203da43874e332505727a2a`. Commit sau implementation
chỉ bổ sung metadata SHA/PR vào report; SHA head cuối được bàn giao trong chat/GitHub.
Independent reviewer cần đọc đúng PR head cuối; không mặc định test PASS là security gate PASS.
LIVE/API provider calls=0. Merge/deploy NOT RUN. Feature chưa được bật public.

## INDEPENDENT REVIEW CHANGE REQUEST — JUDGE CASE MUTATION GUARD

### Authorization, baseline và findings

Coordinator cấp amendment hẹp trong chat ngày 15/10/2026: chỉ sửa `core/controls.py`,
`tests/test_judge_input_c1.py` và report này; tiếp tục branch `codex/judge-input-c1`, PR #68.
Reviewed SHA: `129f106f53b8ed4da1991e19fbcdd6c2ffb65368`. Fetch xác nhận remote branch
vẫn đúng SHA, dev vẫn `11bd04205e560e489203da43874e332505727a2a`, không conflict.

Independent review xác nhận hai khoảng trống: `rerun_case()` có thể tạo case con từ judge
preview/escalation trong private mode; `override_decision()` chưa chặn judge provenance ở
các trạng thái được phép override. Checkpoint PASS trước chỉ phủ privileged denial trong
restricted và worker retry/schedule, chưa phủ đủ các đường admin private này. Change request
này bổ sung coverage và sửa cả hai finding; không dùng PASS lịch sử thay evidence mới.

### Fix

- `_require_non_judge()` nhận provenance từ `is_judge_case()` hiện có hoặc cùng namespace
  CASE_PREFIX trên connection của giao dịch mutation. Kiểm tra độc lập status, flag và grant TTL.
- `rerun_case()`: guard ngay sau kiểm ADMIN, trước đọc quyết định, gọi pipeline hoặc tạo case.
  Không giữ transaction DB qua provider call.
- `override_decision()`: guard trong BEGIN IMMEDIATE, trước bất kỳ mutation nào.
- `_store_manual_decision()`: defense-in-depth dùng chính connection của caller, trước thay
  decisions/status/escalations/Audit, chặn cả lời gọi gián tiếp qua helper.
- Provenance store/query lỗi thì exception dừng thao tác, không fallback cho phép.
- Không sửa module khác, schema, audit actions, enum, quota/grant/ownership hoặc expected cũ.

### Tests và invariant

Test IDs mới:

- `test_private_admin_cannot_mutate_judge_provenance`: 12 tổ hợp rerun/override/manual
  helper × preview/FACT_UNRESOLVED/OUT_OF_POLICY/AUTHORITY_REQUIRED.
- `test_private_admin_cannot_override_judge_pending_approval`: provenance vẫn chặn khi
  status được đặt vào trạng thái admin thường được override (fault setup chỉ trong DB test).
- `test_admin_mutation_guard_store_error_fails_closed`: 2 nhánh rerun/override; injection
  lỗi đọc provenance, gồm SQLite authorizer deny đọc settings trong transaction override.
- `test_normal_private_admin_rerun_and_override_remain_available`: case thường vẫn
  AUTO_REPLY/PENDING_SEND → admin ESCALATE → rerun child PENDING_SEND có audit đúng.

Negative tests so sánh nguyên trạng 10 bảng trước/sau: cases, case_jobs, decisions,
case_results, audit_events, drafts, escalations, extractions, human_decisions, settings.
Judge mutation bị từ chối không đổi status/decision/snapshot/Audit/quota, không child case,
job, PENDING_SEND hoặc SEND_SCHEDULED/SEND_DISPATCHED/RERUN_CASE/OVERRIDE_DECISION.
Pipeline spy dùng pytest.fail để chứng minh denied rerun không chạm pipeline.

### Validation exact commands / kết quả

Môi trường Mac, `.venv` Python 3.11, DB tạm và seed synthetic, replay provider double;
tests/conftest.py khóa network/DNS/OpenAI SDK. Không official evaluation hoặc Gold Set A/B.

```text
.venv/bin/python -m pytest -q tests/test_judge_input_c1.py -k 'private_admin_cannot_mutate_judge_provenance or normal_private_admin_rerun_and_override'
```

Trước fix: **12 failed, 1 passed** — tái hiện guard còn thiếu, normal compatibility PASS.
Sau fix: **13 passed, 35 deselected in 1.94s**.

```text
.venv/bin/python -m pytest -q tests/test_judge_input_c1.py -k 'private_admin or admin_mutation_guard'
```

Sau bổ sung pending-approval/store faults: **16 passed, 35 deselected in 2.28s**.

```text
.venv/bin/python -m pytest -q tests/test_judge_input_c1.py tests/test_guards.py tests/test_runtime_worker.py tests/test_restricted_demo.py tests/test_judge_new_input_offline.py tests/test_audit_navigation_session.py tests/test_email_input_ui.py tests/test_pre_m4_ux.py tests/test_runtime_replay_audit.py tests/test_audit_coverage.py tests/test_audit_details.py tests/test_llm_budget.py tests/test_ux_responsive_cardless.py
.venv/bin/python -m black --check --line-length 100 core/controls.py tests/test_judge_input_c1.py
.venv/bin/python -m ruff check core/controls.py tests/test_judge_input_c1.py
git diff --check
```

**253 passed in 13.22s**, gồm 51 C1 tests; Black/Ruff/diff check đều PASS, exit 0.
Regression giữ Judge AUTO_REPLY=PREVIEW_READY, normal private AUTO_REPLY/rerun/override,
canonical/Verify4 4/4, restricted privileged denial, UI-01 và Audit. Artifact M7 hashes khớp
fingerprint preflight và không stage/commit.

### Owner self-review / handoff

Đã đọc toàn diff: đúng ba file amendment; helper không thêm quyền hoặc thay public interface;
override/manual guard dùng connection của transaction; rerun guard chạy trước pipeline;
không catch lỗi provenance thành allow; denied actions không tạo audit mutation giả.
Đã kiểm tra các đường mutation còn lại trong controls.py: manual decision helper được bảo vệ;
pause/resume là settings toàn cục, không sửa riêng case judge; cancel_send được import từ
dispatch đã có judge guard trong baseline. Không phát hiện đường case mutation khác cần sửa
ngoài scope trong lượt review này.

Result: READY_FOR_REVIEW cho bản sửa hai findings; không tự xác nhận independent security gate.
Implementation SHA sẽ bổ sung trong metadata handoff; PR vẫn #68. Reviewer cần đối chiếu SHA
head sau push. Các giới hạn C1/C2 đã ghi ở trên tiếp tục áp dụng; semantic/provider LIVE vẫn
NOT VERIFIED. LIVE/API=0; merge/deploy NOT RUN. Next: independent security review lại hai
findings và regression → Coordinator acceptance.
