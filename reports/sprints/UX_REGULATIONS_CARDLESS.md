# UX-REGULATIONS-CARDLESS — Regulations database error handling

## Handoff

- Result: `READY_FOR_REVIEW`
- Owner: Lenovo — Technical UX Owner
- Authorization: Coordinator-approved cardless implementation supplied for this task; no Trello card was required.
- Repository: `ThanhVu165/MLAi_VNG_A`
- Baseline: `dev@a6f3b7c7c564cb7bde13e124eb03f121eca0a114`
- Final implementation SHA: `d6a5acb4bd4af120b827cac72e2f218e49ff89b1`
- Branch: `codex/ux-regulations-cardless`
- PR: [#63](https://github.com/ThanhVu165/MLAi_VNG_A/pull/63), open and targeting `dev`
- LIVE/API calls: `0`

## Change

`pages/3_Quan_tri_quy_dinh.py` now routes every `list_sources()` read through one UI
boundary. The boundary catches only `sqlite3.Error` and `OSError`, writes a server-side
exception log, shows a fixed Vietnamese recovery message, and stops the Streamlit run.
Dependent source data is therefore not rendered after a failed read, and a database
failure cannot be mistaken for an empty catalog.

The Restricted DEMO filter, mutation guards, source metadata, admin approval behavior,
and the four UI-05 states remain unchanged. No database schema, query, permission,
corpus, Core, Verify, Email, Audit, deployment, Gold, or evaluation file changed.

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| AC1 — six synthetic sources render | PASS | AppTest asserts six rows and the existing metadata columns. |
| AC2 — read failure is safe | PASS | Fault injection covers `sqlite3.OperationalError` in restricted and private modes; no AppTest exception reaches the page. |
| AC3 — failure differs from empty state | PASS | Fault tests assert neither empty-state message is shown after failure. |
| AC4 — Restricted DEMO access unchanged | PASS | Existing restricted regression suite passed; production access modules were untouched. |
| AC5 — UI-05 preserved | PASS | AppTests cover populated table, true empty list, and search no-match as distinct states. |
| AC6 — tests, self-review, report and PR | PASS | Focused tests and static checks passed; this report and PR #63 provide the handoff. |

## Validation

Environment: Windows, Python 3.11 isolated `.venv`, SQLite databases under pytest temporary
directories, `APP_MODE` selected per test, `LLM_MODE=replay`, provider network blocked by
the repository test fixture.

| Command/check | Result |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q tests/test_ux_regulations_error.py` | PASS — 5 passed in 3.09s |
| `.venv\Scripts\python.exe -m pytest -q tests/test_ux_regulations_error.py tests/test_pre_m4_ux.py tests/test_source_workflow.py tests/test_restricted_demo.py` | PASS — 44 passed in 12.58s |
| `python -m black --check --line-length 100 pages/3_Quan_tri_quy_dinh.py tests/test_ux_regulations_error.py` | PASS |
| `python -m ruff check pages/3_Quan_tri_quy_dinh.py tests/test_ux_regulations_error.py` | PASS |
| `git diff --check` | PASS |
| Scoped credential/private-key pattern scan | PASS — no match |
| Browser smoke against a running Streamlit server | NOT RUN — AppTest covered both page modes and required UI states without touching Railway or production data. |
| LIVE/API/provider calls | PASS — 0 |

The first combined regression run reported one timeout in the pre-existing three-second
AppTest call for the seeded table. That test passed alone in 2.40 seconds, and the unchanged
combined command then passed all 44 tests. No test source or timeout was altered to hide it.

## Self-review and risks

Self-review checked the complete diff for overly broad exception handling, accidental empty
fallbacks, client-visible exception details, continued rendering after failure, scope leakage,
access-control changes, and secrets. `RuntimeError` fault injection confirms programming errors
are not converted into the user-facing database state.

Residual risk: this hotfix handles the reported catalog-read boundary. A later database failure
inside a separate detail action keeps that action's existing behavior and was not generalized
into a page-wide exception wrapper. This preserves the requested narrow scope and avoids hiding
unrelated defects.

Coordinator review and merge authorization remain required. This task does not merge, deploy,
or mark the work `DONE`.
