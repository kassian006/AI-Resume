import streamlit as st

from core.api import get_sessions, upload_resume
from core.auth import logout
from components.session_card import render_session_card


def render_dashboard_page():
    st.markdown('<div class="app-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="app-subtitle">Logged in as {st.session_state.user_email}</div>',
        unsafe_allow_html=True,
    )

    top1, top2 = st.columns([5, 1])
    with top2:
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Resume")
    uploaded_file = st.file_uploader("Choose PDF file", type=["pdf"])

    if st.button("Upload Resume", use_container_width=True):
        if not uploaded_file:
            st.warning("Choose a PDF file first.")
        else:
            try:
                result = upload_resume(st.session_state.access_token, uploaded_file)
                st.success(result["message"])
                st.session_state.selected_session_id = result["session_id"]
                st.session_state.page = "session_detail"
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("## Your Sessions")

    try:
        sessions = get_sessions(st.session_state.access_token)
    except Exception as e:
        st.error(str(e))
        return

    if not sessions:
        st.info("No sessions yet.")
        return

    for session in sessions:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        opened = render_session_card(session)
        st.markdown('</div>', unsafe_allow_html=True)

        if opened:
            st.session_state.selected_session_id = session["session_id"]
            st.session_state.page = "session_detail"
            st.rerun()