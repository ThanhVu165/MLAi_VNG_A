"""Mọi test mặc định offline, kể cả khi cấu hình local chọn LIVE."""

import ipaddress
from pathlib import Path
import socket
import sys
import tempfile

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


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    # DEFAULT_DATABASE_PATH được chốt khi import infra.db; không sửa muộn rồi tiếp tục.
    if "infra.db" in sys.modules:
        raise pytest.UsageError(
            "TEST_DATABASE_ISOLATION: infra.db imported before isolation"
        )
    try:
        directory = tempfile.TemporaryDirectory(prefix="mlai-pytest-db-")
        config.add_cleanup(directory.cleanup)
        database_path = Path(directory.name).resolve(strict=True) / "app.db"
        if not database_path.is_absolute() or database_path.exists():
            raise OSError("Test database must be a fresh absolute path")
        _isolation.setenv("DATABASE_PATH", str(database_path))
    except OSError as error:
        raise pytest.UsageError(
            "TEST_DATABASE_ISOLATION: cannot create safe test database"
        ) from error
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
