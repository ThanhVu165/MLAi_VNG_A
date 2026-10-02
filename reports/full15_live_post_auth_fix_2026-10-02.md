# full15 LIVE post-auth-fix regression — 2026-10-02

**PASS 4/15; FAIL 11/15. CURRENT CORE GATE: FAIL.**

Đây là POST-AUTH-FIX regression, không phải baseline ban đầu. Chạy đúng một lần qua existing `verify.harness.main`; không sửa harness/source/prompt/policy/retrieval/model/expected labels, không rerun case hoặc suite, không commit/merge. Existing application timeout/retry và SDK behavior được giữ nguyên.

## Runtime và DB

- Python **3.11.9**; google-genai **2.25.0**; GOOGLE_API_KEY Present=YES; fingerprint **62598f1de6df**.
- Trong chính child PowerShell của lượt chạy: `Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue`; project tự nạp `.env`; LLM_MODE=live, LLM_CACHE=0.
- Runtime Gemini model resolved/passed: **gemini-3.6-flash**. Raw harness metadata lần này cũng ghi cùng model. Không capture response model_version ở từng call của harness.
- DATABASE_PATH: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\manual-live.db`.
- Schema 2; 6 sources: 5 ACTIVE, 1 SUPERSEDED; 72 chunks; 6 bản gốc; 60 ACTIVE candidates, 60 resolve thành công; foreign-key errors=0.
- Corpus version: `cv_f6eb04187bb0`. DB đã sẵn sàng, không cần init/migration/seed. Không sửa corpus. Cases trước/sau: 15/30.
- Timeout 30s/attempt, ngân sách case 60s và tối đa 4 wrapper attempts, retry transient tối đa một lần theo application; không thay đổi.
- SDK cảnh báo đồng thời có GOOGLE_API_KEY/GEMINI_API_KEY và chọn GOOGLE_API_KEY; không in giá trị credential.

## Invocation và thời gian

Child PowerShell đặt LIVE/cache=0/DATABASE_PATH như RUNBOOK và gọi `.venv-bootstrap\Scripts\python.exe -B -`. Trong chính Python process này, preflight assert Python/SDK/key fingerprint/model/LIVE/cache/DB trước mọi Gemini call; sau đó gọi duy nhất:

```python
verify.harness.main(['--set', 'full15', '--output', 'data/validation/full15_live_post_auth_fix_2026-10-02.json'])
```

Existing harness và `process_case()` chạy nguyên trạng. Python runner chỉ kiểm tra runtime, lưu evidence, redirect stdout/stderr đã redact và đo thời gian; không monkeypatch application/SDK/harness.
- Bắt đầu: 2026-10-02T18:23:26.216005+07:00; kết thúc: 2026-10-02T18:26:16.728076+07:00.
- Harness elapsed: 170.513182s; wall bao quanh harness.main: 170.516726s.
- Total Python process wall-clock, gồm preflight/snapshot/khởi động/kết thúc: **171.514298s**.
- Harness return code=1 vì có FAIL; orchestration process exit=0 sau khi lưu evidence đầy đủ. Full15 không áp giới hạn 90s của escalation5.

## Bảng 15 case

Latency là elapsed_ms của existing harness. P04/TECHNICAL_ERROR ghi actual rule; không dùng technical fallback thay P03.

| case_id | Expected decision | Expected type | Expected rule | Actual decision | Actual type | Actual rule | PASS/FAIL | Latency ms | Technical error | P04 / TECHNICAL_ERROR |
|---|---|---|---|---|---|---|---|---:|---|---|
| V01 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 15488 | R4_select; ServerError | TECHNICAL_ERROR |
| V02 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 58197 | R7_generate; ServerError/ClientError | TECHNICAL_ERROR |
| V03 | ESCALATE | AUTHORITY_REQUIRED | P01 | ERROR | — | TECHNICAL_ERROR | FAIL | 27596 | R4_select; ServerError | TECHNICAL_ERROR |
| V04 | ESCALATE | OUT_OF_POLICY | P02 | ESCALATE | OUT_OF_POLICY | P02 | PASS | 13314 | — | — |
| E01 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 802 | R2_extract; ClientError | TECHNICAL_ERROR |
| E02 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 18446 | R4_select; ServerError | TECHNICAL_ERROR |
| E03 | AUTO_REPLY | — | P05 | AUTO_REPLY | — | P05 | PASS | 18624 | — | — |
| E04 | ESCALATE | FACT_UNRESOLVED | P03 | ERROR | — | TECHNICAL_ERROR | FAIL | 9819 | R4_select; ClientError | TECHNICAL_ERROR |
| E05 | ESCALATE | AUTHORITY_REQUIRED | P01 | ERROR | — | TECHNICAL_ERROR | FAIL | 895 | R2_extract; ClientError | TECHNICAL_ERROR |
| F01 | INVALID_INPUT | — | R0 | INVALID_INPUT | — | R0 | PASS | 125 | — | — |
| F02 | ESCALATE | OUT_OF_POLICY | R1 | ESCALATE | OUT_OF_POLICY | R1 | PASS | 155 | — | — |
| F03 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 861 | R2_extract; ClientError | TECHNICAL_ERROR |
| F04 | ESCALATE | AUTHORITY_REQUIRED | P01 | ERROR | — | TECHNICAL_ERROR | FAIL | 4515 | R2_extract; ServerError/ClientError | TECHNICAL_ERROR |
| F05 | ESCALATE | OUT_OF_POLICY | P02 | ERROR | — | TECHNICAL_ERROR | FAIL | 833 | R2_extract; ClientError | TECHNICAL_ERROR |
| F06 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 826 | R2_extract; ClientError | TECHNICAL_ERROR |

## Summary

- PASS **4/15**; FAIL **11/15**; TECHNICAL_FAILURE **11/15**.
- Actual rule counts: P01=0; P02=1; P03=0; P04=0; TECHNICAL_ERROR=11; P05=1; R0=1; R1=1.
- API error affected cases=11. Final failed LLM calls: ServerError=3 (V01/V03/E02), ClientError=8 (V02/E01/E04/E05/F03/F04/F05/F06).
- Wrapper exception logs, kể cả transient attempts đã retry: ServerError=9, ClientError=8, total=17. Đây không phải số HTTP requests ở mức SDK.
- Timeout exception count xác nhận=0; output/schema parse errors quan sát được=0. Không suy timeout từ latency; HTTP status/provider details không được existing wrapper lưu nên chưa thể chia nhỏ nguyên nhân ServerError/ClientError, quota/auth/service exact reason=UNKNOWN.
- Median latency **4515 ms**; max **58197 ms** (V02); wall **171.514298s**.
- So với baseline 2 PASS / 13 FAIL, lượt post-auth-fix có 4 PASS / 11 FAIL; baseline giữ nguyên. Một lần chạy này không đủ kết luận nguyên nhân gốc hoặc độ ổn định dài hạn.

## Three-stop evidence và Core Gate

| Điều kiện | Evidence | PASS/FAIL |
|---|---|---|
| TECHNICAL_FAILURE <=1/15 | 11/15 | FAIL |
| >=1 correct-rule FACT_UNRESOLVED / P03 PASS | 0; E04 actual ERROR / TECHNICAL_ERROR | FAIL |
| >=1 correct-rule OUT_OF_POLICY / P02 PASS | V04: ESCALATE / OUT_OF_POLICY / P02, harness PASS; card có question/options | PASS |
| >=1 correct-rule AUTHORITY_REQUIRED / P01 PASS | 0; V03/E05/F04 actual ERROR / TECHNICAL_ERROR | FAIL |

**CURRENT CORE GATE: FAIL.** F02 OUT_OF_POLICY/R1 PASS không tính P02. E04 TECHNICAL_ERROR không tính P03. Actual P04=0; P04 nếu có cũng không tính thay P03. E03 AUTO_REPLY/P05 PASS, citation PK-2026-204:seed:2 ACTIVE, grounded=true.

## Danh sách FAIL và phân loại sơ bộ

Mọi FAIL có evidence trực tiếp là lỗi SDK tại LLM step, dẫn tới actual ERROR/TECHNICAL_ERROR. Phân loại **TECHNICAL**; nguyên nhân gốc **UNKNOWN**. Chưa đủ HTTP/provider evidence để kết luận INFRASTRUCTURE, auth/quota, hoặc POLICY/LOGIC, RETRIEVAL/EVIDENCE, LLM INFERENCE/PARSING. V03 có một ServerError transient tại R2 nhưng R2 sau retry thành công; V02 có một ServerError tại R4 nhưng R4 sau retry thành công; lỗi cuối tương ứng ở R4 và R7.

| Case | Expected rule → Actual rule | Bước lỗi cuối | Exception logs của case | Phân loại | Nguyên nhân gốc |
|---|---|---|---|---|---|
| V01 | P05 → TECHNICAL_ERROR | R4_select | attempt 1: ServerError, attempt 2: ServerError | TECHNICAL | UNKNOWN |
| V02 | P05 → TECHNICAL_ERROR | R7_generate | attempt 1: ServerError, attempt 1: ClientError | TECHNICAL | UNKNOWN |
| V03 | P01 → TECHNICAL_ERROR | R4_select | attempt 1: ServerError, attempt 1: ServerError, attempt 2: ServerError | TECHNICAL | UNKNOWN |
| E01 | P05 → TECHNICAL_ERROR | R2_extract | attempt 1: ClientError | TECHNICAL | UNKNOWN |
| E02 | P05 → TECHNICAL_ERROR | R4_select | attempt 1: ServerError, attempt 2: ServerError | TECHNICAL | UNKNOWN |
| E04 | P03 → TECHNICAL_ERROR | R4_select | attempt 1: ClientError | TECHNICAL | UNKNOWN |
| E05 | P01 → TECHNICAL_ERROR | R2_extract | attempt 1: ClientError | TECHNICAL | UNKNOWN |
| F03 | P05 → TECHNICAL_ERROR | R2_extract | attempt 1: ClientError | TECHNICAL | UNKNOWN |
| F04 | P01 → TECHNICAL_ERROR | R2_extract | attempt 1: ServerError, attempt 2: ClientError | TECHNICAL | UNKNOWN |
| F05 | P02 → TECHNICAL_ERROR | R2_extract | attempt 1: ClientError | TECHNICAL | UNKNOWN |
| F06 | P05 → TECHNICAL_ERROR | R2_extract | attempt 1: ClientError | TECHNICAL | UNKNOWN |

HTTP status/provider status/message body chi tiết=UNKNOWN vì wrapper chỉ log exception class và lưu thông báo fail-safe; không thay wrapper để bổ sung instrumentation. Persisted reason và audit nguyên văn có trong `_case_evidence.json`.

## Evidence và integrity

- HEAD: `8c7638d4ccd0603e65e5187e3f36413c60a18331`.
- Hai báo cáo baseline và mọi raw artifact `full15_live_actual_2026-10-02*` được kiểm tra SHA256 trước/sau: giữ nguyên.
- Snapshot toàn bộ validation DB trước run: `data\validation\full15_live_post_auth_fix_2026-10-02_before.db` (SQLite Backup API, gồm WAL nhất quán). Baseline case_results vẫn giữ nguyên trong DB hiện tại; 15 case mới được append.
- Corpus tables sources/chunks/source_contents/corpus_versions hash trước/sau bằng nhau: `f0ccc86bf0117aa623dcc6904b5dd5396e992c69152f28cdbe14373e6749688b`.
- Tất cả tracked files tồn tại trước run giữ nguyên hash. Thay đổi .env.example/.env.example.txt đã tồn tại trước task, không động vào. Raw artifacts dưới data/validation đã gitignore.

Artifact SHA256:

- `data\validation\full15_live_post_auth_fix_2026-10-02.json`: `2b1b3f550e7cf9112977bfb8f521a7bbe07378e48286ef75826f1e0470ba1ac4`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_before.db`: `2d48cd1a4a42605cd706e33c02bb24f503d142a84b594836563900018722ebd6`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_before.db-shm`: `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_before.db-wal`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_case_evidence.json`: `d68cd45a1aa57b6f082ba0c91b30545a909f4c35c443f8c364eaa7f277997b2b`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_preflight.json`: `c12d240e7f53190b784a217a77bd22b5024719957d55118190323fa2c1d29eec`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_process.json`: `00f69a8f41e06ce945ac42cada683a1459e0b085c54546890450f19447558f8b`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_shell_process.json`: `268c1f1d676dfafe712bf1142a4d9e7ceb533eae44d2ce261799ae5e79280054`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_stderr.txt`: `8abc51667390252dd8ec573865bc430119294cc90cbc6f565c6eae764a2a120e`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_stdout.txt`: `5b1c904c944280887c1e060e62119e64e13a776aabaaac461552a1f888aa0760`.
- `data\validation\full15_live_post_auth_fix_2026-10-02_summary.json`: `f3a3e9f2ce42113e81b38c42d04969ab18ee2ed69dabb03d6e333002dfadaf6d`.

Baseline protected SHA256:

- `data\validation\full15_live_actual_2026-10-02.json`: `7179943a64b77b6c4f793d48e39e952980aba84ab25023521daeb0c93675aa66`.
- `data\validation\full15_live_actual_2026-10-02_preflight.json`: `3cb887132bdfab84ce99c9ce3d19f697b6e50412078ade505463f840db15c3c2`.
- `data\validation\full15_live_actual_2026-10-02_process.json`: `4dd12b1158e21a4aa457f40894e8dc3333e28c3cd6a6f0b9ab7fac38d9dbe8d8`.
- `data\validation\full15_live_actual_2026-10-02_stderr.txt`: `0127bf7eda1802f13217640e84bf887ead29cd1591b6de46f98d1cee8535a293`.
- `data\validation\full15_live_actual_2026-10-02_stdout.txt`: `d5447a5aba8d9879dbe6bae488a366e926c54ac7470cea57739657dd12dfd7f8`.
- `reports\baseline_full15_live_2026-10-02.md`: `31ca2e04f2e54c2f38c6b32d19908c6c85ee757a66c7abf48b0fd2bf7e47c4e9`.
- `reports\baseline_full15_live_actual_2026-10-02.md`: `9e33cef9b22e9a8b83a11f406b94cc54c4172eb5cc8a8cacffaba9495de99e48`.

## Final Git

`git diff --stat`:

```text
 .env.example | 5 -----
 1 file changed, 5 deletions(-)
```

`git status --short`:

```text
 D .env.example
?? .env.example.txt
?? reports/baseline_full15_live_actual_2026-10-02.md
?? reports/full15_live_post_auth_fix_2026-10-02.md
```

Đã STOP. Không fix/retry/rerun/commit/merge.
