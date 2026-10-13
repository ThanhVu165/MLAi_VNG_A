# M6-T03 — Docker Replay & Verify Integration

## Kết luận

- Task ID: `M6-T03`
- Execution Owner: Project Coordinator
- `RESULT=BLOCKED`
- Trạng thái: **BLOCKED**
- Preflight: `STARTABLE`
- Baseline SHA / tested source SHA: `348058f9c7c0f9d81ab38870271b4260fadbb79f`
- Branch: `sprint/m6-t03-replay-verify`
- Commit/PR: chỉ handoff blocker evidence; **không phải PASS candidate**.
- LIVE/API/email: **0**

M6-T03 không đủ điều kiện làm PASS candidate. Commit/PR chỉ bảo toàn blocker evidence. Trên exact image và đúng replay config, V02 có expected `AUTO_REPLY/P05` nhưng actual `ESCALATE/FACT_UNRESOLVED/P04`. Không sửa cassette, expected result, policy hay business logic trong M6-T03.

Disposition: **Coordinator/Runtime Owner cần quyết định remediation task/Owner riêng.**

## Môi trường và image

| Hạng mục | Giá trị |
|---|---|
| Docker Server | `29.1.3`, Linux, `overlayfs` |
| Docker Compose | `v2.40.3-desktop.1` |
| Python trong image | `3.11.17` |
| Image tag | `exodia:m6-t03-348058f` |
| Image digest/ID | `sha256:05678ee9830084c1d3334be4cc84f951541a8f189aea8f209f05a671f0fd0cec` |
| LLM mode | `replay` |
| Provider/model identity | `openai` / `gpt-6-luna` |
| Cache | tắt (`LLM_CACHE=0`) |
| DB | `/tmp/app.db` hoặc temporary directory riêng trong container; synthetic, bị hủy cùng container |
| Network | `none` |
| Cassette mount | `tests/cassettes` → `/app/tests/cassettes`, read-only |

`docker compose config --quiet` trả exit `0`. Build exact source bằng:

```powershell
docker build --pull=false -t exodia:m6-t03-348058f .
docker image inspect exodia:m6-t03-348058f --format 'ID={{.Id}} REPO_DIGESTS={{json .RepoDigests}} CREATED={{.Created}}'
docker run --rm --network none --entrypoint python exodia:m6-t03-348058f --version
```

Build dùng đúng checkout tại tested SHA; không mount source host vào `/app`.

## Replay pack và provenance

- Manifest kỹ thuật: `reports/readiness/M6_T05_BASE24_RECORDED_PACK.json`
- SHA-256 manifest: `2a3c80855923010e3ead807424bc1d2e904c01422ab08eade7655fe30aa280c8`
- Replay result tham chiếu: `reports/readiness/M6_T05_BASE24_REPLAY_RESULT.json`
- SHA-256 replay result: `e087aa86d955464179434b49da54d9af39d4921f4e551f8319cf2f54ffd9e262`
- Pack scope/status: `BASE_PACK_V1_PLUS_DELTA_REPAIR_V1` / `VALIDATED_ZERO_MISS_PENDING_COORDINATOR_ACCEPTANCE`
- Recording SHAs: `8371b34385c39696d8ccfd06dae93311fd3e58fa`, `dfcdec2f6d557a72f5adf742bb4fc1bb36fa5359`
- M6-T05 merge SHA `8e32ee43158160ac3dda6a84906871f3e3c183f2` là ancestor của baseline.
- Integrity hiện hành: 24 file; **24/24 hash khớp**, 0 mismatch; manifest ghi `PASS_24_OF_24`.
- Provenance: **PASS** cho traceability kỹ thuật; từng cassette có prompt hash, file hash, model, recorded SHA, request ID, SDK response hash, thời điểm và nguồn authorized provider response.
- Không re-key, tạo mới hay sửa cassette/manifest/expected result.

Đối chiếu source fingerprint có hai sai khác so với thời điểm record: `core/worker.py` và `scripts/guarded_runtime_delta_recording.py`. `core/worker.py` thay đổi ở M6-T02; file recording helper không thuộc runtime replay. Critical run hiện hành vẫn đạt 23/23 replay hits, nên pack tương thích với các flow đã thực thi; sai khác fingerprint vẫn được giữ là risk cần reviewer biết.

