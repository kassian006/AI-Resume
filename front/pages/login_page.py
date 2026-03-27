import streamlit as st

from core.api import login_user, register_user, get_me
from core.auth import set_auth


def render_login_page():
    st.markdown('<div class="app-title">AI Resume Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Login or create account to work with your resume analysis.</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            try:
                data = login_user(email, password)
                me = get_me(data["access_token"])
                set_auth(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    user_email=me["email"],
                )
                st.session_state.page = "dashboard"
                st.rerun()
            except Exception as e:
                st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")

        if st.button("Register", use_container_width=True):
            try:
                register_user(email, password)
                st.success("Registration completed. Now login.")
            except Exception as e:
                st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)