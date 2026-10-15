# Pre-M4 UX/UI Implementation — Cardless Closeout

## Authorization and scope

- **Authorization:** Project Coordinator directly authorized this UX-only package in the ChatGPT/Codex session on 15/10/2026 and waived Trello for this work.
- **Owner:** Project Coordinator operating the current Mac with Codex implementation support.
- **Repository:** `ThanhVu165/MLAi_VNG_A`
- **Baseline:** `dev@cefd3db950f76b35d2960490f161141145172919`
- **Previously reviewed SHA:** `0630a1a6878d685257eb1fda0f2edfe36d0dd457`
- **Initial implementation SHA:** `3457f90b9e0edb965163e69ccbb867a09083db58`
- **Final validated implementation SHA:** `3d3934cb4e343b95e40ba92b2d83ff65c9fccd94`
- **Branch:** `codex/ux-pre-m4-cardless`
- **Result:** `READY_FOR_REVIEW`
- **LIVE/API calls:** 0
- **Deployment:** `NOT RUN`

Authorization was limited to UI-03, UX-07, UI-05 and UI-04. It did not authorize backend capability, access-control, routing, policy, corpus, evaluation-set, Gold, Railway or deployment changes.

## Preflight

- Remote `dev` was verified at the requested baseline `cefd3db950f76b35d2960490f161141145172919` before branching.
- At minor-correction preflight, remote `dev` had advanced to `53b6a8e3c0f90b11fc9c9b87e110bd29505639b8` through merged M4-T02 documentation/evidence only. Those files do not overlap the correction, and GitHub reported PR #62 clean and mergeable before editing.
- The preceding M7 PR #61 was already merged, so no implementation task remained active on the prior branch.
- The task branch was created from verified `origin/dev`; no reset, clean, stash, rebase, extra clone or worktree was used.
- The required report path did not exist before implementation.
- Existing untracked/ignored M7 artifacts remained untouched and were excluded from both commits and validation evidence.
- Python 3.11.17 and the existing repository virtual environment were used; no dependency was added.

## Files changed

| File | Change |
|---|---|
| `pages/1_Xu_ly_email.py` | Adds first-time five-step guidance and puts Restricted DEMO limitations before the input form. Clarifies that only three canonical samples run in public replay and new free-form input is not processed. |
| `pages/3_Quan_tri_quy_dinh.py` | Adds a friendly catalog-empty state in restricted and private views while retaining the existing table and distinct search-no-match message. |
| `pages/5_Verify.py` | Identifies replay mode, distinguishes pipeline results from UI fixtures, explains PASS/FAIL, and renders stored result timestamps without generating render-time timestamps. |
| `tests/test_pre_m4_ux.py` | Adds five AppTest regressions for onboarding, regulations empty/table states, replay explanation, pipeline provenance and timestamp stability. |
| `tests/test_restricted_demo.py` | Makes the restricted fixture self-contained with the locked replay model/cache configuration. |

Minor correction after review changed only `pages/1_Xu_ly_email.py` and its assertion in `tests/test_pre_m4_ux.py`: step 5 now instructs users to open Audit from the left sidebar in the same session. It does not advertise deep-link recovery and does not change navigation, ownership or access control.

No file under `core/`, `corpus/`, `policies/`, `infra/`, `verify/`, deployment configuration or evaluation data was changed.

## Acceptance criteria

| AC | Result | Evidence |
|---|---|---|
| AC1 — First-time public-demo guidance appears before input | **PASS** | AppTest and local browser show the limitation banner and five-step workflow before the sample buttons/form. |
| AC2 — Three canonical samples work; public new input remains blocked; private input does not regress | **PASS** | Restricted-demo and email-input regressions pass. Guard and canonical matching were not changed. |
| AC3 — Regulations table remains; true empty catalog has a friendly state; permissions remain unchanged | **PASS** | New empty/table AppTests pass; restricted access regression remains green. |
| AC4 — Verify4 behavior preserved; replay/fixture/PASS/FAIL/timestamp clarified | **PASS** | Verify4 replay is 4/4; pipeline output is explicitly distinguished from UI fixture; timestamp survives rerender unchanged. |
| AC5 — No LIVE/API, policy, guard, authorization or mutation privilege change | **PASS** | Offline barrier active, LIVE/API 0, scoped diff contains UI/tests/report only. |
| AC6 — Reviewable evidence and validation | **PASS** | This report, implementation commit, diff review and recorded validation commands. |

