"""C2-A offline: provisioning/revocation, atomic forecast budgets và crash recovery."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from core.judge_input import process_judge_case
from core.results import load_result
from core.types import CaseStatus, Decision
from infra import db, judge_access as access, llm
from test_judge_input_c1 import NONCE, SECRET, _input, _provider
from test_judge_input_c1 import judge as _judge_fixture

judge = _judge_fixture


def _ledgers() -> tuple[dict, dict]:
    with db.transaction() as connection:
        return access._load(connection), access._load_c2(connection)


def test_provisioning_requires_operator_and_is_single_use(judge: access.JudgeGrant) -> None:
    for secret in ("", "guest", "ADMIN:fake"):
        with pytest.raises(access.JudgeDenied):
            access.provision_grant("session-b", secret, "provisioning-request-0001")
    granted = access.provision_grant("session-b", SECRET, "provisioning-request-0001")
    before = _ledgers()
    with pytest.raises(access.JudgeDenied):
        access.provision_grant("session-b", SECRET, "provisioning-request-0001")
    assert _ledgers() == before
    assert access.grant_is_valid(granted, "session-b")
    assert not access.grant_is_valid(granted, "session-other")
    assert granted.token not in json.dumps(_ledgers())


@pytest.mark.parametrize("grant_kind", ["guest", "forged", "expired", "revoked"])
def test_invalid_or_revoked_grant_has_no_request_side_effect(
    judge, monkeypatch, grant_kind
) -> None:
    grant = judge
    if grant_kind == "guest":
        grant = None
    elif grant_kind == "forged":
        grant = access.JudgeGrant("forged")
    elif grant_kind == "expired":
        monkeypatch.setattr(access.time, "time", lambda: 99_999_999_999)
    else:
        access.revoke_grant(judge, SECRET)
    before = _ledgers()
    with pytest.raises(access.JudgeDenied):
        process_judge_case(_input(), grant=grant, session="session-a", nonce=NONCE)
    assert _ledgers() == before
    assert not db.fetch_all("SELECT * FROM cases")


def test_revocation_requires_operator_persists_and_works_with_flag_off(judge, monkeypatch) -> None:
    with pytest.raises(access.JudgeDenied):
        access.revoke_grant(judge, "guest")
    assert access.grant_is_valid(judge, "session-a")
    monkeypatch.setenv("JUDGE_INPUT_ENABLED", "0")
    access.revoke_grant(judge, SECRET)
    access.revoke_grant(judge, SECRET)
    monkeypatch.setenv("JUDGE_INPUT_ENABLED", "1")
    assert not access.grant_is_valid(judge, "session-a")
    assert _ledgers()[1]["revoked"] == [access._hash(judge.token)]


@pytest.mark.parametrize("limit_kind", ["token", "estimated_cost"])
def test_concurrent_reservation_cannot_exceed_budget(judge, monkeypatch, limit_kind) -> None:
    grants = [judge] + [access.issue_grant("session-" + str(i), SECRET) for i in range(1, 8)]
    barrier = Barrier(8)
    if limit_kind == "token":
        monkeypatch.setattr(access, "GLOBAL_TOKEN_RESERVATION_LIMIT", 60_000)
        expected = 2
    else:
        monkeypatch.setattr(access, "GLOBAL_ESTIMATE_MICRO_USD_LIMIT", 15_000)
        expected = 1

    def attempt(index: int) -> bool:
        barrier.wait(timeout=10)
        session = "session-a" if index == 0 else "session-" + str(index)
        try:
            with access.request_scope(
                grants[index], session, NONCE, "budget-" + str(index), "hash"
            ):
                return True
        except access.JudgeDenied:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(8)))
    c1, c2 = _ledgers()
    assert sum(results) == expected
    assert c1["total"] == expected
    assert len(c2["requests"]) == expected
    assert (
        sum(r["input_tokens"] + r["output_tokens"] for r in c2["requests"].values())
        <= access.GLOBAL_TOKEN_RESERVATION_LIMIT
    )
    assert (
        sum(r["estimated_micro_usd"] for r in c2["requests"].values())
        <= access.GLOBAL_ESTIMATE_MICRO_USD_LIMIT
    )


def test_new_grants_cannot_reset_session_token_budget(judge, monkeypatch) -> None:
    monkeypatch.setattr(access, "SESSION_TOKEN_RESERVATION_LIMIT", 30_000)
    with access.request_scope(judge, "session-a", NONCE, "first", "hash"):
        pass
    other = access.issue_grant("session-a", SECRET)
    before = _ledgers()
    with pytest.raises(access.JudgeDenied):
        with access.request_scope(other, "session-a", NONCE, "second", "hash"):
            pytest.fail("Grant mới đã reset budget của session")
    assert _ledgers() == before


@pytest.mark.parametrize("action", ["revoke", "kill"])
def test_revocation_or_kill_switch_between_provider_steps(judge, monkeypatch, action) -> None:
    calls = _provider(monkeypatch)
    replay = llm._replay

    def revoke_after_response(prompt_hash: str, model: str) -> llm.LLMResult:
        result = replay(prompt_hash, model)
        if action == "revoke":
            access.revoke_grant(judge, SECRET)
        else:
            monkeypatch.setenv("JUDGE_INPUT_ENABLED", "0")
        return result

    monkeypatch.setattr(llm, "_replay", revoke_after_response)
    result = process_judge_case(_input(), grant=judge, session="session-a", nonce=NONCE)
    assert result.status is CaseStatus.ERROR
    assert result.decision.decision is Decision.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR"
    assert len(calls) == 1
    assert load_result(result.case_id).status is CaseStatus.ERROR
    assert not db.fetch_all("SELECT * FROM audit_events WHERE action LIKE 'SEND_%'")
    assert len(_ledgers()[1]["requests"]) == 1


def _crash_process(grant: access.JudgeGrant, phase: str) -> None:
    root = Path(__file__).resolve().parents[1]
    code = """
