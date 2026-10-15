# UX-RESPONSIVE-CARDLESS — Responsive & App Shell UX

## Thông tin thực hiện

- Owner: Thu — Windows
- Task ID: `UX-RESPONSIVE-CARDLESS`
- Authorization: yêu cầu trực tiếp của Coordinator/user trong phiên ngày 2026-10-15; user chỉ định bỏ qua bước kiểm tra Trello.
- Branch: `codex/ux-responsive-cardless`
- Baseline đã xác minh: `origin/dev@a6f3b7c7c564cb7bde13e124eb03f121eca0a114`
- Final implementation SHA: `14a98e6ff6c3176ddc16c4854959157eecc16695`
- PR: cập nhật sau khi push/mở PR; target `dev`.
- LIVE/API calls: **0**

## Preflight

- Đã đọc `AGENT.md`, `docs/TEAM_WORKFLOW.md`, `PROJECT_SPEC.md`, `STATUS.md`,
  `docs/SPRINT_ROADMAP.md`, `docs/RUNBOOK.md` và các UI/presentation tests liên quan.
- `git fetch origin dev` xác nhận remote `dev` vẫn đúng reference baseline `a6f3b7c...`.
- PR #60 đã merge vào `dev` tại `53b6ad3...`; PR #62 đã merge vào `dev` tại
  `a6f3b7c...`. File của PR #62 không giao với scope hiện tại.
- Branch ban đầu là `sprint/m4-t02-official-set-a`, working tree chỉ có `.codex_tmp/` và
  `outputs/` untracked. Hai thư mục này được bảo toàn và không đưa vào commit.
- Tạo `codex/ux-responsive-cardless` trực tiếp từ `origin/dev`; không reset, clean, stash,
  force-push, clone hoặc tạo worktree phụ.
- Kiểm tra Trello được bỏ qua theo chỉ dẫn trực tiếp của user. Ownership Thu và Task ID được
  dùng theo authorization trong yêu cầu này; không phát hiện giao file với Mac/Lenovo.

## Files changed

- `streamlit_app.py`: nạp CSS dùng chung cho app shell; mô tả Restricted DEMO chính xác;
  giữ nguyên tập menu và điều kiện runtime hiện hành.
- `ui/presentation.py`: responsive container/sidebar/columns/card/KPI/badge/typography,
  wrapping cho text/control và horizontal overflow nội bộ cho table/dataframe.
- `tests/test_ux_responsive_cardless.py`: regression cho responsive CSS và Restricted DEMO
  shell bằng Streamlit AppTest.
- `reports/sprints/UX_RESPONSIVE_CARDLESS.md`: preflight, validation, viewport evidence và
  owner self-review.

Không sửa page thuộc owner khác, routing, permission, Core, Policy, DB, worker, health,
runtime contract hoặc business logic.

## Acceptance evidence

| AC | Kết quả | Evidence |
| --- | --- | --- |
| AC1 — menu đúng theo runtime mode | PASS | Điều kiện menu `restricted_demo` giữ nguyên; navigation regression nằm trong bộ 160 tests; smoke Restricted DEMO hiển thị đúng bốn mục cho phép. |
| AC2 — không regression startup/navigation/access guard | PASS | `160 passed`; gồm baseline integration, Restricted DEMO, navigation, AppTest và guards. |
| AC3 — desktop 1440px | PASS | Browser smoke viewport CDP chính xác 1440px; `body/html scrollWidth=1440`, sidebar 320px, không có phần tử vượt viewport. |
| AC4 — mobile 390px và table overflow | PASS | Browser smoke viewport CDP chính xác 390px; trang không overflow ngang; sidebar mở rộng 288px và đọc/thao tác được; Verify dataframe có `clientWidth=346`, `scrollWidth=361`, tức cuộn ngang nội bộ thay vì làm tràn trang. |
| AC5 — không ảnh hưởng logic/permission | PASS | Diff giới hạn ở shell/presentation/tests/report; guard regression PASS; không mở lại controls bị khóa. |
| AC6 — evidence/tests/SHA/self-review/report | PASS | Evidence và hash bên dưới; implementation SHA `14a98e6...`; self-review đã hoàn tất. |

## Validation

Môi trường: Windows, Python 3.11.9 trong `.venv`, Streamlit 1.39.0,
`APP_MODE=restricted_demo`, `LLM_MODE=replay`, `LLM_CACHE=0`,
`HF_HUB_OFFLINE=1`; database test tách biệt trong `.codex_tmp/`. Không có LIVE/API call.

