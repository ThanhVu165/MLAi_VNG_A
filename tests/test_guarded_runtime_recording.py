"""Observer/authorization mechanics only. No provider responses or product acceptance fixtures."""

from decimal import Decimal
import hashlib
import json
import os
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from scripts.audit_runtime_replay import source_fingerprints
from scripts.guarded_runtime_recording import (
    ProviderObserver,
    RecordingStop,
    validate_go,
    recording_cases,
)
from scripts.runtime_recording_readiness import (
    AUTHORIZATION_REQUIREMENTS,
    AttemptBudget,
    PROPOSED_CONFIG,
    prepare_readiness,
)
from scripts.validate_recorded_replay_pack import (
    contained_file,
    validate_pack,
    parse_original_response,
    validate_attempt,
    privacy_flags,
    validate_inline_schema,
    pack_findings,
    validate_usage,
)


def go_metadata() -> tuple[dict, dict]:
    readiness = prepare_readiness()
    go = dict.fromkeys(AUTHORIZATION_REQUIREMENTS, True)
    go.update(
        decision="GO",
        source_sha="unit-sha-NOT-AUTHORIZATION",
        config=PROPOSED_CONFIG,
        sdk_capture_format="SDK_JSON_PAYLOAD_NOT_HTTP_WIRE_BYTES",
        input_hashes={c["flow"]: c["input_sha256"] for c in readiness["cases_proposal"]},
        flow_caps={c["flow"]: c["attempt_cap"] for c in readiness["cases_proposal"]},
        total_cap=22,
        authorized_senders=sorted({c["input"]["sender"] for c in readiness["cases_proposal"]}),
        source_fingerprints=source_fingerprints(),
        go_reference="unit://NOT_REAL_GO",
        account_evidence_reference="unit://not-account",
        bound_evidence_reference="unit://not-cost-proof",
        allowed_response_models=["gpt-6-luna"],
        cost_bound={
            "basis": "VERIFIED_PROVIDER_ENFORCED_MAXIMA_AND_MAXIMUM_BILLED_RATES",
            "service_tier": "standard",
            "processing_region": "global",
            "max_input_tokens": 1050000,
            "max_output_tokens": 128000,
            "max_input_usd_per_million": "0.25",
            "max_output_usd_per_million": "0.75",
        },
        verified_upper_cost_usd="0.3585",
        approved_usd_cap="10",
    )
    return go, readiness


def test_missing_go_cli_stops_without_product_import_or_provider(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.guarded_runtime_recording",
            "--output-dir",
            str(tmp_path / "unused"),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        env=dict(os.environ, LLM_MODE="live", LLM_CACHE="1"),
    )
    assert result.returncode == 2 and "NOT_AUTHORIZED" in result.stderr
    assert not (tmp_path / "unused").exists()


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ({"decision": "NO_GO"}, "GO_INCOMPLETE"),
        ({"source_sha": "wrong"}, "SOURCE_OR_CONFIG"),
        ({"total_cap": 24}, "PACK_CAPS"),
        ({"approved_usd_cap": "0.033"}, "NOT_FUNDED"),
        ({"verified_upper_cost_usd": "NaN"}, "POSITIVE_FINITE"),
    ],
)
def test_go_metadata_cannot_bypass_pins_caps_or_full_cost(mutation, reason) -> None:
    go, readiness = go_metadata()
    go.update(mutation)
    with pytest.raises((RecordingStop, ValueError), match=reason):
        validate_go(go, readiness, "unit-sha-NOT-AUTHORIZATION")


def test_assumed_thousand_output_tokens_is_not_a_provider_bound() -> None:
    go, readiness = go_metadata()
    go["cost_bound"]["max_output_tokens"] = 1000
    with pytest.raises(RecordingStop, match="UNCAPPED_PROVIDER_MAXIMUM"):
        validate_go(go, readiness, "unit-sha-NOT-AUTHORIZATION")


def test_documented_worst_case_calculation_is_not_account_authorization() -> None:
    go, readiness = go_metadata()
    budget, upper = validate_go(go, readiness, "unit-sha-NOT-AUTHORIZATION")
    assert upper == Decimal("0.3585") and budget.max_usd > upper * 22
    # This tests math/completeness only; unit:// references do not authorize a run.


@pytest.mark.parametrize(
    "field,value",
    [("service_tier", "fast"), ("processing_region", "regional")],
)
def test_cost_bound_requires_verified_standard_global_project(field, value) -> None:
    go, readiness = go_metadata()
    go["cost_bound"][field] = value
    with pytest.raises(RecordingStop, match="STANDARD_GLOBAL"):
        validate_go(go, readiness, "unit-sha-NOT-AUTHORIZATION")


