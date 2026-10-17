# JUDGE-PUBLIC-LIVE-DEMO — offline implementation

RESULT: **READY_FOR_REVIEW**. Production Public LIVE/browser E2E: **NOT RUN**.

## Authorization và baseline

Coordinator đã duyệt CONTRACT-CHANGE và implementation offline: public admission tự động,
10 email/phiên, operator lane 3 case/grant, global budget $5, concurrency 2/1,
rate limit, session isolation, Audit, preview-only/no-send; dedicated regression,
self-review, PR/evidence. Không merge, deploy, bật public switch hoặc gọi OpenAI thật.
Ưu tiên CORE và frontend demo; hoãn cleanup, UI nâng cao và test không liên quan AC.

- Verified `origin/dev`: `4914f893756b3f7e52819538387625fdb1b02653` (PR #78 merged).
- Branch: `codex/public-live-demo`; code/contract/test SHA:
  `f6685f66383340fcece58831eed5fedaa5953c86`.
- Preflight production: deployment `0cc24c03-3f98-4879-bde2-e040f395bb2e`,
  SUCCESS/RUNNING; observed source hashes match baseline, Public switch absent.
  Read-only ledger snapshot: 4 finished requests, $0.04 debit/$4.96 remaining,
  12 historical provider attempts, zero active/HOLD/pending/blocked. This is a preflight
  snapshot, not a claim that other authorized testers cannot subsequently consume budget.
- Existing PR #51/#55 do not overlap proposed runtime files. Original checkout's
  untracked artifacts and branches were preserved; reused this task's clean checkout.

## Change

`JUDGE_PUBLIC_DEMO_ENABLED` defaults OFF. When ON with all existing Judge LIVE guards,
the Email UI accepts arbitrary synthetic pasted email. First submit lazily obtains a
server-only public capability, then runs the existing Judge reservation/pipeline. No
reference exchange, operator contact or manual provisioning is needed. Public UI hides
the operator reference and shows the public quota/rate information.

Operator capabilities remain 3 cases/600s. Public capabilities expire after 1800s and
share a durable 10-case quota across bindings of the same server AppSession ID. A new
WebSocket gets fresh ownership credentials and cannot read the old connection's case.
The ID is only a quota key, never proof of authority. Revoked public quota cannot be
reissued on another binding of the same server session.

New JSON settings namespace/provenance is validated against the existing C1/C2 ledgers.
Admission is atomic; public quota/rate updates and the existing cost/token/concurrency
reservation share BEGIN IMMEDIATE. Budget includes operator/public and all historical
reservations, without refunds. Corrupt/missing provenance, HOLD, invalid/blocked usage
or orphan pending attempts fail closed. Owners can still read their technical-error result
and Audit. Switch OFF blocks admission/reservation and the next public provider attempt;
it does not refund quota or disable operator admission.

Limits: 2 public requests/min/session, 10/min globally, 10 new bindings/min and 100 distinct
public server-session admissions for the entire demo run, persisted across restarts.
Existing 2 global/1 session concurrency, $0.01/case/$5 global, attempts/tokens, preview
and no-send are unchanged. No provider/model, policy/corpus, Verify4/Gold, SQLite migration,
audit action, account system, dashboard or framework changes.

## Validation

macOS arm64, Python 3.11.17, Streamlit 1.39.0. `tests/conftest.py` isolates a synthetic DB,
blocks network/OpenAI SDK; LIVE-path tests replace the provider boundary with a mock.
The executable below is abbreviated as `PY` in commands:

```text
/Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A/.venv/bin/python
```

| Check | Result |
|---|---|
| `PY -m pytest -q -p no:cacheprovider tests/test_public_live_demo.py` | 21 PASS in 3.21s |
| `PY -m pytest -q -p no:cacheprovider tests/test_public_live_demo.py tests/test_judge_input_c1.py tests/test_judge_input_c2a.py tests/test_judge_input_c2b.py tests/test_judge_input_live.py -k 'not test_normal_private_admin_rerun_and_override_remain_available'` | 162 PASS, 1 deselected in 20.78s |
| `PY -m black --check --line-length 100 infra/public_demo.py infra/judge_access.py ui/judge_gateway.py pages/1_Xu_ly_email.py streamlit_app.py tests/test_public_live_demo.py` | PASS, 6 files unchanged |
| `PY -m ruff check --no-cache infra/public_demo.py infra/judge_access.py ui/judge_gateway.py pages/1_Xu_ly_email.py streamlit_app.py tests/test_public_live_demo.py` | PASS |
| `git diff --check` | PASS |

Baseline failure is explicit: the initial combined run had 160 PASS/1 FAIL (before two
additional public tests). The same isolated private-admin test fails in the untouched
archive of baseline `4914f89`: fixture selects private+replay, but existing
`infra/llm.py:288` rejects private replay. Its code/expected and provider adapter were not
modified. This is not a fully green C1 suite; baseline owner disposition remains required.

New frontend test executes `streamlit_app.py` with real st.navigation/page.run; only supplies
the ScriptCache omitted by AppTest 1.39. A fresh harness session submits 10 arbitrary new
emails, each reaches the mocked OpenAI path (replay is forbidden), produces PREVIEW_READY,
draft/citations and Audit; request 11 fails before provider or creating case 11. The same
session opens Audit through its actual UI button. Fake clock advances respect the real
2/min rate limit; these are not 10 permitted simultaneous/immediate requests.

Other dedicated checks cover admission race, operator/public budget race with historical
debit, exact $5 boundary through existing C2-A test, concurrency 2/1 across bindings,
restart in an actual child process, quota 10/11, durable rate/admission caps, revoked/expired
grants, ledger damage, usage failure, orphan pending, kill switch, reconnect/cross-session
read denial, AUTO_REPLY/ESCALATE/error outcomes, invalid input rejection, Unix IPC and
no-job/no-SEND assertions. No full suite was run.

## Self-review, limits, handoff

- Reviewed complete source/test/contract diff; public token prefix alone never grants
  privilege: persistent provenance, binding, expiry and revocation are also checked.
- Operator path/limits stay independent. No frontend grants/secret widget or exposed token.
- Per-session means server AppSession, not an authenticated person. Hard refresh/new
  profile creating a new AppSession can obtain a new quota subject to durable admission
  and global guards. Same-ID reconnect does not reset quota or inherit read authority.
- Restart does not reset accounting; it can lose in-memory ownership bindings. No cookie
  resume or durable restoration of old case access is claimed.
- Anonymous users can exhaust the shared budget/admission pool; the controls bound
  spending/rate, not guarantee fair access or protection against all denial-of-service.
- $5 is the existing application reservation/debit envelope, not independently verified
  OpenAI billing enforcement. Model/pricing were not changed or revalidated by API calls.
- All AC have offline evidence; actual production browser + real OpenAI result remains
  NOT RUN, requiring independent security review, Coordinator merge/deploy/activation
  decisions and exact case/budget LIVE authorization.

LIVE/API provider calls: **0**. Merge/deploy/Public LIVE activation: **NOT RUN**.
