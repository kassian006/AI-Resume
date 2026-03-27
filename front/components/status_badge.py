import streamlit as st


def apply_global_styles():
    st.markdown(
        """
        <style>
        .main {
            background: linear-gradient(180deg, #0b1020 0%, #111827 100%);
            color: white;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1100px;
        }

        .app-title {
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 8px;
            color: #f9fafb;
        }

        .app-subtitle {
            font-size: 16px;
            color: #cbd5e1;
            margin-bottom: 24px;
        }

        .card {
            background: rgba(17, 24, 39, 0.9);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            margin-bottom: 16px;
        }

        .soft-text {
            color: #cbd5e1;
        }

        .success-box {
            background: rgba(34,197,94,0.12);
            border: 1px solid rgba(34,197,94,0.35);
            border-radius: 14px;
            padding: 14px;
            color: #dcfce7;
        }

        .muted-box {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )