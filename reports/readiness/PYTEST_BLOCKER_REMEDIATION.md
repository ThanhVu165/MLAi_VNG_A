# Pytest blocker remediation — frozen fixture portability

## Current result — approved continuation (12/10/2026)

**RESULT: READY_FOR_REVIEW.** Coordinator đã phê duyệt scope update **92 fixture failures + 0 subprocess failures**:

> Remediate 92 cross-platform frozen-fixture integrity failures while preserving Gold, frozen semantic content and integrity protection; then execute the underlying assertions and determine whether any real product/test defects were previously hidden.

Report này tiếp tục report local hiện có; historical STOP record và original failed IDs ở phía dưới được giữ để truy vết. Các bảng NOT RUN/NOT COMMITTED trong historical record mô tả lượt trước, không phải disposition cuối.

### Baseline và preflight re-check

- Remote dev vẫn **ed9d053e337dbd49314870eef4157f1fe27ca2ad**, fetch và direct ls-remote xác minh lại trước implementation.
- Branch **codex/pytest-blocker-remediation**; report local và 10 sidecars cũ giữ nguyên. Không worktree/clone/backup.
- PR #40 vẫn OPEN, head **a7acf60a64fded8835d82ed4291ab0f10eab831b**, base dev; không sửa/cherry-pick/merge.
- Original reproduction: **605 collected / 513 PASS / 92 FAIL / 0 SKIP**, 63.93s.
- Group B: **CURRENTLY PASS / NO REMEDIATION**. Cả ba positive DB-isolation configurations PASS; không sửa interpreter/dependency/test Group B.

### Chosen canonical integrity mechanism và alternatives

Existing integrity contract là raw final-file bytes, không semantic JSON equivalence: hai loaders dùng read_bytes()/SHA-256; constants và reports M2 đã ghi digest d18cd770...cccc04. Không thay hash guard/expected digest/serialization/evaluation policy.

Chọn **Git-enforced canonical LF cho đúng một frozen artifact**:

~~~gitattributes
/verify/cases_m2_combined_dev.json text eol=lf
~~~

- Root .gitattributes trước task chưa tồn tại; scoped M1 evidence attributes đã có, giữ nguyên.
- Explicit eol=lf giữ canonical checkout khớp authoritative Git bytes dù core.autocrlf=true/input/false. Không áp pattern *.json hoặc reports/evidence.
- Canonical JSON serialization/hash đã xét nhưng không chọn: sẽ thay final-byte contract, bỏ qua khác biệt whitespace/key order có thể thuộc integrity evidence và thay digest/provenance. Chưa có authorization đổi evaluation semantics.
- Loader-side CRLF normalization không chọn: sẽ chấp nhận transformed file bytes thay strict byte contract hiện hành. Giữ unchanged loaders, bảo đảm representation tại Git checkout boundary.
- Trong checkout hiện có, kiểm current CRLF bytes chỉ khác Git blob ở newline, rồi ghi **exact authoritative Git blob** làm canonical working representation. Không regenerate dataset hoặc sửa giá trị; fixture không có committed diff.
- Git checkout filters thực tế: git -c core.autocrlf=<mode> cat-file --filters HEAD:verify/cases_m2_combined_dev.json; so byte equality với Git blob và working file. Ba modes PASS. Đây là conversion proof, không claim đã tạo clean clone/platform khác.
- File bị CRLF/tamper ngoài Git checkout vẫn bị raw SHA guard BLOCK; không mở quyền normalize mọi input.

### Files changed và frozen/Gold preservation

| File | Change |
|---|---|
| [.gitattributes](../../.gitattributes) | Một exact-path text/eol=lf rule và comment |
| [tests/test_frozen_fixture_portability.py](../../tests/test_frozen_fixture_portability.py) | 3 checkout-mode checks, positive loader check, semantic-mutation negative check |
| [reports/readiness/PYTEST_BLOCKER_REMEDIATION.md](PYTEST_BLOCKER_REMEDIATION.md) | Update continuation/result/validation, giữ historical reproduction |

Preservation proof **PASS**:

