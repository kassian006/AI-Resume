import streamlit as st


def render_about_page():
    st.markdown('<div class="app-title">About</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
            <p>This Streamlit app is a frontend for your AI Resume Analyzer backend.</p>
            <ul>
                <li>Login / Register</li>
                <li>Upload PDF resume</li>
                <li>Track session status</li>
                <li>View AI suggestions and final message</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )