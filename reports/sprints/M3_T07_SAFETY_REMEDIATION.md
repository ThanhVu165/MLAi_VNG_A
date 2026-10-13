# M3-T07 — Remediation R11 Human Decision/Resume

## 0. Change Request — MLAI review / PR #47

**CURRENT RESULT: READY_FOR_FINAL_REVIEW sau khi correction được push lên PR #47; chưa merge,
chưa DONE và không phải product gate PASS.**

### Preflight correction

- Reviewed SHA: `762520eb1de754c89c43c686c8fe6fd42b68a9cf`.
- Correction code/test SHA: `37619ddec6e4f93489e518da778c7e4d401ea1a9` —
  `fix(m3-t07): harden resume authority validation`.
- PR: [#47](https://github.com/ThanhVu165/MLAi_VNG_A/pull/47), branch
  `sprint/m3-t07-safety-remediation`, target `dev`.
- Remote branch và `refs/pull/47/head` đều trỏ đúng reviewed SHA khi preflight.
- `origin/dev` hiện tại: `348058f9c7c0f9d81ab38870271b4260fadbb79f`; merge base và parent
  của code commit M3-T07 vẫn là baseline `9dfb33494cbf28e05651508ecfed145e5cc70fe7`.
  Không rebase/merge/đổi baseline. Read-only merge-tree không phát hiện conflict; thay đổi mới trên
  `dev` thuộc Docker và worker startup instrumentation, không chạm ba file correction.
- Working tree sạch tại đầu lượt; diff chỉ có ba file được Task Contract cho phép.

### Finding authority — before/after

Regression dùng `choice="Yêu cầu bổ sung"`, trong khi `reason` chỉ nhắc hồ sơ tham chiếu
"đã được duyệt"; candidate lại khẳng định case hiện tại "đã được duyệt".

Trước fix, test mới **FAIL**: actual `PENDING_APPROVAL`, expected `HUMAN_DECIDED`. Cụm từ trong
`reason` làm `human_authorizes=True`, đồng thời `_authority_failure(trusted)` cũng bị dùng như
giấy phép. Candidate vượt thẩm quyền vì vậy lọt validator. JUnit SHA-256:
`ad15c6018cb8dc32174c0d575532b7c0796a7c914232c61a1a14d3e615f2bb0c`.

Fix chỉ suy quyền từ affirmative decision rõ ràng ở đầu `choice`; quyết định phủ định luôn thắng,
và `reason`/`_authority_failure(trusted)` không còn cấp quyền. `reason` vẫn được bảo toàn làm dữ
liệu tin cậy cho groundedness/unsupported-value checks. Positive choice `Chấp thuận` vẫn PASS;
candidate mâu thuẫn, vượt thẩm quyền, bịa citation/số liệu tiếp tục fail-closed.

### Correction validation trên exact SHA `37619dd`

| Check | Kết quả | Evidence |
|---|---|---|
| Regression reason-only authority | **PASS — 1/1** | Sau fix giữ `HUMAN_DECIDED`, job failed, zero draft, một `CASE_ERROR`, không resume/approve |
| Focused M3-T07 | **PASS — 9/9**, 0.51s | `/private/tmp/m3-t07-cr-postcommit-focused.xml`; SHA-256 `ca26035d27e6c896a57b825afa50e3722d1a259ee8d96f6596c1b5dc2b361011` |
| Targeted blast radius | **PASS — 135/135**, 1 warning, 6.77s | JUnit SHA-256 `d95a71b8f06635b72d914cac908bf97a83383e68e15e2acf228023e3cd97e072` |
| Black | **PASS** | Hai file code/test unchanged by formatter |
| Ruff | **PASS** | Không có finding |
| Diff check | **PASS** | Không whitespace error |
| Mypy | **FAIL — baseline** | 4 lỗi `infra/llm.py:459,484,504,510`; không có lỗi M3-T07 |
| Full suite | **NOT RUN** | Task Contract yêu cầu targeted regression; không nâng thành full-suite PASS |

Targeted command giữ nguyên selection ở Mục 5.3 và thêm regression mới. Environment:
Python 3.11.17, SQLite 3.53.1, `LLM_MODE=replay`, `LLM_CACHE=0`, model
`gpt-6-luna`, synthetic SQLite/temp ngoài repository. R11 cassette không đổi, SHA-256
`1f0df8886213ba84b7985e773ee949d0742be844afbd5e66550f7d97c4584417`.
Không LIVE/API/recording/email thật.

### Change Request AC mapping

| AC | Disposition | Evidence / giới hạn |
|---|---|---|
| AC1 | **PASS** | Regression trước fix tái hiện bypass thật: `PENDING_APPROVAL` thay vì fail-closed |
| AC2 | **PASS** | Cùng expected FAIL trước fix, PASS sau fix; không sửa expected để che lỗi |
| AC3 | **PASS** | R11 replay, choice/reason/actor, approval, audit, restart, persistence và idempotency nằm trong 9 focused/135 targeted PASS |
| AC4 | **PASS** | Reason-only authority giữ `HUMAN_DECIDED`, zero draft; R11 hợp lệ vẫn không auto-send |
| AC5 | **PASS** | Black, Ruff, diff và targeted PASS; mypy baseline FAIL và full suite NOT RUN được công bố đúng |
| AC6 | **PASS** | Report ghi PR #47, reviewed/correction SHA, validation mới và blocker cũ đã giải quyết |
| AC7 | **PASS — handoff prepared** | Scope/self-review/secret scan và evidence hoàn tất; final reviewer/Coordinator acceptance còn pending |

### Owner self-review và Trello handoff content

- **Self-review: COMPLETED.** Full correction diff từ reviewed SHA chỉ sửa ba file allowed;
  production change giới hạn ở authority gate trong `core/resume.py`.
- Prompt/schema/cassette/replay identity, public interface, SQLite schema, audit action, workflow,
  policy, expected tests và LLM call budget không đổi.
- Scope/diff/secret scan: PASS; không có credential, PII thật, local DB/cache hoặc file ngoài scope.
- F01, V02, aggregate harness và product gate giữ nguyên, không được xử lý trong correction này.

Nội dung handoff để Owner đăng vào Trello (không thay Coordinator đánh DONE):

```text
M3-T07 CHANGE REQUEST / PR #47
RESULT: READY_FOR_FINAL_REVIEW
CORRECTION SHA: 37619ddec6e4f93489e518da778c7e4d401ea1a9
AUTHORITY REGRESSION: FAIL trước fix (PENDING_APPROVAL bypass) -> PASS sau fix (fail-closed)
VALIDATION: 9/9 focused PASS; 135/135 targeted PASS; Black/Ruff/diff PASS
KNOWN CHECKS: mypy FAIL 4 lỗi baseline infra/llm.py; full suite NOT RUN
SAFETY: R11 replay/PENDING_APPROVAL/approval/restart/persistence/idempotency PASS; LIVE/API/email=0
PR: https://github.com/ThanhVu165/MLAi_VNG_A/pull/47
LIMIT: R11 targeted PASS không phải product gate hoặc complete LIVE E2E PASS
REQUEST: Final reviewer kiểm tra authority fix/evidence; Coordinator quyết định acceptance/merge.
```

## 1. Kết luận

**RESULT: READY_FOR_FINAL_REVIEW trong phạm vi M3-T07; chưa DONE, chưa merge, không phải product gate PASS.**

R11 FAIL đã được tái hiện trên baseline, nguyên nhân đã được xác nhận và bản sửa nhỏ nhất đã
được kiểm chứng offline trên code commit `cd989677b28352fc29239cab6c85b5285260c790`.
R11 hiện tạo đúng một draft an toàn từ quyết định đã lưu, chuyển
`HUMAN_DECIDED -> PENDING_APPROVAL`, không tự gửi; preview, duyệt gửi mô phỏng, restart,
SQLite persistence và audit đều có targeted evidence. Không có LIVE/API, recording, email thật
hoặc dữ liệu người tham gia.

Kết luận kỹ thuật chỉ áp dụng cho chuỗi R11 synthetic/replay được mô tả tại đây. Replay hit và
pytest xanh không chứng minh complete product E2E, vận hành thật hoặc GO-STUDY/LIVE. F01, V02 và
aggregate harness ngoài scope, không được sửa hay tái phân loại.

Lịch sử được giữ nguyên: push đầu tiên không force đã dừng với
`fatal: could not read Username for 'https://github.com': Device not configured`; không credential
nào được lưu hoặc bypass. Blocker sau đó đã được Owner giải quyết, branch được push và PR #47 đã
được tạo. Correction này tiếp tục cập nhật đúng PR đó, không mở PR mới.

## 2. Authorization, baseline và preflight

- Project Coordinator cung cấp trực tiếp Task Contract M3-T07 và GO trong chat ngày 14/10/2026;
  đây là authorization hiện hành thay cho việc Codex tự thao tác Trello. Không đọc/ghi/move card
  hoặc tuyên bố DONE trên Trello.
- Đã đọc `AGENT.md`, `PROJECT_SPEC.md`, `docs/TEAM_WORKFLOW.md` và source/test liên quan.
- Repository: `https://github.com/ThanhVu165/MLAi_VNG_A.git`.
- Remote `dev` tại lượt triển khai ban đầu:
  `9dfb33494cbf28e05651508ecfed145e5cc70fe7`.
- Baseline/source parent: `9dfb33494cbf28e05651508ecfed145e5cc70fe7`.
- Branch: `sprint/m3-t07-safety-remediation`, tạo trực tiếp từ verified `origin/dev`; không có
  branch local/remote cùng tên tại preflight, không clone/worktree phụ, không reset/stash/clean.
- Initial tested code/test SHA: `cd989677b28352fc29239cab6c85b5285260c790`.
- Initial code/test commit: `fix(m3-t07): remediate human decision resume`; correction SHA và
  remote preflight mới ở Mục 0.
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
| `tests/test_m3_t07_safety_remediation.py` | 9 targeted cases: replay R11, idempotency, authority bypass, unsafe candidates, human conflict, approval/send/restart/persistence/audit |
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
| AC7 | **PASS** | Correction run 135 targeted regressions PASS; stale/double approval, idempotency, payload binding và atomicity suites gồm trong selection |
| AC8 | **READY_FOR_FINAL_REVIEW** | Code/test commits, report, diff review, tested SHA, rollback/risk và PR #47 đã có; independent review/Coordinator acceptance pending |

## 8. Risks, giới hạn và rollback

- Kiểm tra contradiction mới cố ý chỉ nhận diện các đảo ngược trực tiếp đã định nghĩa; không chứng
  minh hiểu mọi mâu thuẫn ngôn ngữ tự nhiên. Rủi ro được giới hạn bằng việc không dùng prose LLM
  trong draft cuối và vẫn yêu cầu human approval.
- Authority helper cố ý chỉ chấp nhận affirmative decision rõ ràng ở đầu `choice`; lựa chọn tùy
  biến mơ hồ hoặc chỉ yêu cầu cấp khác xem xét sẽ fail-closed thay vì suy quyền từ `reason`.
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
- Blocker GitHub credential ban đầu đã được Owner giải quyết; failure cũ vẫn được giữ ở Mục 1 để
  bảo toàn audit trail. Không có blocker implementation hiện hành.

**E2E STATUS:** R11 replay/synthetic human-control chain PASS trong phạm vi targeted; complete
product E2E và LIVE **NOT VERIFIED / NOT AUTHORIZED**.

**PR:** [#47 — M3-T07 safety remediation](https://github.com/ThanhVu165/MLAi_VNG_A/pull/47),
target `dev`; không force-push, không merge.
