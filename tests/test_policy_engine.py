from pathlib import Path

import yaml  # type: ignore[import-untyped]

import core.policy_engine as policy_engine
from core.policy_engine import PolicyInput, decide_policy
from core.types import Decision, EscalationType, EvidenceResult, EvidenceStatus
from infra import db
from infra.audit import events_for_case

POLICIES_DIR = Path(__file__).parents[1] / "policies"


def test_policy_configuration_is_valid_and_complete() -> None:
    policy = yaml.safe_load((POLICIES_DIR / "policy.yaml").read_text(encoding="utf-8"))
    blocklist = yaml.safe_load((POLICIES_DIR / "blocklist.yaml").read_text(encoding="utf-8"))
    fallbacks = yaml.safe_load(
        (POLICIES_DIR / "fallback_questions.yaml").read_text(encoding="utf-8")
    )

    assert [rule["id"] for rule in policy["priority_order"]] == ["P01", "P02", "P03", "P04", "P05"]
    assert all(rule["reason_vi"] for rule in policy["priority_order"])
    assert "vui lòng xem xét" in blocklist["phrases"]
    assert set(fallbacks["templates"]) == {
        "FACT_UNRESOLVED",
        "OUT_OF_POLICY",
        "AUTHORITY_REQUIRED",
    }
    for template in fallbacks["templates"].values():
        assert set(template) == {"summary", "facts", "basis", "question", "options"}
        assert 2 <= len(template["options"]) <= 3


def _policy_input(
    *,
    decision_lock: EscalationType | None = None,
    evidence_status: EvidenceStatus = EvidenceStatus.OK,
    llm_error: bool = False,
    parse_error: bool = False,
    timeout: bool = False,
    guard_failed: bool = False,
) -> PolicyInput:
    return PolicyInput(
        case_id="case-policy",
        actor="SYSTEM",
        corpus_version="cv_test",
        decision_lock=decision_lock,
        evidence=EvidenceResult(evidence_status, [], []),
        llm_error=llm_error,
        parse_error=parse_error,
        timeout=timeout,
        guard_failed=guard_failed,
    )


def test_policy_engine_covers_p01_to_p05(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    cases = (
        (_policy_input(decision_lock=EscalationType.AUTHORITY_REQUIRED), "P01", Decision.ESCALATE),
        (
            _policy_input(evidence_status=EvidenceStatus.NO_AUTHORITATIVE_SOURCE),
            "P02",
            Decision.ESCALATE,
        ),
        (_policy_input(evidence_status=EvidenceStatus.FACT_MISSING), "P03", Decision.ESCALATE),
        (_policy_input(llm_error=True), "TECHNICAL_ERROR", Decision.ERROR),
        (_policy_input(), "P05", Decision.AUTO_REPLY),
    )

    for inp, rule_id, decision in cases:
        result = decide_policy(inp)
        assert result.rule_id == rule_id and result.decision is decision


def test_policy_engine_prioritizes_lock_and_fails_safe(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    lock_with_evidence = decide_policy(
        _policy_input(decision_lock=EscalationType.AUTHORITY_REQUIRED)
    )
    lock_with_failed_evidence = decide_policy(
        _policy_input(
            decision_lock=EscalationType.AUTHORITY_REQUIRED,
            evidence_status=EvidenceStatus.FACT_MISSING,
        )
    )
    failures = (
        decide_policy(_policy_input(llm_error=True)),
        decide_policy(_policy_input(parse_error=True)),
        decide_policy(_policy_input(timeout=True)),
        decide_policy(_policy_input(guard_failed=True)),
    )

    assert lock_with_evidence.rule_id == lock_with_failed_evidence.rule_id == "P01"
    assert lock_with_evidence.escalation_type is EscalationType.AUTHORITY_REQUIRED
    assert lock_with_failed_evidence.decision is Decision.ESCALATE
    assert all(result.decision is Decision.ERROR for result in failures[:3])
    assert failures[3].rule_id == "P04" and failures[3].decision is Decision.ESCALATE


def test_policy_engine_audits_rule_and_falls_back_when_no_rule_matches(
    monkeypatch, tmp_path
) -> None:
    database_path = tmp_path / "app.db"
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", database_path)
    monkeypatch.setattr(policy_engine, "_load_rules", lambda: [])

    result = decide_policy(_policy_input())
    events = events_for_case("case-policy", database_path=str(database_path))

    assert result.rule_id == "TECHNICAL_ERROR" and result.decision is Decision.ERROR
    assert [event.action for event in events] == ["POLICY_DECIDED"]
    assert events[0].rule_id == "TECHNICAL_ERROR"