## Lệnh chạy integration

Mỗi container dùng `--network none`, `--read-only`, `--tmpfs /tmp`, `--cap-drop ALL`, `no-new-privileges`, cassette bind-mount read-only và DB synthetic. Config identity dùng đúng manifest, trong đó có:

```text
LLM_MODE=replay
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-6-luna
OPENAI_REASONING_EFFORT=none
LLM_CACHE=0
LLM_TIMEOUT_S=30
LLM_RETRIES=1
SIMILARITY_THRESHOLD=0.35
CITATION_RATIO_MIN=0.6
RETRIEVAL_TOP_K=6
QUESTION_WORDS_MIN=8
QUESTION_WORDS_MAX=45
PENDING_SEND_SECONDS=60
PENDING_STATUS_REFRESH_SECONDS=1
```

Verify case command tương đương cho từng `V01`–`V04`:

```powershell
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m --cap-drop ALL --security-opt no-new-privileges:true -e LLM_MODE=replay -e LLM_PROVIDER=openai -e OPENAI_MODEL=gpt-6-luna -e OPENAI_REASONING_EFFORT=none -e LLM_CACHE=0 -e DATABASE_PATH=/tmp/app.db --mount "type=bind,source=<repo>\tests\cassettes,target=/app/tests/cassettes,readonly" --mount "type=bind,source=<repo>\data\validation\m6-t03,target=/evidence" --entrypoint python exodia:m6-t03-348058f -m verify.harness --set verify4 --case <V01|V02|V03|V04> --output /evidence/configured-verify-<case>.json
```

Critical evidence dùng `scripts.audit_runtime_replay` trong image, bỏ riêng `DEV_HUMAN_R11` vì ngoài critical scope M6-T03. Product pipeline không bị stub. Raw artifact cục bộ (ignored):

- `data/validation/m6-t03/critical/M6_T05_REPLAY_EVIDENCE.json`
- `data/validation/m6-t03/critical/M6_T05_REPLAY_MANIFEST.json`
- `data/validation/m6-t03/configured-verify-V01.json` đến `configured-verify-V04.json`

Runner trả exit `2` theo thiết kế vì nó không tự cấp acceptance cho provenance; raw runtime result là **23 calls / 23 hits / 0 replay failures / LIVE=0**.

Lần thử đầu chỉ đặt `LLM_MODE=replay` và `LLM_CACHE=0` đã fail-safe với `Chưa cấu hình OPENAI_MODEL`. Kết quả này chứng minh replay cần model/config identity của pack; các kết quả chính bên dưới là lượt rerun bằng config đầy đủ.

## AC2 — replay result

| Chỉ số | Kết quả |
|---|---:|
| Flow product/Verify thực thi | 7 |
| Prompt calls | 23 |
| Replay hits | 23 |
| Replay failures/misses | 0 |
| Missing flow | 0 trong critical + V01–V04 |
| LIVE fallback | 0 |
| LIVE/API/email | 0 |

AC2: **PASS**. Coverage replay PASS không che semantic FAIL của V02.

## AC3 — critical flows

| Flow/scenario | Expected | Actual | Stop reason / rule | DB và audit | Miss | Kết quả |
|---|---|---|---|---|---:|---|
| Routine / `DEV_ROUTINE` | `AUTO_REPLY` | `AUTO_REPLY` | `P05` | `PENDING_SEND`, draft=1; có `EVIDENCE_RETRIEVED`, `EVIDENCE_VALIDATED`, `DRAFT_GENERATED`, `SEND_SCHEDULED` | 0 | PASS |
| OUT_OF_POLICY / `V04` | `ESCALATE/OUT_OF_POLICY` | `ESCALATE/OUT_OF_POLICY` | `P02` | `AWAITING_HUMAN`, draft=0; kết thúc `QUESTION_GENERATED`, `CASE_QUEUED` | 0 | PASS |
| AUTHORITY_REQUIRED / `DEV_AUTHORITY` | `ESCALATE/AUTHORITY_REQUIRED` | `ESCALATE/AUTHORITY_REQUIRED` | `P01` | `AWAITING_HUMAN`, draft=0; kết thúc `QUESTION_GENERATED`, `CASE_QUEUED` | 0 | PASS |
| FACT_UNRESOLVED / `DEV_FACT` | `ESCALATE/FACT_UNRESOLVED` | `ESCALATE/FACT_UNRESOLVED` | `P03` | `AWAITING_HUMAN`, draft=0; kết thúc `QUESTION_GENERATED`, `CASE_QUEUED` | 0 | PASS |

