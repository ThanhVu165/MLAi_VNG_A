# M2 Final Closeout Report & M1 + M2 Check-in Preparation

Ngày: 09/10/2026 (Asia/Saigon). Tác giả: Codex. **RESULT: CLOSEOUT_REPORT_READY.**
**RECOMMENDED VERDICT: M2_CONDITIONAL_CLOSEOUT**, chờ Coordinator quyết định; không phải M2_PASS tuyệt đối hoặc chứng nhận hoàn thành toàn bộ yêu cầu BTC.

## 1. Executive Summary

M2 có positive evidence cho bốn nhóm: P01/AUTHORITY_REQUIRED (A1, A2), P02/OUT_OF_POLICY (B3, A4/Probe 08), P03/FACT_UNRESOLVED (B1), P05/AUTO_REPLY hoàn tất đến PENDING_SEND (B4/Probe 09). Hai blocker của Final Gate trước đã có correction checkpoint và regression offline: numeric identifier handling và fallback handoff. Routine completion đã được quan sát LIVE sau correction; fallback mới chưa được LIVE exercise.

Giữ nguyên lịch sử Probe 02 semantic FAIL, Probe 03 R2 technical failure và Probe 05 numeric-guard rejection. Chín observations có bảy technical completions, trong đó một original semantic FAIL; hai technical failures. Sáu original run verdicts vẫn REVIEW_REQUIRED. Không biến routing đúng hoặc pytest xanh thành full semantic PASS.

Narrative adjudication gần nhất cho Probe 01–08: **95 criterion records = 68 PASS / 5 FAIL / 22 REVIEW_REQUIRED**. Probe 09 thêm tám records vẫn REVIEW_REQUIRED, thành **103 records = 68 PASS / 5 FAIL / 30 REVIEW_REQUIRED** khi trình bày chung narrative cũ với records mới chưa adjudicate. Tất cả 103 criterion records trong assessments gốc vẫn REVIEW_REQUIRED, không có formal review bundle mới. Đây không phải tỷ lệ accuracy.

Không phát hiện bằng chứng mới về một mandatory defect còn tồn tại ở final source sau hai correction. Đề xuất conditional dựa trên bằng chứng offline trực tiếp cho handoff và positive LIVE routine completion, không đổi mandatory handoff thành optional. Các giới hạn LIVE branch coverage, semantic adjudication và generalization phải đi cùng quyết định closeout. Nếu Coordinator yêu cầu full semantic certification thì evidence hiện tại chưa đủ.

## 2. Baseline & Evidence Provenance

| Thành phần | Baseline đã đối chiếu |
|---|---|
| Repository / branch | MLAi_VNG_A / sprint/m2-core-decision-escalation-quality |
| HEAD | 32fd88a9c7a50e47a959580fb90f803912554542 |
| Frozen fixture | [cases_m2_combined_dev.json](../../verify/cases_m2_combined_dev.json) |
| Fixture SHA-256 | d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04 |
| Ledger | [M2_live_budget.json](M2_live_budget.json): 45 total, 12 consumed, 33 remaining |
| Accounting scope | 3 reconciled baseline observations + 9 Probe observations; provider attempts không debit thành observations mới |
| Provider của tranche | OpenAI / gpt-6-luna; không claim so sánh ưu thế provider |
| Data | Synthetic DEV corpus; exposed cases, không phải held-out test set |

