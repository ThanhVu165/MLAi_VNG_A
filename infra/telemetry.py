"""Tính các chỉ số vận hành trực tiếp từ SQLite."""

from __future__ import annotations

from datetime import datetime
from math import ceil
from pathlib import Path

from infra.db import fetch_all

ESCALATION_TYPES = ("FACT_UNRESOLVED", "OUT_OF_POLICY", "AUTHORITY_REQUIRED")
APPROVED_CHOICES = frozenset({"APPROVE", "APPROVE_SEND", "APPROVED", "CHẤP THUẬN"})


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _percentile(values: list[int], percentile: float) -> int:
    ordered = sorted(values)
    return ordered[ceil(len(ordered) * percentile) - 1] if ordered else 0


def _review_seconds(shown_at: str, decided_at: str) -> float:
    shown = datetime.fromisoformat(shown_at.replace("Z", "+00:00"))
    decided = datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
    return (decided - shown).total_seconds()


def _reviews(database_path: str | Path | None) -> list[tuple[str, float]]:
    rows = fetch_all(
        "SELECT choice, shown_at, decided_at FROM human_decisions "
        "WHERE shown_at IS NOT NULL AND decided_at IS NOT NULL",
        database_path=database_path,
    )
    return [(row["choice"], _review_seconds(row["shown_at"], row["decided_at"])) for row in rows]


def snapshot(*, database_path: str | Path | None = None) -> dict[str, object]:
    """Trả về tám nhóm chỉ số; không ghi dữ liệu telemetry vào cơ sở dữ liệu."""
    decision_rows = fetch_all(
        "SELECT decision, escalation_type, is_override FROM decisions",
        database_path=database_path,
    )
    classified = [row for row in decision_rows if row["decision"] in {"AUTO_REPLY", "ESCALATE"}]
    escalations = [row for row in classified if row["decision"] == "ESCALATE"]
    escalation_rate_by_type = {
        kind: _ratio(sum(row["escalation_type"] == kind for row in escalations), len(classified))
        for kind in ESCALATION_TYPES
    }

    latencies: dict[str, list[int]] = {}
    for row in fetch_all("SELECT step, ms FROM step_latencies", database_path=database_path):
        latencies.setdefault(row["step"], []).append(row["ms"])

    reviews = _reviews(database_path)
    review_durations = sorted(seconds for _, seconds in reviews)
    approved_reviews = [
        seconds for choice, seconds in reviews if choice.strip().upper() in APPROVED_CHOICES
    ]
    event_counts = {
        row["action"]: row["total"]
        for row in fetch_all(
            "SELECT action, COUNT(*) AS total FROM audit_events "
            "WHERE action IN ('DRAFT_GENERATED', 'GROUNDEDNESS_FAILED') GROUP BY action",
            database_path=database_path,
        )
    }

    return {
        "auto_rate": _ratio(
            sum(row["decision"] == "AUTO_REPLY" for row in classified), len(classified)
        ),
        "escalation_rate_by_type": escalation_rate_by_type,
        "p50_latency_ms": {step: _percentile(values, 0.5) for step, values in latencies.items()},
        "p95_latency_ms": {step: _percentile(values, 0.95) for step, values in latencies.items()},
        "median_review_seconds": (
            review_durations[len(review_durations) // 2]
            if len(review_durations) % 2
            else (
                (
                    review_durations[len(review_durations) // 2 - 1]
                    + review_durations[len(review_durations) // 2]
                )
                / 2
                if review_durations
                else 0.0
            )
        ),
        "pct_approved_under_5s": _ratio(
            sum(seconds < 5 for seconds in approved_reviews), len(approved_reviews)
        ),
        "override_rate": _ratio(
            sum(row["is_override"] for row in decision_rows), len(decision_rows)
        ),
        "groundedness_fail_rate": _ratio(
            event_counts.get("GROUNDEDNESS_FAILED", 0), event_counts.get("DRAFT_GENERATED", 0)
        ),
        "missed_escalation_rate": None,
        "over_escalation_rate": None,
    }
