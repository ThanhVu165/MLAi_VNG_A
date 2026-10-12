# M2 offline artifact handoff

Ngày kiểm kê: 2026-10-12 (Asia/Saigon)
Coordinator decision: cho phép đọc cục bộ các đường dẫn dưới đây để tiếp tục readiness offline. Không cấp quyền LIVE.

## Kết luận

- Không có `tests/cassettes/` trong checkout hiện tại. Con số `116` trong hồ sơ M2 là `116 PASS / 0 FAIL / 0 SKIP` của bộ kiểm thử offline, không phải 116 cassette.
- Có 9 capture M2 LIVE gốc ở `data/validation/m2_dev_live_probe_01` đến `m2_dev_live_probe_09`.
- Các capture ghi rõ `LLM_MODE=live`, `LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-6-luna`, observation ID, trace ID và fixture SHA-256.
- Capture là bằng chứng đầu ra và telemetry. Chúng không chứa đầy đủ response trung gian theo định dạng cassette keyed by prompt hash, nên không được đổi tên/copy trực tiếp thành cassette replay. Việc dựng cassette phải là task riêng có review và provenance.
- `data/validation/` bị `.gitignore` loại trừ, do đó các capture chỉ tồn tại trong workspace cục bộ này và không có provenance theo Git object. SHA-256 dưới đây là mốc toàn vẹn tại thời điểm kiểm kê.

## Capture inventory

| Run / case | Observation / trace | Capture SHA-256 |
| --- | --- | --- |
| `m2_dev_live_probe_01 / M2DEV-A1` | `live_m2_dev_live_probe_01_M2DEV-A1` / `ab418007-53da-4f01-a52d-21b93fe7752c` | `411b191cf0ef7fdad273f7b270fac18dd098b88507b5d941919c8b8298a23480` |
| `m2_dev_live_probe_02 / M2DEV-A4` | `live_m2_dev_live_probe_02_M2DEV-A4` / `90b54865-0566-4725-9b54-81429d9b48eb` | `ddd281c0e0368c41391d40799994077eb6489841b2821a90ce3cde6ea403eb39` |
| `m2_dev_live_probe_03 / M2DEV-A4` | `live_m2_dev_live_probe_03_M2DEV-A4` / `7df943cb-ddd9-4f27-a0de-9c29401f608c` | `b5dfa108bb7beac8417acc2b61328a07605dbd53362970d85ba3dc9b4c066810` |
| `m2_dev_live_probe_04 / M2DEV-B1` | `live_m2_dev_live_probe_04_M2DEV-B1` / `3cc57630-ef17-49db-a1e0-1ddbe51fe468` | `268e586ac07d250c0035e5a6e8ac001fd22787d8c20744c34ad113b0c4b7b587` |
| `m2_dev_live_probe_05 / M2DEV-B4` | `live_m2_dev_live_probe_05_M2DEV-B4` / `4faa66bd-5eb9-4be3-9983-aca22e378839` | `9449dc7385535aeaddbc1851841c2e9dfc530ba5fc4769060ca4efea9f6d50c5` |
| `m2_dev_live_probe_06 / M2DEV-B3` | `live_m2_dev_live_probe_06_M2DEV-B3` / `4c52b338-8399-48ca-995c-cc30ce3d8b91` | `1e01863ec58b36836886b90531fe0897f96750b27990ebe9234187b93bf05910` |
| `m2_dev_live_probe_07 / M2DEV-A2` | `live_m2_dev_live_probe_07_M2DEV-A2` / `e4bc463e-0796-4902-986c-bb64c3a482fa` | `a8b0b0eb4f6f8ae83c293e76823fea75da6e08d742a27c55e90d29d06802845f` |
| `m2_dev_live_probe_08 / M2DEV-A4` | `live_m2_dev_live_probe_08_M2DEV-A4` / `6dc9b5e8-e17b-4621-96f3-7fb5595a761f` | `1a59fb2b2873c1873a58f328602e631f17d639597d8d09e9cddb08aeed83ce11` |
| `m2_dev_live_probe_09 / M2DEV-B4` | `live_m2_dev_live_probe_09_M2DEV-B4` / `01ad5c0b-7569-4bc7-b5c3-1ec9d5ce9866` | `4181f55bce09849f3ef7c8a8c4864d98e053daf49327d7d7ebc3923f35822a29` |

Mỗi capture nằm tại:

`data/validation/<run>/cases/<case>/capture.json`

Manifest của mỗi run nằm tại:

`data/validation/<run>/live_manifest.json`

## Provenance bổ sung

- Checkout khi kiểm kê: branch `codex/sprint2-doc-consistency`, HEAD `aac7bb62df380c3ea2eb8b02bc2180f0dd96e3b0`.
- Báo cáo Git-tracked mô tả 116 test offline và provenance M2: `reports/sprints/M2_goal_progress.md`.
- Báo cáo Git-tracked đối soát các run/capture M2: `reports/sprints/M2_LIVE_BUDGET_RECONCILIATION.md`.
- Commit gần nhất chạm hai báo cáo trên: `2a9bc6db8cc4f6e5bf2563f8499bcacf68c884f7` (`2026-10-09T05:13:32+07:00`, `feat(m2): checkpoint controlled Combined DEV execution`).

## Phạm vi cho phép

Cho phép đọc các capture, manifest và báo cáo nêu trên để kiểm kê, xác minh và thiết kế khôi phục offline. Không cho phép gọi provider, dùng secret, chạy `LLM_MODE=live`, hoặc tuyên bố các capture hiện tại là cassette replay đã được duyệt.
