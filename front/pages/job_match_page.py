import streamlit as st

from core.api import match_jobs_from_resume


def render_job_match_page():
    st.markdown('<div class="app-title">Подбор вакансий</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">Загрузите резюме, и система подберет подходящие вакансии.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Выберите PDF резюме", type=["pdf"], key="job_match_pdf")

    if st.button("Подобрать вакансии", use_container_width=True):
        if not uploaded_file:
            st.warning("Сначала выберите PDF файл.")
        else:
            try:
                result = match_jobs_from_resume(uploaded_file)
                st.session_state.job_match_result = result
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.markdown("</div>", unsafe_allow_html=True)

    result = st.session_state.get("job_match_result")
    if not result:
        return

    skills_found = result.get("skills_found", [])
    jobs = result.get("jobs", [])

    st.markdown("## Найденные навыки")
    if skills_found:
        st.write(", ".join(skills_found))
    else:
        st.info("Навыки не найдены.")

    st.markdown("## Подходящие вакансии")
    if not jobs:
        st.info("Подходящие вакансии не найдены.")
        return

    for job in jobs:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### {job.get('job_title', 'Без названия')}")
        st.write(f"**Компания:** {job.get('company', 'Не указана')}")
        st.write(f"**Зарплата:** {job.get('salary', 'Не указана')}")
        st.write(f"**Локация:** {job.get('location', 'Не указана')}")
        st.write(f"**Источник:** {job.get('source', 'Не указан')}")
        st.write(f"**Match score:** {job.get('match_score', 0)}")

        why_match = job.get("why_match", [])
        if why_match:
            st.write(f"**Почему подходит:** {', '.join(why_match)}")

        url = job.get("url")
        if url:
            st.markdown(f"[Открыть вакансию]({url})")

        st.markdown("</div>", unsafe_allow_html=True)