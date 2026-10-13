"""Offline safeguards; unit metadata is not a provider response or cassette provenance."""

from decimal import Decimal
import json

import pytest

from scripts.runtime_recording_readiness import (
    AttemptBudget,
    authorization_blockers,
    prepare_readiness,
    m2_capture_inventory,
    write_attempt_sidecar,
)


def test_published_m2_checksums_do_not_certify_unavailable_capture_bytes(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("scripts.runtime_recording_readiness.ROOT", tmp_path)
    handoff = tmp_path / "handoff.md"
    handoff.write_text(
        "| `m2_dev_live_probe_01 / M2DEV-A1` | `observation` / `trace` | `" + "a" * 64 + "` |",
        encoding="utf-8",
    )
    row = m2_capture_inventory(handoff)[0]
    assert row["published_sha256"] == "a" * 64
    assert row["classification"] == "NOT VERIFIED"
    assert not row["available_here"]
    assert row["actual_sha256"] is None and row["checksum_status"] == "NOT VERIFIED"


def test_no_go_stops_before_authorizing_any_recording() -> None:
    missing = authorization_blockers({})
    assert missing[0] == "LIVE_NOT_AUTHORIZED" and len(missing) == 11
    assert "approved_usd_cap_and_pre_request_cost_bound" in missing


def test_per_flow_quota_cannot_borrow_another_flows_unused_attempts() -> None:
    budget = AttemptBudget(4, {"routine": 3, "human": 1}, Decimal("1.00"))
    for _ in range(3):
        budget.reserve("routine", "0.01")
    with pytest.raises(ValueError, match="FLOW_ATTEMPT_CAP"):
        budget.reserve("routine", "0.01")
    assert budget.used == 3 and budget.reserved_usd == Decimal("0.03")
    budget.reserve("human", "0.01")


def test_global_cap_rejects_before_mutating_ledger() -> None:
    budget = AttemptBudget(1, {"routine": 3}, Decimal("1"))
    budget.reserve("routine", "0.01")
    with pytest.raises(ValueError, match="GLOBAL_ATTEMPT_CAP"):
        budget.reserve("routine", "0.01")
    assert budget.used == 1 and budget.reserved_usd == Decimal("0.01")


@pytest.mark.parametrize("bound", [None, "NaN", "Infinity", "0", "-1", "0.051"])
def test_cost_guard_rejects_unknown_or_excessive_reservation_before_attempt(bound) -> None:
    budget = AttemptBudget(2, {"routine": 2}, Decimal("0.05"))
    with pytest.raises(ValueError):
        budget.reserve("routine", bound)
    assert budget.used == 0 and budget.flow_used == {} and budget.reserved_usd == 0


def test_same_hash_attempts_preserve_original_metadata_and_refuse_overwrite(tmp_path) -> None:
    original = {
        "prompt_hash": "a" * 64,
        "attempt_index": 1,
        "kind": "unit_metadata_fixture",
        "raw_response": None,
    }
    write_attempt_sidecar(tmp_path, original)
    first = next(tmp_path.glob("*.json"))
    first_bytes = first.read_bytes()
    write_attempt_sidecar(tmp_path, dict(original, attempt_index=2))
    with pytest.raises(FileExistsError):
        write_attempt_sidecar(tmp_path, original)
    assert first.read_bytes() == first_bytes and len(list(tmp_path.glob("*.json"))) == 2
    assert json.loads(first_bytes)["origin_verification"] == "NOT_VERIFIED"


def test_preparation_preserves_base_cap_and_requires_supplemental_cited_r11_approval() -> None:
    readiness = prepare_readiness()
    assert readiness["nominal_calls_proposal"] == 21
    assert readiness["provider_attempt_cap_proposal"] == 22
    assert readiness["live_authorization"] == "NOT_AUTHORIZED"
    assert readiness["actual_provider_attempts"] == readiness["cassette_conversion_count"] == 0
    assert Decimal(readiness["pricing_public_documentation"]["cap_estimate_usd"]) == Decimal(
        "0.033"
    )
    assert all(
        row["prompt_hash"] is None and row["status"] == "REQUIRES_SEPARATE_COORDINATOR_APPROVAL"
        for row in readiness["r11_supplemental_proposal"]
    )