- Working bytes == index blob bytes == verified baseline Git blob bytes.
- Git object ID vẫn **af2dd539a1ac8feb003194d3766085e906e0c25c**.
- Existing authoritative SHA-256 vẫn **d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04**; canonical checkout không CRLF.
- Parsed JSON toàn bộ bằng nhau; **12 cases**, IDs, input, labels/expected results và Gold metadata bằng nhau. Equality transitive với before-fix CRLF JSON đã kiểm tại reproduction.
- Comparison-only semantic digest (sorted compact JSON UTF-8): **500dd28a1eab26923af10327840f74eca6f3d4e0d17683c931913959e8694989**. Chỉ chứng minh content equality, không thay loader contract.
- Git check-attr chỉ target frozen file text=set/eol=lf. verify/cases_verify4.json, verify/cases_full15.json, reports/sprints/M2_goal_progress.md vẫn unspecified; scoped M1 evidence file vẫn text=unset.
- Không thay case/Gold/Set A/B/frozen values/expected hash/history/core/policy/approval/schema/STATUS/workflow docs. Staged fixture blob khớp HEAD, không commit fixture representation change.

### Positive và negative integrity proof

**PASS**: canonical fixture được cả load_frozen_cases và load_prereg chấp nhận.

**PASS**: temporary copy đổi một real field value: case đầu input.subject thêm INTEGRITY_TEST_MUTATION, thay một JSON string token trong raw bytes. Parsed copy xác minh subject đổi. Cả hai loaders ném BLOCKED_FIXTURE_HASH_MISMATCH. Original fixture bytes không đổi sau test. Không dùng newline-only mutation làm semantic negative proof; không sửa Gold labels hoặc authoritative fixture.

### Original 92 rerun / targeted / full-suite truth run

Mọi run dùng project .venv/Scripts/python.exe, Python 3.11.9 / pytest 8.3.3, existing precollection temp DB + replay/socket/provider barriers. Parent env: PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, PYTHONIOENCODING=utf-8, LLM_MODE=replay; loại PYTEST_ADDOPTS. Không cài dependency hoặc gọi LIVE provider.

~~~text
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider --basetemp <fresh-run-temp> --junitxml <run.xml> --tb=short --show-capture=no <targets>
~~~

Targets actual:
- Original92: expand đúng 92 node IDs từ baseline classification.json, không broad -k hoặc đổi test. Manifest original-92-ids.json lưu local; exact list trong historical appendix dưới.
- Targeted: tests/test_frozen_fixture_portability.py tests/test_m2_dev_assessment.py tests/test_m2_dev_execution.py tests/test_m2_dev_live.py tests/test_m2_telemetry_cost.py tests/test_r2_validation_diagnostics.py.
- Full: không target args; canonical pytest.ini discovery tests/ và verify/.

| Run | Collected | PASS | FAIL | SKIP | ERROR | Duration | Exit |
|---|---:|---:|---:|---:|---:|---|---:|
| Initial mechanism checks | 5 | 5 | 0 | 0 | 0 | 0.36s | 0 |
| Exact original 92 | 92 | 92 | 0 | 0 | 0 | 4.51s | 0 |
| Targeted regression | 180 | 180 | 0 | 0 | 0 | 4.69s | 0 |
| Canonical full truth run | 610 | 610 | 0 | 0 | 0 | 54.74s | 0 |

JUnit xác minh counts/failure/skip/error, original92 manifest matched baseline 92 unique node IDs. Năm regression mới giải thích 605→610 collected. 92 tests thực hiện existing assertions sau hash guard, không skip/xfail/expected mutation. Ba historical diagnostics có local captures nên chạy và PASS, không chuyển sang SKIP.

**REMAINING FAILED IDS: NONE. PRODUCT BUGS DISCOVERED: NONE in executed suite.** Không suy suite xanh thành LIVE/evaluation accuracy hoặc milestone PASS.

### Self-review / artifact ledger / handoff

Ruff và Black scoped **PASS** sau format-only correction; Git whitespace/diff/scope, Markdown links/tables/UTF-8/NFC và sensitive-data scan kiểm trước commit. Không in/commit fixture content, private Gold, captured email, secrets hoặc local raw logs. Full suite giữ một AltairDeprecationWarning; không che warning.

