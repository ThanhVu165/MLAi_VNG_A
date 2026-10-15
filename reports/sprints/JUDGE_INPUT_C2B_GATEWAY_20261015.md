# C2-B — local/server-only gateway & offline staging

Owner Mac + Codex; authorization: **COORDINATOR AMENDMENT — GO C2-B LOCAL/SERVER-ONLY**.
Baseline `dev@ac5184ee5f1568827df321b7c737f218885f293f`, verified fetch; #70 merged
đúng SHA này, chứa CR01. Branch `codex/judge-input-c2b`. READY_FOR_REVIEW, chưa DONE.

## Scope / trust boundary

- `ui/judge_gateway.py`: registry và Unix-domain IPC operator; không HTTP provisioning.
- `scripts/judge_operator.py`: local terminal client; secret nhập bằng getpass, không argv,
  widget, URL, stdout hoặc log. Secret chỉ đi qua IPC trong private OS directory.
- Điểm nối Email/Audit: khi `JUDGE_GATEWAY_SOCKET` được cấu hình, grant nằm trong registry
  server, bind theo ScriptRunContext.session_id do Streamlit server cấp. Không tin query,
  widget hoặc credential/session được chèn vào session_state. Mã đối chiếu hiển thị là
  identifier không cấp quyền; operator phải đối chiếu đúng phiên với judge trước cấp.
- Khi gateway chưa cấu hình, giữ seam C1 server-only và canonical/private behavior cũ.
  Không có form tự cấp quyền ở cả hai chế độ. Không thay chữ ký Core/public API hiện hữu.
- IPC yêu cầu operator secret C2-A cho mọi thao tác, cả list/inspect/recovery; directory
  canonical, owner hiện tại, mode 0700; socket 0600. Không overwrite path cũ/symlink.
  Envelope ≤4096 bytes, timeout 3 giây; trả lỗi generic, không echo request/exception.
- Local OS account và tiến trình cùng UID là trusted computing base, không chống host
  compromise. Không dùng interface này như public authentication hoặc remote gateway.

Provisioning giữ lock local và gọi C2-A one-use provisioning ID. Một session chỉ được
provision một lần, kể cả đổi request ID sau revoke/expiry. Rerun/native reconnect giữ binding
đang có, không cấp thêm; reload nếu tạo session mới không kế thừa quyền. Restart mất registry,
không deserialize token hoặc tự
cấp lại grant. Quota/nonce/reservations/revocation vẫn ở ledger bền vững, không reset.
Grant TTL/limits, HOLD/CR01, PREVIEW_READY, dispatch guards giữ nguyên C2-A.

## Validation / AC

