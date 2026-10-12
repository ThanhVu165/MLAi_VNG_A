"""Offline M6-T05 inventory and real pipeline/Verify/human-resume observations.

Run from the repository root: python -m scripts.audit_runtime_replay.
Exit 2 means the observed replay pack is incomplete, not an audit tool failure.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-luna"
CONFIG = {
    "LLM_MODE": "replay",
    "LLM_PROVIDER": "openai",
    "OPENAI_MODEL": MODEL,
    "OPENAI_REASONING_EFFORT": "none",
    "LLM_CACHE": "0",
}
DEV_INPUTS = (
    (
        "DEV_ROUTINE",
        "Hỏi lệ phí phúc khảo",
        "Cho em hỏi lệ phí phúc khảo một học phần là bao nhiêu?",
    ),
    (
        "DEV_AUTHORITY",
        "Xin phúc khảo trễ",
        "Em xin được nộp đơn phúc khảo môn X sau thời hạn, nhờ trường chấp thuận ngoại lệ cho em.",
    ),
    (
        "DEV_FACT",
        "Văn bản rèn luyện áp dụng",
        "Cho em hỏi văn bản điểm rèn luyện nào áp dụng cho khóa học và học kỳ của em?",
    ),
)
HUMAN_INPUT = {
    "subject": "Synthetic DEV — yêu cầu bản dịch",
    "body": "学生の質問を確認してください。",
    "choice": "Yêu cầu bản dịch",
    "reason": "Đề nghị bổ sung nội dung bằng tiếng Việt hoặc tiếng Anh để đối chiếu quy định.",
}
SOURCE_FILES = (
    "infra/llm.py",
    "infra/settings.py",
    "infra/db.py",
    "core/pipeline.py",
    "core/extract.py",
    "core/retrieval.py",
    "core/generate.py",
    "core/question_gen.py",
    "core/question_guard.py",
    "core/resume.py",
    "core/worker.py",
    "pages/2_Hang_cho_duyet.py",
    "verify/harness.py",
    "verify/cases_verify4.json",
    "policies/policy.yaml",
)


class OfflineViolation(BaseException):
    """Cannot be swallowed by the product's technical-error handlers."""


def forbidden(*args: object, **kwargs: object) -> None:
    raise OfflineViolation("OFFLINE_ONLY: network/provider/cache access forbidden")


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def inventory(directory: Path, schemas: dict[str, dict]) -> list[dict]:
    """Inspect artifacts without assigning provider provenance from their contents."""
    from jsonschema import Draft202012Validator

    entries = []
    for path in sorted(directory.glob("*.json")):
        raw = path.read_bytes()
        entry = {
            "file": path.name,
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "filename_hash_valid": bool(re.fullmatch(r"[0-9a-f]{64}\.json", path.name)),
            "source": "existing checkout file; provider origin NOT VERIFIED",
            "provenance_status": "MISSING",
            "recorded_sha": None,
            "authorization": None,
            "prompt_identity_verified": False,
        }
        try:
            payload = json.loads(raw)
            data = payload.get("data", payload) if isinstance(payload, dict) else None
            if not isinstance(data, dict):
                raise ValueError("Response is not an object")
            entry["readable"] = True
            entry["model"] = payload.get("model")
            entry["model_compatible"] = entry["model"] == MODEL
            entry["matching_schemas"] = [
                name
                for name, schema in schemas.items()
                if Draft202012Validator(schema).is_valid(data)
            ]
        except (ValueError, UnicodeError):
            entry.update(readable=False, model_compatible=False, matching_schemas=[])
        entries.append(entry)
    return entries


