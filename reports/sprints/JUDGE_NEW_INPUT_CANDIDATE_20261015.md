# P0 Controlled Judge New-Input — Offline Candidate (cardless)

## 1. Handoff

- **Kết quả:** `READY_FOR_REVIEW` đối với thiết kế security và bằng chứng offline;
  **không public-ready**.
- **Work label:** `P0 Controlled Judge New-Input — Cardless`.
- **Authorization:** Project Coordinator chấp thuận thực hiện ngày 15/10/2026; bỏ qua
  Trello theo đúng task contract, không tạo hoặc cập nhật card.
- **Task contract model label:** Codex GPT-6 / High.
- **Owner/môi trường:** Coordinator vận hành máy Mac cùng Codex; macOS, Python 3.11,
  SQLite tạm, provider double offline.
- **Repository:** `ThanhVu165/MLAi_VNG_A`.
- **Baseline đã xác minh:**
  `dev@b728d00ba6e53b8568554082fe7f4cb6a0dc03e1`.
- **Branch:** `codex/judge-new-input-candidate`.
- **Implementation SHA:** `a661fff9499f60a687ec32e4718b942f90a97f66`.
- **Pull request:** sẽ bổ sung sau khi push branch; bắt buộc nhắm `dev`.
- **LIVE/API calls:** `0`.
- **Merge/deploy:** `NOT RUN`.

Candidate này chỉ thêm test offline và báo cáo. Không sửa `infra/demo_access.py`,
`infra/llm.py`, `core/`, `streamlit_app.py`, SQLite schema, policy, Gold/Set A/Set B,
deployment hoặc authorization contract.

## 2. Preflight

### Kết quả

| Kiểm tra | Kết quả | Evidence |
|---|---|---|
| Remote `dev` mới nhất | **PASS** | `git fetch origin dev`; `origin/dev=b728d00ba6e53b8568554082fe7f4cb6a0dc03e1`. |
| PR #64 / UI-01 | **PASS** | GitHub xác nhận PR #64 merged; merge commit đúng `b728d00...`; local baseline chứa thay đổi UI-01. |
| PR #63 / ownership | **PASS** | PR #63 còn open, chỉ sửa trang Quy định do Lenovo sở hữu, test và report riêng; không đụng file candidate. |
| Local branch/HEAD | **PASS** | Branch tạo trực tiếp từ verified `origin/dev`; không clone/worktree phụ. |
| Tracked tree | **PASS** | Không có tracked modification trước task. |
| M7 local artifact | **PASS** | Hai untracked artifact được giữ nguyên và không stage/commit. |
| Nguy cơ mất dữ liệu | **PASS** | Không reset, clean, stash, restore, rebase, rewrite history hoặc force-push. |

Fingerprint M7 trước khi tạo branch:

- `reports/evaluation/M7_SET_B_PREPARATION_20261015.md`:
  `sha256:7a37ba82d7126ed9c617c28b00c72f8c3de08f23087ec17d870e836c55a8f3d1`.
- `outputs/m7_blind_private_work/render_blank.mjs`:
  `sha256:55eab88ec53e0c5a3814555d7e00c347160f35d6616b9de5e119bb11b93bdbe4`.

## 3. Root cause trên code thực tế

Đường xử lý đã đối chiếu:

```text
Textbox
→ paste_input()
→ _submit()
→ authorize_case_input()
→ private: submit_case() → worker_tick() → process_case()
  restricted: process_case() trực tiếp
→ infra.llm.call_json()
→ PipelineResult
→ SQLite case/result/audit
```

Các boundary chặn input mới trong Restricted DEMO:

1. `pages/1_Xu_ly_email.py:102-113`: `paste_input()` kiểm tra input, giữ timestamp canonical
   cho ba mẫu; input khác nhận timestamp mới.
2. `pages/1_Xu_ly_email.py:122-142`: `_submit()` gọi `authorize_case_input()` trước
   `process_case()` trong restricted. Noncanonical bị từ chối trước persistence; private mới
   dùng `submit_case()`.
3. `infra/demo_access.py:117-128`: validation hiện có yêu cầu ba trường không rỗng, text,
   không NUL và body tối đa 5.000 ký tự.
4. `infra/demo_access.py:131-155`: restricted chỉ cho key khớp whitelist replay.
   Whitelist gồm ba mẫu canonical và Verify4 (`infra/demo_access.py:167-200`). Input mới
   khác timestamp/content/external ID nên không được cấp quyền.