Python 3.11.17, pytest 8.3.3, Darwin arm64; synthetic SQLite riêng từng fixture. Main
conftest khóa socket/DNS/OpenAI. Smoke chạy child process chỉ cho AF_UNIX, chặn AF_INET/
DNS/OpenAI constructors; thực sự bind/connect IPC local, không phải network/provider call.
Sandbox mặc định chặn bind Unix socket; smoke được chạy với quyền local IPC bổ sung.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -rs -p no:cacheprovider tests/test_judge_input_c2b.py tests/test_judge_input_c2a.py tests/test_judge_input_c1.py tests/test_judge_new_input_offline.py tests/test_core_reliability.py tests/test_llm_budget.py tests/test_guards.py tests/test_semantic_validator_compat.py tests/test_provider_observability.py tests/test_runtime_worker.py tests/test_m3_t06_human_control.py tests/test_restricted_demo.py tests/test_runtime_replay_audit.py tests/test_policy_engine.py tests/test_r2_validation_diagnostics.py tests/test_audit_navigation_session.py tests/test_email_input_ui.py tests/test_pre_m4_ux.py tests/test_audit_coverage.py tests/test_audit_details.py tests/test_ux_responsive_cardless.py --tb=short
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m black --check --line-length 100 ui/judge_gateway.py scripts/judge_operator.py tests/test_judge_input_c2b.py pages/1_Xu_ly_email.py pages/4_Nhat_ky_kiem_toan.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m ruff check --no-cache ui/judge_gateway.py scripts/judge_operator.py tests/test_judge_input_c2b.py pages/1_Xu_ly_email.py pages/4_Nhat_ky_kiem_toan.py
git diff --check
```

**457 PASS, 3 SKIP in 26.88s**, exit 0 (12 new C2-B cases). SKIP: historical LIVE artifacts
không có tại test_r2_validation_diagnostics.py:355; không skip security/smoke. Black/Ruff/
diff check PASS. No-fail-open/no-over-escalation, Verify4 4/4, Core #71, C1/C2-A/CR01,
guards, persistence, Human Control, restricted/private, Audit/Email/UI PASS.

| AC | Evidence offline |
|---|---|
| 1 guest/forged/expired/revoked denied | Operator denial, fake state/reference, expiry/revoke/mode tests; no side effects |
| 2 refresh/replay/quota | Rerun, new browser session, cleared registry restart simulation, durable provisioning ID replay; 8 concurrent operator attempts issue exactly one grant |
| 3 cross-session | Two server contexts cannot read/submit for each other; AppTest guest Audit denied despite injecting actual other-session grant into state |
| 4 HOLD | Operator inspect/recover idempotent, HOLD retains slot/debit; no cases/jobs/Audit/provider/send created |
| 5 kill switch | OFF rejects submit/provision; operator revoke still works OFF; live/private gateway modes denied |
| 6 regression/no-send | Suite above; gateway submit PREVIEW_READY, no jobs/send events; preserved Core/Infra source diff |
| 7 smoke | Actual Unix IPC: wrong secret denied, provision once/replay denied, replay pipeline 3 calls, preview, CLI revoke, ownership denial, recovery; socket permissions checked |

AppTest hard-codes the same session_id for every fake browser; test-only context adapter
distinguishes actual harness server SessionState instances. Production uses native server
session_id, not Python object IDs or client state. Existing C1 tests/fixtures unchanged.
Initial runs caught that harness collision, missing model in smoke environment and sandbox
IPC permission; corrected test setup, not policy/expected values or production bypasses.

## Local operator runbook (commands are instructions, not deployment evidence)

1. Use one local trusted process, a **new synthetic DB**, server secret supplied privately
   to that process (≥32 chars), `APP_MODE=restricted_demo`, `LLM_MODE=replay`.
   `JUDGE_INPUT_ENABLED` remains default OFF unless operator explicitly enables offline.
   Create a short canonical private directory via `mktemp -d /private/tmp/exodia-c2b.XXXXXX`;
   set `JUDGE_GATEWAY_SOCKET` to `<directory>/operator.sock`. Do not reuse real DB/path.
2. Open existing local Email UI. Gateway starts lazily; guest only sees pairing reference.
   Confirm that reference with judge in person/trusted channel. Do not treat it as proof
   of identity or accept unauthenticated remote requests to approve a reference.
3. On the same host/UID, run `.venv/bin/python -m scripts.judge_operator --socket <path>
   sessions`. Enter secret via hidden terminal prompt. Use `provision --reference <ref>
   --request-id <stable-operator-ID-at-least-16-chars>` once. CLI never returns raw grant.
   Judge reruns UI to refresh granted state; never paste token/secret into browser.
4. `holds` inspects case IDs/phases only; `revoke --reference <ref>` revokes durably, even
   when feature OFF. `recover` uses C2-A/CR01 terminal reader and never executes pipeline.
   Ambiguous HOLD stays HOLD; no manual SQL reset, refund, queue/send or auto retry.
5. Kill switch: set JUDGE_INPUT_ENABLED=0 in trusted server process/environment and apply
   through the host's normal controlled restart if needed. No kill-switch widget added.
   Restart loses bindings; do not reuse provisioning IDs or issue new grants automatically.
   For stale IPC paths, stop the owning process and start with a fresh private directory;
   gateway deliberately refuses to delete/overwrite a socket. Durable quota stays unchanged.

## Self-review / risks / handoff

No ownership overlap found in open PR #51 (deployment artifacts) or #55 (study docs).
No infra/llm.py, core/, C2-A ledger/schema/migrations/audit/policy/budget/deployment changes.
M7 hashes before/after unchanged: report `7a37ba82d7126ed9c617c28b00c72f8c3de08f23087ec17d870e836c55a8f3d1`,
renderer `55eab88ec53e0c5a3814555d7e00c347160f35d6616b9de5e119bb11b93bdbe4`.
No token/issuer in guest render/query or gateway responses; logs test checks secret absent.

Limits: single-process Unix/Mac/Linux only, trusted local OS operator; no production auth,
multi-host guarantees or Windows IPC. Registry bounded to 100 sessions without automatic
eviction (fail-closed availability limit); operator must plan short staging sessions.
Expired/revoked session is not re-granted. On restart old in-memory tokens are unavailable
to gateway (including operator revoke-by-reference); prior persisted revoke/debits remain,
but grant handoff/restoration is deliberately unsupported. Restart smoke covers server IPC
in a fresh child; browser reload/restart ownership is tested via changed context/cleared
registry, not deployed-browser E2E. Full suite/mypy/real deployment/provider quality NOT RUN.
Streamlit transport session IDs/reconnect behavior remain framework-managed; they are not
authenticated human identity. Không mở rộng safety claim sang public/hostile deployment.

LIVE/provider calls **0**. No email, merge or deploy. Independent security review and
Coordinator acceptance required before integration. Final commit/PR recorded in handoff.

Implementation/test SHA: `e2e8f7a48698568464449ded423e1216c0692afd`.
PR: [#72](https://github.com/ThanhVu165/MLAi_VNG_A/pull/72), targets dev. Follow-up commit
chỉ ghi metadata này; final HEAD bàn giao trong chat, reviewer kiểm đúng final SHA.

## Fast self-review — PR #72 @ 32ede2cc

Reviewed exact SHA: `32ede2cc43c7e51a6621cc52324af77286594b6e`, base
`ac5184ee5f1568827df321b7c737f218885f293f`. Local HEAD khớp; reviewed six-file diff.
Không sửa code, test hoặc policy trong lượt self-review; chỉ thêm section report này
ở working tree, chưa commit/push. Không thay thế independent review/Coordinator acceptance.

| Check | Result / evidence |
|---|---|
| Session isolation | PASS trong local trust boundary: server context binding, ignored forged credential/state/reference; two-context and Email/Audit AppTest cross-session denied |
| Unix caller permissions | PASS trong trusted local UID scope: parent ownership/0700/no symlink, socket 0600; all operations require operator secret; unsafe-parent test and actual IPC wrong-secret denial PASS. Không claim kernel peer-UID attestation hoặc thực nghiệm bằng user OS thứ hai |
| Secret/token disclosure | PASS trong inspected paths: getpass/TTY, no secret argv/widget/URL, no grant returned; generic IPC errors, UI/query/log assertions and sessions/holds response checks PASS |
| Replay/reload issuance | PASS: one-use durable ID plus per-session provisioned flag; 8 concurrent attempts issue one grant, rerun/reload/new context/cleared registry never auto-issue or reset ledger |
| Revoke/HOLD/no-send | PASS: revoked/expired/OFF deny; HOLD inspect/recovery keeps slot/debit with no pipeline/case/jobs/Audit mutation; actual gateway smoke PREVIEW_READY/no send, CLI revoke denies read |

Targeted command only:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -rs -p no:cacheprovider tests/test_judge_input_c2b.py --tb=short
git diff --check ac5184ee5f1568827df321b7c737f218885f293f..32ede2cc43c7e51a6621cc52324af77286594b6e
```