Nguồn ưu tiên: frozen Gold/rubric và captures/assessments gốc ở §3; [PROJECT_SPEC §5](../../PROJECT_SPEC.md#L85); [BTC Track A brief](../../Challenge_Brief_OrganizationAI_VN%20%281%29.md#L39); [roadmap M2 exit gate](../../docs/SPRINT_ROADMAP.md#L273); [criterion mapping](../../verify/m2_dev_rubric.py); [assessment contract](../../verify/M2_DEV_ASSESSMENT.md).

Nguồn adjudication ngoài repository được giữ theo identifier: `M2_PACKAGE1_SEMANTIC_REVIEW_EXIT_SCOPE_a4824be` (Package 1), `M2_FINAL_GATE_ff5c567_20261009` (Final Gate), và `M2_EVIDENCE_EXIT_GATE_AUDIT_a4824be` (evidence/exit audit). Package 1/Final Gate là narrative assessments của Codex, không được tự nhận là independent human adjudication. Final Gate M2_NOT_READY tại ff5c567 là kết luận lịch sử hợp lệ ở snapshot đó; báo cáo này không sửa nó.

Đã đọc trực tiếp chín captures và assessments; canonical JSON SHA-256 của cả **9/9 captures** khớp assessment.capture_sha256. Đã kiểm lại 95 dòng criterion trong bảng chi tiết Final Gate, không chỉ chép số tổng. Các independent REVIEW_PASS cho diagnostics/numeric/fallback là quyết định do Coordinator xác nhận trong các authorization hiện có; không có standalone Anti review artifact được xác lập tại task này. Không invent reviewer identity hoặc rerun review.

Regression 500 tests cho numeric fix và 512 tests cho fallback fix có kết quả từ các implementation sessions đã hoàn thành; 512 PASS/36.18s và targeted 93 PASS đã quan sát trong tool output của phiên trước, staged hashes đã đối chiếu trước checkpoint. Không có log regression riêng được tạo thêm trong báo cáo này. Checkpoint retention được Coordinator xác nhận 202 PASS; không coi đó là run mới của task closeout.

## 3. LIVE Probe 01–09 Results

| Probe / Case | Actual final route / status | Original verdict giữ nguyên | Evidence / disposition | Artifacts |
|---|---|---|---|---|
| 01 / M2DEV-A1 | ESCALATE/P01/AUTHORITY_REQUIRED; AWAITING_HUMAN | REVIEW_REQUIRED | P01 đúng; fallback options chung, basis quote rỗng. | Run `m2_dev_live_probe_01`; `data/validation/m2_dev_live_probe_01/cases/M2DEV-A1/` (local evidence — not published) |
| 02 / M2DEV-A4 | ESCALATE/P01/AUTHORITY_REQUIRED; AWAITING_HUMAN | FAIL | Gold P02/OUT_OF_POLICY; actual P01/AUTHORITY_REQUIRED — historical semantic FAIL. | Run `m2_dev_live_probe_02`; `data/validation/m2_dev_live_probe_02/cases/M2DEV-A4/` (local evidence — not published) |
| 03 / M2DEV-A4 | ERROR/TECHNICAL_ERROR/—; ERROR | TECHNICAL_ERROR | R2 domain validation thất bại sau 2 logical calls; không có card/draft. | Run `m2_dev_live_probe_03`; `data/validation/m2_dev_live_probe_03/cases/M2DEV-A4/` (local evidence — not published) |
| 04 / M2DEV-B1 | ESCALATE/P03/FACT_UNRESOLVED; AWAITING_HUMAN | REVIEW_REQUIRED | P03 đúng cho thiếu dữ kiện áp dụng; question/options usability còn RR. | Run `m2_dev_live_probe_04`; `data/validation/m2_dev_live_probe_04/cases/M2DEV-B1/` (local evidence — not published) |
| 05 / M2DEV-B4 | ERROR/TECHNICAL_ERROR/—; ERROR | TECHNICAL_ERROR | R6 P05 đúng nhưng R8 reason number → final ERROR; INT301 trong body bị nhận nhầm. | Run `m2_dev_live_probe_05`; `data/validation/m2_dev_live_probe_05/cases/M2DEV-B4/` (local evidence — not published) |
| 06 / M2DEV-B3 | ESCALATE/P02/OUT_OF_POLICY; AWAITING_HUMAN | REVIEW_REQUIRED | P02 đúng; giữ conflict 60%/70%, không chọn nguồn thắng. | Run `m2_dev_live_probe_06`; `data/validation/m2_dev_live_probe_06/cases/M2DEV-B3/` (local evidence — not published) |
| 07 / M2DEV-A2 | ESCALATE/P01/AUTHORITY_REQUIRED; AWAITING_HUMAN | REVIEW_REQUIRED | P01 đúng; repair chạm attempt budget, fallback mất caveat minh chứng chưa gửi. | Run `m2_dev_live_probe_07`; `data/validation/m2_dev_live_probe_07/cases/M2DEV-A2/` (local evidence — not published) |
| 08 / M2DEV-A4 | ESCALATE/P02/OUT_OF_POLICY; AWAITING_HUMAN | REVIEW_REQUIRED | A4 sau correction: P02/OUT_OF_POLICY đúng; FINDING-04 VERIFIED_LIVE trong observation này. | Run `m2_dev_live_probe_08`; `data/validation/m2_dev_live_probe_08/cases/M2DEV-A4/` (local evidence — not published) |
| 09 / M2DEV-B4 | AUTO_REPLY/P05/—; PENDING_SEND | REVIEW_REQUIRED | AUTO_REPLY/P05/PENDING_SEND, grounded=true; INT301 chỉ ở subject nên correction branch INCONCLUSIVE. | Run `m2_dev_live_probe_09`; `data/validation/m2_dev_live_probe_09/cases/M2DEV-B4/` (local evidence — not published) |

Gold B4 là AUTO_REPLY/P05, expected_type=null; PENDING_SEND là status consistency của đường AUTO_REPLY. Không gọi PENDING_SEND là thư đã gửi thật.

Phân biệt lần quan sát đầu và correction verification:
- Sáu unique cases xuất hiện đầu tiên ở P1/P2/P4/P5/P6/P7: bốn correct final routes, một wrong route (P2), một technical failure (P5).
- P3 là planned A4 verification sau correction nhưng technical failure; P8 là verification A4 sau diagnostics checkpoint; P9 là B4 correction verification. Không chọn best-of để xóa kết quả đầu.
- Tính toàn bộ chín observations: sáu correct completed final routes, một wrong completed route và hai technical failures. Các số này mô tả protocol lịch sử nhiều revisions, không phải final-HEAD accuracy estimate.
- Chỉ Probe 09 chạy tại final HEAD 32fd88a; không claim cả bốn gold groups đã được LIVE rerun tại final HEAD.

## 4. Decision & Escalation Quality

| Nhóm | Positive evidence | Kết luận có giới hạn |
|---|---|---|
| P01 / AUTHORITY_REQUIRED | P1 A1, P7 A2: ESCALATE, AWAITING_HUMAN | Authority priority đúng; historical handoff content có defect, được sửa offline sau P7 |
| P02 / OUT_OF_POLICY | P6 B3, P8 A4 | Relevant conflict/no authoritative answer được chuyển đúng; P8 phân biệt informational appeal procedure với appeal action |
| P03 / FACT_UNRESOLVED | P4 B1 | Thiếu dữ kiện áp dụng, không suy tuần học từ timestamp/hearsay; không dùng P04/ERROR để chứng minh P03 |
| P05 / AUTO_REPLY | P9 B4 | Grounded draft đến PENDING_SEND, card=null; không escalate chỉ vì input nhắc conflict hoàn phí |

Ở P9: R2 tạo một informational request; asks_appeal/asks_exception/asks_authority_decision/requires_personal_record đều false. R3 audit PREPOLICY_LOCKED ghi không cần khóa tự động; R5 evidence.status=ok và failed_checks=[]; R6 P05; draft.grounded=true, guard_failures=[].

Các corrections cuối không đổi policy priority, routing hay R2 flags. Evidence chuyển tiếp ở snapshots trước được kết hợp với regression offline final snapshot, không giả đó là cùng một run.

## 5. Semantic Assessment

### Denominator và coverage

Frozen fixture có **134 criterion texts / 12 cases**, gồm 44 pass criteria, 43 fail signals và 47 forbidden assumptions; mapping có 208 criterion–dimension slots. Đó không phải 134 observations hoặc 208 criteria bổ sung.

Sáu cases A1/A2/A4/B1/B3/B4 bao phủ **67/134 unique criterion identities**. A4 xuất hiện ba lần và B4 hai lần, nên chín observations tạo **103 criterion records**, không tăng unique-case coverage. Sáu cases chưa quan sát trong tranche: A3, B2, C1, C2, C3, C4; 67 criterion identities còn lại là UNOBSERVED, không tự gán PASS hoặc gọi là RR records đã tạo.

| Nguồn / trạng thái review | PASS | FAIL | REVIEW_REQUIRED | Tổng |
|---|---:|---:|---:|---:|
| Narrative Final Gate P1–P8, đã kiểm 95 dòng | 68 | 5 | 22 | 95 |
| P9 assessment, chưa adjudicate | 0 | 0 | 8 | 8 |
| Roll-up narrative + P9 chưa adjudicate | 68 | 5 | 30 | 103 |
| Assessments gốc P1–P9, không sửa | 0 | 0 | 103 | 103 |

Package 1 từng có 40 records (P1–P3) và 7 RR dimension records; đó là subset lịch sử, không cộng vào 95 hoặc 103. Một criterion có thể cần nhiều dimensions. Narrow criterion PASS không chứng minh toàn dimension options/question/grounding PASS.

Năm narrative FAIL lịch sử: P2 pass_criteria:0 và fail_signals:1 (wrong route); P3 pass_criteria:0 (không có required result vì technical failure); P5 pass_criteria:0 (routine completion fail); P7 pass_criteria:3 (delivered card bỏ caveat minh chứng). Không xóa hoặc reassess chúng bằng code mới.

### Probe 09 — evidence mới, không nâng verdict

P9 draft.body nêu đúng “17 giờ 00 thứ Sáu của tuần học thứ 8”, citation RH-2026-101:seed:5; nơi gửi là cổng dịch vụ sinh viên, citation RH-2026-101:seed:3. Selected chunks chứa trực tiếp hai nội dung đó. Không nêu tỷ lệ hoàn phí 60%/70%, không giải quyết conflict và không biến hearsay thành policy. Options/question/temporal dimensions là NOT_APPLICABLE theo assessment cho case này.

Giữ nguyên tám criterion records cần adjudicate: pass_criteria:0–2, fail_signals:0–1, forbidden_assumptions:0–2; grounding_and_citation và selective_conflict_handling dimensions vẫn REVIEW_REQUIRED. Guard PASS chứng minh checks hiện hành chấp nhận output, không thay thế semantic review hoàn chỉnh.

## 6. Technical Reliability

P1–P9 có **7 technical completions / 2 technical failures**, trong bảy completions có một original semantic FAIL và sáu REVIEW_REQUIRED. Không tính all completions là semantic successes.

- **P3/R2:** hai provider wrapper calls thành công nhưng domain validation thất bại, initial extraction rồi validation retry. Historical leaf code không được capture; không thể phân biệt hồi tố FACT_NAME_EMPTY/FACT_VALUE_EMPTY/FACT_DUPLICATE_CONFLICT từ thông báo chung. Raw response không được lưu, không suy diễn payload hoặc blame FINDING-04.
- **P5/R8:** supported deadline/portal draft bị reason number vì digits 301 trong INT301. Final Gate xác lập false positive bằng draft/source sets và pure helper check; final ERROR vẫn giữ.
- **P7/R7:** năm started provider attempts và hai skipped events vì case_budget_or_deadline; internal repair không còn attempt budget, guard chuyển fallback. Final result completed nhưng content handoff có defect. Không gọi skipped events là thêm API calls hoặc transport retries.
- **P9:** ba logical calls R2/R4/R7, ba attempts completed success; validation retry=0, transport retry=0; input 8,893/output 429/cache-read 0/cache-write 8,884 tokens. Estimated USD 0.001326125, billed UNKNOWN; stop COMPLETED.

P2–P9 có **27 recorded started provider attempts**, transport retry attempts=0; P1 thiếu attempt telemetry nên tổng API calls của toàn chín probes là UNKNOWN, không phải 27. Diagnostics P2–P9 có 28 logical-call entries, bao gồm một call chỉ có skipped events ở P7; số entries không đồng nhất số SDK invocations. Sum estimates có mặt ở P2–P9 = USD 0.012636125; P1 cost unavailable nên tổng cost tranche UNKNOWN. Nominal USD 0.50/case guard không bảo đảm hard provider billing cap.

Không suy technical reliability xác suất từ tranche nhỏ, có repeated cases, nhiều revisions và purposeful correction verification.

## 7. Corrections & Checkpoints

| Correction / checkpoint | Evidence đã xác minh | Giới hạn |
|---|---|---|
| FINDING-04 + FINDING-05: cbada3d20bce8d11145ce196b665746afe2e5825 | R2 prompt intent distinction + offline tests; pytest DB isolation trước import; P8 A4 P02 đúng | P2/P3 history giữ nguyên; isolation là offline verified |
| Safe R2 diagnostics: a4824be031e98bf6547cea146736c7c71b6191b6 | Stable FACT_NAME_EMPTY, FACT_VALUE_EMPTY, FACT_DUPLICATE_CONFLICT; per-call domain/provider separation | Không phục hồi metadata của P3 |
| LIVE retention: ff5c56766a8500b74cf360bfe2df4988fbe15009 | Capture r2_validation + provider_attempt, UUID/call index; P4–P9 có persisted validation PASS | P3 pre-retention không có leaf code |
| Numeric guard: 1cddcd96d920eff88f5a27dcf1a51685ad82b678 | Structured input course_code + input course context; không blanket whitelist; 500 offline tests PASS theo implementation evidence; B4 synthetic replay; Coordinator-attested independent safety REVIEW_PASS | P9 end-to-end AUTO_REPLY PASS nhưng identifier bypass branch chưa exercise LIVE |
| Fallback handoff: 32fd88a9c7a50e47a959580fb90f803912554542 | Structured R2/R5 context, numbered requests, critical caveats, selected-source quotes; specific procedural options; 93 targeted / 512 full tests PASS; Coordinator-attested REVIEW_PASS | Chưa LIVE verified sau correction; không thay initial R7 exception-before-card path hoặc attempt budget |

Code/test evidence: [R2 extraction](../../core/extract.py), [diagnostics tests](../../tests/test_r2_validation_diagnostics.py), [LIVE observer](../../verify/m2_dev_live.py#L94), [DB isolation](../../tests/conftest.py#L33), [isolation tests](../../tests/test_database_isolation.py), [numeric guard](../../core/ground_guard.py#L66), [numeric/synthetic B4 tests](../../tests/test_guards.py#L1053), [structured fallback](../../core/question_guard.py#L97), [fallback regression](../../tests/test_guards.py#L1339), [pipeline context wiring](../../core/pipeline.py#L650).

Fallback nay hiển thị request cụ thể và facts được đánh dấu chưa xác minh, giữ missing/conflicting/no-authority states và exact selected quotes. Hai options nêu hành động của người xử lý hoặc giữ chờ xác minh; không tự approve/reject, không ép ba options. Missing source không tạo fake citation. Legacy callers thiếu context vẫn dùng YAML path; production pipeline truyền đủ context.

Security evidence gồm allowlisted diagnostics fields, UUID preservation/sanitization và tests chống raw values/prompt/credential retention; không có logging raw provider output mới. Không claim toàn repository đã qua security certification. Regression kết quả được kế thừa từ exact committed snapshot; task này không rerun pytest.

## 8. Exit Gate Matrix

| Gate | Evidence | Result | Limitation |
|---|---|---|---|
| Routing | P1/P7 P01; P6/P8 P02; P4 P03; P9 P05 | Bounded positive evidence cho cả bốn groups | P2 wrong route lịch sử; không full 12-case hoặc final-HEAD LIVE sweep |
| Escalation subtype | AUTHORITY_REQUIRED / OUT_OF_POLICY / FACT_UNRESOLVED đúng ở completed positive paths | PASS trong scope đã quan sát | Không chứng minh mọi input |
| AUTO_REPLY end-to-end | P9 grounded=true, PENDING_SEND, card=null | PASS cho observation P9 | Không phải thư thật đã gửi; P5 failure giữ nguyên |
| Grounding/citations | P9 direct source-backed claims; guard checks unchanged; numeric counterexamples offline | CONDITIONAL | Broad semantic dimensions RR; input identifier bypass chưa exercise LIVE |
| Options/question quality | Structured fallback requests/options + offline regression | CORRECTED_OFFLINE; không còn defect cũ trong paths đã test | Historical A1/A2 FAIL; B1/B3/A4 usability RR; chưa chứng nhận BTC maximum question score |
| Human handoff | Correct queued routes + caveat-preserving fallback tests | Bounded functional evidence; CONDITIONAL | Chưa LIVE fallback sau correction, không claim full human usability |
| Safety | No automatic authority grant; uncertainty/conflict retained; unsupported numeric claims vẫn bị kiểm tra offline | Bounded positive evidence | Không universal safety PASS; semantic RR giữ nguyên |
| Technical reliability | 7/9 completions lịch sử; failures diagnosed/dispositioned, P9 complete | CONDITIONAL | P3 cause leaf UNKNOWN; R7 budget fallback vẫn có thể xảy ra |
| Observability | P4–P9 r2_validation persisted cùng provider metadata | CAPTURED cho current path | P1 attempts/cost và P3 leaf không hồi tố |
| Reproducibility | Frozen SHA, 9/9 capture binding, run IDs/fresh DBs, committed corrections | PASS về bounded traceability | Local ignored evidence và reports ngoài repo không tự có trên GitHub; stochastic repeatability chưa đo |

**Phân tầng acceptance:**

- **BTC/project mandatory:** routine automation; ba nhóm uncertainty; câu hỏi chuyển tiếp cụ thể; không khẳng định trên suspicious data; tối thiểu 15-case test set; Verify escalation 3 routine/2 escalation; các nghĩa vụ live URL/operational controls của project. M1 archive xác minh 15 executed và escalation5 3 AUTO/2 ESC, nhưng không chứng nhận toàn BTC/project submission hoặc current deployed URL. Handoff vẫn mandatory; bằng chứng correction offline là căn cứ đóng defect cụ thể, không phải miễn requirement.
- **Internal M2 gate:** positive evidence P01/P02/P03/P05; P04/technical không thay P03. Roadmap chưa lock numeric M2 threshold; không tự đặt % pass mới. Điều kiện full semantic certification chưa đạt nên không gọi M2_PASS.
- **Internal quality targets:** complete adjudication, no unresolved demonstrated unsafe behavior, safe diagnostics, bounded attempts, source/DB integrity. Remaining RR không mặc định unsafe hoặc PASS.
- **Recommended coverage:** full frozen 12 cases, temporal contrasts và preregistered repeated observations nếu sau này được cấp phép. Không phải minimum LIVE count của BTC.
- **Optional improvements:** polish wording/latency, richer safe metadata ngoài nhu cầu diagnosis, broader benchmarks; không được gắn optional cho một confirmed mandatory defect.

## 9. Remaining Limitations

| Limitation | Disposition / owner |
|---|---|
| 22 narrative RR cũ + 8 P9 RR; broad usability judgments chưa đầy đủ | Coordinator giữ explicit semantic condition; chặn M2_PASS toàn diện, không tự đòi thêm LIVE |
| Năm narrative FAIL lịch sử, P2/P3/P5 original run failures | Giữ immutable; không refund quota hoặc đổi Gold; không coi lịch sử là current regression nếu thiếu bằng chứng |
| 6/12 unique frozen cases, DEV exposed và mẫu nhỏ | Công bố coverage/generalization limitation; không có accuracy estimate cho toàn fixture |
| Numeric identifier branch chưa exercise ở P9 | **INCONCLUSIVE_LIVE cho specific path**; offline counterexamples và synthetic B4 là evidence có giới hạn |
| Fallback mới chưa LIVE verified | **NOT_VERIFIED_LIVE**; corrected offline/reviewed; không claim A1/A2 post-fix LIVE PASS |
| P3 first-call/leaf diagnostics không lưu | ROOT_CAUSE_PARTIAL; không giữ raw response để suy lỗi, không sửa historical observation |
| Budget/timeout và docs drift | PROJECT_SPEC §6 nói bốn attempts, source infra/settings.py hiện năm; ghi source thực tế, không sửa docs hoặc claim strict total transport cancellation |
| Small seed corpus, no student-record verification/real email delivery | Không claim production authority decisions, real-world deployment safety hoặc real-user study |
| M3 soft decision variable | Hard P01/P02/P03 priority không phải calibrated confidence; similarity threshold không tự là decision-confidence/adaptation proof |

Sau hai corrections không tìm thấy confirmed unresolved mandatory blocker mới trong evidence đã kiểm. Missing LIVE branch coverage và open semantic adjudication là điều kiện công bố/theo dõi, không bị chuyển thành claim đã PASS. Nếu review sau đó xác lập unsafe claims, wrong routing hoặc handoff vẫn không chỉ rõ yêu cầu/caveat ở final source thì phải chuyển disposition sang M2_NOT_READY; không giữ conditional bằng cách hạ requirement.

Các nghĩa vụ Sprint 2 như independent evaluation, feedback adaptation và ít nhất ba người dùng thực chưa được task này xác minh. M2 conditional closeout không miễn chúng và không tự authorize M3.

## 10. M2 Closeout Recommendation

**Đề xuất: M2_CONDITIONAL_CLOSEOUT.**

Lý do: mandatory core group routing có evidence, routine completion đã hoàn tất sau numeric correction; confirmed fallback defect đã sửa ở shared production path với structured evidence, offline integration tests và independent review được Coordinator xác nhận. Không có yêu cầu BTC phải có một số lượng LIVE observations cố định hoặc bắt buộc mọi correction phải rerun LIVE. Vì vậy evidence offline có thể hỗ trợ disposition defect, trong khi các giới hạn phải được giữ rõ.

Điều kiện đi kèm: Coordinator phê duyệt bản này và giữ tất cả RR/history; numeric branch INCONCLUSIVE_LIVE và fallback NOT_VERIFIED_LIVE không bị reword thành VERIFIED_LIVE; không quảng bá 68/95 hoặc 68/103 là accuracy; không claim toàn 12 cases/full semantic safety PASS; không tự triển khai M3.

M2_PASS chỉ có thể được cân nhắc khi scope/threshold/evaluator được phê duyệt và các applicable semantic judgments có đủ bằng chứng đạt, không còn mandatory blocker. M2_NOT_READY áp dụng nếu một mandatory defect được xác lập vẫn chưa disposition bằng evidence đáng tin cậy. Conditional này là proposed milestone disposition, không sửa roadmap Gate hoặc thay quyết định của Coordinator.

## 11. M1 + M2 Check-in Preparation

**CHECK-IN CONTENT: READY**, có giới hạn claim được ghi rõ; chưa gửi lên hệ thống nào.

### M1 deliverables đã kiểm

[Living M1 report](M1_runtime_reliability.md) và [immutable M1 evidence manifest](../evidence/m1/README.md) ghi M1 PASS/CLOSED. Đã đọc JSON gốc archive và tính hash:

| Suite | Verified result | Thời gian | Artifact / SHA-256 |
|---|---|---:|---|
| verify4 | 4/4 passed; 0 technical errors | 35.28s | [verify4_final.json](../evidence/m1/verify4_final.json); 351b9573f35d7953b075c6d96cadf7abd8d6665fbc861d5f5ada523e2142e6e2 |
| escalation5 | 4/5 passed; 0 technical errors; 3 AUTO/2 ESC | 44.48s ≤90s | [escalation5_final.json](../evidence/m1/escalation5_final.json); 07869713037ca86aa59b9456a7bb2a55e66c8609cbbf04fe17d0fe3241787fa8 |
| full15 | 15 executed, 14 passed; 0 technical errors | 93.19s | [full15_gate_final.json](../evidence/m1/full15_gate_final.json); 81203a4a50eb01c68595555a7f7ce8c3b0060d8e8451ed5e81c9138cc705ddaf |

M1 technical gate ≤1/15 đạt với 0/15; 90s requirement ở đây áp cho escalation5, không áp nhầm cho full15. JSONs ghi OpenAI/gpt-6-luna, live/cache=false. M1 original E04 expected P03 nhưng actual P01 là semantic mismatch, không phải technical failure.

M2.2 đã có local evidence riêng sửa E04: run `m2_2_targeted_live_20261006_025456_887c1029`, artifact `E04.json` dưới `data/validation/` (local evidence — not published), có P03/FACT_UNRESOLVED và passed=true; living M2 report ghi targeted E04/E01/E05 3/3 và canonical escalation5 5/5. Không gộp các runs này vào nine-Probe denominator hoặc ledger baseline hiện tại; không gọi original M1 E04 thành PASS hồi tố. Full final-HEAD canonical E04 rerun NOT_VERIFIED.

M1 code milestones theo living report: c4d2f8d OpenAI adapter; a2ed369 bounded clock/basis repair; d1b4e2a field-preserving basis repair. M1 independent review acceptance là Coordinator-attested PASS WITH DOCUMENTED DEBT; sáu LOW debts và tracked bytecode hygiene vẫn được công bố, không được xóa bằng M2 closure.

### Nội dung check-in đề xuất

“Exodia đã đóng M1 technical reliability với full15 0/15 technical errors (14/15 label matches); M2 đề xuất đóng có điều kiện. Bốn routing groups có positive evidence, A4 informational/appeal confusion được verified LIVE, safe R2 diagnostics đã persisted, numeric guard và fallback handoff có reviewed corrections. Probe 09 hoàn tất AUTO_REPLY/P05. Chúng tôi giữ mọi historical failures và semantic REVIEW_REQUIRED; chưa claim held-out accuracy, full 12-case coverage hoặc LIVE verification của fallback mới/specific identifier branch.”

Quantitative claims dùng đúng §3/§5/§6; Git checkpoints dùng full SHA ở §7. Không claim general provider superiority, actual billed cost, calibrated adaptive threshold, real-user effectiveness hoặc hoàn thành toàn bộ BTC requirements.

### Hướng chuyển tiếp M3

Coordinator có thể dùng evidence và limitations này để xác định M3 scope: đánh giá soft decision variable thực sự, protocol/calibration và feedback requirements trước khi nói về adaptation. Đây chỉ là check-in preparation; không mở task, không implement M3, không thêm experiment hoặc authorization ngầm.

### Integrity & task execution

**INTEGRITY: PASS.** Chỉ tạo báo cáo Markdown này. Không sửa source, fixtures/Gold/rubric/policy, ledger, historical artifacts/assessments hoặc DB. Không pytest, LIVE/API, commit/push/merge, cleanup hoặc gọi Anti/Ponytail. Đối chiếu cuối: **241/241 existing file hashes giữ nguyên**; DB SHA-256 2884f58cb132cfdff6347b5b88d8cf5d3ef5c9c32958bcaa20690a237d1da2d5; WAL/SHM không tồn tại trước/sau. HEAD giữ nguyên, index rỗng; Git status chỉ thêm báo cáo này ngoài các dirty changes có sẵn. Kiểm 44 local links đều tồn tại; không thấy email hoặc credential pattern trong báo cáo mới.

**LEDGER: 12/45 consumed, 33 remaining. LIVE/API CALLS trong task này: 0.**
**NEXT:** Coordinator duyệt conditional closeout và quyết định check-in M1 + M2. Dừng sau báo cáo.
