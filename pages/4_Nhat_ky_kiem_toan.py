from __future__ import annotations

from datetime import date

import streamlit as st

from core.explain import explain_plainly
from infra.audit import ACTIONS, AuditEvent, recent_events
from infra.db import to_local
from streamlit_app import render_global_controls

EARLIEST_FILTER_DATE = date(2000, 1, 1)


def _matches(
    event: AuditEvent,
    case_id: str,
    actor: str,
    action: str,
    start_date: date,
    end_date: date,
) -> bool:
    return (
        (not case_id or event.case_id == case_id)
        and (not actor or actor.casefold() in event.actor.casefold())
        and (action == "Tất cả" or event.action == action)
        and start_date <= date.fromisoformat(event.ts[:10]) <= end_date
    )


def _details(event: AuditEvent) -> dict[str, object]:
    return {
        "Làm gì": event.action,
        "Lúc nào": to_local(event.ts),
        "Trên dữ liệu nào": {"input_ref": event.input_ref, "sources": event.sources or []},
        "Vì sao": event.reason or "Không có lý do được ghi.",
        "Theo luật nào": event.rule_id or "Không áp dụng",
        "Phiên bản corpus": event.corpus_version or "Không áp dụng",
        "Actor": event.actor,
        "output_ref": event.output_ref,
    }


st.set_page_config(page_title="Nhật ký kiểm toán", page_icon="📋", layout="wide")
render_global_controls()
st.title("Nhật ký kiểm toán")

query_case_id = st.query_params.get("case_id", "")
case_id = st.text_input("Case ID", value=query_case_id, placeholder="Ví dụ: c_01")
actor = st.text_input("Actor", placeholder="SYSTEM, HUMAN: hoặc ADMIN:")
action = st.selectbox("Hành động", ("Tất cả", *sorted(ACTIONS)))
start_column, end_column = st.columns(2)
start_value = start_column.date_input("Từ ngày", value=EARLIEST_FILTER_DATE)
end_value = end_column.date_input("Đến ngày", value=date.today())

if not isinstance(start_value, date) or not isinstance(end_value, date):
    st.error("Bộ lọc ngày phải chọn đúng một ngày bắt đầu và một ngày kết thúc.")
    st.stop()

start_date = start_value
end_date = end_value
if start_date > end_date:
    st.error("Khoảng thời gian không hợp lệ: ngày bắt đầu phải không muộn hơn ngày kết thúc.")
    st.stop()

events = [
    event
    for event in recent_events(limit=None)
    if _matches(event, case_id.strip(), actor.strip(), action, start_date, end_date)
]

if not events:
    st.info("Chưa có event phù hợp. Hãy nới bộ lọc hoặc xử lý một email để tạo nhật ký.")
else:
    st.caption(f"Hiển thị {len(events)} event mới nhất theo thời gian giảm dần.")
    st.dataframe(
        [
            {
                "Lúc nào (+07:00)": to_local(event.ts),
                "Hành động": event.action,
                "Case": event.case_id or "—",
                "Actor": event.actor,
                "Lý do": event.reason or "—",
            }
            for event in events
        ],
        use_container_width=True,
        hide_index=True,
    )
    for event in events:
        label = f"{event.action} · {to_local(event.ts)} · {event.case_id or 'Không có case'}"
        with st.expander(label):
            st.json(_details(event))
            if event.case_id and st.button(
                "Giải thích cho người không chuyên", key=f"explain_{event.event_id}"
            ):
                try:
                    explanation = explain_plainly(event.case_id)
                except ValueError:
                    st.error("Chưa thể tạo giải thích cho case này. Hãy kiểm tra lại dữ liệu case.")
                else:
                    with st.container(border=True):
                        st.subheader("Vì sao hệ thống xử lý như vậy?")
                        st.write(explanation)
