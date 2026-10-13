# Kiểm chứng runtime hiện tại và các luồng trọng yếu của sản phẩm

## 1. Tóm tắt kết quả

**BLOCKED**. Ứng dụng khởi động được và cả sáu trang Streamlit đều hoạt động tại mốc mã đã kiểm thử. Tuy nhiên, chế độ `replay` với cơ sở dữ liệu cách ly không có cassette LLM khớp với các lời nhắc phát sinh. Vì vậy, tình huống thường và tình huống bắt buộc `AUTHORITY_REQUIRED` kết thúc ở `ERROR / TECHNICAL_ERROR` trước bước phân loại.

Theo Stop Condition của task, việc kiểm tra tiếp `FACT_UNRESOLVED`, duyệt cuối, gửi mô phỏng và khởi động lại đã dừng. Không có kết luận PASS cho những phần chưa được kiểm chứng.

Toàn bộ đầu vào là dữ liệu mô phỏng. **LIVE LLM/API/email = 0.**

## 2. Mốc mã và trạng thái trước khi chạy

| Hạng mục | Giá trị quan sát | Trạng thái |
|---|---|---|
| Repository | `ThanhVu165/MLAi_VNG_A` | PASS |
| SHA được kiểm thử chính xác | `95607f5d2f695bddcc1d0eac3a3d1e258e97fd97` | PASS |
| Branch | `codex/pytest-blocker-remediation` | PASS |
| `origin/dev` | `ed9d053e337dbd49314870eef4157f1fe27ca2ad` | PASS |
| Python | `.venv` của dự án, Python 3.11.9 | PASS |
| Chế độ runtime | `LLM_MODE=replay`, `LLM_CACHE=0`, Hugging Face và Transformers ở chế độ offline | PASS |
| Cấu hình nhà cung cấp | OpenAI, `gpt-6-luna`, reasoning `none`; `replay` được chọn trước khi có khả năng gọi nhà cung cấp | PASS |
| Trạng thái thư mục làm việc ban đầu | Không có thay đổi được Git theo dõi; có sẵn 10 file SQLite `-shm`/`-wal` chưa được theo dõi từ pytest | PASS, có giới hạn |
| Cơ sở dữ liệu mặc định | `data/app.db` đã tồn tại, kích thước 425.984 byte, nhưng không được mở trong lượt kiểm chứng | PASS |
| Trạng thái PR gần nhất | PR #42 là bản nháp đang mở; PR #41 đã merge; PR #40 là bản nháp đang mở | Thông tin tham chiếu |

Mốc khắc phục đã báo `610/610 PASS`. Đây là bằng chứng kiểm thử đơn vị và tích hợp của mốc mã, không được chạy lại trong task kiểm chứng runtime này.

## 3. Python và môi trường chạy

- Trình thông dịch: `.venv\Scripts\python.exe`.
- Phiên bản: Python 3.11.9.
- Các thư viện phụ thuộc được dùng từ `.venv` hiện có của repository.
- Không cài thêm gói và không thay đổi thư viện phụ thuộc.
- `HF_HUB_OFFLINE=1` và `TRANSFORMERS_OFFLINE=1` được đặt để ngăn truy cập mạng ngoài ý muốn.
- `LLM_CACHE=0` được đặt để không dùng bộ nhớ đệm che khuất kết quả `replay`.

## 4. Chế độ runtime

- `LLM_MODE=replay`.
- `LLM_PROVIDER=openai`.
- `OPENAI_MODEL=gpt-6-luna`.
- `OPENAI_REASONING_EFFORT=none`.
- Không có lời gọi LIVE tới LLM, API hoặc dịch vụ email.
- Khi lời nhắc cần LLM không có cassette tương ứng, hệ thống trả lỗi an toàn thay vì gọi nhà cung cấp hoặc dựng câu trả lời.

## 5. Cơ sở dữ liệu cách ly

- Đường dẫn: `%TEMP%/exodia-runtime-smoke-95607f5/app.db`.
- Kích thước sau lượt chạy: 237.568 byte.
- Đường dẫn này chưa tồn tại trước khi khởi động.
- Không sao chép hoặc tái sử dụng cơ sở dữ liệu mặc định, dữ liệu người dùng hay dữ liệu người tham gia.
- `run_local.py` gọi `ensure_seeded()`, khởi tạo cấu trúc dữ liệu bằng cơ chế hiện có và nạp sáu nguồn quy định mô phỏng.
- Không đặt lại, xóa hoặc ghi đè cơ sở dữ liệu cũ. Việc cách ly được thực hiện bằng một đường dẫn mới.

