"""Trích xuất và chuẩn hóa nội dung PDF/DOCX trước khi chia chunk."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from docx import Document

try:
    import pdfplumber
except ModuleNotFoundError:  # pragma: no cover - phụ thuộc được ghim trong requirements.
    pdfplumber = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from collections.abc import Sequence


LEGAL_HEADING = re.compile(
    r"^(?:Điều\s+\d+[A-Za-z]?\.|Khoản\s+\d+[A-Za-z]?\.|Điểm\s+[a-zđ]\))", re.I
)


def extract_document(content: bytes, filename: str) -> str:
    """Trích xuất PDF/DOCX theo phần mở rộng của tệp đã nạp."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return normalize_pages(_extract_pdf_pages(content))
    if suffix == ".docx":
        document = Document(BytesIO(content))
        return normalize_pages(["\n".join(paragraph.text for paragraph in document.paragraphs)])
    raise ValueError("Chỉ hỗ trợ tệp PDF hoặc DOCX.")


def normalize_pages(pages: Sequence[str]) -> str:
    """Bỏ lề lặp, chuẩn hóa NFC và nối các dòng bị ngắt giữa câu."""
    normalized_pages = [[_clean_line(line) for line in page.splitlines()] for page in pages]
    repeated = _repeated_margins(normalized_pages)
    lines = [line for page in normalized_pages for line in page if line and line not in repeated]
    return _join_wrapped_lines(lines)


def _extract_pdf_pages(content: bytes) -> list[str]:
    if pdfplumber is None:
        raise RuntimeError("Thiếu pdfplumber; hãy cài dependencies từ requirements.txt.")
    with pdfplumber.open(BytesIO(content)) as document:
        return [page.extract_text() or "" for page in document.pages]


def _clean_line(line: str) -> str:
    return unicodedata.normalize("NFC", " ".join(line.split()))


def _repeated_margins(pages: Sequence[list[str]]) -> set[str]:
    if len(pages) < 2:
        return set()
    margins = Counter(line for page in pages if page for line in {page[0], page[-1]})
    required_pages = len(pages) // 2 + 1
    return {line for line, count in margins.items() if count >= required_pages}


def _join_wrapped_lines(lines: Sequence[str]) -> str:
    result: list[str] = []
    for line in lines:
        if (
            not result
            or LEGAL_HEADING.match(line)
            or result[-1].endswith((".", ";", ":", "!", "?"))
        ):
            result.append(line)
        elif result[-1].endswith("-"):
            result[-1] = result[-1][:-1] + line
        else:
            result[-1] = f"{result[-1]} {line}"
    return "\n".join(result)
