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


STOP_REASON_DESCRIPTIONS = {
    "FACT_UNRESOLVED": "Thiếu dữ kiện cần thiết để đưa ra kết luận.",
    "OUT_OF_POLICY": "Không tìm thấy quy định đang áp dụng cho yêu cầu này.",
    "AUTHORITY_REQUIRED": "Trường hợp này cần người có thẩm quyền quyết định.",
}

DECISION_DESCRIPTIONS = {
    "AUTO_REPLY": "Có đủ căn cứ để tự động phản hồi.",
    "ESCALATE": "Cần chuyên viên xem xét trước khi tiếp tục.",
    "INVALID_INPUT": "Cần bổ sung thông tin email.",
    "ERROR": "Chưa xử lý được do sự cố kỹ thuật.",
}


def stop_reason_text(reason: str) -> str:
    return STOP_REASON_DESCRIPTIONS.get(
        reason, TYPE_LABELS.get(reason, "Cần chuyên viên xem xét.")
    )


def decision_desc(decision: str) -> str:
    return DECISION_DESCRIPTIONS.get(decision, "Chưa xác định cách xử lý.")


def inject_app_css() -> None:
    """Áp dụng hệ thống giao diện Light Mode Enterprise SaaS tối giản, sạch sẽ."""
    import streamlit as st

    st.markdown(
        """
        <style>
        /* Light mode enterprise clean style */
        .stApp {
            background-color: #F8FAFC;
            color: #0F172A;
        }
        /* Top padding refinement */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px;
        }
        /* Cards */
        .ex-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 14px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        }
        .ex-card-title {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #64748B;
            margin-bottom: 8px;
        }
        /* Badges */
        .ex-badge {
            display: inline-flex;
            align-items: center;
            font-size: 12px;
            font-weight: 600;
            padding: 2px 10px;
            border-radius: 9999px;
            line-height: 1.4;
            white-space: nowrap;
        }
        .ex-badge-auto {
            background: #ECFDF5;
            color: #047857;
            border: 1px solid #A7F3D0;
        }
        .ex-badge-escalate {
            background: #FFFBEB;
            color: #B45309;
            border: 1px solid #FDE68A;
        }
        .ex-badge-info {
            background: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
        }
        .ex-badge-neutral {
            background: #F1F5F9;
            color: #475569;
            border: 1px solid #CBD5E1;
        }
        .ex-badge-danger {
            background: #FEF2F2;
            color: #B91C1C;
            border: 1px solid #FECACA;
        }
        .ex-badge-purple {
            background: #F5F3FF;
            color: #6D28D9;
            border: 1px solid #DDD6FE;
        }
        /* KPI Cards */
        .ex-kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
            text-align: left;
        }
        .ex-kpi-val {
            font-size: 26px;
            font-weight: 700;
            line-height: 1.2;
            margin: 4px 0 2px 0;
        }
        .ex-kpi-label {
            font-size: 13px;
            color: #64748B;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .ex-kpi-sub {
            font-size: 12px;
            color: #94A3B8;
        }
        /* Failure banner */
        .ex-fail-banner {
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-left: 4px solid #EF4444;
            border-radius: 8px;
            padding: 14px 18px;
            margin: 14px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        /* Stop reason card */
        .ex-stop-card {
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 4px solid #D97706;
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 16px;
        }
        .ex-stop-header {
            font-size: 14px;
            font-weight: 700;
            color: #92400E;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .ex-stop-desc {
            font-size: 13.5px;
            color: #78350F;
            margin: 0;
            line-height: 1.45;
        }
        /* Evidence item */
        .ex-evidence-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 3px solid #2563EB;
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }
        .ex-evidence-breadcrumb {
            font-size: 12px;
            font-weight: 600;
            color: #1E40AF;
            margin-bottom: 4px;
        }
        .ex-evidence-text {
            font-size: 13px;
            color: #334155;
            line-height: 1.5;
        }
        /* Action preview callout */
        .ex-action-preview {
            background: #F8FAFC;
            border: 1px dashed #94A3B8;
            border-radius: 6px;
            padding: 14px 16px;
            margin: 14px 0;
        }
        .ex-action-preview-title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            color: #475569;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .ex-action-preview-item {
            font-size: 13px;
            color: #1E293B;
            margin: 3px 0;
            display: flex;
            align-items: baseline;
            gap: 6px;
        }
        /* Timeline styles for Audit */
        .ex-timeline {
            position: relative;
            padding-left: 28px;
            margin: 16px 0;
        }
        .ex-timeline::before {
            content: '';
            position: absolute;
            top: 10px;
            bottom: 10px;
            left: 9px;
            width: 2px;
            background: #E2E8F0;
        }
        .ex-timeline-item {
            position: relative;
            margin-bottom: 22px;
        }
        .ex-timeline-item:last-child {
            margin-bottom: 6px;
        }
        .ex-timeline-dot {
            position: absolute;
            left: -28px;
            top: 4px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #FFFFFF;
            border: 3px solid #2563EB;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .ex-timeline-dot-admin {
            border-color: #7C3AED;
        }
        .ex-timeline-dot-human {
            border-color: #D97706;
        }
        .ex-timeline-dot-system {
            border-color: #2563EB;
        }
        .ex-timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 4px;
        }
        .ex-timeline-title {
            font-size: 14px;
            font-weight: 700;
            color: #0F172A;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .ex-timeline-time {
            font-size: 12px;
            color: #64748B;
            font-family: monospace;
        }
        .ex-timeline-body {
            font-size: 13px;
            color: #334155;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 10px 14px;
            margin-top: 6px;
            line-height: 1.5;
        }
        /* Stepper for Email Processing */
        .ex-stepper {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            position: relative;
            margin: 18px 0 22px 0;
            padding: 0 10px;
        }
        .ex-stepper::before {
            content: '';
            position: absolute;
            top: 18px;
            left: 40px;
            right: 40px;
            height: 2px;
            background: #E2E8F0;
            z-index: 0;
        }
        .ex-step {
            position: relative;
            z-index: 1;
            text-align: center;
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .ex-step-num {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #FFFFFF;
            border: 2px solid #CBD5E1;
            color: #64748B;
            font-size: 13.5px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 6px;
        }
        .ex-step-active .ex-step-num {
            border-color: #2563EB;
            background: #2563EB;
            color: #FFFFFF;
            box-shadow: 0 0 0 4px #DBEAFE;
        }
        .ex-step-done .ex-step-num {
            border-color: #10B981;
            background: #10B981;
            color: #FFFFFF;
        }
        .ex-step-title {
            font-size: 13px;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 2px;
        }
        .ex-step-desc {
            font-size: 11px;
            color: #64748B;
            max-width: 140px;
            line-height: 1.3;
        }

        /* Quick sample card */
        .ex-sample-card {
            background: #FFFFFF;
            border: 1.5px solid #E2E8F0;
            border-radius: 8px;
            padding: 12px 14px;
            text-align: left;
            margin-bottom: 8px;
        }
        .ex-sample-title {
            font-size: 13px;
            font-weight: 700;
            color: #0F172A;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 2px;
        }
        .ex-sample-sub {
            font-size: 12px;
            color: #64748B;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge_html(text: str, tone: str = "neutral") -> str:
    """Tạo mã HTML cho badge trạng thái."""
    tone_class = f"ex-badge-{tone}"
    return f'<span class="ex-badge {tone_class}">{text}</span>'


def decision_badge_html(decision: str) -> str:
    if decision == "AUTO_REPLY":
        return badge_html("AUTO_REPLY · Tự động", "auto")
    if decision == "ESCALATE":
        return badge_html("ESCALATE · Cần người", "escalate")
    if decision == "ERROR":
        return badge_html("ERROR · Sự cố", "danger")
    return badge_html(decision, "neutral")


def status_badge_html(status: str) -> str:
    label = status_label(status)
    tone_map = {
        "AWAITING_HUMAN": "escalate",
        "HUMAN_DECIDED": "purple",
        "PENDING_APPROVAL": "escalate",
        "PENDING_SEND": "info",
        "SENT": "auto",
        "RESOLVED": "auto",
        "CANCELLED": "neutral",
        "ERROR": "danger",
        "INVALID_INPUT": "neutral",
    }
    return badge_html(label, tone_map.get(status, "neutral"))


def stop_reason_badge_html(reason: str) -> str:
    label = TYPE_LABELS.get(reason, reason)
    return badge_html(label, "escalate")


def pass_fail_badge_html(passed: bool) -> str:
    """Tạo badge PASS (xanh) hoặc FAIL (đỏ)."""
    if passed:
        return badge_html("✓ PASS", "auto")
    return badge_html("✕ FAIL", "danger")


def actor_badge_html(actor: str) -> str:
    """Tạo badge hiển thị chủ thể thực hiện hành động."""
    if actor == "SYSTEM":
        return badge_html("Hệ thống", "info")
    if actor.startswith("ADMIN:"):
        name = actor.removeprefix("ADMIN:").strip() or "local"
        return badge_html(f"Quản trị ({name})", "purple")
    if actor.startswith("HUMAN:"):
        name = actor.removeprefix("HUMAN:").strip() or "local"
        return badge_html(f"Chuyên viên ({name})", "escalate")
    return badge_html(actor, "neutral")


def action_badge_html(action: str) -> str:
    """Tạo badge hiển thị hành động nghiệp vụ."""
    label = ACTION_LABELS.get(action, action)
    if any(k in action for k in ("OVERRIDE", "REJECT", "CANCEL", "ERROR")):
        return badge_html(label, "danger")
    if any(k in action for k in ("APPROVED", "DISPATCHED", "RESOLVED")):
        return badge_html(label, "auto")
    if any(k in action for k in ("QUEUED", "QUESTION", "ESCALATE")):
        return badge_html(label, "escalate")
    return badge_html(label, "info")


def kpi_card_html(
    label: str,
    value: str,
    subtext: str = "",
    tone: str = "neutral",
    icon: str = "",
) -> str:
    """Tạo mã HTML cho thẻ KPI card chuẩn Light Enterprise SaaS."""
    border_color = {
        "neutral": "#E2E8F0",
        "primary": "#BFDBFE",
        "success": "#A7F3D0",
        "warning": "#FDE68A",
        "danger": "#FECACA",
        "purple": "#DDD6FE",
    }.get(tone, "#E2E8F0")

    val_color = {
        "neutral": "#0F172A",
        "primary": "#1D4ED8",
        "success": "#047857",
        "warning": "#B45309",
        "danger": "#B91C1C",
        "purple": "#6D28D9",
    }.get(tone, "#0F172A")

    icon_html = f'<span style="font-size: 16px; margin-right: 4px;">{icon}</span>' if icon else ""
    sub_html = f'<div class="ex-kpi-sub" style="margin-top: 4px; font-size: 12px; color: #64748B;">{subtext}</div>' if subtext else ""

    return (
        f'<div class="ex-kpi-card" style="border: 1px solid {border_color}; border-radius: 8px; padding: 14px 16px; background: #FFFFFF; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">'
        f'<div class="ex-kpi-label" style="font-size: 13px; font-weight: 600; color: #64748B; display: flex; align-items: center; gap: 6px;">{icon_html}{label}</div>'
        f'<div class="ex-kpi-val" style="color: {val_color}; font-size: 24px; font-weight: 700; margin: 4px 0 2px 0; line-height: 1.2;">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )


def page_header_html(kicker: str, title: str, description: str) -> str:
    """Tạo tiêu đề trang thống nhất cho toàn bộ hệ thống Exodia."""
    return (
        f'<div style="margin-bottom: 1rem;">'
        f'<div style="font-size: 11.5px; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px;">{kicker}</div>'
        f'<h1 style="margin: 2px 0 4px 0; font-size: 1.85rem; font-weight: 700; color: #0F172A; line-height: 1.25;">{title}</h1>'
        f'<p style="margin: 0; color: #64748B; font-size: 14px; line-height: 1.5;">{description}</p>'
        f'</div>'
    )


def empty_state_card_html(icon: str, title: str, description: str) -> str:
    """Tạo thẻ trạng thái dữ liệu trống chuẩn Light Enterprise SaaS."""
    return (
        f'<div class="ex-card" style="text-align: center; padding: 36px 20px; background: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 8px;">'
        f'<div style="font-size: 32px; margin-bottom: 8px;">{icon}</div>'
        f'<h3 style="margin: 0 0 6px 0; color: #0F172A; font-size: 16px; font-weight: 700;">{title}</h3>'
        f'<p style="margin: 0; color: #64748B; font-size: 13.5px; line-height: 1.45; max-width: 500px; margin-left: auto; margin-right: auto;">{description}</p>'
        f'</div>'
    )
