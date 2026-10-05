"""Manual, synthetic OpenAI probe: exactly one request each for R2, R4, R7.

Requires OPENAI_API_KEY and OPENAI_MODEL in the launching environment.
No .env credential fallback, production wrapper calls, or request retries.
PASS means unchanged schemas work; PARTIAL includes normalized-schema success
or mixed results; FAIL means no stage passed (or preflight failed).
"""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace


def strict_copy(schema: dict) -> dict:
    """Close object shapes only; preserve properties, required fields and enums."""
    normalized = copy.deepcopy(schema)

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(normalized)
    return normalized


def probe(client, model: str, stage: str, schema: dict, prompt: str, validate) -> dict:
    normalized = strict_copy(schema)
    report = {
        "stage": stage,
        "result": "FAIL",
        "http_status": None,
        "exception_class": None,
        "latency_ms": None,
        "schema": "unchanged" if normalized == schema else "normalized",
        "validator": "NOT_RUN",
        "token_usage": None,
    }
    started = time.perf_counter()
    try:
        # The only network call in this function; no fallback or retry on failure.
        raw = client.chat.completions.with_raw_response.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": stage, "strict": True, "schema": normalized},
            },
        )
        report["http_status"] = raw.status_code
        response = raw.parse()
        if response.usage is not None:
            report["token_usage"] = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        report["validator"] = "FAIL"
        message = response.choices[0].message
        if message.refusal or response.choices[0].finish_reason != "stop":
            raise ValueError("Refused or incomplete structured output")
        data = json.loads(message.content or "")
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        validate(data)
        report["validator"] = "PASS"
        report["result"] = "SUCCESS"
    except Exception as error:
        # Do not print str(error), error.body, response content, or SDK tracebacks.
        report["exception_class"] = type(error).__name__
        status = getattr(error, "status_code", None)
        if isinstance(status, int):
            report["http_status"] = status
        if getattr(error, "code", None) == "invalid_json_schema":
            report["schema"] = "rejected"
    finally:
        report["latency_ms"] = round((time.perf_counter() - started) * 1000)
    print(json.dumps(report, ensure_ascii=True), flush=True)
    return report


def run(api_key: str, model: str) -> int:
    from openai import OpenAI

    from core import extract, generate, retrieval
    from core.extract import EXTRACTION_SCHEMA
    from core.generate import GENERATE_SCHEMA
    from core.retrieval import SELECT_SCHEMA

    email = "What is the maximum conduct score? Please explain the general rule."
    extraction = {
        "language": "en",
        "requests": [{
            "domain": "conduct_score",
            "intent": "Hỏi thang điểm rèn luyện tối đa",
            "is_informational": True,
            "requires_personal_record": False,
            "asks_exception": False,
            "asks_appeal": False,
            "asks_authority_decision": False,
        }],
        "critical_facts": [],
        "missing_critical_facts": [],
        "injection_suspected": False,
    }
    chunks = [
        {"chunk_id": "SYNTH_A", "breadcrumb": "Synthetic conduct rule",
         "text": "The maximum conduct score is 100 points."},
        {"chunk_id": "SYNTH_B", "breadcrumb": "Synthetic withdrawal rule",
         "text": "Course withdrawal uses the designated withdrawal form."},
        {"chunk_id": "SYNTH_C", "breadcrumb": "Synthetic appeal rule",
         "text": "Grade appeals use the designated appeal form."},
    ]
    # Citation validators only inspect chunk_id; no database lookup is required.
    evidence = SimpleNamespace(chunks=[SimpleNamespace(**chunks[0])])

    def validate_r2(data: dict) -> None:
        extract._language(data.get("language"))
        for request in extract._items(data.get("requests"), "requests"):
            extract._request(request)
        extract._items(data.get("critical_facts"), "critical_facts")
        extract._facts(data.get("critical_facts"))
        extract._strings(data.get("missing_critical_facts"), "missing_critical_facts")
        extract._boolean(data.get("injection_suspected"), "injection_suspected")

    def validate_r4(data: dict) -> None:
        ids = retrieval._strings(data.get("chunk_ids"))
        retrieval._strings(data.get("missing_facts"))
        retrieval._strings(data.get("unanswered_requests"))
        if not set(ids) <= {chunk["chunk_id"] for chunk in chunks}:
            raise ValueError("Unknown evidence ID")

    def validate_r7(data: dict) -> None:
        generate._string(data.get("subject"), "subject")
        body = generate._string(data.get("body"), "body")
        citations = generate._citations(data.get("citations"), evidence)
        if not generate._paragraphs_cited(body, citations):
            raise ValueError("Missing paragraph citation")

    # Independent synthetic fixtures allow all three calls even if R2/R4 fails.
    calls = [
        ("R2", EXTRACTION_SCHEMA, extract.EXTRACT_PROMPT_V1.format(body=email), validate_r2),
        ("R4", SELECT_SCHEMA, retrieval.SELECT_PROMPT_V1.format(
            email=email, extraction=json.dumps(extraction),
            received_at="2026-10-05T09:00:00+07:00", evidence=json.dumps(chunks),
        ), validate_r4),
        ("R7", GENERATE_SCHEMA, generate.GENERATE_PROMPT_V1.format(
            language="English", email=email, extraction=json.dumps(extraction),
            evidence=generate._evidence_text(evidence),
        ), validate_r7),
    ]
    originals = [copy.deepcopy(schema) for _, schema, _, _ in calls]
    with OpenAI(
        api_key=api_key, base_url="https://api.openai.com/v1",
        max_retries=0, timeout=30.0,
    ) as client:
        reports = [probe(client, model, *call) for call in calls]
    if any(schema != original for (_, schema, _, _), original in zip(calls, originals)):
        raise RuntimeError("Source schema mutation detected")
    passed = sum(report["result"] == "SUCCESS" for report in reports)
    verdict = "FAIL" if passed == 0 else "PARTIAL"
    if passed == 3 and all(report["schema"] == "unchanged" for report in reports):
        verdict = "PASS"
    print(f"PROBE {verdict}")
    return {"PASS": 0, "PARTIAL": 2, "FAIL": 1}[verdict]


def main() -> int:
    # Capture these BEFORE project imports, which may load local .env settings.
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    if not api_key or not model:
        print("Preflight FAIL: OPENAI_API_KEY and OPENAI_MODEL must be in environment.")
        print("PROBE FAIL")
        return 1
    logging.disable(logging.CRITICAL)  # Avoid SDK/project payload logging.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    previous_db = os.environ.get("DATABASE_PATH")
    try:
        # corpus imports auto-seed SQLite: isolate that side effect from app DBs.
        with tempfile.TemporaryDirectory(prefix="openai_compat_probe_") as directory:
            os.environ["DATABASE_PATH"] = str(Path(directory) / "probe.db")
            return run(api_key, model)
    except Exception as error:
        print(json.dumps({"setup_or_local_failure": type(error).__name__}))
        print("PROBE FAIL")
        return 1
    finally:
        if previous_db is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = previous_db


if __name__ == "__main__":
    raise SystemExit(main())
