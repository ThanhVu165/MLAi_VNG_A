# P0-JUDGE-C2A — Offline Production Safety Foundation

## Handoff / authorization

- Owner: Mac + Codex, ngày 15/10/2026.
- Coordinator authorization trực tiếp: **GO-C2A OFFLINE — CARDLESS (CONDITIONAL)**.
- Không kế thừa miễn Trello từ C1; task C2-A được cấp cardless riêng trong chat.
- Baseline exact: `dev@534064f88b2851febc762fcdd0d376a2f0b76cd6`.
- Branch: `codex/judge-input-c2a`, tạo từ verified origin/dev.
- Result: READY_FOR_REVIEW cho foundation offline; independent security/code review và
  Coordinator acceptance còn pending. Không đề xuất merge trước review.
- Implementation SHA/PR: bổ sung sau commit/push.
- LIVE/API provider calls: **0**. Merge/deploy: **NOT RUN**.

## Preflight và ownership

Fetch xác nhận origin/dev đúng baseline; PR #68 đã merged, gồm security fix private admin
rerun/override. Tracked tree sạch trước task. Không reset, clean, stash, force-push, merge,
clone hoặc worktree phụ. Hai artifact M7 untracked vẫn nguyên vẹn, không stage:

- `reports/evaluation/M7_SET_B_PREPARATION_20261015.md`:
  SHA-256 `7a37ba82d7126ed9c617c28b00c72f8c3de08f23087ec17d870e836c55a8f3d1`.
- `outputs/m7_blind_private_work/render_blank.mjs`:
  SHA-256 `55eab88ec53e0c5a3814555d7e00c347160f35d6616b9de5e119bb11b93bdbe4`.

Đã đọc evidence Core Reliability hiện có và kiểm PR open trên GitHub: không có open PR Acer
trong kết quả, nhưng dữ liệu này không chứng minh Acer không giữ WIP/ownership ngoài remote.
Vì vậy **không sửa infra/llm.py** theo conditional scope; quyền không-overlap vẫn NOT VERIFIED.
Phần token output cap/usage reconciliation trực tiếp tại adapter không được triển khai trong
task này. Các file độc lập vẫn hoàn tất; không thay Core Reliability logic/policy của Acer.

Baseline C1 giữ nguyên: grant TTL 600 giây, 3 request/grant, 10/session, 20/toàn DB,
concurrency 2/toàn DB và 1/session; processing attempts=3, deadline=60 giây.

## Files changed / contract boundary

1. `infra/judge_access.py`: provisioning một lần, revocation, budget ledger và recovery.
2. `core/judge_input.py`: đánh dấu PROCESSING trước khi vào common pipeline.
3. `tests/test_judge_input_c2a.py`: dedicated offline/security/crash tests.
4. Report này.

Không đổi chữ ký các API/interface hiện hữu, CaseInput/Decision/EscalationType/CaseStatus,
SQLite schema, migration, audit action/meaning hoặc deployment. Helpers vận hành mới chỉ là
call phía server, không có HTTP/UI/query route. Ledger C1 giữ nguyên cấu trúc; metadata C2-A
được lưu tại hai key `judge_c2a:ledger` và `judge_c2a:initialized` trong settings hiện có.

## Implementation

### Secure provisioning / revocation

- `provision_grant()` yêu cầu operator secret server như C1, provisioning ID dài 16–128 ký tự
  do operator giữ. ID chỉ lưu hash; cùng ID không cấp lại grant sau refresh, revoke/recovery.
- Việc cấp grant và lưu provisioning ID cùng BEGIN IMMEDIATE, không có cửa sổ cấp trùng.
- C1 `issue_grant()` giữ chữ ký/limit hiện hành và vẫn là hàm server-only; không browser caller.
  Operator dùng ID mới vẫn không vượt số grant/request toàn DB hoặc session budget.
- `revoke_grant()` yêu cầu operator secret, lưu grant hash vào revoked list bền vững, idempotent.
  Revoke được cả khi feature OFF, không hoàn lại quota/budget, không xóa case/Audit.
- `_grant()` và `check_active()` kiểm revocation trong ledger; vì C1 adapter đã gọi check_active
  trước mỗi bước, request đang chạy bị chặn ở bước tiếp theo mà không sửa adapter.
- Session là anonymous ownership context, **không phải authenticated identity**. Không nhúng
  issuer secret vào UI, không tạo endpoint provisioning public, không mở feature public.

### Budget reservation — phân biệt rõ bằng chứng