AC3: **PASS (4/4)**.

## AC4 — Verify V01–V04

| Case | Expected | Actual | Rule expected/actual | Evidence | Replay | Semantic |
|---|---|---|---|---|---|---|
| V01 | `AUTO_REPLY` | `AUTO_REPLY` | `P05/P05` | `PENDING_SEND`, draft=1, corpus `cv_f6eb04187bb0` | 3 hits, 0 miss | PASS |
| V02 | `AUTO_REPLY` | `ESCALATE/FACT_UNRESOLVED` | `P05/P04` | `GROUNDEDNESS_FAILED`, `CASE_QUEUED`, corpus `cv_f6eb04187bb0` | 3 hits, 0 miss | **FAIL** |
| V03 | `ESCALATE/AUTHORITY_REQUIRED` | `ESCALATE/AUTHORITY_REQUIRED` | `P01/P01` | `AWAITING_HUMAN`, question card tồn tại | 4 hits, 0 miss | PASS |
| V04 | `ESCALATE/OUT_OF_POLICY` | `ESCALATE/OUT_OF_POLICY` | `P02/P02` | `AWAITING_HUMAN`, question card tồn tại | 2 hits, 0 miss | PASS |

- EXECUTED: **4/4**
- Semantic PASS: **3/4**
- Semantic FAIL: **1/4 (`V02`)**
- Missing: **0/4**

Đối chiếu evidence hiện hành cho thấy đây là cùng biểu hiện đã ghi trong M6-T05: groundedness không chấp nhận cách diễn đạt thời gian tiếng Anh `5:00 p.m.` so với căn cứ `17 giờ 00`. Kết luận dựa trên run hiện hành, không mặc định từ historical report.

AC4: **FAIL**.

## AC5 — persistence/reset/restart

**NOT RUN** sau khi Stop Condition V02 được kích hoạt.

Phần đã chứng minh: mọi lượt đã chạy dùng DB synthetic riêng trong `/tmp`/temporary directory và container network riêng; không mount hay chạm volume/DB `dev`, `study`, `demo`. Chưa chạy chu kỳ seed → run 1 → restart → rerun, nên không tuyên bố deterministic persistence.

## AC6 — reporting/audit

**NOT RUN đầy đủ** sau Stop Condition.

Raw evidence đã ghi đúng transition của bảy flow. Riêng V02 ghi `GROUNDEDNESS_FAILED` rồi `CASE_QUEUED`, không ghi `SEND_SCHEDULED`. Không có `TECHNICAL_ERROR` trong lượt configured critical. Yêu cầu kiểm riêng rằng `TECHNICAL_ERROR` không bị tính như completed automation chưa được thực thi tới kết luận, nên AC6 không được gọi PASS.

## AC7 — evidence

**PASS cho blocker evidence report**. Báo cáo này ghi đầy đủ exact image, pack/provenance/hash, config, raw counts, expected/actual, FAIL/NOT RUN và LIVE/API=0. Commit/push/PR chỉ phục vụ evidence handoff được Coordinator cho phép; không biến AC4 thành PASS.

## Ma trận AC

