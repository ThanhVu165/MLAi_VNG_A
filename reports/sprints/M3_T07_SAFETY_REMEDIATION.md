# M3-T07 — Remediation R11 Human Decision/Resume

## 1. Kết luận

**RESULT: BLOCKED ở bước GitHub handoff; code/evidence đạt targeted validation nhưng chưa có PR.**

R11 FAIL đã được tái hiện trên baseline, nguyên nhân đã được xác nhận và bản sửa nhỏ nhất đã
được kiểm chứng offline trên code commit `cd989677b28352fc29239cab6c85b5285260c790`.
R11 hiện tạo đúng một draft an toàn từ quyết định đã lưu, chuyển
`HUMAN_DECIDED -> PENDING_APPROVAL`, không tự gửi; preview, duyệt gửi mô phỏng, restart,
SQLite persistence và audit đều có targeted evidence. Không có LIVE/API, recording, email thật
hoặc dữ liệu người tham gia.

Kết luận kỹ thuật chỉ áp dụng cho chuỗi R11 synthetic/replay được mô tả tại đây. Replay hit và
pytest xanh không chứng minh complete product E2E, vận hành thật hoặc GO-STUDY/LIVE. F01, V02 và
aggregate harness ngoài scope, không được sửa hay tái phân loại.

Push không force lên `origin/sprint/m3-t07-safety-remediation` đã được thử sau validation nhưng
dừng với `fatal: could not read Username for 'https://github.com': Device not configured`. Theo
Stop Condition, không lưu credential của chủ máy và không bypass xác thực. Vì PR là deliverable bắt
buộc, task chưa đủ điều kiện `READY_FOR_REVIEW` cho đến khi người có GitHub authorization push các
commit local và mở PR nhắm `dev`.

## 2. Authorization, baseline và preflight

- Project Coordinator cung cấp trực tiếp Task Contract M3-T07 và GO trong chat ngày 14/10/2026;
  đây là authorization hiện hành thay cho việc Codex tự thao tác Trello. Không đọc/ghi/move card
  hoặc tuyên bố DONE trên Trello.
- Đã đọc `AGENT.md`, `PROJECT_SPEC.md`, `docs/TEAM_WORKFLOW.md` và source/test liên quan.
- Repository: `https://github.com/ThanhVu165/MLAi_VNG_A.git`.
- Remote `dev` kiểm lại trước sửa và trước handoff:
  `9dfb33494cbf28e05651508ecfed145e5cc70fe7`.
- Baseline/source parent: `9dfb33494cbf28e05651508ecfed145e5cc70fe7`.
- Branch: `sprint/m3-t07-safety-remediation`, tạo trực tiếp từ verified `origin/dev`; không có
  branch local/remote cùng tên tại preflight, không clone/worktree phụ, không reset/stash/clean.
- Tested code/test SHA: `cd989677b28352fc29239cab6c85b5285260c790`.
- Code/test commit: `fix(m3-t07): remediate human decision resume`.
- Môi trường: macOS, Python 3.11.17, SQLite 3.53.1,
  `LLM_MODE=replay`, `LLM_CACHE=0`, `OPENAI_MODEL=gpt-6-luna`.
- Database và pytest temp đều cách ly dưới `/private/tmp`; input chỉ là synthetic `.invalid`.

## 3. Root cause và bản sửa

### Trước sửa

`core/resume.py::resume_case()` gọi đúng `RESUME_PROMPT_V1` và nhận replay R11 thành công,
nhưng sau đó yêu cầu `choice` và `reason` phải xuất hiện nguyên văn trong prose do LLM trả về.
Contract prompt cho phép diễn đạt lại; cassette hiện hữu diễn đạt đúng ý nhưng không chứa nguyên
văn cả hai trường. Validator vì vậy ném:

```text
ValueError: Bản nháp phải giữ nguyên quyết định và lý do của chuyên viên.
```

Worker giữ case ở `HUMAN_DECIDED`, job `failed`, không tạo draft. Đây là fail-closed nhưng chặn
resume hợp lệ.

### Sau sửa

- Giữ nguyên prompt, schema, replay identity và một R11 LLM call.
- Kiểm tra response candidate trước: subject/body bắt buộc, citation phải thuộc evidence, không
  được đảo ngược trực tiếp quyết định, tự cấp thẩm quyền hoặc thêm số liệu/căn cứ không được hỗ trợ.
- Dựng nội dung draft cuối bằng logic xác định từ `choice` và `reason` đã lưu, sau PII masking;
  prose LLM không trở thành nguồn quyết định.
- Validator cho human-edited draft vẫn bắt buộc giữ `choice/reason`, citation/groundedness và bổ
  sung fail-closed `human_conflict` khi nội dung trực tiếp đảo ngược quyết định.
- Không đổi public interface, SQLite schema, workflow status, audit action, prompt/schema,
  cassette/manifest, call budget hoặc expected test lịch sử.

Đây không phải nối chuỗi để qua assertion: nguồn thẩm quyền của draft được chuyển về đúng dữ liệu
quyết định có cấu trúc đã commit trong DB; candidate không an toàn vẫn làm job fail và không tạo
draft.

