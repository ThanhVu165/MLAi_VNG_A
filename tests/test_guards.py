from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json

import core.pipeline as pipeline
from core.extract import EXTRACTION_SCHEMA, extract_facts
from core.sanitize import detect_language, mask_pii, sanitize_body
from core.types import CaseInput, CaseStatus, Decision
from infra import db
from infra.audit import events_for_case
from infra.llm import LLMResult


def _input(*, sender: str = "student@example.edu") -> CaseInput:
    return CaseInput(
        sender=sender,
        subject="Hỏi quy trình",
        body="Em cần biết quy trình xử lý yêu cầu này.",
        received_at=datetime(2026, 9, 21, 8, 30, tzinfo=timezone(timedelta(hours=7))),
        channel="paste",
    )


def test_r0_creates_one_case_and_freezes_corpus_version(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "app.db"
    versions = iter(("cv_before", "cv_after"))
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: next(versions))

    result = pipeline.process_case(_input())

    rows = db.fetch_all("SELECT * FROM cases", database_path=database_path)
    events = events_for_case(result.case_id, database_path=str(database_path))
    assert len(rows) == 1
    assert rows[0]["case_id"] == result.case_id
    assert rows[0]["status"] == CaseStatus.RECEIVED
    assert rows[0]["corpus_version"] == result.corpus_version == "cv_before"
    assert rows[0]["received_at"].endswith("Z")
    assert result.case_id.startswith("c_") and len(result.case_id) == 28
    assert len(events) == 1 and events[0].action == "CASE_RECEIVED"


def test_r0_marks_missing_required_input_invalid(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "app.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)

    result = pipeline.process_case(_input(sender=""))

    row = db.fetch_one(
        "SELECT status FROM cases WHERE case_id = ?", (result.case_id,), database_path=database_path
    )
    assert result.decision.decision is Decision.INVALID_INPUT
    assert result.status is CaseStatus.INVALID_INPUT
    assert row is not None and row["status"] == CaseStatus.INVALID_INPUT


def test_sanitize_removes_quotes_signatures_html_and_extra_whitespace() -> None:
    cases = (
        ("Em cần hỗ trợ.\nOn Tue, 21 Sep wrote:\n> Nội dung cũ", "Em cần hỗ trợ."),
        ("Cho em hỏi hạn nộp.\nVào 21/09, cô đã viết:\n> Nội dung cũ", "Cho em hỏi hạn nộp."),
        ("Em cần hỗ trợ.\n\nTrân trọng,\nNguyễn Văn A", "Em cần hỗ trợ."),
        (
            "Em cần hỗ trợ.\n--\nNguyễn Văn A\nEmail: a@example.edu\nĐiện thoại: 0900000000",
            "Em cần hỗ trợ.",
        ),
        ("<p>Em cần <b>hỗ trợ</b>.</p><p>Trân trọng,<br>Nguyễn Văn A</p>", "Em cần hỗ trợ."),
        ("Em   cần\n\n  Cà phe\u0302.", "Em cần Cà phê."),
    )

    assert [sanitize_body(raw) for raw, _ in cases] == [expected for _, expected in cases]


def test_detect_language_handles_vietnamese_english_and_other() -> None:
    cases = (
        ("Em muốn biết hạn rút học phần.", "vi"),
        ("Xin cho em hỏi quy định phúc khảo điểm.", "vi"),
        ("Toi muon hoi han rut mon la khi nao", "vi"),
        ("Cho em biet cach tinh diem ren luyen", "vi"),
        ("Vui long huong dan thu tuc rut hoc phan", "vi"),
        ("What is the deadline for course withdrawal?", "en"),
        ("Please explain the grade appeal process.", "en"),
        ("Can I see my conduct score?", "en"),
        ("こんにちは、質問があります", "other"),
        ("Это вопрос о курсе", "other"),
    )

    assert [detect_language(body) for body, _ in cases] == [expected for _, expected in cases]


def test_mask_pii_and_keep_audit_free_of_raw_values(monkeypatch, tmp_path) -> None:
    body = (
        "MSSV 12345678901, CCCD 012345678901, SĐT 0912345678, "
        "email student.name+test@example.edu."
    )
    masked = mask_pii(body)
    assert masked == "MSSV [MSSV], CCCD [CCCD], SĐT [SĐT], email [EMAIL]."

    database_path = tmp_path / "app.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    inp = CaseInput(
        sender="student@example.edu",
        subject="Hỏi quy định",
        body=body,
        received_at=datetime(2026, 9, 21, 8, 30, tzinfo=timezone.utc),
        channel="paste",
    )
    result = pipeline.process_case(inp)
    row = db.fetch_one(
        "SELECT body_raw, body_masked FROM cases WHERE case_id = ?",
        (result.case_id,),
        database_path=database_path,
    )
    assert row is not None and row["body_raw"] == body and row["body_masked"] == masked
    audit_json = json.dumps([asdict(event) for event in events_for_case(result.case_id)])
    assert all(
        value not in audit_json
        for value in ("12345678901", "012345678901", "0912345678", "student.name+test@example.edu")
    )


def test_extract_uses_schema_and_maps_eight_domain_samples(monkeypatch) -> None:
    domains = iter(
        (
            "conduct_score",
            "course_withdrawal",
            "grade_appeal",
            "conduct_score",
            "course_withdrawal",
            "grade_appeal",
            "conduct_score",
            "course_withdrawal",
        )
    )

    def fake_call(prompt: str, **kwargs: object) -> LLMResult:
        assert "chỉ trích xuất" in prompt.lower()
        assert kwargs["schema"] == EXTRACTION_SCHEMA
        assert kwargs["step"] == "R2_extract"
        assert kwargs["temperature"] == 0.0
        domain = next(domains)
        return LLMResult(
            ok=True,
            data={
                "language": "vi",
                "requests": [
                    {
                        "domain": domain,
                        "intent": "information",
                        "is_informational": True,
                        "requires_personal_record": False,
                        "asks_exception": False,
                        "asks_appeal": False,
                        "asks_authority_decision": False,
                    }
                ],
                "critical_facts": {},
                "missing_critical_facts": [],
                "injection_suspected": False,
            },
            error=None,
            latency_ms=0,
            prompt_hash="test",
            model="replay",
        )

    monkeypatch.setattr("core.extract.call_json", fake_call)
    extractions = [extract_facts(f"Email mẫu {index}", f"case-{index}") for index in range(8)]

    assert all(extraction.llm_error is None for extraction in extractions)
    assert [extraction.requests[0].domain.value for extraction in extractions] == [
        "conduct_score",
        "course_withdrawal",
        "grade_appeal",
        "conduct_score",
        "course_withdrawal",
        "grade_appeal",
        "conduct_score",
        "course_withdrawal",
    ]
    required = EXTRACTION_SCHEMA["required"]
    assert isinstance(required, list)
    assert set(required) == {
        "language",
        "requests",
        "critical_facts",
        "missing_critical_facts",
        "injection_suspected",
    }


def test_extraction_schema_uses_gemini_supported_fields() -> None:
    """SDK 0.8.3 chỉ nhận OpenAPI Schema subset cho response_schema."""
    assert "additionalProperties" not in EXTRACTION_SCHEMA
    requests = EXTRACTION_SCHEMA["properties"]
    assert isinstance(requests, dict)
    request_items = requests["requests"]
    assert isinstance(request_items, dict)
    assert "additionalProperties" not in request_items["items"]
    assert "additionalProperties" not in requests["critical_facts"]
