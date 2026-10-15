# Judge LIVE session reference — UI fix — 2026-10-16

## Kết quả và phạm vi ủy quyền

Owner: Ponytail / Codex. Công việc cardless theo **COORDINATOR APPROVAL — JUDGE LIVE
SESSION REFERENCE UI FIX**. Trạng thái implementation: **READY_FOR_REVIEW**.
Production acceptance/deploy: **HOLD**, chờ xác minh trực tiếp production và authorization
deployment riêng. Không tự merge/deploy hoặc kích hoạt thêm tester.

Nguyên văn phạm vi Coordinator duyệt:

> - Giữ nguyên `prepare_session()` và authentication/session binding.
> - Chuyển phần hiển thị reference vào khối `st.info` hoặc container ổn định ngay sau page header, trước hướng dẫn sử dụng.
> - Reference chỉ dùng để đối chiếu phiên, không hiển thị grant/issuer secret.
> - Không sửa gateway, provider, policy, budget, schema hoặc audit actions.
> - Thêm regression qua `streamlit_app.py` và `st.navigation`, không chỉ `AppTest.from_file()`.

## Baseline và provenance

- `git fetch origin --prune`: exit 0.
- Verified `origin/dev`: `b8c031180e12546b24789c8238338f3fab46ab49`, merge PR #77.
- Branch: `codex/judge-session-reference-ui-fix`, tạo từ baseline trên.
- Code/test commit: `04393278dd7fe38da9f5acd6fb13209cb594e2a6`.
- Final handoff SHA gồm báo cáo được xác định bằng commit chứa file này và output bàn giao.
- Checkout gốc có `outputs/`, `reports/evaluation/M7_SET_B_PREPARATION_20261015.md`,
  `reports/sprints/FINAL_DEPLOY_PREFLIGHT_20261015.md` chưa commit; giữ nguyên toàn bộ.
  Worktree cô lập được dùng cho patch, không reset/clean/stash hay ghi đè artifact.

Coordinator xác nhận production thuộc `exodia-restricted-demo / production / exodia-web`,
project ID tham chiếu `d0c599c4-395a-474d-95df-4636a96934e5`; source SHA theo evidence
gần nhất là `b8c031180e12546b24789c8238338f3fab46ab49`.

**Chưa xác minh trực tiếp SHA đang chạy:** Railway connector trên máy này chỉ thấy project
`sweet-perfection` và hai service cũ, không phải Exodia production. Read-only inventory đã
được đối chiếu và loại khỏi provenance production. Không thay cấu hình/deploy project đó,
không yêu cầu secret hoặc đổi tài khoản/project. Ponytail cần bàn giao read-only deployment
evidence từ máy có quyền Exodia Railway trước deployment acceptance.

## Thay đổi và chẩn đoán

Trước sửa, trang Email hiển thị reference qua `st.caption` trước CSS/header. Bản sửa chỉ
giữ giá trị trả về từ lần gọi `prepare_session()` hiện hữu và render bằng `st.info` ngay sau
page header, trước `_render_first_time_guidance()`. Khi gateway không cấu hình, không có
reference được render. Nhánh gateway lỗi vẫn dừng fail-closed như baseline.

Diff production: chỉ `pages/1_Xu_ly_email.py`, 4 dòng thêm/1 dòng xóa. `prepare_session()`,
gateway, binding, grant/quota/revoke, provider, policy, budget, schema, audit và dispatch
không đổi. Không thêm widget cấp quyền hoặc dữ liệu credential vào UI.

Regression mới trong `tests/test_judge_input_c2b.py` khởi chạy `streamlit_app.py`, dùng
`st.navigation` và `StreamlitPage.run()` thật. AppTest 1.39 tạo PagesManager thiếu ScriptCache,
khiến page.run thực thi bytecode rỗng; test chỉ bổ sung `get_page_script_byte_code` bằng
ScriptCache thật trong harness, không mock router/Page/run hoặc sửa framework. AppTest dùng
cùng literal session ID cho browser giả lập, nên seam server-context đã có được giữ để
phân biệt session; đây không phải bằng chứng WebSocket production. Test native reconnect
hiện hữu kiểm tra bổ sung qua WebsocketSessionManager/BrowserWebSocketHandler thật.

## Validation và commands