| Loại | Thực thi / ý nghĩa |
|---|---|
| Request quota | Giữ đúng C1, đếm thật và consume trước pipeline. |
| Planned input/output token reservation | Reserve 24.000 input + 6.000 output units/case; đây là envelope dự toán cho tối đa 3 attempts, không phải usage quan sát. |
| Token reservation ledger limits | 300.000/session, 600.000/toàn DB; reserve nguyên tử, không hoàn trả kể cả lỗi hoặc unused envelope. |
| Estimated-cost reservation | 10.000 micro-USD/case (=USD 0,01 dự toán), 100.000/session, 200.000/toàn DB. Đây là phân bổ dự toán tham chiếu, không dùng bảng giá provider để claim actual cost. |
| Actual provider tokens/USD | NOT EVALUATED; không gọi API thật. |
| Hard provider token/USD cap | NOT IMPLEMENTED / NOT CLAIMED; cần max input/output bounds, adapter enforcement và usage reconciliation được Owner/Coordinator duyệt riêng. |

Quota, nonce, case provenance, C2 budget reservation và active slot cùng transaction. Concurrent
budget tests giảm giới hạn trong test để chứng minh chỉ đủ tối đa 2 token reservations hoặc
1 cost reservation trong 8 threads; denied requests không debit C1 hoặc tạo reservation.
Các giá trị dự toán không tăng limit C1 và không tạo quyền gọi provider LIVE.

Không hoàn lại token/cost allocations khi request kết thúc/recovery, vì chưa có usage đã
đối soát. Thiết kế bảo thủ này ngăn tự tạo lại ngân sách nhưng không phải quyết toán chi phí.

### Crash / restart

Lifecycle metadata nội bộ: RESERVED → PROCESSING → FINISHED; bất định → HOLD; snapshot
terminal đã xác minh → RECOVERED. Các nhãn này chỉ ở settings ledger, không đổi CaseStatus.

- Reserve commit trước pipeline. Facade đánh dấu PROCESSING trước intake; direct common
  pipeline dùng server scope cũng đánh dấu PROCESSING tại authorize_payload.
- Crash trước reserve không consume; crash sau reserve không refund quota/nonce/budget.
- `recover_reservations()` chỉ operator được gọi, không gọi pipeline/provider hoặc mutation case.
- Chỉ nhả active slot khi cases.status khớp snapshot case_id/status và latest decision,
  terminal thuộc PREVIEW_READY/AWAITING_HUMAN/ERROR/INVALID_INPUT, deadline NULL,
  không send events và không case_jobs. Quota/token/cost/nonce giữ debit.
- Không có snapshot, mismatch hoặc lỗi kho quyền: giữ HOLD và giữ slot, không retry AI.
- Context đang sống bị recovery chuyển HOLD cũng không được gọi provider tiếp, và finally
  không tự nhả slot HOLD. Thoát PROCESSING mà không lưu được terminal snapshot cũng giữ HOLD.
- Recovery idempotent, không tạo case, Audit hoặc quyền mới; revoke vẫn có hiệu lực sau restart.
- Ledger C2 mất/hỏng hoặc lệch markers/C1 totals: deny; initialized anchor ngăn tự tái tạo ledger.
- Khi nâng từ DB C1 chưa từng có C2 metadata, mọi case C1 cũ được debit full envelope bảo thủ
  từ provenance marker, phase HOLD; không cấp lại phần budget đã tiêu thụ.

### Kill switch / no-dispatch

JUDGE_INPUT_ENABLED thiếu/sai/OFF vẫn fail closed. OFF ngăn submit và bước provider tiếp theo;
không hủy ngược request đang trong provider. Revocation cũng không thể thu hồi một response
đã phát sinh trước thời điểm revoke. C1 chỉ replay/offline nên task không kiểm cancellation LIVE.
Không xóa lịch sử hoặc mở admin/human. PREVIEW_READY, deadline NULL, no-send invariants và
guards private rerun/override giữ nguyên qua regression C1.

## Threat model / limitations

| Threat | Control / giới hạn |
|---|---|
| Guest tự cấp grant / replay provisioning | Secret server, stable one-use provisioning ID, không có UI/public endpoint. |
| Đổi session/grant để reset quota | Durable C1 quota + C2 global/session budgets trong SQLite transaction. |
| Concurrent token/cost oversubscription | Atomic envelope reservation, không refund tự động. Không claim actual provider cap. |
| Crash ambiguous / duplicate nonce | Durable reservation/nonce, HOLD, không tự chạy lại pipeline. |
| Revoked grant sống lại | Revocation persisted, recovery không cấp quyền; ledger corruption fail closed. |
| Cross-session đọc case | C1 ownership + revocation check, fresh-process/reload tests. |
| Privileged mutation/send | C1 provenance guards và PREVIEW_READY/no-dispatch regression. |
| Secrets/logs | Chỉ hashes trong ledger; không raw token/secret/frontend credentials. |

Không có production gateway/authenticated principal, hard USD cap, provider usage settlement,
automatic HOLD operator resolution, multi-host storage hoặc staging proof. Đây là phần C2-A
offline trong scope độc lập, không chứng minh production/staging/LIVE readiness.

## Validation

