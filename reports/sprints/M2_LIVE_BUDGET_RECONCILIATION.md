# M2 — Đối soát ngân sách LIVE và đề xuất baseline

Ngày lập theo client: 2026-10-09 (Asia/Saigon). OFFLINE ONLY.
RESULT: M2_BUDGET_RECONCILIATION_READY. BASELINE_UNRESOLVED. Không phải ledger/phê duyệt.
Branch: sprint/m2-core-decision-escalation-quality; HEAD: 67d6028a1a6804e7db5c0c34dafccf9dd8b5352d.

## A. Phạm vi ngân sách

Tổng 45 theo task Coordinator, M2_goal_progress.md và TOTAL_BUDGET trong verify/m2_live_budget.py.
Mốc Goal được progress ghi: 2026-10-07T19:16:34.2127687+07:00, starting HEAD 67d6028.
Progress mục R7 POST-FIX ghi rõ prior baseline observations không cộng lại. Vì vậy phân loại
M2 trước mốc Goal riêng, không cộng tất cả LIVE từng chạy vào quota này. Cần Coordinator xác nhận scope này.
Một observation là một independent invocation đã bắt đầu, có fresh identity. Technical failure
vẫn là một attempted observation; không cần semantic result để debit. Transport retries,
R7 repair calls hoặc skipped provider attempts không tạo independent observation.
Case ID/trace ID + artifact run phân biệt observation; label A3-clean-1 có thể được dùng lại
ở baseline và post-fix với UUID/thời điểm khác. Provider calls không đồng nghĩa observations.

## B. Danh mục bằng chứng

- reports/sprints/M2_goal_progress.md: scope/start/history và R7 claim; secondary, không authoritative current count.
- reports/sprints/M2_core_decision_escalation_quality.md: lịch sử baseline/controls; secondary; phần đầu cũ không đại diện current state.
- verify/m2_live_budget.py; verify/M2_DEV_EXECUTION.md: accounting contract, không evidence consumption.
- AGENT.md; PROJECT_SPEC.md: workflow/technical distinction; không chứa current budget approval.
- 9 manifest.json có config LLM_MODE=live trong data/validation; metadata nguồn, không đọc secrets.
- 34 observation.json + 9 canonical summary rows: 43 M2 candidate records; chỉ trích metadata, không copy raw LLM output.
- R7 post-fix dev.db/cases/case_results: persisted result identity và timestamps; primary.
- SQLite được mở URI mode=ro&immutable=1, không tạo WAL/checkpoint/sidecar. DB có WAL chỉ dùng base-file metadata
  hỗ trợ, không coi là complete latest snapshot; JSON là nguồn chính cho các runs trước Goal.
- Toàn bộ data/**/*.db được inventory metadata; không DB unreadable. Sau Goal tìm 3 R7 rows và
  204 case rows trong offline test basetemps (diagnostic/phase1/2c/stale-contract/pre-request suites).
  Timestamp/case row không tự chứng minh LIVE. Các suites này được progress/task offline ghi nhận;
  không nâng test fixture rows thành independent LIVE observations.
- 61 run_summary.json trong validation đều run_mode=OFFLINE_MOCK: 347 case rows (không phải 347 unique LIVE).
- M1/full15/manual-live root artifacts và M1.4/M1.5/M1.6 DBs được inventory: metadata thời gian trước Goal;
  không cộng bản before.db hoặc nhiều report vào consumption. Không công bố tổng LIVE M1 từ số DB rows.
- Git log report: baseline archive 9e23f4b (2026-10-06T14:25:17+07:00), B1 archive baa385e
  (2026-10-06T17:35:21+07:00), progress commit 67d6028 (2026-10-07T19:12:49+07:00).

### SHA-256 các nguồn trọng yếu

