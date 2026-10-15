"""Regression cho responsive CSS và trạng thái app shell."""

from __future__ import annotations

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from infra import db
from ui.presentation import inject_app_css


ROOT = Path(__file__).resolve().parents[1]


def test_shared_css_covers_mobile_layout_and_table_overflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rendered: list[str] = []
    monkeypatch.setattr(st, "markdown", lambda body, **_: rendered.append(body))

    inject_app_css()

    css = rendered[0]
    assert "@media (max-width: 640px)" in css
    assert '[data-testid="stSidebar"]' in css
    assert '[data-testid="stHorizontalBlock"]' in css
    assert '[data-testid="stDataFrame"]' in css
    assert "overflow-x: auto" in css
    assert "overflow-wrap: anywhere" in css
    assert ".ex-stepper" in css and "grid-template-columns: 36px minmax(0, 1fr)" in css
    assert ".stButton > button" in css and "white-space: normal" in css


def test_restricted_shell_describes_offline_simulation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "shell.db")
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("LLM_CACHE", "0")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setattr("core.worker.start_worker", lambda: None)
    db.initialize_database()

    app = AppTest.from_file(str(ROOT / "streamlit_app.py")).run(timeout=20)

    assert not app.exception
    captions = "\n".join(item.value for item in app.sidebar.caption)
    shell = "\n".join(item.value for item in app.sidebar.markdown)
    assert "Restricted DEMO" in captions and "replay offline" in captions
    assert "không gửi email thật" in captions and "không gọi provider LIVE" in captions
    assert "Restricted DEMO" in shell and "email LIVE không hoạt động" in shell
    assert "Hệ thống hoạt động" not in shell
