from datetime import date, datetime, timezone

from core.types import (
    CaseInput,
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
    Extraction,
    PipelineResult,
    PolicyDecision,
    RequestItem,
    SourceStatus,
)


def test_contract_enums_have_specified_members() -> None:
    assert len(Decision) == 4
    assert len(EscalationType) == 3
    assert len(EvidenceStatus) == 7
    assert len(CaseStatus) == 12
    assert len(Domain) == 4
    assert len(SourceStatus) == 4
    assert len(ChunkLabel) == 2


def test_contract_dataclasses_accept_sample_data() -> None:
    now = datetime(2026, 9, 19, tzinfo=timezone.utc)
    request = RequestItem(Domain.CONDUCT_SCORE, "score_scale", True, False, False, False, False)
    extraction = Extraction("vi", [request], {}, [], False, "{}")
    chunk = EvidenceChunk(
        "chunk-1",
        "doc-1",
        "QĐ 3150/2026 · Điều 8 · Khoản 2",
        "Điều 8 quy định thang điểm.",
        Domain.CONDUCT_SCORE,
        ChunkLabel.AUTO_ANSWERABLE,
        0.9,
        date(2026, 1, 1),
        None,
        [],
        [],
        False,
        False,
    )
    evidence = EvidenceResult(EvidenceStatus.OK, [chunk], [])
    decision = PolicyDecision(
        Decision.AUTO_REPLY, None, "P05", "Câu hỏi thường quy.", ["chunk-1"], "cv_1"
    )
    draft = DraftReply("Trả lời", "Theo Điều 8.", ["chunk-1"], True, [])
    card = EscalationCard(
        "Tóm tắt",
        ["Sự kiện"],
        [(chunk.breadcrumb, chunk.text)],
        "Có duyệt không?",
        ["Có", "Không"],
        EscalationType.FACT_UNRESOLVED,
        None,
    )
    result = PipelineResult(
        "case-1",
        "trace-1",
        CaseStatus.PENDING_SEND,
        decision,
        extraction,
        evidence,
        draft,
        card,
        "cv_1",
        {},
        now,
        now,
    )
    inp = CaseInput("student@example.edu", "Hỏi", "Nội dung", now, "paste")

    assert inp.sender == "student@example.edu"
    assert result.decision is decision