| AC | Trạng thái | Evidence chính |
|---|---|---|
| AC1 — Exact image | PASS | image digest, Python 3.11.17, Compose config exit 0, replay config và DB path |
| AC2 — Replay | PASS | 23/23 hits, 0 miss, LIVE=0 |
| AC3 — Critical flows | PASS | 4/4 expected/actual match |
| AC4 — Verify V01–V04 | **FAIL** | V02 mismatch; 4/4 executed, 3/4 semantic PASS |
| AC5 — Persistence/reset/restart | NOT RUN | dừng theo Stop Condition |
| AC6 — Reporting/audit | NOT RUN | partial event evidence, chưa hoàn tất TECHNICAL_ERROR metric check |
| AC7 — Evidence | PASS (local blocker report) | file này và ignored raw artifacts |

## Risks và downstream impact

- V02 là semantic mismatch trên exact candidate image; sửa cần thay đổi production/business behavior ngoài scope M6-T03.
- Persistence/restart và TECHNICAL_ERROR reporting chưa được xác minh vì bắt buộc dừng sau mismatch.
- Image chỉ nhận replay config đầy đủ khi command/environment truyền model identity; chỉ `LLM_MODE=replay` là chưa đủ để chạy pipeline.
- Hai source fingerprints khác thời điểm record được công khai ở trên; critical pack hiện vẫn replay zero-miss.
- Commit/PR evidence-only không được hiểu là PASS, DONE hoặc cho phép merge.

## Blocker

**[M6-T03] BLOCKER**

- Problem: V02 expected `AUTO_REPLY/P05`, actual `ESCALATE/FACT_UNRESOLVED/P04` với audit `GROUNDEDNESS_FAILED`.
- Impact: AC4 FAIL; AC5 và AC6 không được tiếp tục tới kết luận; không đủ điều kiện làm PASS candidate hoặc merge. PR chỉ lưu evidence.
- Evidence: exact image `sha256:05678ee...`, raw `configured-verify-V02.json`, critical evidence 23/23 hits và 0 misses.
- Solution/Responsible: Coordinator mở/ủy quyền task production riêng để xử lý semantic normalization/groundedness; M6-T03 không được sửa business logic.
- Decision Needed: quyết định owner và scope cho production fix, sau đó rerun M6-T03 từ exact approved revision.
- Safe Work Continuing: Coordinator có thể review blocker report và raw evidence; không merge, không sửa cassette/expected result.

---

## POST-INTEGRATION FINAL VALIDATION

### Disposition hiện hành

- Authorization: Coordinator chấp nhận audit hai tầng cho AC6: R2 được ghi một
  diagnostic `CASE_ERROR`; pipeline ghi đúng một terminal `CASE_ERROR` có
  `rule_id=TECHNICAL_ERROR` khi case kết thúc `ERROR`.
- Result: **READY_FOR_COORDINATOR_REVIEW**.
- Historical evidence: toàn bộ V02 FAIL và AC6 FAIL/NOT RUN phía trên được giữ nguyên.
  Phần này là hậu kiểm sau remediation/integration, không sửa hoặc xóa raw FAIL.
- Production/runtime change trong M6-T03: **0**. Diff cuối chỉ gồm targeted test assertion
  và report này.
- LIVE/API/email: **0/0/0**.

### Revision và exact image

| Mốc | SHA / giá trị | Kết quả |
|---|---|---|
| Original tested baseline | `348058f9c7c0f9d81ab38870271b4260fadbb79f` | Historical blocker run phía trên |
| Original evidence commit | `92be4059c330e06a8c25c76e1b8630c3ef534700` | Historical report được bảo toàn |
| Integrated `origin/dev` | `e8f44c5b87a671916267aeede5bf10602016a6c2` | V02 remediation và safety integration |
| Image-tested merge SHA | `7801eabc5859fb4cb8cb049620d04bba79dde917` | Critical replay, Verify, reset/restart và reporting evidence |
| Final test/report SHA | PR #48 head sau commit cuối | Khác image-tested SHA chỉ ở test/report; xem PR head |
| Image tag | `exodia:m6-t03-7801eab` | Tồn tại cục bộ, được inspect lại |
| Image ID / RepoDigest | `sha256:34fb7d38e8464ff54a72756f29cf1864770fdb2c9eebfa208dd94182b0369940` | Khớp exact image đã báo cáo |