5. `core/pipeline.py:441-473`: pipeline kiểm lại `authorize_case_input()` ở boundary dùng
   chung. Gọi trực tiếp không bypass; lỗi authorization được trả fail-closed `ERROR`.
6. `core/worker.py:31-47`: `submit_case()` cũng kiểm authorization trước giao dịch. Worker
   private sau đó dựng lại `CaseInput` và gọi đúng `process_case()`
   (`core/worker.py:267-310`).
7. `streamlit_app.py:18-20` gọi `validate_runtime_mode()` khi khởi động;
   `infra/demo_access.py:81-87` bắt restricted chỉ chạy `LLM_MODE=replay`.
8. `infra/llm.py:158-197`: restricted từ chối LIVE/record, replay chỉ đọc cassette theo
   prompt hash. Email mới không có cassette không thể tự tạo kết quả.
9. `core/pipeline.py:490-725`: input được chạy qua R0–R14, policy thật, guards, persistence
   và Audit. Exception provider/parse/persistence đi vào fail-safe kỹ thuật ở
   `core/pipeline.py:726-770`, không đổi thành business escalation.
10. `infra/demo_access.py:158-164` và UI ownership check tại
    `pages/1_Xu_ly_email.py:597-601` không tin query/case ID đơn lẻ trong restricted.
11. `infra/demo_access.py:90-99`, `streamlit_app.py:30-38,56-78` và các mutation guard
    hiện có tách quyền pipeline khỏi actor string, ẩn trang human/admin và từ chối mutation
    đặc quyền trong restricted.
12. `core/dispatch.py:51-88,142-176` chỉ lên lịch/gửi **mô phỏng**; restricted cấm
    dispatch. Candidate test xác nhận không có `EMAIL_SENT`/`SEND_DISPATCHED`.

Kết luận: textbox không phải root cause. Root cause là security contract fail-closed có chủ ý
tại UI, intake, pipeline và LLM runtime. Muốn xử lý public input mới bắt buộc thay đổi các
boundary read-only; việc đó nằm ngoài authorization Phase B.

## 4. So sánh kiến trúc A/B/C

### A — Đưa public chạy `APP_MODE=private`

**Không khuyến nghị.** Private mode bỏ qua whitelist input, bật worker, hiển thị hàng chuyên
viên/đo lường và các control admin. Actor local không phải xác thực production. Chuyển public
sang private vì vậy gộp quyền “được nhập một email judge” với toàn bộ mutation đặc quyền,
provider/cost và đọc dữ liệu lịch sử. Blast radius lớn, rollback thô và trái nguyên tắc least
privilege.

Private vẫn phù hợp cho test cô lập sau khi provider đã được thay bằng double và DB tạm, như
bằng chứng offline của candidate; điều đó không tạo quyền public.

### B — Bỏ whitelist canonical

**Không khuyến nghị.** Bỏ check `authorize_case_input()` làm mọi khách có textbox trở thành
caller không giới hạn của pipeline. Không có rate limiter/session budget/concurrency gate hiện
hành; replay miss tạo technical error, còn bật LIVE sẽ mở chi phí và nguy cơ abuse. Case/audit
được ghi vào SQLite nhưng session ownership hiện là danh sách trong Streamlit session, không
phải authorization bền vững. B còn mở bề mặt prompt injection/PII và có thể tạo nhiều case/job
dù vẫn chưa mở quyền admin.

### C — Controlled judge-input capability

**Khuyến nghị.** Tạo capability riêng, không suy ra từ `APP_MODE=private`, actor string,
query parameter, case ID hay UI flag. Mặc định disabled và fail-closed. Capability chỉ mở đúng
hành động “submit một synthetic judge email”, không mở admin/human/source lifecycle/dispatch.

## 5. Thiết kế C đề xuất

### 5.1 Authorization boundary

1. Cấu hình server `JUDGE_INPUT_ENABLED=0` là kill switch mặc định.
2. Chỉ một staging/demo deployment có access gateway xác thực judge/operator mới được arm.
   Không dùng URL bí mật làm authentication.
3. Sau xác thực, server tạo grant opaque, entropy cao, có `grant_id`, principal/session hash,
   expiry, remaining requests và nonce. Grant không serialize vào query/case ID và không nhận
   giá trị do browser tự khai.
4. UI gọi một facade server-side mới với object capability. Facade kiểm và consume quota nguyên
   tử trước persistence. Pipeline boundary kiểm lại capability thay vì tin UI.
