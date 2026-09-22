from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from infra.audit import log_event
from infra.db import (
    MIGRATION_PATH,
    SCHEMA_VERSION,
    execute,
    fetch_one,
    initialize_database,
    transaction,
)


def test_upgrade_preserves_legacy_content_and_creates_backup(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO sources(doc_id,status) VALUES ('original','PENDING_REVIEW')"
        )
        connection.execute("CREATE TABLE source_contents(doc_id TEXT PRIMARY KEY,content BLOB)")
        connection.execute("INSERT INTO source_contents VALUES ('original',?)", (b"original",))
    initialize_database(path)
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert connection.execute(
            "SELECT content,extracted_text FROM source_contents"
        ).fetchone() == (b"original", "")
    backups = list((tmp_path / "backups").glob("*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert (
            connection.execute("SELECT content FROM source_contents").fetchone()[0] == b"original"
        )


def test_fresh_database_has_all_workflow_tables(tmp_path: Path) -> None:
    path = tmp_path / "new.db"
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"source_contents", "case_results", "case_jobs"} <= tables
    assert not (tmp_path / "backups").exists()


def test_claimed_current_schema_cannot_hide_missing_workflow_table(tmp_path: Path) -> None:
    path = tmp_path / "incomplete.db"
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE case_jobs")
    with pytest.raises(RuntimeError, match="thiếu bảng"):
        initialize_database(path)


def test_audit_uses_callers_transaction_and_rolls_back_with_it(tmp_path: Path) -> None:
    path = tmp_path / "audit.db"
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        log_event(
            case_id=None,
            actor="ADMIN:test",
            action="PAUSE_AUTOMATION",
            reason="Dừng để đối chiếu.",
            connection=connection,
        )
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


def test_nested_source_writes_and_audit_roll_back_together(tmp_path: Path) -> None:
    path = tmp_path / "transaction.db"
    initialize_database(path)
    with pytest.raises(ValueError, match="Lỗi sau khi duyệt"):
        with transaction(path):
            execute(
                "INSERT INTO sources(doc_id, status) VALUES ('new', 'ACTIVE')",
                database_path=path,
            )
            with transaction(path):
                assert fetch_one("SELECT doc_id FROM sources", database_path=path) is not None
                log_event(
                    case_id=None,
                    actor="ADMIN:test",
                    action="ACTIVATE_SOURCE",
                    reason="Đối chiếu nguồn.",
                    database_path=str(path),
                )
            raise ValueError("Lỗi sau khi duyệt")
    assert fetch_one("SELECT doc_id FROM sources", database_path=path) is None
    assert fetch_one("SELECT event_id FROM audit_events", database_path=path) is None
