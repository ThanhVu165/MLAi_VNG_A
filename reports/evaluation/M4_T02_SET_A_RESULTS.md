# M4-T02 — Kết quả Official Post-Tuning Set A

- Task ID: `M4-T02`
- Owner: Minh — Evaluation/Logic
- Kết quả execution: **OFFICIAL_SET_A_RUN_COMPLETE**
- Quality mode: **DESCRIPTIVE**; không có post-hoc PASS threshold
- Official run ID: `M4-T02-OFFICIAL-b5229b31-4246-4c07-b532-3bb14b75d104`
- Máy chạy: `LAPTOP-FGVTPVC1`
- PR #60 frozen head: `b177a0eab7ffa6324a89f7061dd49092e7741abf`
- Runtime source SHA: `47a1fcd9686b5409674979b34a521ead2f65ae8d`
- Freeze manifest: [`M4_T02_FREEZE_MANIFEST.json`](../../docs/evaluation/M4_T02_FREEZE_MANIFEST.json), status `FROZEN`
- Freeze Completion Amendment: Trello action `6ad09d61dc90b3a61a7bd4e4`
- GO-A Attempt Budget Amendment: Trello action `6ad0a0b9a1a4026bcadf1b35`
- Started: `2026-10-15T16:52:33.451111+07:00`
- Ended: `2026-10-15T16:55:57.656804+07:00`
- Official run count: **1**
- Abort: **NO**
- Rerun: **NO**

## 1. Exact bindings và execution config

| Binding | Exact value | Verification |
|---|---|---|
| Set A | `M4-SET-A-POSTTUNE / v1`; 18 case | PASS |
| Set A SHA-256 | `98d691c8437f1c466a6c2b7be1cd4ca3c34f4e0a0218f02376c2ae4f4a414385` | PASS trên exact private bytes |
| Gold | `M4-SET-A-POSTTUNE-GOLD / v1` | PASS |
| Gold SHA-256 | `e6b7ea08c03c93d3b952f5166a1cfcd0ecb0423cdb2c9c5cb532110f024509f5` | PASS trên exact private bytes |
| Corpus | `M4-T02-CORPUS / v1`; DB ref `M4T02_EVAL_DB_V1` | PASS |
| Corpus SHA-256 | `03f1f7d346775200d2c9cecd94efeeb14a4de0f90047a62f9eba00de705d44fd` | PASS; 6 source, 5 ACTIVE, 1 SUPERSEDED, 72 chunks |
| Collector | `sha256:3bcff1577f2fde9e0716a3a75f77eba766244e5b916b4195dbcf52d9885c0d68` | PASS |
| Harness | `sha256:76e476eb33b1bb8e5fa13f64b5c1ad45f2eb68ea4113774c2f66a87555b2109e` | PASS |
| Provider/model | `openai / gpt-6-luna` | PASS |
| Parameters | `reasoning_effort=none`; `temperature=0`; cache disabled | PASS |
| Mode | isolated private `LIVE`; không gửi email thật | PASS |
| Timeout/deadline | 30 giây provider; 60 giây mỗi case | PASS |
| Processing attempt limits | tối đa 3/case, 54 toàn run | PASS: thực tế 52; max/case 3 |
| Resume/R11 provider execution | Không được phép | PASS: 0 attempt |

GO-A được consume tại provider request đầu tiên. Từ thời điểm đó run count giữ bằng 1;
không restart, best-of, tuning, đổi Gold hoặc chạy lần hai.

## 2. Normalized inventory — 18/18 planned IDs

`route/stop/rule` chỉ là đối chiếu sanitized sau execution; không công bố raw input,
Gold rationale hoặc provider payload.