5. `case_id` được tạo sau authorization; mapping grant/session → case được lưu server-side.
   Mọi xem Result/Audit kiểm ownership theo mapping đó. Session mất hoặc registry/DB lỗi thì
   deny, không tự fallback sang global read.
6. Capability không được truyền cho `authorize_demo_action()` và không thể gọi human/admin,
   corpus mutation, pause/resume, cancel/escalate, source approval hoặc dispatch.

Thiết kế bền vững qua restart cần một bảng grant/ownership hoặc session store có TTL. Đây là
thay đổi SQLite schema/security contract, phải qua `CONTRACT-CHANGE`; không được lén dùng
`st.session_state` hoặc case ID để thay thế.

### 5.2 Input, abuse, rate và concurrency

- Chỉ `str`, Unicode NFC, sender/subject/body bắt buộc; từ chối NUL/control character nguy hiểm.
- Body tối đa 5.000 ký tự như guard hiện có; đề xuất thêm sender 254 ký tự, subject 300 ký tự và
  tổng payload 6.000 ký tự ở cả facade lẫn pipeline boundary.
- Chỉ synthetic data; UI cảnh báo không nhập PII thật. PII detector mask audit/log hiện có;
  staging retention ngắn và có quy trình xóa được Coordinator phê duyệt.
- Per grant: tối đa 3 request/10 phút, 10 request/toàn session; global concurrency 2;
  một case đang chạy/session. Quota phải consume atomically trước provider call.
- Reject duplicate nonce/idempotency key; retry technical error dùng chính case hoặc một retry
  được audit, không tạo vô hạn case mới.
- Prompt injection tiếp tục bị coi là data; `strip_prompt_injection()` chạy trước mọi prompt.
  Không bao giờ đưa grant, secrets hoặc system prompt vào model context.

### 5.3 Provider, timeout và cost

- Model/config đề xuất theo runtime hiện tại: OpenAI `gpt-6-luna`, `temperature=0`, structured
  output; không provider fallback.
- Giữ tối đa 3 processing attempts/case và deadline 60 giây hiện có
  (`infra/settings.py:64-72`); timeout provider 30 giây, retry tối đa một lần trong budget.
- Thêm semaphore global 2 và circuit breaker mở khi rate-limit/5xx liên tiếp; lỗi trả
  `TECHNICAL_ERROR`, giữ case/audit và không tạo câu trả lời giả.
- Ước tính tham chiếu từ M4 Set A: USD 0,0146718/52 provider attempts ≈ USD 0,000282/attempt.
  Dùng dự phòng khoảng 10× cho prompt mới: **trần đề xuất USD 0,01/case**, tối đa 10 case =
  **USD 0,10/session**. Đây là ước tính/guardrail đề xuất, **không phải quyền chi tiêu** và phải
  được kiểm chứng bằng usage telemetry trước khi mở staging.

### 5.4 Persistence, Audit và lỗi hàng đợi

- Tận dụng `cases`, `case_results`, `decisions`, `drafts`, `escalations`, `step_latencies` và
  audit actions hiện có; không đổi meaning của audit action.
- Audit thêm metadata an toàn `grant_id_hash`, principal/session hash, quota outcome và reason;
  không ghi token hoặc PII thô. Nếu cần action mới thì đó là contract change riêng.
- Nếu dùng worker, job phải mang server-generated grant reference và worker re-authorize grant
  scope/expiry trước provider. Queue claim/lease hiện có tiếp tục xử lý crash; grant hết hạn sau
  khi đã nhận case có thể cho case hoàn tất nhưng không cho submit mới, tùy quyết định Coordinator.
- Phương án đơn giản hơn cho một lượt judge là xử lý đồng bộ qua `process_case()` với semaphore;
  vẫn phải lưu case/result/audit. Chọn sync hay worker cần load test trước staging.
- SQLite busy/persistence failure phải thành `TECHNICAL_ERROR` khi có thể lưu; không chuyển thành
  P01/P02/P03 và không công bố thành công trước transaction hoàn tất.

### 5.5 Không gửi email thật

- Capability judge không chứa quyền dispatch.
- AUTO_REPLY chỉ hiển thị draft/result. Không gọi email provider; giữ banner mô phỏng.
- Khuyến nghị ở judge lane không lên `PENDING_SEND`, hoặc dùng một dispatch sink riêng luôn no-op
  có audit. Thay đổi status/interface cần Coordinator xác nhận và regression vì contract hiện tại
  tự lên lịch gửi mô phỏng cho AUTO_REPLY.