**12 passed in 1.78s, zero failures/skips**, exit 0; Unix IPC smoke used local permission
override, AF_INET/DNS/OpenAI blocked. Diff check PASS. Full suite NOT RUN this review.
Verified no diff in Core, C2-A access ledger, LLM adapter, schema, audit or policy versus
baseline; both M7 fingerprints unchanged. Confirmed actionable code findings: **NONE**
within these checks; this is not proof of absence of all security defects.

Code Review plugin CI discovery returned **Connect your GitHub account to continue**.
Remote CI diagnostics NOT VERIFIED; no CLI fallback for plugin CI and no claim of remote
CI PASS. Self-review above is direct local diff/test evidence, not plugin certification.

Remaining risks: native Streamlit reconnect/session-ID behavior is not authenticated human
identity; no hostile/deployed-browser session hijack test. Same-UID host processes remain
trusted (no SO_PEERCRED enforcement). Registry 100-session saturation, stale socket and
restart token loss are fail-closed operational availability limits described above.
Recommendation: READY_FOR_INDEPENDENT_REVIEW, not automatic merge/GO-LIVE. LIVE/provider
calls 0; no new HTTP endpoint, email, merge or deploy.

## Final macOS Unix validation — FAIL / HOLD (supersedes earlier disposition)

Reviewed exact PR #72 SHA: `c4ff44a102194ac9fa119d6eb31ef8c847381f82`.
Owner authorization: MAC — C2-B FINAL UNIX VALIDATION; artifact-only commit/push approved.
macOS Darwin arm64, Python 3.11.17, Streamlit **1.39.0**, actual OS UID **501**.
Không sửa source/test trong repo; previous self-review PASS did not test native reconnect.
This section supersedes its no-finding/READY recommendation: **HOLD pending correction**.

