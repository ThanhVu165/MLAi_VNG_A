"""Ledger ngân sách DEV; không gọi provider hoặc tự tạo baseline được xác nhận."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

DEFAULT_LEDGER_PATH = Path("reports/sprints/M2_live_budget.json")
TOTAL_BUDGET = 45
STATUSES = {"ATTEMPTED", "SEMANTIC_RESULT", "TECHNICAL_FAILURE"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class BudgetVerificationError(Exception):
    """Baseline/ledger không đủ để cấp phép LIVE."""


class BudgetExceededError(Exception):
    """Không còn quota cho observation độc lập."""


@dataclass(frozen=True)
class LiveBudgetInfo:
    total_budget: int | None
    used_observations: int | None
    remaining_budget: int | None
    is_verified: bool
    source_file: str


def _require(condition: bool) -> None:
    if not condition:
        raise BudgetVerificationError("BUDGET_UNVERIFIED: ledger không hợp lệ hoặc chưa xác nhận.")


def _timestamp(value: object) -> None:
    _require(isinstance(value, str))
    try:
        _require(datetime.fromisoformat(value).utcoffset() is not None)
    except ValueError:
        raise BudgetVerificationError("BUDGET_UNVERIFIED: timestamp không hợp lệ.") from None


def _integer(value: object, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def validate_ledger(data: object, source: Path) -> LiveBudgetInfo:
    """Một baseline/current duy nhất; consumed = baseline + mọi attempted IDs."""
    _require(
        isinstance(data, dict)
        and set(data) == {"schema_version", "baseline", "attempts", "current"}
    )
    _require(type(data["schema_version"]) is int and data["schema_version"] == 1)
    baseline, attempts, current = data["baseline"], data["attempts"], data["current"]
    _require(
        isinstance(baseline, dict)
        and set(baseline)
        == {"total", "consumed", "confirmed_by", "confirmed_at", "reconciliation_reference"}
    )
    _require(type(baseline["total"]) is int and baseline["total"] == TOTAL_BUDGET)
    _require(_integer(baseline["consumed"]) and baseline["consumed"] <= TOTAL_BUDGET)
    for name in ("confirmed_by", "reconciliation_reference"):
        _require(isinstance(baseline[name], str) and bool(baseline[name].strip()))
    _timestamp(baseline["confirmed_at"])
    _require(isinstance(attempts, list))
    seen = set()
    for event in attempts:
        _require(
            isinstance(event, dict)
            and set(event)
            == {"observation_id", "case_id", "started_at", "status", "internal_retries"}
        )
        for name in ("observation_id", "case_id"):
            _require(isinstance(event[name], str) and bool(SAFE_ID.fullmatch(event[name])))
        _require(event["observation_id"] not in seen)
        seen.add(event["observation_id"])
        _require(isinstance(event["status"], str) and event["status"] in STATUSES)
        _require(_integer(event["internal_retries"]))
        _timestamp(event["started_at"])
    consumed = baseline["consumed"] + len(attempts)
    _require(consumed <= TOTAL_BUDGET)
    expected = {"total": TOTAL_BUDGET, "consumed": consumed, "remaining": TOTAL_BUDGET - consumed}
    _require(isinstance(current, dict) and set(current) == set(expected))
    _require(all(type(current[k]) is int and current[k] == v for k, v in expected.items()))
    return LiveBudgetInfo(TOTAL_BUDGET, consumed, TOTAL_BUDGET - consumed, True, str(source))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    data = {}
    for key, value in pairs:
        _require(key not in data)
        data[key] = value
    return data


def _load_ledger(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, ValueError):
        raise BudgetVerificationError(
            "BUDGET_UNVERIFIED: ledger thiếu hoặc không đọc được."
        ) from None
    validate_ledger(data, path)
    return data


def verify_live_budget(ledger_path: Path = DEFAULT_LEDGER_PATH) -> LiveBudgetInfo:
    return validate_ledger(_load_ledger(ledger_path), ledger_path)


def check_budget_authorization(
    requested_count: int,
    *,
    is_live: bool = False,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
) -> LiveBudgetInfo:
    """Mock không cấp phép LIVE; thiếu ledger vẫn báo unverified, không suy ra zero."""
    _require(_integer(requested_count))
    try:
        info = verify_live_budget(ledger_path)
    except BudgetVerificationError:
        if is_live:
            raise
        return LiveBudgetInfo(None, None, None, False, str(ledger_path))
    if is_live and requested_count > info.remaining_budget:
        raise BudgetExceededError("BUDGET_EXCEEDED")
    return info


def _account(
    data: dict[str, object], observation_id: str, case_id: str, status: str, internal_retries: int
) -> dict[str, object]:
    _require(isinstance(status, str) and status in STATUSES and _integer(internal_retries))
    updated = deepcopy(data)
    events = updated["attempts"]
    found = next((e for e in events if e["observation_id"] == observation_id), None)
    if status == "ATTEMPTED":
        _require(found is None and internal_retries == 0)
        if updated["current"]["remaining"] == 0:
            raise BudgetExceededError("BUDGET_EXCEEDED")
        events.append(
            {
                "observation_id": observation_id,
                "case_id": case_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "internal_retries": 0,
            }
        )
        updated["current"]["consumed"] += 1
        updated["current"]["remaining"] -= 1
    else:
        _require(
            found is not None and found["case_id"] == case_id and found["status"] == "ATTEMPTED"
        )
        found.update(status=status, internal_retries=internal_retries)
    return updated


def record_live_observation(
    ledger_path: Path,
    *,
    observation_id: str,
    case_id: str,
    status: str = "ATTEMPTED",
    internal_retries: int = 0,
) -> LiveBudgetInfo:
    """Future boundary: persist ATTEMPTED trước gọi, finalize sau; không gọi pipeline."""
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    try:
        lock = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except OSError:
        raise BudgetVerificationError(
            "BUDGET_UNVERIFIED: ledger đang khóa hoặc không ghi được."
        ) from None
    temporary = None
    try:
        data = _account(
            _load_ledger(ledger_path), observation_id, case_id, status, internal_retries
        )
        info = validate_ledger(data, ledger_path)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=ledger_path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, ledger_path)
        return info
    finally:
        os.close(lock)
        lock_path.unlink()
        if temporary is not None and temporary.exists():
            temporary.unlink()
