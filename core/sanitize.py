from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser

QUOTE_MARKER = re.compile(
    r"^(?:on .+ wrote:|vào .+ đã viết:|-----original message-----|>)", re.IGNORECASE
)
SIGNATURE_MARKER = re.compile(r"^(?:--|trân trọng|best regards)[,!]*$", re.IGNORECASE)
CONTACT_MARKER = re.compile(r"^(?:email|e-mail|điện thoại|sđt|phone|tel)\s*[:|]", re.IGNORECASE)
BLOCK_TAGS = frozenset({"br", "div", "li", "p", "tr"})


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