### Two Windows-blocked tests — 2 PASS

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -rs -p no:cacheprovider tests/test_judge_input_c2b.py::test_socket_path_rejects_unsafe_directory tests/test_judge_input_c2b.py::test_local_ipc_staging_smoke_network_and_provider_blocked --tb=short
```

**2 passed in 0.75s**, exit 0. Unix IPC local permission override used; child permits
AF_UNIX only, blocks AF_INET/DNS/OpenAI. Directory 0755 rejected; actual operator socket
0600 in 0700 private directory works. Wrong operator secret denied, correct secret can
provision once/revoke, replay provisioning denied, PREVIEW_READY and no-send hold.

### Additional focused UID + reconnect probes — 1 PASS / 1 FAIL

Outside-repo probe: `/private/tmp/exodia-c2b-final.B0wyZp/test_final_unix.py`.
SHA-256: `a6e14fc60f737d15e7272268cc3f0e8b5158e1a393949eeec016dc8eaf63082d`.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A/tests:/Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A .venv/bin/python -B -c 'import pytest, conftest; raise SystemExit(pytest.main(["-q", "-p", "no:cacheprovider", "--tb=short", "/private/tmp/exodia-c2b-final.B0wyZp/test_final_unix.py"], plugins=[conftest]))'
```

**1 failed, 1 passed, 1 warning in 1.86s**, exit 1. Warning is anyio assertion-rewrite,
not a network/provider attempt. Test conftest blocks network/DNS/OpenAI before imports.
Total for this request: **3 PASS / 1 FAIL**, of which exactly two requested missing tests
PASS. Full suite NOT RUN.

UID probe PASS: actual directory/socket stat owners equal getuid()=501, modes 0700/0600.
Client rejects UID mismatch before prompting for issuer secret. Mismatch predicate tested
by replacing getuid() in test only; NOT a real second-user/setuid attempt. No SO_PEERCRED
attestation claimed; trusted same-UID host processes remain in the trust boundary.

### Confirmed finding C2B-R01 [P1] — known old session ID recovers judge capability

Affected app code: `ui/judge_gateway.py:46–51,76–81`, registry keyed only by native
Streamlit session_id, with no disconnect invalidation or reconnect approval boundary.

Installed framework evidence:

- browser_websocket_handler.py:112–129 reads client-supplied third WebSocket subprotocol
  as existing_session_id, then passes it to runtime.connect_session.
- websocket_session_manager.py:80–97 reattaches an inactive stored AppSession by ID,
  without an independent identity/capability comparison; native default storage TTL is
  120 seconds. Active sessions instead get a new ID (control verified).
