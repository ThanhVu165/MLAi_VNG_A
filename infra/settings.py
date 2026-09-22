"""Các ngưỡng runtime, có thể override qua biến môi trường cùng tên."""

import logging
import os

LOGGER = logging.getLogger(__name__)
_MINIMUM_NON_NEGATIVE = 0
_MINIMUM_POSITIVE = 1


def _read_int(name: str, default: int, minimum: int = _MINIMUM_NON_NEGATIVE) -> int:
    """Đọc số nguyên dương/không âm, lỗi cấu hình phải dừng khởi động rõ ràng."""
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as error:
        LOGGER.error("Biến môi trường %s phải là số nguyên.", name)
        raise ValueError(f"{name} phải là số nguyên.") from error
    if value < minimum:
        raise ValueError(f"{name} phải lớn hơn hoặc bằng {minimum}.")
    return value


def _read_float(name: str, default: float) -> float:
    """Đọc số thực không âm, không tự im lặng khi cấu hình hỏng."""
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as error:
        LOGGER.error("Biến môi trường %s phải là số thực.", name)
        raise ValueError(f"{name} phải là số thực.") from error
    if value < _MINIMUM_NON_NEGATIVE:
        raise ValueError(f"{name} phải không âm.")
    return value


# Ngưỡng điểm hybrid để coi kết quả retrieval là có căn cứ.
SIMILARITY_THRESHOLD: float = _read_float("SIMILARITY_THRESHOLD", 0.35)
# Tỷ lệ tối thiểu số câu trong bản nháp phải có citation.
CITATION_RATIO_MIN: float = _read_float("CITATION_RATIO_MIN", 0.6)
# Thời gian chờ trước khi email tự chuyển sang trạng thái đã gửi mô phỏng.
PENDING_SEND_SECONDS: int = _read_int("PENDING_SEND_SECONDS", 60, _MINIMUM_POSITIVE)
# Chu kỳ giao diện kiểm tra lại mốc gửi được lưu trong SQLite.
PENDING_STATUS_REFRESH_SECONDS: int = _read_int(
    "PENDING_STATUS_REFRESH_SECONDS", 1, _MINIMUM_POSITIVE
)
# Số từ tối thiểu của email ngắn trước khi hỏi lại thay vì gửi LLM.
MIN_WORDS_GUARD: int = _read_int("MIN_WORDS_GUARD", 15, _MINIMUM_POSITIVE)
# Thời gian tối đa cho một lần gọi LLM.
LLM_TIMEOUT_S: int = _read_int("LLM_TIMEOUT_S", 20, _MINIMUM_POSITIVE)
# Số lần thử lại LLM sau lần gọi đầu tiên.
LLM_RETRIES: int = _read_int("LLM_RETRIES", 1)
# Số chunk tối đa retrieval trả về cho pipeline.
RETRIEVAL_TOP_K: int = _read_int("RETRIEVAL_TOP_K", 6, _MINIMUM_POSITIVE)
# Giới hạn số từ của một câu hỏi chuyển tiếp.
QUESTION_WORDS_MIN: int = _read_int("QUESTION_WORDS_MIN", 8, _MINIMUM_POSITIVE)
QUESTION_WORDS_MAX: int = _read_int("QUESTION_WORDS_MAX", 45, _MINIMUM_POSITIVE)
# Khoảng thời gian quét case cần kiểm tra lại khi nguồn bị gỡ hiệu lực.
RECHECK_WINDOW_DAYS: int = _read_int("RECHECK_WINDOW_DAYS", 30, _MINIMUM_POSITIVE)
# Thời gian SQLite chờ writer khác nhả khóa khi Verify chạy tuần tự.
DATABASE_BUSY_TIMEOUT_MS: int = _read_int("DATABASE_BUSY_TIMEOUT_MS", 5000, _MINIMUM_POSITIVE)

if QUESTION_WORDS_MIN > QUESTION_WORDS_MAX:
    raise ValueError("QUESTION_WORDS_MIN không được lớn hơn QUESTION_WORDS_MAX.")