## Validation

All test commands used the project Python 3.11 environment. Network/provider access was blocked by the test harness.

| Check | Result | Details |
|---|---|---|
| Format | **PASS** | `python -m black --check --line-length 100` on all changed Python files. |
| Lint | **PASS** | `python -m ruff check` on all changed Python files. |
| New UX tests | **PASS** | `pytest tests/test_pre_m4_ux.py -q` → 5 passed. |
| Targeted UI/safety suite, initial run | **FAIL — explained and fixed** | 4 restricted replay cases failed closed with `TECHNICAL_ERROR` because the existing fixture did not set `OPENAI_MODEL`; 63 tests passed. No UI regression was found. |
| Restricted fixture after fix | **PASS** | `pytest tests/test_restricted_demo.py -q` without shell model injection → 23 passed. |
| Full targeted suite after fix | **PASS** | `pytest tests/test_restricted_demo.py tests/test_email_input_ui.py tests/test_presentation.py tests/test_ui_baseline_integration.py tests/test_source_workflow.py tests/test_pre_m4_ux.py -q` → 67 passed, one pre-existing Altair deprecation warning. |
| Verify4 isolated replay | **PASS** | Locked environment (`gpt-6-luna`, replay, cache off, restricted demo, empty API key) and fresh temporary DB → 4/4 PASS in 0.18 s; corpus `cv_f6eb04187bb0`. |
| Local browser desktop smoke | **PASS** | Email page guidance, existing regulations table, Verify replay notice, 4/4 pipeline result, stored timestamps and timestamp column visually/semantically confirmed. |
| Audit sidebar smoke in the same session | **PASS** | A canonical email was processed, then Audit was opened through the left sidebar in the same browser session; the page retained ownership and displayed the correct case/events. No deep-link claim was tested or added. |
| Mobile browser smoke | **NOT RUN** | The available in-app browser did not expose a viewport override. AppTest coverage passed, but no mobile visual claim is made. |
| LIVE/API | **NOT RUN** | Explicitly prohibited; call count 0. |

Minor-correction validation: `pytest tests/test_pre_m4_ux.py tests/test_restricted_demo.py tests/test_email_input_ui.py -q` → **35 passed**. Black, Ruff and `git diff --check` also passed.

The restricted fixture fix is intentionally test-only. Production continues to fail closed when `OPENAI_MODEL` is missing; no silent production default was introduced.

## Self-review

- `git diff --check`: PASS.
- Scoped file review: PASS; only three approved UI pages, two test files and this report are included.
- Input guard, canonical matching, pipeline, expected decisions, harness calculation, session ownership and access-control code are unchanged.
- The timestamp shown by Verify comes from `VerifyResult.timestamp`; rerendering does not replace it with current time. When no timestamp exists, the UI says it is missing.
- Restricted Regulations checks an empty list successfully; database exceptions are not caught or relabeled as an empty catalog.
- No Audit navigation fix was attempted and no claim was made that UI-01 is resolved.
- The correction verifies and documents only sidebar navigation inside the current session; it does not claim that direct Audit links restore a lost session.

## M4-T02 isolation

This change does not modify or consume the M4-T02 manifest, rubric, Set A, Set B, Gold, seal, GO-A or GO-B state. It does not treat replay/UI fixture output as official evaluation evidence. M4-T02 remains an independent dependency and gate.

## Risks and limitations

1. Mobile visual behavior was not directly inspected because viewport emulation was unavailable.
2. Existing Streamlit navigation emits a warning about combining `st.navigation` with a `pages/` directory; this predates the task and was not changed.
3. The Verify page still exposes the existing audit link; UI-01 session-loss navigation remains out of scope.
4. The UI uses the existing English technical terms `Restricted DEMO`, `replay`, `PASS` and `FAIL` alongside Vietnamese explanations for traceability.

## Handoff

- Implementation commit: `3457f90b9e0edb965163e69ccbb867a09083db58`
- Evidence report commit: `0b0ba84ff67e4d1c5959e080764e1ead14e725f3`.
- Minor-correction implementation commit: `3d3934cb4e343b95e40ba92b2d83ff65c9fccd94`.
- Pull request: [#62 — feat(ux): clarify pre-M4 restricted demo workflow](https://github.com/ThanhVu165/MLAi_VNG_A/pull/62), targeting `dev`.
- Merge/deploy: not authorized and not performed.

The package is ready for MLAI/Coordinator review. It is not declared DONE.
