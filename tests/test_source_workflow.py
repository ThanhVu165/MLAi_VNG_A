"""Nguồn mới đi qua thao tác thật, không sửa quyền từng đoạn để được kích hoạt."""

from dataclasses import replace
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
import sqlite3
import unicodedata

import pytest

from core.types import ChunkLabel, Domain, SourceStatus
from corpus import api, lifecycle, workflow
from corpus.intake import _download_once, ingest_text
from corpus.lifecycle import activate_source, reject_source
from corpus.metadata import MetadataDraft, MetadataProposal, save_metadata
from corpus.seed import ensure_seeded
from corpus.store import get_source, get_source_content, list_chunks, save_source_content, update_source
from infra import db


def test_new_source_keeps_original_and_needs_one_source_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "new.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", path)
    text = unicodedata.normalize(
        "NFD", "Điều 7. Lệ phí\nKhoản 2. Lệ phí phúc khảo là 175.000 đồng."
    )
    intake = ingest_text(text, actor="ADMIN:tester", title="Hướng dẫn thử nghiệm")
    draft = MetadataDraft(
        intake.source.doc_id,
        "Hướng dẫn thử nghiệm",
        "Phòng giả lập",
        None,
        "2026-08-01",
        None,
        ("undergraduate",),
        ("K49",),
        (),
        False,
        ("grade_appeal",),
        "not-trusted",
    )
    monkeypatch.setattr(
        workflow, "propose_metadata", lambda *_args, **_kwargs: MetadataProposal(draft, None)
    )

    proposal = workflow.prepare_source(intake.source, actor="ADMIN:tester")
    assert proposal.draft == draft
    original = get_source_content(intake.source.doc_id)
    assert original is not None and original.content == text.encode()
    assert original.extracted_text == unicodedata.normalize("NFC", text)
    assert len(list_chunks(intake.source.doc_id)) == 2
    assert api.available_evidence([Domain.GRADE_APPEAL]) == []
    with pytest.raises(ValueError):
        workflow.approve_source(
            intake.source, replace(draft, applies_to=()), actor="ADMIN:tester", reason="Duyệt"
        )
    with pytest.raises(ValueError):
        activate_source(intake.source, actor="ADMIN:tester", reason="Bỏ qua xác nhận")
    approved = workflow.approve_source(
        intake.source, draft, actor="ADMIN:tester", reason="Đã đối chiếu nguồn và phạm vi."
    )
    assert approved.status is SourceStatus.ACTIVE
    assert all(chunk.label is ChunkLabel.HUMAN_ONLY for chunk in list_chunks(approved.doc_id))
    evidence = api.available_evidence(
        [Domain.GRADE_APPEAL], datetime(2026, 9, 22, tzinfo=timezone.utc)
    )
    assert len(evidence) == 2
    expanded = api.get_chunk(evidence[0].chunk_id)
    assert expanded is not None and "175.000" in expanded.text and "Điều 7" in expanded.text
    with pytest.raises(ValueError):
        save_metadata(draft, actor="ADMIN:tester", source_id=approved.doc_id)
    with pytest.raises(ValueError):
        save_source_content(replace(original, extracted_text="Nội dung thay đổi"))
    before = list_chunks(approved.doc_id)
    with pytest.raises(ValueError):
        workflow.materialize_source(intake.source)
    with pytest.raises(ValueError):
        reject_source(intake.source, actor="ADMIN:tester", reason="Biểu mẫu cũ")
    assert list_chunks(approved.doc_id) == before
    stored = get_source(approved.doc_id)
    assert stored is not None and stored.status is SourceStatus.ACTIVE


def test_failed_metadata_proposal_keeps_source_pending_and_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "pending.db"
    source = ingest_text(
        "Điều 1. Thông tin\nKhoản 1. Nội dung thử nghiệm.", actor="ADMIN:tester", database_path=path
    ).source
    monkeypatch.setattr(
        workflow, "propose_metadata", lambda *_args, **_kwargs: MetadataProposal(None, "timeout")
    )
    result = workflow.prepare_source(source, actor="ADMIN:tester", database_path=path)
    assert result.error == "timeout"
    stored = get_source(source.doc_id, database_path=path)
    assert stored is not None and stored.status is SourceStatus.PENDING_REVIEW
    assert get_source_content(source.doc_id, database_path=path) is not None


def test_seed_backfill_never_attaches_new_text_to_old_hash(tmp_path: Path) -> None:
    path = tmp_path / "seed.db"
    ensure_seeded(database_path=path)
    db.execute("DELETE FROM source_contents WHERE doc_id='RL-2026-3150'", database_path=path)
    db.execute(
        "UPDATE sources SET sha256='old-different-content' WHERE doc_id='RL-2026-3150'",
        database_path=path,
    )
    ensure_seeded(database_path=path)
    assert get_source_content("RL-2026-3150", database_path=path) is None


