from __future__ import annotations

import pytest

from infra.audit import events_for_case, log_event, recent_events


def test_case_lifecycle_has_a_continuous_audit_trail(tmp_path) -> None:
    database_path = str(tmp_path / "audit.db")
    case_id = "c-audit"
    actions = ("CASE_RECEIVED", "CASE_SANITIZED", "POLICY_DECIDED", "CASE_QUEUED")

    for action in actions:
        log_event(
            case_id=case_id,
            actor="SYSTEM",
            action=action,
            input_ref="email:masked",
            output_ref="case:c-audit",
            reason="Đã hoàn tất bước xử lý.",
            sources=["chunk-01"],
            corpus_version="cv-1",
            database_path=database_path,
        )

    events = events_for_case(case_id, database_path=database_path)

    assert [event.action for event in events] == list(actions)
    assert all(event.ts.endswith("Z") and event.reason and event.input_ref for event in events)
    assert events[0].sources == ["chunk-01"]
    assert recent_events(1, database_path=database_path)[0].action == "CASE_QUEUED"


@pytest.mark.parametrize(
    "action",
    ("OVERRIDE_DECISION", "PAUSE_AUTOMATION", "HUMAN_DECISION", "CANCEL_SEND"),
)
def test_reason_required_actions_reject_empty_reason(tmp_path, action: str) -> None:
    with pytest.raises(ValueError, match="bắt buộc có reason"):
        log_event(
            case_id="c-audit",
            actor="HUMAN:test",
            action=action,
            reason="   ",
            database_path=str(tmp_path / "audit.db"),
        )


def test_unknown_action_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="không hợp lệ"):
        log_event(
            case_id=None,
            actor="SYSTEM",
            action="NOT_A_REAL_ACTION",
            database_path=str(tmp_path / "audit.db"),
        )
