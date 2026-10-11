# Sprint 2 — Evidence reconciliation — 12/10/2026

## Authorization, scope và kết quả

Coordinator authorization từ yêu cầu trực tiếp:

> Đã phê duyệt thực hiện. Đây là công việc bổ sung tài liệu lịch sử, không yêu cầu Trello card hoặc Task ID mới.

> Mục tiêu: Bảo đảm các task Sprint 2 đã thực hiện và bàn giao có báo cáo `.md` trong repository, với bằng chứng thật và trạng thái chính xác.

Scope được giao: audit Git/Trello/PR/commits/handoff, giữ nguyên report đầy đủ, chỉ bổ sung report có nguồn thật, self-review/link/Markdown/sensitive-data validation và commit/push/Draft PR nhắm dev. Không sửa code/tests/fixture/STATUS/PROJECT_SPEC/roadmap, không đụng PR #40, không merge hoặc đổi DONE/gate. Không tạo card/ID/worktree/clone/backup phụ.

**Result: READY_FOR_COORDINATOR_REVIEW.** 26 mục lịch sử được đối chiếu: **11 mục có report**, giữ nguyên; **11 report bổ sung** (8 từ PR, 3 static audits từ Trello); **3 mục chưa đủ evidence**, không tạo completion report; **1 mục excluded** PR #40. M1.1–M1.6 dùng cùng living report; đếm task/mục, không đếm 11 file cũ khác nhau. Các package cardless giữ tên lịch sử, không bịa Task ID. Nhiều mục có report vẫn có từng phần NOT VERIFIED; 3 là số mục không đủ evidence để tạo report mới, không phải tổng mọi gap trong dự án.

## Repository preflight

- Remote: `https://github.com/ThanhVu165/MLAi_VNG_A.git`, đúng repository được giao.
- Checkout đầu phiên: `codex/coordinator-workflow-docs`, HEAD `5f8017ddc1461e7b4e7a21cee9b9c98d55501ad6`.
- `git fetch origin dev` thành công: origin/dev từ 73e23f9 đến **ed9d053e337dbd49314870eef4157f1fe27ca2ad**; direct `git ls-remote origin refs/heads/dev` khớp.
- Branch mới: `codex/sprint2-evidence-reconciliation`, tạo trực tiếp từ verified origin/dev; không worktree/clone/backup.
- Tracked worktree sạch trước đổi branch. Có 10 untracked SQLite WAL/SHM của ba nhóm m16a/m16b/m16c từ trước; giữ nguyên, không mở/xóa/stage.
- PR list đủ 41 PR trong repository (limit 60), và danh sách base dev (limit 100) đủ 18 PR #24–#41. PR #41 MERGED; #40 OPEN/base dev, không đọc diff/chỉnh sửa. #24–#39 đã MERGED. Metadata không chứng minh gate hoặc full human acceptance.
- Đọc AGENT.md và docs/TEAM_WORKFLOW.md hiện hành ở baseline; khảo sát toàn bộ tracked Markdown qua rg --files, đọc reports/handoff liên quan. Existing reports không đổi byte.

## Phương pháp và mức bằng chứng

