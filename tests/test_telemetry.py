from __future__ import annotations

from infra.audit import log_event
from infra.db import execute, now_iso
from infra.telemetry import snapshot


def _add_case(case_id: str, database_path: str) -> None:
    execute(
        "INSERT INTO cases (case_id, trace_id, channel, created_at, status, corpus_version) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, f"t-{case_id}", "verify", now_iso(), "RESOLVED", "cv-1"),
        database_path=database_path,
    )


def test_snapshot_matches_hand_counted_metrics(tmp_path) -> None:
    database_path = str(tmp_path / "telemetry.db")
    outcomes = [("AUTO_REPLY", None)] * 6 + [
        ("ESCALATE", "FACT_UNRESOLVED"),
        ("ESCALATE", "FACT_UNRESOLVED"),
        ("ESCALATE", "FACT_UNRESOLVED"),
        ("ESCALATE", "OUT_OF_POLICY"),
        ("ESCALATE", "OUT_OF_POLICY"),
        ("ESCALATE", "OUT_OF_POLICY"),
        ("ESCALATE", "AUTHORITY_REQUIRED"),
        ("ESCALATE", "AUTHORITY_REQUIRED"),
        ("ESCALATE", "AUTHORITY_REQUIRED"),
    ]
    for index, (decision, escalation_type) in enumerate(outcomes):
        case_id = f"c-{index}"
        _add_case(case_id, database_path)
        execute(
            "INSERT INTO decisions (decision_id, case_id, decision, escalation_type, rule_id, reason, "
            "corpus_version, is_override, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"d-{index}",
                case_id,
                decision,
                escalation_type,
                "P05",
                "Đếm telemetry.",
                "cv-1",
                int(index == 0),
                now_iso(),
            ),
            database_path=database_path,
        )

    for step, latency in (("R1", 10), ("R1", 20), ("R1", 30), ("R1", 40), ("R2", 5), ("R2", 15)):
        execute(
            "INSERT INTO step_latencies (case_id, step, ms, ok, ts) VALUES (?, ?, ?, ?, ?)",
            ("c-0", step, latency, 1, now_iso()),
            database_path=database_path,
        )

    for index, (choice, shown_at, decided_at) in enumerate(
        (
            ("APPROVE", "2026-01-01T00:00:00Z", "2026-01-01T00:00:03Z"),
            ("APPROVE", "2026-01-01T00:00:00Z", "2026-01-01T00:00:07Z"),
            ("REJECT", "2026-01-01T00:00:00Z", "2026-01-01T00:00:11Z"),
        )
    ):
        execute(
            "INSERT INTO human_decisions (id, case_id, actor, choice, reason, shown_at, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"h-{index}", "c-0", "HUMAN:test", choice, "Đã xem hồ sơ.", shown_at, decided_at),
            database_path=database_path,
        )

    for index in range(5):
        log_event(
            case_id="c-0",
            actor="SYSTEM",
            action="DRAFT_GENERATED",
            reason="Đã tạo nháp.",
            database_path=database_path,
        )
    log_event(
        case_id="c-0",
        actor="SYSTEM",
        action="GROUNDEDNESS_FAILED",
        reason="Không đủ căn cứ.",
        database_path=database_path,
    )

    metrics = snapshot(database_path=database_path)

    assert metrics["auto_rate"] == 0.4
    assert metrics["escalation_rate_by_type"] == {
        "FACT_UNRESOLVED": 0.2,
        "OUT_OF_POLICY": 0.2,
        "AUTHORITY_REQUIRED": 0.2,
    }
    assert metrics["p50_latency_ms"] == {"R1": 20, "R2": 5}
    assert metrics["p95_latency_ms"] == {"R1": 40, "R2": 15}
    assert metrics["median_review_seconds"] == 7.0
    assert metrics["pct_approved_under_5s"] == 0.5
    assert metrics["override_rate"] == 1 / 15
    assert metrics["groundedness_fail_rate"] == 0.2
    assert metrics["missed_escalation_rate"] is None
    assert metrics["over_escalation_rate"] is None
