"""Lịch sử email và quyết định, trình bày theo công việc."""

from __future__ import annotations

import json
from dataclasses import asdict
from urllib.parse import quote

import streamlit as st

from core.controls import override_decision
from core.types import Decision
from core.pipeline import load_result
from core.worker import retry_case
from corpus.api import get_chunk
from infra.audit import events_for_case, recent_events
from infra.db import fetch_all, fetch_one
from ui.presentation import ACTION_LABELS, actor_label, local_time, readable_text, status_label

st.title("Lịch sử xử lý")
cases = fetch_all("SELECT * FROM cases ORDER BY rowid DESC LIMIT 200")
labels = {
    row[
        "case_id"
    ]: f"{row['subject']} · {status_label(row['status'])} · {local_time(row['received_at'])}"
    for row in cases
}
query_id = st.query_params.get("case_id")
if isinstance(query_id, str) and query_id and query_id not in labels:
    older = fetch_one("SELECT * FROM cases WHERE case_id = ?", (query_id,))
    if older is not None:
        cases.append(older)
        labels[query_id] = (
            f"{older['subject']} · {status_label(older['status'])} · {local_time(older['received_at'])}"
        )
options = ["", *labels]
selected = st.selectbox(
    "Chọn email để xem lịch sử",
    options,
    index=options.index(query_id) if query_id in options else 0,
    format_func=lambda value: labels.get(value, "Hoạt động gần đây"),
)
if selected:
    events = events_for_case(selected)
    case = next(row for row in cases if row["case_id"] == selected)
    st.caption(f"Từ {case['sender']} · {local_time(case['received_at'])}")
    st.text(case["body_raw"])
    st.link_button("Mở nội dung phản hồi", f"/?case_id={quote(selected)}")
    with st.expander("Can thiệp của người quản trị"):
        st.caption(
            "Mọi thay đổi đều lưu lý do. Email đã gửi không thể bị thu hồi hoặc gửi lại bằng thao tác này."
        )
        reason = st.text_area("Lý do điều chỉnh")
        choice = st.selectbox(
            "Cách xử lý mới",
            [Decision.ESCALATE, Decision.AUTO_REPLY],
            format_func=lambda value: (
                "Chuyển chuyên viên"
                if value is Decision.ESCALATE
                else "Đưa phản hồi đã kiểm tra sang chờ duyệt gửi"
            ),
        )
        if st.button("Ghi nhận điều chỉnh", disabled=not reason.strip()):
            try:
                override_decision(selected, choice, "ADMIN:local", reason)
            except ValueError as error:
                st.error(readable_text(str(error)))
            else:
                st.success("Đã lưu điều chỉnh. Nội dung chưa được gửi ra ngoài.")
                st.rerun()
        if case["status"] in ("ERROR", "NEEDS_RECHECK", "CANCELLED"):
            if st.button("Xử lý lại bằng quy định hiện tại"):
                try:
                    new_id = retry_case(selected, actor="ADMIN:local")
                except ValueError as error:
                    st.error(readable_text(str(error)))
                else:
                    st.success("Đã lưu một lần xử lý mới; lịch sử cũ được giữ nguyên.")
                    st.link_button("Mở lần xử lý mới", f"/?case_id={quote(new_id)}")
else:
    events = recent_events(limit=200)
if not events:
    st.info("Chưa có hoạt động được ghi nhận.")
else:
    st.caption(f"{len(events)} hoạt động · Thời gian Việt Nam")
    for event in events:
        action = ACTION_LABELS.get(event.action, "Cập nhật công việc")
        with st.expander(f"{local_time(event.ts)} · {actor_label(event.actor)} · {action}"):
            st.write(readable_text(event.reason) if event.reason else action)
            if event.case_id and event.case_id in labels:
                st.caption(labels[event.case_id])
            result = load_result(event.case_id) if event.case_id and event.sources else None
            snapshots = (
                {item.chunk_id: item for item in result.evidence.chunks}
                if result and result.evidence
                else {}
            )
            for source in event.sources or []:
                chunk = snapshots.get(source) or get_chunk(source)
                if chunk:
                    st.write(chunk.breadcrumb)
                    st.write(chunk.text)
                else:
                    st.caption(
                        "Căn cứ gốc được ghi trong dữ liệu kiểm tra; có thể đã được thay thế."
                    )
    st.download_button(
        "Tải dữ liệu kiểm tra đầy đủ",
        json.dumps([asdict(event) for event in events], ensure_ascii=False, indent=2),
        file_name="lich-su-xu-ly.json",
        mime="application/json",
    )
