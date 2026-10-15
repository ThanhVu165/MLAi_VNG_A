"""Regression UI-only cho gói UX cardless trước M4."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from corpus.seed import ensure_seeded
from infra import db

ROOT = Path(__file__).resolve().parents[1]
EMAIL_PAGE = ROOT / "pages" / "1_Xu_ly_email.py"
REGULATIONS_PAGE = ROOT / "pages" / "3_Quan_tri_quy_dinh.py"
VERIFY_PAGE = ROOT / "pages" / "5_Verify.py"


@pytest.fixture
def isolated_ui_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    database_path = tmp_path / "ux.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    monkeypatch.setenv("APP_MODE", "restricted_demo")
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setattr("core.worker.start_worker", lambda: None)
    db.initialize_database()
    return database_path


def test_restricted_email_guidance_appears_before_input(isolated_ui_db: Path) -> None:
    app = AppTest.from_file(str(EMAIL_PAGE)).run()

    assert not app.exception
    assert any(
        "Restricted DEMO" in item.value
        and "3 email mẫu synthetic canonical" in item.value
        and "không gọi provider LIVE" in item.value
        for item in app.info
    )
    guidance = "\n".join(item.value for item in app.markdown)
    assert "Bắt đầu trong 5 bước" in guidance
    assert (
        "Trong cùng phiên, dùng thanh điều hướng bên trái để mở **Nhật ký kiểm toán**" in guidance
    )


def test_restricted_regulations_has_distinct_empty_state(isolated_ui_db: Path) -> None:
    app = AppTest.from_file(str(REGULATIONS_PAGE)).run()

    assert not app.exception
    assert any("Danh mục quy chế synthetic hiện chưa có dữ liệu" in item.value for item in app.info)
    assert not app.dataframe


def test_restricted_regulations_keeps_existing_table(isolated_ui_db: Path) -> None:
    ensure_seeded(database_path=isolated_ui_db)
    app = AppTest.from_file(str(REGULATIONS_PAGE)).run()

    assert not app.exception
    assert app.dataframe
    assert not any(
        "Danh mục quy chế synthetic hiện chưa có dữ liệu" in item.value for item in app.info
    )


def test_verify_explains_replay_before_execution(isolated_ui_db: Path) -> None:
    app = AppTest.from_file(str(VERIFY_PAGE)).run()

    assert not app.exception
    assert any(
        "Replay offline" in item.value
        and "pipeline chuẩn" in item.value
        and "không gọi provider LIVE" in item.value
        for item in app.info
    )


def test_verify_pipeline_result_keeps_provenance_timestamp(isolated_ui_db: Path) -> None:
    ensure_seeded(database_path=isolated_ui_db)
    app = AppTest.from_file(str(VERIFY_PAGE)).run(timeout=20)
    app.button(key="run_verify_main_btn").click().run(timeout=30)

    assert not app.exception
    assert any("KẾT QUẢ PIPELINE" in item.value for item in app.success)
    captions = [item.value for item in app.caption]
    timestamp_caption = next(
        value for value in captions if "Thời điểm hoàn tất theo lần chạy pipeline" in value
    )
    assert "không thay đổi khi chỉ render lại trang" in timestamp_caption
    previous_timestamp = timestamp_caption

    app.run()
    rerendered = next(
        item.value
        for item in app.caption
        if "Thời điểm hoàn tất theo lần chạy pipeline" in item.value
    )
    assert rerendered == previous_timestamp
