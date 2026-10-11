"""Protect the exact frozen bytes without changing loader hash semantics."""

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from verify import m2_dev_assessment as assessment
from verify import m2_dev_execution as execution

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = "verify/cases_m2_combined_dev.json"


@pytest.mark.parametrize("autocrlf", ["true", "input", "false"])
def test_git_checkout_preserves_frozen_bytes(autocrlf):
    blob = subprocess.check_output(["git", "show", f"HEAD:{FIXTURE_PATH}"], cwd=ROOT)
    checkout = subprocess.check_output(
        [
            "git",
            "-c",
            f"core.autocrlf={autocrlf}",
            "cat-file",
            "--filters",
            f"HEAD:{FIXTURE_PATH}",
        ],
        cwd=ROOT,
    )
    assert checkout == blob == execution.FIXTURE.read_bytes()
    assert b"\r\n" not in checkout
    assert hashlib.sha256(checkout).hexdigest() == execution.FIXTURE_SHA256
    assert assessment.FIXTURE_SHA256 == execution.FIXTURE_SHA256


def test_canonical_fixture_passes_both_integrity_loaders():
    cases = execution.load_frozen_cases()
    assert len(cases) == 12
    assert assessment.load_prereg(cases[0]["id"]) == cases[0]


def test_semantic_mutation_is_blocked_by_both_loaders(tmp_path):
    raw = execution.FIXTURE.read_bytes()
    cases = json.loads(raw)
    original_subject = cases[0]["input"]["subject"]
    mutated_subject = original_subject + " INTEGRITY_TEST_MUTATION"
    original_token = json.dumps(original_subject, ensure_ascii=False).encode("utf-8")
    mutated_token = json.dumps(mutated_subject, ensure_ascii=False).encode("utf-8")
    mutated = raw.replace(original_token, mutated_token, 1)
    assert mutated != raw
    assert json.loads(mutated)[0]["input"]["subject"] == mutated_subject
    fixture = tmp_path / "semantic-mutation.json"
    fixture.write_bytes(mutated)
    with pytest.raises(ValueError, match="BLOCKED_FIXTURE_HASH_MISMATCH"):
        execution.load_frozen_cases(fixture)
    with pytest.raises(ValueError, match="BLOCKED_FIXTURE_HASH_MISMATCH"):
        assessment.load_prereg(cases[0]["id"], fixture)
    assert execution.FIXTURE.read_bytes() == raw