Docker build của exact image đã PASS trong lượt post-integration. Không rebuild sau khi chỉ
đổi assertion/report, để không tạo một image có runtime giống hệt nhưng digest khác.

### BASE24, replay và Verify

- Canonical BASE24 manifest:
  `reports/readiness/M6_T05_BASE24_RECORDED_PACK.json`.
- Manifest SHA-256:
  `2a3c80855923010e3ead807424bc1d2e904c01422ab08eade7655fe30aa280c8`.
- Cassette integrity kiểm lại từ canonical manifest: **24/24 hash khớp, 0 mismatch**;
  `integrity=PASS_24_OF_24`.
- Privacy: `PASS_AUTOMATED_SCAN`; raw SDK responses vẫn ở ignored quarantine.
- Critical product flows: **4/4 PASS** — Routine/P05, Authority/P01, Fact/P03,
  Out-of-policy/P02.
- Verify V01–V04: **4/4 PASS** sau V02 remediation; V02 hiện
  `AUTO_REPLY/P05` như expected.
- Runtime replay: **23 calls / 23 hits / 0 misses**, network guard bật,
  `live_provider_calls=0`.
- Evidence exact SHA:
  `data/validation/m6-t03/post-remediation-critical/M6_T05_REPLAY_EVIDENCE.json`
  và `M6_T05_REPLAY_MANIFEST.json` (local ignored evidence). Canonical provenance và
  acceptance status lấy từ tracked BASE24 manifest ở trên; runtime-observation manifest
  không thay thế canonical provenance record.

Không chạy lại 23-call replay trong lượt AC6 final vì production, cassette, config và image
không thay đổi; exact-image evidence trên vẫn khớp SHA `7801eab`.

### Reset/restart

Hai lượt DB synthetic độc lập (`run1`, `run2`) đều giữ nguyên sau restart:

| Kiểm tra | Run 1 | Run 2 |
|---|---:|---:|
| V01 `AUTO_REPLY/P05`, `PENDING_SEND` | PASS | PASS |
| V03 `ESCALATE/AUTHORITY_REQUIRED/P01`, `AWAITING_HUMAN` | PASS | PASS |
| Auto draft | 1 | 1 |
| Authority escalation | 1 | 1 |
| Forbidden side effects | 0 | 0 |

DB chỉ chứa synthetic inputs và nằm trong evidence directory riêng. Không dùng DB dev/study/demo.

### AC6 — diagnostic và terminal evidence

Hai regression lịch sử được chạy trước khi điều chỉnh assertion và tái hiện nguyên trạng:

```text
extract_timeout: FAIL — total CASE_ERROR actual 2, expected cũ 1
extract_schema:  FAIL — total CASE_ERROR actual 2, expected cũ 1
```

Đối chiếu từng row chứng minh expected cũ đang đếm gộp hai tầng audit:

| Scenario | R2 diagnostic `CASE_ERROR` (`rule_id IS NULL`) | Terminal `CASE_ERROR/TECHNICAL_ERROR` | Final status / decision | Classified completed | Send/approval/resolved |
|---|---:|---:|---|---:|---:|
| `extract_timeout` | 1, reason còn truy vết | 1 | `ERROR / ERROR` | 0 | 0 |
| `extract_schema` | 1, reason còn truy vết | 1 | `ERROR / ERROR` | 0 | 0 |

Targeted assertion nay phân biệt `rule_id IS NULL` và `TECHNICAL_ERROR`; không yêu cầu tổng
`CASE_ERROR=1`. Guard exception vẫn yêu cầu 0 diagnostic và đúng 1 terminal event. Test còn
xác minh không có `CASE_QUEUED`, `CASE_RESOLVED`, `HUMAN_DECISION`,
`HUMAN_APPROVED_SEND`, `SEND_SCHEDULED` hoặc `SEND_DISPATCHED`.
Scenario R2 missing-cassette dùng cùng invariant hai tầng; nhánh R11 vẫn giữ đúng một error
event vì case giữ `HUMAN_DECIDED` và không kết thúc ở trạng thái `ERROR`.

