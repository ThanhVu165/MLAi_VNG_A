"""Offline contracts and synthetic R2 responses; no claim of LIVE model adherence."""

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

import pytest

from core import extract, pipeline
from core.policy_engine import PolicyInput, decide_policy
from core.prepolicy import decision_lock
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    Domain,
    EscalationCard,
    EscalationType,
    EvidenceResult,
    EvidenceStatus,
    Extraction,
    RequestItem,
)
from infra import db
from infra.llm import LLMResult


def test_prompt_separates_background_appeal_from_requested_action() -> None:
    prompt = extract.EXTRACT_PROMPT_V1.format(body="EMAIL_SENTINEL")
    assert prompt.endswith("Email:\nEMAIL_SENTINEL")
    for instruction in (
        "asks_appeal=true chỉ khi",
        "Không tạo request hành động riêng từ câu nêu dự định",
        '"Em muốn phúc khảo, cho em hỏi lệ phí và điều kiện miễn giảm?"',
        '"Em đề nghị xem xét lại điểm thi của em."',
        "Yêu cầu chấp thuận ngoại lệ vẫn cần thẩm quyền dù viết dưới dạng câu hỏi",
        "tách từng ý; giữ cờ thẩm quyền ở yêu cầu thực sự xin quyết định",
    ):
        assert instruction in prompt
    assert "M2DEV-" not in prompt


def test_appeal_schema_documents_intent_without_changing_boolean_contract() -> None:
    request = extract.EXTRACTION_SCHEMA["properties"]["requests"]["items"]
    appeal = request["properties"]["asks_appeal"]
    assert appeal["type"] == "boolean"
    assert "asks_appeal" in request["required"]
    assert "yêu cầu thực hiện" in appeal["description"]
    assert "dự định" in appeal["description"]
    assert "hỏi thông tin" in appeal["description"]


def _requests(scenario: str) -> list[RequestItem]:
    informational = RequestItem(
        Domain.GRADE_APPEAL, "Hỏi lệ phí phúc khảo", True, False, False, False, False
    )
    if scenario == "A4":
        return [
            RequestItem(Domain.GRADE_APPEAL, intent, True, False, False, False, False)
            for intent in (
                "Hỏi tổng lệ phí cho ba học phần",
                "Hỏi cách nộp lệ phí",
                "Hỏi chính sách miễn giảm cho diện hộ nghèo",
                "Hỏi chính sách hoàn lệ phí nếu điểm được sửa",
            )
        ]
    if scenario == "A1":
        return [
            informational,
            RequestItem(
                Domain.GRADE_APPEAL,
                "Xin gia hạn nộp phúc khảo",
                False,
                False,
                True,
                False,
                True,
            ),
            RequestItem(
                Domain.GRADE_APPEAL,
                "Nhờ xác nhận hồ sơ đã nộp có hợp lệ không",
                False,
                True,
                False,
                False,
                False,
            ),
        ]
    if scenario == "A2":
        return [
            RequestItem(
                Domain.COURSE_WITHDRAWAL,
                "Xin xác nhận cho rút học phần dù quá hạn",
                False,
                False,
                True,
                False,
                True,
            )
        ]
    if scenario == "mixed":
        return [
            informational,
            RequestItem(
                Domain.GRADE_APPEAL,
                "Cho em hỏi trường có thể phê duyệt cho em nộp trễ không?",
                False,
                False,
                True,
                False,
                True,
            ),
        ]
    if scenario == "actual-appeal":
        return [
            RequestItem(
                Domain.GRADE_APPEAL,
                "Cho em hỏi và nhờ thầy cô xem xét lại điểm thi của em",
                False,
                False,
                False,
                True,
                False,
            )
        ]
    return [informational]


