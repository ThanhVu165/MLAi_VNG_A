"""Hồi quy UI-01: điều hướng Audit giữ nguyên phiên và không tự cấp quyền."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from core.pipeline import process_case
from core.types import CaseInput
from corpus.seed import ensure_seeded
from infra import db
from infra.demo_access import canonical_demo_inputs

ROOT = Path(__file__).resolve().parents[1]
EMAIL_PAGE = ROOT / "pages/1_Xu_ly_email.py"
AUDIT_PAGE = ROOT / "pages/4_Nhat_ky_kiem_toan.py"
VERIFY_PAGE = ROOT / "pages/5_Verify.py"


@pytest.fixture
def restricted_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "ui-01.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setattr("core.worker.start_worker", lambda: None)
    db.initialize_database()
    ensure_seeded(database_path=database_path)
    return database_path


def _canonical_case(index: int = 0) -> str:
    sample = canonical_demo_inputs()[index]
    result = process_case(
        CaseInput(
            sample.sender,
            sample.subject,
            sample.body,
            datetime.fromisoformat(sample.received_at),
            sample.channel,
        )
    )
    return result.case_id


def _audit_app(owned: list[str], requested: str | None = None) -> AppTest:
    app = AppTest.from_file(str(AUDIT_PAGE))
    app.session_state["restricted_demo_case_ids"] = owned
    if requested is not None:
        app.session_state["audit_case_id"] = requested
    return app.run(timeout=20)


def test_email_audit_button_keeps_owned_case_in_same_session(
    restricted_app: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case_id = _canonical_case()
    switched_to: list[str] = []
    monkeypatch.setattr(st, "switch_page", switched_to.append)
    app = AppTest.from_file(str(EMAIL_PAGE))
    app.session_state["restricted_demo_case_ids"] = [case_id]
    app.session_state["active_case_id"] = case_id
    app.run(timeout=20)

    app.button(key=f"open_audit_{case_id}").click().run(timeout=20)

    assert not app.exception
    assert app.session_state["audit_case_id"] == case_id
    assert switched_to == ["pages/4_Nhat_ky_kiem_toan.py"]

    audit_app = _audit_app([case_id], case_id)
    audit_text = "\n".join(item.value for item in audit_app.markdown)
    assert not audit_app.exception
    assert case_id in audit_text
    assert canonical_demo_inputs()[0].subject in audit_text


def test_verify4_audit_button_keeps_selected_case_in_same_session(
    restricted_app: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    switched_to: list[str] = []
    monkeypatch.setattr(st, "switch_page", switched_to.append)
    app = AppTest.from_file(str(VERIFY_PAGE)).run(timeout=20)
    app.button(key="run_verify_main_btn").click().run(timeout=30)
    run_results, _, _ = app.session_state["verification_result"]
    selected = run_results[0]

    app.button(key=f"open_verify_audit_{selected.case_ref}").click().run(timeout=20)

    assert not app.exception
    assert app.session_state["audit_case_id"] == selected.case_ref
    assert selected.case_ref in app.session_state["restricted_demo_case_ids"]
    assert switched_to == ["pages/4_Nhat_ky_kiem_toan.py"]

    audit_app = _audit_app(app.session_state["restricted_demo_case_ids"], selected.case_ref)
    audit_text = "\n".join(item.value for item in audit_app.markdown)
    assert not audit_app.exception
    assert selected.case_ref in audit_text


@pytest.mark.parametrize("context_source", ["session", "query"])
def test_case_id_without_session_ownership_is_denied(
    restricted_app: Path, context_source: str
) -> None:
    foreign_case_id = _canonical_case()
    app = AppTest.from_file(str(AUDIT_PAGE))
    if context_source == "session":
        app.session_state["audit_case_id"] = foreign_case_id
    else:
        app.query_params["case_id"] = foreign_case_id

    app.run(timeout=20)

    assert not app.exception
    assert any("không có quyền" in item.value for item in app.warning)
    assert not any(foreign_case_id in item.value for item in app.markdown)


@pytest.mark.parametrize("invalid_case_id", ["case-khong-ton-tai", "case-bi-chinh-sua"])
def test_invalid_or_tampered_case_id_is_denied(restricted_app: Path, invalid_case_id: str) -> None:
    owned_case_id = _canonical_case()
    app = AppTest.from_file(str(AUDIT_PAGE))
    app.session_state["restricted_demo_case_ids"] = [owned_case_id]
    app.session_state["audit_case_id"] = invalid_case_id
    app.run(timeout=20)

    assert not app.exception
    assert any("không có quyền" in item.value for item in app.warning)
    assert not any(invalid_case_id in item.value for item in app.markdown)


def test_tampered_query_cannot_hide_behind_owned_session(restricted_app: Path) -> None:
    owned_case_id = _canonical_case()
    app = AppTest.from_file(str(AUDIT_PAGE))
    app.session_state["restricted_demo_case_ids"] = [owned_case_id]
    app.session_state["audit_case_id"] = owned_case_id
    app.query_params["case_id"] = "case-bi-chinh-sua"
    app.run(timeout=20)

    assert not app.exception
    assert any("không có quyền" in item.value for item in app.warning)
    assert not any(owned_case_id in item.value for item in app.markdown)


def test_sidebar_audit_keeps_owned_case_selection(restricted_app: Path) -> None:
    case_id = _canonical_case()
    app = AppTest.from_file(str(AUDIT_PAGE))
    app.session_state["restricted_demo_case_ids"] = [case_id]
    app.run(timeout=20)

    assert not app.exception
    assert app.selectbox(key="restricted_audit_case_selector").label == "Chọn case"
    assert app.selectbox(key="restricted_audit_case_selector").value == case_id
    assert not app.warning