def test_cited_r11_requires_explicit_scope_and_matching_24_attempt_budget() -> None:
    go, readiness = go_metadata()
    go["scope"] = "BASE_PLUS_CITED_R11_V1"
    with pytest.raises(RecordingStop, match="NOT_EXPLICITLY_APPROVED"):
        validate_go(go, readiness, "unit-sha-NOT-AUTHORIZATION")
    cases = recording_cases(readiness, True)
    go.update(
        cited_r11_scope_approved=True,
        total_cap=24,
        approved_usd_cap="18.9288",
        input_hashes={c["flow"]: c["input_sha256"] for c in cases},
        flow_caps={c["flow"]: c["attempt_cap"] for c in cases},
    )
    budget, _ = validate_go(go, readiness, "unit-sha-NOT-AUTHORIZATION")
    assert budget.total_cap == 24 and len(cases) == 10


def observer_fixture(tmp_path, monkeypatch) -> tuple[ProviderObserver, list[str]]:
    monkeypatch.setattr("scripts.guarded_runtime_recording.assert_checkout", lambda sha: None)
    go, _ = go_metadata()
    for key, value in PROPOSED_CONFIG.items():
        monkeypatch.setenv(key, value)
    delegated = []
    module = ModuleType("unit_mechanics_NO_PROVIDER")
    module._run_mode = module._response_usage = module._record_cassette = lambda *a, **k: None
    module.CASSETTE_DIRECTORY = tmp_path / "cassettes"

    def failure(*args, **kwargs):
        delegated.append("unit_function_called_NO_NETWORK")
        raise RuntimeError("unit_failure")

    module._request_openai = failure
    observer = ProviderObserver(
        module,
        go,
        tmp_path,
        ["DEV_ROUTINE"],
        AttemptBudget(1, {"DEV_ROUTINE": 1}, Decimal("1")),
        Decimal("0.1"),
    )
    observer.context = {"flow": "DEV_ROUTINE", "prompt_hash": "a" * 64}
    return observer, delegated


def test_failed_attempt_keeps_reservation_and_next_call_never_delegates(
    tmp_path, monkeypatch
) -> None:
    observer, delegated = observer_fixture(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="unit_failure"):
        observer.request("unit metadata", {}, "a" * 64, "gpt-6-luna", "UNIT_SECRET", 30)
    with pytest.raises(RecordingStop, match="CAP_REACHED"):
        observer.request("unit metadata", {}, "a" * 64, "gpt-6-luna", "UNIT_SECRET", 30)
    assert len(delegated) == observer.budget.used == 1
    assert observer.budget.reserved_usd == Decimal("0.1")
    assert all("UNIT_SECRET" not in file.read_text() for file in tmp_path.glob("*.json"))


def test_sdk_metadata_bytes_preserved_before_rejecting_missing_origin(
    tmp_path, monkeypatch
) -> None:
    observer, _ = observer_fixture(tmp_path, monkeypatch)
    observer.pending = {"prompt_hash": "b" * 64, "attempt_index": 1}
    raw = '{"kind":"unit_metadata_fixture_NO_LLM_RESPONSE"}'
    metadata = SimpleNamespace(model_dump_json=lambda: raw, _request_id=None)
    with pytest.raises(RecordingStop, match="METADATA_MISSING"):
        observer.usage(metadata)
    saved = next(tmp_path.glob("*.sdk-response-*.json")).read_bytes()
    assert (
        saved == raw.encode()
        and observer.pending["sdk_response_sha256"] == hashlib.sha256(saved).hexdigest()
    )


def test_nonstandard_response_tier_stops_after_preserving_original(tmp_path, monkeypatch) -> None:
    observer, _ = observer_fixture(tmp_path, monkeypatch)
    observer.pending = {"prompt_hash": "b" * 64, "attempt_index": 1}
    observer.original_usage = lambda response: {
        "input_tokens": 1,
        "output_tokens": 1,
        "service_tier": "priority",
    }
    response = SimpleNamespace(
        model_dump_json=lambda: '{"kind":"unit_nonstandard_tier"}',
        _request_id="unit-request",
        id="unit-response",
        model="gpt-6-luna",
    )
    with pytest.raises(RecordingStop, match="NOT_STANDARD_TIER"):
        observer.usage(response)
    assert next(tmp_path.glob("*.sdk-response-*.json")).is_file()


def test_same_hash_conflicting_unit_metadata_cannot_replace_file(tmp_path, monkeypatch) -> None:
    observer, _ = observer_fixture(tmp_path, monkeypatch)
    observer.llm.CASSETTE_DIRECTORY.mkdir()
    file = observer.llm.CASSETTE_DIRECTORY / ("c" * 64 + ".json")
    file.write_text(json.dumps({"data": {"unit_marker": 1}, "model": "unit"}))
    original = file.read_bytes()
    with pytest.raises(RecordingStop, match="DIFFERENT_RESPONSE"):
        observer.record(
            SimpleNamespace(prompt_hash="c" * 64, data={"unit_marker": 2}, model="unit")
        )
    assert file.read_bytes() == original