def observe_runtime() -> tuple[list[dict], list[dict], dict]:
    """Only observe real responses; never supply an extraction, draft or policy result."""
    from core import extract, generate, question_gen, resume, retrieval
    from core.pipeline import process_case
    from infra import db, llm

    calls: list[dict] = []
    outcomes: list[dict] = []
    original = llm._run_mode

    def observe(prompt, schema, prompt_hash, model, timeout_s, retries, **kwargs):
        assert os.environ["LLM_MODE"] == "replay"
        identity = ["openai", model, schema, prompt, 0.0]
        assert digest(identity) == llm._prompt_hash(identity) == prompt_hash
        result = original(prompt, schema, prompt_hash, model, timeout_s, retries, **kwargs)
        calls.append(
            {
                "step": kwargs["step"],
                "case_ref": kwargs["case_id"],
                "prompt_hash": prompt_hash,
                "prompt": prompt,
                "schema": schema,
                "schema_sha256": digest(schema),
                "provider_schema_sha256": digest(llm._openai_schema(schema)),
                "temperature": 0.0,
                "model": model,
                "provider": "openai",
                "reasoning_effort": "none",
                "timeout_s": timeout_s,
                "retries": retries,
                "cassette_source": f"tests/cassettes/{prompt_hash}.json",
                "replay_ok": result.ok,
                "error": result.error,
                "data": result.data,
                "flow": active_flow[0],
            }
        )
        return result

    active_flow = [""]
    with patch.object(llm, "_run_mode", observe), patch.object(
        llm, "_call_live", forbidden
    ), patch.object(llm, "_load_cache", forbidden):
        outcomes.extend(observe_pipeline_cases(process_case, active_flow))
        active_flow[0] = "DEV_HUMAN_R11"
        outcomes.append(observe_human_resume(process_case, db))
    schemas = {
        "R2_extract": extract.EXTRACTION_SCHEMA,
        "R4_select": retrieval.SELECT_SCHEMA,
        "R7_generate": generate.GENERATE_SCHEMA,
        "R7_question": question_gen.QUESTION_SCHEMA,
        "R11_resume": resume.RESUME_SCHEMA,
    }
    return calls, outcomes, schemas


def observe_pipeline_cases(process_case: Callable, active_flow: list[str]) -> list[dict]:
    from core.types import CaseInput
    from verify.harness import run_cases

    outcomes = []
    for name, subject, body in DEV_INPUTS:
        active_flow[0] = name
        inp = CaseInput(
            "synthetic@example.invalid",
            subject,
            body,
            datetime.fromisoformat("2026-09-21T09:00:00+07:00"),
            "paste",
        )
        outcomes.append({"flow": name, "input": asdict(inp), "result": asdict(process_case(inp))})
    for name in ("V01", "V02", "V03", "V04"):
        active_flow[0] = name
        result = run_cases(
            Path("verify/cases_verify4.json"), run_name="m6-t05-offline", case_id=name
        )[0]
        outcomes.append({"flow": name, "verify_result": asdict(result)})
    return outcomes


def observe_human_resume(process_case: Callable, db: ModuleType) -> dict:
    """Reach R11 through actual R1 intake, review page decision and worker job."""
    from core.types import CaseInput, CaseStatus
    from core.worker import worker_tick
    from streamlit.testing.v1 import AppTest

    inp = CaseInput(
        "synthetic@example.invalid",
        HUMAN_INPUT["subject"],
        HUMAN_INPUT["body"],
        datetime.fromisoformat("2026-09-21T09:04:00+07:00"),
        "paste",
    )
    result = process_case(inp)
    assert result.status is CaseStatus.AWAITING_HUMAN
    case_id = result.case_id
    page = AppTest.from_file(str(ROOT / "pages/2_Hang_cho_duyet.py")).run(timeout=20)
    assert not page.exception
    page.radio(key=f"choice_{case_id}").set_value(HUMAN_INPUT["choice"])
    page.text_area(key=f"reason_{case_id}").set_value(HUMAN_INPUT["reason"])
    page.run(timeout=20)
    page.button(key=f"decide_{case_id}").click().run(timeout=20)
    assert not page.exception
    assert (
        db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))[0] == "HUMAN_DECIDED"
    )
    worker_tick()
    return {
        "flow": "DEV_HUMAN_R11",
        "input": asdict(inp),
        "human_input": HUMAN_INPUT,
        "intake_result": asdict(result),
        "final_case": dict(db.fetch_one("SELECT status FROM cases WHERE case_id = ?", (case_id,))),
        "job": dict(db.fetch_one("SELECT state FROM case_jobs WHERE case_id = ?", (case_id,))),
        "human_decision": dict(
            db.fetch_one(
                "SELECT choice, reason, actor FROM human_decisions WHERE case_id = ?", (case_id,)
            )
        ),
        "draft_count": db.fetch_one("SELECT COUNT(*) FROM drafts WHERE case_id = ?", (case_id,))[0],
    }


