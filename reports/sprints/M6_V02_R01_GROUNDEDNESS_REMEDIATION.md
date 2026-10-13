# M6-V02-R01 — Khắc phục groundedness cho Verify V02

## Kết luận

- Task ID: `M6-V02-R01`
- Vai trò thực thi: Codex — implementer
- Execution Owner / final approver: Project Coordinator
- Trạng thái candidate: `READY_FOR_COORDINATOR_REVIEW`
- Branch: `sprint/m6-v02-r01-groundedness`
- Baseline SHA: `8d79492a8354aa2b6e0f92dce748a908e70a1506`
- Tested source state: baseline trên cộng đúng diff của bốn file được phép; production file có SHA-256 `d5c3a552ad37bcad150ee910eff5135c090f89e8e189516a36ad0c8ee5dfffaa`
- Final SHA: xem commit/PR và handoff sau khi report này được commit; commit không thể tự chứa SHA của chính nó
- LIVE/API/email: **0**

V02 đã đổi từ expected `AUTO_REPLY/P05`, actual
`ESCALATE/FACT_UNRESOLVED/P04`, `groundedness_failed:number` thành actual
`AUTO_REPLY/P05`. V01–V04 đạt **4/4 semantic PASS** trên product pipeline/replay thật,
**12/12 replay hits, 0 misses**, không sửa expected, cassette hoặc Gold.

## Môi trường và provenance

| Hạng mục | Giá trị |
|---|---|
| Docker Server | `29.1.3` |
| Python trong image | `3.11.17` |
| Baseline image | `exodia:m6-v02-r01-before-8d79492` |
| Baseline image ID | `sha256:10fc78ca96963242806512da280cc38a67890dd84a26f3cdb75dc0a4683d866c` |
| Exact candidate image | `exodia:m6-v02-r01-candidate` |
| Candidate image ID | `sha256:5645ad2c5abda70ac3f71aee0e88b89d072c00d8ff3e0317a16c151f1b154b8b` |
| Candidate construction | baseline image cộng duy nhất `core/ground_guard.py`; label task/baseline; không network |
| Replay mode | `LLM_MODE=replay`, provider `openai`, model `gpt-6-luna`, reasoning `none`, cache `0` |
| DB | `/tmp/app.db`, mới theo container và bị hủy khi container thoát |
| Network | Docker `--network none`; `_call_live` bị audit replay chặn |
| Replay pack | `tests/cassettes`, 24 file, bind mount read-only |
| Pack manifest | `reports/readiness/M6_T05_BASE24_RECORDED_PACK.json` |
| Manifest SHA-256 | `2a3c80855923010e3ead807424bc1d2e904c01422ab08eade7655fe30aa280c8` |

Preflight xác minh `origin/dev` đúng baseline, working tree sạch trước khi tạo branch,
không có branch/task ID trùng, và PR #48 của M6-T03 vẫn `OPEN/DRAFT` tại
`92be4059c330e06a8c25c76e1b8630c3ef534700`. Không tạo clone/worktree khác và không
thay đổi M6-T03.

V02 dùng hai evidence chunk được draft trích dẫn:

- `RH-2026-101:seed:1`: ACTIVE, `effective_from=2026-08-01`, effective tại ngày case
  `2026-09-21`; breadcrumb `Quy chế rút học phần năm học 2026-2027 · Điều 1`.
- `RH-2026-101:seed:4`: ACTIVE, cùng hiệu lực; breadcrumb
  `Quy chế rút học phần năm học 2026-2027 · Điều 2`.

Các chunk này là evidence thật được retrieval trả về và citation thật của draft; không lấy số từ
breadcrumb không được trích dẫn.

## Before fix và nguyên nhân gốc

Lượt reproduction trên baseline image, network none:

```text
V02 | AUTO_REPLY/- | ESCALATE/FACT_UNRESOLVED | P04 | FAIL
```

Artifact cục bộ bị ignore: `data/validation/m6-v02-r01/before-v02.json`.

Nguyên nhân gốc:

1. Generator dựng evidence context từ `breadcrumb + text`, nên draft hợp lệ có cụm
   `2026–2027 academic year` và giờ `5:00 p.m.`.