| Lệnh | Kết quả |
| --- | --- |
| `.venv\\Scripts\\python.exe -m pytest -q --basetemp=.codex_tmp/ux-responsive-cardless/pytest-targeted tests/test_ux_responsive_cardless.py` | PASS — 2 passed |
| `.venv\\Scripts\\python.exe -m pytest -q --basetemp=.codex_tmp/ux-responsive-cardless/pytest-regression tests/test_ux_responsive_cardless.py tests/test_presentation.py tests/test_ui_baseline_integration.py tests/test_restricted_demo.py tests/test_pre_m4_ux.py tests/test_email_input_ui.py tests/test_guards.py tests/test_ui_cleanup_phase2.py tests/test_ui_repository_cleanup_phase1.py` | PASS — 160 passed, 1 Altair deprecation warning không thuộc diff |
| `.venv\\Scripts\\python.exe -m black --check --line-length 100 streamlit_app.py ui/presentation.py tests/test_ux_responsive_cardless.py` | PASS — 3 files unchanged |
| `.venv\\Scripts\\python.exe -m ruff check streamlit_app.py ui/presentation.py tests/test_ux_responsive_cardless.py` | PASS |
| `git diff --check` | PASS |

Lần chạy pytest đầu tiên dùng temp mặc định gặp lỗi quyền truy cập thư mục temp Windows trước
khi thu test. Chạy lại với `--basetemp` nằm trong workspace đã PASS; đây là lỗi môi trường,
không phải regression sản phẩm.

## Browser evidence

Ảnh evidence được giữ local dưới `.codex_tmp/ux-responsive-cardless/` và không commit để
tuân thủ strict four-file scope.

| Viewport | File | SHA-256 | Quan sát |
| --- | --- | --- | --- |
| Before desktop | `before-1440.png` | `CDD4124F2D8FA37EFB190EDF5ED14E2B86845B8C58CE4A69A0CAE60B3E38B8D9` | Shell cũ ghi “Hệ thống hoạt động”, chưa nói email LIVE không hoạt động. |
| Before mobile | `before-390-v2.png` | `651B057E7F0E36222CB8F8E6460D90364898E913DF09E63C7F152C0C7B9100E7` | Nội dung mobile bị cắt theo chiều ngang. |
| After desktop 1440 | `after-1440-final.png` | `B2242A79C7E3A396D426D20BAA8555BC6B584F19ECB8CADC63F5102853B4F1` | Shell Restricted DEMO chính xác, không page overflow. |
| After mobile 390 | `after-390-final-v2.png` | `01D92A800D96964F00CCFF60E3D178F770A669FD6AF3F384690166DE8D4C2B1C` | Content/card/button wrap và xếp cột, `body/html scrollWidth=390`. |
| After mobile sidebar | `after-390-sidebar-final-v2.png` | `EC2E2ABA94205B13A20A046CEB46C962DDC0A8A99984B62FD0D3C68F3354FADA` | Sidebar rộng 288px trong viewport 390px; navigation/status đọc được và nút đóng khả dụng. |
| After mobile table | `after-390-table-final-v2.png` | `767C47FF2B9D7AE9A9833D6812BA8E249C5B21153BF169CF2C1FBA122CB2CFF6` | Verify dataframe cuộn ngang nội bộ; trang vẫn `scrollWidth=390`. |

Browser smoke dùng local Streamlit headless tại `127.0.0.1`, Microsoft Edge headless và
Chrome DevTools Protocol để đặt/đo viewport thực. Không gọi provider hoặc dịch vụ LIVE.

## Owner self-review

- Menu list và access guard không đổi; biến `restricted_demo` chỉ tránh đọc mode lặp lại.
- CSS chỉ tác động presentation, có breakpoint 640px và không gắn logic vào viewport.
- Sidebar dùng native Streamlit drawer: khi đóng nằm hoàn toàn ngoài canvas; khi mở overlay
  288px là hành vi native và control đóng vẫn nhìn thấy.
- Table/dataframe overflow nằm trong component; page không có horizontal overflow.
- Text dài, badge, caption và button đều wrap; KPI/card không còn fixed-height trên mobile.
- Restricted DEMO nói rõ replay offline/synthetic, không mailbox, không email thật và không
  provider LIVE; không tạo khả năng gửi mới.
- Không có secret trong diff; `.codex_tmp/` và `outputs/` không staged.

## Risks

- CSS phụ thuộc `data-testid` của Streamlit 1.39.0; khi nâng Streamlit cần chạy lại visual
  smoke ở 1440px/390px.
- Browser smoke tập trung app shell và Verify table, không chụp từng trạng thái dữ liệu của
  mọi page; phần còn lại được bao phủ bởi AppTest/regression suite.
- PR chưa merge và chưa deploy theo stop condition.
