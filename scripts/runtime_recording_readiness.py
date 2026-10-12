"""M6-T05 offline readiness and storage/budget checks. No provider execution path."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
import logging
from pathlib import Path
import re
import subprocess

from scripts.audit_runtime_replay import CONFIG, DEV_INPUTS, HUMAN_INPUT, ROOT, digest

LOGGER = logging.getLogger(__name__)
PRICING_SOURCE = "https://developers.openai.com/api/docs/models/gpt-6-luna"
MODEL_DOC_VERIFIED_ON = "2026-10-12"
INPUT_RATE = Decimal("0.125")  # Conservative standard short-context cache-write rate.
OUTPUT_RATE = Decimal("0.50")
MILLION = Decimal(1_000_000)
PROPOSED_CONFIG = dict(CONFIG, LLM_MODE="record")
OFFLINE_REFERENCE = "https://trello.com/c/7nEZN4bu#comment-6accb8f4b731380929f71f9a"
AUTHORIZATION_REQUIREMENTS = (
    "coordinator_go_reference",
    "source_sha_and_fingerprints",
    "exact_provider_model_config",
    "approved_case_input_hashes",
    "global_attempt_cap_including_retries",
    "per_flow_attempt_caps",
    "account_model_access_and_account_pricing_proof",
    "approved_usd_cap_and_pre_request_cost_bound",
    "synthetic_data_and_provenance_approval",
    "stop_conditions_and_failure_reporting",
)


def usd(value: str | Decimal) -> Decimal:
    amount = Decimal(value)
    if not amount.is_finite() or amount <= 0:
        raise ValueError("POSITIVE_FINITE_COST_REQUIRED")
    return amount


@dataclass
class AttemptBudget:
    """Pure offline reservation ledger; a ledger is never LIVE authorization."""

    total_cap: int
    flow_caps: dict[str, int]
    max_usd: Decimal
    used: int = 0
    reserved_usd: Decimal = Decimal(0)
    flow_used: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if type(self.total_cap) is not int or self.total_cap <= 0:
            raise ValueError("INVALID_ATTEMPT_CAP")
        if not self.flow_caps or any(type(n) is not int or n <= 0 for n in self.flow_caps.values()):
            raise ValueError("INVALID_FLOW_CAP")
        self.flow_caps = dict(self.flow_caps)
        self.max_usd = usd(self.max_usd)

    def reserve(self, flow: str, verified_upper_cost_usd: str | Decimal | None) -> None:
        """Reserve worst-case cost before dispatch; failures retain their full reservation."""
        if verified_upper_cost_usd is None:
            raise ValueError("PRE_REQUEST_COST_BOUND_UNVERIFIED")
        amount = usd(verified_upper_cost_usd)
        if flow not in self.flow_caps or self.flow_used.get(flow, 0) >= self.flow_caps[flow]:
            raise ValueError("FLOW_ATTEMPT_CAP_REACHED")
        if self.used >= self.total_cap:
            raise ValueError("GLOBAL_ATTEMPT_CAP_REACHED")
        if self.reserved_usd + amount > self.max_usd:
            raise ValueError("APPROVED_COST_CAP_WOULD_BE_EXCEEDED")
        self.used += 1
        self.flow_used[flow] = self.flow_used.get(flow, 0) + 1
        self.reserved_usd += amount


def write_attempt_sidecar(directory: Path, attempt: dict) -> str:
    """Append one original attempt without certifying provider origin or replacing old attempts."""
    prompt_hash, index = attempt.get("prompt_hash"), attempt.get("attempt_index")
    if not isinstance(prompt_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", prompt_hash):
        raise ValueError("INVALID_PROMPT_HASH")
    if type(index) is not int or index <= 0:
        raise ValueError("INVALID_ATTEMPT_INDEX")
    payload = dict(attempt, origin_verification="NOT_VERIFIED")
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / f"{prompt_hash}.attempt-{index:03}.json").open("xb") as handle:
        handle.write(raw)
    return hashlib.sha256(raw).hexdigest()


def proposed_cases() -> list[dict]:
    """Freeze public synthetic input, not an extraction, policy output or expected label."""
    cases = [
        {
            "flow": name,
            "input": {
                "sender": "synthetic@example.invalid",
                "subject": subject,
                "body": body,
                "received_at": "2026-09-21T09:00:00+07:00",
                "channel": "paste",
                "external_id": None,
            },
            "nominal_calls": 3,
            "attempt_cap": 3,
        }
        for name, subject, body in DEV_INPUTS
    ]
    for item in json.loads((ROOT / "verify/cases_verify4.json").read_text(encoding="utf-8")):
        cases.append(
            {
                "flow": item["id"],
                "input": dict(item["input"], channel="verify", external_id=item["id"]),
                "nominal_calls": 2 if item["id"] == "V04" else 3,
                "attempt_cap": 3,
            }
        )
    cases.append(
        {
            "flow": "DEV_HUMAN_R11",
            "input": {
                "subject": HUMAN_INPUT["subject"],
                "body": HUMAN_INPUT["body"],
                "sender": "synthetic@example.invalid",
                "received_at": "2026-09-21T09:04:00+07:00",
                "channel": "paste",
                "external_id": None,
            },
            "human_decision": {key: HUMAN_INPUT[key] for key in ("choice", "reason")},
            "nominal_calls": 1,
            "attempt_cap": 1,
        }
    )
    for case in cases:
        case.update(input_sha256=digest(case["input"]), is_synthetic=True)
    return cases


def recovery_inventory() -> dict:
    """Read only accessible/public metadata; no capture conversion or raw database reads."""
    history = subprocess.check_output(
        ["git", "log", "--all", "--format=%H", "--", "tests/cassettes"], text=True
    ).splitlines()
    artifacts = [
        {
            "file": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "classification": "NOT VERIFIED",
            "kind": "historical_result_summary_or_telemetry",
            "missing_reason": "M1 archive explicitly excludes raw prompt/provider responses",
        }
        for path in sorted((ROOT / "reports/evidence/m1").iterdir())
        if path.suffix in {".json", ".log"}
    ]
    handoff = ROOT / "reports/M2_OFFLINE_ARTIFACT_HANDOFF_20261012.md"
    return {
        "cassette_files": [
            str(p.relative_to(ROOT)) for p in (ROOT / "tests/cassettes").glob("*.json")
        ],
        "commits_touching_cassette_directory": history,
        "m1_candidates": artifacts,
        "m2_probes": m2_capture_inventory(handoff),
        "coordinator_clarification": "116 was offline tests PASS, not cassette inventory; 9 M2 captures attested",
        "handoff_file_available_here": handoff.exists(),
        "handoff_sha256": (
            hashlib.sha256(handoff.read_bytes()).hexdigest() if handoff.exists() else None
        ),
        "m2_conversion": "SEPARATE_TASK_AND_REVIEW_REQUIRED; not performed",
    }


def m2_capture_inventory(handoff: Path) -> list[dict]:
    """Published checksums are attestation; only available local bytes can be verified."""
    text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""
    rows = re.findall(r"\| `(m2_dev_live_probe_\d{2}) / ([^`]+)` \|.*?\| `([0-9a-f]{64})` \|", text)
    captures = []
    for probe, case, expected in rows:
        path = ROOT / f"data/validation/{probe}/cases/{case}/capture.json"
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        captures.append(
            {
                "probe": probe,
                "file": path.relative_to(ROOT).as_posix(),
                "available_here": path.is_file(),
                "published_sha256": expected,
                "actual_sha256": actual,
                "checksum_status": (
                    "NOT VERIFIED" if actual is None else ("PASS" if actual == expected else "FAIL")
                ),
                "classification": "NOT VERIFIED",
                "kind": "historical_output_and_telemetry; not replay cassette",
            }
        )
    return captures


def authorization_blockers(evidence: dict) -> list[str]:
    """Check required evidence statements; this function cannot authorize or execute a provider."""
    missing = [name for name in AUTHORIZATION_REQUIREMENTS if evidence.get(name) is not True]
    if evidence.get("decision") != "GO":
        missing.insert(0, "LIVE_NOT_AUTHORIZED")
    return missing


def record_plan(cases: list[dict]) -> dict:
    return {
        "record_config_proposal": PROPOSED_CONFIG,
        "cases_proposal": cases,
        "nominal_calls_proposal": sum(case["nominal_calls"] for case in cases),
        "provider_attempt_cap_proposal": sum(case["attempt_cap"] for case in cases),
        "budget_warning": "Six 3-step cases have no retry/repair headroom; quotas cannot transfer between flows",
        "r11_supplemental_proposal": [
            {
                "upstream_flow": name,
                "choice": "Quyết định khác",
                "reason": reason,
                "resume_attempt_cap": 1,
                "prompt_hash": None,
                "evidence_ids": None,
                "status": "REQUIRES_SEPARATE_COORDINATOR_APPROVAL",
            }
            for name, reason in (
                (
                    "DEV_AUTHORITY",
                    "Chuyển đề nghị phúc khảo trễ đến cấp có thẩm quyền; chưa chấp thuận ngoại lệ.",
                ),
                (
                    "DEV_FACT",
                    "Yêu cầu bổ sung khóa học và học kỳ trước khi xác định văn bản áp dụng.",
                ),
            )
        ],
    }


def pricing(cases: list[dict]) -> dict:
    nominal = sum(case["nominal_calls"] for case in cases)
    total_cap = sum(case["attempt_cap"] for case in cases)
    return {
        "source": PRICING_SOURCE,
        "verified_on": MODEL_DOC_VERIFIED_ON,
        "standard_input_usd_per_million": "0.10",
        "conservative_input_usd_per_million": str(INPUT_RATE),
        "output_usd_per_million": str(OUTPUT_RATE),
        "account_model_access": "NOT VERIFIED",
        "account_tier_and_billed_rates": "NOT VERIFIED",
        "proposed_usd_cap": None,
        "assumed_input_tokens_per_attempt": 8000,
        "assumed_output_tokens_per_attempt": 1000,
        "nominal_estimate_usd": str(
            Decimal(nominal) * (8000 * INPUT_RATE + 1000 * OUTPUT_RATE) / MILLION
        ),
        "cap_estimate_usd": str(
            Decimal(total_cap) * (8000 * INPUT_RATE + 1000 * OUTPUT_RATE) / MILLION
        ),
        "estimate_is_a_hard_cap": False,
    }


def prepare_readiness() -> dict:
    phase1 = json.loads(
        (ROOT / "reports/readiness/M6_T05_REPLAY_EVIDENCE.json").read_text(encoding="utf-8")
    )
    fingerprints = {
        name: value
        for name, value in phase1["source_sha256"].items()
        if not name.startswith("scripts/")
    }
    changed = [
        name
        for name, value in fingerprints.items()
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value
    ]
    if changed:
        raise ValueError("PRODUCTION_OR_CORPUS_DRIFT: " + ", ".join(changed))
    cases = proposed_cases()
    return {
        "schema_version": 1,
        "prepared_on_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "runtime_source_sha": phase1["tested_sha"],
        "runtime_source_fingerprints": fingerprints,
        "phase1_preserved": True,
        "offline_preparation_reference": OFFLINE_REFERENCE,
        "live_authorization": "NOT_AUTHORIZED",
        "authorization_blockers": authorization_blockers({}),
        **record_plan(cases),
        "pricing_public_documentation": pricing(cases),
        "execution_readiness": {
            "pre_attempt_ledger": "OFFLINE_UNIT_TESTED_ONLY",
            "provider_attempt_observer": "NOT INTEGRATED; existing telemetry is post-request",
            "output_token_bound": "NOT ENFORCED by current production adapter",
            "cost_guard": "BLOCKED until verified per-request upper cost and account tier are supplied",
            "sidecar_storage": "APPEND_ONLY; origin still requires original response/source/authorization review",
            "recording_runner": "NOT ENABLED; no provider execution code in readiness module",
        },
        "recovery": recovery_inventory(),
        "actual_provider_attempts": 0,
        "actual_tokens": 0,
        "actual_cost_usd": "0",
        "cassette_conversion_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/readiness/M6_T05_RECORDING_READINESS.json")
    )
    options = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error("Run from repository root")
    payload = prepare_readiness()
    options.output.parent.mkdir(parents=True, exist_ok=True)
    with options.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    LOGGER.warning("Offline readiness saved; recording NOT_AUTHORIZED; provider attempts=0")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