| Source | SHA-256 |
| --- | --- |
| reports/sprints/M2_goal_progress.md | ef7c91c6cb088cf818325b1c230b72aabe1c62be9dd78b32f1defae6ae536324 |
| reports/sprints/M2_core_decision_escalation_quality.md | cf11e4edb9f1af9658fd1f399b9aa9bc63a7080b446ca61ae293ea529d9ca587 |
| data/validation/m2_r7_postfix_live_20261008_040014/manifest.json | 4ea2406d6b9db5b9e7dda4a2ee7ca03cbc31590c1480efbce94081c5d94d131e |
| data/validation/m2_r7_postfix_live_20261008_040014/assessment.json | fc894c65cf8032ca4cc8de258aff083ad2a3a04a94aa55e33a78e0a62e908075 |
| data/validation/m2_r7_postfix_live_20261008_040014/summary.json | be494ca70607ddca9f2b02d6995ddea38de92011a970580d14d53b52cad813b5 |
| data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-1/observation.json | 46b41b4f4d542376a6d0db5d243225a9fffaac296d1efc89174b177912a61578 |
| data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-2/observation.json | 1cf929a7d0814a8893ad0c635020f7736ed6043b5557f83d0c47f1cd58e172a8 |
| data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-3/observation.json | dc960e063bb22b86ceba3e4d18da2b660c8020dd33b6e8cc28f7c47103d8b1d4 |
| data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-1/dev.db | f445265d64b99583fddccbf0e1584a74f1d40f303a70b1bcc28aa2d45d9d6c90 |
| data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-2/dev.db | 71eac5333636a275047da552f9b3e6612243a00cf7d9207fcc4977cd1b5b824a |
| data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-3/dev.db | 455f9c874ab249f001deffc3868197d1c9e40ebc7f7884bbbe3c8935a37f36a3 |

## C. Bảng đối soát từng observation

Thời gian dưới đây là started_at từ persisted result/JSON khi có; giữ offset gốc.
UNAVAILABLE nghĩa không có exact observation start; không suy từ directory name, received_at,
file mtime hoặc ULID. Hai direct controls không có pipeline trace/start; run_started.json chỉ là
run-level bound: 2026-10-06T15:07:34.735274+07:00 và 2026-10-06T17:20:13.401662+07:00.

