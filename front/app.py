import streamlit as st

from core.auth import init_state
from core.styles import apply_global_styles
from pages.login_page import render_login_page
from pages.dashboard_page import render_dashboard_page
from pages.session_detail_page import render_session_detail_page
from pages.about_page import render_about_page


def sidebar():
    st.sidebar.title("Navigation")

    if st.session_state.access_token:
        if st.sidebar.button("Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

        if st.sidebar.button("About", use_container_width=True):
            st.session_state.page = "about"
            st.rerun()
    else:
        st.sidebar.write("Please login first.")


def main():
    st.set_page_config(
        page_title="AI Resume Analyzer",
        page_icon="📄",
        layout="wide",
    )

    init_state()
    apply_global_styles()
    sidebar()

    if not st.session_state.access_token:
        render_login_page()
        return

    if st.session_state.page == "dashboard":
        render_dashboard_page()
    elif st.session_state.page == "session_detail":
        render_session_detail_page()
    elif st.session_state.page == "about":
        render_about_page()
    else:
        render_dashboard_page()


if __name__ == "__main__":
    main()