Local evidence directory suffix **exodia-pytest-continuation-awkhle4y** (OS temp); không upload raw logs/DB hoặc commit absolute local paths.

| Artifact | SHA-256 |
|---|---|
| original92.txt | 8a91a78d55a955936328eb5981d9867685eb8bd1f988af133edbd0cecde849a8 |
| original92.xml | 6bcd9c2e4269fb03af965fffba4fe595c2216e7d424e76918278b5f9f4d7a78a |
| original-92-ids.json | 7d83dad0d0fdbd21160aaaf50ad8ab2a7c6e470dea0d0b06b523b95cfadfd330 |
| targeted.txt | e5087837bab97f3406b30d728b607cafcc0dad0db3253528b100172fe1136ab6 |
| targeted.xml | 21f038405ffc268ff2eafcccb1b41abb07aecb7d29827dadda2034b2efb6ab48 |
| full.txt | d8a1e973a9a1be6acf651e60af4fcc0cf329753bf320388facc8327b3996f703 |
| full.xml | 8fdb3d7e39da2fb16a73ff5f53178d30328a1d00710267d66d0d1bf886ef7cd6 |

Commit/push được Coordinator ủy quyền khi validation/self-review hoàn tất; actual SHA và push result ghi trong final handoff để tránh self-referencing commit. Không yêu cầu mở PR mới ở continuation; không tự tạo PR, merge hoặc DONE.

Risks: existing checkout cần refresh đúng canonical bytes sau khi nhận attribute; custom tooling ngoài Git có thể tạo CRLF và vẫn bị BLOCK. Chưa actual clean-clone multi-OS execution; ba Git checkout modes và raw-byte equality đã kiểm. Local capture availability có thể làm historical tests SKIP ở máy khác; không thay policy. OS temp logs có thể bị cleanup; summary/digests/IDs giữ trong report.

**PR #40: UNCHANGED. LIVE LLM/provider/API/email: 0. NEXT STEP: Coordinator review; không merge/mark DONE.**

## Historical STOP record — before continuation scope approval


## Result và authorization

**HISTORICAL RESULT: BLOCKED — STOP trước implementation ở lượt trước.** Ngày 12/10/2026 (Asia/Saigon). Scope update phía trên đã cho phép tiếp tục và supersede disposition này.
Owner thực thi kỹ thuật: Codex theo yêu cầu Coordinator; không nhận thay human review/acceptance.

Yêu cầu đầu vào dự kiến 95 failures: Group A 92 fixture/newline, Group B 3 subprocess/rank_bm25. Stop condition nguyên văn:

> Nếu phân loại 92+3 không còn đúng: STOP. Không tiếp tục fix dựa trên giả thuyết cũ. Báo lại failed-ID/root-cause mới.

Kết quả hiện hành **92 + 0**, không phải 95: **605 collected, 513 PASS, 92 FAIL, 0 SKIP, 0 ERROR**, 63.93s, exit 1. Đã dừng trước mọi remediation. Report này là evidence reproduction, không tuyên bố READY_FOR_REVIEW của fix hoặc suite PASS.

## Verified baseline / repository / environment

- Repository: ThanhVu165/MLAi_VNG_A.
- Baseline được báo trước: `73e23f916f2d9f8904c4b47a0a4370d241d796c8`.
- Remote dev sau fetch và direct ls-remote: **ed9d053e337dbd49314870eef4157f1fe27ca2ad**.
- Delta từ baseline báo trước chỉ AGENT.md, docs/TEAM_WORKFLOW.md, docs/COORDINATOR_WORKFLOW_UPDATE_20261012.md; không thay fixture/tests/runtime/dependency nên không kích hoạt stop do root-cause baseline thay đổi.
- Checkout đầu phiên: codex/sprint2-evidence-reconciliation @ 9d035d64cd57306577f6ab1edb7fd7505c909f8c; tracked worktree sạch.
- Branch task: **codex/pytest-blocker-remediation**, tạo từ verified origin/dev. HEAD là baseline ed9d053; không worktree/clone/backup phụ.
- 10 pre-existing untracked SQLite WAL/SHM được giữ nguyên; không đọc/stage/delete. Test DB dùng temporary directory, không dùng data/app.db.
- PR #40: [OPEN](https://github.com/ThanhVu165/MLAi_VNG_A/pull/40), head `a7acf60a64fded8835d82ed4291ab0f10eab831b`, branch sprint/repository-cleanup-phase2, base dev. Chỉ đọc state/head; không sửa/merge/diff PR #40.
- Parent pytest: project interpreter **.venv/Scripts/python.exe**, Python **3.11.9**, pytest **8.3.3**; rank-bm25 **0.2.2**, OpenAI SDK **3.24.0**, Streamlit **1.39.0**. Không cài dependency.
- PATH `python`: system Python 3.11.9; find_spec('rank_bm25') trả None. Đây là environment khác với project venv; không dùng system interpreter để chạy suite.
- Đọc PROJECT_SPEC.md/STATUS.md/SPRINT_ROADMAP.md sections liên quan, pytest.ini, requirements.txt, .gitignore, conftest/isolation tests và fixture loaders/test call sites. Không chỉnh workflow docs.