import os, socket, openai
from infra import judge_access as a
from core.pipeline import process_case
from test_judge_input_c1 import _input, _provider
import pytest
def forbidden(*args, **kwargs):
    raise AssertionError('OFFLINE_ONLY')
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.socket.sendto = forbidden
socket.create_connection = forbidden
socket.getaddrinfo = forbidden
openai.OpenAI = forbidden
openai.AsyncOpenAI = forbidden
if os.environ['C2_PHASE'] == 'before':
    os._exit(17)
grant = a.JudgeGrant(os.environ['C2_GRANT'])
inp = _input()
scope = a.request_scope(grant, 'session-a', 'crash-nonce-offline-0001', 'c_crash', a.payload_hash(inp.sender, inp.subject, inp.body, inp.received_at))
scope.__enter__()
if os.environ['C2_PHASE'] != 'reserved':
    a.mark_processing()
if os.environ['C2_PHASE'] == 'terminal':
    patch = pytest.MonkeyPatch()
    _provider(patch)
    assert process_case(inp, actor='SYSTEM', case_id='c_crash').status.value == 'PREVIEW_READY'
os._exit(17)
"""
    environment = {
        **os.environ,
        "DATABASE_PATH": str(db.DEFAULT_DATABASE_PATH),
        "C2_PHASE": phase,
        "C2_GRANT": grant.token,
        "PYTHONPATH": str(root / "tests") + os.pathsep + str(root),
        "LLM_MODE": "replay",
        "OPENAI_API_KEY": "",
    }
    completed = subprocess.run(
        [sys.executable, "-c", code], env=environment, capture_output=True, timeout=20
    )
    assert completed.returncode == 17, "Offline child did not reach intended crash point"


@pytest.mark.parametrize("phase", ["before", "reserved", "processing", "terminal"])
def test_real_process_crash_recovery_never_refunds_or_replays(judge, phase) -> None:
    _crash_process(judge, phase)
    before_c1, before_c2 = _ledgers()
    original_cases = [tuple(r) for r in db.fetch_all("SELECT * FROM cases ORDER BY rowid")]
    original_audit = [tuple(r) for r in db.fetch_all("SELECT * FROM audit_events ORDER BY rowid")]
    access.revoke_grant(judge, SECRET)
    outcomes = access.recover_reservations(SECRET)
    c1, c2 = _ledgers()
    assert c1["total"] == before_c1["total"] == (0 if phase == "before" else 1)
    assert c1["sessions"] == before_c1["sessions"]
    assert c1["grants"] == before_c1["grants"]
    assert not access.grant_is_valid(judge, "session-a")
    assert len(c2["requests"]) == len(before_c2["requests"])
    if phase == "terminal":
        assert outcomes == {"c_crash": "RECOVERED"}
        assert not c1["active"]
        assert load_result("c_crash").status is CaseStatus.PREVIEW_READY
    elif phase != "before":
        assert outcomes == {"c_crash": "HOLD"}
        assert c1["active"] == {"c_crash": access._hash("session-a")}
    else:
        assert outcomes == {}
    assert [tuple(r) for r in db.fetch_all("SELECT * FROM cases ORDER BY rowid")] == original_cases
    assert [
        tuple(r) for r in db.fetch_all("SELECT * FROM audit_events ORDER BY rowid")
    ] == original_audit
    assert access.recover_reservations(SECRET) == (
        {} if phase in {"before", "terminal"} else {"c_crash": "HOLD"}
    )


def test_recovery_and_replay_nonce_remain_denied(judge) -> None:
    _crash_process(judge, "terminal")
    access.recover_reservations(SECRET)
    before = _ledgers()
    with pytest.raises(access.JudgeDenied):
        with access.request_scope(
            judge, "session-a", "crash-nonce-offline-0001", "duplicate", "hash"
        ):
            pytest.fail("Recovery cleared consumed nonce")
    assert _ledgers() == before


def test_recovery_cannot_resume_an_uncertain_live_context(judge) -> None:
    with access.request_scope(judge, "session-a", NONCE, "uncertain", "hash"):
        access.mark_processing()
        assert access.recover_reservations(SECRET) == {"uncertain": "HOLD"}
        with pytest.raises(access.JudgeDenied):
            access.check_active()
    assert "uncertain" in _ledgers()[0]["active"]


@pytest.mark.parametrize("corruption", ["missing", "malformed", "lost_request"])
def test_budget_ledger_corruption_does_not_restore_permissions(judge, corruption) -> None:
    access.revoke_grant(judge, SECRET)
    if corruption == "missing":
        db.execute("DELETE FROM settings WHERE key=?", (access.C2_STATE_KEY,))
    elif corruption == "malformed":
        db.execute("UPDATE settings SET value='{}' WHERE key=?", (access.C2_STATE_KEY,))
    else:
        _crash_process(access.issue_grant("session-a", SECRET), "reserved")
        with db.transaction() as connection:
            c2 = access._load_c2(connection)
            c2["requests"] = {}
            access._save_c2(connection, c2)
    assert not access.grant_is_valid(judge, "session-a")
    with pytest.raises(access.JudgeDenied):
        access.recover_reservations(SECRET)


def test_operator_required_for_recovery_and_budget_never_refunded(judge, monkeypatch) -> None:
    _provider(monkeypatch)
    result = process_judge_case(_input(), grant=judge, session="session-a", nonce=NONCE)
    before = _ledgers()
    with pytest.raises(access.JudgeDenied):
        access.recover_reservations("guest")
    assert _ledgers() == before
    assert result.status is CaseStatus.PREVIEW_READY
    assert access.recover_reservations(SECRET) == {}
    assert _ledgers() == before


def test_processing_exit_without_terminal_evidence_keeps_hold(judge) -> None:
    with pytest.raises(OSError):
        with access.request_scope(judge, "session-a", NONCE, "uncertain-exit", "hash"):
            access.mark_processing()
            raise OSError("offline failure before durable terminal snapshot")
    c1, c2 = _ledgers()
    assert c1["active"] == {"uncertain-exit": access._hash("session-a")}
    assert c2["requests"]["uncertain-exit"]["phase"] == "HOLD"
    assert c1["total"] == 1


def test_revoked_provisioning_id_cannot_be_reissued(judge) -> None:
    granted = access.provision_grant("session-b", SECRET, "stable-operator-provision-id")
    access.revoke_grant(granted, SECRET)
    access.recover_reservations(SECRET)
    before = _ledgers()
    with pytest.raises(access.JudgeDenied):
        access.provision_grant("session-b", SECRET, "stable-operator-provision-id")
    assert _ledgers() == before


def test_recovery_snapshot_mismatch_stays_hold(judge) -> None:
    _crash_process(judge, "terminal")
    db.execute("UPDATE cases SET status='AWAITING_HUMAN' WHERE case_id='c_crash'")
    assert access.recover_reservations(SECRET) == {"c_crash": "HOLD"}
    assert _ledgers()[0]["total"] == 1
    assert "c_crash" in _ledgers()[0]["active"]


def test_legacy_c1_budget_is_conservatively_carried_forward(judge, monkeypatch) -> None:
    _provider(monkeypatch)
    result = process_judge_case(_input(), grant=judge, session="session-a", nonce=NONCE)
    # Tái tạo dữ liệu C1 trước nâng cấp trong DB synthetic tạm, không sửa schema.
    db.execute(
        "DELETE FROM settings WHERE key IN (?,?)", (access.C2_STATE_KEY, access.C2_ANCHOR_KEY)
    )
    legacy, c2 = _ledgers()
    assert legacy["total"] == 1
    assert c2["requests"][result.case_id]["phase"] == "HOLD"
    assert c2["requests"][result.case_id]["input_tokens"] == access.CASE_INPUT_TOKEN_RESERVATION
    assert c2["requests"][result.case_id]["estimated_micro_usd"] == access.CASE_ESTIMATE_MICRO_USD


def test_direct_common_pipeline_cannot_release_uncertain_processing(judge, monkeypatch) -> None:
    from core.pipeline import process_case

    _provider(monkeypatch)

    def failed_snapshot(*args: object, **kwargs: object) -> None:
        raise OSError("offline terminal persistence unavailable")

    monkeypatch.setattr("core.pipeline.save_result", failed_snapshot)
    inp = _input()
    fingerprint = access.payload_hash(inp.sender, inp.subject, inp.body, inp.received_at)
    with access.request_scope(judge, "session-a", NONCE, "c_direct", fingerprint):
        result = process_case(inp, actor="SYSTEM", case_id="c_direct")
        assert result.status is CaseStatus.ERROR
    assert _ledgers()[0]["active"] == {"c_direct": access._hash("session-a")}
    assert _ledgers()[1]["requests"]["c_direct"]["phase"] == "HOLD"


def test_reservation_commit_failure_rolls_back_both_ledgers(judge, monkeypatch) -> None:
    before = _ledgers()

    def fail_commit(*args: object, **kwargs: object) -> None:
        raise OSError("offline failure after budget reserve before C1 ledger save")

    monkeypatch.setattr(access, "_save", fail_commit)
    with pytest.raises(access.JudgeDenied):
        process_judge_case(_input(), grant=judge, session="session-a", nonce=NONCE)
    assert _ledgers() == before
    assert not db.fetch_all("SELECT * FROM settings WHERE key=?", (access.C2_ANCHOR_KEY,))
    assert not db.fetch_all("SELECT * FROM cases")


def test_release_store_failure_preserves_debit_until_verified_recovery(judge, monkeypatch) -> None:
    _provider(monkeypatch)
    save = access._save_c2

    def fail_release(connection, state) -> None:
        if db.fetch_one("SELECT 1 FROM case_results"):
            raise OSError("offline release store failure")
        save(connection, state)

    monkeypatch.setattr(access, "_save_c2", fail_release)
    with pytest.raises(access.JudgeDenied):
        process_judge_case(_input(), grant=judge, session="session-a", nonce=NONCE)
    monkeypatch.setattr(access, "_save_c2", save)
    c1, _ = _ledgers()
    assert c1["total"] == 1 and len(c1["active"]) == 1
    case_id = next(iter(c1["active"]))
    assert load_result(case_id).status is CaseStatus.PREVIEW_READY
    assert access.recover_reservations(SECRET) == {case_id: "RECOVERED"}
    assert _ledgers()[0]["total"] == 1
    assert len(_ledgers()[1]["requests"]) == 1