def test_empty_pack_and_outside_path_never_certify_provenance(tmp_path) -> None:
    (tmp_path / "RECORDING_MANIFEST.json").write_text(
        json.dumps({"recorded_sha": "unit", "authorization": {}, "attempts": []})
    )
    result = validate_pack(tmp_path)
    assert result["integrity_status"] == "FAIL" and result["pack_status"] == "NOT_APPROVED"
    with pytest.raises(ValueError, match="OUTSIDE_RECORDING"):
        contained_file(tmp_path, "../other.json")


def test_checksum_and_identity_tampering_rejected_without_a_provider_response(tmp_path) -> None:
    file = tmp_path / "unit_metadata.json"
    file.write_text('{"kind":"unit_metadata_NOT_PROVIDER_RESPONSE"}', encoding="utf-8")
    with pytest.raises(ValueError, match="CHECKSUM_MISMATCH"):
        parse_original_response(
            tmp_path, {"sdk_response": file.name, "sdk_response_sha256": "0" * 64}, {}
        )
    with pytest.raises(ValueError, match="IDENTITY_OR_SCHEMA"):
        validate_attempt(
            tmp_path,
            {"model": "unit", "schema": {}, "prompt": "unit metadata", "prompt_hash": "a" * 64},
            {},
        )


def test_effective_config_drift_stops_before_reservation_or_delegate(tmp_path, monkeypatch) -> None:
    observer, delegated = observer_fixture(tmp_path, monkeypatch)
    monkeypatch.setenv("LLM_CACHE", "1")
    with pytest.raises(RecordingStop, match="CONFIG_DRIFT"):
        observer.request("unit metadata", {}, "a" * 64, "gpt-6-luna", "UNIT_SECRET", 30)
    assert observer.budget.used == 0 and delegated == [] and not list(tmp_path.glob("*.json"))


def test_privacy_scanner_flags_values_without_publishing_or_rewriting_them() -> None:
    assert privacy_flags("synthetic@example.invalid", {"synthetic@example.invalid"}) == []
    assert "UNAPPROVED_EMAIL" in privacy_flags("unit@unapproved.invalid", set())
    assert "SECRET_PATTERN" in privacy_flags("sk-" + "a" * 30, set())
    assert "PHONE_OR_STUDENT_ID_PATTERN" in privacy_flags("MSSV: 12345678", set())


def test_schema_reference_cannot_make_offline_validator_fetch_network() -> None:
    validate_inline_schema({"type": "object"}, {})
    with pytest.raises(Exception, match="Unresolvable"):
        validate_inline_schema({"$ref": "https://unit.example.invalid/schema"}, {})


def test_pack_inventory_rejects_orphans_duplicates_and_source_drift(tmp_path) -> None:
    manifest = {
        "recorded_sha": "unit-sha",
        "authorization": {"source_sha": "unit-sha"},
        "attempts": [{"prompt_hash": "a" * 64, "attempt_index": 1}],
    }
    folder = tmp_path / "cassettes"
    folder.mkdir()
    (folder / ("a" * 64 + ".json")).write_text("unit inventory marker; NOT a response")
    assert pack_findings(tmp_path, manifest) == []
    manifest["attempts"].append({"prompt_hash": "a" * 64, "attempt_index": 2})
    assert pack_findings(tmp_path, manifest) == []  # A genuine retry may reuse the hash.
    manifest["attempts"].append(manifest["attempts"][0])
    manifest["recorded_sha"] = "different-unit-sha"
    (folder / "orphan.json").write_text("unit inventory marker")
    assert pack_findings(tmp_path, manifest) == [
        "DUPLICATE_ATTEMPT_IDENTITY",
        "MANIFEST_SOURCE_SHA_MISMATCH",
        "UNREFERENCED_CASSETTE_FILE",
    ]


def test_privacy_scan_covers_full_sdk_metadata_and_preserves_original(tmp_path) -> None:
    raw = b'{"unit_metadata_NOT_PROVIDER_RESPONSE":"unit@unapproved.invalid"}'
    file = tmp_path / "unit-metadata.json"
    file.write_bytes(raw)
    with pytest.raises(ValueError, match="PRIVACY_REVIEW_REQUIRED"):
        parse_original_response(
            tmp_path,
            {"sdk_response": file.name, "sdk_response_sha256": hashlib.sha256(raw).hexdigest()},
            {"authorized_senders": []},
        )
    assert file.read_bytes() == raw


@pytest.mark.parametrize("invalid", [True, -1, 1.0, "1"])
def test_token_usage_requires_nonnegative_integers(invalid) -> None:
    with pytest.raises(ValueError, match="INVALID_TOKEN_USAGE"):
        validate_usage(
            {"prompt_tokens": invalid, "completion_tokens": 0, "total_tokens": invalid},
            {"input_tokens": invalid, "output_tokens": 0},
        )


def test_token_usage_chain_must_reconcile() -> None:
    usage = {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5}
    validate_usage(usage, {"input_tokens": 2, "output_tokens": 3})
    with pytest.raises(ValueError, match="USAGE_CHAIN_MISMATCH"):
        validate_usage(usage, {"input_tokens": 3, "output_tokens": 2})