| Observation (run/label) | Case / actual identity | Thời gian bắt đầu | Kết quả | Số lần tính M2 Goal | Evidence | Trạng thái xác minh |
| --- | --- | --- | --- | --- | --- | --- |
| m2_r7_postfix_live_20261008_040014/A3-clean-1 | A3-clean; c_01M4C2NF8ZRWKWY16H14W18X0N | 2026-10-07T21:00:16.543269+00:00 | P01 | 1 | data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-1/observation.json | VERIFIED_IN_GOAL |
| m2_r7_postfix_live_20261008_040014/A3-clean-2 | A3-clean; c_01M4C2P2MB5EV6QFN6HJ8QCZ7W | 2026-10-07T21:00:36.363321+00:00 | P01 | 1 | data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-2/observation.json | VERIFIED_IN_GOAL |
| m2_r7_postfix_live_20261008_040014/A3-clean-3 | A3-clean; c_01M4C2PK2KG25M9GE4EJ7VWFHN | 2026-10-07T21:00:53.203305+00:00 | P01 | 1 | data/validation/m2_r7_postfix_live_20261008_040014/A3-clean-3/observation.json | VERIFIED_IN_GOAL |
| m2_2_targeted_live_20261006_024148_bc6d53fd/E04 | E04; c_01M46SCCP1X1K528HHF0Z12H6H | 2026-10-05T19:41:49.633184+00:00 | TECHNICAL | 0 | data/validation/m2_2_targeted_live_20261006_024148_bc6d53fd/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_2_targeted_live_20261006_025456_887c1029/E01 | E01; c_01M46T4V0HPY55SP9JJMYVKX4J | 2026-10-05T19:55:10.737530+00:00 | P05 | 0 | data/validation/m2_2_targeted_live_20261006_025456_887c1029/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_2_targeted_live_20261006_025456_887c1029/E04 | E04; c_01M46T4DJVA0N461DR2Q5AEA51 | 2026-10-05T19:54:56.987900+00:00 | P03 | 0 | data/validation/m2_2_targeted_live_20261006_025456_887c1029/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_2_targeted_live_20261006_025456_887c1029/E05 | E05; c_01M46T50FW6X7T6QAA0EMRXAAY | 2026-10-05T19:55:16.348743+00:00 | P01 | 0 | data/validation/m2_2_targeted_live_20261006_025456_887c1029/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_b1_postfix_live_20261006_150548/B1-postfix-1 | B1-postfix-1; c_01M4841XFHD4VJXF5R0EH5KAEJ | 2026-10-06T08:07:35.153885+00:00 | P02 | 0 | data/validation/m2_b1_postfix_live_20261006_150548/B1-postfix-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_b1_postfix_live_20261006_150548/B1-postfix-2 | B1-postfix-2; c_01M4842ASZK9Z0X6N46QJCJDVX | 2026-10-06T08:07:48.799733+00:00 | P02 | 0 | data/validation/m2_b1_postfix_live_20261006_150548/B1-postfix-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_b1_postfix_live_20261006_150548/B1-postfix-3 | B1-postfix-3; c_01M4842KJCENKHD5DHWYWQ25G2 | 2026-10-06T08:07:57.772564+00:00 | P02 | 0 | data/validation/m2_b1_postfix_live_20261006_150548/B1-postfix-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_b1_postfix_live_20261006_150548/supported-duration-control | supported-duration-control; control-340063d478984b64a327d105d143f97a | UNAVAILABLE | TECHNICAL | 0 | data/validation/m2_b1_postfix_live_20261006_150548/supported-duration-control/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_b1_supported_duration_control_v2_live_20261006_171921/supported-duration-control-v2 | supported-duration-control-v2; control-5dac8f8e5a6e4d0dab06fcc1d01bde33 | UNAVAILABLE | CONTROL_ACCEPTED | 0 | data/validation/m2_b1_supported_duration_control_v2_live_20261006_171921/supported-duration-control-v2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-clean-1 | A3-clean; c_01M47ZYQY51A2Q41TAJE7X2S98 | 2026-10-06T06:55:56.869660+00:00 | TECHNICAL | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-clean-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-clean-2 | A3-clean; c_01M4801Z4BQQ16GWCKAEJMN7VF | 2026-10-06T06:57:42.539783+00:00 | P01 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-clean-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-clean-3 | A3-clean; c_01M48048V6MC3A9J4D4XEDN5QV | 2026-10-06T06:58:58.022712+00:00 | TECHNICAL | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-clean-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-neg-1 | A3-neg; c_01M47ZVQQ6Z8DB911TRC6JQK2Z | 2026-10-06T06:54:18.342907+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-neg-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-neg-2 | A3-neg; c_01M47ZW6T9KMSZ2E3T7ENJC2DF | 2026-10-06T06:54:33.801716+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-neg-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-neg-3 | A3-neg; c_01M47ZWHA19WZM490H2KEZF5ST | 2026-10-06T06:54:44.545398+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-neg-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-no-diacritic-1 | A3-no-diacritic; c_01M48004RBJ1ZTVG7TG065R8T8 | 2026-10-06T06:56:42.763821+00:00 | P01 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-no-diacritic-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-no-diacritic-2 | A3-no-diacritic; c_01M4802C2Z6EVN671A3K2WB8HZ | 2026-10-06T06:57:55.807818+00:00 | P01 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-no-diacritic-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/A3-no-diacritic-3 | A3-no-diacritic; c_01M4805MKMHNAMATMBZYRKWNHM | 2026-10-06T06:59:42.836951+00:00 | P01 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/A3-no-diacritic-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B2-claim-1 | B2-claim; c_01M47ZWTYHN2Z317QC0NGCW76R | 2026-10-06T06:54:54.417782+00:00 | P02 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B2-claim-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B2-claim-2 | B2-claim; c_01M47ZXE2X2F6M6V8FS0NDZXJB | 2026-10-06T06:55:14.013086+00:00 | P02 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B2-claim-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B2-claim-3 | B2-claim; c_01M47ZXWCKACJY84PDDHHVH2NP | 2026-10-06T06:55:28.659108+00:00 | P02 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B2-claim-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-1 | B3-chat-abbreviation; c_01M4800YH0E60MMX5PF5ZNQBBE | 2026-10-06T06:57:09.152752+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-2 | B3-chat-abbreviation; c_01M480414KFX88R04TECQDVAYW | 2026-10-06T06:58:50.131818+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-3 | B3-chat-abbreviation; c_01M48064XB0CSDVEE4XH6YPZRX | 2026-10-06T06:59:59.531142+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B3-clean-1 | B3-clean; c_01M4800Q4P81SSE24KNSCRC2ZA | 2026-10-06T06:57:01.590992+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B3-clean-1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B3-clean-2 | B3-clean; c_01M4803R3E6D5J8K4XCTXS0RE1 | 2026-10-06T06:58:40.878414+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B3-clean-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_baseline_live_20261006_065338_utc/B3-clean-3 | B3-clean; c_01M4805Y1N0WBS6CFQFA5NF6MW | 2026-10-06T06:59:52.501983+00:00 | P05 | 0 | data/validation/m2_baseline_live_20261006_065338_utc/B3-clean-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_final_escalation5_live_20261006_080948_ef333650/E01 | E01; c_01M47C4ZBFB3YBX0DBTXEMGQTX | 2026-10-06T01:09:49.551659+00:00 | P05 | 0 | data/validation/m2_final_escalation5_live_20261006_080948_ef333650/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_final_escalation5_live_20261006_080948_ef333650/E02 | E02; c_01M47C5B8V9A6TK72C01H1Z2TE | 2026-10-06T01:10:01.755832+00:00 | P05 | 0 | data/validation/m2_final_escalation5_live_20261006_080948_ef333650/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_final_escalation5_live_20261006_080948_ef333650/E03 | E03; c_01M47C5HWV7Z3ZJYSC01WXQYZQ | 2026-10-06T01:10:08.539684+00:00 | P05 | 0 | data/validation/m2_final_escalation5_live_20261006_080948_ef333650/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_final_escalation5_live_20261006_080948_ef333650/E04 | E04; c_01M47C5RC6TXKR4HDNN39A71MQ | 2026-10-06T01:10:15.174299+00:00 | P03 | 0 | data/validation/m2_final_escalation5_live_20261006_080948_ef333650/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| m2_final_escalation5_live_20261006_080948_ef333650/E05 | E05; c_01M47C63GAB83TZTAHE9M66T8X | 2026-10-06T01:10:26.570563+00:00 | P01 | 0 | data/validation/m2_final_escalation5_live_20261006_080948_ef333650/summary.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_b1_repeats_20261006_1c38225/B1-repeat-2 | B1; c_01M47WKPRQJC3S0DFYCKKRGDNM | 2026-10-06T05:57:29.495166+00:00 | P02 | 0 | data/validation/step5_b1_repeats_20261006_1c38225/B1-repeat-2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_b1_repeats_20261006_1c38225/B1-repeat-3 | B1; c_01M47WM0F3WDMPMS7PV1FST8XT | 2026-10-06T05:57:39.427541+00:00 | P02 | 0 | data/validation/step5_b1_repeats_20261006_1c38225/B1-repeat-3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_screening_20261006_1c38225/A1 | A1; c_01M47VVMJ86D2SR1GZNGMJKYKY | 2026-10-06T05:44:20.808961+00:00 | P03 | 0 | data/validation/step5_screening_20261006_1c38225/A1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_screening_20261006_1c38225/A2 | A2; c_01M47VW1QQEZVKYQ9WFRF6N5PE | 2026-10-06T05:44:34.295346+00:00 | P05 | 0 | data/validation/step5_screening_20261006_1c38225/A2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_screening_20261006_1c38225/A3 | A3; c_01M47VW995EN2NGKV90JXE5KKM | 2026-10-06T05:44:42.021225+00:00 | P01 | 0 | data/validation/step5_screening_20261006_1c38225/A3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_screening_20261006_1c38225/B1 | B1; c_01M47VWP98MTZMK62MC07J9MM2 | 2026-10-06T05:44:55.336453+00:00 | P02 | 0 | data/validation/step5_screening_20261006_1c38225/B1/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_screening_20261006_1c38225/B2 | B2; c_01M47VWYPMS4X1VNRXGVQG6SJW | 2026-10-06T05:45:03.956371+00:00 | P02 | 0 | data/validation/step5_screening_20261006_1c38225/B2/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |
| step5_screening_20261006_1c38225/B3 | B3; c_01M47VVAKWR0WSXAY6DVNC2TAY | 2026-10-06T05:44:10.620847+00:00 | P05 | 0 | data/validation/step5_screening_20261006_1c38225/B3/observation.json | PRE_GOAL_EXCLUDED_PENDING_SCOPE_CONFIRMATION |

