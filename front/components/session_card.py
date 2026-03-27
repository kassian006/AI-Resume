import streamlit as st
from components.status_badge import render_status_badge


def render_session_card(session: dict):
    col1, col2, col3 = st.columns([5, 2, 1])

    with col1:
        st.markdown(f"**{session['filename']}**")
        st.caption(session["created_at"])

    with col2:
        render_status_badge(session["status"])

    with col3:
        opened = st.button("Open", key=f"open_{session['session_id']}", use_container_width=True)

    return opened