### 5.6 Kill switch và rollback

- Kill switch server-side ngay lập tức: `JUDGE_INPUT_ENABLED=0`.
- Khi tắt: từ chối grant mới, không xóa case/audit đã có, không tự retry job.
- Rollback code bằng revert PR sau Coordinator approval; không reset/rewrite history.
- Giữ Restricted DEMO canonical/Verify4 mặc định. Nếu config thiếu/hỏng, khởi động hoặc request
  phải fail closed về restricted canonical-only.

## 6. Phần đã có và phần mới chỉ là thiết kế

### Đã có trong repository

- Canonical/Verify4 whitelist; public text validation 5.000 ký tự.
- Pipeline/worker kiểm authorization lặp lại; actor restricted ép về `SYSTEM`.
- Object-identity capability nội bộ cho schedule, admin/human mutation guard.
- Case budget 3 processing attempts, provider timeout 30 giây, case deadline 60 giây.
- Structured output, injection stripping, PII masking, policy/ground/question guard.
- SQLite persistence, result snapshot, audit, worker lease/recovery và technical fail-safe.
- Session ownership check cho Restricted DEMO.
- Không có email provider thật; dispatch hiện là mô phỏng SQLite.

### Chưa triển khai, cần phê duyệt riêng

- Judge grant issuer/verifier, access gateway và durable ownership store.
- Judge-specific rate limit, global concurrency, USD ceiling/circuit breaker.
- Restricted LIVE exception chỉ cho capability hợp lệ.
- Judge lane không-dispatch hoặc status contract tương ứng.
- Retention/data policy, operational logging/alerts, staging deployment và abuse test.

## 7. Offline implementation

File mới `tests/test_judge_new_input_offline.py`:

- đặt provider double đúng tại `infra.llm._call_live`; SDK/network vẫn bị
  `tests/conftest.py` khóa;
- dùng `APP_MODE=private` chỉ trong pytest, SQLite tạm và corpus seed synthetic;
- chạy pipeline thật cho AUTO_REPLY/P05, FACT_UNRESOLVED/P03, OUT_OF_POLICY/P02,
  AUTHORITY_REQUIRED/P01 và TECHNICAL_ERROR;
- chạy AppTest form thật → `paste_input()` → `_submit()` → `submit_case()` → `worker_tick()` →
  `process_case()` → provider double → persistence/Audit;
- kiểm INVALID_INPUT cho sender/subject/body thiếu, body >5.000, NUL, prompt injection,
  cross-session ownership và không có real send event;
- kiểm mỗi case chỉ dùng 1–3 provider steps trong proof.

Synthetic input khác toàn bộ canonical và không dùng cassette/Set A/Set B. Expected fixture,
Gold và evaluation baseline không thay đổi.

### Evidence boundary

- **Pipeline executed:** đã kiểm chứng.
- **Deterministic control/status/persistence/Audit:** đã kiểm chứng trong điều kiện test.
- **Semantic correctness của provider thật:** **NOT VERIFIED**; output của double không phải
  bằng chứng mô hình hiểu đúng email mới.
- **Provider reliability/latency/cost live:** **NOT VERIFIED**.
- **Public capability/LIVE security:** chỉ là thiết kế, chưa triển khai.

## 8. Synthetic cases

| Case | Kỳ vọng | Evidence loại |
|---|---|---|
| JUDGE-AUTO | AUTO_REPLY / P05 / PENDING_SEND | Flow/control path với structured provider double; không phải model quality. |
| JUDGE-FACT | ESCALATE / FACT_UNRESOLVED / P03 | Policy/evidence flow thật; semantic fields do double cấp. |
| JUDGE-OUT-OF-POLICY | ESCALATE / OUT_OF_POLICY / P02 | Unknown-domain policy flow thật. |
| JUDGE-AUTHORITY | ESCALATE / AUTHORITY_REQUIRED / P01 | Authority lock/policy flow thật. |
| JUDGE-TECHNICAL | ERROR / TECHNICAL_ERROR | Provider failure fail-safe thật; không có business escalation/card. |
| JUDGE-INJECTION | AUTO_REPLY sau stripping | Injection text không tới bất kỳ provider step nào; output vẫn do double cấp. |
| Missing sender/subject/body | INVALID_INPUT | Không gọi provider. |
| >5.000/NUL | ValueError trước persistence | Không gọi provider, không tạo case. |

## 9. Acceptance Criteria