| Case ID | Outcome | Actual route | Actual stop | Rule | Route | Stop | Rule | Latency ms |
|---|---|---|---|---|---|---|---|---:|
| M4A-PT-001 | VALID | AUTO_REPLY | — | P05 | PASS | N/A | PASS | 16992.989 |
| M4A-PT-002 | VALID | AUTO_REPLY | — | P05 | PASS | N/A | PASS | 14266.358 |
| M4A-PT-003 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | PASS | PASS | 9971.222 |
| M4A-PT-004 | TECHNICAL_ERROR | ERROR | — | TECHNICAL_ERROR | N/A | N/A | N/A | 13136.742 |
| M4A-PT-005 | TECHNICAL_ERROR | ERROR | — | TECHNICAL_ERROR | N/A | N/A | N/A | 13752.271 |
| M4A-PT-006 | TECHNICAL_ERROR | ERROR | — | TECHNICAL_ERROR | N/A | N/A | N/A | 13416.484 |
| M4A-PT-007 | VALID | ESCALATE | FACT_UNRESOLVED | P03 | PASS | PASS | PASS | 10121.709 |
| M4A-PT-008 | VALID | ESCALATE | FACT_UNRESOLVED | P03 | PASS | PASS | PASS | 12675.914 |
| M4A-PT-009 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | FAIL | FAIL | 12464.084 |
| M4A-PT-010 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | PASS | PASS | 6957.291 |
| M4A-PT-011 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | PASS | PASS | 10782.511 |
| M4A-PT-012 | VALID | AUTO_REPLY | — | P05 | FAIL | FAIL | FAIL | 12075.204 |
| M4A-PT-013 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | FAIL | FAIL | 7513.216 |
| M4A-PT-014 | VALID | ESCALATE | AUTHORITY_REQUIRED | P01 | PASS | PASS | PASS | 7875.018 |
| M4A-PT-015 | TECHNICAL_ERROR | ERROR | — | TECHNICAL_ERROR | N/A | N/A | N/A | 10674.150 |
| M4A-PT-016 | TECHNICAL_ERROR | ERROR | — | TECHNICAL_ERROR | N/A | N/A | N/A | 8406.311 |
| M4A-PT-017 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | FAIL | FAIL | 9972.324 |
| M4A-PT-018 | VALID | ESCALATE | OUT_OF_POLICY | P02 | PASS | FAIL | FAIL | 12876.143 |

Outcome totals: `VALID=13`, `TECHNICAL_ERROR=5`, `MALFORMED=0`,
`INVALID_INPUT=0`, `MISSING=0`, tổng `18`. Coverage gate yêu cầu 18 normalized rows và
`MISSING=0`: **PASS**. Năm technical failures là case-deadline exhaustion sau các
provider responses đã được ghi nhận; chúng không bị đổi thành business escalation.

## 3. Confusion và Gold-by-outcome

| Confusion | Count |
|---|---:|
| TP | 10 |
| FN | 1 |
| FP | 0 |
| TN | 2 |

`TP + FN + FP + TN = 13`, đúng bằng số valid business decisions.

| Gold route | AUTO_REPLY output | ESCALATE output | TECHNICAL_ERROR | Planned |
|---|---:|---:|---:|---:|
| AUTO_REPLY | 2 | 0 | 0 | 2 |
| ESCALATE | 1 | 10 | 5 | 16 |

## 4. Metrics — raw n/N và Wilson 95%

| Metric | Raw n/N | Rate | Wilson 95% |
|---|---:|---:|---:|
| MER | 1/11 | 9.09% | 1.62%–37.74% |
| OER | 0/2 | 0.00% | 0.00%–65.76% |
| Escalation precision | 10/10 | 100.00% | 72.25%–100.00% |
| Escalation recall | 10/11 | 90.91% | 62.26%–98.38% |
| Route correctness | 12/13 | 92.31% | 66.69%–98.63% |
| End-to-end route success | 12/18 | 66.67% | 43.75%–83.72% |
| Stop correctness | 6/11 | 54.55% | 28.01%–78.73% |
| Conditional stop correctness | 6/10 | 60.00% | 31.27%–83.18% |
| Rule correctness | 8/13 | 61.54% | 35.52%–82.29% |
| Decision coverage | 13/18 | 72.22% | 49.13%–87.50% |
| Technical failure | 5/18 | 27.78% | 12.50%–50.87% |
| Missingness | 0/18 | 0.00% | 0.00%–17.59% |
| Invalid-input rate | 0/18 | 0.00% | 0.00%–17.59% |

