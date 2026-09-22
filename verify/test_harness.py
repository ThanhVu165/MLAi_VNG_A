from __future__ import annotations

import json

from infra import db
from infra.audit import recent_events
from core.types import Decision, EscalationType
from verify import harness
from verify.harness import VerifyResult, run_cases


def test_run_cases_uses_pipeline_and_audits_run(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_MODE", "replay")
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "id": "T01",
                    "input": {
                        "sender": "student@example.edu",
                        "subject": "Hỏi thông tin",
                        "body": "Em cần biết quy trình điểm rèn luyện trong học kỳ một năm học 2026-2027 và thời hạn công bố.",
                        "received_at": "2026-09-22T09:00:00+07:00",
                    },
                    "expected_decision": "ESCALATE",
                    "expected_type": "FACT_UNRESOLVED",
                }
            ]
        ),
        encoding="utf-8",
    )

    results = run_cases(cases_path, run_name="unit")

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].timestamp.endswith("+07:00")
    assert {event.action for event in recent_events()} >= {
        "VERIFY_RUN_STARTED",
        "VERIFY_RUN_FINISHED",
    }


def test_main_returns_nonzero_when_any_case_fails(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    failed = VerifyResult(
        "T01",
        "Hỏi thông tin",
        None,
        Decision.AUTO_REPLY,
        None,
        Decision.ESCALATE,
        EscalationType.FACT_UNRESOLVED,
        "P04",
        False,
        1,
        "2026-09-22T09:00:00+07:00",
        "cv_test",
        "case-test",
    )
    monkeypatch.setattr(harness, "run_cases", lambda *_args, **_kwargs: (failed,))

    assert harness.main(["--set", "verify4"]) == 1
    assert "FAIL" in capsys.readouterr().out