- app_session.py:726 puts session_id in the browser initialization message. This does
  not prove attacker discovery of a victim ID; it disproves treating that ID as a
  purely server-only, non-replayable identity.

Reproduction uses real BrowserWebSocketHandler.open, WebsocketSessionManager,
MemorySessionStorage and AppSession (not mocked reconnect decisions):

1. Create native victim session, bind/provision through gateway operator path, run a
   synthetic replay case; verify PREVIEW_READY and victim can_read=True.
2. New client supplies the known victim ID while victim active: framework creates a
   different ID, gateway cannot read the victim case (negative control PASS).
3. Disconnect victim through native session manager; within default storage TTL a new
   guest handler supplies `Sec-Websocket-Protocol: streamlit,unused,<old-session-id>`.
4. Native manager returns exactly the victim ID and the same AppSession object, including
   its owned case IDs. Gateway context now resolves the retained registry grant;
   can_read=True and grant_valid=True without another operator approval or issuer/grant
   token supplied by this guest. Negative assertion fails with KNOWN_ID_RECONNECT.
5. Explicit operator revoke still makes can_read=False. No send events or jobs created.

Only file watching is disabled in probe; gateway context accessor is supplied the native
manager's returned ID to model the reconnecting script execution. No hand-edited registry
grant or fake manager result. This is an in-process native handler/runtime + real gateway/
SQLite proof, NOT browser-level/deployed WebSocket handshake E2E. It establishes a real
application authorization path under the stated known-ID/disconnected-session precondition;
it does not establish remote ID theft, random-ID guessing, or cross-origin handshake bypass.

Impact: existing judge capability/case-read ownership can move to a new guest connection.
No new grant or budget is issued; therefore the earlier no-reissuance tests can remain
green while isolation fails. Operator secret and Unix permissions do not guard this judge
reconnect path. Revoke/HOLD/no-send remain effective and limit, but do not remove, impact.

### Decision / remaining work

**FAIL — recommend HOLD PR #72** until Coordinator approves a focused correction of the
disconnect/reconnect grant boundary, with regression for known-ID inactive reconnect and
active-session control. Prefer invalidation/reapproval over treating transport ID as
authenticated identity; precise hook/ownership/contract must be agreed before code change.
No source fix was attempted in this validation request. Independent re-review required.

Remaining unverified: deployed-browser E2E, origin/proxy behavior, actual foreign OS user
connect denial, native-ID acquisition by an attacker. Do not claim these PASS. Other known
availability limits (registry saturation/stale socket/restart token loss) still apply.
M7 fingerprints unchanged; Core/LLM/schema/policy unchanged. LIVE/provider calls **0**;
no public HTTP endpoint, real email, full suite, merge or deploy. Artifact-only final SHA
is provided in handoff; source remains byte-identical to reviewed c4ff44a.

### Reproduction appendix (copy to a temporary test file outside repo)

