from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

import streamlit as st

from infra.telemetry import snapshot


class MetricColumn(Protocol):
    def metric(self, label: str, value: str) -> object: ...

    def caption(self, body: str) -> object: ...


def _percent(value: object) -> str:
    return f"{value:.1%}" if isinstance(value, (int, float)) else "Chưa có dữ liệu"


def _milliseconds(value: object) -> str:
    return f"{value} ms" if isinstance(value, (int, float)) else "Chưa có dữ liệu"


def _latency_summary(metrics: dict[str, object]) -> str:
    p50 = metrics["p50_latency_ms"]
    p95 = metrics["p95_latency_ms"]
    if not isinstance(p50, Mapping) or not isinstance(p95, Mapping) or not p50:
        return "Chưa có dữ liệu"
    return " · ".join(
        f"{step}: p50 {_milliseconds(value)}, p95 {_milliseconds(p95.get(step))}"
        for step, value in p50.items()
    )


def _escalation_summary(value: object) -> str:
    if not isinstance(value, Mapping):
        return "Chưa có dữ liệu"
    return " · ".join(f"{kind}: {_percent(rate)}" for kind, rate in value.items())


def _seconds(value: object) -> str:
    return f"{value} giây" if isinstance(value, (int, float)) else "Chưa có dữ liệu"


def _card(column: MetricColumn, label: str, value: str, formula: str) -> None:
    column.metric(label, value)
    column.caption(formula)


st.set_page_config(page_title="Đo lường", page_icon="📈", layout="wide")
st.title("Đo lường")
st.info("Dữ liệu hiện tại là từ chạy nội bộ, chưa phải dữ liệu người dùng thật.")

metrics = snapshot()
efficiency = st.columns(3)
st.header("Chỉ số hiệu quả")
_card(
    efficiency[0],
    "Tỷ lệ trả lời tự động",
    _percent(metrics["auto_rate"]),
    "AUTO_REPLY / (AUTO_REPLY + ESCALATE)",
)
_card(
    efficiency[1],
    "Tỷ lệ escalation theo loại",
    _escalation_summary(metrics["escalation_rate_by_type"]),
    "ESCALATE theo từng loại / (AUTO_REPLY + ESCALATE)",
)
_card(
    efficiency[2],
    "Độ trễ p50 / p95",
    _latency_summary(metrics),
    "Phân vị 50% và 95% thời gian chạy của từng bước R1–R13",
)

efficiency = st.columns(2)
_card(
    efficiency[0],
    "Thời gian duyệt trung vị",
    _seconds(metrics["median_review_seconds"]),
    "Trung vị của decided_at − shown_at",
)
_card(
    efficiency[1],
    "Bỏ sót / escalation thừa",
    f"{_percent(metrics['missed_escalation_rate'])} / {_percent(metrics['over_escalation_rate'])}",
    "Sai lệch dự đoán so với expected của Run All 15",
)

st.header("Chỉ số rủi ro")
risk = st.columns(3)
_card(
    risk[0],
    "Duyệt dưới 5 giây",
    _percent(metrics["pct_approved_under_5s"]),
    "Số quyết định chấp thuận dưới 5 giây / tổng quyết định chấp thuận",
)
_card(
    risk[1],
    "Tỷ lệ ghi đè",
    _percent(metrics["override_rate"]),
    "Số quyết định bị ghi đè / tổng quyết định",
)
_card(
    risk[2],
    "Groundedness thất bại",
    _percent(metrics["groundedness_fail_rate"]),
    "Số R8a fail / số bản nháp trả lời tự động",
)