## 6. Lệnh khởi động

```powershell
$env:DATABASE_PATH = "$env:TEMP/exodia-runtime-smoke-95607f5/app.db"
$env:LLM_MODE = "replay"
$env:LLM_PROVIDER = "openai"
$env:OPENAI_MODEL = "gpt-6-luna"
$env:OPENAI_REASONING_EFFORT = "none"
$env:LLM_CACHE = "0"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
.\.venv\Scripts\python.exe run_local.py --server.address 127.0.0.1 --server.port 8511 --server.headless true --browser.gatherUsageStats false
```

## 7. Kết quả khởi động

- Tiến trình mở `http://127.0.0.1:8511` sau khoảng 10 giây.
- Streamlit khởi động thành công.
- Tiến trình xử lý nền nhận và xử lý được công việc trong hàng đợi.
- Khởi tạo cấu trúc dữ liệu và nạp dữ liệu mẫu hoàn tất.
- Không có traceback nghiêm trọng trong giai đoạn khởi động.
- Không có lời gọi LIVE ngoài ý muốn.

**Kết quả kiểm tra khởi động: PASS.**

## 8. Ma trận kiểm tra sáu trang giao diện

Kiểm tra được thực hiện bằng trình duyệt thật kết nối tới Streamlit đang chạy, không dùng Streamlit AppTest.

| Trang | Kết quả quan sát trong runtime | Trạng thái |
|---|---|---|
| Xử lý email | Biểu mẫu nhập liệu, ba mẫu nhanh, hộp thư mô phỏng và kết quả xử lý đều hiển thị được | PASS |
| Cần chuyên viên xử lý | Tình huống R1 xuất hiện cùng câu hỏi chuyển tiếp, tóm tắt bằng chứng và biểu mẫu quyết định của chuyên viên | PASS |
| Quy định & căn cứ | Sáu nguồn mô phỏng hiển thị được; năm nguồn đang áp dụng và một nguồn đã thay thế | PASS |
| Nhật ký kiểm toán | Tình huống và dòng thời gian sự kiện được đọc từ SQLite và hiển thị được | PASS, có vấn đề F-02 |
| Verify | Trang tải thành công; thao tác chạy thật tạo và hiển thị kết quả mới cho bốn tình huống | PASS |
| Đo lường | KPI trên cơ sở dữ liệu ít dữ liệu hiển thị được và ghi rõ `Đánh giá nội bộ · 0 LIVE API` | PASS |

**Kết quả giao diện runtime: 6/6 trang PASS.**

## 9. Kết quả tình huống thường

**FAIL**

- Đầu vào mô phỏng: tiêu đề `Hỏi hạn rút học phần kỳ 1`, người gửi `runtime.smoke@example.test`.
- Kỳ vọng: đi qua xử lý, quyết định, kết quả, lưu bền vững và kiểm toán mà không chuyển tiếp không cần thiết.
- Thực tế: `ERROR / TECHNICAL_ERROR`; không có loại chuyển tiếp, bản nháp hoặc câu trả lời.
- Log tiến trình nền: `Không đọc được cassette ... FileNotFoundError`, sau đó `Pipeline failed safely: Không có cassette hợp lệ cho prompt này.`
- Lưu bền vững: tình huống `c_01M4PCKVXT5T43GJ21JB289ZTY`, bốn sự kiện kiểm toán, không có bản nháp và không có quyết định chuyên viên.
- Kết quả an toàn: không tạo câu trả lời thiếu căn cứ và không gửi mô phỏng.

## 10. Kết quả FACT_UNRESOLVED

**NOT VERIFIED**

Không chạy sau khi tình huống bắt buộc `AUTHORITY_REQUIRED` không trả đúng loại dừng. Việc dừng tuân thủ Stop Condition. Trạng thái này không được diễn giải thành PASS hoặc FAIL cho hành vi `FACT_UNRESOLVED`.