## Reproduction command và isolation

PowerShell từ repository root. `$taskRunDir` là directory mới dưới OS temporary directory; không backup repository hoặc existing database. Exact command đã chạy:

```powershell
$taskRunDir = Join-Path $env:TEMP ('exodia-pytest-remediation-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskRunDir | Out-Null
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
$env:PYTHONIOENCODING='utf-8'
Remove-Item Env:PYTEST_ADDOPTS -ErrorAction SilentlyContinue
& .venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp (Join-Path $taskRunDir 'pytest-temp') --junitxml (Join-Path $taskRunDir 'baseline.xml') --tb=short --show-capture=no *> (Join-Path $taskRunDir 'baseline.txt')
```

pytest.ini canonical discovery: tests/ và verify/, loại data/validation. Existing tests/conftest.py tạo fresh absolute temp SQLite path trước project imports, LLM_MODE=replay và block socket/DNS/OpenAI constructors. DB-isolation children copy cùng hook và dùng sys.executable; inherited controlled env dùng PYTHONDONTWRITEBYTECODE/PYTEST_DISABLE_PLUGIN_AUTOLOAD/PYTHONPATH, loại PYTEST_ADDOPTS. Không mock rank_bm25 hoặc bypass import.

Full run trên **baseline chưa sửa**, cần để xác minh exact failed IDs trước implementation. Đây không phải Phase 7 after-fix truth run. Warning duy nhất: deprecation; không đổi warnings/tests để đẹp số liệu.

## Failure classification theo file

| File | FAIL | Root cause tại assertion/guard đầu tiên |
|---|---:|---|
| tests/test_m2_dev_assessment.py | 46 | Frozen fixture raw-byte SHA mismatch |
| tests/test_m2_dev_execution.py | 22 | Frozen fixture raw-byte SHA mismatch |
| tests/test_m2_dev_live.py | 16 | Frozen fixture raw-byte SHA mismatch |
| tests/test_m2_telemetry_cost.py | 2 | Frozen fixture raw-byte SHA mismatch |
| tests/test_r2_validation_diagnostics.py | 6 | Frozen fixture raw-byte SHA mismatch |
| TOTAL | 92 | 91 failures chạm hash guard (86 ValueError trực tiếp, 5 regex AssertionError do guard xuất hiện trước lỗi mong đợi) + 1 direct SHA assertion |

Ba tests historical_capture_without_r2_field_still_reads đều **FAIL hash guard**, không SKIP ở checkout này: ignored historical capture paths hiện có nên nhánh đọc được thực hiện. Đây là ba tests khác với ba DB-isolation configurations. Không sao chép historical capture/Gold vào report, không sửa raw evidence.

## Group A — root cause verified

Fixture duy nhất được xác định trong failures: `verify/cases_m2_combined_dev.json`.

| Representation | SHA-256 | Bytes | CRLF | LF total |
|---|---|---:|---:|---:|
| Verified dev Git blob | d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04 | 29962 | 0 | 506 |
| Working-tree checkout | 6d5dad27bb693103c282647c1c4de680bbc334ebd0d15155c8f5508777728595 | 30468 | 506 | 506 |

