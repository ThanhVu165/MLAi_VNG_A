"""M6-T05 guarded product recording. Never run without separately verified Coordinator GO."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch

from scripts.audit_runtime_replay import (
    ROOT,
    digest,
    observe_human_resume,
    observe_cited_resumes,
    observe_pipeline_cases,
    source_fingerprints,
)
from scripts.runtime_recording_readiness import (
    AttemptBudget,
    PROPOSED_CONFIG,
    authorization_blockers,
    prepare_readiness,
    usd,
    write_attempt_sidecar,
)

LOGGER = logging.getLogger(__name__)
PROVIDER_CONTEXT_MAX = 1_050_000  # Official gpt-6-luna model limits; reverify before GO.
PROVIDER_OUTPUT_MAX = 128_000
MAX_STANDARD_GLOBAL_INPUT_RATE = Decimal("0.25")  # Cache-write, long-context maximum.
MAX_STANDARD_GLOBAL_OUTPUT_RATE = Decimal("0.75")  # Long-context maximum.


class RecordingStop(BaseException):
    """Safety stops must escape product Exception handlers and transport retries."""


def save_json(path: Path, value: object) -> str:
    raw = (json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)
    return hashlib.sha256(raw).hexdigest()


def assert_checkout(sha: str) -> None:
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != sha:
        raise RecordingStop("HEAD_CHANGED")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise RecordingStop("TRACKED_OR_UNTRACKED_WORKTREE_CHANGES")


def recording_cases(readiness: dict, cited: bool = False) -> list[dict]:
    cases = list(readiness["cases_proposal"])
    if cited:
        for supplement in readiness["r11_supplemental_proposal"]:
            upstream = next(c for c in cases if c["flow"] == supplement["upstream_flow"])
            human = {key: supplement[key] for key in ("choice", "reason")}
            cases.append(
                {
                    "flow": upstream["flow"] + "_CITED_R11",
                    "input": upstream["input"],
                    "human_decision": human,
                    "attempt_cap": 1,
                    "input_sha256": digest({"input": upstream["input"], "human_decision": human}),
                }
            )
    return cases


def validate_go(go: dict, readiness: dict, sha: str) -> tuple[AttemptBudget, Decimal]:
    """Validate bindings, not the identity of an approver. Operator must verify GO source."""
    if authorization_blockers(go):
        raise RecordingStop("COORDINATOR_GO_INCOMPLETE")
    if go.get("source_sha") != sha or go.get("config") != PROPOSED_CONFIG:
        raise RecordingStop("SOURCE_OR_CONFIG_NOT_APPROVED")
    if go.get("sdk_capture_format") != "SDK_JSON_PAYLOAD_NOT_HTTP_WIRE_BYTES":
        raise RecordingStop("ORIGINAL_RESPONSE_CAPTURE_FORMAT_NOT_APPROVED")
    if go.get("scope", "BASE_PACK_V1") not in ("BASE_PACK_V1", "BASE_PLUS_CITED_R11_V1"):
        raise RecordingStop("UNKNOWN_PACK_SCOPE")
    cited = go.get("scope") == "BASE_PLUS_CITED_R11_V1"
    if cited and go.get("cited_r11_scope_approved") is not True:
        raise RecordingStop("CITED_R11_NOT_EXPLICITLY_APPROVED")
    cases = recording_cases(readiness, cited)
    inputs = {case["flow"]: case["input_sha256"] for case in cases}
    caps = {case["flow"]: case["attempt_cap"] for case in cases}
    if set(go.get("authorized_senders", [])) != {c["input"]["sender"] for c in cases}:
        raise RecordingStop("SYNTHETIC_SENDERS_NOT_PINNED")
    total_cap = sum(caps.values())
    if (
        go.get("input_hashes") != inputs
        or go.get("flow_caps") != caps
        or go.get("total_cap") != total_cap
    ):
        raise RecordingStop("EXACT_PACK_CAPS_OR_INPUTS_MISMATCH")
    if go.get("source_fingerprints") != source_fingerprints():
        raise RecordingStop("SOURCE_FINGERPRINT_MISMATCH")
    for field in ("go_reference", "account_evidence_reference", "bound_evidence_reference"):
        if not isinstance(go.get(field), str) or not go[field].strip():
            raise RecordingStop("MISSING_EXTERNAL_EVIDENCE_REFERENCE")
    upper = validate_cost_bound(go, total_cap)
    if (
        not isinstance(go.get("allowed_response_models"), list)
        or not go["allowed_response_models"]
        or any(not isinstance(model, str) or not model for model in go["allowed_response_models"])
    ):
        raise RecordingStop("EXACT_RESPONSE_MODELS_NOT_APPROVED")
    return AttemptBudget(total_cap, caps, usd(go["approved_usd_cap"])), upper


def validate_cost_bound(go: dict, total_cap: int) -> Decimal:
    bound = go.get("cost_bound", {})
    if bound.get("basis") != "VERIFIED_PROVIDER_ENFORCED_MAXIMA_AND_MAXIMUM_BILLED_RATES":
        raise RecordingStop("TOKEN_ASSUMPTION_IS_NOT_ENFORCEABLE_COST_BOUND")
    if bound.get("service_tier") != "standard" or bound.get("processing_region") != "global":
        raise RecordingStop("BOUND_REQUIRES_VERIFIED_STANDARD_GLOBAL_PROJECT")
    token_caps = [bound.get(key) for key in ("max_input_tokens", "max_output_tokens")]
    if any(type(n) is not int or n <= 0 for n in token_caps):
        raise RecordingStop("INVALID_PROVIDER_TOKEN_MAXIMA")
    if token_caps[0] < PROVIDER_CONTEXT_MAX or token_caps[1] < PROVIDER_OUTPUT_MAX:
        raise RecordingStop("BOUND_BELOW_UNCAPPED_PROVIDER_MAXIMUM")
    if (
        usd(bound["max_input_usd_per_million"]) < MAX_STANDARD_GLOBAL_INPUT_RATE
        or usd(bound["max_output_usd_per_million"]) < MAX_STANDARD_GLOBAL_OUTPUT_RATE
    ):
        raise RecordingStop("BOUND_BELOW_DOCUMENTED_MAXIMUM_BILLED_RATES")
    upper = sum(
        Decimal(n) * usd(bound[rate])
        for n, rate in zip(token_caps, ("max_input_usd_per_million", "max_output_usd_per_million"))
    ) / Decimal(1_000_000)
    if upper != usd(go["verified_upper_cost_usd"]):
        raise RecordingStop("UPPER_COST_CALCULATION_MISMATCH")
    if usd(go["approved_usd_cap"]) < upper * total_cap:
        raise RecordingStop("FULL_BASE_PACK_WORST_CASE_NOT_FUNDED")
    return upper


class ProviderObserver:
    """Single-thread product observer; SDK calls remain inside infra.llm unchanged."""

    def __init__(
        self,
        llm: ModuleType,
        go: dict,
        folder: Path,
        active_flow: list[str],
        budget: AttemptBudget,
        upper: Decimal,
    ) -> None:
        self.llm, self.go, self.folder, self.active_flow = llm, go, folder, active_flow
        self.budget, self.upper = budget, upper
        self.original_mode, self.original_request = llm._run_mode, llm._request_openai
        self.original_usage, self.original_record = llm._response_usage, llm._record_cassette
        self.context: dict = {}
        self.pending: dict | None = None
        self.hash_counts: dict[str, int] = {}
        self.attempts: list[dict] = []
        self.calls: list[dict] = []
        self.outcomes: list[dict] = []

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
            raise RecordingStop("PROMPT_IDENTITY_MISMATCH")
        self.context = {
            "flow": self.active_flow[0],
            "step": kwargs["step"],
            "case_ref": kwargs["case_id"],
            "prompt_hash": prompt_hash,
            "prompt": prompt,
            "schema": schema,
            "model": model,
            "schema_sha256": digest(schema),
            "provider_schema": self.llm._openai_schema(schema),
            "provider_schema_sha256": digest(self.llm._openai_schema(schema)),
        }
        result = self.original_mode(
            prompt, schema, prompt_hash, model, timeout_s, retries, **kwargs
        )
        self.calls.append(dict(self.context, provider_ok=result.ok, error=result.error))
        return result

    def request(
        self,
        prompt: str,
        schema: dict,
        prompt_hash: str,
        model: str,
        api_key: str,
        timeout_s: int,
        **kwargs: object,
    ) -> object:
        if self.pending is not None:
            raise RecordingStop("CONCURRENT_REQUEST_NOT_SUPPORTED")
        assert_checkout(self.go["source_sha"])
        if any(os.environ.get(key) != value for key, value in PROPOSED_CONFIG.items()):
            raise RecordingStop("EFFECTIVE_CONFIG_DRIFT")
        if source_fingerprints() != self.go["source_fingerprints"]:
            raise RecordingStop("SOURCE_DRIFT_BEFORE_ATTEMPT")
        try:
            self.budget.reserve(self.active_flow[0], self.upper)
        except (ValueError, ArithmeticError) as error:
            raise RecordingStop(str(error)) from error
        index = self.hash_counts.get(prompt_hash, 0) + 1
        self.hash_counts[prompt_hash] = index
        self.pending = dict(
            self.context,
            attempt_index=index,
            reserved_usd=str(self.upper),
            authorization=self.go["go_reference"],
            recorded_sha=self.go["source_sha"],
            source_fingerprints=self.go["source_fingerprints"],
            config=PROPOSED_CONFIG,
            started_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            effective_timeout_s=timeout_s,
            sdk_retries=0,
            input_hash=self.go["input_hashes"][self.active_flow[0]],
        )
        write_attempt_sidecar(self.folder, self.pending)
        outcome = {"prompt_hash": prompt_hash, "attempt_index": index, "status": "INTERRUPTED"}
        try:
            result = self.original_request(
                prompt, schema, prompt_hash, model, api_key, timeout_s, **kwargs
            )
            outcome["status"] = "RETURNED"
            return result
        except BaseException as error:
            outcome.update(status="FAILED", exception_class=type(error).__name__)
            status = getattr(error, "status_code", None)
            outcome["http_status"] = status if type(status) is int else None
            raise
        finally:
            outcome.update(
                sdk_response=self.pending.get("sdk_response"),
                sdk_response_sha256=self.pending.get("sdk_response_sha256"),
                request_id=self.pending.get("request_id"),
            )
            save_json(self.folder / f"{prompt_hash}.outcome-{index:03}.json", outcome)
            self.attempts.append(dict(self.pending, **outcome))
            self.pending = None

    def usage(self, response: object) -> object:
        """Save complete SDK payload before product parser; never replace returned data."""
        if self.pending is None:
            raise RecordingStop("RESPONSE_WITHOUT_RESERVED_ATTEMPT")
        name = f"{self.pending['prompt_hash']}.sdk-response-{self.pending['attempt_index']:03}.json"
        raw = response.model_dump_json().encode("utf-8")
        with (self.folder / name).open("xb") as handle:
            handle.write(raw)
        self.pending.update(
            sdk_response=name,
            sdk_response_sha256=hashlib.sha256(raw).hexdigest(),
            request_id=getattr(response, "_request_id", None),
            capture_format="SDK_JSON_PAYLOAD_NOT_HTTP_WIRE_BYTES",
        )
        usage = self.original_usage(response)
        bound = self.go["cost_bound"]
        if usage is None or not getattr(response, "id", None) or not self.pending["request_id"]:
            raise RecordingStop("RESPONSE_USAGE_OR_ORIGIN_METADATA_MISSING; original preserved")
        if getattr(response, "model", None) not in self.go["allowed_response_models"]:
            raise RecordingStop("RESPONSE_MODEL_NOT_APPROVED; original preserved")
        if usage.get("service_tier") != "default":
            raise RecordingStop("RESPONSE_NOT_STANDARD_TIER; original preserved")
        if (
            usage["input_tokens"] > bound["max_input_tokens"]
            or usage["output_tokens"] > bound["max_output_tokens"]
        ):
            raise RecordingStop("ACTUAL_USAGE_EXCEEDS_CERTIFIED_BOUND")
        self.pending["usage"] = usage
        return usage

    def record(self, result: object) -> None:
        path = self.llm.CASSETTE_DIRECTORY / f"{result.prompt_hash}.json"
        if path.exists():
            old = json.loads(path.read_text(encoding="utf-8"))
            if old != {"data": result.data, "model": result.model}:
                raise RecordingStop(
                    "SAME_HASH_DIFFERENT_RESPONSE; originals preserved, no overwrite"
                )
            return
        self.original_record(result)
        if not path.is_file():
            raise RecordingStop("CASSETTE_WRITE_FAILED")


def no_cache(*args: object, **kwargs: object) -> None:
    raise RecordingStop("CACHE_READ_FORBIDDEN_DURING_RECORD")


def run_product_flows(observer: ProviderObserver, process_case: object, db: ModuleType) -> None:
    """Preserve actual persisted failures before stopping recording; no outcome replacement."""
    from verify import harness

    def capture_case(*args: object, **kwargs: object) -> object:
        result = process_case(*args, **kwargs)
        observer.outcomes.append({"flow": observer.active_flow[0], "result": asdict(result)})
        if str(result.decision.decision) == "ERROR":
            raise RecordingStop("PRODUCT_TECHNICAL_ERROR; actual outcome preserved")
        flow = observer.active_flow[0]
        if flow.startswith("V"):
            case = next(
                c
                for c in harness.load_cases(ROOT / "verify/cases_verify4.json")
                if c.case_id == flow
            )
            matched = harness._matches(case, result)
        else:
            expected = {
                "DEV_ROUTINE": ("AUTO_REPLY", None),
                "DEV_AUTHORITY": ("ESCALATE", "AUTHORITY_REQUIRED"),
                "DEV_FACT": ("ESCALATE", "FACT_UNRESOLVED"),
            }[flow]
            matched = (result.decision.decision, result.decision.escalation_type) == expected
        observer.outcomes[-1]["business_match"] = matched
        if not matched:
            raise RecordingStop(
                "BUSINESS_MISMATCH; actual result preserved, no policy/response change"
            )
        return result

    with patch.object(harness, "process_case", capture_case):
        observer.outcomes.extend(observe_pipeline_cases(capture_case, observer.active_flow))
    observer.active_flow[0] = "DEV_HUMAN_R11"
    observer.outcomes.append(observe_human_resume(process_case, db))
    if observer.go.get("scope") == "BASE_PLUS_CITED_R11_V1":
        run_cited_resumes(observer, db)


def run_cited_resumes(observer: ProviderObserver, db: ModuleType) -> None:
    outcomes = observe_cited_resumes(observer.outcomes, observer.active_flow, db)
    observer.outcomes.extend(outcomes)
    for outcome, case in zip(outcomes, recording_cases(prepare_readiness(), True)[8:], strict=True):
        if (
            outcome.get("status") == "NOT_RUN"
            or outcome["human_decision"] != case["human_decision"]
            or outcome["final_case"]["status"] != "PENDING_APPROVAL"
        ):
            raise RecordingStop("CITED_R11_DECISION_OR_DRAFT_FAILURE")


def run_recording(go: dict, output: Path, readiness: dict, sha: str) -> None:
    budget, upper = validate_go(go, readiness, sha)
    assert_checkout(sha)
    if any(name in sys.modules for name in ("infra.db", "infra.settings")):
        raise RecordingStop("FRESH_INTERPRETER_REQUIRED_BEFORE_RECORDING")
    if output.exists() or not output.resolve().is_relative_to((ROOT / "data/validation").resolve()):
        raise RecordingStop("FRESH_LOCAL_VALIDATION_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="m6-t05-record-") as directory, ExitStack() as hooks:
        hooks.enter_context(
            patch.dict(
                os.environ, dict(PROPOSED_CONFIG, DATABASE_PATH=str(Path(directory) / "app.db"))
            )
        )
        from core.pipeline import process_case
        from infra import db, llm

        active_flow = [""]
        observer = ProviderObserver(llm, go, output, active_flow, budget, upper)
        for name, callback in (
            ("_run_mode", observer.mode),
            ("_request_openai", observer.request),
            ("_response_usage", observer.usage),
            ("_record_cassette", observer.record),
            ("_load_cache", no_cache),
        ):
            hooks.enter_context(patch.object(llm, name, callback))
        hooks.enter_context(patch.object(llm, "CASSETTE_DIRECTORY", output / "cassettes"))
        try:
            run_product_flows(observer, process_case, db)
        finally:
            save_json(
                output / "RECORDING_MANIFEST.json",
                {
                    "recorded_sha": sha,
                    "authorization": go,
                    "attempts": observer.attempts,
                    "calls": observer.calls,
                    "outcomes": observer.outcomes,
                    "reserved_attempts": budget.used,
                    "reserved_usd": str(budget.reserved_usd),
                    "pack_status": "NOT_APPROVED",
                    "privacy_status": "REQUIRES_REVIEW_BEFORE_COMMIT",
                    "database": "isolated temporary DB",
                },
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/validation/m6-t05-record-new")
    )
    options = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error("Run from repository root")
    if options.authorization is None:
        LOGGER.warning(
            "NOT_AUTHORIZED: missing separate, verified Coordinator GO; provider attempts=0"
        )
        return 2
    # A JSON statement is not authorization. The operator must verify its authoritative GO reference.
    try:
        go = json.loads(options.authorization.read_text(encoding="utf-8"))
        readiness = prepare_readiness()
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        run_recording(go, options.output_dir, readiness, sha)
    except RecordingStop as error:
        LOGGER.error("Recording stopped: %s", error)
        return 2
    except (ValueError, KeyError, TypeError, ArithmeticError, OSError) as error:
        LOGGER.error("Invalid authorization/storage; stopped: %s", type(error).__name__)
        return 2
    LOGGER.warning(
        "Recorded candidates remain NOT_APPROVED; validate provenance/privacy and guarded replay"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
