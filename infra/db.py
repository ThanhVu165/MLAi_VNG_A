"""Truy cập SQLite và chuẩn hóa thời gian của ứng dụng."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from math import ceil
from pathlib import Path
from threading import RLock
from uuid import uuid4

from infra.settings import DATABASE_BUSY_TIMEOUT_MS

DEFAULT_DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/app.db"))
MIGRATION_PATH = Path(__file__).parent / "migrations" / "001_init.sql"
WORKFLOW_MIGRATION_PATH = MIGRATION_PATH.with_name("002_workflow.sql")
SCHEMA_VERSION = 2
_MIGRATION_LOCK = RLock()
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
_TRANSACTION: ContextVar[tuple[Path, sqlite3.Connection] | None] = ContextVar(
    "database_transaction", default=None
)


def now_iso() -> str:
    """Trả về thời điểm UTC theo ISO-8601 với hậu tố Z để lưu SQLite."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def to_utc_iso(value: datetime) -> str:
    """Đổi datetime có múi giờ sang UTC ISO-8601 để lưu SQLite."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime phải có múi giờ.")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def to_local(timestamp: str) -> str:
    """Đổi chuỗi UTC đã lưu sang múi giờ hiển thị +07:00."""
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp phải có múi giờ.")
    return parsed.astimezone(LOCAL_TIMEZONE).isoformat()


def seconds_until(timestamp: str) -> int:
    """Tính số giây còn lại đến mốc UTC được lưu trong SQLite."""
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp phải có múi giờ.")
    return max(
        0, ceil((parsed.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds())
    )


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
    """Nâng schema có phiên bản; sao lưu dữ liệu cũ trước khi sửa cấu trúc."""
    with _MIGRATION_LOCK, closing(_connect(database_path)) as connection:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if tables and not EXPECTED_TABLES <= tables:
            raise RuntimeError("Cơ sở dữ liệu có cấu trúc chưa hoàn tất; không tự sửa dữ liệu.")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError("Dữ liệu thuộc phiên bản ứng dụng mới hơn; hãy cập nhật ứng dụng.")
        if version == SCHEMA_VERSION:
            if not {"source_contents", "case_results", "case_jobs"} <= tables:
                raise RuntimeError(
                    "Dữ liệu thiếu bảng công việc hoặc bản gốc. Hãy phục hồi từ bản sao lưu; không khởi tạo đè."
                )
            source_columns = {row["name"] for row in connection.execute("PRAGMA table_info(source_contents)")}
            case_columns = {row["name"] for row in connection.execute("PRAGMA table_info(cases)")}
            if {"extracted_text", "filename"} <= source_columns and "external_id" in case_columns:
                return
        if tables:
            _backup_database(connection, _database_path(database_path))
        else:
            connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            for statement in WORKFLOW_MIGRATION_PATH.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    connection.execute(statement)
            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(source_contents)")
            }
            for column in ("extracted_text", "filename"):
                if column not in columns:
                    connection.execute(
                        f"ALTER TABLE source_contents ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
                    )
            case_columns = {row["name"] for row in connection.execute("PRAGMA table_info(cases)")}
            if "external_id" not in case_columns:
                connection.execute("ALTER TABLE cases ADD COLUMN external_id TEXT")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS cases_external_id "
                "ON cases(channel, external_id) WHERE external_id IS NOT NULL"
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _backup_database(connection: sqlite3.Connection, path: Path) -> None:
    directory = path.parent / "backups"
    directory.mkdir(parents=True, exist_ok=True)
    backup_path = directory / f"{path.stem}.pre-v{SCHEMA_VERSION}-{uuid4().hex}.db"
    with closing(sqlite3.connect(backup_path)) as backup:
        connection.backup(backup)


def get_connection(database_path: str | Path | None = None) -> sqlite3.Connection:
    """Mở kết nối SQLite đã bật WAL cho truy vấn thủ công ngắn hạn."""
    initialize_database(database_path)
    return _connect(database_path)


def _transaction_connection(database_path: str | Path | None) -> sqlite3.Connection | None:
    current = _TRANSACTION.get()
    if current is None:
        return None
    if current[0] != _database_path(database_path).resolve():
        raise ValueError("Không ghi hai cơ sở dữ liệu trong cùng một giao dịch.")
    return current[1]


@contextmanager
def transaction(database_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Gom các lời gọi execute/fetch và audit vào một giao dịch, không giữ qua lời gọi AI."""
    current = _transaction_connection(database_path)
    if current is not None:
        yield current
        return
    with closing(get_connection(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        token = _TRANSACTION.set((_database_path(database_path).resolve(), connection))
        try:
            yield connection
        finally:
            _TRANSACTION.reset(token)


def execute(
    statement: str,
    parameters: Sequence[SqlValue] = (),
    *,
    database_path: str | Path | None = None,
) -> int:
    """Chạy một lệnh ghi và trả về số hàng bị ảnh hưởng."""
    current = _transaction_connection(database_path)
    if current is not None:
        return current.execute(statement, parameters).rowcount
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
    current = _transaction_connection(database_path)
    if current is not None:
        return current.execute(statement, parameters).fetchone()
    with closing(get_connection(database_path)) as connection:
        return connection.execute(statement, parameters).fetchone()


def fetch_all(
    statement: str,
    parameters: Sequence[SqlValue] = (),
    *,
    database_path: str | Path | None = None,
) -> list[sqlite3.Row]:
    """Lấy mọi hàng SQLite dạng ``sqlite3.Row``."""
    current = _transaction_connection(database_path)
    if current is not None:
        return current.execute(statement, parameters).fetchall()
    with closing(get_connection(database_path)) as connection:
        return connection.execute(statement, parameters).fetchall()