### R7 post-fix — identity, provider và attempts

| Label | Case ID | Trace ID | Provider/model | STARTED | Transport retries | R7 repair calls |
| --- | --- | --- | --- | --- | --- | --- |
| A3-clean-1 | c_01M4C2NF8ZRWKWY16H14W18X0N | c4b1de69-a0a7-4af6-a66c-b8cf8b38748e | openai/gpt-6-luna | 4 | 0 | 1 |
| A3-clean-2 | c_01M4C2P2MB5EV6QFN6HJ8QCZ7W | f746e4aa-8726-4726-a9b3-e172514fff74 | openai/gpt-6-luna | 4 | 0 | 1 |
| A3-clean-3 | c_01M4C2PK2KG25M9GE4EJ7VWFHN | 8e190c13-aacd-4316-a043-8c69bcb2eafa | openai/gpt-6-luna | 4 | 0 | 1 |

Cả 3: ESCALATE/AUTHORITY_REQUIRED/P01, AWAITING_HUMAN, semantic PASS, technical=false.
Observation JSON, summary và progress là các views của cùng 3 observations, không phải 9.
12 distinct call_ids, 4 steps/observation (R2_extract, R4_select, R7_question, R7_question_repair),
attempt_index=1 toàn bộ, 0 skipped. Ba repair calls không phải ba observations bổ sung.

