import time
import streamlit as st

from core.api import get_session_detail
from components.error_card import render_error_card
from components.status_badge import render_status_badge


def render_session_detail_page():
    session_id = st.session_state.selected_session_id
    if not session_id:
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown('<div class="app-title">Session Detail</div>', unsafe_allow_html=True)

    top1, top2 = st.columns([1, 5])
    with top1:
        if st.button("Back", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    try:
        detail = get_session_detail(st.session_state.access_token, session_id)
    except Exception as e:
        st.error(str(e))
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"## {detail['filename']}")
    render_status_badge(detail["status"])
    st.write(f"**Iteration:** {detail['current_iteration']}")
    st.write(f"**Created at:** {detail['created_at']}")
    st.write(f"**Updated at:** {detail['updated_at']}")
    st.markdown('</div>', unsafe_allow_html=True)

    result = detail.get("result", {})
    errors = result.get("errors", [])
    final_message = result.get("final_message", "")

    if detail["status"] in ("queued", "processing"):
        st.info("Resume is being processed...")
        time.sleep(3)
        st.rerun()
        return

    if detail["status"] == "failed":
        st.error("Processing failed.")
        return

    if final_message:
        st.markdown(
            f'<div class="success-box"><strong>{final_message}</strong></div>',
            unsafe_allow_html=True,
        )

    st.markdown("## Improvements")
    if not errors:
        st.info("No errors returned.")
        return

    for index, item in enumerate(errors, start=1):
        render_error_card(index, item)