## 11. Kết quả OUT_OF_POLICY

**PASS**

- Tình huống mô phỏng: đầu vào tương đương F02 bằng tiếng Nhật, `寮の申請方法と締切を教えてください。`.
- Kỳ vọng: `ESCALATE / OUT_OF_POLICY / R1` trước bước dùng LLM.
- Thực tế: `ESCALATE / OUT_OF_POLICY / R1`.
- Câu hỏi chuyển tiếp: chuyên viên có thể xử lý bằng ngôn ngữ gốc hay cần yêu cầu người gửi bổ sung bản dịch.
- Trạng thái cuối quan sát được: `HUMAN_DECIDED` sau thao tác của chuyên viên.
- Lưu bền vững và kiểm toán: tình huống `c_01M4PCP1KM8EJFEW4PNAFFTDPE`, một quyết định hệ thống, một quyết định chuyên viên và sáu sự kiện kiểm toán.
- Kết quả an toàn: không tạo câu trả lời quy định với mức tự tin sai.

## 12. Kết quả AUTHORITY_REQUIRED

**FAIL VÀ STOP**

- Đầu vào mô phỏng: `Xin phúc khảo quá hạn`, có yêu cầu xử lý ngoại lệ sau khi nhập viện.
- Kỳ vọng: `ESCALATE / AUTHORITY_REQUIRED / P01` cùng câu hỏi cho người có thẩm quyền.
- Thực tế: `ERROR / TECHNICAL_ERROR`, không có loại chuyển tiếp và không có câu hỏi chuyển tiếp.
- Trạng thái cuối: `ERROR`.
- Kiểm toán: ghi nhận lỗi trích xuất `Không có cassette hợp lệ cho prompt này`, sau đó lưu trạng thái dừng an toàn.
- Kết quả an toàn: hệ thống không tự quyết định thay người có thẩm quyền và không tạo câu trả lời thiếu căn cứ.

Đây là điều kiện kích hoạt Stop Condition của lượt kiểm chứng.

## 13. Kết quả phê duyệt của con người (human approval)

**FAIL**

Tình huống `OUT_OF_POLICY` xuất hiện trong hàng chờ thật. Qua giao diện, chuyên viên chọn `Yêu cầu bản dịch` và ghi lý do `Yêu cầu người gửi bổ sung bản dịch tiếng Việt hoặc tiếng Anh trước khi xử lý tiếp.` SQLite lưu được lựa chọn, lý do, người thao tác `HUMAN:local` và thời gian xem xét khoảng 31 giây.

Bước soạn bản nháp tiếp theo thất bại vì `replay` không có cassette khớp. Giao diện thông báo đúng rằng quyết định chuyên viên vẫn được giữ và chưa soạn được phản hồi. Không có bản xem trước, duyệt cuối, đối chiếu nội dung gửi hoặc hoàn tất gửi.

Không có trạng thái `SENT`. Không có email thật được gửi và cũng chưa đạt tới **SIMULATED SEND / DB STATE ONLY**.

## 14. Kết quả lưu bền vững (persistence)

| Nội dung kiểm tra | Quan sát | Trạng thái |
|---|---|---|
| Tình huống và kết quả | Bảy tình huống do runtime tạo cùng trạng thái cuối tồn tại trong cơ sở dữ liệu cách ly | PASS |
| Quyết định chuyên viên | Lựa chọn, lý do, người thao tác và thời gian xem xét còn nguyên sau khi chuyển trang và hiển thị lại | PASS |
| Duyệt cuối và gửi mô phỏng | Bước tạo bản nháp thất bại trước khi có bản xem trước hoặc `SENT` | NOT VERIFIED |
| Dữ liệu sau khi chuyển trang | Tình huống chuyển tiếp và quyết định chuyên viên vẫn tồn tại khi rời trang rồi mở lại | PASS |

**Kết quả persistence trong phạm vi toàn luồng bắt buộc: FAIL.** Các trạng thái trung gian đã quan sát được lưu đúng.

## 15. Kết quả kiểm toán (audit)

**PASS, có vấn đề F-02.**

Trang Nhật ký kiểm toán và truy vấn SQLite chỉ đọc đều trả về hành động, thời gian, quy tắc và lý do có ý nghĩa. Số lượng hành động kiểm toán sau khi dừng:

