# M5-T02 — Study readiness

**Status:** `READY_FOR_COORDINATOR_REVIEW`; **không phải GO-STUDY hoặc M5-T02 DONE**.
Participant thực tế: **0 confirmed / PENDING recruitment**. Study sessions: **0**.

## Baseline và phạm vi

- Task: `M5-T02 — Recruitment, Consent & Study Readiness`.
- Coordinator giữ Owner và quyền nghiệm thu.
- Branch: `sprint/m5-t02-study-readiness`.
- Baseline và working-tree HEAD: `2ce699c6a0d5b3d4ac6252a394468fb2aab329cd`.
- Dữ liệu task: chỉ synthetic; LIVE/API/email thật: `0`.
- Không chạy participant session, không mở Gold/Set A/Set B và không sửa production,
  corpus, policy, schema, results hoặc milestone status.

## Artifact

| File | Mục đích |
|---|---|
| [Recruitment tracker](recruitment_tracker.md) | Theo dõi P01–P04 bằng code, không chứa PII |
| [Consent và storage plan](consent_and_storage_plan.md) | Ranh giới consent/privacy và các quyết định chờ Coordinator |
| [Protocol và environment check](protocol_and_environment_check.md) | Đối chiếu B0/B2, 8 case, S1–S4, corpus và runtime evidence |
| [GO-STUDY unlock checklist](go_study_unlock_checklist.md) | Trạng thái READY/BLOCKED/NOT VERIFIED, không tự ban hành GO |
| [Readiness report](../../../reports/studies/M5_T02_STUDY_READINESS.md) | Phương pháp, AC matrix, validation, blocker và risk |

## Kết luận hiện tại

- Protocol/corpus/form: cấu trúc hiện hành đã được đối chiếu từ
  [M5-T01](../m5_t01/README.md); không suy ra Gold approval hoặc study acceptance.
- Environment: có evidence M6 offline/replay và tách volume DEV/STUDY/DEMO, nhưng
  exact STUDY product SHA, Study DB instance và isolation trên revision được chọn
  vẫn `NOT VERIFIED`.
- Recruitment/consent: chưa có participant, invitation, consent hoặc role/exposure
  screening thực tế. Coordinator đã phê duyệt storage/privacy plan; AC2 là
  `PASS candidate`, nhưng consent thực tế vẫn `NOT RUN`.
- AC3 chính thức: `NOT RUN / BLOCKED`; chỉ cơ chế screening đã được chuẩn bị.
- AC6 chính thức: `NOT VERIFIED / PENDING FINAL COMMIT AND PR`; evidence package
  đã sẵn sàng nhưng chưa có commit SHA, PR và validation trên committed SHA.
- GO-STUDY: `BLOCKED — PARTICIPANT/CONSENT AND OTHER VERIFIED ENTRY CONDITIONS PENDING`.

Project Coordinator là custodian. Private evidence dùng Google Drive PRIVATE với
`General access = Restricted`, tách `01_consent_contact`,
`02_eligibility_exposure` và `03_raw_study_results`. Public Git chỉ giữ template,
participant code, aggregate metrics, de-identified results và sanitized feedback.
Gold private tiếp tục theo boundary riêng.
