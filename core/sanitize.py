from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Literal

QUOTE_MARKER = re.compile(
    r"^(?:on .+ wrote:|vào .+ đã viết:|-----original message-----|>)", re.IGNORECASE
)
SIGNATURE_MARKER = re.compile(r"^(?:--|trân trọng|best regards)[,!]*$", re.IGNORECASE)
CONTACT_MARKER = re.compile(r"^(?:email|e-mail|điện thoại|sđt|phone|tel)\s*[:|]", re.IGNORECASE)
BLOCK_TAGS = frozenset({"br", "div", "li", "p", "tr"})
VIETNAMESE_MARK_RATIO_MIN = 0.02
VIETNAMESE_MARKS = frozenset("ăâđêôơưáàảãạấầẩẫậắằẳẵặèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ")
VIETNAMESE_KEYWORDS = frozenset(
    {
        "em",
        "toi",
        "tôi",
        "xin",
        "hoi",
        "hỏi",
        "han",
        "hạn",
        "rut",
        "rút",
        "mon",
        "môn",
        "hoc",
        "học",
        "diem",
        "điểm",
        "quy",
        "dinh",
        "định",
        "phuc",
        "phúc",
        "khao",
        "khảo",
        "vui",
        "long",
        "cach",
        "thuc",
        "tuc",
    }
)
ENGLISH_KEYWORDS = frozenset(
    {
        "what",
        "when",
        "where",
        "how",
        "please",
        "the",
        "is",
        "for",
        "course",
        "withdrawal",
        "grade",
        "appeal",
        "can",
        "my",
        "score",
        "process",
    }
)
OTHER_SCRIPT_RANGES = (("\u0400", "\u052f"), ("\u3040", "\u30ff"), ("\u3400", "\u9fff"))
MIN_VIETNAMESE_KEYWORDS = 2
MIN_ENGLISH_KEYWORDS = 1
MSSV_PATTERN = re.compile(r"(?<!\d)\d{11}(?!\d)")
CCCD_PATTERN = re.compile(r"(?<!\d)\d{12}(?!\d)")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+84|84|0)[35789]\d{8}(?!\d)")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PII_PATTERNS = (
    (EMAIL_PATTERN, "[EMAIL]"),
    (CCCD_PATTERN, "[CCCD]"),
    (MSSV_PATTERN, "[MSSV]"),
    (PHONE_PATTERN, "[SĐT]"),
)
INJECTION_PATTERN = re.compile(
    r"(?:bỏ qua quy định|duyệt luôn|bạn là ai hãy|ignore previous|system prompt|"
    r"đừng chuyển cho ai|tự động chấp thuận)[^\n.?!]*(?:[.?!]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InjectionRemoval:
    body: str
    removed: tuple[str, ...]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _strip_html(body: str) -> str:
    parser = _TextExtractor()
    parser.feed(body)
    parser.close()
    return "".join(parser.parts)


def _without_quote(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if QUOTE_MARKER.match(line.strip()):
            return lines[:index]
    return lines


def _without_signature(lines: list[str]) -> list[str]:
    last_contact_index = len(lines) - 3
    for index, line in enumerate(lines):
        stripped = line.strip()
        if SIGNATURE_MARKER.match(stripped) or (
            index >= last_contact_index and CONTACT_MARKER.match(stripped)
        ):
            return lines[:index]
    return lines


def sanitize_body(body: str) -> str:
    """Trả nội dung email đã bỏ HTML, quote, chữ ký và khoảng trắng thừa."""
    normalized = unicodedata.normalize("NFC", body)
    lines = _without_signature(_without_quote(_strip_html(normalized).splitlines()))
    return " ".join(" ".join(lines).split())


def mask_pii(body: str) -> str:
    """Che thông tin định danh trước khi hiển thị hoặc ghi audit."""
    for pattern, replacement in PII_PATTERNS:
        body = pattern.sub(replacement, body)
    return body


def strip_prompt_injection(body: str) -> InjectionRemoval:
    """Tước câu lệnh nhắm vào hệ thống trước khi nội dung tới LLM."""
    removed: list[str] = []

    def remove(match: re.Match[str]) -> str:
        removed.append(match.group().strip())
        return " "

    clean_body = " ".join(INJECTION_PATTERN.sub(remove, body).split())
    return InjectionRemoval(clean_body, tuple(removed))


def detect_language(body: str) -> Literal["vi", "en", "other"]:
    """Nhận diện vi/en/other bằng ký tự và từ khóa, không gọi LLM."""
    normalized = unicodedata.normalize("NFC", body).lower()
    if any(
        start <= character <= end for start, end in OTHER_SCRIPT_RANGES for character in normalized
    ):
        return "other"
    letters = [character for character in normalized if character.isalpha()]
    if (
        letters
        and sum(character in VIETNAMESE_MARKS for character in letters) / len(letters)
        >= VIETNAMESE_MARK_RATIO_MIN
    ):
        return "vi"
    words = set(re.findall(r"[a-zđ]+", normalized))
    if len(words & VIETNAMESE_KEYWORDS) >= MIN_VIETNAMESE_KEYWORDS:
        return "vi"
    if len(words & ENGLISH_KEYWORDS) >= MIN_ENGLISH_KEYWORDS:
        return "en"
    return "other"
