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

def render_status_badge(status: str):
    status = (status or "").lower()

    badge_map = {
        "queued": ("📥 Queued", "#3b82f6"),
        "processing": ("⏳ Processing", "#f59e0b"),
        "completed": ("✅ Completed", "#22c55e"),
        "failed": ("❌ Failed", "#ef4444"),
        "stopped": ("⏹ Stopped", "#6b7280"),
    }

    label, color = badge_map.get(status, (f"ℹ️ {status}", "#9ca3af"))

    st.markdown(
        f"""
        <div style="
            display:inline-block;
            padding:6px 12px;
            border-radius:999px;
            border:1px solid {color};
            background:{color}22;
            color:white;
            font-weight:600;
            font-size:14px;
        ">
            {label}
        </div>
        """,
        unsafe_allow_html=True,
    )