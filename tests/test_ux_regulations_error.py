"""Regression cho lỗi đọc database trên trang Quy định & căn cứ."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from corpus.intake import ingest_text
from corpus.seed import ensure_seeded
from infra import db


REGULATIONS_PAGE = Path(__file__).resolve().parents[1] / "pages" / "3_Quan_tri_quy_dinh.py"
SAFE_ERROR = (
    "Hiện chưa thể truy xuất danh mục quy chế. " "Vui lòng thử lại sau hoặc liên hệ người quản trị."
)


def _assert_safe_read_failure(app: AppTest) -> None:
    assert not app.exception
    assert [item.value for item in app.error] == [SAFE_ERROR]
    client_text = "\n".join(item.value for item in (*app.error, *app.info))
    assert "no such table" not in client_text
    assert "private_source_path" not in client_text
    assert "Danh mục quy chế synthetic hiện chưa có dữ liệu" not in client_text
    assert "Danh mục quy chế hiện chưa có dữ liệu" not in client_text
    assert "Không tìm thấy quy định phù hợp" not in client_text


@pytest.mark.parametrize("app_mode", ["restricted_demo", "private"])
def test_source_database_failure_stops_with_safe_message(
    app_mode: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("APP_MODE", app_mode)
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "ui.db")

    def fail_sources(*_args: object, **_kwargs: object) -> object:
        raise sqlite3.OperationalError("no such table: private_source_path")

    monkeypatch.setattr("corpus.store.list_sources", fail_sources)

    app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)

    _assert_safe_read_failure(app)


@pytest.mark.parametrize(
    ("target", "error"),
    [
        ("corpus.store.get_source_content", OSError("private_source_path")),
        ("corpus.store.list_chunks", sqlite3.OperationalError("no such table: chunks")),
        ("infra.db.fetch_all", sqlite3.OperationalError("no such table: decisions")),
    ],
)
def test_dependent_source_read_failure_stops_safely(
    target: str, error: BaseException, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "ui.db"
    monkeypatch.setenv("APP_MODE", "private")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    ensure_seeded(database_path=database_path)

    def fail_read(*_args: object, **_kwargs: object) -> object:
        raise error

    monkeypatch.setattr(target, fail_read)

    app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)

    _assert_safe_read_failure(app)


def test_pending_source_lookup_failure_stops_safely(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "ui.db"
    monkeypatch.setenv("APP_MODE", "private")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    ingest_text("Điều 1. Nội dung synthetic.", actor="ADMIN:tester", database_path=database_path)

    def fail_source(*_args: object, **_kwargs: object) -> object:
        raise sqlite3.OperationalError("no such table: private_source_path")

    monkeypatch.setattr("corpus.store.get_source", fail_source)

    app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)

    _assert_safe_read_failure(app)


def test_programming_error_is_not_hidden(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "ui.db")

    def fail_sources(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("programming bug")

    monkeypatch.setattr("corpus.store.list_sources", fail_sources)

    app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)

    assert app.exception
    assert not any(item.value == SAFE_ERROR for item in app.error)


def test_restricted_source_table_keeps_six_synthetic_records(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "ui.db"
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    ensure_seeded(database_path=database_path)

    app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)

    assert not app.exception
    assert len(app.dataframe) == 1
    table = app.dataframe[0].value
    assert len(table) == 6
    assert set(table.columns) == {"Mã nguồn", "Tên quy định", "Trạng thái", "Lĩnh vực"}


def test_private_source_page_distinguishes_empty_and_no_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "ui.db"
    monkeypatch.setenv("APP_MODE", "private")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    db.initialize_database()

    empty_app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)
    assert not empty_app.exception
    assert any("Danh mục quy chế hiện chưa có dữ liệu" in item.value for item in empty_app.info)

    ensure_seeded(database_path=database_path)
    filtered_app = AppTest.from_file(str(REGULATIONS_PAGE)).run(timeout=20)
    filtered_app.text_input(key="policy_search_query").set_value("không-có-kết-quả").run(timeout=20)

    assert not filtered_app.exception
    assert any("Không tìm thấy quy định phù hợp" in item.value for item in filtered_app.info)
    assert not any(
        "Danh mục quy chế hiện chưa có dữ liệu" in item.value for item in filtered_app.info
    )
