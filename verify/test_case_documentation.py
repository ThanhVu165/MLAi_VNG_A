"""Bản đọc phải giữ nguyên mọi trường của bộ case đã duyệt."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from infra import db
from verify.harness import load_cases, run_cases


def test_documentation_matches_all_executable_cases() -> None:
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "verify/cases_full15.json").read_text(encoding="utf-8"))
    document = (root / "docs/bo_15_ca_kiem_thu.md").read_text(encoding="utf-8")
    section = document.split("<!-- CASES_START -->")[1].split("<!-- CASES_END -->")[0]
    ids = re.findall(r"^## (\w+)$", section, re.MULTILINE)
    assert len(ids) == len(set(ids)) == len(cases) == 15
    assert ids == [case["id"] for case in cases]
    blocks = re.split(r"^## \w+\n", section, flags=re.MULTILINE)[1:]
    for case, block in zip(cases, blocks, strict=True):
        expected = {**case["input"], **{k: v for k, v in case.items() if k not in {"id", "input"}}}
        fields = re.findall(r"^- .*?\(`(\w+)`\): (.*)$", block, re.MULTILINE)
        assert len(fields) == len(expected)
        assert dict(fields) == {
            key: "null" if value is None else value for key, value in expected.items()
        }


def test_full15_loads_empty_body_and_runs_real_invalid_case(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    path = Path(__file__).resolve().parent / "cases_full15.json"
    assert len(load_cases(path)) == 15
    results = run_cases(path, run_name="full15", case_id="F01")
    assert len(results) == 1 and results[0].passed
    assert results[0].rule_id == "R0"
    assert db.fetch_all("SELECT case_id FROM escalations") == []
