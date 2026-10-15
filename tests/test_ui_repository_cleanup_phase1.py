"""Regression UI cho cleanup Phase 1; chỉ dùng SQLite tạm và fixture mô phỏng."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.pipeline import process_case
from infra import audit, db
from test_runtime_worker import _email, runtime as _runtime

runtime = _runtime
ROOT = Path(__file__).resolve().parents[1]


def _markdown(app: AppTest) -> str:
    return "\n".join(item.value for item in app.markdown)


def test_audit_html_escapes_email_and_event_content(runtime) -> None:
    result = process_case(_email())
    payload = '<img src=x onerror="alert(1)">'
    db.execute(
        "UPDATE cases SET sender = ?, subject = ? WHERE case_id = ?",
        (payload, payload, result.case_id),
    )
    audit.log_event(
        case_id=result.case_id,
        actor="SYSTEM",
        action="CASE_ERROR",
        reason=payload,
        sources=[payload],
    )

    app = AppTest.from_file(str(ROOT / "pages/4_Nhat_ky_kiem_toan.py"))
    app.query_params["case_id"] = result.case_id
    app.run(timeout=20)

    assert not app.exception
    rendered = _markdown(app)
    assert payload not in rendered
    assert "&lt;img src=x onerror=&quot;" in rendered


def test_fixture_results_are_prominently_marked_as_synthetic(runtime) -> None:
    for page in ("5_Verify.py", "6_Do_luong.py"):
        app = AppTest.from_file(str(ROOT / "pages" / page))
        app.query_params["fixture"] = "all_pass"
        app.run(timeout=20)
        assert not app.exception
        assert any("DỮ LIỆU MÔ PHỎNG" in item.value for item in app.warning)


def test_metrics_describes_p04_as_guard_failure(runtime) -> None:
    result = process_case(_email())
    db.execute(
        "UPDATE decisions SET rule_id = 'P04' WHERE case_id = ?",
        (result.case_id,),
    )

    app = AppTest.from_file(str(ROOT / "pages/6_Do_luong.py")).run(timeout=20)
    assert not app.exception
    rendered = _markdown(app)
    assert "P04" in rendered
    assert "Kiểm tra an toàn hoặc căn cứ không đạt" in rendered