### Attempts của các observations trước Goal (không debit Goal)

| Observation | Provider STARTED | Transport retry attempts thực chạy | Skipped |
| --- | --- | --- | --- |
| m2_2_targeted_live_20261006_024148_bc6d53fd/E04 | [] | UNAVAILABLE | UNAVAILABLE |
| m2_2_targeted_live_20261006_025456_887c1029/E04 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4DJVA0N461DR2Q5AEA51', 'trace_id': None, 'call_id': '6a5f87526a70414f96890ea71f1d361d', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 4200, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.97724290000042, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3263, 'prompt_hash12': '07eb14b0c7ba', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4DJVA0N461DR2Q5AEA51', 'trace_id': None, 'call_id': '7fa7a430197347838bd6cf75253177d4', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 2905, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 55.66421199997421, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 11386, 'prompt_hash12': 'c9f2080a6425', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4DJVA0N461DR2Q5AEA51', 'trace_id': None, 'call_id': '6e66b007ffdc44348d097425f8f1431c', 'step': 'R7_question', 'attempt_index': 1, 'elapsed_ms': 3172, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 52.636018400022294, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2376, 'prompt_hash12': '07a49d33c6eb', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4DJVA0N461DR2Q5AEA51', 'trace_id': None, 'call_id': '4db52233ba3a466790b6c5c1bcb26921', 'step': 'R7_question_repair', 'attempt_index': 1, 'elapsed_ms': 3055, 'effective_timeout_s': 30, 'attempts_remaining_before': 1, 'attempts_remaining_after': 0, 'remaining_case_time_s': 49.442833899986, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2596, 'prompt_hash12': 'de1570f8b586', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_2_targeted_live_20261006_025456_887c1029/E01 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4V0HPY55SP9JJMYVKX4J', 'trace_id': None, 'call_id': '58a22f6437fc4b07bd793ea6d63a4844', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 2031, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.96896349999588, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3263, 'prompt_hash12': 'c27ad14ba8a4', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4V0HPY55SP9JJMYVKX4J', 'trace_id': None, 'call_id': '6549148cc54e4c22bd34cf9c8e52d830', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 1659, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 57.87031399999978, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 11621, 'prompt_hash12': '69256a5dfd0e', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T4V0HPY55SP9JJMYVKX4J', 'trace_id': None, 'call_id': '66965f055b934e1bb0955475211b41c5', 'step': 'R7_generate', 'attempt_index': 1, 'elapsed_ms': 1582, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 56.15582370001357, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2189, 'prompt_hash12': 'a2976458970a', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_2_targeted_live_20261006_025456_887c1029/E05 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M46T50FW6X7T6QAA0EMRXAAY', 'trace_id': None, 'call_id': 'f8a6c24c790e42b0b61275cb9b01c03b', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 2515, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.96932850003941, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3319, 'prompt_hash12': 'e25c735a45b9', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T50FW6X7T6QAA0EMRXAAY', 'trace_id': None, 'call_id': 'c804cb0a8ca34f0293f870bb6e10404a', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 1957, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 57.37148560001515, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 16539, 'prompt_hash12': '7fd664889775', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T50FW6X7T6QAA0EMRXAAY', 'trace_id': None, 'call_id': '05be36b283d64e81a177a71748125b52', 'step': 'R7_question', 'attempt_index': 1, 'elapsed_ms': 3379, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 55.336465500004124, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3076, 'prompt_hash12': '9b1f63ddb2b0', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M46T50FW6X7T6QAA0EMRXAAY', 'trace_id': None, 'call_id': '94dad0ea9b7b480ea5ad7c38d6204691', 'step': 'R7_question_repair', 'attempt_index': 1, 'elapsed_ms': 2505, 'effective_timeout_s': 30, 'attempts_remaining_before': 1, 'attempts_remaining_after': 0, 'remaining_case_time_s': 51.929813000024296, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3296, 'prompt_hash12': '7d2314c7ee86', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_b1_postfix_live_20261006_150548/B1-postfix-1 | 3 | 0 | 0 |
| m2_b1_postfix_live_20261006_150548/B1-postfix-2 | 3 | 0 | 0 |
| m2_b1_postfix_live_20261006_150548/B1-postfix-3 | 3 | 0 | 0 |
| m2_b1_postfix_live_20261006_150548/supported-duration-control | 2 | 0 | 0 |
| m2_b1_supported_duration_control_v2_live_20261006_171921/supported-duration-control-v2 | 1 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-clean-1 | 4 | 1 | 2 |
| m2_baseline_live_20261006_065338_utc/A3-clean-2 | 4 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-clean-3 | 4 | 0 | 1 |
| m2_baseline_live_20261006_065338_utc/A3-neg-1 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-neg-2 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-neg-3 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-no-diacritic-1 | 4 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-no-diacritic-2 | 4 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/A3-no-diacritic-3 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B2-claim-1 | 4 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B2-claim-2 | 4 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B2-claim-3 | 4 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-1 | 4 | 1 | 0 |
| m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-2 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B3-chat-abbreviation-3 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B3-clean-1 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B3-clean-2 | 3 | 0 | 0 |
| m2_baseline_live_20261006_065338_utc/B3-clean-3 | 3 | 0 | 0 |
| m2_final_escalation5_live_20261006_080948_ef333650/E01 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M47C4ZBFB3YBX0DBTXEMGQTX', 'trace_id': None, 'call_id': '341ade83afed458588efdd1f4243ab29', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 4787, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.9719934000168, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3263, 'prompt_hash12': 'c27ad14ba8a4', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C4ZBFB3YBX0DBTXEMGQTX', 'trace_id': None, 'call_id': 'ea887d5907e3402587811ed90c0e0904', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 2991, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 55.06460949999746, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 11609, 'prompt_hash12': '3b85956b18d6', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C4ZBFB3YBX0DBTXEMGQTX', 'trace_id': None, 'call_id': '677d4efc055347839b3a6857be554488', 'step': 'R7_generate', 'attempt_index': 1, 'elapsed_ms': 4016, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 51.99219550000271, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2435, 'prompt_hash12': 'd8a3ad1ac0cb', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_final_escalation5_live_20261006_080948_ef333650/E02 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5B8V9A6TK72C01H1Z2TE', 'trace_id': None, 'call_id': '2b4f10c4e5234cce8731ca51ee1cbfcf', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 2482, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.96356239996385, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3251, 'prompt_hash12': '59246788364b', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5B8V9A6TK72C01H1Z2TE', 'trace_id': None, 'call_id': '89d7814f01ff46dc99b98aa14f3afe3a', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 2027, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 57.388111000007484, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 16198, 'prompt_hash12': 'f4a534dda91f', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5B8V9A6TK72C01H1Z2TE', 'trace_id': None, 'call_id': 'ea4e05ca6af446f8916b9def430860c8', 'step': 'R7_generate', 'attempt_index': 1, 'elapsed_ms': 1865, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 55.27971719997004, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3065, 'prompt_hash12': 'b56dc5ec2e02', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_final_escalation5_live_20261006_080948_ef333650/E03 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5HWV7Z3ZJYSC01WXQYZQ', 'trace_id': None, 'call_id': '3f78bf8668a54c419ab5200a7f830fdd', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 2173, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.97083899995778, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3250, 'prompt_hash12': '5b123deeb11e', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5HWV7Z3ZJYSC01WXQYZQ', 'trace_id': None, 'call_id': 'ca8ff7b04b3e40c5b5841f7aad1b36a4', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 2144, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 57.73340119997738, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 11296, 'prompt_hash12': 'fad734d501e2', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5HWV7Z3ZJYSC01WXQYZQ', 'trace_id': None, 'call_id': 'ee56da292e2e41d79a5f7ee23ba0fd24', 'step': 'R7_generate', 'attempt_index': 1, 'elapsed_ms': 1988, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 55.53284060000442, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2275, 'prompt_hash12': '4bdbbe9d9d59', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_final_escalation5_live_20261006_080948_ef333650/E04 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5RC6TXKR4HDNN39A71MQ', 'trace_id': None, 'call_id': '6ede0749592d478fb6a4a1a21d2ecaa1', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 1984, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.97234130004654, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3263, 'prompt_hash12': '07eb14b0c7ba', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5RC6TXKR4HDNN39A71MQ', 'trace_id': None, 'call_id': '247fa1019af94036a80b6a9a2fbced40', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 2235, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 57.908407300012186, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 11386, 'prompt_hash12': 'c9f2080a6425', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5RC6TXKR4HDNN39A71MQ', 'trace_id': None, 'call_id': '3fa48238fd354ae9a2670d600e80d0b4', 'step': 'R7_question', 'attempt_index': 1, 'elapsed_ms': 2480, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 55.5949254000443, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2373, 'prompt_hash12': '733b42e0bc7e', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C5RC6TXKR4HDNN39A71MQ', 'trace_id': None, 'call_id': '94c43df0275c423285b810985912f168', 'step': 'R7_question_repair', 'attempt_index': 1, 'elapsed_ms': 4313, 'effective_timeout_s': 30, 'attempts_remaining_before': 1, 'attempts_remaining_after': 0, 'remaining_case_time_s': 53.09898080001585, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2593, 'prompt_hash12': 'bb339790e45f', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| m2_final_escalation5_live_20261006_080948_ef333650/E05 | [{'event': 'llm_provider_attempt', 'case_id': 'c_01M47C63GAB83TZTAHE9M66T8X', 'trace_id': None, 'call_id': 'd335913f90634ef0aef2ae171faad1d5', 'step': 'R2_extract', 'attempt_index': 1, 'elapsed_ms': 2318, 'effective_timeout_s': 30, 'attempts_remaining_before': 4, 'attempts_remaining_after': 3, 'remaining_case_time_s': 59.971502500004135, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 3319, 'prompt_hash12': 'e25c735a45b9', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C63GAB83TZTAHE9M66T8X', 'trace_id': None, 'call_id': 'b461dbe069e5453cba7a8636b9366993', 'step': 'R4_select', 'attempt_index': 1, 'elapsed_ms': 2044, 'effective_timeout_s': 30, 'attempts_remaining_before': 3, 'attempts_remaining_after': 2, 'remaining_case_time_s': 57.56160880002426, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 16475, 'prompt_hash12': 'fd0c0604637c', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C63GAB83TZTAHE9M66T8X', 'trace_id': None, 'call_id': '8aa93043fe114e268364204914ad8428', 'step': 'R7_question', 'attempt_index': 1, 'elapsed_ms': 2908, 'effective_timeout_s': 30, 'attempts_remaining_before': 2, 'attempts_remaining_after': 1, 'remaining_case_time_s': 55.43972130003385, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2600, 'prompt_hash12': 'edd87932e3d6', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}, {'event': 'llm_provider_attempt', 'case_id': 'c_01M47C63GAB83TZTAHE9M66T8X', 'trace_id': None, 'call_id': 'e4f473d769b54d4c8d0311d3fcc4e0e1', 'step': 'R7_question_repair', 'attempt_index': 1, 'elapsed_ms': 2948, 'effective_timeout_s': 30, 'attempts_remaining_before': 1, 'attempts_remaining_after': 0, 'remaining_case_time_s': 52.514577399997506, 'model': 'gpt-6-luna', 'provider': 'openai', 'prompt_chars': 2820, 'prompt_hash12': '3943a585e2e1', 'success': True, 'retryable': False, 'will_retry': False, 'retry_backoff_ms': 0, 'stop_reason': None}] | UNAVAILABLE | UNAVAILABLE |
| step5_b1_repeats_20261006_1c38225/B1-repeat-2 | 3 | 0 | 0 |
| step5_b1_repeats_20261006_1c38225/B1-repeat-3 | 3 | 0 | 0 |
| step5_screening_20261006_1c38225/A1 | 4 | 0 | 0 |
| step5_screening_20261006_1c38225/A2 | 3 | 0 | 0 |
| step5_screening_20261006_1c38225/A3 | 4 | 0 | 0 |
| step5_screening_20261006_1c38225/B1 | 3 | 0 | 0 |
| step5_screening_20261006_1c38225/B2 | 3 | 0 | 0 |
| step5_screening_20261006_1c38225/B3 | 3 | 0 | 0 |

