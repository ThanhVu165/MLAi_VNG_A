"""Mọi test mặc định offline, kể cả khi cấu hình local chọn LIVE."""

import ipaddress
import socket

import openai
import pytest

_isolation = pytest.MonkeyPatch()
_getaddrinfo = socket.getaddrinfo


def _forbidden(*args: object, **kwargs: object) -> None:
    # pytest.fail không bị production `except Exception` nuốt thành kết quả hợp lệ.
    pytest.fail("OFFLINE_ONLY: real network/provider access forbidden")


def _numeric_address_only(
    host: str, port: int, family: int = 0, type: int = 0, proto: int = 0, flags: int = 0
) -> list:
    # SSRF tests cần phân loại IP literal; không cho phép truy vấn DNS.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        _forbidden()
    return _getaddrinfo(host, port, family, type, proto, flags | socket.AI_NUMERICHOST)


def pytest_configure(config: pytest.Config) -> None:
    # Cài trước collection/import settings; .env dùng setdefault không thể ghi đè.
    _isolation.setenv("LLM_MODE", "replay")
    for name in ("connect", "connect_ex", "sendto"):
        _isolation.setattr(socket.socket, name, _forbidden)
    _isolation.setattr(socket, "create_connection", _forbidden)
    _isolation.setattr(socket, "getaddrinfo", _numeric_address_only)
    _isolation.setattr(openai, "OpenAI", _forbidden)
    _isolation.setattr(openai, "AsyncOpenAI", _forbidden)


def pytest_unconfigure(config: pytest.Config) -> None:
    _isolation.undo()