## 4. Files changed và scope review

| File | Thay đổi |
|---|---|
| `core/resume.py` | Kiểm tra candidate và render draft xác định từ quyết định đã lưu; giữ safety guards |
| `tests/test_m3_t07_safety_remediation.py` | 8 targeted cases: replay R11, idempotency, unsafe candidates, human conflict, approval/send/restart/persistence/audit |
| `reports/sprints/M3_T07_SAFETY_REMEDIATION.md` | Evidence và handoff này |

Không đổi production file nào khác, cassette, manifest, corpus, policy, DB schema hoặc assertion
hiện hữu. Diff code/test so với baseline: 298 insertions, 6 deletions.

## 5. Validation commands và kết quả

Tất cả command chạy từ repository root. `--basetemp` và JUnit ở ngoài repository.

### 5.1 AC1 — reproduction trước sửa

```bash
env LLM_MODE=replay LLM_CACHE=0 OPENAI_MODEL=gpt-6-luna \
  .venv/bin/python -m pytest -q \
  tests/test_m3_t07_safety_remediation.py::test_existing_r11_replay_creates_one_safe_pending_approval_draft \
  --basetemp=/private/tmp/m3-t07-before-pytest \
  --junitxml=/private/tmp/m3-t07-before.xml
```

**FAIL — 0 PASS / 1 FAIL.** Actual `HUMAN_DECIDED`, expected `PENDING_APPROVAL`;
traceback tới `core/resume.py` với ValueError nêu ở Mục 3. JUnit SHA-256:
`c9ef1e3e67c7dcef33663b374e30d4c6fab78b35d4f2416c97d0bc9ac5dff606`.

### 5.2 Focused R11 trên exact tested SHA

```bash
env LLM_MODE=replay LLM_CACHE=0 OPENAI_MODEL=gpt-6-luna \
  .venv/bin/python -m pytest -q tests/test_m3_t07_safety_remediation.py \
  --basetemp=/private/tmp/m3-t07-postcommit-pytest \
  --junitxml=/private/tmp/m3-t07-postcommit.xml
```

**PASS — 8 PASS / 0 FAIL / 0 SKIP, 0.47s.** JUnit SHA-256:
`1b1354bec4037e0da386ea5c7f30020db59b411978a1aa9cd3a04415adf96551`.

### 5.3 Targeted blast-radius regression trên exact tested SHA

```bash
env LLM_MODE=replay LLM_CACHE=0 OPENAI_MODEL=gpt-6-luna \
  .venv/bin/python -m pytest -q \
  tests/test_m3_t07_safety_remediation.py \
  tests/test_runtime_worker.py tests/test_m3_atomicity.py tests/test_m3_failsafe.py \
  tests/test_database_isolation.py tests/test_offline_isolation.py \
  tests/test_runtime_replay_audit.py tests/test_ui_baseline_integration.py \
  --basetemp=/private/tmp/m3-t07-postcommit-targeted-pytest \
  --junitxml=/private/tmp/m3-t07-postcommit-targeted.xml
```

**PASS — 134 PASS / 0 FAIL / 0 SKIP, 6.70s.** Một Altair deprecation warning không liên
quan M3-T07. JUnit SHA-256:
`bc932a5471f242e908e1cb2d488757a1f442dd1e815d22f165ec45a06ebdac62`.

### 5.4 Static/diff checks

```bash
.venv/bin/python -m black --check --line-length 100 \
  core/resume.py tests/test_m3_t07_safety_remediation.py
.venv/bin/python -m ruff check core/resume.py tests/test_m3_t07_safety_remediation.py
git diff --check 9dfb33494cbf28e05651508ecfed145e5cc70fe7..cd989677b28352fc29239cab6c85b5285260c790
.venv/bin/python -m mypy --ignore-missing-imports core/resume.py
```

- Black: **PASS**.
- Ruff: **PASS**.
- Diff check: **PASS**.
- Mypy: **FAIL**, 4 lỗi baseline trong `infra/llm.py` tại 459, 484, 504, 510; không có lỗi
  `core/resume.py`/M3-T07. Không sửa vì ngoài scope và không gọi check này là PASS.
- Full suite: **NOT RUN**; Task Contract yêu cầu targeted validation, không có thay đổi ngoài blast
  radius đã chọn.

### 5.5 Replay identity

Cassette không đổi:
`tests/cassettes/2447ffcce6d7372fd5cdc1810653804259f0f7b82402b57472679884de20d015.json`.
SHA-256: `1f0df8886213ba84b7985e773ee949d0742be844afbd5e66550f7d97c4584417`.

Focused test xác nhận đúng một `R11_resume` call với `ok=1`; không có replay miss. Đây chỉ là
transport/replay evidence, không tự tạo semantic/product PASS.

## 6. R11 runtime evidence và safety invariants

Trên synthetic SQLite của test R11:

- Quyết định lưu trước resume: choice `Yêu cầu bản dịch`, reason synthetic và actor
  `HUMAN:local`; cả ba được bảo toàn sau resume/restart/send.