2. Numeric guard chỉ lấy số từ `chunk.text`; cặp `2026`, `2027` nằm trong breadcrumb của
   chính evidence được cite nên bị xem là unsupported.
3. Normalization đồng hồ đã đúng: `5:00 p.m.` được đối chiếu với `17 giờ 00` và loại khỏi
   numeric check. Probe before-fix còn đúng hai số unsupported là `2026`, `2027`; vì vậy
   clock không phải root cause.

Hai regression dương tính mới chạy trên baseline code trước khi sửa đều FAIL đúng P04:

```text
2 failed
groundedness_failed:number
```

## Thay đổi và safety trade-off

`core/ground_guard.py` thêm normalization hẹp cho năm học:

- Chỉ nhận cặp bốn chữ số khi có ngữ cảnh rõ `năm học 2026-2027`,
  `2026-2027 academic year` hoặc dạng tương đương đã khai báo.
- Chỉ ground khi đúng cặp năm xuất hiện trong breadcrumb của chunk nằm trong
  `draft.citations`.
- Không thêm toàn bộ số trong breadcrumb vào `source_numbers`; tiền, ngày, thời hạn,
  phần trăm và số liệu khác không được hưởng miễn trừ.
- Citation guard vẫn buộc citation tồn tại trong evidence và ACTIVE. Retrieval/pipeline vẫn
  chịu trách nhiệm chọn evidence có hiệu lực tại thời điểm case.
- Clock equivalence, authority guard, citation ratio, policy, routing, approval, audit,
  SQLite contract và public interface không thay đổi.

Rollback: revert commit của task này; không có migration, data rewrite hay cassette change.

## Regression tests

Positive:

- V02 với breadcrumb năm học được cite và `5:00 p.m.`/`17 giờ 00`: PASS.
- Full guard trả grounded draft, không tạo P04: PASS.

Fail-closed:

- Không có năm học trong breadcrumb: PASS (bị chặn).
- Cùng số nhưng ngữ cảnh `Quyết định số 2026-2027`: PASS (bị chặn).
- Sai năm `2025-2026`: PASS (bị chặn).
- Năm học chỉ có trong breadcrumb không được cite: PASS (bị chặn).
- Tiền, thời hạn theo ngày, phần trăm không được text hỗ trợ: PASS (bị chặn).
- Clock không tương đương: PASS (bị chặn bởi regression hiện hữu).
- Citation không hợp lệ/không ACTIVE: PASS (bị chặn bởi citation guard hiện hữu).
- Authority claim không hợp lệ: PASS (bị chặn bởi authority guard hiện hữu).

## Product Verify V01–V04

| Case | Expected | Actual | Rule expected/actual | Replay | Kết quả |
|---|---|---|---|---:|---|
| V01 | `AUTO_REPLY` | `AUTO_REPLY` | `P05/P05` | 3 hits, 0 miss | PASS |
| V02 | `AUTO_REPLY` | `AUTO_REPLY` | `P05/P05` | 3 hits, 0 miss | PASS |
| V03 | `ESCALATE/AUTHORITY_REQUIRED` | `ESCALATE/AUTHORITY_REQUIRED` | `P01/P01` | 4 hits, 0 miss | PASS |
| V04 | `ESCALATE/OUT_OF_POLICY` | `ESCALATE/OUT_OF_POLICY` | `P02/P02` | 2 hits, 0 miss | PASS |

- Executed: **4/4**
- Semantic PASS: **4/4**
- Raw replay calls: **12**
- Hits/misses: **12/0**
- LIVE provider calls/API/email: **0/0/0**
- Artifact cục bộ bị ignore: `data/validation/m6-v02-r01/final-V01.json` đến
  `final-V04.json`.

## Validation commands và kết quả

Các Docker run bên dưới đều có `--network none --read-only --tmpfs /tmp`,
`--cap-drop ALL`, `no-new-privileges`, cassette read-only và DB tạm. Đường dẫn host tuyệt đối
được rút gọn thành `<repo>` trong bảng.