Missing-outcome bounds:

- Gold AUTO_REPLY: lower `0/2 = 0%`, upper `0/2 = 0%`.
- Gold ESCALATE: lower `1/16 = 6.25%`, upper `(1+5)/16 = 37.50%`.

Không diễn giải bất kỳ metric nào thành PASS/FAIL quality threshold.

## 5. Latency, attempts và cost evidence

- Latency count: `18`.
- Median latency: `10782.511 ms`.
- Nearest-rank p95: `16992.989 ms`.
- Full-run wall time: `204.243 s`.
- Processing provider attempts: `52`; max single case: `3`; limits `54 / 3`.
- Attempt outcomes: `52 SUCCESS`; exception/HTTP failures: `0`.
- Provider steps: R2 extraction `18`, R4 selection `15`, R7 generation `5`,
  R7 question generation `14`.
- Resume/R11 provider attempts: `0`.
- Provider usage evidence present: `52/52` attempts.
- Input tokens: `112418`; output tokens: `6860`; cached input tokens: `0`.
- Best-supported estimated API cost: `USD 0.0146718`, từ numeric provider usage và
  public Standard pricing quan sát cho GPT-6 Luna (`$0.10/M` input, `$0.01/M` cached
  input, `$0.50/M` output). Đây không phải invoice/billing ledger và runtime không có
  hard USD cap; status: `BEST_SUPPORTED_FROM_PROVIDER_USAGE`.

## 6. Validation

| Check | Result |
|---|---|
| Exact candidate/Gold/corpus hashes và bindings | PASS |
| Result schema validation | PASS |
| 18 planned-ID reconciliation | PASS |
| Duplicate/foreign ID check | PASS |
| Outcome totals = 18 | PASS |
| `TP+FN+FP+TN = valid business decisions` | PASS (`13=13`) |
| Metric arithmetic consistency | PASS |
| Wilson computation validation | PASS |
| Latency median/nearest-rank p95 validation | PASS |
| Provider attempt count ≤54 | PASS (`52`) |
| Max processing attempts/case ≤3 | PASS (`3`) |
| Resume/R11 attempts = 0 | PASS |
| Corpus unchanged after run | PASS |
| Secret/sanitized leak scan | PASS |
| `git diff --check` | PASS |

Hai setup checks trước provider đã fail-closed (system Python thiếu dependency; process
ban đầu rơi về restricted-demo). Cả hai đều có `official_run_count=0`, provider attempts
`0`, results `0`; evidence được giữ private. Chúng không phải official exposure hoặc rerun.

## 7. Limitations và evidence boundary

- Gold là **AI-adjudicated evaluation Gold** được Coordinator chấp nhận; không claim
  human-reviewed, blind-human hoặc independently human-adjudicated Gold.
- Gold strata: P01=7, P03=5, P02=4, P05=2, P04=0. Không có P04 Gold case.
- Gold AUTO_REPLY chỉ có `n=2`; OER interval vì vậy rất rộng.
- 10 Gold cases có reviewer confidence MEDIUM: 001, 005, 008, 009, 011, 012, 013,
  014, 017, 018.
- 5/18 case là technical failure; quality/business metrics trên valid population phải
  được đọc cùng decision coverage và end-to-end metric.
- M7 Set B vẫn là final independent held-out evidence.
- Sau exposure chính thức này, Set A có trạng thái **DEV_DIAGNOSTIC_AFTER_OFFICIAL_RUN**
  và không được mô tả lại là unseen independent evaluation evidence.

Raw candidate, Gold, receipts, provider outputs, logs và private absolute paths không vào
Git. Private evidence được giữ bằng opaque references dưới run ID, gồm state ledger,
provider-attempt ledger, raw pipeline results, normalized results và aggregate summary.
Không có real email send, tuning/adaptation, label change, best-of hoặc second official run.

**MERGE: NO.** PR #60 tiếp tục OPEN để Coordinator/MLAI review execution evidence và ra
final M4-T02 acceptance.