Git blob object ID (Git SHA-1, khác SHA-256 integrity digest): `af2dd539a1ac8feb003194d3766085e906e0c25c`.
`git config --get core.autocrlf` trả **true**; `git check-attr -a -- verify/cases_m2_combined_dev.json` không có explicit attribute output.

Kiểm stdlib bằng subprocess.check_output(['git','show','origin/dev:'+fixture]) và Path.read_bytes(), không in fixture content:

- working bytes replace CRLF→LF **bằng chính xác Git blob bytes**.
- json.loads(working bytes) == json.loads(blob bytes): **True**.
- Git blob SHA-256 khớp frozen constant; working checkout SHA-256 không khớp.
- [load_prereg](../../verify/m2_dev_assessment.py) và [load_frozen_cases](../../verify/m2_dev_execution.py) đều hash **read_bytes() trước parse**, không normalize. [Assessment contract](../../verify/M2_DEV_ASSESSMENT.md) và [execution contract](../../verify/M2_DEV_EXECUTION.md) yêu cầu final-byte integrity.

Representative traceback (safe excerpt từ baseline XML/log):

```text
verify/m2_dev_assessment.py:209: in load_prereg
    raise ValueError("BLOCKED_FIXTURE_HASH_MISMATCH")
E   ValueError: BLOCKED_FIXTURE_HASH_MISMATCH

verify/m2_dev_execution.py:107: in load_frozen_cases
    raise ValueError("BLOCKED_FIXTURE_HASH_MISMATCH")
E   ValueError: BLOCKED_FIXTURE_HASH_MISMATCH
```

Ngoài 86 ValueError trực tiếp, năm tests fail bằng AssertionError vì regex mong lỗi identity/path-traversal nhưng nhận BLOCKED_FIXTURE_HASH_MISMATCH sớm hơn. Một failure SHA trực tiếp: tests/test_m2_dev_execution.py::test_frozen_fixture_sha256_remains_unchanged_after_execution dừng ở assertion **hash_before == FIXTURE_SHA256**, trước execution. Tổng 92 cùng root cause raw-byte mismatch; chưa chạy assertion nghiệp vụ phía sau.

Không thay frozen content/Gold/expected SHA, không normalize file hoặc loader. Vì stop condition đã kích hoạt, chưa chọn/implement phương án canonical LF attributes/serialization và chưa chạy assertions phía sau blockers.

## Group B — historical hypothesis not reproduced

Parent run dùng project venv, có rank_bm25. [tests/test_database_isolation.py](../../tests/test_database_isolation.py) hiện dùng **sys.executable** tại cả hai subprocess.run call sites, không gọi literal 'python'. Child executable là exact parent interpreter theo arguments đã kiểm; không sửa test để in/mask import hoặc weaken assertion.

| Existing test | Baseline result |
|---|---|
| test_database_isolated_before_import_and_audit[dotenv] | PASS |
| test_database_isolated_before_import_and_audit[relative-env] | PASS |
| test_database_isolated_before_import_and_audit[absolute-env] | PASS |
| test_database_bootstrap_fails_closed[preimported-db] | PASS |
| test_database_bootstrap_fails_closed[temp-unavailable] | PASS |

Ba positive configurations đã import real core/pipeline chain, child pytest báo 1 passed, chạy audit/network-barrier/per-test-isolation assertions và kiểm synthetic user DB SHA/sentinel không đổi. Hai fail-closed bootstrap tests cũng PASS. Không có ModuleNotFoundError rank_bm25 trong failed records.

**Group B current failures: 0.** System Python thiếu dependency được xác minh read-only; không đủ evidence để kết luận ba lỗi lịch sử là child dùng sai interpreter. Historical execution command/environment chưa được cung cấp; nếu chạy suite bằng system Python thì sys.executable cũng chọn system Python. Không đổi sys.executable vốn đúng hoặc cài package vào system environment để hợp thức hóa giả thuyết cũ.

## Remediation / validation / product bugs