@pytest.mark.parametrize(
    "scenario,evidence_status,expected_rule",
    [
        ("A4", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P02"),
        ("A1", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P01"),
        ("A2", EvidenceStatus.CONFLICTING_SOURCES, "P01"),
        ("mixed", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P01"),
        ("actual-appeal", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P01"),
        ("missing-fact", EvidenceStatus.FACT_MISSING, "P03"),
        ("routine", EvidenceStatus.OK, "P05"),
    ],
)
def test_prepolicy_and_rules_preserve_authority_and_fail_closed(
    monkeypatch, tmp_path, scenario, evidence_status, expected_rule
) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "rules.db")
    extraction = Extraction("vi", _requests(scenario), {}, [], False, "{}")
    lock = decision_lock(extraction)
    assert (lock is EscalationType.AUTHORITY_REQUIRED) == (expected_rule == "P01")
    result = decide_policy(
        PolicyInput(
            "offline-case",
            "SYSTEM",
            "cv_test",
            lock,
            EvidenceResult(evidence_status, [], []),
            False,
            False,
            False,
            False,
        )
    )
    assert result.rule_id == expected_rule
    assert result.decision is (
        Decision.AUTO_REPLY if expected_rule == "P05" else Decision.ESCALATE
    )


@pytest.mark.parametrize("asks_appeal,expected_rule", [(True, "P01"), (False, "P02")])
def test_spurious_appeal_flag_alone_explains_routing(
    monkeypatch, tmp_path, asks_appeal, expected_rule
):
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "causal.db")
    requests = _requests("A4")
    requests.append(
        RequestItem(
            Domain.GRADE_APPEAL,
            "Dự định phúc khảo vì điểm thấp",
            not asks_appeal,
            False,
            False,
            asks_appeal,
            False,
        )
    )
    extraction = Extraction("vi", requests, {}, [], False, "{}")
    decision = decide_policy(
        PolicyInput(
            "offline-causal",
            "SYSTEM",
            "cv_test",
            decision_lock(extraction),
            EvidenceResult(
                EvidenceStatus.NO_AUTHORITATIVE_SOURCE, [], ["unanswered_request"]
            ),
            False,
            False,
            False,
            False,
        )
    )
    assert decision.rule_id == expected_rule
    assert decision.decision is Decision.ESCALATE


@pytest.mark.parametrize(
    "scenario,evidence_status,expected_rule",
    [
        ("A4", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P02"),
        ("A1", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P01"),
        ("A2", EvidenceStatus.CONFLICTING_SOURCES, "P01"),
        ("mixed", EvidenceStatus.NO_AUTHORITATIVE_SOURCE, "P01"),
        ("missing-fact", EvidenceStatus.FACT_MISSING, "P03"),
    ],
)
def test_pipeline_routes_intended_r2_payload_without_mocking_policy(
    monkeypatch, tmp_path, scenario, evidence_status, expected_rule
) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "pipeline.db")
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: "cv_test")
    specs = json.loads(
        (Path(__file__).parents[1] / "verify/cases_m2_combined_dev.json").read_text(
            encoding="utf-8"
        )
    )
    raw = next(
        s["input"]
        for s in specs
        if s["id"] == f"M2DEV-{scenario if scenario in ('A1', 'A2', 'A4') else 'A4'}"
    )
    inp = CaseInput(
        **{**raw, "received_at": datetime.fromisoformat(raw["received_at"])}
    )
    if scenario == "mixed":
        inp = CaseInput(
            inp.sender,
            "Hỏi thủ tục và xin phê duyệt",
            "Cho em hỏi lệ phí phúc khảo và xin trường phê duyệt cho em nộp trễ.",
            inp.received_at,
            "paste",
        )
    requests = _requests(scenario)
    calls = []

    def synthetic_r2(prompt, **kwargs):
        calls.append(kwargs["step"])
        assert kwargs["step"] == "R2_extract"
        assert kwargs["schema"] is extract.EXTRACTION_SCHEMA
        assert inp.subject in prompt
        return LLMResult(
            True,
            {
                "language": "vi",
                "requests": [asdict(r) for r in requests],
                "critical_facts": (
                    [
                        {"name": "cohort", "value": "K48"},
                        {"name": "course_count", "value": "3 học phần"},
                    ]
                    if scenario == "A4"
                    else []
                ),
                "missing_critical_facts": [],
                "injection_suspected": False,
            },
            None,
            0,
            "offline-synthetic",
            "test",
        )

    monkeypatch.setattr(extract, "call_json", synthetic_r2)
    evidence = EvidenceResult(evidence_status, [], ["unanswered_request"])
    monkeypatch.setattr(pipeline, "retrieve_evidence", lambda **kwargs: evidence)
    # R4/R5 evidence is supplied; R2 parsing, R3, R6, persistence and R8 execute for real.
    monkeypatch.setattr(pipeline, "validate_evidence", lambda **kwargs: evidence)
    monkeypatch.setattr(
        pipeline,
        "generate_escalation_card",
        lambda **kwargs: EscalationCard(
            "Cần chuyên viên xác nhận",
            ["Yêu cầu đang chờ xác nhận"],
            [("Căn cứ kiểm thử offline", "Chưa đủ căn cứ trả lời.")],
            "Chuyên viên xác nhận hướng xử lý nào cho yêu cầu đang chờ xem xét?",
            ["Yêu cầu bổ sung căn cứ", "Chuyển đơn vị có thẩm quyền"],
            kwargs["escalation_type"],
            None,
        ),
    )
    result = pipeline.process_case(inp)
    expected_type = {
        "P01": EscalationType.AUTHORITY_REQUIRED,
        "P02": EscalationType.OUT_OF_POLICY,
        "P03": EscalationType.FACT_UNRESOLVED,
    }[expected_rule]
    assert calls == ["R2_extract"]
    assert result.extraction.requests == requests
    assert result.decision.rule_id == expected_rule
    assert result.decision.decision is Decision.ESCALATE
    assert result.decision.escalation_type is expected_type
    assert result.status is CaseStatus.AWAITING_HUMAN
    assert result.draft is None
    assert db.fetch_one("SELECT COUNT(*) AS n FROM drafts")["n"] == 0
    assert db.fetch_one("SELECT COUNT(*) AS n FROM escalations")["n"] == 1