def source_fingerprints() -> dict[str, str]:
    source_hashes = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_FILES
    }
    source_hashes.update(
        {
            str(path.relative_to(ROOT))
            .replace("\\", "/"): hashlib.sha256(path.read_bytes())
            .hexdigest()
            for path in sorted((ROOT / "data/seed_docs").glob("*.json"))
        }
    )
    source_hashes["scripts/audit_runtime_replay.py"] = hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    return source_hashes


def write_artifacts(
    output_dir: Path, sha: str, calls: list[dict], outcomes: list[dict], entries: list[dict]
) -> None:
    evidence = {
        "schema_version": 1,
        "tested_sha": sha,
        "python": sys.version,
        "config": CONFIG,
        "source_sha256": source_fingerprints(),
        "database": "fresh TemporaryDirectory; destroyed after observation",
        "is_synthetic": True,
        "live_provider_calls": 0,
        "network_guard": "socket and _call_live denied; replay must bypass _load_cache",
        "calls": calls,
        "outcomes": outcomes,
    }
    manifest = {
        "schema_version": 1,
        "tested_sha": sha,
        "pack_status": "NOT_APPROVED",
        "record_authorization": None,
        "cassette_directory_exists": (ROOT / "tests/cassettes").is_dir(),
        "reported_historical_count": 116,
        "historical_artifacts_available": False,
        "cassette_count": len(entries),
        "cassettes": entries,
        "required_observed_calls": [
            {
                key: call[key]
                for key in (
                    "flow",
                    "step",
                    "prompt_hash",
                    "schema_sha256",
                    "provider_schema_sha256",
                    "model",
                    "provider",
                    "temperature",
                    "reasoning_effort",
                    "cassette_source",
                    "replay_ok",
                )
            }
            | {"provenance_status": "MISSING", "authorization": None}
            for call in calls
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in (("EVIDENCE", evidence), ("MANIFEST", manifest)):
        (output_dir / f"M6_T05_REPLAY_{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/readiness"))
    options = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error("Run from the repository root")
    if "infra.db" in sys.modules:
        parser.error("Database already imported; use a fresh interpreter")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="m6-t05-offline-") as directory, ExitStack() as guards:
        os.environ.update(CONFIG)
        os.environ["DATABASE_PATH"] = str(Path(directory) / "app.db")
        for name in ("connect", "connect_ex", "sendto"):
            guards.enter_context(patch.object(socket.socket, name, forbidden))
        guards.enter_context(patch.object(socket, "create_connection", forbidden))
        guards.enter_context(patch.object(socket, "getaddrinfo", forbidden))
        calls, outcomes, schemas = observe_runtime()
        entries = inventory(ROOT / "tests/cassettes", schemas)
        observed = {call["prompt_hash"] for call in calls}
        for entry in entries:
            entry["referenced_by_observed_run"] = Path(entry["file"]).stem in observed
    write_artifacts(options.output_dir, sha, calls, outcomes, entries)
    LOGGER.warning(
        "Audit complete: %s cassettes; %s calls; %s replay failures; LIVE=0",
        len(entries),
        len(calls),
        sum(not call["replay_ok"] for call in calls),
    )
    # This Phase 1 tool cannot certify provider provenance, even if response files appear.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
