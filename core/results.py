"""Ảnh chụp kết quả giữ nguyên căn cứ tại thời điểm xử lý, độc lập phiên giao diện."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any

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
    Extraction,
    PipelineResult,
    PolicyDecision,
    RequestItem,
)
from infra.db import execute, fetch_one


def save_result(result: PipelineResult) -> None:
    """Lưu bản gốc kết quả trước khi giao diện hoặc tiến trình gửi thay đổi trạng thái."""
    execute(
        "INSERT OR REPLACE INTO case_results(case_id, payload_json) VALUES (?, ?)",
        (
            result.case_id,
            json.dumps(asdict(result), ensure_ascii=False, default=lambda value: value.isoformat()),
        ),
    )


def _decode(data: dict[str, Any]) -> PipelineResult:
    decision = data["decision"]
    decision["decision"] = Decision(decision["decision"])
    decision["escalation_type"] = (
        EscalationType(decision["escalation_type"]) if decision["escalation_type"] else None
    )
    extraction = data["extraction"]
    if extraction:
        extraction["requests"] = [
            RequestItem(**{**item, "domain": Domain(item["domain"])})
            for item in extraction["requests"]
        ]
    evidence = data["evidence"]
    if evidence:
        evidence["status"] = EvidenceStatus(evidence["status"])
        evidence["chunks"] = [
            EvidenceChunk(
                **{
                    **chunk,
                    "domain": Domain(chunk["domain"]),
                    "label": ChunkLabel(chunk["label"]),
                    "effective_from": date.fromisoformat(chunk["effective_from"]),
                    "effective_to": (
                        date.fromisoformat(chunk["effective_to"]) if chunk["effective_to"] else None
                    ),
                }
            )
            for chunk in evidence["chunks"]
        ]
    card = data["card"]
    if card:
        card["escalation_type"] = EscalationType(card["escalation_type"])
        card["basis"] = [tuple(item) for item in card["basis"]]
        card["partial_draft"] = (
            DraftReply(**card["partial_draft"]) if card["partial_draft"] else None
        )
    return PipelineResult(
        data["case_id"],
        data["trace_id"],
        CaseStatus(data["status"]),
        PolicyDecision(**decision),
        Extraction(**extraction) if extraction else None,
        EvidenceResult(**evidence) if evidence else None,
        DraftReply(**data["draft"]) if data["draft"] else None,
        EscalationCard(**card) if card else None,
        data["corpus_version"],
        data["step_latencies_ms"],
        datetime.fromisoformat(data["started_at"]),
        datetime.fromisoformat(data["finished_at"]),
    )


def load_result(case_id: str) -> PipelineResult | None:
    """Khôi phục kết quả, lấy trạng thái/quyết định/bản nháp mới nhất sau thao tác của người."""
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if case is None or case["status"] in (CaseStatus.RECEIVED, CaseStatus.PROCESSING):
        return None
    snapshot = fetch_one("SELECT payload_json FROM case_results WHERE case_id = ?", (case_id,))
    latest = fetch_one(
        "SELECT * FROM decisions WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
    )
    result = (
        _decode(json.loads(snapshot["payload_json"]))
        if snapshot
        else PipelineResult(
            case_id,
            case["trace_id"],
            CaseStatus(case["status"]),
            PolicyDecision(
                Decision.ERROR,
                None,
                "TECHNICAL_ERROR",
                "Lần xử lý bị gián đoạn. Hãy chạy lại email.",
                [],
                case["corpus_version"],
            ),
            None,
            None,
            None,
            None,
            case["corpus_version"],
            {},
            datetime.fromisoformat(case["created_at"]),
            datetime.now(timezone.utc),
        )
    )
    result.status = CaseStatus(case["status"])
    if latest:
        result.decision = PolicyDecision(
            Decision(latest["decision"]),
            EscalationType(latest["escalation_type"]) if latest["escalation_type"] else None,
            latest["rule_id"],
            latest["reason"],
            json.loads(latest["evidence_ids_json"] or "[]"),
            latest["corpus_version"],
        )
    draft = fetch_one(
        "SELECT * FROM drafts WHERE case_id = ? ORDER BY rowid DESC LIMIT 1", (case_id,)
    )
    if draft:
        result.draft = DraftReply(
            draft["subject"],
            draft["body"],
            json.loads(draft["citations_json"] or "[]"),
            bool(draft["grounded"]),
            json.loads(draft["guard_failures_json"] or "[]"),
        )
    card = fetch_one("SELECT * FROM escalations WHERE case_id = ?", (case_id,))
    if card:
        partial = result.card.partial_draft if result.card else None
        if draft and draft["kind"] == "partial":
            partial = result.draft
        result.card = EscalationCard(
            card["summary"],
            json.loads(card["facts_json"] or "[]"),
            [tuple(item) for item in json.loads(card["basis_json"] or "[]")],
            card["question"],
            json.loads(card["options_json"] or "[]"),
            EscalationType(card["escalation_type"]),
            partial,
        )
    if result.status is CaseStatus.ERROR:
        result.card = None
        if result.decision.decision is not Decision.ERROR:
            result.decision = PolicyDecision(
                Decision.ERROR,
                None,
                "TECHNICAL_ERROR",
                "Lần xử lý bị gián đoạn. Hãy kiểm tra kết nối và chạy lại email.",
                [],
                result.corpus_version,
            )
    return result