Nguồn task: [EXODIA - Sprint 2 — MLAI](https://trello.com/b/sAFTCfVj/exodia-sprint-2-mlai). list_by_board filter=all, 21 cards, 7 lists, hasNextPage=false; gồm template/overview và duplicate legacy M3-T02 yXOgGnNk trong Backlog. Card M3-T02 có evidence được audit là ShqO507C; không gộp/sửa duplicate. Không sao chép nguyên board hoặc private payload vào Git.

Đọc đầy đủ comments của **9 cards**: TEAM-ONBOARDING, M3-T01, T02, T03, T04, T05, M5-T01, M6-T01 và COORD-T01. Đọc activity của cả **8 Done cards**; từng response hasNextPage=false. Không biến complete=false/due.complete=false thành task chưa Done; trạng thái list và các hành động Coordinator được ghi riêng.

GitHub CLI body/metadata/comments/reviews/files và git log/show/ls-tree là evidence integration/source. Report mới dẫn PR body hoặc comment ID cụ thể. **Reported historical validation** là kết quả nguồn đã ghi, không phải rerun hoặc raw logs đã kiểm tại reconciliation. Source corroboration mới chỉ đọc Git blobs của M3-T03/M6-T01/M3-T05; không import app/LLM/DB. Không mở Gold private, Set A/B, secrets hoặc PII; không sao chép study cases/Gold/participant records.

## Bảng theo Task ID / historical work

| Task / work | Owner và provenance | Trạng thái nghiệm thu xác minh | PR / SHA | Report .md | Evidence / giới hạn |
|---|---|---|---|---|---|
| M1.1 | Owner NOT VERIFIED; không suy từ PR author | Repository ghi DONE; M1 PASS/CLOSED, Coordinator-attested theo living report | [PR #24](https://github.com/ThanhVu165/MLAi_VNG_A/pull/24); [efc0dac](https://github.com/ThanhVu165/MLAi_VNG_A/commit/efc0dac70aa4ccef073e849e195a43093ea52433) (PR checkpoint chung) | CÓ — [M1 living report](M1_runtime_reliability.md) | Đủ báo cáo chung; Owner/review độc lập và local raw logs từng task NOT VERIFIED trong audit này |
| M1.2 | Owner NOT VERIFIED; không suy từ PR author | Repository ghi DONE; M1 PASS/CLOSED, Coordinator-attested theo living report | [PR #24](https://github.com/ThanhVu165/MLAi_VNG_A/pull/24); [efc0dac](https://github.com/ThanhVu165/MLAi_VNG_A/commit/efc0dac70aa4ccef073e849e195a43093ea52433) (PR checkpoint chung) | CÓ — [M1 living report](M1_runtime_reliability.md) | Đủ báo cáo chung; Owner/review độc lập và local raw logs từng task NOT VERIFIED trong audit này |
| M1.3 | Owner NOT VERIFIED; không suy từ PR author | Repository ghi DONE; M1 PASS/CLOSED, Coordinator-attested theo living report | [PR #24](https://github.com/ThanhVu165/MLAi_VNG_A/pull/24); [efc0dac](https://github.com/ThanhVu165/MLAi_VNG_A/commit/efc0dac70aa4ccef073e849e195a43093ea52433) (PR checkpoint chung) | CÓ — [M1 living report](M1_runtime_reliability.md) | Đủ báo cáo chung; Owner/review độc lập và local raw logs từng task NOT VERIFIED trong audit này |
| M1.4 | Owner NOT VERIFIED; không suy từ PR author | Repository ghi DONE; M1 PASS/CLOSED, Coordinator-attested theo living report | [PR #24](https://github.com/ThanhVu165/MLAi_VNG_A/pull/24); [efc0dac](https://github.com/ThanhVu165/MLAi_VNG_A/commit/efc0dac70aa4ccef073e849e195a43093ea52433) (PR checkpoint chung) | CÓ — [M1 living report](M1_runtime_reliability.md) | Đủ báo cáo chung; Owner/review độc lập và local raw logs từng task NOT VERIFIED trong audit này |
| M1.5 | Owner NOT VERIFIED; không suy từ PR author | Repository ghi DONE; M1 PASS/CLOSED, Coordinator-attested theo living report | [PR #24](https://github.com/ThanhVu165/MLAi_VNG_A/pull/24); [efc0dac](https://github.com/ThanhVu165/MLAi_VNG_A/commit/efc0dac70aa4ccef073e849e195a43093ea52433) (PR checkpoint chung) | CÓ — [M1 living report](M1_runtime_reliability.md) | Đủ báo cáo chung; Owner/review độc lập và local raw logs từng task NOT VERIFIED trong audit này |
| M1.6 | Owner NOT VERIFIED; không suy từ PR author | Repository ghi DONE; M1 PASS/CLOSED, Coordinator-attested theo living report | [PR #24](https://github.com/ThanhVu165/MLAi_VNG_A/pull/24); [efc0dac](https://github.com/ThanhVu165/MLAi_VNG_A/commit/efc0dac70aa4ccef073e849e195a43093ea52433) (PR checkpoint chung) | CÓ — [M1 living report](M1_runtime_reliability.md) | Đủ báo cáo chung; Owner/review độc lập và local raw logs từng task NOT VERIFIED trong audit này |
| M2.2 | Owner NOT VERIFIED | Historical targeted/canonical observations; không M2_PASS | [PR #25](https://github.com/ThanhVu165/MLAi_VNG_A/pull/25); [124b06d](https://github.com/ThanhVu165/MLAi_VNG_A/commit/124b06d6b36b7af5f3c822faa459e34a0a0ac020) | CÓ — [M2 report](M2_core_decision_escalation_quality.md) | Evidence trong report; ignored raw LIVE logs không kiểm ở lượt này |
| M2 package / closeout (cardless, không gán ID) | Owner NOT VERIFIED | M2_CONDITIONAL_CLOSEOUT theo TEAM_HANDOFF; không PASS | [PR #25](https://github.com/ThanhVu165/MLAi_VNG_A/pull/25), [PR #26](https://github.com/ThanhVu165/MLAi_VNG_A/pull/26); [32fd88a](https://github.com/ThanhVu165/MLAi_VNG_A/commit/32fd88a9c7a50e47a959580fb90f803912554542) | CÓ — [Final closeout](M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md), [progress](M2_goal_progress.md) | Đủ báo cáo chung; 6/12 DEV coverage, historical failures/RR, fallback/identifier LIVE gaps giữ nguyên |
| [TEAM-ONBOARDING](https://trello.com/c/1hdsXCm7) | Bốn thành viên; Coordinator nghiệm thu | Coordinator move Done xác minh; bốn confirmations NOT VERIFIED | [PR #27](https://github.com/ThanhVu165/MLAi_VNG_A/pull/27); [baa198a](https://github.com/ThanhVu165/MLAi_VNG_A/commit/baa198a90c5791ed5dd13f671cf17664e865e448) (docs hỗ trợ, không thay onboarding) | CHƯA — không tạo báo cáo hoàn tất onboarding | NOT VERIFIED: comments chỉ có quy trình/request, không đủ bốn confirmations; không suy PR docs chứng minh onboarding |
| DOC-T01 — Đồng bộ kế hoạch | Project Coordinator; PR author AIVIETNAM-AIO-MinhThuw | MERGED xác minh; acceptance chi tiết NOT VERIFIED | [PR #28](https://github.com/ThanhVu165/MLAi_VNG_A/pull/28); [ce9096a](https://github.com/ThanhVu165/MLAi_VNG_A/commit/ce9096a7604ddd6803710590c39e39d799fc8bb0) | BỔ SUNG — [report](DOC_T01_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| Cardless — Four-attempt LLM budget | Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw | MERGED xác minh; acceptance chi tiết NOT VERIFIED | [PR #29](https://github.com/ThanhVu165/MLAi_VNG_A/pull/29); [717457a](https://github.com/ThanhVu165/MLAi_VNG_A/commit/717457a037ce736eca75e706fd7ebf4bf4afb9fb) | BỔ SUNG — [report](LLM_BUDGET_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| M3-T01 — Approval safety regression | Vũ; reviewer Nam | Coordinator move Done xác minh; historical 2 FAIL | [PR #31](https://github.com/ThanhVu165/MLAi_VNG_A/pull/31); [c7f7ba4](https://github.com/ThanhVu165/MLAi_VNG_A/commit/c7f7ba490b5a33d349b7cff66469ac27e343bd00) | BỔ SUNG — [report](M3_T01_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| M3-FIX-01 — Stale approval preview | Project Coordinator theo PR body | MERGED xác minh; acceptance chi tiết NOT VERIFIED | [PR #35](https://github.com/ThanhVu165/MLAi_VNG_A/pull/35); [311aa14](https://github.com/ThanhVu165/MLAi_VNG_A/commit/311aa14a14117a49d38fa15e054fac4f1a1130ff) | BỔ SUNG — [report](M3_FIX_01_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| M3-FIX-02 — Persistence fail-closed / P04 | Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw | MERGED xác minh; acceptance chi tiết NOT VERIFIED | [PR #36](https://github.com/ThanhVu165/MLAi_VNG_A/pull/36); [7d5005f](https://github.com/ThanhVu165/MLAi_VNG_A/commit/7d5005f1e4a69bc24c733fba8f94eb9f81e64200) | BỔ SUNG — [report](M3_FIX_02_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| M3-FIX-03 — Atomic controls/correction | Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw | MERGED; Coordinator acceptance reported trong PR | [PR #37](https://github.com/ThanhVu165/MLAi_VNG_A/pull/37); [07e6cae](https://github.com/ThanhVu165/MLAi_VNG_A/commit/07e6cae5ee8a84c6a29e010e426baa3c93449130) | BỔ SUNG — [report](M3_FIX_03_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| Cardless — UI baseline integration | Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw | MERGED xác minh; acceptance chi tiết NOT VERIFIED | [PR #38](https://github.com/ThanhVu165/MLAi_VNG_A/pull/38); [8c80b8b](https://github.com/ThanhVu165/MLAi_VNG_A/commit/8c80b8b080c2661145e604adb782485980bf0f38) | BỔ SUNG — [report](UI_BASELINE_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| Cardless — Repository cleanup Phase 1 | Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw | MERGED xác minh; acceptance chi tiết NOT VERIFIED | [PR #39](https://github.com/ThanhVu165/MLAi_VNG_A/pull/39); [4753e41](https://github.com/ThanhVu165/MLAi_VNG_A/commit/4753e41bdb273d00a254d394df3e26af7333b0da) | BỔ SUNG — [report](REPOSITORY_CLEANUP_PHASE1_HISTORY_REPORT.md) | Đủ để lưu historical summary; validation theo PR body, raw logs không kiểm lại; xem giới hạn trong report |
| [M3-T02](https://trello.com/c/ShqO507C) | Minh | Coordinator move Done xác minh; STOP research, không adaptation implementation | [PR #34](https://github.com/ThanhVu165/MLAi_VNG_A/pull/34); [2b254df](https://github.com/ThanhVu165/MLAi_VNG_A/commit/2b254dff4581c97db8b5795131cd75603880675a) | CÓ — [Feasibility report](M3_T02_FEASIBILITY_REPORT.md) | CÓ review Vũ-confirmed, GitHub COMMENTED; AC3/4 DESIGN ONLY; Minh human self-review NOT VERIFIED. Giữ nguyên report snapshot |
| [M3-T03 — Environment isolation static audit](https://trello.com/c/ZxfyUkU6) | Nam | Coordinator move Done xác minh; handoff kỹ thuật partial/pending | READ_ONLY; không implementation PR/commit; source baseline trong report | BỔ SUNG — [report](M3_T03_HISTORY_REPORT.md) | Đủ evidence static để đóng gói; runtime/human review/acceptance rationale NOT VERIFIED |
| [M6-T01 — Deployment/replay readiness static audit](https://trello.com/c/DSIUsD0p) | Nam | Coordinator move Done xác minh; handoff kỹ thuật partial/pending | READ_ONLY; không implementation PR/commit; source baseline trong report | BỔ SUNG — [report](M6_T01_HISTORY_REPORT.md) | Đủ evidence static để đóng gói; runtime/human review/acceptance rationale NOT VERIFIED |
| [M3-T05 — Feedback/audit source evidence](https://trello.com/c/X4uwlHfE) | Minh | Coordinator move Done xác minh; handoff kỹ thuật partial/pending | READ_ONLY; không implementation PR/commit; source baseline trong report | BỔ SUNG — [report](M3_T05_HISTORY_REPORT.md) | Đủ evidence static để đóng gói; runtime/human review/acceptance rationale NOT VERIFIED |
| [M3-T04](https://trello.com/c/8vStdeob) | Vũ | Coordinator move Done xác minh; latest technical handoff audit NOT_STARTED | Remote preflight 16f584fa213416db30b247a431b92fffb94be075; không implementation PR | CHƯA — không tạo audit results report | NOT VERIFIED: chỉ preflight/blocker, thiếu source matrix/runtime findings; không dùng PR31 hoặc T02 làm kết quả T04 |
| [M5-T01](https://trello.com/c/nSzHYb2a) | Thư / Project Coordinator theo card | Coordinator move Done xác minh; decision riêng yêu cầu reviewer sign-off trước full acceptance | [PR #30](https://github.com/ThanhVu165/MLAi_VNG_A/pull/30), [PR #32](https://github.com/ThanhVu165/MLAi_VNG_A/pull/32), [PR #33](https://github.com/ThanhVu165/MLAi_VNG_A/pull/33); [c305961](https://github.com/ThanhVu165/MLAi_VNG_A/commit/c305961c850c91672ed8478c38f8686d12d5339e) | CÓ — [Owner handoff](../../docs/studies/m5_t01/owner_handoff.md), [validation](../../docs/studies/m5_t01/validation_report.md) | NOT VERIFIED full acceptance: comment 6acb76103ddc6d8a288798ff nói không dùng list placement thay sign-off; study/runtime/participants chưa validated |
| [COORD-T01](https://trello.com/c/zxKGaEnG) | Project Coordinator | IN PROGRESS; handoff NOT VERIFIED | Baseline field PENDING_VERIFIED_DEV_SHA; không PR được liên kết | CHƯA — không tạo report task chưa bàn giao | NOT VERIFIED: chỉ contract/role comment, thiếu dependency map và handoff |
| [COORD-T02](https://trello.com/c/dp1ZZ86a) | Project Coordinator theo card | IN REVIEW; PR #40 OPEN | [PR #40](https://github.com/ThanhVu165/MLAi_VNG_A/pull/40) | KHÔNG RÀ SOÁT diff/report của PR #40 | EXCLUDED theo authorization: chỉ đọc metadata trạng thái trong PR list/board; không sửa PR/branch/file của Phase 2 |
| Coordinator workflow update (cardless) | Project Coordinator | PR #41 MERGED; historical report lúc Draft giữ nguyên | [PR #41](https://github.com/ThanhVu165/MLAi_VNG_A/pull/41); [5f8017d](https://github.com/ThanhVu165/MLAi_VNG_A/commit/5f8017ddc1461e7b4e7a21cee9b9c98d55501ad6) | CÓ — [workflow evidence](../../docs/COORDINATOR_WORKFLOW_UPDATE_20261012.md) | Đủ report docs; không sửa historical handoff Draft thành trạng thái mới |

## Coordinator status actions được xác minh

Dates dưới đây là UTC như API trả; giờ Việt Nam = UTC+07. Mỗi action là move của **card**, không phải review verdict. Latest Done moves do Coordinator Minh Thuw thực hiện; không tạo move mới trong reconciliation.

| Card | Date UTC | Actor | Action ID |
|---|---|---|---|
| [[TEAM-ONBOARDING] Thống nhất quy trình làm việc Sprint 2](https://trello.com/c/1hdsXCm7) | 2026-10-11T10:37:48.814Z | Minh Thuw | `6acb66fcea44f897df0cb2c2` |
| [M3-T05: Rà soát Feedback và Audit Evidence](https://trello.com/c/X4uwlHfE) | 2026-10-11T16:22:59.441Z | Minh Thuw | `6acbb7e36516a1e801e9823d` |
| [[M5-T01] Chuẩn bị nghiên cứu người dùng thực tế B0/B2](https://trello.com/c/nSzHYb2a) | 2026-10-11T16:22:58.335Z | Minh Thuw | `6acbb7e2605e6482c32b9a83` |
| [[M3-T02] Khảo sát khả thi cơ chế thích nghi từ phản hồi](https://trello.com/c/ShqO507C) | 2026-10-11T16:22:56.605Z | Minh Thuw | `6acbb7e04b53033c6ef2def9` |
| [M3-T04: Audit luồng Escalation và Ground Guard](https://trello.com/c/8vStdeob) | 2026-10-11T16:22:57.489Z | Minh Thuw | `6acbb7e1b134d8ea5a5c732d` |
| [[M3-T01] Kiểm thử an toàn cơ chế phê duyệt](https://trello.com/c/69HYW10S) | 2026-10-11T16:22:55.693Z | Minh Thuw | `6acbb7dfdd1cc366169c059b` |
| [[M3-T03] Kiểm tra cách ly môi trường DEV / Study / Demo](https://trello.com/c/ZxfyUkU6) | 2026-10-11T16:22:54.486Z | Minh Thuw | `6acbb7de5ad81d51111c97dc` |
| [[M6-T01] Audit Docker, Fresh Clone và Verify Replay](https://trello.com/c/DSIUsD0p) | 2026-10-11T16:22:53.472Z | Minh Thuw | `6acbb7ddfc23849a0dbafc0e` |

**Acceptance gaps không được tự giải quyết:**

- M3-T04: latest handoff [6acb5f0e46ee29d88c83488f](https://trello.com/c/8vStdeob#comment-6acb5f0e46ee29d88c83488f) nói audit NOT_STARTED. Chỉ lưu NOT VERIFIED; không dựng source findings/results report.
- M3-T02: [Vũ-confirmed review](https://trello.com/c/ShqO507C#comment-6acb92455669d876ffc42144) và [GitHub COMMENTED review](https://github.com/ThanhVu165/MLAi_VNG_A/pull/34#pullrequestreview-5483520382) xác minh AC1/2 PASS, AC3/4 DESIGN ONLY; Minh human self-review còn pending. Không ghi lại independent review là chưa tồn tại, không coi COMMENTED là APPROVE hoặc toàn bộ AC đạt.
- M5-T01: [Coordinator decision](https://trello.com/c/nSzHYb2a#comment-6acb76103ddc6d8a288798ff) nói rõ Done placement không thay independent sign-off; approval PR33 có điều kiện, actual study/runtime/participants chưa validated. Giữ report cũ, ghi **NOT VERIFIED full acceptance**; không dựng sign-off/Gold review mới.
- M3-T03/M6-T01: static handoff thật có thể lưu lại, nhưng runtime isolation/replay/fresh clone không chứng minh; historical BLOCKED không được coi là current card status.
- M3-T05: source audit mới hơn preflight tồn tại nhưng ghi NOT OWNER SIGN-OFF. Report mới giữ rõ source-only và pending human review.

## Thông tin cần Owner / Coordinator bổ sung

| Người xử lý | Mục | Evidence còn thiếu / quyết định cần ghi |
|---|---|---|
| Bốn thành viên và Coordinator | TEAM-ONBOARDING | Bốn comment xác nhận cá nhân hoặc explicit accepted exception; liên kết rationale sau lịch sử Done→Backlog→Done. PR27 docs không thay confirmations. |
| Vũ / Coordinator | M3-T01 | Formal handoff về card69HYW10S, giải thích Task Contract URL Ik4fEVHU trong PR31; Nam review evidence nếu đã có; scope acceptance tests có known FAIL. |
| Minh / Coordinator | M3-T02 | Human Owner self-review thật và scope STOP acceptance; Vũ confirmation đã có, không yêu cầu dựng lại. |
| Nam / Vũ / Coordinator | M3-T03, M6-T01 | Confirm baseline/card link; self-review/reviewer evidence; phân biệt accepted static findings với runtime gaps. Runtime follow-up cần scope riêng. |
| Vũ / Coordinator | M3-T04 | Xác nhận có audit chính thức sau preflight không; nếu có, cung cấp source matrix/baseline/findings/report; nếu chưa, ghi disposition của Done card. |
| Minh / Nam / Coordinator | M3-T05 | Owner handoff/self-review và independent verdict cho source matrix; disposition các gaps sau PR35/37, không suy code existence thành learner. |
| Thư / Minh / Coordinator | M5-T01 | Independent sign-off trên final diff/8-of-8 evidence theo decision, hoặc liên kết record có thật; không đưa Gold/PII vào Git. Không unlock study tự động. |
| Coordinator | COORD-T01 | Dependency map/kế hoạch/handoff có evidence; chưa tạo report khi chỉ có contract. |
| Coordinator / PR authors | DOC-T01, budget fix, M3-FIX-01–03, UI integration, cleanup Phase1 | Owner/authorization/acceptance references ngoài PR nếu có; raw logs safe hoặc disposition nếu cần certify reported validation. PR37 đã báo direct acceptance/review exception, không gán human-review PASS. |
| Coordinator | M1/M2 history | Owner từng task và reviewer/raw artifact access nếu cần mức xác minh sâu hơn; không yêu cầu rerun LIVE hoặc thay gate. |

Không gửi message cho Owner/Trello/GitHub comments trong lượt này; đây là danh sách follow-up, không nhận trách nhiệm thay Owner.

## Validation và sensitive-data self-review

Targeted documentation checks **PASS**: 12 Markdown files UTF-8/NFC, table column widths, heading/fence structure, **35 relative links**, **3 pinned blob links**, **28 commit links/ancestry** qua local Git objects và scoped secret/private-path patterns. Comment IDs/review links được đối chiếu API responses. Exact added-only Markdown scope và staged whitespace được kiểm trước commit; không claim HTTP crawl mọi external link hoặc raw runtime artifacts.

Không pytest hình thức, không chạy runtime/tests/app/DB/seed/reset/deploy. Code/tests/fixture/STATUS/PROJECT_SPEC/roadmap và report cũ không đổi; không Graph/board mutation, không gate/DONE update. No Gold/private study data/raw emails/credentials được thêm; chỉ dùng tên vai trò ngắn và nguồn công khai/task links. Risk chính là reports có kết quả **reported**, raw logs ngoài Git và acceptance details không truy cập được; merge/move không xóa gap.

## LIVE/API ledger và bàn giao

Application/provider/LLM/email LIVE calls thực tế: **0**. Network evidence access có thật; không claim zero network. Trello reads gồm 1 search_boards, 1 list_by_board, 9 list_comments, 8 list_activity = **19 connector calls**; không writes. GitHub CLI: 3 pr-list invocations; commit/push/Draft-create/read-back theo authorization được ghi kết quả cuối ở PR và handoff. Git HTTPS fetch/ls-remote/push không phải application LIVE. Không đếm HTTP requests nội bộ CLI/pagination/retries vì chưa instrument.

Branch: `codex/sprint2-evidence-reconciliation`; baseline `ed9d053e337dbd49314870eef4157f1fe27ca2ad`. Commit và Draft PR number sẽ do output Git/GitHub xác định, dẫn trong PR/handoff để tránh tự tham chiếu SHA. Coordinator review required; không merge, không tự DONE hoặc milestone/gate PASS.
