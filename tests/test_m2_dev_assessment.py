"""Chỉ dùng PipelineResult synthetic; cấm network/provider/pipeline thật."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, replace
from datetime import date, datetime, timezone

import pytest

from core.types import (
    CaseStatus,
    ChunkLabel,
    Decision,
    Domain,
    DraftReply,
    EscalationCard,
    EscalationType,
    EvidenceChunk,
    EvidenceResult,
    EvidenceStatus,
    PipelineResult,
    PolicyDecision,
)
from verify import m2_dev_assessment as dev


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Network/provider/pipeline thật bị cấm")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    from infra import llm
    from core import pipeline

    monkeypatch.setattr(llm, "call_json", forbidden)
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setattr(pipeline, "process_case", forbidden)


def result(case_id="M2DEV-A1"):
    spec = dev.load_prereg(case_id)
    decision = Decision(spec["expected_decision"])
    kind = EscalationType(spec["expected_type"]) if spec["expected_type"] else None
    chunk = EvidenceChunk(
        "PK-2026-204:seed:1",
        "PK-2026-204",
        "Điều 1",
        "Lệ phí 150.000 đồng.",
        Domain.GRADE_APPEAL,
        ChunkLabel.AUTO_ANSWERABLE,
        0.9,
        date(2026, 8, 15),
        None,
        [],
        [],
        False,
        False,
    )
    card = (
        EscalationCard(
            "Cần chuyên viên xem xét.",
            ["Có yêu cầu ngoài phạm vi trả lời."],
            [(chunk.breadcrumb, chunk.text)],
            "Chuyên viên có thể xác nhận yêu cầu này không?",
            ["Có", "Không"],
            kind,
            None,
        )
        if decision is Decision.ESCALATE
        else None
    )
    draft = (
        DraftReply(
            "Thông tin", "Lệ phí 150.000 đồng. [PK-2026-204:seed:1]", [chunk.chunk_id], True, []
        )
        if decision is Decision.AUTO_REPLY
        else None
    )
    now = datetime(2026, 10, 8, tzinfo=timezone.utc)
    return PipelineResult(
        "synthetic-pipeline-case",
        "synthetic-trace",
        CaseStatus.AWAITING_HUMAN if card else CaseStatus.PENDING_SEND,
        PolicyDecision(
            decision,
            kind,
            spec["expected_rule_id"],
            "Synthetic.",
            [chunk.chunk_id],
            "synthetic-corpus",
        ),
        None,
        EvidenceResult(EvidenceStatus.OK, [chunk], []),
        draft,
        card,
        "synthetic-corpus",
        {"R2": 100},
        now,
        now,
    )


def bound_capture_result(pipeline_result, *, case_id, observation_id, **kwargs):
    submitted = dev.load_prereg(case_id)["input"]
    execution = dev.execution_context(
        submitted, pipeline_result, case_id=case_id, observation_id=observation_id
    )
    return dev.capture_result(
        pipeline_result,
        case_id=case_id,
        observation_id=observation_id,
        execution=execution,
        **kwargs,
    )


def capture(case_id="M2DEV-A1", pipeline_result=None):
    return bound_capture_result(
        pipeline_result or result(case_id),
        case_id=case_id,
        observation_id="synthetic-1",
        config={"LLM_PROVIDER": "openai", "OPENAI_MODEL": "offline-mock"},
    )


def judgment(captured, dimension, verdict="PASS"):
    return dev.ReviewDecision(
        dimension,
        verdict,
        "Synthetic reviewer judgment cho đúng criterion; không phải automatic semantic proof.",
        [
            dev.EvidenceReference(path, quote)
            for path, quote in dev.review_scope(captured, dimension).items()
        ],
    )


def reviewed(captured, verdict="PASS", all_criteria=True):
    assessment = dev.assess_capture(captured)
    mapping = dev.criterion_dimensions(captured.case_id)
    ids = list(mapping) if all_criteria else [next(iter(mapping))]
    mapped = {name for names in mapping.values() for name in names}
    return dev.HumanReview(
        dev.capture_hash(captured),
        "synthetic-reviewer",
        "2026-10-09T12:00:00+07:00",
        [
            dev.CriterionReview(key, [judgment(captured, name, verdict) for name in mapping[key]])
            for key in ids
        ],
        [
            judgment(captured, name, verdict)
            for name, item in assessment.dimensions.items()
            if item.status == "REVIEW_REQUIRED" and name not in mapped
        ],
    )


def test_structurally_correct_fabricated_option_is_not_full_pass():
    r = result()
    r.card.options = ["Gia hạn 5 ngày", "Gia hạn 10 ngày"]
    assessment = dev.assess_capture(capture(pipeline_result=r))
    assert assessment.dimensions["decision_match"].status == "PASS"
    assert assessment.verdict == "REVIEW_REQUIRED"
    assert assessment.dimensions["options_quality"].status == "REVIEW_REQUIRED"
    assert any("5 ngày" in item for item in assessment.risk_findings)


def test_wrong_decision_fails():
    r = result()
    r.decision.decision = Decision.AUTO_REPLY
    a = dev.assess_capture(capture(pipeline_result=r))
    assert a.verdict == "FAIL"
    assert a.dimensions["decision_match"].status == "FAIL"
    assert a.dimensions["decision_match"].evidence


def test_p05_unsupported_claim_not_pass_even_if_runtime_guard_passed():
    r = result("M2DEV-B2")
    r.draft.body = "Bạn sẽ được hoàn 90% trong 3 ngày."
    a = dev.assess_capture(capture("M2DEV-B2", r))
    assert a.dimensions["decision_match"].status == "PASS"
    assert a.verdict == "REVIEW_REQUIRED"


def test_supported_conflict_comparison_not_automatic_fail():
    r = result("M2DEV-B3")
    r.card.facts = ["RH ghi 70%; HP ghi 60%; hai nguồn mâu thuẫn, chưa chọn tỷ lệ."]
    r.card.options = ["Xin xác nhận tỷ lệ", "Yêu cầu đối chiếu hai nguồn"]
    a = dev.assess_capture(capture("M2DEV-B3", r))
    assert a.verdict == "REVIEW_REQUIRED"
    assert all(d.status != "FAIL" for d in a.dimensions.values())
    assert a.dimensions["selective_conflict_handling"].status == "REVIEW_REQUIRED"


def test_unqualified_approved_refund_fails_when_human_establishes_claim():
    r = result("M2DEV-B2")
    r.draft.body = "Bạn đã được duyệt hoàn 90% học phí."
    c = capture("M2DEV-B2", r)
    review = dev.HumanReview(
        dev.capture_hash(c),
        "synthetic-reviewer",
        "2026-10-09T12:00:00+07:00",
        [
            dev.CriterionReview(
                "forbidden_assumptions:0",
                [
                    dev.ReviewDecision(
                        "grounding_and_citation",
                        "FAIL",
                        "Xác nhận private approval/90% không có nguồn.",
                        [dev.EvidenceReference("/result/draft/body", r.draft.body)],
                    )
                ],
            )
        ],
    )
    assert dev.assess_capture(c, review=review).verdict == "FAIL"


@pytest.mark.parametrize("field", ["question", "options"])
def test_missing_escalation_content_fails(field):
    r = result()
    setattr(r.card, field, "" if field == "question" else [])
    a = dev.assess_capture(capture(pipeline_result=r))
    assert a.verdict == "FAIL"
    assert a.dimensions[field + "_quality"].status == "FAIL"


def test_technical_error_separate_from_semantic_escalation():
    r = result()
    r.decision = PolicyDecision(Decision.ERROR, None, "TECHNICAL_ERROR", "Timeout.", [], "cv")
    r.status = CaseStatus.ERROR
    r.card = None
    a = dev.assess_capture(capture(pipeline_result=r))
    assert a.verdict == "TECHNICAL_ERROR"
    assert a.dimensions["technical_error"].status == "FAIL"
    assert a.dimensions["case_status_consistency"].status == "PASS"


def test_missing_assessment_evidence_requires_review():
    c = capture(pipeline_result=replace(result(), evidence=None))
    a = dev.assess_capture(c)
    assert a.verdict == "REVIEW_REQUIRED"
    assert c.diagnostics["provider_attempts"] is None
    assert c.diagnostics["source_status"] is None
    assert a.dimensions["grounding_and_citation"].evidence


def test_valid_full_review_can_pass_without_mutating_capture():
    c = capture()
    before = asdict(c)
    a = dev.assess_capture(c, review=reviewed(c))
    assert a.verdict == "PASS"
    assert asdict(c) == before


def test_incomplete_rubric_coverage_never_full_pass():
    c = capture()
    a = dev.assess_capture(c, review=reviewed(c, all_criteria=False))
    assert a.verdict == "REVIEW_REQUIRED"
    assert any(c.status == "REVIEW_REQUIRED" for c in a.criteria.values())


def test_content_review_cannot_use_only_correct_route_as_evidence():
    c = capture()
    row = dev.CriterionReview(
        "pass_criteria:2",
        [
            dev.ReviewDecision(
                "grounding_and_citation",
                "PASS",
                "Test.",
                [dev.EvidenceReference("/result/decision/rule_id", "P01")],
            )
        ],
    )
    review = replace(reviewed(c), criteria=[row])
    with pytest.raises(ValueError, match="không thuộc dimension"):
        dev.assess_capture(c, review=review)


def test_multiline_output_quote_is_verified_against_actual_text():
    r = result()
    r.card.options = ["Xin xác nhận\nquyết định", "Chưa quyết định"]
    c = capture(pipeline_result=r)
    assert dev.assess_capture(c, review=reviewed(c)).verdict == "PASS"


def test_tokens_redacted_and_unsanitized_capture_not_written(tmp_path):
    r = result()
    r.decision.reason = "Authorization: Bearer fake-test-token"
    c = capture(pipeline_result=r)
    assert "fake-test-token" not in json.dumps(asdict(c))
    unsafe = replace(c, config={"OPENAI_API_KEY": "fake-test-value"})
    with pytest.raises(ValueError):
        dev.write_artifacts(tmp_path / "must-not-exist", unsafe)
    assert not (tmp_path / "must-not-exist").exists()


@pytest.mark.parametrize(
    "problem",
    ["duplicate", "missing_rationale", "wrong_quote", "unknown_ref", "wrong_hash", "override"],
)
def test_invalid_or_contradictory_review_rejected(problem):
    c = capture()
    review = reviewed(c)
    row = review.criteria[0]
    item = row.judgments[0]
    if problem == "duplicate":
        review = replace(
            review, criteria=[row, replace(row, judgments=[replace(item, verdict="FAIL")])]
        )
    elif problem == "missing_rationale":
        review = replace(review, criteria=[replace(row, judgments=[replace(item, rationale="")])])
    elif problem == "wrong_quote":
        review = replace(
            review,
            criteria=[
                replace(
                    row,
                    judgments=[
                        replace(
                            item,
                            evidence=[
                                dev.EvidenceReference("/result/decision/decision", "không tồn tại")
                            ],
                        )
                    ],
                )
            ],
        )
    elif problem == "unknown_ref":
        review = replace(review, criteria=[replace(row, criterion_id="invented:0")])
    elif problem == "wrong_hash":
        review = replace(review, capture_sha256="wrong-capture")
    else:
        review = replace(
            review, criteria=[replace(row, judgments=[replace(item, dimension="options_quality")])]
        )
    with pytest.raises(ValueError):
        dev.assess_capture(c, review=review)


def test_fixture_hash_mismatch_fails_closed(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_bytes(dev.FIXTURE.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="BLOCKED_FIXTURE_HASH_MISMATCH"):
        dev.capture_result(result(), case_id="M2DEV-A1", observation_id="x", fixture=fixture)
    with pytest.raises(ValueError, match="BLOCKED_FIXTURE_HASH_MISMATCH"):
        dev.assess_capture(capture(), fixture=fixture)


def test_artifacts_cli_and_review_preserve_raw_capture(tmp_path):
    c = capture()
    first = tmp_path / "unreviewed"
    dev.write_artifacts(first, c)
    original = (first / "capture.json").read_bytes()
    review = reviewed(c)
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(asdict(review)), encoding="utf-8")
    second = tmp_path / "reviewed"
    assert (
        dev.main(
            [
                "--capture",
                str(first / "capture.json"),
                "--review",
                str(review_path),
                "--output",
                str(second),
            ]
        )
        == 0
    )
    assert (
        (first / "capture.json").read_bytes() == original == (second / "capture.json").read_bytes()
    )
    assert json.loads((second / "assessment.json").read_text(encoding="utf-8"))["verdict"] == "PASS"
    assert (second / "human_review.json").is_file()
    assert "NOT Set B" in (second / "report.md").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        dev.write_artifacts(first, c)


def test_guard_failure_is_definitive_structured_grounding_failure():
    r = result("M2DEV-B2")
    r.draft.grounded = False
    r.draft.guard_failures = ["unsupported_value"]
    assert dev.assess_capture(capture("M2DEV-B2", r)).verdict == "FAIL"


def test_capture_keeps_diagnostic_availability_without_inventing_attempts():
    r = result()
    d = dev.CaptureDiagnostics(source_status={"PK-2026-204": "ACTIVE"}, guard_failures=[])
    c = bound_capture_result(r, case_id="M2DEV-A1", observation_id="x", diagnostics=d)
    assert c.result["card"]["basis"] == [["Điều 1", "Lệ phí 150.000 đồng."]]
    assert c.result["evidence"]["chunks"][0]["doc_id"] == "PK-2026-204"
    assert c.result["started_at"] == r.started_at.isoformat()
    assert c.diagnostics["provider_attempts"] is None
    assert c.diagnostics["logical_calls"] is None
    assert c.diagnostics["cost"] is None
    assert c.diagnostics["guard_failures"] == []
    with pytest.raises(ValueError):
        bound_capture_result(
            r, case_id="M2DEV-A1", observation_id="x", config={"OPENAI_API_KEY": "fake"}
        )
    with pytest.raises(ValueError):
        bound_capture_result(
            r,
            case_id="M2DEV-A1",
            observation_id="x",
            diagnostics=dev.CaptureDiagnostics(provider_attempts=[{"body": "fake"}]),
        )


def test_temporal_reference_and_stale_source_remain_reviewable():
    c = capture("M2DEV-C1")
    a = dev.assess_capture(c)
    assert "2026-09-25" in a.dimensions["temporal_safety"].evidence[0]
    stale = bound_capture_result(
        result("M2DEV-C4"),
        case_id="M2DEV-C4",
        observation_id="x",
        diagnostics=dev.CaptureDiagnostics(source_status={"RL-2025-2363": "SUPERSEDED"}),
    )
    a = dev.assess_capture(stale)
    assert a.verdict == "REVIEW_REQUIRED"
    assert any("SUPERSEDED" in e for e in a.dimensions["grounding_and_citation"].evidence)


def test_mapping_covers_every_frozen_criterion_in_all_twelve_cases():
    for item in json.loads(dev.FIXTURE.read_bytes()):
        expected = {
            f"{group}:{i}"
            for group in ("pass_criteria", "fail_signals", "forbidden_assumptions")
            for i, _ in enumerate(item["meta"][group])
        }
        mapping = dev.criterion_dimensions(item["id"])
        assert set(mapping) == expected
        assert all(names and set(names) <= set(dev.DIMENSIONS) for names in mapping.values())


def test_missing_criterion_or_multi_dimension_judgment_cannot_pass():
    c = capture()
    review = reviewed(c)
    assert (
        dev.assess_capture(c, review=replace(review, criteria=review.criteria[:-1])).verdict
        == "REVIEW_REQUIRED"
    )
    duration = next(row for row in review.criteria if row.criterion_id == "pass_criteria:1")
    partial = replace(duration, judgments=duration.judgments[:-1])
    rows = [partial if row.criterion_id == partial.criterion_id else row for row in review.criteria]
    a = dev.assess_capture(c, review=replace(review, criteria=rows))
    assert a.criteria[partial.criterion_id].status == "REVIEW_REQUIRED"
    assert a.verdict == "REVIEW_REQUIRED"


def test_generic_quote_reused_for_unrelated_criteria_is_not_coverage():
    c = capture()
    review = reviewed(c)
    rows = []
    for row in review.criteria:
        judgments = [
            (
                replace(
                    j,
                    evidence=[
                        dev.EvidenceReference("/result/card/summary", "Cần chuyên viên xem xét.")
                    ],
                )
                if j.dimension == "grounding_and_citation"
                else j
            )
            for j in row.judgments
        ]
        rows.append(replace(row, judgments=judgments))
    a = dev.assess_capture(c, review=replace(review, criteria=rows))
    assert a.verdict == "REVIEW_REQUIRED"
    assert a.criteria["pass_criteria:1"].status == "REVIEW_REQUIRED"
    assert a.criteria["pass_criteria:2"].status == "REVIEW_REQUIRED"


def test_automatic_fail_cannot_be_overridden_by_criterion_review():
    r = result()
    r.decision.rule_id = "P02"
    c = capture(pipeline_result=r)
    with pytest.raises(ValueError, match="override automatic"):
        dev.assess_capture(c, review=reviewed(c))
    assert dev.assess_capture(c).verdict == "FAIL"


def test_old_review_json_is_rejected_clearly(tmp_path):
    c = capture()
    capture_path = tmp_path / "capture.json"
    capture_path.write_text(json.dumps(asdict(c)), encoding="utf-8")
    old = tmp_path / "old-review.json"
    old.write_text(
        json.dumps(
            {
                "capture_sha256": dev.capture_hash(c),
                "reviewer": "old",
                "reviewed_at": "2026-10-09T12:00:00+07:00",
                "decisions": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="REVIEW_SCHEMA_V2_REQUIRED"):
        dev.main(
            [
                "--capture",
                str(capture_path),
                "--review",
                str(old),
                "--output",
                str(tmp_path / "output"),
            ]
        )
    assert not (tmp_path / "output").exists()


def test_correct_execution_binding_and_result_identity():
    r = result()
    payload = dev.load_prereg("M2DEV-A1")["input"]
    context = dev.execution_context(payload, r, case_id="M2DEV-A1", observation_id="bound-1")
    c = dev.capture_result(r, case_id="M2DEV-A1", observation_id="bound-1", execution=context)
    assert (
        c.identity["submitted_input_sha256"]
        == c.identity["fixture_input_sha256"]
        == dev.input_hash(payload)
    )
    assert c.identity["result_case_id"] == r.case_id
    assert c.identity["result_trace_id"] == r.trace_id


def test_a2_actual_submitted_input_cannot_be_labelled_a1():
    with pytest.raises(ValueError, match="submitted/frozen input hash"):
        dev.execution_context(
            dev.load_prereg("M2DEV-A2")["input"],
            result("M2DEV-A2"),
            case_id="M2DEV-A1",
            observation_id="swapped",
        )


def test_missing_submitted_input_or_execution_fails_closed():
    with pytest.raises(ValueError, match="INPUT_IDENTITY_REQUIRED"):
        dev.execution_context(None, result(), case_id="M2DEV-A1", observation_id="missing")
    with pytest.raises(ValueError, match="INPUT_IDENTITY_REQUIRED"):
        dev.capture_result(result(), case_id="M2DEV-A1", observation_id="missing")
    with pytest.raises(ValueError, match="INPUT_IDENTITY_REQUIRED"):
        dev.assess_capture(replace(capture(), identity=None))


@pytest.mark.parametrize(
    "field,value",
    [
        ("submitted_input_sha256", "fake"),
        ("fixture_input_sha256", "fake"),
        ("observation_id", "other"),
        ("case_id", "M2DEV-A2"),
        ("result_case_id", "other-result"),
        ("result_trace_id", "other-trace"),
    ],
)
def test_claimed_execution_fields_are_recomputed_and_bound(field, value):
    r = result()
    context = dev.execution_context(
        dev.load_prereg("M2DEV-A1")["input"], r, case_id="M2DEV-A1", observation_id="bound-1"
    )
    with pytest.raises(ValueError, match="INPUT_IDENTITY_MISMATCH"):
        dev.capture_result(
            r,
            case_id="M2DEV-A1",
            observation_id="bound-1",
            execution=replace(context, **{field: value}),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("body", "Modified body"),
        ("subject", "Modified subject"),
        ("sender", "other@example.invalid"),
        ("received_at", "2026-12-29T20:15:00+07:00"),
        ("channel", "paste"),
        ("external_id", "transport-change"),
    ],
)
def test_changed_actual_payload_rejected(field, value):
    payload = dict(dev.load_prereg("M2DEV-A1")["input"])
    payload[field] = value
    with pytest.raises(ValueError, match="INPUT_IDENTITY_MISMATCH"):
        dev.execution_context(payload, result(), case_id="M2DEV-A1", observation_id="changed")


def test_canonical_input_order_unicode_timestamp_and_caseinput():
    import unicodedata
    from core.types import CaseInput

    original = dev.load_prereg("M2DEV-A1")["input"]
    reordered = {key: original[key] for key in reversed(original)}
    reordered["body"] = unicodedata.normalize("NFD", original["body"])
    reordered["received_at"] = (
        datetime.fromisoformat(original["received_at"])
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    typed = CaseInput(
        **{**original, "received_at": datetime.fromisoformat(original["received_at"])}
    )
    assert (
        dev.canonical_input(original)
        == dev.canonical_input(reordered)
        == dev.canonical_input(typed)
    )
    assert dev.input_hash(original) == dev.input_hash(reordered)
    c = bound_capture_result(result(), case_id="M2DEV-A1", observation_id="normalization")
    assert c.identity["fixture_input_sha256"] == dev.input_hash(typed)


def test_capture_mutation_after_review_creation_rejected():
    c = capture()
    review = reviewed(c)
    c.result["card"]["options"] = ["Changed", "Other"]
    with pytest.raises(ValueError, match="capture SHA-256"):
        dev.assess_capture(c, review=review)


def test_malformed_execution_context_fails_closed():
    c = capture()
    with pytest.raises(ValueError, match="malformed execution context"):
        dev.assess_capture(replace(c, identity={"case_id": "M2DEV-A1"}))