Các canonical summary counter không có đủ per-attempt index để suy retry count; giữ UNAVAILABLE.
Pre-request credential-failure E04 đã attempted harness invocation nhưng không nhận R2 LIVE response;
không coi đó là semantic PASS hay zero independent attempt chỉ vì không có provider request.
Technical trước Goal gồm credential E04, baseline A3-clean-1/A3-clean-3 và control v1.
Nếu Coordinator mở rộng scope về trước Goal, phải tính lại các attempts này; không loại technical.

## D. Tổng hợp ngân sách

- Tổng theo contract: 45.
- VERIFIED_IN_GOAL có primary evidence: 3 independent observations; 0 technical; 12 provider STARTED.
- Transport retries thuộc 3 observations này: 0; R7 repair logical calls: 3, không tính riêng.
- M2 candidate attempts trước Goal: 40 (gồm 4 technical); count vào Goal hiện đề xuất 0 theo scope được progress ghi.
- Historical M1/root LIVE artifacts: ngoài phạm vi; không dùng số report/DB copies để ước lượng observation total.
- Offline/mock: 61 bundles / 347 case rows, LIVE debit 0. Không merge reused synthetic IDs với real results.
- Không tìm thêm identifiable in-Goal LIVE row trong inventory local ngoài 3 R7; số lượt thiếu evidence/off-repo
  không thể định lượng. Đây KHÔNG phải assertion có 0 observations bị thất lạc.