```python
import asyncio
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace

import pytest
from streamlit.runtime.app_session import AppSession
from streamlit.runtime.memory_session_storage import MemorySessionStorage
from streamlit.runtime.memory_uploaded_file_manager import MemoryUploadedFileManager
from streamlit.runtime.script_data import ScriptData
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
from streamlit.runtime.websocket_session_manager import WebsocketSessionManager
from streamlit.web.server.browser_websocket_handler import BrowserWebSocketHandler

from infra import db
from scripts import judge_operator
from ui import judge_gateway as gateway
from test_judge_input_c1 import SECRET, _input, _provider
from test_judge_input_c1 import judge as judge_fixture

judge = judge_fixture


def test_actual_socket_uid_modes_and_client_uid_gate(judge, monkeypatch):
    monkeypatch.setattr(gateway, "_LISTENER", None)
    with tempfile.TemporaryDirectory(prefix="c2b-uid-", dir="/private/tmp") as directory:
        path = Path(directory) / "o.sock"
        monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", str(path))
        gateway._start_listener()
        listener = gateway._LISTENER
        try:
            assert Path(directory).stat().st_uid == path.stat().st_uid == os.getuid()
            assert stat.S_IMODE(Path(directory).stat().st_mode) == 0o700
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
            monkeypatch.setattr(sys, "argv", ["operator", "--socket", str(path), "sessions"])
            monkeypatch.setattr(judge_operator.getpass, "getpass", lambda _: pytest.fail("SECRET_PROMPT_MUST_NOT_RUN"))
            current_uid = os.getuid()
            with monkeypatch.context() as different_uid:
                different_uid.setattr(os, "getuid", lambda: current_uid + 1)
                with pytest.raises(SystemExit) as denied:
                    judge_operator.main()
                assert denied.value.code == 2
        finally:
            listener.close()


def test_known_disconnected_session_id_must_not_recover_judge_grant(judge, monkeypatch):
    monkeypatch.setenv("JUDGE_GATEWAY_SOCKET", "/not-opened/reconnect.sock")
    monkeypatch.setattr(gateway, "_BINDINGS", {})
    monkeypatch.setattr(gateway, "_start_listener", lambda: None)
    # Only filesystem watching is disabled; session creation/storage/reconnect remain native.
    monkeypatch.setattr(AppSession, "register_file_watchers", lambda self: None)
    context = SimpleNamespace(session_id="")
    monkeypatch.setattr(gateway, "get_script_run_ctx", lambda **kwargs: context)
    _provider(monkeypatch)

    async def exercise():
        script = ScriptData(str(Path.cwd() / "streamlit_app.py"))
        manager = WebsocketSessionManager(MemorySessionStorage(),
            MemoryUploadedFileManager("/unused"), ScriptCache(), None)

        class LocalRuntime:
            def connect_session(self, client, user_info, existing_session_id=None):
                return manager.connect_session(client, script, user_info, existing_session_id)

        runtime = LocalRuntime()

        def open_client(previous=None):
            headers = {} if previous is None else {
                "Sec-Websocket-Protocol": "streamlit,unused," + previous
            }
            client = SimpleNamespace(request=SimpleNamespace(headers=headers), _runtime=runtime)
            BrowserWebSocketHandler.open(client)
            return client

        victim = open_client()
        context.session_id = victim._session_id
        reference = gateway.prepare_session()
        gateway._operate(dict(operation="provision", secret=SECRET, reference=reference,
                              request_id="final-reconnect-proof-0001"))
        result = gateway.submit(_input())
        victim_session = manager.get_active_session_info(victim._session_id).session
        victim_session.session_state["restricted_demo_case_ids"] = [result.case_id]
        assert gateway.can_read(result.case_id)
        # Active victim cannot be joined merely by supplying its ID.
        active_attacker = open_client(victim._session_id)
        assert active_attacker._session_id != victim._session_id
        context.session_id = active_attacker._session_id
        assert not gateway.can_read(result.case_id)
        manager.close_session(active_attacker._session_id)
        manager.disconnect_session(victim._session_id)
        # Same old ID in a new guest connection; no operator or grant credentials.
        attacker = open_client(victim._session_id)
        assert attacker._session_id == victim._session_id
        restored = manager.get_active_session_info(attacker._session_id).session
        assert restored is victim_session
        assert restored.session_state["restricted_demo_case_ids"] == [result.case_id]
        context.session_id = attacker._session_id
        regained_read = gateway.can_read(result.case_id)
        regained_grant = gateway.grant_valid()
        # Revoke still mitigates the restored session; no send side effect.
        gateway._operate(dict(operation="revoke", secret=SECRET, reference=reference))
        assert not gateway.can_read(result.case_id)
        assert not db.fetch_all("SELECT * FROM case_jobs")
        assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
        manager.close_session(attacker._session_id)
        assert not (regained_read or regained_grant), (
            "KNOWN_ID_RECONNECT: new guest recovered disconnected victim session, "
            "existing grant and judge case read access without operator approval"
        )

    asyncio.run(exercise())

```
