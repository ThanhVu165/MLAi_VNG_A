"""Offline prompt contract and intended payloads; these do not prove model adherence."""

from dataclasses import asdict

import pytest

import core.extract as extract
from core.policy_engine import PolicyInput, decide_policy
from core.prepolicy import decision_lock
from core.types import (
    Decision,
    Domain,
    EscalationType,
    EvidenceResult,
    EvidenceStatus,
    RequestItem,
)
from infra import db
from infra.llm import LLMResult


def test_prompt_distinguishes_applicability_record_access_and_approval() -> None:
    prompt = extract.EXTRACT_PROMPT_V1.format(body="EMAIL_SENTINEL")
    assert prompt.endswith("Email:\nEMAIL_SENTINEL")
    for contract in (
        '"Quy định đánh giá điểm rèn luyện nào đang áp dụng cho em?"\n'
        "→ is_informational=true, requires_personal_record=false, asks_exception=false,\n"
        "asks_appeal=false, asks_authority_decision=false.",
        "Cần biết cohort, semester, academic_year hoặc applies_to không tự có nghĩa là cần xem hồ sơ",
        "giữ missing_critical_facts=[] ở bước này",
        "requires_personal_record=true chỉ khi trả lời cần xem trạng thái hồ sơ cá nhân riêng tư",
        '"Điểm rèn luyện hiện tại của em trên hệ thống là bao nhiêu?" cần xem hồ sơ cá nhân.',
        '"Quy định nào áp dụng cho sinh viên K49?" không cần xem hồ sơ cá nhân.',
        'Các từ "cho em", "áp dụng cho em", "trường hợp của em" riêng lẻ không chứng minh cần xem hồ sơ.',
        "asks_authority_decision=true chỉ khi sinh viên xin trường hoặc người có thẩm quyền phê duyệt",
        '"Em đã quá hạn, xin trường chấp thuận cho em rút học phần." → asks_authority_decision=true.',
        '"Cho em hỏi ai có quyền duyệt phúc khảo?" chỉ hỏi thông tin: is_informational=true,\n'
        "requires_personal_record=false, asks_exception=false, asks_appeal=false, asks_authority_decision=false.",
        "vẫn tách yêu cầu đó và giữ các cờ tương ứng; không xóa cờ.",
    ):
        assert contract in prompt


@pytest.mark.parametrize(
    "body,domain,flags,evidence_status,expected_rule",
    [
        (
            "Em muốn hỏi quy định đánh giá điểm rèn luyện nào đang áp dụng cho em, cảm ơn thầy.",
            Domain.CONDUCT_SCORE,
            (True, False, False, False, False),
            EvidenceStatus.FACT_MISSING,
            "P03",
        ),
        (
            "Em đã quá hạn nhưng xin được miễn điều kiện và cho rút học phần vì hoàn cảnh gia đình. "
            "Mong trường quyết định chấp thuận cho hồ sơ của em.",
            Domain.COURSE_WITHDRAWAL,
            (False, True, True, False, True),
            EvidenceStatus.FACT_MISSING,
            "P01",
        ),
        (
            "Điểm rèn luyện hiện tại của em trên hệ thống là bao nhiêu?",
            Domain.CONDUCT_SCORE,
            (False, True, False, False, False),
            EvidenceStatus.OK,
            "P01",
        ),
        (
            "Cho em hỏi ai có quyền duyệt phúc khảo?",
            Domain.GRADE_APPEAL,
            (True, False, False, False, False),
            EvidenceStatus.OK,
            "P05",
        ),
        (
            "Em đề nghị phúc khảo điểm thi của em.",
            Domain.GRADE_APPEAL,
            (False, False, False, True, False),
            EvidenceStatus.OK,
            "P01",
        ),
    ],
    ids=["E04-applicability", "E05-exception", "record-lookup", "authority-procedure", "actual-appeal"],
)
def test_intended_extraction_preserves_flags_and_downstream_policy(
    monkeypatch, tmp_path, body, domain, flags, evidence_status, expected_rule
) -> None:
    # The response is synthetic: only parsing and downstream rules execute here.
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "offline.db")
    request = RequestItem(domain, body, *flags)

    def fake_call(prompt, **kwargs):
        assert prompt.endswith(f"Email:\n{body}")
        assert kwargs["schema"] is extract.EXTRACTION_SCHEMA
        assert kwargs["step"] == "R2_extract"
        return LLMResult(
            True,
            {
                "language": "vi",
                "requests": [asdict(request)],
                "critical_facts": [],
                "missing_critical_facts": [],
                "injection_suspected": False,
            },
            None,
            0,
            "offline-contract",
            "test",
        )

    monkeypatch.setattr(extract, "call_json", fake_call)
    extraction = extract.extract_facts(body, "offline-case")
    assert extraction.llm_error is None
    assert extraction.requests == [request]
    assert extraction.critical_facts == {}
    assert extraction.missing_critical_facts == []
    lock = decision_lock(extraction)
    expected_type = {
        "P01": EscalationType.AUTHORITY_REQUIRED,
        "P03": EscalationType.FACT_UNRESOLVED,
        "P05": None,
    }[expected_rule]
    assert lock == (EscalationType.AUTHORITY_REQUIRED if expected_rule == "P01" else None)
    evidence = EvidenceResult(
        evidence_status, [], ["facts"] if evidence_status is EvidenceStatus.FACT_MISSING else []
    )
    decision = decide_policy(
        PolicyInput("offline-case", "SYSTEM", "cv_test", lock, evidence, False, False, False, False)
    )
    assert decision.rule_id == expected_rule
    assert decision.escalation_type == expected_type
    assert decision.decision is (Decision.AUTO_REPLY if expected_rule == "P05" else Decision.ESCALATE)