Mac Python **3.11.17**, .venv; DB SQLite tạm và synthetic seed. Main pytest khóa network/DNS/
OpenAI SDK qua conftest. Subprocess crash tests khóa socket/DNS/OpenAI SDK riêng, dùng replay
double và `os._exit(17)` tại trước reserve, sau reserve, PROCESSING và sau snapshot terminal.
Không process crash nào chạy trên DB local thật.

```text
.venv/bin/python -m pytest -q tests/test_judge_input_c2a.py tests/test_judge_input_c1.py tests/test_guards.py tests/test_runtime_worker.py tests/test_restricted_demo.py tests/test_judge_new_input_offline.py tests/test_audit_navigation_session.py tests/test_email_input_ui.py tests/test_pre_m4_ux.py tests/test_runtime_replay_audit.py tests/test_audit_coverage.py tests/test_audit_details.py tests/test_llm_budget.py tests/test_ux_responsive_cardless.py
.venv/bin/python -m black --check --line-length 100 infra/judge_access.py core/judge_input.py tests/test_judge_input_c2a.py
.venv/bin/python -m ruff check infra/judge_access.py core/judge_input.py tests/test_judge_input_c2a.py
git diff --check
```

Final results: **281 passed in 17.27s** (28 C2-A, 51 C1); Black/Ruff/diff check **PASS**,
exit 0. Verify4 4/4, canonical, private workflow, UI-01 và audit regression PASS.
Một lượt mở rộng test trước đó báo 75 passed/1 failed vì assertion đặt nhầm trong test
legacy fixture (NameError); sửa test placement, không sửa expected cũ hoặc core để ép PASS.
Ruff ban đầu phát hiện fixture import shadowing; sửa re-export fixture trong file test mới.

Negative coverage: forged/guest/expired/revoked; wrong session; operator secret và replay
provisioning; concurrency token/cost; multi-grant session budget; revoke/kill giữa provider
steps; crash 4 giai đoạn; duplicate nonce sau recovery; snapshot mismatch; missing/malformed/
lost-request ledger; terminal persistence failure; operator recovery denial; legacy debit;
rollback cả hai ledger khi lỗi giữa reserve và C1 save; release-store failure giữ debit/slot
cho đến khi operator recovery xác minh terminal snapshot.

Không sửa infra/llm.py/core/types.py/infra/audit.py/infra/db.py/migrations: `git diff --exit-code
origin/dev -- ...` PASS. M7 fingerprints cuối khớp preflight.

## AC status

| C2-A AC | Trạng thái | Evidence |
|---|---|---|
| AC1 provisioning | PASS offline | Operator-only, one-use ID, forged/revoked/replay tests; không có public grant route. |
| AC2 budget | PASS cho reservation; actual provider cap NOT VERIFIED | Atomic concurrency/session tests; dự toán, usage và hard cap phân biệt ở bảng trên. |
| AC3 crash/restart | PASS | Real child-process crashes, durable revoke/debit/nonce, HOLD/RECOVERED, không case/Audit duplicates. |
| AC4 kill switch | PASS offline | Default disabled C1 + C2 kill giữa provider steps. |
| AC5 ownership | PASS | C1 cross-session/fresh-process + C2 revocation. |
| AC6 no-dispatch | PASS | C1 preview/escalation/private mutation security, C2 recovery không mutate case/Audit. |
| AC7 compatibility | PASS | Suite 281 gồm Verify4/canonical/private/UI-01/Audit. |
| AC8 evidence | PASS candidate | Dedicated tests/report/self-review/commit/PR; independent review pending. |

Coordinator conditional AC1–7: AC1 provisioning/revocation PASS; AC2 concurrent budget
reservation PASS; AC3 durable recovery/revoke PASS; AC4 C1 regression PASS; AC5 không đổi
schema/interface/audit semantics PASS; AC6 evidence candidate PASS; AC7 provider calls=0 PASS.
Independent acceptance không được suy ra từ các PASS offline này.

## Owner self-review / next gate

Đã rà toàn diff, schema/interface/action preservation, atomic transaction boundaries, budget
debits qua crash/error/restart, durable revoke, provenance reconciliation và no duplicate
processing. Đã bổ sung guard cho direct common pipeline scope để lỗi snapshot không nhả slot
PROCESSING bất định. Không sửa test C1/fixture cũ hoặc evidence lịch sử. Scope đúng 4 files;
infra/llm.py được giữ nguyên vì chưa có ownership clearance với Acer.

C2-B cần independent review trên final SHA, authenticated gateway/provisioning handoff,
staging/retention/HOLD operational procedure. C2-C cần ownership clearance của adapter và
authorization riêng về provider/model/cases/budget; max-output/input enforcement và numeric
usage reconciliation trước bất kỳ tuyên bố hard USD ceiling nào. Nếu cần schema/interface/
audit/provider-policy change, phải có amendment riêng. LIVE/API=0; merge/deploy NOT RUN.