@pytest.mark.parametrize(
    "url", ["file:///private", "http://localhost/", "https://127.0.0.1/", "https://[::1]/"]
)
def test_source_url_rejects_private_or_non_https_targets(url: str) -> None:
    with pytest.raises(ValueError):
        _download_once(url)


def test_source_page_upload_and_approval_without_chunk_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "ui.db")
    monkeypatch.setenv("LLM_MODE", "replay")
    db.initialize_database()
    page = Path(__file__).resolve().parents[1] / "pages/3_Quan_tri_quy_dinh.py"
    app = AppTest.from_file(str(page)).run()
    assert not app.exception
    assert next(button for button in app.button if button.label == "Nạp và đọc tài liệu").disabled
    app.text_input(key="source-reviewer").set_value("Người thử nghiệm")
    app.text_input(key="new-title").set_value("Hướng dẫn thử nghiệm nguồn mới")
    next(area for area in app.text_area if area.label == "Nội dung văn bản").set_value(
        "Điều 5. Lệ phí\nKhoản 1. Lệ phí phúc khảo là 175.000 đồng."
    )
    app.run()
    next(button for button in app.button if button.label == "Nạp và đọc tài liệu").click().run()
    assert not app.exception
    next(widget for widget in app.text_input if widget.label == "Đơn vị ban hành").set_value(
        "Phòng Đào tạo giả lập"
    )
    next(widget for widget in app.date_input if widget.label == "Hiệu lực từ").set_value(
        date(2026, 8, 1)
    )
    next(widget for widget in app.multiselect if widget.label == "Lĩnh vực áp dụng").set_value(
        ["grade_appeal"]
    )
    next(
        widget
        for widget in app.checkbox
        if widget.label == "Áp dụng cho sinh viên đại học chính quy"
    ).check()
    next(widget for widget in app.checkbox if widget.label.startswith("Tôi đã đối chiếu")).check()
    next(
        widget for widget in app.text_area if widget.label == "Lý do xác nhận hoặc từ chối"
    ).set_value("Đã đọc bản gốc và xác nhận phạm vi.")
    next(
        button for button in app.button if button.label == "Xác nhận và đưa vào sử dụng"
    ).click().run()
    assert not app.exception and not app.error
    count = db.fetch_one("SELECT COUNT(*) AS n FROM sources WHERE status='ACTIVE'")
    assert count is not None and count["n"] == 1
    assert not any("Nhãn" in widget.label for widget in app.selectbox)


@pytest.mark.parametrize("operation", ["approve", "reject", "rollback"])
def test_source_transition_is_atomic_for_readers_and_rolls_back_on_audit_error(
    operation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "atomic.db"
    source = ingest_text(
        "Điều 1. Lệ phí\nKhoản 1. Lệ phí phúc khảo là 175.000 đồng.",
        actor="ADMIN:tester", database_path=path,
    ).source
    workflow.materialize_source(source, database_path=path)
    draft = MetadataDraft(
        source.doc_id, "Nguồn thử nghiệm", "Đơn vị giả lập", None, "2026-08-01", None,
        ("undergraduate",), ("K49",), (), False, ("grade_appeal",), "computed-later",
    )
    if operation == "rollback":
        source = workflow.approve_source(
            source, draft, actor="ADMIN:tester", reason="Đã đối chiếu nguồn", database_path=path
        )
        source = replace(source, status=SourceStatus.SUPERSEDED)
        update_source(source, database_path=path)
    tables = ("sources", "chunks", "source_contents", "settings", "corpus_versions", "audit_events")
    before = {table: db.fetch_all(f"SELECT * FROM {table}", database_path=path) for table in tables}
    previous_status = source.status.value

    def fail_audit(**_kwargs: object) -> str:
        with closing(sqlite3.connect(path)) as reader:
            row = reader.execute("SELECT status FROM sources WHERE doc_id = ?", (source.doc_id,)).fetchone()
            assert row is not None and row[0] == previous_status
        raise RuntimeError("Lỗi ghi nhật ký được chủ động tạo trong kiểm tra")

    monkeypatch.setattr(lifecycle, "log_event", fail_audit)
    with pytest.raises(RuntimeError):
        if operation == "approve":
            workflow.approve_source(
                source, draft, actor="ADMIN:tester", reason="Duyệt nguồn", database_path=path
            )
        elif operation == "reject":
            lifecycle.reject_source(source, actor="ADMIN:tester", reason="Từ chối", database_path=path)
        else:
            lifecycle.rollback_source(source, actor="ADMIN:tester", reason="Khôi phục", database_path=path)
    assert {table: db.fetch_all(f"SELECT * FROM {table}", database_path=path) for table in tables} == before
