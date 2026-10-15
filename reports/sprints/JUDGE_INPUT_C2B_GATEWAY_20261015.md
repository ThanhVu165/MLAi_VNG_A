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
