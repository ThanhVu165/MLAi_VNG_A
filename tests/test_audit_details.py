from __future__ import annotations

from infra.audit import events_for_case, log_event, recent_events


def test_admin_and_corpus_events_keep_auditable_fields(tmp_path) -> None:
    database_path = str(tmp_path / "audit-details.db")
    log_event(
        case_id=None,
        actor="ADMIN:lan",
        action="PAUSE_AUTOMATION",
        input_ref="setting:automation",
        reason="Tạm dừng để kiểm tra sự cố.",
        corpus_version="cv-4",
        database_path=database_path,
    )
    log_event(
        case_id="c-04",
        actor="ADMIN:lan",
        action="ACTIVATE_SOURCE",
        input_ref="source:RL-2026",
        output_ref="source:ACTIVE",
        reason="Đã duyệt quy định mới.",
        sources=["RL-2026/Điều 3"],
        corpus_version="cv-5",
        database_path=database_path,
    )

    event = events_for_case("c-04", database_path=database_path)[0]

    assert event.action == "ACTIVATE_SOURCE"
    assert event.input_ref == "source:RL-2026"
    assert event.sources == ["RL-2026/Điều 3"]
    assert event.reason == "Đã duyệt quy định mới."
    assert event.corpus_version == "cv-5"
    assert event.ts.endswith("Z")
    assert len(recent_events(limit=None, database_path=database_path)) == 2