| Hạng mục | Trạng thái |
|---|---|
| Reproduction trước sửa | 605 collected; 513 PASS / 92 FAIL / 0 SKIP; 63.93s; exit 1 |
| Group A raw-byte/root cause | VERIFIED: LF Git blob vs CRLF checkout, semantic JSON bằng nhau |
| Group B 3 subprocess failures | NOT REPRODUCED: 3 positive isolation configurations PASS |
| Files changed | Chỉ report mới này; không implementation change |
| Exact remediation | NONE — dừng theo 92+3 mismatch stop condition |
| Gold/frozen content protection | Fixture bytes giữ nguyên; Git source/fixtures/Gold/expecteds không sửa |
| Integrity positive/negative after fix | NOT RUN — chưa có fix |
| Assertions sau 92 blockers | NOT RUN sau remediation; baseline bị block như phân loại |
| Targeted after | NOT RUN — STOP trước implementation |
| Full-suite after fix | NOT RUN — baseline full run ở trên không được gọi after-fix |
| Product bugs discovered | NONE VERIFIED trong reproduction; behavior sau hash guard còn NOT VERIFIED |
| PR mới / push / merge / DONE | NONE; không yêu cầu mở PR mới trong task này |
| Commit remediation/report | NONE tại STOP handoff; branch vẫn HEAD verified baseline |

Không biến no verified product bug thành chứng nhận product correctness. 92 tests chưa đi qua blocker; phải cập nhật scope/baseline classification với Coordinator trước tiếp tục.

## Evidence retention và risks

Local temporary evidence directory có suffix **exodia-pytest-remediation-96b7a261b17e4b99995631c8e3e58f7c**: baseline.txt, baseline.xml, classification.json. Không upload raw logs hoặc commit local paths/private captures. Exact failed IDs có trong report này để review mà không cần local logs.

| Local artifact | SHA-256 |
|---|---|
| baseline.txt | b0fdc46027ab81874f7b1ecbbb2f774f69d643fbd5a088249e42607a32267eec |
| baseline.xml | 514d1e15d028656a44034f221ab4315952cfd7102f8dd27e91e6999b90127076 |
| classification.json | e28333a871d854f92761de2a94872f2a03e6cc33a3eee091fe0e73fe78cb5319 |

Risk: 95-failure contract dựa trên environment/count cũ; hiện 92 fixture failures, ba DB-isolation tests PASS. Ignored capture availability ảnh hưởng FAIL/SKIP của ba historical diagnostics. Integrity contract vẫn nguyên final-byte SHA; chưa remediation portability, chưa chứng minh behavior phía sau guards hoặc negative-proof after-fix. No core/policy/approval/schema change, no fixture/Gold/Set A/B modification, no historical evidence/STATUS/AGENT/TEAM_WORKFLOW changes.

LIVE LLM/provider/API/email thực tế: **0**; existing offline barriers enforced. Git fetch/ls-remote và GitHub PR40 metadata là network evidence access, không phải application LIVE. Không chạy deployment/migration hoặc gọi provider.

**Coordinator cần cập nhật classification/scope sang baseline 92 fixture failures + 0 subprocess failures, hoặc cung cấp command/environment/logs tái lập ba lỗi Group B, trước implementation tiếp theo.** Không tự tiếp tục fix dựa trên giả thuyết 95.

## Exact remaining failed IDs — baseline, chưa sửa