- Baseline consumed tối thiểu được evidence xác nhận: 3. Exact current consumed và remaining: UNVERIFIED.
- Không công bố 42 remaining như giá trị đã xác minh. Không có authoritative ledger.

## E. Đề xuất Baseline

BASELINE_UNRESOLVED

Không tạo JSON PROPOSED hoặc M2_live_budget.json, không điền confirmed_by/confirmed_at.
Có đủ evidence cho 3 R7 observations, nhưng chưa đủ chứng minh completeness của consumption
từ Goal start tới lúc lập báo cáo: chưa có accounting ledger/per-attempt durable registry hoặc
coordinator confirmation về scope và mọi runs ngoài local worktree. Không tìm thấy evidence không
có nghĩa là không phát sinh LIVE. Giá trị 3 là verified subtotal/lower bound, không tự phê duyệt baseline.

## F. Quyết định cần Coordinator xác nhận

1. Xác nhận contract 45 bắt đầu tại Goal start nêu trên và không cộng lại historical baseline/controls/M1.
2. Xác nhận có hay không thêm independent LIVE attempts, aborted/technical invocations hoặc runs trên
   workspace/host khác sau Goal start, đặc biệt sau 2026-10-08T04:01:05.968655+07:00.
   Nếu có, cần metadata artifact/IDs/start/status/attempt linkage; không cần raw provider payload.
3. Review những offline test basetemps chỉ có DB rows và các missing exact timestamps của historical
   direct controls nếu scope được mở rộng; không infer mode từ tên thư mục hoặc ngày received_at.
4. Anti review độc lập inventory/dedup/scope. Chỉ sau review và coordinator reconciliation confirmation
   mới được task riêng tạo authoritative ledger. Task hiện tại không bật LIVE hoặc sửa verifier.

## Validation và trạng thái Git

Đối chiếu unique case/trace IDs, per-attempt case_id/call_id và counters R7: PASS.
Historical label collision A3-clean-* không bị tính trùng với post-fix; underlying case IDs khác.
Đọc SQLite immutable: WAL completeness limitation giữ nguyên, không checkpoint/mutate evidence.
Sensitive review: report chỉ metadata/status/paths/hashes, không raw input, exception/provider payload hay credentials.
Fixture final-byte SHA-256: d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04 (MATCH).
git diff --check: PASS. Không rerun pytest hoặc pipeline. LIVE/API trong task=0.
Chỉ thêm báo cáo này; dirty worktree có trước được giữ. Không commit/push/merge/tag.
NEXT: Anti review độc lập, sau đó Coordinator xem xét xác nhận baseline.