| Hành động | Số lượng |
|---|---:|
| `CASE_RECEIVED` | 7 |
| `CASE_SANITIZED` | 7 |
| `CASE_QUEUED` | 2 |
| `CASE_ERROR` | 13 |
| `HUMAN_DECISION` | 1 |
| `VERIFY_RUN_STARTED` | 1 |
| `VERIFY_RUN_FINISHED` | 1 |

Nhật ký ghi rõ việc thiếu cassette, `TECHNICAL_ERROR`, quyết định của chuyên viên và việc giữ quyết định khi tạo bản nháp thất bại.

## 16. Kết quả Verify

**PASS cho tính đúng đắn của trang và thao tác; kết quả bộ tình huống là 0/4.**

Nút `Chạy kiểm thử` gọi pipeline runtime và tạo một kết quả mới cho bốn tình huống trong khoảng 0,3 giây. Trang hiển thị `0 PASS / 4 FAIL`; V01–V04 đều có kết quả `ERROR / TECHNICAL_ERROR`. Phần chi tiết trình bày rõ kết quả kỳ vọng và kết quả thực tế.

Trang không trình bày fixture tất định hoặc kết quả lịch sử như kết quả vừa chạy. Thao tác và cách biểu diễn đạt PASS, nhưng bộ Verify được thực thi không có tình huống nào đạt vì thiếu cassette.

## 17. Kết quả Đo lường

**PASS**

Trang hiển thị được từ cơ sở dữ liệu cách ly dù dữ liệu còn ít. Tại thời điểm quan sát, trang hiển thị một email đã tiếp nhận, `0.0% AUTO_REPLY`, `0.0% ESCALATE` và nhãn `Đánh giá nội bộ · 0 LIVE API`.

Dữ liệu quan sát là **OFFLINE / REPLAY / SYNTHETIC** và không được trình bày như bằng chứng LIVE.

## 18. Kết quả khởi động lại (restart)

**SKIP**

Không khởi động lại sau khi tình huống `AUTHORITY_REQUIRED` thiếu loại dừng mong đợi và kích hoạt Stop Condition. Tiến trình được dừng sau khi thu thập bằng chứng; cổng 8511 đã được xác nhận đóng. Không suy diễn kết quả persistence qua lần khởi động lại.

## 19. Vấn đề phát hiện

### F-01 — Chế độ replay không hoàn tất được luồng sản phẩm bắt buộc

- Mức độ: **Cao, chặn kiểm chứng**.
- Cách tái hiện: khởi động với cơ sở dữ liệu mới và `LLM_MODE=replay`, sau đó gửi tình huống thường hoặc tình huống cần thẩm quyền qua trang Xử lý email.
- Thực tế: `infra.llm` không tìm thấy file khớp trong `tests/cassettes`; `core.pipeline` lưu `ERROR / TECHNICAL_ERROR` trước bước phân loại.
- Ảnh hưởng: không thể kiểm chứng offline tình huống thường, `FACT_UNRESOLVED`, `AUTHORITY_REQUIRED`, bản xem trước của bản nháp, duyệt cuối, gửi mô phỏng và persistence qua khởi động lại tại mốc mã này.
- Phạm vi liên quan: đầu vào replay của `infra/llm.py` và đường xử lý runtime trong `core/pipeline.py`.
- Task này không sửa mã nguồn, policy, fixture hoặc cấu trúc dữ liệu.

### F-02 — Tóm tắt trang kiểm toán mô tả tình huống lỗi như đã tự động hoàn tất

- Mức độ: **Trung bình, ảnh hưởng độ chính xác của báo cáo runtime**.
- Cách tái hiện: sau khi tình huống thường kết thúc ở `ERROR`, mở trang Nhật ký kiểm toán.
- Thực tế: trang hiển thị `Tự động xử lý 1 (100%)` với chú thích `Đã hoàn tất tự động`, trong khi chính trang đó hiển thị trạng thái tình huống là `Chưa xử lý được` và dòng thời gian `TECHNICAL_ERROR`.
- Ảnh hưởng: phần tóm tắt có thể trình bày quá mức số tình huống tự động xử lý thành công.
- Phạm vi liên quan: phép tính hoặc cách trình bày tóm tắt tại trang Nhật ký kiểm toán.

