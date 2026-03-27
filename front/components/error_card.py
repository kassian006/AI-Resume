import streamlit as st


def render_error_card(index: int, item: dict):
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### Issue #{index}")
        st.markdown(f"**Original:** {item.get('original', '—')}")
        st.markdown(f"**Improved:** {item.get('improved', '—')}")
        st.markdown(f"**Advice:** {item.get('advice', '—')}")
        st.markdown("</div>", unsafe_allow_html=True)