"""Tool safety/integrity checks; these never establish business replay success."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.audit_runtime_replay import MODEL, inventory


def test_inventory_rejects_malformed_and_incompatible_artifacts(tmp_path) -> None:
    schema = {
        "type": "object",
        "required": ["subject"],
        "properties": {"subject": {"type": "string"}},
    }
    (tmp_path / ("a" * 64 + ".json")).write_text("{broken", encoding="utf-8")
    (tmp_path / "wrong-key.json").write_text(
        json.dumps({"model": "different-model", "data": {"subject": 42}}), encoding="utf-8"
    )
    entries = inventory(tmp_path, {"draft": schema})
    assert not entries[0]["readable"]
    assert not entries[1]["filename_hash_valid"]
    assert not entries[1]["model_compatible"]
    assert not entries[1]["matching_schemas"]


def test_readable_response_is_not_provider_provenance(tmp_path) -> None:
    (tmp_path / ("b" * 64 + ".json")).write_text(
        json.dumps({"model": MODEL, "data": {"subject": "unit fixture"}}), encoding="utf-8"
    )
    entry = inventory(tmp_path, {"draft": {"type": "object"}})[0]
    assert entry["readable"] and entry["model_compatible"]
    assert entry["provenance_status"] == "MISSING"
    assert entry["prompt_identity_verified"] is False
    assert entry["recorded_sha"] is entry["authorization"] is None


@pytest.fixture(scope="module")
def missing_run(tmp_path_factory) -> tuple[dict, Path]:
    tmp_path = tmp_path_factory.mktemp("missing-replay")
    sentinel = tmp_path / "existing.db"
    sentinel.write_bytes(b"preserve-existing-database")
    environment = dict(os.environ, LLM_MODE="live", LLM_CACHE="1", DATABASE_PATH=str(sentinel))
    output = tmp_path / "evidence"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.audit_runtime_replay",
            "--output-dir",
            str(output),
            "--cassette-dir",
            str(tmp_path / "empty-cassettes"),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 2, result.stderr
    evidence = json.loads((output / "M6_T05_REPLAY_EVIDENCE.json").read_text(encoding="utf-8"))
    return evidence, sentinel


def test_audit_isolates_live_environment_and_existing_database(missing_run) -> None:
    evidence, sentinel = missing_run
    assert sentinel.read_bytes() == b"preserve-existing-database"
    assert evidence["config"]["LLM_MODE"] == "replay"
    assert evidence["live_provider_calls"] == 0
    assert {call["flow"] for call in evidence["calls"]} >= {
        "DEV_ROUTINE",
        "DEV_AUTHORITY",
        "DEV_FACT",
        "V01",
        "V02",
        "V03",
        "V04",
        "DEV_HUMAN_R11",
    }
    assert any(call["step"] == "R11_resume" for call in evidence["calls"])


def test_missing_pack_preserves_human_decision(missing_run) -> None:
    evidence, _ = missing_run
    assert len(evidence["calls"]) == 8
    assert all(not call["replay_ok"] for call in evidence["calls"])
    human = next(item for item in evidence["outcomes"] if item["flow"] == "DEV_HUMAN_R11")
    assert human["human_decision"]["choice"] == "Yêu cầu bản dịch"
    assert human["final_case"]["status"] == "HUMAN_DECIDED"
    assert human["job"]["state"] == "failed" and human["draft_count"] == 0


def test_audit_refuses_to_overwrite_historical_evidence(tmp_path) -> None:
    artifact = tmp_path / "M6_T05_REPLAY_EVIDENCE.json"
    artifact.write_bytes(b"immutable observation")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.audit_runtime_replay", "--output-dir", str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2 and "Evidence already exists" in result.stderr
    assert artifact.read_bytes() == b"immutable observation"


def test_cited_r11_does_not_invent_missing_upstream_context(tmp_path) -> None:
    output = tmp_path / "cited-evidence"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.audit_runtime_replay",
            "--output-dir",
            str(output),
            "--cassette-dir",
            str(tmp_path / "empty-pack"),
            "--include-cited-r11",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 2, result.stderr
    evidence = json.loads((output / "M6_T05_REPLAY_EVIDENCE.json").read_text(encoding="utf-8"))
    assert len(evidence["calls"]) == 8 and evidence["live_provider_calls"] == 0
    cited = [row for row in evidence["outcomes"] if row["flow"].endswith("_CITED_R11")]
    assert len(cited) == 2 and all(row["status"] == "NOT_RUN" for row in cited)