- Hai worker ticks chỉ tạo một resume draft, một `CASE_RESUMED`, job `done`; không duplicate.
- Draft chứa nguyên choice/reason đã lưu, grounded, không guard failure; case chuyển chính xác
  `HUMAN_DECIDED -> PENDING_APPROVAL`.
- Trước explicit approval không có `HUMAN_APPROVED_SEND` hoặc `SEND_DISPATCHED`.
- Preview hiện đúng draft; explicit human approval chuyển sang simulated `SENT`; approval lặp/stale
  bị từ chối; đúng một `HUMAN_APPROVED_SEND`, vẫn không có `SEND_DISPATCHED`.
- Process Python mới đọc cùng SQLite xác nhận một draft và state/decision/actor còn nguyên ở cả
  `PENDING_APPROVAL` và `SENT`.
- Candidate thiếu body, đảo quyết định, tự phê duyệt, thêm số liệu hoặc citation bịa đều giữ
  `HUMAN_DECIDED`, job `failed`, zero draft, một `CASE_ERROR`, không resume/approve/send.
- Draft do người sửa nhưng thêm câu đảo quyết định bị `human_conflict`; quyết định người thật sự
  positive vẫn cho phép wording thẩm quyền tương ứng.
- PII masking, citation membership, unsupported-value guard, authority guard và transaction/state
  machine hiện hữu không bị bỏ qua.

## 7. Acceptance Criteria

| AC | Disposition | Evidence / giới hạn |
|---|---|---|
| AC1 | **PASS** | R11 FAIL tái hiện trên baseline trước sửa; 1 failed node và traceback được giữ |
| AC2 | **PASS** | Root cause prompt cho phép paraphrase nhưng validator yêu cầu exact text; fix dùng stored decision làm nguồn thẩm quyền |
| AC3 | **PASS** | Exact cassette hit, zero miss, một R11 call, đúng một safe draft |
| AC4 | **PASS** | `HUMAN_DECIDED -> PENDING_APPROVAL`; không auto-send/dispatch trước approval |
| AC5 | **PASS trong targeted cases** | choice/reason/actor giữ nguyên; 5 unsafe candidate classes và edited contradiction fail-closed |
| AC6 | **PASS cho R11 synthetic/replay chain; product E2E NOT CLAIMED** | Preview, explicit simulated approval/send, fresh-process restart, SQLite persistence và audit có evidence; không LIVE/email |
| AC7 | **PASS** | 134 targeted regressions PASS; stale/double approval, idempotency, payload binding và atomicity suites gồm trong selection |
| AC8 | **BLOCKED** | Code/test commit, report, diff review, tested SHA, rollback/risk đã có; push/PR thiếu vì GitHub credential không sẵn có |

## 8. Risks, giới hạn và rollback

- Kiểm tra contradiction mới cố ý chỉ nhận diện các đảo ngược trực tiếp đã định nghĩa; không chứng
  minh hiểu mọi mâu thuẫn ngôn ngữ tự nhiên. Rủi ro được giới hạn bằng việc không dùng prose LLM
  trong draft cuối và vẫn yêu cầu human approval.
- Candidate prose được validate rồi loại khỏi nội dung cuối. Điều này ưu tiên nguồn quyết định đã
  lưu; reviewer cần xác nhận trade-off UX/wording là phù hợp contract.
- Test dùng actor/local, DB/input synthetic và simulated send. Không có evidence provider, inbox,
  SMTP hoặc dữ liệu thật.
- Mypy toàn dependency graph còn 4 lỗi baseline trong `infra/llm.py`; không phát sinh từ diff này.
- F01, V02, aggregate harness và product gate tổng thể vẫn giữ nguyên disposition của task sở hữu
  tương ứng. Không GO-STUDY/LIVE từ báo cáo này.
- Rollback: revert commit code/test và commit report; không cần DB migration, cassette re-record,
  corpus/policy rollback hay dữ liệu chuyển đổi.

## 9. Handoff

- Owner/implementer: người được Coordinator giao M3-T07; Codex hỗ trợ implementation và
  self-review trong scope được duyệt.
- Reviewer cần kiểm tra `core/resume.py`, targeted test, giới hạn semantic ở Mục 8 và evidence hash.
- PR phải nhắm `dev`, không force-push, không merge trong task này.
- Coordinator quyết định acceptance/DONE và mọi product gate; báo cáo này không thay quyết định đó.
- Blocker: GitHub HTTPS không có username/credential trên máy. Ảnh hưởng: remote branch và PR chưa
  tồn tại. Owner: người có quyền GitHub push các commit local và mở PR vào `dev`. Coordinator cần
  xác nhận sau khi PR hiện diện; không cần thay đổi production/contract để giải blocker này.

**E2E STATUS:** R11 replay/synthetic human-control chain PASS trong phạm vi targeted; complete
product E2E và LIVE **NOT VERIFIED / NOT AUTHORIZED**.

**PR:** **NOT CREATED / BLOCKED** — push bị từ chối do credential không sẵn có; không lưu credential
trên máy, không force-push, không merge.
