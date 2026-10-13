"""Offline checks for the exact three-call M6-T05 delta guard."""

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import guarded_runtime_recording as recording
from scripts.audit_runtime_replay import digest
from scripts.guarded_runtime_delta_recording import (
    DeltaObserver,
    FINAL_FLOW_CAPS,
    TARGETS,
    validate_delta_go,
)
from scripts.runtime_recording_readiness import AttemptBudget


@dataclass
class Result:
    ok: bool
    error: str | None = None


def observer(tmp_path: Path, flow: str) -> tuple[DeltaObserver, SimpleNamespace]:
    module = SimpleNamespace()
    module.CASSETTE_DIRECTORY = tmp_path / "new"
    module._openai_schema = lambda schema: schema
    module._replay = lambda prompt_hash, model: Result(True)
    module._run_mode = lambda *args, **kwargs: Result(True)
    module._request_openai = lambda *args, **kwargs: Result(True)
    module._response_usage = lambda response: None
    module._record_cassette = lambda result: None
    budget = AttemptBudget(25, {name: 4 for name in TARGETS}, Decimal("10"))
    item = DeltaObserver(
        module,
        {"source_sha": "sha", "source_fingerprints": {}, "input_hashes": {}},
        tmp_path,
        [flow],
        budget,
        Decimal("0.3585"),
        base_cassettes=tmp_path / "base",
    )
    return item, module


def test_delta_reuses_existing_cassette_without_provider(tmp_path, monkeypatch):
    item, module = observer(tmp_path, "DEV_AUTHORITY")
    prompt, schema, prompt_hash = "existing", {"type": "object"}, ""
    prompt_hash = digest(["openai", "gpt-6-luna", schema, prompt, 0.0])
    (tmp_path / "base").mkdir()
    (tmp_path / "base" / f"{prompt_hash}.json").write_text(json.dumps({"data": {}}))
    monkeypatch.setattr(
        module, "_run_mode", lambda *a, **k: pytest.fail("provider path")
    )

    result = item.mode(
        prompt,
        schema,
        prompt_hash,
        "gpt-6-luna",
        30,
        1,
        step="R2_extract",
        case_id="case",
    )

    assert result.ok and item.reused_hashes == [prompt_hash]
    assert item.calls[0]["source"] == "BASE21_REPLAY"


def test_delta_rejects_every_missing_hash_except_exact_repair(tmp_path):
    item, _ = observer(tmp_path, "DEV_AUTHORITY")
    prompt, schema = "unapproved", {"type": "object"}
    prompt_hash = digest(["openai", "gpt-6-luna", schema, prompt, 0.0])
    with pytest.raises(
        recording.RecordingStop, match="UNAPPROVED_DELTA_PROVIDER_REQUEST"
    ):
        item.mode(
            prompt,
            schema,
            prompt_hash,
            "gpt-6-luna",
            30,
            1,
            step="R7_question_repair",
            case_id="case",
        )


def test_delta_go_carries_prior_reservation_and_caps_cumulative_cost(
    tmp_path, monkeypatch
):
    from scripts import guarded_runtime_delta_recording as delta

    manifest = tmp_path / "base.json"
    manifest.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(delta, "BASE_MANIFEST", manifest)
    monkeypatch.setattr(delta, "source_fingerprints", lambda: {"source": "hash"})
    base = {
        "reserved_cost_upper_usd": "7.5285",
        "flow_attempts": {
            name: cap - (1 if name in TARGETS else 0)
            for name, cap in FINAL_FLOW_CAPS.items()
        },
    }
    go = {
        "decision": "GO",
        "scope": "DELTA_REPAIR_V1",
        "source_sha": "implementation-sha",
        "source_fingerprints": {"source": "hash"},
        "config": delta.PROPOSED_CONFIG,
        "repair_prompt_hashes": TARGETS,
        "prior_attempts": 21,
        "prior_reserved_usd": "7.5285",
        "cumulative_flow_caps": FINAL_FLOW_CAPS,
        "cumulative_global_cap": 25,
        "new_attempt_cap": 3,
        "supplemental_cited_r11_recording_approved": False,
        "base_manifest_sha256": hashlib.sha256(b"{}").hexdigest(),
        "go_reference": "Coordinator exact-SHA GO",
        "account_evidence_reference": "verified project evidence",
        "bound_evidence_reference": "verified model/pricing evidence",
        "sdk_capture_format": "SDK_JSON_PAYLOAD_NOT_HTTP_WIRE_BYTES",
        "allowed_response_models": ["gpt-6-luna"],
        "cost_bound": {
            "basis": "VERIFIED_PROVIDER_ENFORCED_MAXIMA_AND_MAXIMUM_BILLED_RATES",
            "service_tier": "standard",
            "processing_region": "global",
            "max_input_tokens": 1_050_000,
            "max_output_tokens": 128_000,
            "max_input_usd_per_million": "0.25",
            "max_output_usd_per_million": "0.75",
        },
        "verified_upper_cost_usd": "0.3585",
        "approved_usd_cap": "10.00",
    }

    budget, upper = validate_delta_go(go, "implementation-sha", base)

    assert upper == Decimal("0.3585")
    assert budget.used == 21 and budget.reserved_usd == Decimal("7.5285")
    assert budget.flow_used == base["flow_attempts"]
    go["approved_usd_cap"] = "8.00"
    with pytest.raises(
        recording.RecordingStop, match="CUMULATIVE_WORST_CASE_NOT_FUNDED"
    ):
        validate_delta_go(go, "implementation-sha", base)
