"""Offline integrity/chain checks for genuine recorded candidates; no origin sign-off or LIVE."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry

from scripts.audit_runtime_replay import digest, source_fingerprints
from scripts.guarded_runtime_recording import save_json

LOGGER = logging.getLogger(__name__)


def deny_schema_resource(uri: str) -> None:
    raise ValueError("OFFLINE_SCHEMA_RESOURCE_RETRIEVAL_FORBIDDEN")


def validate_inline_schema(schema: dict, data: object) -> None:
    Draft202012Validator(schema, registry=Registry(retrieve=deny_schema_resource)).validate(data)


def privacy_flags(content: str, allowed_emails: set[str]) -> list[str]:
    flags = []
    if re.search(r"sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9_-]{20,}|BEGIN .*PRIVATE KEY", content):
        flags.append("SECRET_PATTERN")
    emails = set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", content))
    if emails - allowed_emails:
        flags.append("UNAPPROVED_EMAIL")
    if re.search(
        r"\b(?:0\d{9}|84\d{9})\b|(?:MSSV|mã số sinh viên)\s*[:：]?\s*\d{6,}", content, re.I
    ):
        flags.append("PHONE_OR_STUDENT_ID_PATTERN")
    return flags


def contained_file(folder: Path, name: str) -> Path:
    path = (folder / name).resolve()
    if not path.is_relative_to(folder.resolve()):
        raise ValueError("PROVENANCE_PATH_OUTSIDE_RECORDING_DIRECTORY")
    return path


def validate_attempt(folder: Path, attempt: dict, authorization: dict) -> dict:
    """Validate source bytes and bindings; do not infer provider origin from a readable JSON."""
    prompt_hash = digest(["openai", attempt["model"], attempt["schema"], attempt["prompt"], 0.0])
    if (
        prompt_hash != attempt["prompt_hash"]
        or digest(attempt["schema"]) != attempt["schema_sha256"]
    ):
        raise ValueError("IDENTITY_OR_SCHEMA_DIGEST_MISMATCH")
    if digest(attempt["provider_schema"]) != attempt["provider_schema_sha256"]:
        raise ValueError("STRICT_SCHEMA_DIGEST_MISMATCH")
    if (
        attempt["model"] != authorization["config"]["OPENAI_MODEL"]
        or attempt["status"] != "RETURNED"
    ):
        raise ValueError("ATTEMPT_NOT_RETURNED_OR_MODEL_MISMATCH")
    if attempt["authorization"] != authorization["go_reference"]:
        raise ValueError("AUTHORIZATION_REFERENCE_MISMATCH")
    if (
        attempt["recorded_sha"] != authorization["source_sha"]
        or attempt["source_fingerprints"] != authorization["source_fingerprints"]
        or attempt["config"] != authorization["config"]
        or attempt["input_hash"] != authorization["input_hashes"][attempt["flow"]]
    ):
        raise ValueError("SOURCE_CONFIG_INPUT_BINDING_MISMATCH")
    if not attempt.get("sdk_response") or not attempt.get("request_id"):
        raise ValueError("ORIGINAL_RESPONSE_OR_REQUEST_ID_MISSING")
    data = parse_original_response(folder, attempt, authorization)
    cassette = contained_file(folder, f"cassettes/{prompt_hash}.json")
    cassette_raw = cassette.read_bytes()
    if json.loads(cassette_raw) != {"data": data, "model": attempt["model"]}:
        raise ValueError("CASSETTE_DIFFERS_FROM_ORIGINAL_PARSED_RESPONSE")
    return {
        "flow": attempt["flow"],
        "step": attempt["step"],
        "prompt_hash": prompt_hash,
        "cassette_sha256": hashlib.sha256(cassette_raw).hexdigest(),
        "integrity_status": "PASS",
        "provider_origin": "CHAIN_PRESENT_REQUIRES_INDEPENDENT_REVIEW",
    }


def parse_original_response(folder: Path, attempt: dict, authorization: dict) -> dict:
    raw = contained_file(folder, attempt["sdk_response"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != attempt["sdk_response_sha256"]:
        raise ValueError("ORIGINAL_RESPONSE_CHECKSUM_MISMATCH")
    response = json.loads(raw)
    if privacy_flags(
        json.dumps(response, ensure_ascii=False), set(authorization["authorized_senders"])
    ):
        raise ValueError("PRIVACY_REVIEW_REQUIRED; original response quarantined, not edited")
    if (
        not response.get("id")
        or response.get("model") not in authorization["allowed_response_models"]
    ):
        raise ValueError("RESPONSE_ID_OR_MODEL_NOT_APPROVED")
    choice = response["choices"][0]
    if choice["finish_reason"] != "stop" or choice["message"].get("refusal"):
        raise ValueError("REFUSED_OR_INCOMPLETE_RESPONSE")
    data = json.loads(choice["message"]["content"])
    validate_inline_schema(attempt["schema"], data)
    validate_inline_schema(attempt["provider_schema"], data)
    usage = response["usage"]
    validate_usage(usage, attempt["usage"])
    return data


def validate_usage(usage: dict, recorded_usage: dict) -> None:
    counts = [usage[key] for key in ("prompt_tokens", "completion_tokens", "total_tokens")]
    counts.extend(recorded_usage[key] for key in ("input_tokens", "output_tokens"))
    if any(type(count) is not int or count < 0 for count in counts):
        raise ValueError("INVALID_TOKEN_USAGE")
    if (
        usage["prompt_tokens"] != recorded_usage["input_tokens"]
        or usage["completion_tokens"] != recorded_usage["output_tokens"]
        or usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]
    ):
        raise ValueError("USAGE_CHAIN_MISMATCH")


def pack_findings(folder: Path, manifest: dict) -> list[str]:
    """Account for every cassette and attempt without treating retries as duplicate hashes."""
    findings = []
    if manifest["recorded_sha"] != manifest["authorization"].get("source_sha"):
        findings.append("MANIFEST_SOURCE_SHA_MISMATCH")
    identities = set()
    referenced = set()
    for attempt in manifest["attempts"]:
        identity = (attempt.get("prompt_hash"), attempt.get("attempt_index"))
        if identity in identities:
            findings.append("DUPLICATE_ATTEMPT_IDENTITY")
        identities.add(identity)
        if type(identity[1]) is not int or identity[1] < 1:
            findings.append("INVALID_ATTEMPT_INDEX")
        referenced.add(f"{identity[0]}.json")
    for path in sorted((folder / "cassettes").rglob("*")):
        if path.is_file() and path.relative_to(folder / "cassettes").as_posix() not in referenced:
            findings.append("UNREFERENCED_CASSETTE_FILE")
    return sorted(set(findings))


def validate_pack(folder: Path) -> dict:
    manifest = json.loads((folder / "RECORDING_MANIFEST.json").read_text(encoding="utf-8"))
    checks = []
    authorization = manifest["authorization"]
    findings = pack_findings(folder, manifest)
    source_match = authorization.get("source_fingerprints") == source_fingerprints()
    for attempt in manifest["attempts"]:
        try:
            checks.append(validate_attempt(folder, attempt, authorization))
        except Exception as error:
            checks.append(
                {
                    "flow": attempt.get("flow"),
                    "step": attempt.get("step"),
                    "prompt_hash": attempt.get("prompt_hash"),
                    "integrity_status": "FAIL",
                    "reason": (
                        str(error).split(";")[0]
                        if type(error) is ValueError
                        else type(error).__name__
                    ),
                }
            )
    return {
        "recorded_sha": manifest["recorded_sha"],
        "checks": checks,
        "pack_findings": findings,
        "integrity_status": (
            "PASS"
            if source_match
            and not findings
            and checks
            and all(c["integrity_status"] == "PASS" for c in checks)
            else "FAIL"
        ),
        "pack_status": "NOT_APPROVED",
        "current_source_match": "PASS" if source_match else "FAIL",
        "privacy_status": "NOT_VERIFIED",
        "product_replay": "NOT_RUN; guarded fresh-DB audit required",
        "business_semantics": "NOT_VERIFIED",
        "live_provider_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    save_json(options.output, validate_pack(options.directory))
    LOGGER.warning(
        "Integrity check saved; origin/privacy/pack acceptance still requires independent review"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
