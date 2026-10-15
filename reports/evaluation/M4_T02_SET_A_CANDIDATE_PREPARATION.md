# M4-T02 — Chuẩn bị Set A candidate input-only

- Task ID: `M4-T02`
- Owner/author: Minh — Evaluation/Logic
- Baseline `origin/dev`: `47a1fcd9686b5409674979b34a521ead2f65ae8d`
- Branch: `sprint/m4-t02-official-set-a`
- PR: `#60`
- Phân loại: **POST-TUNING INDEPENDENT EVALUATION SET A**
- Kết quả: **READY_FOR_INDEPENDENT_GOLD**
- Freeze status: **FREEZE_INCOMPLETE**
- Official Set A runs: **0**
- LIVE/API/provider/email: **0**

Báo cáo này chỉ xác nhận candidate input-only. Nó không claim pre-M2 held-out,
historical preregistration hoặc final sealed held-out; không chứa case text, Gold,
expected label, private path, secret hay PII.

## 1. Authority và storage

Coordinator cho phép preparation tại Trello action `6ad04dd2fb6c52f6121deaa4` và
phê duyệt controlled private storage tại action `6ad04fd528b7095d4152b4c1`.
Opaque reference được duyệt là `M4T02_PRIVATE_SET_A_STORE`.

Actual private directory đã được xác minh nằm ngoài repository và ngoài mọi Git
worktree. Raw candidate cùng provenance/access log chỉ nằm tại private store;
absolute path không được ghi vào Git hoặc Trello.

## 2. Candidate receipt

| Field | Giá trị |
|---|---|
| Identifier | `M4-SET-A-POSTTUNE` |
| Version | `v1` |
| Case count | `18` |
| Exact-byte SHA-256 | `98d691c8437f1c466a6c2b7be1cd4ca3c34f4e0a0218f02376c2ae4f4a414385` |
| Created UTC | `2026-10-15T04:01:59Z` |
| Finalized UTC | `2026-10-15T04:03:53Z` |
| Author | Minh — Evaluation/Logic |
| Authoring assistance | Authorized Codex task session |
| Private reference | `M4T02_PRIVATE_SET_A_STORE` |

Candidate là canonical UTF-8 JSON có newline cuối file. Hash được tính trên exact
final bytes; mọi thay đổi tiếp theo phải dùng version mới.

## 3. Authoring và coverage design

Count `18` được cố định trước khi viết case để bao phủ vừa đủ ba domain được project
hỗ trợ và các boundary bắt buộc trong timebox Gold review. Đây là coverage design,
không phải sample-size/acceptance gate.

| Nhóm thiết kế | Số case |
|---|---:|
| Routine informational | 3 |
| Authority boundary | 3 |
| Missing critical fact | 3 |
| Unsupported/conflicting evidence | 3 |
| Content-verification/guard | 2 |
| Multi-intent/precedence | 2 |
| Applicability/scope | 2 |
| **Tổng** | **18** |

Thiết kế có ba supported domains và các tình huống dự kiến tạo cả hai population
AUTO_REPLY/ESCALATE cùng P01–P04/P05 boundary. Không có mapping case → route/rule,
expected label, answer key hoặc rationale trong candidate hay public evidence; Gold
reviewer phải quyết định độc lập.

Case được viết tổng hợp từ requirements, policy boundary, M4 protocol và hiểu biết
domain công khai. DEV/regression, M5 study và M7 Set B không được dùng làm nguồn viết.
Không case nào được sửa theo output của Exodia/model.

## 4. Overlap và independence

Validation dùng offline deterministic comparison: Unicode NFKC + casefold cho exact,
`SequenceMatcher` cho fuzzy, token-trigram Jaccard cho near-template, sau đó review
family/scope. High-similarity threshold là `0.86`; template threshold là `0.65`.

| Corpus đối chiếu | Phạm vi | Kết quả | Max fuzzy / template |
|---|---:|---|---:|
| Candidate nội bộ | 18 cases | **PASS** | `0.4642 / 0.0143` |
| DEV/regression | 53 accessible inputs | **PASS** | `0.4459 / 0.0820` |
| M5 public study material | 573 eligible lines | **PASS** | `0.4345 / 0.0455` |
| M7 Set B input-only | 16 inputs | **PASS** | `0.4329 / 0.0543` |

Family/domain overlap với supported business scope là có chủ đích và không được coi
là contamination. Không có exact duplicate, high fuzzy match, near-template reuse
hoặc obvious scenario/entity copy. Với M7 chỉ mở đúng authorized input-only candidate
để so sánh; không mở Set B Gold, expected label hay reviewer worksheet và không đưa
Set B payload vào private Set A store.

## 5. Provenance và access history

- Creation method: synthetic input-only authoring, không dùng observed system failure.
- Sources used: project requirements, M4 protocol/schema, business-policy boundaries,
  supported-domain understanding.
- Sources explicitly not used: model/Exodia outputs, DEV/M5/Set B case text làm nguồn,
  Set A/Set B Gold, reviewer material và real personal data.
- `2026-10-15T04:01:59Z`: tạo candidate bởi Minh qua authorized Codex task session.
- `2026-10-15T04:03:53Z`: finalize exact bytes sau offline validation/overlap checks.
- Model execution: `NONE`; Gold access: `NONE`; Set B Gold access: `NONE`.
- Tuning/adaptation từ candidate: `0`; LIVE/API: `0`; official runs: `0`.

## 6. Validation và disposition

PASS: input-only schema, 18 unique namespace IDs, deterministic serialization/hash
reproduction, reserved synthetic sender domain, timezone-aware timestamps, PII scan,
internal duplicate/fuzzy/template checks, DEV/regression overlap, M5 public-study
overlap và Set B input-only overlap.

Public report/receipt được scan để bảo đảm không chứa case text, expected labels,
Gold, absolute private path, secret hoặc PII. Raw candidate không được stage/commit.

Candidate đủ điều kiện chuyển sang **independent Gold review**. Freeze vẫn
`FREEZE_INCOMPLETE`: Gold identity/version/hash/reviewer/binding, corpus/image
disposition và các Coordinator-approved numeric gates còn unresolved. GO-A vẫn
`NOT GRANTED`, `execution_authorized=false`, budget `0`; không được chạy Set A.
