"""Synthetic accounting proof only; no claim about actual provider token usage."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from core.pipeline import process_case
from core.results import load_result
from core.types import CaseStatus
from infra import db, judge_access as access, llm
from test_judge_input_c1 import NONCE, SECRET, _input
from test_judge_input_c1 import judge as _judge_fixture
from test_judge_input_c2a import _ledgers
from test_judge_new_input_offline import _extraction, _selection
from test_core_reliability import _retry_payload

TEMPLATE = Path(__file__).parent / "fixtures/c2c_simulation/usage_case.json"
judge = _judge_fixture
CASE = "c_c2c_simulation"
PROMPT = "synthetic prompt"
SCHEMA = {"type": "object"}


def _fixture(directory, prompt=PROMPT, **updates):
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    payload.update(updates)
    key = llm._prompt_hash(["openai", payload["model"], SCHEMA, prompt, 0.0])
    payload["prompt_hash"] = key
    directory.mkdir(exist_ok=True)
    (directory / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
    return key


def _call(prompt=PROMPT, step="R2_extract", **kwargs):
    return llm.call_json(prompt, schema=SCHEMA, step=step, case_id=CASE, **kwargs)


@pytest.fixture
def simulation(judge, tmp_path):
    directory = tmp_path / "synthetic"
    _fixture(directory)
    with access.request_scope(judge, "session-a", NONCE, CASE, "unused"):
        with llm._c2c_simulation(CASE, directory) as budget:
            yield directory, budget
        assert not db.fetch_all("SELECT * FROM case_jobs")
        assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")


def test_cumulative_attempts_retry_and_repair_cannot_reset(simulation):
    _, budget = simulation
    before = deepcopy(_ledgers())
    for step in ("R2_extract", "R2_validation_retry", "R7_basis_repair"):
        with llm.case_call_budget(3):
            result = _call(step=step, retries=10)
            assert result.ok and result.usage["source"] == "synthetic"
    assert (budget.input_tokens, budget.output_tokens, budget.attempts) == (24000, 6000, 3)
    with llm.case_call_budget(3):
        assert not _call().ok
    assert budget.attempts == 3
    assert _ledgers() == before


@pytest.mark.parametrize("axis", ["input", "output"])
def test_over_budget_blocks_before_response_decode(simulation, monkeypatch, axis):
    directory, budget = simulation
    assert _call().ok
    request = {
        "input_tokens": 16001 if axis == "input" else 1,
        "max_output_tokens": 4001 if axis == "output" else 1,
    }
    _fixture(directory, request=request)
    calls = []
    monkeypatch.setattr(llm, "_parse_object", lambda value: calls.append(value))
    assert not _call().ok
    assert calls == [] and budget.attempts == 1
    assert (budget.input_tokens, budget.output_tokens) == (8000, 2000)


@pytest.mark.parametrize(
    "usage",
    [
        None,
        {},
        {"input_tokens": True, "output_tokens": 1},
        {"input_tokens": -1, "output_tokens": 1},
        {"input_tokens": 8000, "output_tokens": "2"},
        {"input_tokens": 1, "output_tokens": 2000},
        {"input_tokens": 8000, "output_tokens": 2001},
    ],
)
def test_untrusted_usage_poisoned_scope_never_refunds(simulation, usage):
    directory, budget = simulation
    before = deepcopy(_ledgers())
    _fixture(directory, usage=usage)
    assert not _call().ok
    assert (budget.input_tokens, budget.output_tokens, budget.attempts) == (8000, 2000, 1)
    _fixture(directory)
    assert not _call().ok
    assert budget.attempts == 1 and budget.blocked
    assert _ledgers() == before


def test_missing_usage_key_retains_full_allocation(simulation):
    directory, budget = simulation
    key = _fixture(directory)
    path = directory / f"{key}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["usage"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert not _call().ok and budget.blocked
    assert (budget.input_tokens, budget.output_tokens) == (8000, 2000)


def test_valid_synthetic_usage_reconciles_only_in_memory(simulation):
    directory, budget = simulation
    before = deepcopy(_ledgers())
    _fixture(directory, usage={"input_tokens": 8000, "output_tokens": 100})
    assert _call().ok
    assert (budget.input_tokens, budget.output_tokens) == (8000, 100)
    assert _ledgers() == before


def test_direct_sdk_boundary_is_disabled_in_simulation(simulation):
    with pytest.raises(ValueError, match="LIVE"):
        llm._request_openai(PROMPT, SCHEMA, "synthetic", "model", "unused", 1)


@pytest.mark.parametrize(
    "update", [{"request": {}}, {"request": None}, {"is_synthetic": False}, {"model": "different"}]
)
def test_invalid_request_or_provenance_denied(simulation, update):
    directory, budget = simulation
    key = _fixture(directory)
    path = directory / f"{key}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(update)
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert not _call().ok
    assert budget.attempts == 0


@pytest.mark.parametrize("action", ["kill", "revoke", "hold", "deadline", "live"])
def test_next_attempt_blocked_by_runtime_guards(simulation, judge, monkeypatch, action):
    _, budget = simulation
    assert _call().ok
    if action == "kill":
        monkeypatch.setenv("JUDGE_INPUT_ENABLED", "0")
    elif action == "revoke":
        access.revoke_grant(judge, SECRET)
    elif action == "hold":
        assert access.recover_reservations(SECRET) == {CASE: "HOLD"}
    elif action == "deadline":
        budget.deadline = llm.perf_counter() - 1
    else:
        monkeypatch.setenv("LLM_MODE", "live")
    before = deepcopy(_ledgers())
    assert not _call().ok
    assert _ledgers() == before and budget.attempts == 1


def test_nested_scope_cannot_restart_allowance(simulation):
    directory, _ = simulation
    with pytest.raises(ValueError):
        with llm._c2c_simulation(CASE, directory):
            pass


@pytest.mark.parametrize("retry", [False, True])
def test_strict_pipeline_preserves_c2a_and_core71(judge, tmp_path, monkeypatch, retry):
    directory = tmp_path / "pipeline"
    data = (
        [
            _retry_payload(_extraction("JUDGE-AUTHORITY")),
            _extraction("JUDGE-AUTHORITY"),
            _selection("JUDGE-AUTHORITY"),
        ]
        if retry
        else [
            _extraction("JUDGE-AUTO"),
            _selection("JUDGE-AUTO"),
            {
                "subject": "Lệ phí phúc khảo",
                "body": "Lệ phí phúc khảo là 150.000 đồng cho mỗi học phần [PK-2026-204:seed:2].",
                "citations": ["PK-2026-204:seed:2"],
            },
        ]
    )
    keys = [
        _fixture(directory, prompt=f"synthetic-{i}", data=value) for i, value in enumerate(data)
    ]
    iterator = iter(keys)
    monkeypatch.setattr(llm, "_prompt_hash", lambda identity: next(iterator))
    inp = _input("JUDGE-AUTHORITY" if retry else "JUDGE-AUTO")
    expected = CaseStatus.AWAITING_HUMAN if retry else CaseStatus.PREVIEW_READY
    fingerprint = access.payload_hash(inp.sender, inp.subject, inp.body, inp.received_at)
    with access.request_scope(judge, "session-a", NONCE, CASE, fingerprint):
        access.mark_processing()
        before = deepcopy(_ledgers())
        with llm._c2c_simulation(CASE, directory) as budget:
            result = process_case(inp, actor="SYSTEM", case_id=CASE)
            assert result.status is expected
            if retry:
                assert result.card is not None and result.decision.rule_id == "P01"
            assert (budget.input_tokens, budget.output_tokens, budget.attempts) == (24000, 6000, 3)
        assert _ledgers() == before
    c1, c2 = _ledgers()
    assert c1["total"] == 1 and not c1["active"]
    assert c2["requests"][CASE]["input_tokens"] == 24000
    assert c2["requests"][CASE]["output_tokens"] == 6000
    assert load_result(CASE).status is expected
    assert not db.fetch_all("SELECT * FROM case_jobs")
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
