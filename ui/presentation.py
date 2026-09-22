"""Ngôn ngữ hiển thị; mã lưu trữ chỉ xuất khi tải dữ liệu kiểm tra."""

from __future__ import annotations

import re
from datetime import datetime

from infra.db import to_local

STATUS_LABELS = {
    "RECEIVED": "Đã tiếp nhận",
    "PROCESSING": "Đang xử lý",
    "INVALID_INPUT": "Cần bổ sung email",
    "PENDING_SEND": "Sắp gửi phản hồi",
    "SENT": "Đã gửi (mô phỏng)",
    "CANCELLED": "Đã hủy gửi",
    "AWAITING_HUMAN": "Cần chuyên viên xử lý",
    "HUMAN_DECIDED": "Đã có quyết định",
    "PENDING_APPROVAL": "Chờ duyệt nội dung gửi",
    "RESOLVED": "Đã giải quyết",
    "NEEDS_RECHECK": "Cần đối chiếu quy định mới",
    "ERROR": "Chưa xử lý được",
    "ACTIVE": "Đang áp dụng",
    "PENDING_REVIEW": "Chờ duyệt",
    "SUPERSEDED": "Đã được thay thế",
    "REJECTED": "Không sử dụng",
}
TYPE_LABELS = {
    "FACT_UNRESOLVED": "Cần bổ sung thông tin",
    "OUT_OF_POLICY": "Chưa đủ căn cứ để trả lời",
    "AUTHORITY_REQUIRED": "Cần người có thẩm quyền quyết định",
}
ACTION_LABELS = {
    "CASE_RECEIVED": "Tiếp nhận email",
    "CASE_SANITIZED": "Đọc và làm sạch email",
    "FACTS_EXTRACTED": "Ghi nhận nội dung yêu cầu",
    "PREPOLICY_LOCKED": "Kiểm tra thẩm quyền",
    "EVIDENCE_RETRIEVED": "Tìm quy định liên quan",
    "EVIDENCE_VALIDATED": "Đối chiếu căn cứ",
    "POLICY_DECIDED": "Chọn cách xử lý",
    "DRAFT_GENERATED": "Soạn phản hồi",
    "GROUNDEDNESS_FAILED": "Phản hồi chưa đủ căn cứ",
    "QUESTION_GENERATED": "Đặt câu hỏi cho chuyên viên",
    "QUESTION_GUARD_FAILED": "Câu hỏi cần làm rõ",
    "CASE_QUEUED": "Chuyển cho chuyên viên",
    "CASE_RESUMED": "Tiếp tục xử lý",
    "CASE_RESOLVED": "Hoàn tất yêu cầu",
    "CASE_ERROR": "Ghi nhận sự cố xử lý",
    "SEND_SCHEDULED": "Lên lịch gửi phản hồi",
    "SEND_DISPATCHED": "Gửi phản hồi mô phỏng",
    "CANCEL_SEND": "Hủy gửi phản hồi",
    "CORRECTION_CREATED": "Tạo thư đính chính",
    "HUMAN_DECISION": "Chuyên viên quyết định",
    "HUMAN_APPROVED_SEND": "Chuyên viên duyệt gửi",
    "HUMAN_REJECTED_DRAFT": "Trả lại nội dung phản hồi",
    "EXPLAIN_REQUESTED": "Xem giải thích",
    "PAUSE_AUTOMATION": "Tạm dừng tự động",
    "RESUME_AUTOMATION": "Tiếp tục tự động",
    "OVERRIDE_DECISION": "Điều chỉnh cách xử lý",
    "RERUN_CASE": "Xử lý lại email",
    "SOURCE_UPLOADED": "Tiếp nhận quy định",
    "SOURCE_METADATA_EDITED": "Cập nhật thông tin quy định",
    "CHUNK_LABELLED": "Điều chỉnh quyền sử dụng cũ",
    "ACTIVATE_SOURCE": "Đưa quy định vào sử dụng",
    "REJECT_SOURCE": "Không sử dụng quy định",
    "SUPERSEDE_SOURCE": "Thay thế quy định",
    "ROLLBACK_SOURCE": "Khôi phục quy định",
    "FLAG_NEEDS_RECHECK": "Yêu cầu đối chiếu lại",
    "SOURCE_RECHECKED": "Kiểm tra cập nhật quy định",
    "VERIFY_RUN_STARTED": "Bắt đầu kiểm tra hệ thống",
    "VERIFY_RUN_FINISHED": "Kết thúc kiểm tra hệ thống",
}


