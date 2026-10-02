# Exodia — attempt 2: full15 LIVE baseline actual — 2026-10-02

**Baseline: EVALUATED. PASS: 2/15. FAIL: 13/15. CURRENT CORE GATE: FAIL.**

Đây là một lượt full15 LIVE được thực thi đầy đủ. 13 case lỗi kỹ thuật ở R2 trước retrieval/policy; kết quả không chứng minh logic policy thất bại. Không fix, không rerun case hoặc suite, không commit/merge.

## Timeline và Git

- Attempt 1: NOT EVALUATED, bị chặn ở preflight. Báo cáo `baseline_full15_live_2026-10-02.md` giữ nguyên.
- Runtime bootstrap: READY cho environment/schema và đường đọc corpus/evidence không LLM.
- Attempt 2: một lượt full15 LIVE/cache-free, 15/15 cases hoàn tất.
- Repository: `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A`.
- Branch: `dev`; HEAD: `8c7638d4ccd0603e65e5187e3f36413c60a18331`.
- `git status --short` trước lượt chạy: rỗng; working tree sạch. Worktree OFF; không tạo branch.
- Không thay source, prompt, policy, retrieval, model, expected labels, matching, timeout hoặc retry.

## Preflight và exact command

- Python 3.11.9 trong `.venv-bootstrap`; google.genai import OK.
- GOOGLE_API_KEY: YES.
- GEMINI_MODEL override: NO. Resolved runtime model: `gemini-3.6-flash`, từ `infra.llm.DEFAULT_MODEL`.
- Trong chính session evaluation: LLM_MODE=live, LLM_CACHE=0, DATABASE_PATH=data/validation/manual-live.db.
- DB theo RUNBOOK: schema 2; 6 nguồn (5 ACTIVE, 1 SUPERSEDED), 72 chunks, 6 bản gốc; 60 candidates ACTIVE đều resolve được, foreign-key errors=0, cases trước run=0.
- DB chưa tồn tại lúc preflight đầu. Chỉ chạy canonical command `python -c "from corpus.seed import ensure_seeded; print(ensure_seeded())"`; output `SeedResult(seeded=False, document_count=0, chunk_count=0)`. Không viết SQL tay hoặc copy corpus. Readiness được xác minh sau command; không diễn giải seeded=False thành một lần nạp seed mới.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:LLM_MODE='live'
$env:LLM_CACHE='0'
$env:DATABASE_PATH='data/validation/manual-live.db'
.\.venv-bootstrap\Scripts\python.exe -m verify.harness --set full15 --output data/validation/full15_live_actual_2026-10-02.json
```

Stdout/stderr được redirect sang file evidence; stopwatch bao quanh đúng một lần gọi harness. Kiểm tra session trước harness xác nhận LIVE/cache=0 và model resolve, không gọi API.

Timeout giữ nguyên 30 giây/call attempt, giới hạn thêm bởi ngân sách còn lại. Case budget: 60 giây và tối đa 4 wrapper attempts, dùng chung qua các bước/retry. Wrapper retry lỗi tạm thời tối đa một lần; ClientError không nằm trong danh sách transient nên mỗi case thất bại có một wrapper attempt được log. SDK retry và các parse/regenerate retry hiện có giữ nguyên. Ngân sách LLM không phải cam kết tổng thời gian pipeline. Full15 không có giới hạn tổng 90 giây (giới hạn đó chỉ dành escalation5).

`infra.llm._run_mode()` với live/cache=0 bỏ `_load_cache()` và gọi `_call_live()` → `_request_gemini()` → `client.models.generate_content(model=model, ...)`. Không có cassette/replay fallback. DB sau run không có llm_cache records; log ghi 13 SDK ClientError ở lượt gọi thật. F01/F02 kết thúc trước LLM.

## Bảng đầy đủ 15 case

E1 = SDK `ClientError` tại R2_extract; wrapper trả thông báo chung về kết nối/cấu hình. Không có HTTP status/provider error body trong evidence. Loại lỗi chi tiết UNKNOWN.

| case_id | Expected decision | Expected escalation type | Expected rule_id | Actual decision | Actual escalation type | Actual rule_id | Harness | Latency ms | API/LLM error | P04 YES/NO |
|---|---|---|---|---|---|---|---|---:|---|---|
| V01 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 1514 | E1 | NO |
| V02 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 632 | E1 | NO |
| V03 | ESCALATE | AUTHORITY_REQUIRED | P01 | ERROR | — | TECHNICAL_ERROR | FAIL | 650 | E1 | NO |
| V04 | ESCALATE | OUT_OF_POLICY | P02 | ERROR | — | TECHNICAL_ERROR | FAIL | 642 | E1 | NO |
| E01 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 708 | E1 | NO |
| E02 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 663 | E1 | NO |
| E03 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 691 | E1 | NO |
| E04 | ESCALATE | FACT_UNRESOLVED | P03 | ERROR | — | TECHNICAL_ERROR | FAIL | 657 | E1 | NO |
| E05 | ESCALATE | AUTHORITY_REQUIRED | P01 | ERROR | — | TECHNICAL_ERROR | FAIL | 664 | E1 | NO |
| F01 | INVALID_INPUT | — | R0 | INVALID_INPUT | — | R0 | PASS | 97 | Không; không gọi LLM | NO |
| F02 | ESCALATE | OUT_OF_POLICY | R1 | ESCALATE | OUT_OF_POLICY | R1 | PASS | 125 | Không; không gọi LLM | NO |
| F03 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 652 | E1 | NO |
| F04 | ESCALATE | AUTHORITY_REQUIRED | P01 | ERROR | — | TECHNICAL_ERROR | FAIL | 665 | E1 | NO |
| F05 | ESCALATE | OUT_OF_POLICY | P02 | ERROR | — | TECHNICAL_ERROR | FAIL | 648 | E1 | NO |
| F06 | AUTO_REPLY | — | P05 | ERROR | — | TECHNICAL_ERROR | FAIL | 679 | E1 | NO |

## Summary

- PASS: 2/15; FAIL: 13/15; TECHNICAL_FAILURE: 13/15.
- Actual P01: 0; P02: 0; P03: 0; P04: 0.
- Actual TECHNICAL_ERROR: 13; R0: 1; R1: 1.
- API/LLM ClientError cases: 13; tất cả ở R2_extract.
- API timeout count xác nhận: 0; API quota/service error count xác nhận: 0; output parsing/schema failure count xác nhận: 0. Không có đủ provider detail để loại trừ hoặc chia nhỏ nguyên nhân 13 ClientError; quota/service/request-schema cause = UNKNOWN.
- Technical failures ngoài nhóm ClientError: 0 quan sát được.
- Harness elapsed: 9.707495 giây.
- Total process wall-clock: 10.3635665 giây, gồm khởi động/kết thúc interpreter.
- Median case latency: 657 ms; max: 1514 ms (V01).
- Process exit: 1 — harness hoàn tất và trả exit 1 do có FAIL.
- Runtime model resolved/passed theo code path: `gemini-3.6-flash`. Nguồn: runtime default, không override. Đường SDK đã được thực thi; model argument lấy trực tiếp từ biến resolved này. Không capture HTTP payload hoặc provider-confirmed model, nên không tuyên bố model observed độc lập từ network.
- Harness metadata ghi `model=gemini-3.5-flash-lite`: đây là fallback cosmetic trong `verify/harness.py`, KHÔNG phải bằng chứng runtime model. Giữ nguyên raw JSON, không sửa metadata.
- Corpus version của 15 results: `cv_f6eb04187bb0`. DB validation là corpus canonical riêng; không lấy version của DB legacy để mô tả lượt này.

## Three-stop evidence và Core Gate

| Điều kiện | Evidence | Kết quả |
|---|---|---|
| TECHNICAL_FAILURE <= 1/15 | 13/15 ERROR/TECHNICAL_ERROR | FAIL |
| >=1 correct FACT_UNRESOLVED/P03 PASS | E04 FAIL, actual ERROR/TECHNICAL_ERROR | FAIL |
| >=1 correct OUT_OF_POLICY/P02 PASS | V04 và F05 FAIL; F02 PASS bằng R1, không tính P02 | FAIL |
| >=1 correct AUTHORITY_REQUIRED/P01 PASS | V03, E05, F04 đều FAIL | FAIL |

**CURRENT CORE GATE: FAIL.** Nguyên nhân: 13 lỗi kỹ thuật và không có PASS đúng luật P01/P02/P03. Đây là kết quả gate của lượt thực thi, không suy ra lỗi logic policy từ các case chưa tới policy.

Không có actual P04 trong lượt này. Technical fail-safe hiện trả `TECHNICAL_ERROR`, không phải P04. E04 expected P03 nhưng actual TECHNICAL_ERROR: FAIL; không tính là bằng chứng FACT_UNRESOLVED. P04 cũng không được tính là P03.

## Mọi FAIL, rule mismatch và phân loại

Tất cả 13 FAIL đều mismatch expected rule với actual TECHNICAL_ERROR. Phân loại sơ bộ: **P04 / TECHNICAL (nhóm fail-safe kỹ thuật; actual rule là TECHNICAL_ERROR)**. Lỗi trực tiếp: SDK ClientError ở R2. Nguyên nhân gốc: **UNKNOWN**, không đủ evidence để quy cho policy/retrieval/inference/parsing hoặc một lỗi hạ tầng cụ thể.

| Case | Rule mismatch | Phân loại | Lỗi trực tiếp / nguyên nhân gốc |
|---|---|---|---|
| V01 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| V02 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| V03 | P01 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| V04 | P02 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| E01 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| E02 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| E03 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| E04 | P03 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| E05 | P01 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| F03 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| F04 | P01 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| F05 | P02 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |
| F06 | P05 → TECHNICAL_ERROR | P04 / TECHNICAL; actual TECHNICAL_ERROR | ClientError / UNKNOWN |

Thông báo wrapper/persisted extraction cho mọi case E1:

> Dịch vụ AI chưa xử lý được yêu cầu do kết nối hoặc cấu hình chưa phù hợp. Email được giữ lại, chưa gửi phản hồi. Hãy kiểm tra kết nối/cấu hình rồi thử lại.

## Raw evidence và integrity

- `data/validation/full15_live_actual_2026-10-02.json`; SHA256 `7179943a64b77b6c4f793d48e39e952980aba84ab25023521daeb0c93675aa66`.
- `data/validation/full15_live_actual_2026-10-02_stdout.txt`; SHA256 `d5447a5aba8d9879dbe6bae488a366e926c54ac7470cea57739657dd12dfd7f8`.
- `data/validation/full15_live_actual_2026-10-02_stderr.txt`; SHA256 `0127bf7eda1802f13217640e84bf887ead29cd1591b6de46f98d1cee8535a293`.
- `data/validation/full15_live_actual_2026-10-02_process.json`; SHA256 `4dd12b1158e21a4aa457f40894e8dc3333e28c3cd6a6f0b9ab7fac38d9dbe8d8`.
- `data/validation/full15_live_actual_2026-10-02_preflight.json`; SHA256 `3cb887132bdfab84ce99c9ce3d19f697b6e50412078ade505463f840db15c3c2`.
- Historical attempt-1 report SHA256 trước/sau: `31ca2e04f2e54c2f38c6b32d19908c6c85ee757a66c7abf48b0fd2bf7e47c4e9` — giữ nguyên.
- DB persisted snapshots: `data/validation/manual-live.db`, liên kết case_ref trong raw JSON.
- Audit VERIFY_RUN_STARTED/FINISHED: [{"action": "VERIFY_RUN_STARTED", "ts": "2026-10-02T09:57:46.611197Z", "reason": "Bắt đầu chạy Verify tuần tự qua pipeline dùng chung."}, {"action": "VERIFY_RUN_FINISHED", "ts": "2026-10-02T09:57:56.305389Z", "reason": "Đã chạy tuần tự 15/15 case Verify."}]

## Final Git

`git diff --stat`: rỗng; không thay tracked files.

`git status --short` sau tạo report:

```text
?? reports/baseline_full15_live_actual_2026-10-02.md
```

Report chưa commit; raw validation artifacts/DB thuộc đường dẫn đã gitignore. Đã STOP, không fix và không rerun.
