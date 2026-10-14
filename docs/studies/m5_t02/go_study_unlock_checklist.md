# M5-T02 — GO-STUDY unlock checklist

Checklist chỉ mô tả entry conditions. Nó không tự ban hành GO-STUDY.

| Entry condition | Status | Evidence / blocker |
|---|---|---|
| M5-T02 participant count >=3 | BLOCKED | `0 confirmed / PENDING recruitment` |
| Consent status | BLOCKED | Storage/privacy plan đã duyệt; consent participant thực tế vẫn `NOT RUN` |
| Exposure/eligibility screening mechanism | READY | `PASS — screening mechanism/process prepared` |
| Exposure/eligibility screening thực tế | BLOCKED | `NOT RUN — 0 participants confirmed`; AC3 chính thức chưa đạt |
| Private storage approval | READY | Project Coordinator; Google Drive PRIVATE Restricted; ba thư mục tách biệt; retention/deletion đã duyệt |
| Private storage configuration proof | NOT VERIFIED | Chưa xác minh thư mục/quyền thực tế trước recruitment |
| Exact STUDY product SHA | NOT VERIFIED | Task baseline không tự trở thành runtime SHA được chọn |
| Study DB/environment | NOT VERIFIED | Prior M6 separation evidence có, instance/path/corpus_version hiện hành chưa pin và rerun |
| Synthetic corpus revision | READY | 5 ACTIVE + 1 SUPERSEDED; six Git-byte SHA-256 đã kiểm |
| B0/B2 protocol revision | READY | 8 case, X/Y và S1–S4 khớp M5-T01 hiện hành |
| Gold/independent sign-off | NOT VERIFIED | Coordinator post-merge audit giữ M5-T01 `HOLD — SIGN-OFF NOT VERIFIED` |
| Runtime safety evidence | NOT VERIFIED | Offline exact-image evidence PASS ở SHA cũ; selected Study SHA chưa xác minh |
| STUDY isolation evidence | NOT VERIFIED | M6-T02 evidence không thay check trên exact Study candidate |
| Stable Integration disposition | NOT VERIFIED | Technical integration accepted trong scope offline/replay; study gate chưa được ban hành |
| LIVE/replay mode | NOT VERIFIED | Compose có replay; Coordinator chưa pin mode/model cho study; LIVE không được phép |
| Stable case/corpus/form manifest | READY | Revision IDs và hashes ghi trong environment check |
| Evidence package readiness | READY | Baseline/methods/validation/risk/privacy boundary đã đủ |
| Final commit/PR evidence | NOT VERIFIED | Chưa có commit SHA, PR hoặc validation trên committed SHA; AC6 chính thức chưa đạt |
| Coordinator GO-STUDY decision | BLOCKED | Chưa có decision; checklist không có quyền tự GO |

## Unlock rule

Chỉ Coordinator có thể chuyển sang `READY` sau khi mọi `BLOCKED`/`NOT VERIFIED` được
đóng bằng evidence trên exact revision và môi trường được chọn. LIVE cần authorization
riêng về provider, run/case, budget và stop conditions; mặc định hiện tại là không gọi.

## Current decision

`BLOCKED — PARTICIPANT/CONSENT AND OTHER VERIFIED ENTRY CONDITIONS PENDING`

Blocker trực tiếp: participant count 0, consent và exposure screening thực tế chưa chạy,
private storage configuration chưa được kiểm chứng, Gold sign-off chưa verified, exact
Study product/environment/mode/isolation chưa pin và Coordinator chưa ban hành GO-STUDY.