| Command | Kết quả |
|---|---|
| `git fetch origin --prune` và xác minh `origin/dev` | PASS — đúng baseline |
| `docker run ... baseline ... pytest ...::test_v02... ...::test_ground_guard...` | EXPECTED FAIL — 2/2 tái hiện lỗi trước fix |
| `docker run ... baseline + candidate file ... pytest` cho 9 regression mới | PASS — 9 passed |
| `docker build --network none --tag exodia:m6-v02-r01-candidate .` | FAIL — dependency layer không có cache và network bị khóa; không có app/API call |
| Tạo image candidate từ baseline và copy duy nhất `core/ground_guard.py` | PASS — exact image ID nêu trên |
| `docker run ... candidate ... pytest -q tests/test_semantic_validator_compat.py tests/test_guards.py` | PASS — final run 135 passed in 2.07s |
| `docker run ... candidate -m verify.harness --set verify4 --case <V01..V04>` | PASS — 4/4 semantic PASS |
| `docker run ... candidate -c <audit V01-V04>` | PASS — 12 calls, 12 hits, 0 misses, LIVE=0 |
| `python -m black --check --line-length 100 core/ground_guard.py tests/test_semantic_validator_compat.py` | PASS |
| `python -m ruff check core/ground_guard.py tests/test_guards.py tests/test_semantic_validator_compat.py` | PASS |
| `git diff --check` | PASS |

Không chạy full suite vì thay đổi chỉ tác động numeric groundedness; hai file targeted đã phủ
logic, guard integration, citation, authority, clock và fail-closed cases. Không chạy browser,
public deployment hoặc LIVE provider.

## AC1–AC7

Do Coordinator cho phép bỏ riêng bước kiểm tra Trello, mapping dưới đây bám trực tiếp approved
prompt trong chat.

| AC | Trạng thái | Evidence |
|---|---|---|
| AC1 — Reproduce và provenance | PASS | Before-fix V02 tái hiện P04; cited chunks ACTIVE/effective và liên hệ draft/evidence được xác minh |
| AC2 — Smallest safe fix | PASS | Chỉ production change trong `core/ground_guard.py`; không mở generic breadcrumb numbers |
| AC3 — Positive behavior | PASS | V02 năm học và clock equivalence đạt `AUTO_REPLY/P05` |
| AC4 — Safety/fail-closed | PASS | Năm không chứng minh, giờ sai, tiền/thời hạn/số liệu sai, citation và authority vẫn bị chặn |
| AC5 — Targeted regressions | PASS | 135 targeted tests PASS; targeted Black và Ruff PASS |
| AC6 — Product Verify/replay | PASS | V01–V04 4/4; 12/12 hits, 0 misses, LIVE/API/email=0 |
| AC7 — Evidence/self-review/handoff | PASS candidate | Report, diff/scope/credential scan; commit/PR metadata ở handoff |

## Self-review, scope và rủi ro

- Full diff review: production delta chỉ thêm academic-year matcher hẹp và gọi normalization
  trước generic number comparison; không bypass guard hay sửa draft.
- Scope: chỉ bốn file được phép. Không sửa cassette, expected, Gold, policy/schema, routing,
  approval, audit, SQLite contract, M6-T03/PR #48, Trello hoặc `STATUS.md`.
- Sensitive-data/credential/PII scan trên added lines và report: 0 credential pattern, 0 email,
  0 số điện thoại. Dữ liệu test dùng ID synthetic; không có key/token/email thật.
- Residual risk: matcher chỉ hỗ trợ các cách ghi năm học đã khai báo; cách diễn đạt khác vẫn
  fail-closed và cần evidence/test riêng.
- BuildKit offline không tái dựng được toàn Dockerfile vì dependency layer cache thiếu. Exact
  candidate image được tạo từ baseline image đã xác minh cộng đúng production file, sau đó test
  lại toàn bộ targeted regressions và Verify. Một clean Docker build từ Dockerfile vẫn nên được
  CI thực hiện khi có dependency network/cache; đây không phải app LIVE/API call và không làm
  yếu evidence runtime hiện tại.

## Handoff

Coordinator review diff, report, candidate image/provenance và PR; không tự động merge. Task
không được tuyên bố DONE trong report này.
