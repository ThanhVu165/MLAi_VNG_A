"""Record only the three authorized BASE21 repair misses; reuse every existing cassette."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

from scripts import guarded_runtime_recording as recording
from scripts.audit_runtime_replay import ROOT, digest, source_fingerprints
from scripts.runtime_recording_readiness import (
    AttemptBudget,
    PROPOSED_CONFIG,
    prepare_readiness,
    usd,
)

LOGGER = logging.getLogger(__name__)
BASE_MANIFEST = ROOT / "reports/readiness/M6_T05_BASE21_RECORDED_PACK.json"
BASE_CASSETTES = ROOT / "tests/cassettes"
TARGETS = {
    "DEV_AUTHORITY": "33f1ec4b55430905cdac8c374a67001370e34fce11bcfca2033be18ad5c13882",
    "DEV_FACT": "436b6d239c2b25acc563ee85a6447002f8331cda4c1e9e9943faa68bbea6fdbf",
    "V03": "6a737acc3a5baf535f278ed20021f9fdc6bbfc12822ed0598dd040ffdc63793c",
}
FINAL_FLOW_CAPS = {
    "DEV_ROUTINE": 3,
    "DEV_AUTHORITY": 4,
    "DEV_FACT": 4,
    "V01": 3,
    "V02": 3,
    "V03": 4,
    "V04": 2,
    "DEV_HUMAN_R11": 1,
}
FINAL_GLOBAL_CAP = 25


def load_base_manifest(path: Path = BASE_MANIFEST) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (
        manifest.get("scope") != "BASE_PACK_V1"
        or manifest.get("actual_attempts") != 21
        or manifest.get("flow_attempts")
        != {
            name: count
            for name, count in FINAL_FLOW_CAPS.items()
            if name not in TARGETS
        }
        | {name: 3 for name in TARGETS}
        or usd(manifest.get("reserved_cost_upper_usd")) != Decimal("7.5285")
        or len(manifest.get("cassettes", [])) != 21
    ):
        raise recording.RecordingStop("BASE21_MANIFEST_MISMATCH")
    expected_files = set()
    for item in manifest["cassettes"]:
        path = ROOT / item["file"]
        expected_files.add(path.resolve())
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != item["file_sha256"]
            or path.stem != item["prompt_hash"]
        ):
            raise recording.RecordingStop("BASE21_CASSETTE_INTEGRITY_FAILURE")
    actual_files = {path.resolve() for path in BASE_CASSETTES.glob("*.json")}
    if actual_files != expected_files:
        raise recording.RecordingStop("BASE21_CASSETTE_SET_CHANGED")
    return manifest


def validate_delta_go(go: dict, sha: str, base: dict) -> tuple[AttemptBudget, Decimal]:
    if go.get("decision") != "GO" or go.get("scope") != "DELTA_REPAIR_V1":
        raise recording.RecordingStop("DELTA_COORDINATOR_GO_INCOMPLETE")
    if (
        go.get("source_sha") != sha
        or go.get("source_fingerprints") != source_fingerprints()
    ):
        raise recording.RecordingStop("SOURCE_OR_FINGERPRINT_NOT_APPROVED")
    if go.get("config") != PROPOSED_CONFIG or go.get("repair_prompt_hashes") != TARGETS:
        raise recording.RecordingStop("CONFIG_OR_EXACT_REPAIR_SCOPE_MISMATCH")
    if (
        go.get("prior_attempts") != 21
        or usd(go.get("prior_reserved_usd")) != usd(base["reserved_cost_upper_usd"])
        or go.get("cumulative_flow_caps") != FINAL_FLOW_CAPS
        or go.get("cumulative_global_cap") != FINAL_GLOBAL_CAP
        or go.get("new_attempt_cap") != len(TARGETS)
        or go.get("supplemental_cited_r11_recording_approved") is not False
    ):
        raise recording.RecordingStop("CUMULATIVE_ATTEMPT_SCOPE_MISMATCH")
    if (
        go.get("base_manifest_sha256")
        != hashlib.sha256(BASE_MANIFEST.read_bytes()).hexdigest()
    ):
        raise recording.RecordingStop("BASE21_MANIFEST_NOT_APPROVED")
    for field in (
        "go_reference",
        "account_evidence_reference",
        "bound_evidence_reference",
    ):
        if not isinstance(go.get(field), str) or not go[field].strip():
            raise recording.RecordingStop("MISSING_EXTERNAL_EVIDENCE_REFERENCE")
    if go.get("sdk_capture_format") != "SDK_JSON_PAYLOAD_NOT_HTTP_WIRE_BYTES":
        raise recording.RecordingStop("ORIGINAL_RESPONSE_CAPTURE_FORMAT_NOT_APPROVED")
    if go.get("allowed_response_models") != ["gpt-6-luna"]:
        raise recording.RecordingStop("EXACT_RESPONSE_MODEL_NOT_APPROVED")
    upper = recording.validate_cost_bound(go, len(TARGETS))
    prior_reserved = usd(go["prior_reserved_usd"])
    if prior_reserved + upper * len(TARGETS) > usd(go["approved_usd_cap"]):
        raise recording.RecordingStop("CUMULATIVE_WORST_CASE_NOT_FUNDED")
    budget = AttemptBudget(
        FINAL_GLOBAL_CAP, FINAL_FLOW_CAPS, usd(go["approved_usd_cap"])
    )
    budget.used = 21
    budget.reserved_usd = prior_reserved
    budget.flow_used = dict(base["flow_attempts"])
    return budget, upper


class DeltaObserver(recording.ProviderObserver):
    """Replay BASE21 locally and dispatch only the exact three approved misses."""

    def __init__(
        self, *args: object, base_cassettes: Path = BASE_CASSETTES, **kwargs: object
    ):
        super().__init__(*args, **kwargs)
        self.base_cassettes = base_cassettes
        self.reused_hashes: list[str] = []

    def mode(
        self,
        prompt: str,
        schema: dict,
        prompt_hash: str,
        model: str,
        timeout_s: int,
        retries: int,
        **kwargs: object,
    ) -> object:
        identity = ["openai", model, schema, prompt, 0.0]
        if digest(identity) != prompt_hash:
            raise recording.RecordingStop("PROMPT_IDENTITY_MISMATCH")
        cassette = self.base_cassettes / f"{prompt_hash}.json"
        if cassette.is_file():
            with patch.object(self.llm, "CASSETTE_DIRECTORY", self.base_cassettes):
                result = self.llm._replay(prompt_hash, model)
            if not result.ok:
                raise recording.RecordingStop("BASE21_REPLAY_FAILURE")
            self.reused_hashes.append(prompt_hash)
            self.calls.append(
                {
                    "flow": self.active_flow[0],
                    "step": kwargs["step"],
                    "case_ref": kwargs["case_id"],
                    "prompt_hash": prompt_hash,
                    "provider_ok": True,
                    "source": "BASE21_REPLAY",
                }
            )
            return result
        if (
            TARGETS.get(self.active_flow[0]) != prompt_hash
            or kwargs.get("step") != "R7_question_repair"
        ):
            raise recording.RecordingStop("UNAPPROVED_DELTA_PROVIDER_REQUEST")
        result = super().mode(
            prompt, schema, prompt_hash, model, timeout_s, retries, **kwargs
        )
        self.calls[-1]["source"] = "AUTHORIZED_DELTA_PROVIDER"
        return result


def run_delta_flows(
    observer: DeltaObserver, process_case: object, readiness: dict
) -> None:
    from core.types import CaseInput
    from verify import harness

    for flow in TARGETS:
        observer.active_flow[0] = flow
        if flow == "V03":
            case = next(
                item
                for item in harness.load_cases(ROOT / "verify/cases_verify4.json")
                if item.case_id == flow
            )
            result = process_case(case.input)
            matched = harness._matches(case, result)
        else:
            proposal = next(
                item for item in readiness["cases_proposal"] if item["flow"] == flow
            )
            input_data = dict(proposal["input"])
            input_data["received_at"] = datetime.fromisoformat(
                input_data["received_at"]
            )
            result = process_case(CaseInput(**input_data))
            expected = {
                "DEV_AUTHORITY": ("ESCALATE", "AUTHORITY_REQUIRED"),
                "DEV_FACT": ("ESCALATE", "FACT_UNRESOLVED"),
            }[flow]
            matched = (
                result.decision.decision,
                result.decision.escalation_type,
            ) == expected
        observer.outcomes.append(
            {"flow": flow, "result": asdict(result), "business_match": matched}
        )


def run_delta_recording(go: dict, output: Path, sha: str) -> None:
    base = load_base_manifest()
    budget, upper = validate_delta_go(go, sha, base)
    recording.assert_checkout(sha)
    if any(name in sys.modules for name in ("infra.db", "infra.settings")):
        raise recording.RecordingStop("FRESH_INTERPRETER_REQUIRED_BEFORE_RECORDING")
    if output.exists() or not output.resolve().is_relative_to(
        (ROOT / "data/validation").resolve()
    ):
        raise recording.RecordingStop("FRESH_LOCAL_VALIDATION_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    readiness = prepare_readiness()
    with tempfile.TemporaryDirectory(
        prefix="m6-t05-delta-"
    ) as directory, ExitStack() as hooks:
        hooks.enter_context(
            patch.dict(
                os.environ,
                dict(PROPOSED_CONFIG, DATABASE_PATH=str(Path(directory) / "app.db")),
            )
        )
        from core.pipeline import process_case
        from infra import llm

        active_flow = [""]
        observer = DeltaObserver(llm, go, output, active_flow, budget, upper)
        for name, callback in (
            ("_run_mode", observer.mode),
            ("_request_openai", observer.request),
            ("_response_usage", observer.usage),
            ("_record_cassette", observer.record),
            ("_load_cache", recording.no_cache),
        ):
            hooks.enter_context(patch.object(llm, name, callback))
        hooks.enter_context(
            patch.object(llm, "CASSETTE_DIRECTORY", output / "cassettes")
        )
        try:
            run_delta_flows(observer, process_case, readiness)
            if (
                set(observer.hash_counts) != set(TARGETS.values())
                or len(observer.attempts) != 3
            ):
                raise recording.RecordingStop(
                    "DELTA_DID_NOT_DISPATCH_EXACTLY_THREE_REPAIRS"
                )
        finally:
            recording.save_json(
                output / "DELTA_RECORDING_MANIFEST.json",
                {
                    "recorded_sha": sha,
                    "authorization": go,
                    "base_manifest_sha256": hashlib.sha256(
                        BASE_MANIFEST.read_bytes()
                    ).hexdigest(),
                    "base_cassettes_reused": len(observer.reused_hashes),
                    "new_attempts": observer.attempts,
                    "calls": observer.calls,
                    "outcomes": observer.outcomes,
                    "cumulative_reserved_attempts": budget.used,
                    "cumulative_reserved_usd": str(budget.reserved_usd),
                    "pack_status": "NOT_APPROVED",
                    "privacy_status": "REQUIRES_REVIEW_BEFORE_COMMIT",
                    "database": "isolated temporary DB",
                },
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/validation/m6-t05-delta-record")
    )
    options = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error("Run from repository root")
    try:
        go = json.loads(options.authorization.read_text(encoding="utf-8"))
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        run_delta_recording(go, options.output_dir, sha)
    except recording.RecordingStop as error:
        LOGGER.error("Delta recording stopped: %s", error)
        return 2
    except (ValueError, KeyError, TypeError, ArithmeticError, OSError) as error:
        LOGGER.error(
            "Invalid delta authorization/storage; stopped: %s", type(error).__name__
        )
        return 2
    LOGGER.warning(
        "Delta candidates remain NOT_APPROVED pending provenance/privacy validation"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
