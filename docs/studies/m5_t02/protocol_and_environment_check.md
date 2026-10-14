# M5-T02 — Protocol và environment check

Đối chiếu tại `HEAD=2ce699c6a0d5b3d4ac6252a394468fb2aab329cd`.
Đây là kiểm tra readiness trên repository; không chạy Study runtime hoặc participant session.

## Protocol revision

Nguồn hiện hành: [M5-T01 protocol](../m5_t01/study_protocol.md),
[case pack](../m5_t01/cases_xy.md) và [measurement forms](../m5_t01/measurement_forms.md).

- Conditions: B0 xử lý thủ công với tài liệu; B2 dùng Exodia.
- Tổng cộng 8 email synthetic: X1–X4 và Y1–Y4; mỗi participant xử lý 4 B0 + 4 B2,
  không thấy cùng email ở cả hai conditions.
- X/Y allocation và thứ tự case giữ nguyên 1→4.

| Sequence | Condition đầu | Condition sau |
|---|---|---|
| S1 | B0-X | B2-Y |
| S2 | B2-Y | B0-X |
| S3 | B0-Y | B2-X |
| S4 | B2-X | B0-Y |

Với n=4, mỗi sequence một người. Với n=3, bốc thăm trước session để bỏ một sequence,
ghi allocation log và Coordinator xác nhận; không đổi allocation theo kết quả.

Form yêu cầu observation cho từng attempted case, condition summary, feedback sau
condition/cuối session và product-improvement trace. Primary time là
`end_at - start_at`; giữ pause/system wait, missing/interruption, final human decision,
AI initial route/action/edit và raw n/N riêng. Không chấm Gold trước sign-off; N=0 là NA.

Revision identifiers từ Git blob tại baseline:

| Artifact | Git blob | SHA-256 nội dung Git |
|---|---|---|
| `cases_xy.md` | `59276d1189b5fb1cc1856ab10b2c778b20b132be` | `ab0b9eda12dfa91f679c617a12d64f228cb3277db218da9c2fa998f3320ed7e1` |
| `study_protocol.md` | `538372d61ba5babe18b607026008b42b65173ec2` | `f00c3f31ddd6297ea193b8ddddabd8c654cf21446aa29df921114c96f39d75f6` |
| `measurement_forms.md` | `201a7fa9bd316c8154145a9c1fbe6e9e55535ebb` | `28a6ff91815983cd31c0c731a4d90de7937b04a20a65bebb2f1fdcf20d4b6007` |

## Corpus revision

Authoritative bytes được đọc từ `HEAD:data/seed_docs/*.json`. Kết quả: **5 ACTIVE,
1 SUPERSEDED**, tất cả `is_synthetic=true`.

| Source | Status | SHA-256 nội dung Git |
|---|---|---|
| HP-2026-1 | ACTIVE | `765a65530d7edc78ef004c984ca5514a08a3720f332b47216f031eebcc6243bd` |
| PK-2026-204 | ACTIVE | `5b24c84754a69e9fcb317589b8c0b2c3608ef26d40ceb1c3e48c454ca3d0a15d` |
| QDPQ-2026-01 | ACTIVE | `8809607390cd0b261e1a2648bc21c6dcdeb2ce6f852ff55e06cb4af261c59aac` |
| RH-2026-101 | ACTIVE | `7f2e3c2188a2613f95399324bb163c6e59ad279d0b0e5ff67bd587bf2d9b597e` |
| RL-2025-2363 | SUPERSEDED | `7b0f41bc63dc9558b95a3573b681d79f3ff7af255b49d51c6051cd6381995012` |
| RL-2026-3150 | ACTIVE | `fcfe0098e313bbf9a5c25e71bfdd08dae14e6ca27b0e4c27f77ae43dcca685f6` |

B0/B2 chỉ dùng cùng năm nguồn ACTIVE; nguồn SUPERSEDED chỉ ở reviewer archive.
Study DB `corpus_version` thực tế chưa được tạo/xác minh cho revision được chọn.

## Environment/readiness evidence

| Hạng mục | Evidence repository | Kết luận cho study hiện tại |
|---|---|---|
| Runtime mode | `compose.yaml` ép `LLM_MODE=replay`, cache off | Replay capability `PASS`; selected study mode `NOT VERIFIED` |
| DB separation | M6-T02 báo DEV/STUDY/DEMO dùng volume riêng, STUDY `/runtime/app.db` | Prior runtime evidence `PASS`; exact selected SHA/instance `NOT VERIFIED` |
| Isolation | M6-T02 chỉ chèn probe vào DEV và không thấy ở STUDY/DEMO | Prior reported evidence `PASS`; chưa rerun cho study candidate |
| Synthetic-only | 8 case và 6 seed đều được kiểm là synthetic | `PASS` cho artifact/corpus; participant session `NOT RUN` |
| Runtime safety | M6-T03 final: 23/23 replay hits, Verify 4/4, critical 4/4, LIVE=0 | `PASS` trong exact-image offline scope; current study SHA `NOT VERIFIED` |
| Human control | M3-T06/T07 và post-merge audit chấp nhận technical integration trong offline/replay scope | Study-specific applicability `NOT VERIFIED` |
| Stable Integration | Coordinator audit: technical integration accepted; M3 milestone vẫn `M3_AUTHORIZED_WITH_CARRYOVER` | `NOT VERIFIED` cho GO-STUDY |
| Restricted public demo | M6-T04 evidence áp dụng DEMO/replay, không phải STUDY | Không dùng làm study acceptance |

Không nâng documentation hoặc evidence trên SHA/môi trường khác thành runtime PASS cho
exact STUDY product. Exact product SHA, Study DB reference, corpus_version, mode/model,
isolation check và Coordinator disposition phải được pin trong session manifest trước GO.

## Kết quả AC4

`PASS` cho consistency của B0/B2, 8 case, X/Y, S1–S4, five-ACTIVE corpus và form
requirements trên repository hiện hành. Kết quả này không xác nhận Gold sign-off,
participant readiness, exact Study runtime hoặc GO-STUDY.
