"""Bấm form Streamlit và kiểm tra DB thật, không thay thế process_case."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from infra import db

ROOT = Path(__file__).resolve().parents[1]
EMAIL_PAGE = ROOT / "pages/1_Xu_ly_email.py"


@pytest.fixture
def isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "app.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    db.initialize_database()
    return database_path


@pytest.mark.parametrize("page", ["paste", "home"])
@pytest.mark.parametrize("missing", ["sender", "subject", "body"])
def test_missing_field_never_enters_pipeline(isolated_db: Path, page: str, missing: str) -> None:
    app = AppTest.from_file(str(EMAIL_PAGE if page == "paste" else ROOT / "streamlit_app.py")).run()
    prefix = "paste_" if page == "paste" else "home_email_"
    values = {"sender": "student@example.test", "subject": "Hỏi thông tin", "body": "Nội dung"}
    for field, value in values.items():
        widget = app.text_area if field == "body" else app.text_input
        widget(key=prefix + field).set_value("   " if field == missing else value)
    button = next(
        item for item in app.button if item.label in {"Xử lý email", "Xử lý email đã dán"}
    )
    button.click().run()
    assert not app.exception
    assert any("nhập đủ" in item.value for item in app.error)
    assert db.fetch_all("SELECT case_id FROM cases") == []
    assert db.fetch_all("SELECT event_id FROM audit_events") == []


def test_complete_paste_preserves_input_and_receipt_time(isolated_db: Path) -> None:
    app = AppTest.from_file(str(EMAIL_PAGE)).run()
    sender, subject, body = (
        " student@example.test ",
        " Tiêu đề gốc ",
        "寮の申請方法と締切を教えてください。",
    )
    app.text_input(key="paste_sender").set_value(sender)
    app.text_input(key="paste_subject").set_value(subject)
    app.text_area(key="paste_body").set_value(body)
    before = datetime.now(timezone.utc)
    app.button(key="process_paste").click().run()
    after = datetime.now(timezone.utc)
    assert not app.exception
    rows = db.fetch_all("SELECT * FROM cases")
    assert len(rows) == 1
    row = rows[0]
    assert (row["sender"], row["subject"], row["body_raw"], row["channel"]) == (
        sender,
        subject,
        body,
        "paste",
    )
    assert before <= datetime.fromisoformat(row["received_at"]) <= after
    assert row["received_at"].endswith("Z")


def test_inbox_preserves_seed_fields_and_timestamp(isolated_db: Path) -> None:
    emails = json.loads((ROOT / "data/seed_inbox.json").read_text(encoding="utf-8"))
    assert len(emails) == 12
    assert all(
        datetime.fromisoformat(email["received_at"]).utcoffset() is not None for email in emails
    )
    app = AppTest.from_file(str(EMAIL_PAGE)).run()
    app.button(key="process_inbox").click().run(timeout=15)
    assert not app.exception
    rows = db.fetch_all("SELECT * FROM cases")
    assert len(rows) == 1
    row, email = rows[0], emails[0]
    assert (row["sender"], row["subject"], row["body_raw"], row["channel"]) == (
        email["sender"],
        email["subject"],
        email["body"],
        "inbox",
    )
    assert datetime.fromisoformat(row["received_at"]) == datetime.fromisoformat(
        email["received_at"]
    )


def test_home_handoff_preserves_complete_email(isolated_db: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run()
    sender, subject, body = (
        "home@example.test",
        "Tiêu đề từ trang chủ",
        "寮の申請方法と締切を教えてください。",
    )
    app.text_input(key="home_email_sender").set_value(sender)
    app.text_input(key="home_email_subject").set_value(subject)
    app.text_area(key="home_email_body").set_value(body)
    before = datetime.now(timezone.utc)
    next(button for button in app.button if button.label == "Xử lý email").click().run()
    assert not app.exception
    app.switch_page("pages/1_Xu_ly_email.py").run()
    assert not app.exception
    assert app.text_input(key="paste_sender").value == sender
    assert app.text_input(key="paste_subject").value == subject
    assert app.text_area(key="paste_body").value == body
    rows = db.fetch_all("SELECT * FROM cases")
    assert len(rows) == 1
    row = rows[0]
    assert (row["sender"], row["subject"], row["body_raw"]) == (sender, subject, body)
    assert before <= datetime.fromisoformat(row["received_at"]) <= datetime.now(timezone.utc)
    app.run()
    assert len(db.fetch_all("SELECT case_id FROM cases")) == 1