## 20. Phân loại kết quả kiểm chứng

| Phạm vi | Kết quả |
|---|---|
| Kiểm thử đơn vị và tích hợp tại mốc khắc phục | 610/610 PASS, không chạy lại trong task này |
| Kiểm tra khởi động | PASS |
| Giao diện runtime | PASS, 6/6 trang |
| Luồng tình huống thường | FAIL |
| FACT_UNRESOLVED | NOT VERIFIED |
| OUT_OF_POLICY | PASS |
| AUTHORITY_REQUIRED | FAIL |
| Human approval | FAIL |
| Persistence | FAIL trong phạm vi toàn luồng bắt buộc |
| Audit | PASS, có F-02 |
| Trang và thao tác Verify | PASS; kết quả vừa chạy là 0/4 |
| Đo lường | PASS |
| Restart | SKIP |

## 21. Lệnh đã chạy

Các lệnh kiểm tra trước khi chạy và kiểm tra GitHub:

```powershell
git branch --show-current
git rev-parse HEAD
git rev-parse origin/dev
git status --short
.\.venv\Scripts\python.exe --version
gh pr list --repo ThanhVu165/MLAi_VNG_A --state all --limit 10 --json number,title,state,isDraft,headRefName,baseRefName,headRefOid,updatedAt,url
gh pr view 40 --repo ThanhVu165/MLAi_VNG_A --json number,state,isDraft,headRefName,baseRefName,headRefOid,updatedAt,url
```

Cơ sở dữ liệu được mở bằng SQLite URI `mode=ro` khi thu thập bằng chứng. Không có câu lệnh SQL thay đổi dữ liệu để tạo trạng thái PASS.

## 22. Vị trí log và bằng chứng

- Cơ sở dữ liệu cách ly: `%TEMP%/exodia-runtime-smoke-95607f5/app.db`, chỉ tồn tại cục bộ và không commit.
- Log Streamlit và tiến trình nền: được thu từ phiên runtime cục bộ; có lỗi thiếu cassette, trạng thái dừng an toàn và lỗi tạo bản nháp.
- Báo cáo này: `reports/readiness/CURRENT_RUNTIME_SMOKE.md`.

## 23. Rủi ro và giới hạn còn lại

- PR #40 không thay đổi và không được kiểm thử trong task này. Head quan sát được là `a7acf60a64fded8835d82ed4291ab0f10eab831b`, base `dev`, trạng thái bản nháp đang mở.
- Branch được kiểm thử có thay đổi khắc phục khả năng chạy pytest trên nhiều môi trường nhưng không thay đổi logic runtime.
- Repository không có file đã commit trong `tests/cassettes` khớp với các lời nhắc runtime. Tạo cassette, đổi hành vi runtime, dùng secret hoặc chuyển sang LIVE đều vượt phạm vi task kiểm chứng này.
- Không dùng Gold private, Set A/B, dữ liệu người dùng, secret hoặc email thật.
- Thay đổi sản phẩm, mã nguồn, kiểm thử và cấu trúc dữ liệu: **không có**.
- Báo cáo chưa commit hoặc push vì kết quả là BLOCKED và task yêu cầu Coordinator chỉ đạo trước khi công bố báo cáo BLOCKED.

## 24. Kết luận readiness trong phạm vi task

Mốc `95607f5d2f695bddcc1d0eac3a3d1e258e97fd97` **chưa sẵn sàng để được xác nhận hoàn tất runtime smoke** trong chế độ offline/replay hiện tại. Khởi động và sáu trang giao diện đạt yêu cầu tải cơ bản; chốt `OUT_OF_POLICY` không cần LLM hoạt động đúng; trang kiểm toán và Đo lường đọc được dữ liệu mô phỏng. Tuy nhiên, thiếu cassette khớp làm hỏng tình huống thường, `AUTHORITY_REQUIRED` và bước tạo bản nháp sau quyết định chuyên viên.

Kết quả cuối cùng của task là **BLOCKED**. Cần Coordinator xem xét F-01 và quyết định task riêng cho cassette replay đã được duyệt hoặc khắc phục runtime. Không merge và không đánh dấu DONE từ báo cáo này.