| AC | Kết quả | Evidence |
|---|---|---|
| AC1 — Root cause | **PASS** | Guard/runtime boundary và line reference tại Mục 3. |
| AC2 — Architecture | **PASS** | A/B/C, threat model, limits, fail-closed, kill switch và decision packet trong report. |
| AC3 — Offline proof | **PASS** | AppTest + worker + common pipeline + provider double + SQLite/Audit; test mới 12/12. |
| AC4 — Security regression | **PASS** | Restricted noncanonical/admin/human/LIVE/record/cross-session tests trong suite 55/55. |
| AC5 — Semantic coverage | **PASS (flow only)** | Đủ sáu nhóm yêu cầu và technical failure; semantic provider thật ghi `NOT VERIFIED`. |
| AC6 — Compatibility | **PASS** | 3 canonical, Verify4, UI-01, sidebar/private và Restricted DEMO nằm trong suite 55/55. |
| AC7 — Evidence | **PASS** | Report, commands, self-review, implementation SHA; PR bổ sung sau push. |

## 10. Validation

Môi trường test: `.venv/bin/python` 3.11, DB dưới pytest temp directory,
`OPENAI_API_KEY` không dùng, provider network bị chặn, corpus synthetic.

| Check | Kết quả |
|---|---|
| `pytest -q tests/test_judge_new_input_offline.py` | **PASS — 12 passed** sau sửa giả định test về private/restricted ownership. |
| Targeted regression: test mới + Restricted DEMO + UI-01 + Email input + pre-M4 UX | **PASS — 55 passed in 4.29s**. |
| Black check file mới | **PASS**. |
| Ruff check file mới | **PASS**. |
| `git diff --check` | **PASS**. |
| Scoped credential/private-key pattern scan | **PASS — no match**. |
| Browser server smoke | **NOT RUN**; AppTest chạy form/UI cùng DB tạm. |
| Official evaluation / Set A / Set B | **NOT RUN**; bị cấm trong task. |
| LIVE/provider/API | **NOT RUN — call count 0**. |

Một lượt test đầu tiên đạt 10/11; assertion cross-session được đặt nhầm trong private mode,
nơi `case_is_owned()` cố ý không áp restriction. Chỉ test được sửa để chuyển assertion sang
Restricted DEMO; code sản phẩm/expected fixture không thay đổi. Sau đó test mới đạt 12/12 và
targeted regression đạt 55/55.

## 11. Safety regression chi tiết

- Noncanonical Restricted DEMO bị từ chối trước persistence: **PASS**.
- Direct pipeline replay miss trả TECHNICAL_ERROR, không persistence: **PASS**.
- Admin/human actor giả không mutate hoặc dispatch: **PASS**.
- Direct schedule spoof không có side effect: **PASS**.
- LIVE/record không chạm provider trong restricted: **PASS**.
- Cross-session/query/session injection bị deny: **PASS**.
- Ba canonical samples: **PASS**.
- Verify4: **4/4 PASS** trong restricted test.
- UI-01 Email/Verify → Audit và session ownership: **PASS**.
- Sidebar/private mode behavior: **PASS**.
- Không có email thật được gửi: **PASS** trong candidate; chỉ `SEND_SCHEDULED` mô phỏng,
  không có `EMAIL_SENT`/`SEND_DISPATCHED`.

## 12. Threat model và stop conditions

| Mối đe dọa | Control đề xuất / trạng thái |
|---|---|
| UI/query/case ID giả capability | Object/grant server-side, double-check; chưa triển khai. |
| Cross-session read | Durable grant→case ownership + TTL; hiện restricted session list đã fail-closed. |
| Cost/rate/concurrency abuse | Atomic quota, global semaphore, circuit breaker, USD ceiling; chưa triển khai. |
| Prompt injection | Existing stripping + prompt data boundary; candidate regression PASS. |
| PII/log leakage | Synthetic-only, mask PII, không log grant/raw token, retention policy. |
| Provider timeout/parse/queue failure | Existing timeout/budget/fail-safe; candidate TECHNICAL_ERROR PASS. |
| Admin/human privilege escalation | Capability không được map sang privileged actions; existing restricted regression PASS. |
| Email send side effect | Judge capability không có dispatch; runtime hiện chỉ mô phỏng. |
| Config drift | Missing/invalid config fail closed; kill switch default off. |

