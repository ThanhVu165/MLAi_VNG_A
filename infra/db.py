"""Truy cập SQLite và chuẩn hóa thời gian của ứng dụng."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from infra.settings import DATABASE_BUSY_TIMEOUT_MS

DEFAULT_DATABASE_PATH = Path("data/app.db")
MIGRATION_PATH = Path(__file__).parent / "migrations" / "001_init.sql"
EXPECTED_TABLES = frozenset(
    {
        "cases",
        "extractions",
        "decisions",
        "drafts",
        "escalations",
        "human_decisions",
        "sources",
        "chunks",
        "corpus_versions",
        "audit_events",
        "step_latencies",
        "settings",
    }
)
LOCAL_TIMEZONE = timezone(timedelta(hours=7), "Asia/Ho_Chi_Minh")
SqlValue = str | int | float | bytes | None


def now_iso() -> str:
    """Trả về thời điểm UTC theo ISO-8601 với hậu tố Z để lưu SQLite."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_local(timestamp: str) -> str:
    """Đổi chuỗi UTC đã lưu sang múi giờ hiển thị +07:00."""
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp phải có múi giờ.")
    return parsed.astimezone(LOCAL_TIMEZONE).isoformat()


def _database_path(database_path: str | Path | None) -> Path:
    return Path(database_path) if database_path is not None else DEFAULT_DATABASE_PATH


def _connect(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = _database_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=DATABASE_BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(f"PRAGMA busy_timeout={DATABASE_BUSY_TIMEOUT_MS}")
    return connection


def initialize_database(database_path: str | Path | None = None) -> None:
    """Tạo đủ bảng của migration duy nhất khi cơ sở dữ liệu còn trống."""
    with closing(_connect(database_path)) as connection:
        with connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            tables = {row["name"] for row in rows}
            if not tables:
                connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
            elif not EXPECTED_TABLES <= tables:
                raise RuntimeError("Cơ sở dữ liệu có migration chưa hoàn tất.")


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Mở kết nối SQLite đã bật WAL cho truy vấn thủ công ngắn hạn."""
    initialize_database(database_path)
    return _connect(database_path)


def execute(
    statement: str,
    parameters: Sequence[SqlValue] = (),
    *,
    database_path: str | Path | None = None,
) -> int:
    """Chạy một lệnh ghi và trả về số hàng bị ảnh hưởng."""
    with closing(get_connection(database_path)) as connection:
        with connection:
            cursor = connection.execute(statement, parameters)
            return cursor.rowcount


def fetch_one(
    statement: str,
    parameters: Sequence[SqlValue] = (),
    *,
    database_path: str | Path | None = None,
) -> sqlite3.Row | None:
    """Lấy tối đa một hàng SQLite dạng ``sqlite3.Row``."""
    with closing(get_connection(database_path)) as connection:
        return connection.execute(statement, parameters).fetchone()


def fetch_all(
    statement: str,
    parameters: Sequence[SqlValue] = (),
    *,
    database_path: str | Path | None = None,
) -> list[sqlite3.Row]:
    """Lấy mọi hàng SQLite dạng ``sqlite3.Row``."""
    with closing(get_connection(database_path)) as connection:
        return connection.execute(statement, parameters).fetchall()


initialize_database()