```text
tests/test_m2_dev_assessment.py::test_structurally_correct_fabricated_option_is_not_full_pass
tests/test_m2_dev_assessment.py::test_wrong_decision_fails
tests/test_m2_dev_assessment.py::test_p05_unsupported_claim_not_pass_even_if_runtime_guard_passed
tests/test_m2_dev_assessment.py::test_supported_conflict_comparison_not_automatic_fail
tests/test_m2_dev_assessment.py::test_unqualified_approved_refund_fails_when_human_establishes_claim
tests/test_m2_dev_assessment.py::test_missing_escalation_content_fails[question]
tests/test_m2_dev_assessment.py::test_missing_escalation_content_fails[options]
tests/test_m2_dev_assessment.py::test_technical_error_separate_from_semantic_escalation
tests/test_m2_dev_assessment.py::test_missing_assessment_evidence_requires_review
tests/test_m2_dev_assessment.py::test_valid_full_review_can_pass_without_mutating_capture
tests/test_m2_dev_assessment.py::test_incomplete_rubric_coverage_never_full_pass
tests/test_m2_dev_assessment.py::test_content_review_cannot_use_only_correct_route_as_evidence
tests/test_m2_dev_assessment.py::test_multiline_output_quote_is_verified_against_actual_text
tests/test_m2_dev_assessment.py::test_tokens_redacted_and_unsanitized_capture_not_written
tests/test_m2_dev_assessment.py::test_invalid_or_contradictory_review_rejected[duplicate]
tests/test_m2_dev_assessment.py::test_invalid_or_contradictory_review_rejected[missing_rationale]
tests/test_m2_dev_assessment.py::test_invalid_or_contradictory_review_rejected[wrong_quote]
tests/test_m2_dev_assessment.py::test_invalid_or_contradictory_review_rejected[unknown_ref]
tests/test_m2_dev_assessment.py::test_invalid_or_contradictory_review_rejected[wrong_hash]
tests/test_m2_dev_assessment.py::test_invalid_or_contradictory_review_rejected[override]
tests/test_m2_dev_assessment.py::test_artifacts_cli_and_review_preserve_raw_capture
tests/test_m2_dev_assessment.py::test_guard_failure_is_definitive_structured_grounding_failure
tests/test_m2_dev_assessment.py::test_capture_keeps_diagnostic_availability_without_inventing_attempts
tests/test_m2_dev_assessment.py::test_temporal_reference_and_stale_source_remain_reviewable
tests/test_m2_dev_assessment.py::test_missing_criterion_or_multi_dimension_judgment_cannot_pass
tests/test_m2_dev_assessment.py::test_generic_quote_reused_for_unrelated_criteria_is_not_coverage
tests/test_m2_dev_assessment.py::test_automatic_fail_cannot_be_overridden_by_criterion_review
tests/test_m2_dev_assessment.py::test_old_review_json_is_rejected_clearly
tests/test_m2_dev_assessment.py::test_correct_execution_binding_and_result_identity
tests/test_m2_dev_assessment.py::test_a2_actual_submitted_input_cannot_be_labelled_a1
tests/test_m2_dev_assessment.py::test_missing_submitted_input_or_execution_fails_closed
tests/test_m2_dev_assessment.py::test_claimed_execution_fields_are_recomputed_and_bound[submitted_input_sha256-fake]
tests/test_m2_dev_assessment.py::test_claimed_execution_fields_are_recomputed_and_bound[fixture_input_sha256-fake]
tests/test_m2_dev_assessment.py::test_claimed_execution_fields_are_recomputed_and_bound[observation_id-other]
tests/test_m2_dev_assessment.py::test_claimed_execution_fields_are_recomputed_and_bound[case_id-M2DEV-A2]
tests/test_m2_dev_assessment.py::test_claimed_execution_fields_are_recomputed_and_bound[result_case_id-other-result]
tests/test_m2_dev_assessment.py::test_claimed_execution_fields_are_recomputed_and_bound[result_trace_id-other-trace]
tests/test_m2_dev_assessment.py::test_changed_actual_payload_rejected[body-Modified body]
tests/test_m2_dev_assessment.py::test_changed_actual_payload_rejected[subject-Modified subject]
tests/test_m2_dev_assessment.py::test_changed_actual_payload_rejected[sender-other@example.invalid]
tests/test_m2_dev_assessment.py::test_changed_actual_payload_rejected[received_at-2026-12-29T20:15:00+07:00]
tests/test_m2_dev_assessment.py::test_changed_actual_payload_rejected[channel-paste]
tests/test_m2_dev_assessment.py::test_changed_actual_payload_rejected[external_id-transport-change]
tests/test_m2_dev_assessment.py::test_canonical_input_order_unicode_timestamp_and_caseinput
tests/test_m2_dev_assessment.py::test_capture_mutation_after_review_creation_rejected
tests/test_m2_dev_assessment.py::test_malformed_execution_context_fails_closed
tests/test_m2_dev_execution.py::test_all_12_frozen_cases_load_correctly
tests/test_m2_dev_execution.py::test_offline_mock_runs_produce_12_distinct_observation_ids
tests/test_m2_dev_execution.py::test_adapter_receives_exactly_submitted_payload_bound_into_capture
tests/test_m2_dev_execution.py::test_swapped_a1_a2_input_is_rejected
tests/test_m2_dev_execution.py::test_mutated_input_after_adapter_invocation_cannot_create_false_identity_match
tests/test_m2_dev_execution.py::test_wrong_result_id_or_trace_id_is_rejected
tests/test_m2_dev_execution.py::test_missing_execution_context_prevents_assessment_pass
tests/test_m2_dev_execution.py::test_decision_error_remains_technical_error
tests/test_m2_dev_execution.py::test_adapter_exception_recorded_separately_without_fabricated_pipeline_result
tests/test_m2_dev_execution.py::test_assessment_or_artifact_write_failure_does_not_produce_false_pass
tests/test_m2_dev_execution.py::test_unreviewed_semantic_case_remains_review_required
tests/test_m2_dev_execution.py::test_existing_artifact_directories_cannot_be_overwritten
tests/test_m2_dev_execution.py::test_path_traversal_is_rejected
tests/test_m2_dev_execution.py::test_mock_execution_never_consumes_live_budget
tests/test_m2_dev_execution.py::test_no_provider_or_network_calls_occur
tests/test_m2_dev_execution.py::test_frozen_fixture_sha256_remains_unchanged_after_execution
tests/test_m2_dev_execution.py::test_synthetic_case_with_unsupported_factual_options_preserves_findings
tests/test_m2_dev_execution.py::test_cli_dry_run
tests/test_m2_dev_execution.py::test_missing_ledger_fails_closed_for_live_but_mock_is_unverified
tests/test_m2_dev_execution.py::test_exception_secret_and_private_body_never_persisted[False]
tests/test_m2_dev_execution.py::test_exception_secret_and_private_body_never_persisted[True]
tests/test_m2_dev_execution.py::test_environment_cannot_select_live_adapter
tests/test_m2_dev_live.py::test_invalid_budget_never_invokes[missing]
tests/test_m2_dev_live.py::test_invalid_budget_never_invokes[corrupt]
tests/test_m2_dev_live.py::test_invalid_budget_never_invokes[quota]
tests/test_m2_dev_live.py::test_accounting_failure_prevents_adapter
tests/test_m2_dev_live.py::test_durable_attempt_before_invocation_and_retry_count
tests/test_m2_dev_live.py::test_technical_failure_consumes_one_without_refund
tests/test_m2_dev_live.py::test_exception_message_never_persisted
tests/test_m2_dev_live.py::test_wrong_identity_cannot_capture_pass[payload]
tests/test_m2_dev_live.py::test_wrong_identity_cannot_capture_pass[result_id]
tests/test_m2_dev_live.py::test_stop_before_next_case_on_cost[None-1.0-1-COST_TELEMETRY_UNAVAILABLE]
tests/test_m2_dev_live.py::test_stop_before_next_case_on_cost[0.6-0.5-1-APPROVED_COST_LIMIT_REACHED]
tests/test_m2_dev_live.py::test_stop_before_next_case_on_cost[0.1-1.0-2-COMPLETED]
tests/test_m2_dev_live.py::test_real_adapter_boundary_fresh_seed_payload_and_runtime_restore
tests/test_m2_dev_live.py::test_default_cli_offline_and_no_ledger_consumption
tests/test_m2_dev_live.py::test_finalize_failure_keeps_attempt_debited_and_stops
tests/test_m2_dev_live.py::test_exception_after_provider_retries_retains_retry_metadata
tests/test_m2_telemetry_cost.py::test_cost_and_usage_survive_capture_with_context
tests/test_m2_telemetry_cost.py::test_adapter_direct_usage_cost_capture_with_mock_sdk
tests/test_r2_validation_diagnostics.py::test_r2_logger_to_live_capture_and_summary[invalid_invalid]
tests/test_r2_validation_diagnostics.py::test_r2_logger_to_live_capture_and_summary[invalid_valid]
tests/test_r2_validation_diagnostics.py::test_r2_logger_to_live_capture_and_summary[provider_failure]
tests/test_r2_validation_diagnostics.py::test_historical_capture_without_r2_field_still_reads[01-A1]
tests/test_r2_validation_diagnostics.py::test_historical_capture_without_r2_field_still_reads[02-A4]
tests/test_r2_validation_diagnostics.py::test_historical_capture_without_r2_field_still_reads[03-A4]
```
