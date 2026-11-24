import os
import requests
import streamlit as st

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
REPO_URL = "https://github.com/amand1ko7aas-dotcom/applied-is-project-2026"

st.set_page_config(page_title="АРМ Хатшы — Кафедра құжат айналымы", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #F8F6F2; color: #2B2623; }
    .lab-card {
        background-color: #FFFFFF;
        border: 1px solid #E5DEC9;
        border-left: 4px solid #B89348;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("АРМ Хатшы — Кафедра құжат айналымы")
st.caption("Кафедра хатшысының автоматтандырылған жұмыс орны • FastAPI + SQLModel + Streamlit")

with st.sidebar:
    st.header("Кафедра ақпараты")
    st.write("**Ақпараттық жүйелер және ИТ кафедрасы**")
    st.write("Әкімші: **Амандық Сабина** (ИС-24-А1)")
    st.caption(f"API сервері: {BASE_URL}")
    st.markdown(f"[Swagger API Docs]({BASE_URL}/docs)")
    st.markdown(f"[GitHub Репозиторий]({REPO_URL})")

tab_docs, tab_add_doc, tab_tasks, tab_emp, tab_labs = st.tabs(
    [
        "Құжаттар тізілімі",
        "Жаңа құжат тіркеу",
        "Тапсырмалар (Бақылау)",
        "Қызметкерлер",
        "ЛР №1–8 (Зертханалық жұмыстар)",
    ]
)

with tab_docs:
    col1, col2, col3 = st.columns([2, 1, 1])
    search_q = col1.text_input("Құжат нөмірі немесе тақырыбы бойынша іздеу", placeholder="Мысалы: 14-08 немесе тәжірибе")
    type_filter = col2.selectbox("Құжат түрі", ["Барлығы", "Бұйрық", "Өкім", "Қызметтік жазба", "Хат", "Есеп"])
    status_filter = col3.selectbox("Мәртебесі", ["Барлығы", "Орындалуда", "Бекітілді", "Мұрағатталған"])

    params = {}
    if search_q.strip():
        params["search"] = search_q.strip()
    if type_filter != "Барлығы":
        params["doc_type"] = type_filter
    if status_filter != "Барлығы":
        params["doc_status"] = status_filter

    try:
        resp = requests.get(f"{BASE_URL}/documents", params=params, timeout=5)
        resp.raise_for_status()
        docs = resp.json()
        if docs:
            st.dataframe(docs, use_container_width=True)

            with st.expander("Құжат мәртебесін өзгерту немесе жою"):
                doc_map = {f"[{d['id']}] {d['doc_number']} — {d['topic']} ({d['status']})": d["id"] for d in docs}
                sel_doc = st.selectbox("Құжатты таңдаңыз", list(doc_map.keys()))
                c_upd, c_del = st.columns(2)
                new_status = c_upd.selectbox("Жаңа мәртебе", ["Орындалуда", "Бекітілді", "Мұрағатталған"])
                if c_upd.button("Мәртебені жаңарту"):
                    r = requests.patch(f"{BASE_URL}/documents/{doc_map[sel_doc]}", json={"status": new_status}, timeout=5)
                    if r.status_code == 200:
                        st.success("Құжат мәртебесі жаңартылды!")
                        st.rerun()
                if c_del.button("Құжатты жою"):
                    r = requests.delete(f"{BASE_URL}/documents/{doc_map[sel_doc]}", timeout=5)
                    if r.status_code == 200:
                        st.success("Құжат тізілімнен жойылды!")
                        st.rerun()
        else:
            st.info("Сұраныс бойынша құжаттар табылмады.")
    except requests.RequestException as exc:
        st.error(f"FastAPI серверіне қосылу қатесі: {exc}")

with tab_add_doc:
    with st.form("add_doc_form"):
        doc_number = st.text_input("Құжат нөмірі", placeholder="№ 14-08/130")
        doc_type = st.selectbox("Құжат түрі", ["Бұйрық", "Өкім", "Қызметтік жазба", "Хат", "Есеп"])
        reg_date = st.date_input("Тіркелген күні")
        topic = st.text_input("Құжат тақырыбы")
        doc_status = st.selectbox("Мұрағат мәртебесі", ["Орындалуда", "Бекітілді", "Мұрағатталған"])
        submitted = st.form_submit_button("Құжатты тіркеу")

        if submitted:
            if not doc_number.strip() or not topic.strip():
                st.warning("Құжат нөмірі мен тақырыбын толтырыңыз.")
            else:
                res = requests.post(
                    f"{BASE_URL}/documents",
                    json={
                        "doc_number": doc_number.strip(),
                        "doc_type": doc_type,
                        "reg_date": str(reg_date),
                        "topic": topic.strip(),
                        "status": doc_status,
                    },
                    timeout=5,
                )
                if res.status_code == 201:
                    st.success("Жаңа құжат сәтті тіркелді!")
                    st.rerun()
                else:
                    st.error(f"Қате: {res.text}")

with tab_tasks:
    try:
        docs_list = requests.get(f"{BASE_URL}/documents", timeout=5).json()
        emps_list = requests.get(f"{BASE_URL}/employees", timeout=5).json()
    except requests.RequestException:
        docs_list, emps_list = [], []

    if docs_list and emps_list:
        with st.form("add_task_form"):
            doc_opts = {f"[{d['id']}] {d['doc_number']} — {d['topic']}": d["id"] for d in docs_list}
            emp_opts = {f"[{e['id']}] {e['full_name']} ({e['position']})": e["id"] for e in emps_list}
            sel_d = st.selectbox("Негіздеме құжат", list(doc_opts.keys()))
            sel_e = st.selectbox("Орындаушы қызметкер", list(emp_opts.keys()))
            task_text = st.text_input("Тапсырма мәні")
            deadline = st.date_input("Орындау мерзімі")
            t_status = st.selectbox("Мәртебесі", ["Орындалуда", "Аяқталды", "Мерзімі өткен"])
            t_sub = st.form_submit_button("Тапсырма тағайындау")

            if t_sub and task_text.strip():
                r = requests.post(
                    f"{BASE_URL}/tasks",
                    json={
                        "document_id": doc_opts[sel_d],
                        "executor_id": emp_opts[sel_e],
                        "task_text": task_text.strip(),
                        "deadline": str(deadline),
                        "status": t_status,
                    },
                    timeout=5,
                )
                if r.status_code == 201:
                    st.success("Тапсырма тағайындалды!")
                    st.rerun()

    st.subheader("Кафедра тапсырмалары")
    try:
        tasks = requests.get(f"{BASE_URL}/tasks", timeout=5).json()
        if tasks:
            st.dataframe(tasks, use_container_width=True)
    except requests.RequestException:
        pass

with tab_emp:
    try:
        emps = requests.get(f"{BASE_URL}/employees", timeout=5).json()
        if emps:
            st.dataframe(emps, use_container_width=True)
    except requests.RequestException as exc:
        st.error(f"Қате: {exc}")

with tab_labs:
    st.subheader("Зертханалық жұмыстар №1–8 — Жүйеде іске асырылуы")
    st.caption("Жоба: «АРМ Хатшы — Кафедра құжат айналымы» • Автор: Амандық Сабина (ИС-24-А1)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pytest автотесттері", "12 / 12 PASSED", "1.78s")
    m2.metric("Bandit (Medium/High)", "0 қауіп", "462 жол код")
    m3.metric("Locust орташа жауабы", "~13.6 мс", "0% қате (10 юзер)")
    m4.metric("GitHub Actions CI/CD", "PASSED", "Коммит 65257e6")

    labs_data = [
        (
            "ЛР №1 — Пәндік аймақ, талаптар және репозиторий",
            "Орындалды",
            "Кафедра хатшысының құжат айналымы («Бұйрық», «Өкім», «Қызметтік жазба») мен тапсырмаларды бақылау талаптары сипатталды. Жоба GitHub-тағы `applied-is-project-2026` репозиторийіне жүктелді.",
            "git status && git log -1",
        ),
        (
            "ЛР №2 — Деректер қорының моделі және бастапқы толтыру",
            "Орындалды",
            "SQLModel арқылы `Kafedra`, `Employee`, `Document`, `Task`, `UserAccount` кестелері және байланыстары жасалды (`app/database/models.py`, `seed.py`). Сонымен қатар `arm_hatshy/` қалтасында Flask + MS Access (`ARM_Secretary.accdb`) нұсқасы сақталған.",
            "python -m app.database.seed",
        ),
        (
            "ЛР №3–4 — REST API сервері және OpenAPI / Swagger құжаттамасы",
            "Орындалды",
            "FastAPI базасында `/documents`, `/tasks`, `/kafedra`, `/employees`, `/auth/login`, `/admin/users` эндпоинттері мен CRUD логикасы іске асырылды. Интерактивті құжаттама `/docs` бетінде қолжетімді.",
            "uvicorn app.main:app --reload",
        ),
        (
            "ЛР №5 — Пайдаланушы веб-интерфейсі (Streamlit)",
            "Орындалды",
            "Құжаттарды іздеу/сүзу, тіркеу, мәртебесін өзгерту/жою, тапсырмаларды бақылау және қызметкерлер тізімін көрсету вкладкаларымен веб-интерфейс әзірленді (`app/frontend/ui.py`).",
            "streamlit run app/frontend/ui.py",
        ),
        (
            "ЛР №6–7 — Контейнерлеу және көпқабатты архитектура",
            "Орындалды",
            "Бэкенд пен фронтендке арналған `Dockerfile`, `Dockerfile.frontend` және `docker-compose.yml` конфигурациялары дайындалды.",
            "docker-compose up --build",
        ),
        (
            "ЛР №8 — Тестілеу, қауіпсіздік, жүктеме және CI/CD",
            "Орындалды",
            "`pytest -v` арқылы 12 тест өтті, `bandit -r app -ll` Medium/High қауіп тапқан жоқ, `locust` жүктеме тесті 0% қатемен өтті, ал `.github/workflows/test.yml` GitHub Actions-та сәтті іске қосылды.",
            "pytest -v && bandit -r app -ll",
        ),
    ]

    for title, badge, desc, cmd in labs_data:
        st.markdown(
            f"""
            <div class="lab-card">
                <strong>{title}</strong> — <span>{badge}</span><br/>
                <p style="margin:6px 0 8px 0;">{desc}</p>
                <code>{cmd}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