STOP và không mở public nếu thiếu bất kỳ điều kiện nào: independent security review; access
gateway; durable ownership; rate/cost/concurrency controls; staging smoke; provider budget
authorization; PII/retention approval; fail-closed kill-switch test; Restricted regression; hoặc
có yêu cầu sửa Gold/Set/schema/audit contract chưa được phê duyệt.

## 13. Security decision packet cho Coordinator

### File có thể cần đổi sau khi được duyệt

- `infra/demo_access.py`: định nghĩa/verify/consume judge capability, limit và kill switch.
- `infra/llm.py`: cho phép LIVE trong restricted **chỉ** khi call context có capability hợp lệ;
  thêm hard cost/circuit-breaker boundary nếu được chọn.
- `core/pipeline.py`, `core/worker.py`: truyền/recheck auth context; xử lý quota/queue fail-closed.
- `pages/1_Xu_ly_email.py`: UI judge lane và error message, không tin flags/query.
- `streamlit_app.py`: expose page/lane theo server config, không mở human/admin.
- SQLite migration/session store: chỉ nếu chọn durable grant ownership; cần CONTRACT-CHANGE.
- Tests/report tương ứng; không sửa Gold/Set/evaluation baseline.

### Quyết định chính xác cần phê duyệt

1. Chấp nhận phương án C và bác bỏ A/B.
2. Chọn môi trường staging có access gateway, owner vận hành và independent security reviewer.
3. Cho phép một task security riêng sửa các file read-only nêu trên và, nếu cần, contract/schema.
4. Chốt grant lifecycle, ownership durability, sync hay worker, retention/PII policy.
5. Chốt limits đề xuất: 5.000 body / 6.000 total, 3 request/10 phút, 10/session,
   concurrency 2, 3 provider attempts, 60 giây/case, USD 0,01/case và USD 0,10/session.
6. Cấp budget/provider/model cụ thể cho **staging validation**, không phải public LIVE.
7. Chốt judge AUTO_REPLY chỉ hiển thị kết quả và không schedule dispatch.
8. Yêu cầu independent security review và Coordinator acceptance trước bất kỳ public enablement.

### Validation còn phải chạy sau khi có quyền

- Unit/property tests cho grant forgery, expiry, replay nonce, quota race và concurrency.
- Restart/session-loss/queue-lease/persistence-failure tests.
- Staging browser test qua gateway, hai session độc lập, Audit ownership và kill switch.
- Provider LIVE nhỏ, budget được phê duyệt, với synthetic inputs mới; kiểm semantic bằng người,
  không dùng output mock làm chuẩn.
- Cost/timeout/rate-limit/5xx evidence, PII/log leak scan và rollback drill.
- Chạy lại toàn bộ security/canonical/Verify4/UI-01 regression trên revision cuối.

## 14. Owner self-review

- Đã đọc toàn diff; chỉ test mới và report task được tạo.
- Không thay đổi public authorization, security guard, LLM adapter, runtime, UI hay schema.
- Provider double nằm đúng boundary, không monkeypatch policy/pipeline/persistence/Audit.
- Test data synthetic, khác canonical; không cassette, Gold, Set A/B hoặc raw private artifact.
- Technical failure giữ `Decision.ERROR/CaseStatus.ERROR`, không gắn P01/P02/P03.
- AUTO_REPLY candidate chỉ lên lịch gửi mô phỏng và test dừng trước dispatch.
- M7 untracked artifacts được giữ nguyên và không stage/commit.
- Không secret/DB/cache/output local nằm trong commit.
- LIVE/API = 0; merge/deploy không chạy.

## 15. Hạn chế và rủi ro còn lại

1. Chưa có semantic evidence từ provider thật cho input mới.
2. Chưa có judge capability implementation, gateway, durable ownership, rate limiter hoặc hard
   USD cap; do đó không được bật public.
3. Session ownership hiện tại phù hợp Restricted DEMO fail-closed nhưng không phải auth bền vững.
4. SQLite/worker in-process chưa chứng minh chịu tải public hoặc multi-process.
5. M4 Set A lịch sử có 5/18 technical failures; đây là cảnh báo reliability, không được suy từ
   55 test offline thành provider readiness.
6. Browser-server, deployment, mobile/anonymous, restart và live kill-switch chưa kiểm chứng.

**Disposition:** `DESIGN_READY + OFFLINE_CANDIDATE_READY_FOR_REVIEW`. Coordinator và
independent security reviewer phải quyết định task tiếp theo. Candidate này tuyệt đối không tự
chứng nhận sản phẩm đã sẵn sàng LIVE.