Reporting/telemetry dùng cùng tiêu chí hiện hành của `infra.telemetry.snapshot` và trang
Đo lường: chỉ `AUTO_REPLY`/`ESCALATE` thuộc classified denominator. Với R2 technical-error
scenario: `total_cases=1`, `classified_completed=0`, `technical_errors=1`,
`auto_rate=0.0`; diagnostic event không làm tăng completed automation. Evidence local:
`data/validation/m6-t03/post-remediation-reporting/technical-error-reporting.json`.

### Before/after và validation

Môi trường host validation: Windows, Python 3.11.9 trong `.venv`, pytest 8.3.3; pytest
network/provider guard luôn bật và DB tạo trong temporary directory riêng.

| Validation | Kết quả |
|---|---|
| Hai regression trước assertion update | **2 FAIL**, đúng historical total-count mismatch |
| Hai regression sau update | **2 PASS** |
| Full parameterized technical-error test + R2 diagnostics + extraction guards + telemetry | **26 PASS** |
| Full Human Control file + R2 diagnostics + extraction guards + telemetry | **39 PASS** |
| BASE24 cassette hash verification | **24/24 PASS**, 0 mismatch |
| Exact Docker image inspect | **PASS**, ID khớp `sha256:34fb7d...9940` |

Commands chính:

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests/test_m3_t06_human_control.py::test_technical_error_state_audit_and_display_are_consistent[extract_timeout] `
  tests/test_m3_t06_human_control.py::test_technical_error_state_audit_and_display_are_consistent[extract_schema] `
  -q -vv --tb=short

.\.venv\Scripts\python.exe -m pytest `
  tests/test_m3_t06_human_control.py::test_technical_error_state_audit_and_display_are_consistent `
  tests/test_r2_validation_diagnostics.py `
  tests/test_guards.py::test_extraction_schema_normalizes_for_openai_without_mutation `
  tests/test_guards.py::test_extract_retries_invalid_payload_once_then_records_error `
  tests/test_guards.py::test_extract_timeout_is_fail_safe_and_records_error `
  tests/test_telemetry.py -q --tb=short

docker image inspect exodia:m6-t03-7801eab `
  --format 'ID={{.Id}} REPO_DIGESTS={{json .RepoDigests}} CREATED={{.Created}}'
```

### AC1–AC7 final mapping

| AC | Trạng thái | Evidence |
|---|---|---|
| AC1 — Exact image | **PASS** | exact tag/ID, integrated SHA và config đã chốt |
| AC2 — Replay | **PASS** | 23/23 hits, 0 misses, network/LIVE=0 |
| AC3 — Critical flows | **PASS** | 4/4 business flows khớp expected |
| AC4 — Verify V01–V04 | **PASS** | 4/4 sau integrated V02 remediation |
| AC5 — Persistence/reset/restart | **PASS** | hai isolated runs có state/count giống nhau sau restart |
| AC6 — Reporting/audit | **PASS** | mỗi R2 error: diagnostic=1, terminal=1; ERROR/ERROR; completed=0; side effects=0 |
| AC7 — Evidence/handoff | **PASS** | historical FAIL giữ nguyên, final section, validation và PR handoff |

### Self-review, risks và rollback

- Full diff self-review: targeted test chỉ thay expected invariant; không sửa production,
  audit action, schema, policy, cassette hoặc expected Verify.
- Historical raw FAIL vẫn còn nguyên trong report và git history.
- Source/image risk được giới hạn: final commit khác `7801eab` chỉ ở test/report; runtime
  image không đổi. Nếu production thay đổi sau handoff, exact-image evidence phải chạy lại.
- Hai fingerprint khác recording time đã công khai (`core/worker.py`, recording helper);
  exact-image critical replay vẫn 23/23 hits.
- Rollback: revert commit test/report cuối; không có data/schema/runtime migration cần hoàn tác.
- Không sửa Trello, `STATUS.md`; không merge PR #48 và không tự tuyên bố DONE.

Owner self-review: **PASS — Project Coordinator handoff candidate**. Bước tiếp theo là
Coordinator review PR #48 trên final head và quyết định ACCEPT/merge.
