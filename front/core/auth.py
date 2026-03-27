import streamlit as st


def init_state():
    defaults = {
        "access_token": None,
        "refresh_token": None,
        "user_email": None,
        "page": "login",
        "selected_session_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_auth(access_token: str, refresh_token: str, user_email: str):
    st.session_state.access_token = access_token
    st.session_state.refresh_token = refresh_token
    st.session_state.user_email = user_email


def logout():
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None
    st.session_state.selected_session_id = None
    st.session_state.page = "login"