Môi trường: macOS 26.6 arm64, Python 3.11.17, Streamlit 1.39.0; SQLite tạm synthetic.
`OPENAI_API_KEY` bị đặt rỗng trong test; conftest chặn network và OpenAI SDK. Không dùng
credential thật. C2-B happy-path dùng replay/provider double có sẵn; provider thật: **0**.
Test mới còn ép `infra.llm.call_json` fail ngay nếu guest flow chạm LLM.

Trong các lệnh dưới, `PY` là executable có sẵn (không cài dependency):

```text
/Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A/.venv/bin/python
```

| Command/check | Kết quả |
|---|---|
| `PY -m pytest -q -p no:cacheprovider tests/test_judge_input_c2b.py::test_navigation_shows_guest_session_reference_in_stable_info` trên UI baseline, test cuối dùng router thật | EXPECTED FAIL — reference không nằm trong info đầu tiên; 1 failed in 0.41s |
| Cùng regression sau fix | PASS; nằm trong final selection dưới |
| `PY -m pytest -q -p no:cacheprovider tests/test_judge_input_c2b.py tests/test_ui_baseline_integration.py::test_navigation_preserves_all_six_pages` | PASS — **16 passed in 2.04s**, exit 0 |
| `PY -m black --check --line-length 100 pages/1_Xu_ly_email.py tests/test_judge_input_c2b.py` | PASS — 2 files unchanged, exit 0 |
| `PY -m ruff check --no-cache pages/1_Xu_ly_email.py tests/test_judge_input_c2b.py` | PASS — all checks passed, exit 0 |
| `git diff --check` | PASS — exit 0 |
| Full suite, LIVE/API, deployment, merge | NOT RUN theo scope |

Lượt chạy đầu trong sandbox có 14 PASS/1 FAIL vì không bind được AF_UNIX; chạy lại ngoài
sandbox theo approval cho đúng test Unix đã PASS. Ruff cache cũng bị sandbox chặn; final
check dùng `--no-cache` và PASS. Không sửa gateway/test expectations để che lỗi môi trường.
Shell không có alias `python`; mọi kết quả chính thức dùng Python 3.11 executable ở trên.

## Acceptance evidence

| AC | Evidence và giới hạn |
|---|---|
| Guest thấy 16 hex | PASS offline: regex `[0-9a-f]{16}`, info xuất hiện đúng một lần, thứ tự header → reference → hướng dẫn; production browser NOT RUN |
| Reference khớp registry | PASS offline: giá trị render bằng `_BINDINGS` và operator `sessions` response |
| Guest chưa provision bị chặn | PASS: submit email synthetic mới báo chưa bật, không case/job/SEND, `call_json` không được gọi |
| Session khác không dùng grant | PASS C2-B: forged credential/query/session-state bị từ chối, Audit ownership isolation; native active/inactive known-ID reconnect cần approval mới |
| Không provider/job/send | PASS: provider/network thật 0; không job/SEND trong C2-B assertions; thành công synthetic đi PREVIEW_READY qua replay double |
| Browser smoke sau deploy | NOT RUN — cần merge được duyệt và authorization deployment riêng |

## Self-review và handoff

- Đã review toàn diff; chỉ email UI, dedicated C2-B tests và báo cáo này thay đổi.
- UI render reference không phải credential; grant/session secret và issuer secret không
  xuất hiện trong rendered text được test. Không thêm authentication/session contract.
- Sửa assertion test cũ từ caption sang info; mở rộng secret scan của test sang info.
- Native reconnect, permissions/socket local, invalid operator secret, revoke, quota,
  cross-session read và no-dispatch targeted checks vẫn PASS.
- Đây là evidence offline; chưa chứng minh bug biến mất trên production hoặc xác minh trực
  tiếp deployed SHA. Không dùng kết quả này để tự thông qua merge/deploy.

NEXT STEP: Coordinator review PR nhắm `dev`; Ponytail cung cấp read-only production SHA
evidence. Sau merge được duyệt, chờ authorization deployment riêng rồi browser smoke guest
để đối chiếu mã 16 hex và registry, không tự cấp tester grant hoặc gọi OpenAI.

LIVE/API: **0**. DEPLOY: **NOT RUN**. MERGE: **NOT RUN**.