def status_label(value: str) -> str:
    return STATUS_LABELS.get(value, "Đang chờ cập nhật")


def decision_label(value: str, escalation_type: str | None = None) -> str:
    if value == "AUTO_REPLY":
        return "Tự động trả lời"
    if value == "ESCALATE":
        return TYPE_LABELS.get(escalation_type or "", "Cần chuyên viên xử lý")
    return "Chưa xử lý được" if value == "ERROR" else "Cần bổ sung email"


def local_time(value: str | datetime | None) -> str:
    if not value:
        return "Chưa có thời điểm"
    try:
        timestamp = value.isoformat() if isinstance(value, datetime) else value
        return datetime.fromisoformat(to_local(timestamp)).strftime("%H:%M:%S ngày %d/%m/%Y")
    except ValueError:
        return "Thời điểm chưa xác định"


def actor_label(value: str) -> str:
    if value == "SYSTEM":
        return "Hệ thống"
    if value.startswith("ADMIN:"):
        return "Người quản trị"
    return "Chuyên viên"


def readable_text(text: str) -> str:
    """Ẩn mã nội bộ trong thông báo; không dùng để sửa dữ liệu gốc."""
    failures = {
        "citation_ratio": "một số nội dung chưa được dẫn nguồn",
        "citation": "trích dẫn chưa đủ hoặc không còn phù hợp",
        "number": "số liệu chưa có căn cứ",
        "authority": "nội dung có thể vượt thẩm quyền",
        "human_decision": "chưa giữ đúng quyết định và lý do của chuyên viên",
        "empty": "chưa có đủ tiêu đề và nội dung",
    }
    for code, message in failures.items():
        text = text.replace(f"groundedness_failed:{code}", f"Phản hồi cần kiểm tra vì {message}.")
    for technical, label in {**STATUS_LABELS, **TYPE_LABELS}.items():
        text = text.replace(technical, label)
    replacements = {
        "Ground Guard": "kiểm tra căn cứ",
        "groundedness_failed": "Phản hồi chưa đủ căn cứ",
        "metadata": "thông tin văn bản",
        "corpus": "bộ quy định",
        "chunk": "điều khoản",
        "case": "yêu cầu",
        "DSA": "văn phòng Công tác Sinh viên",
        "facts": "dữ kiện",
        "escalation": "chuyển tiếp",
        "pipeline": "luồng xử lý",
        "LLM": "dịch vụ AI",
        "supported_domain": "nhóm nội dung được hỗ trợ",
        "similarity": "mức phù hợp của căn cứ",
        "domain": "nhóm nội dung",
        "scope": "phạm vi áp dụng",
        "conflict": "căn cứ mâu thuẫn",
        "unanswered_request": "yêu cầu chưa tìm được căn cứ",
    }
    for technical, label in replacements.items():
        text = re.sub(rf"\b{technical}\b", label, text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:R\d+[ab]?(?:_[a-z]+)?|P0[1-5]|TECHNICAL_ERROR)\b[:：]?", "", text)
    return re.sub(r"\b(?:cv_|c_)[A-Za-z0-9_-]+\b", "(đã lưu trong lịch sử)", text)


def reply_text(body: str, citations: list[str]) -> str:
    for index, citation in enumerate(citations, start=1):
        body = body.replace(f"[{citation}]", f"[{index}]")
    return body
