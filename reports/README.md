# Chỉ mục báo cáo và bằng chứng

Các tài liệu trong thư mục này ghi lại kết quả tại từng checkpoint. Báo cáo lịch
sử không tự đại diện cho trạng thái `dev` hiện hành và không thay thế Task Contract,
`STATUS.md` hoặc quyết định nghiệm thu của Project Coordinator.

## Baseline LIVE lịch sử

- [`baseline_full15_live_2026-10-02.md`](baseline_full15_live_2026-10-02.md) — lượt
  baseline ban đầu; giữ để truy vết điều kiện và giới hạn tại thời điểm chạy.
- [`baseline_full15_live_actual_2026-10-02.md`](baseline_full15_live_actual_2026-10-02.md)
  — kết quả baseline thực tế sau khi phân biệt kế hoạch với lượt chạy đã xảy ra.
- [`full15_live_post_auth_fix_2026-10-02.md`](full15_live_post_auth_fix_2026-10-02.md)
  — kiểm tra tiếp theo sau thay đổi xác thực; đọc cùng hai baseline phía trên.

## Báo cáo checkpoint và regression

### M1 — Runtime reliability

- [`sprints/M1_runtime_reliability.md`](sprints/M1_runtime_reliability.md) — báo cáo
  tổng hợp M1 và liên kết đến evidence bất biến.
- [`sprints/M1_2_provider_observability.md`](sprints/M1_2_provider_observability.md)
  — checkpoint quan sát provider và telemetry.

### M2 — Decision quality và controlled execution

- [`sprints/M2_goal_progress.md`](sprints/M2_goal_progress.md) — tiến độ và lịch sử
  thực hiện M2; các đoạn cũ cần đọc theo ngày/checkpoint.
- [`sprints/M2_core_decision_escalation_quality.md`](sprints/M2_core_decision_escalation_quality.md)
  — baseline và kiểm tra chất lượng quyết định/chuyển tiếp.
- [`sprints/M2_COMBINED_DEV_PROBE_PREREG.md`](sprints/M2_COMBINED_DEV_PROBE_PREREG.md)
  — bằng chứng preregistration cho Combined DEV probe.
- [`sprints/M2_LIVE_BUDGET_RECONCILIATION.md`](sprints/M2_LIVE_BUDGET_RECONCILIATION.md)
  — đối soát ngân sách LIVE; dữ liệu máy đọc nằm tại
  [`sprints/M2_live_budget.json`](sprints/M2_live_budget.json).
- [`sprints/M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md`](sprints/M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md)
  — checkpoint closeout M2 và bàn giao sang giai đoạn tiếp theo.

### M3 — Human control và feedback

- [`sprints/M3_T02_FEASIBILITY_REPORT.md`](sprints/M3_T02_FEASIBILITY_REPORT.md) —
  nghiên cứu feasibility của adaptation; kết luận STOP không chứng minh adaptation
  đã được triển khai hoặc M3 đã PASS.

## Evidence nghiệm thu được lưu bất biến

- [`evidence/m1/README.md`](evidence/m1/README.md) — manifest, SHA-256 và cách đọc
  các JSON/console log cuối của Verify 4, Escalation 5 và Full 15.

Không sửa, đổi tên hoặc di chuyển các artifact trong `evidence/` chỉ để làm gọn
repository. Khi có kết quả mới, thêm báo cáo/checkpoint mới và liên kết vào chỉ mục
này thay vì viết lại bằng chứng lịch sử.
