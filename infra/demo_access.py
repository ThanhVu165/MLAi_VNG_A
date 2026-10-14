"""Ranh giới quyền cho bản DEMO công khai, do cấu hình phía máy chủ kiểm soát."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

APP_MODE_ENV = "APP_MODE"
PRIVATE_MODE = "private"
RESTRICTED_MODE = "restricted_demo"
MAX_PUBLIC_INPUT_CHARS = 5_000
_VALID_MODES = frozenset({PRIVATE_MODE, RESTRICTED_MODE})
_VERIFY4_PATH = Path(__file__).parents[1] / "verify" / "cases_verify4.json"
_LIVE_UNAVAILABLE = "Xử lý email mới hiện chưa được bật. Bạn vẫn có thể chạy email mẫu hoặc Verify."
_PIPELINE_CAPABILITY = object()


class DemoAccessDenied(RuntimeError):
    """Thao tác bị từ chối trước khi có side effect."""


@dataclass(frozen=True)
class CanonicalDemoInput:
    sample_id: str
    tag: str
    description: str
    sender: str
    subject: str
    body: str
    received_at: str
    channel: str = "paste"


_CANONICAL_DEMO_INPUTS = (
    CanonicalDemoInput(
        "sample_routine",
        "Email thường quy",
        "Hỏi lệ phí phúc khảo",
        "synthetic@example.invalid",
        "Hỏi lệ phí phúc khảo",
        "Cho em hỏi lệ phí phúc khảo một học phần là bao nhiêu?",
        "2026-09-21T09:00:00+07:00",
    ),
    CanonicalDemoInput(
        "sample_authority",
        "Cần thẩm quyền",
        "Xin phúc khảo trễ",
        "synthetic@example.invalid",
        "Xin phúc khảo trễ",
        "Em xin được nộp đơn phúc khảo môn X sau thời hạn, nhờ trường chấp thuận ngoại lệ cho em.",
        "2026-09-21T09:00:00+07:00",
    ),
    CanonicalDemoInput(
        "sample_missing_facts",
        "Thiếu dữ kiện",
        "Hỏi văn bản áp dụng",
        "synthetic@example.invalid",
        "Văn bản rèn luyện áp dụng",
        "Cho em hỏi văn bản điểm rèn luyện nào áp dụng cho khóa học và học kỳ của em?",
        "2026-09-21T09:00:00+07:00",
    ),
)


def app_mode() -> str:
    """Đọc mode phía máy chủ; thiếu cấu hình phải rơi vào restricted an toàn."""
    mode = os.getenv(APP_MODE_ENV, RESTRICTED_MODE).strip().lower()
    if mode not in _VALID_MODES:
        raise RuntimeError("APP_MODE phải là private hoặc restricted_demo.")
    return mode


def is_restricted_demo() -> bool:
    return app_mode() == RESTRICTED_MODE


def validate_runtime_mode() -> None:
    """Chặn record/LIVE khi restricted; HF1 chỉ cho phép replay offline."""
    if not is_restricted_demo():
        return
    llm_mode = os.getenv("LLM_MODE", "").strip().lower()
    if llm_mode != "replay":
        raise RuntimeError("Restricted DEMO hiện chỉ được chạy với LLM_MODE=replay.")


def authorize_demo_action(action: str) -> None:
    """Từ chối mọi mutation đặc quyền trong restricted mode, không tin actor."""
    if is_restricted_demo():
        raise DemoAccessDenied(f"Thao tác {action} không khả dụng trong bản DEMO công khai.")


def authorize_pipeline_action(action: str, capability: object | None) -> None:
    """Chỉ pipeline server giữ object identity này; actor string không thể thay thế."""
    if is_restricted_demo() and capability is not _PIPELINE_CAPABILITY:
        raise DemoAccessDenied(f"Thao tác {action} chỉ dành cho pipeline nội bộ.")


def canonical_demo_inputs() -> tuple[CanonicalDemoInput, ...]:
    return _CANONICAL_DEMO_INPUTS


def canonical_demo_input(sender: str, subject: str, body: str) -> CanonicalDemoInput | None:
    return next(
        (
            item
            for item in _CANONICAL_DEMO_INPUTS
            if (sender, subject, body) == (item.sender, item.subject, item.body)
        ),
        None,
    )


def validate_public_text(sender: object, subject: object, body: object) -> None:
    """Kiểm tra text trước persistence và không đưa payload lỗi vào thông báo/log."""
    values = (sender, subject, body)
    if not all(isinstance(value, str) for value in values):
        raise ValueError("Email công khai chỉ chấp nhận nội dung văn bản.")
    text_values = (str(sender), str(subject), str(body))
    if not all(value.strip() for value in text_values):
        raise ValueError("Hãy nhập đủ email người gửi, tiêu đề và nội dung trước khi xử lý.")
    if any("\x00" in value for value in text_values):
        raise ValueError("Nội dung email có ký tự không hợp lệ.")
    if len(text_values[2]) > MAX_PUBLIC_INPUT_CHARS:
        raise ValueError(f"Nội dung email không được vượt quá {MAX_PUBLIC_INPUT_CHARS} ký tự.")


def authorize_case_input(
    *,
    sender: object,
    subject: object,
    body: object,
    received_at: object,
    channel: object,
    external_id: object,
) -> None:
    """Chỉ whitelist payload replay đã ghi; lane LIVE của HF1 luôn đóng."""
    if not is_restricted_demo():
        return
    validate_public_text(sender, subject, body)
    if not isinstance(received_at, datetime) or not isinstance(channel, str):
        raise ValueError("Payload email không hợp lệ.")
    key = (
        str(sender),
        str(subject),
        str(body),
        received_at.isoformat(),
        channel,
        external_id,
    )
    if key not in _approved_replay_keys():
        raise DemoAccessDenied(_LIVE_UNAVAILABLE)


def case_is_owned(case_id: object, owned_case_ids: object) -> bool:
    """Query parameter không đủ cấp quyền; case phải có trong phiên hiện tại."""
    if not is_restricted_demo():
        return True
    if not isinstance(case_id, str) or not isinstance(owned_case_ids, (list, tuple, set)):
        return False
    return case_id in {value for value in owned_case_ids if isinstance(value, str)}


@lru_cache(maxsize=1)
def _approved_replay_keys() -> frozenset[tuple[object, ...]]:
    keys = {
        (
            item.sender,
            item.subject,
            item.body,
            item.received_at,
            item.channel,
            None,
        )
        for item in _CANONICAL_DEMO_INPUTS
    }
    try:
        payload: object = json.loads(_VERIFY4_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("Không đọc được payload Verify4 canonical.") from error
    if not isinstance(payload, list):
        raise RuntimeError("Payload Verify4 canonical không hợp lệ.")
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("input"), dict):
            raise RuntimeError("Payload Verify4 canonical không hợp lệ.")
        inp = item["input"]
        keys.add(
            (
                inp.get("sender"),
                inp.get("subject"),
                inp.get("body"),
                inp.get("received_at"),
                inp.get("channel"),
                item.get("id"),
            )
        )
    return frozenset(keys)
