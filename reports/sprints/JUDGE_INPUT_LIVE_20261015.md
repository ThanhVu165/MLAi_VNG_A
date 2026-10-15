# JUDGE-INPUT-LIVE — evidence handoff

Cardless authorization: Coordinator phê duyệt Judge Input nhận email mới và OpenAI LIVE,
nhưng cấm API/deploy/email thật cho tới khi có GO riêng. Owner: Codex.

- Baseline đã xác minh: `origin/dev@e4b2c8440e242fd2d6e2f28091becea1b0fdde19`.
- Branch: `codex/judge-input-live`; target: `dev`.
- Luồng: operator grant + WebSocket binding → reservation SQLite → OpenAI mock/LIVE
  → pipeline chung → `PREVIEW_READY` hoặc `AWAITING_HUMAN`/`ERROR`; không job/send.
- Guard: `APP_MODE=restricted_demo`; `JUDGE_LIVE_ENABLED=1`; provider OpenAI;
  `JUDGE_LIVE_MODEL == OPENAI_MODEL`; `LLM_CACHE=0`; revoke/kill/HOLD fail-closed.
- Giới hạn: 3 request/grant, 20 request/toàn DB, 1 concurrent/session, 2 concurrent/toàn
  DB; 3 provider attempts/case; reservation 24k input + 6k output/case; request OpenAI gắn
  `max_completion_tokens=2000`; 30 giây/attempt, 60 giây/case, tối đa 1 retry.
- Usage response thiếu/sai, ledger sai, model sai, grant hết/revoke hoặc crash pending đều
  dừng case. Reservation/debit không được refund tự động.

## Decision packet trước GO-LIVE

Chưa được phép gọi API. Coordinator phải điền/xác nhận riêng:

| Mục | Đề xuất/Trạng thái |
|---|---|
| Railway service/máy thực thi | **CHƯA XÁC NHẬN** |
| Provider/model | OpenAI; exact `OPENAI_MODEL`/`JUDGE_LIVE_MODEL`: **CHƯA XÁC NHẬN** |
| LIVE calls tối đa | 3 cases/grant; 3 provider attempts/case; global lifetime 20 cases |
| Ngân sách USD tối đa | Reservation estimate: 0,01 USD/case, 0,20 USD/global; **không phải hard provider cap** |
| Token/concurrency | 24k input + 6k output/case; 2k output/attempt; 1/session, 2/global |
| Stop Conditions | usage/config/ledger sai; revoke/kill/HOLD; timeout; provider/auth/quota error; bất kỳ SEND/job |
| Rollback | `JUDGE_LIVE_ENABLED=0`, revoke grant, `LLM_MODE=replay`; không refund debit |

## Validation offline

- `tests/test_judge_input_live.py`: 10 passed (mock provider/SDK; LIVE/API = 0).
- Judge C1/C2-A/C2-C + C2-B portable subset: 158 passed, 3 Unix-only deselected.
- Restricted/Verify4 guard, OpenAI adapter, budget/observability, Core reliability, UI/audit,
  harness, no-over-escalation/no-fail-open: 138 passed.
- Black/Ruff: PASS. Full suite, Unix IPC smoke, LIVE quality, Railway/deploy: NOT RUN.

Không có secret/PII thật, API call, SMTP/Gmail/dispatch, deploy hoặc merge.
