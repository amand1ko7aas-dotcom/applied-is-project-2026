import os
import csv
import io
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, Response, session, flash

try:
    import pyodbc
except ImportError:
    pyodbc = None

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "arm_hatshy_secret_key_2026")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ACCDB_PATH = os.path.join(BASE_DIR, "ARM_Secretary.accdb")
SQLITE_PATH = os.path.join(BASE_DIR, "arm_hatshy_demo.db")

TABLES = {
    "kafedra": {
        "db_table": "Кафедры",
        "pk": "Код_Кафедры",
        "title": "Кафедра",
        "icon": "fa-landmark",
        "columns": ["Кафедра атауы", "Меңгеруші", "Кабинет"],
        "fields": ["Название_Кафедры", "Зав_Кафедрой", "Кабинет"],
        "types": ["text", "text", "text"]
    },
    "qyzmetkerler": {
        "db_table": "Сотрудники",
        "pk": "Код_Сотрудника",
        "title": "Қызметкерлер",
        "icon": "fa-user-tie",
        "columns": ["Аты-жөні", "Лауазымы", "Телефон", "Email", "Кафедра"],
        "fields": ["ФИО", "Должность", "Телефон", "Email", "Код_Кафедры"],
        "types": ["text", "text", "text", "email", "fk"],
        "fk": {
            "Код_Кафедры": ("Кафедры", "Код_Кафедры", "Название_Кафедры")
        }
    },
    "quzhattar": {
        "db_table": "Документы",
        "pk": "Код_Документа",
        "title": "Құжаттар",
        "icon": "fa-file-alt",
        "columns": ["Құжат №", "Құжат түрі", "Тіркелген күні", "Тақырыбы", "Мұрағат мәртебесі"],
        "fields": ["Номер_Документа", "Тип_Документа", "Дата_Регистрации", "Тема", "Статус_Архив"],
        "types": ["text", "select", "date", "text", "select"],
        "choices": {
            "Тип_Документа": ["Бұйрық", "Өкім", "Қызметтік жазба", "Хат", "Есеп"],
            "Статус_Архив": ["Орындалуда", "Бекітілді", "Мұрағатталған"]
        }
    },
    "hattamalar": {
        "db_table": "Протоколы",
        "pk": "Код_Протокола",
        "title": "Хаттамалар",
        "icon": "fa-clipboard-list",
        "columns": ["Хаттама №", "Отырыс күні", "Күн тәртібі", "Шешім"],
        "fields": ["Номер_Протокола", "Дата_Заседания", "Повестка_Дня", "Решение"],
        "types": ["text", "date", "text", "text"]
    },
    "tapsyrmalar": {
        "db_table": "Порученичя",
        "pk": "Код_Поручения",
        "title": "Тапсырмалар",
        "icon": "fa-tasks",
        "columns": ["Құжат", "Орындаушы", "Тапсырма мәні", "Орындау мерзімі", "Мәртебесі"],
        "fields": ["Код_Документа", "Код_Исполнителя", "Текст_Поручения", "Срок_Исполнения", "Статус"],
        "types": ["fk", "fk", "text", "date", "select"],
        "fk": {
            "Код_Документа": ("Документы", "Код_Документа", "Номер_Документа"),
            "Код_Исполнителя": ("Сотрудники", "Код_Сотрудника", "ФИО")
        },
        "choices": {
            "Статус": ["Орындалуда", "Аяқталды", "Мерзімі өткен"]
        }
    },
    "pander": {
        "db_table": "Дисциплины",
        "pk": "Код_Дисциплины",
        "title": "Пәндер",
        "icon": "fa-book",
        "columns": ["Пән атауы", "Сағат көлемі", "Оқытушы"],
        "fields": ["Название_Дисциплины", "Объем_Часов", "Код_Преподавателя"],
        "types": ["text", "number", "fk"],
        "fk": {
            "Код_Преподавателя": ("Сотрудники", "Код_Сотрудника", "ФИО")
        }
    },
    "toptar": {
        "db_table": "Группы",
        "pk": "Код_Группы",
        "title": "Топтар",
        "icon": "fa-users",
        "columns": ["Топ атауы", "Курс", "Куратор"],
        "fields": ["Название_Группы", "Курс", "Код_Куратора"],
        "types": ["text", "number", "fk"],
        "fk": {
            "Код_Куратора": ("Сотрудники", "Код_Сотрудника", "ФИО")
        }
    },
    "studentter": {
        "db_table": "Студенты",
        "pk": "Код_Студента",
        "title": "Студенттер",
        "icon": "fa-user-graduate",
        "columns": ["Студенттің аты-жөні", "Телефоны", "Тобы"],
        "fields": ["ФИО_Студента", "Телефон", "Код_Группы"],
        "types": ["text", "text", "fk"],
        "fk": {
            "Код_Группы": ("Группы", "Код_Группы", "Название_Группы")
        }
    },
    "otyrystar": {
        "db_table": "Заседания",
        "pk": "Код_Заседания",
        "title": "Отырыстар",
        "icon": "fa-calendar-alt",
        "columns": ["Талқылау тақырыбы", "Хаттама", "Жауапты", "Отырыс күні", "Аудитория"],
        "fields": ["Тема_Обсуждения", "Код_Протокола", "Код_Ответственного", "Дата_Заседания", "Код_Аудитории"],
        "types": ["text", "fk", "fk", "date", "fk"],
        "fk": {
            "Код_Протокола": ("Протоколы", "Код_Протокола", "Номер_Протокола"),
            "Код_Ответственного": ("Сотрудники", "Код_Сотрудника", "ФИО"),
            "Код_Аудитории": ("Аудитории", "Код_Аудитории", "Номер_Кабинета")
        }
    },
    "auditoriyalar": {
        "db_table": "Аудитории",
        "pk": "Код_Аудитории",
        "title": "Аудиториялар",
        "icon": "fa-door-open",
        "columns": ["Кабинет №", "Аудитория түрі", "Орын саны", "Кафедра"],
        "fields": ["Номер_Кабинета", "Тип_Аудитории", "Количество_Мест", "Код_Кафедры"],
        "types": ["text", "select", "number", "fk"],
        "fk": {
            "Код_Кафедры": ("Кафедры", "Код_Кафедры", "Название_Кафедры")
        },
        "choices": {
            "Тип_Аудитории": ["Дәріс залы", "Компьютерлік сынып", "Практикалық кабинет", "Кафедра кабинеті"]
        }
    }
}

ALLOWED_ROLES = {
    "secretary": "Кафедра хатшысы",
    "admin": "Сайт басқарушысы (Админ)"
}


def qid(identifier):
    return f"[{identifier}]"


def format_cell(val):
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        if getattr(val, "hour", 0) == 0 and getattr(val, "minute", 0) == 0:
            return val.strftime("%Y-%m-%d")
        return val.strftime("%Y-%m-%d %H:%M")
    return str(val)


def normalize_rows(rows):
    return [[row[0]] + [format_cell(c) for c in row[1:]] for row in rows]


def coerce_param(val, field_name):
    if val == "":
        return None
    if field_name.startswith("Код_") or field_name in ("Объем_Часов", "Курс", "Количество_Мест"):
        try:
            return int(val)
        except ValueError:
            return val
    return val


def get_initials(full_name):
    parts = [p for p in (full_name or "").strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return full_name[:2].upper() if full_name else "ҚЖ"


def load_fk_lookups(cur):
    lookups = {}
    targets = set()
    for meta in TABLES.values():
        for ref_tbl, ref_pk, ref_label in meta.get("fk", {}).values():
            targets.add((ref_tbl, ref_pk, ref_label))

    for ref_tbl, ref_pk, ref_label in targets:
        try:
            cur.execute(f"SELECT {qid(ref_pk)}, {qid(ref_label)} FROM {qid(ref_tbl)} ORDER BY {qid(ref_pk)} ASC")
            items = [(str(r[0]), format_cell(r[1])) for r in cur.fetchall()]
            lookups[ref_tbl] = {
                "options": items,
                "map": {k: v for k, v in items}
            }
        except Exception:
            lookups[ref_tbl] = {"options": [], "map": {}}
    return lookups


def init_demo_db():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            role_title TEXT NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users (username, password, full_name, role, role_title) VALUES (?, ?, ?, ?, ?)",
            [
                ("hatshy", "1234", "Айтбаева Г.А.", "secretary", "Кафедра хатшысы"),
                ("admin", "admin", "Амандық Сабина", "admin", "Сайт басқарушысы (Админ)")
            ]
        )

    for meta in TABLES.values():
        tname = qid(meta["db_table"])
        pk = qid(meta["pk"])
        cols_def = ", ".join([f"{qid(f)} TEXT" for f in meta["fields"]])
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tname} ({pk} INTEGER PRIMARY KEY AUTOINCREMENT, {cols_def})")

    cur.execute("SELECT COUNT(*) FROM [Порученичя]")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO [Кафедры] ([Название_Кафедры], [Зав_Кафедрой], [Кабинет]) VALUES (?, ?, ?)",
            [("Ақпараттық жүйелер және ИТ кафедрасы", "Нұрланұлы Қ.Т.", "305-каб")]
        )
        cur.executemany(
            "INSERT INTO [Сотрудники] ([ФИО], [Должность], [Телефон], [Email], [Код_Кафедры]) VALUES (?, ?, ?, ?, ?)",
            [
                ("Оспанов Е.Б.", "Қауымдастырылған профессор", "+7 701 111 22 33", "ospanov@edu.kz", "1"),
                ("Серікова Ә.М.", "Аға оқытушы", "+7 702 222 33 44", "serikova@edu.kz", "1"),
                ("Айтбаева Г.А.", "Кафедра хатшысы", "+7 705 333 44 55", "aitbaeva@edu.kz", "1")
            ]
        )
        cur.executemany(
            "INSERT INTO [Документы] ([Номер_Документа], [Тип_Документа], [Дата_Регистрации], [Тема], [Статус_Архив]) VALUES (?, ?, ?, ?, ?)",
            [
                ("№ 14-08/112", "Бұйрық", "2026-02-15", "2026-2027 оқу жылына арналған оқу жүктемесі", "Бекітілді"),
                ("№ 14-08/119", "Өкім", "2026-02-22", "Өндірістік тәжірибеден өту туралы", "Орындалуда")
            ]
        )
        cur.executemany(
            "INSERT INTO [Протоколы] ([Номер_Протокола], [Дата_Заседания], [Повестка_Дня], [Решение]) VALUES (?, ?, ?, ?)",
            [
                ("Хаттама № 6", "2026-02-18", "Дипломдық жоба тақырыптарын бекіту", "Тақырыптар бекітілсін"),
                ("Хаттама № 7", "2026-02-25", "Аралық бақылау қорытындыларын талқылау", "Нәтижелер қабылдансын")
            ]
        )
        cur.executemany(
            "INSERT INTO [Порученичя] ([Код_Документа], [Код_Исполнителя], [Текст_Поручения], [Срок_Исполнения], [Статус]) VALUES (?, ?, ?, ?, ?)",
            [
                ("1", "1", "Оқудан шығарылатын студенттер тізімін дайындау", "2026-02-28", "Орындалуда"),
                ("2", "2", "Жұмыс оқу бағдарламаларын (Силлабустарды) жаңарту", "2026-03-05", "Аяқталды"),
                ("1", "3", "Дипломдық жұмыс жетекшілерін бекіту хаттамасын тексеру", "2026-02-20", "Мерзімі өткен")
            ]
        )
        cur.executemany(
            "INSERT INTO [Дисциплины] ([Название_Дисциплины], [Объем_Часов], [Код_Преподавателя]) VALUES (?, ?, ?)",
            [
                ("Деректер қорын жобалау", "150", "1"),
                ("Веб-бағдарламалау негіздері", "150", "2"),
                ("Жүйелік талдау және шешім қабылдау", "150", "1")
            ]
        )
        cur.executemany(
            "INSERT INTO [Группы] ([Название_Группы], [Курс], [Код_Куратора]) VALUES (?, ?, ?)",
            [
                ("ИС-24-А1", "2", "2"),
                ("ИС-24-А2", "2", "1")
            ]
        )
        cur.executemany(
            "INSERT INTO [Студенты] ([ФИО_Студента], [Телефон], [Код_Группы]) VALUES (?, ?, ?)",
            [
                ("Амандық Сабина", "+7 707 100 20 30", "1"),
                ("Қайратұлы Әлихан", "+7 707 200 30 40", "1"),
                ("Төлегенова Дильназ", "+7 707 300 40 50", "1")
            ]
        )
        cur.executemany(
            "INSERT INTO [Заседания] ([Тема_Обсуждения], [Код_Протокола], [Код_Ответственного], [Дата_Заседания], [Код_Аудитории]) VALUES (?, ?, ?, ?, ?)",
            [("Кафедраның кезекті отырысы", "1", "3", "2026-03-02", "1")]
        )
        cur.executemany(
            "INSERT INTO [Аудитории] ([Номер_Кабинета], [Тип_Аудитории], [Количество_Мест], [Код_Кафедры]) VALUES (?, ?, ?, ?)",
            [
                ("305", "Кафедра кабинеті", "25", "1"),
                ("412", "Компьютерлік сынып", "30", "1")
            ]
        )
    conn.commit()
    conn.close()


def get_db_connection():
    if pyodbc and os.path.exists(ACCDB_PATH):
        try:
            conn_str = (
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"DBQ={ACCDB_PATH};"
            )
            return pyodbc.connect(conn_str), "MS Access"
        except Exception:
            pass
    return sqlite3.connect(SQLITE_PATH), "SQLite (Жергілікті ҚБ)"


init_demo_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Бұл бөлім тек сайт басқарушысына (Админге) қолжетімді!", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


@app.context_processor
def inject_user():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "username": session.get("username", ""),
            "full_name": session.get("full_name", ""),
            "role": session.get("role", ""),
            "role_title": session.get("role_title", ""),
            "initials": get_initials(session.get("full_name", ""))
        }
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    error = None
    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, full_name, role, role_title FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["full_name"] = user[2]
            session["role"] = user[3]
            session["role_title"] = user[4]
            return redirect(url_for("dashboard"))
        error = "Логин немесе құпиясөз қате!"

    return render_template("login.html", error=error, username=username)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn, db_mode = get_db_connection()
    cur = conn.cursor()
    lookups = load_fk_lookups(cur)

    stats = {}
    for key, meta in TABLES.items():
        tname = qid(meta["db_table"])
        cur.execute(f"SELECT COUNT(*) FROM {tname}")
        stats[key] = {"title": meta["title"], "count": cur.fetchone()[0], "icon": meta["icon"]}

    cur.execute("SELECT [Статус], COUNT(*) FROM [Порученичя] GROUP BY [Статус]")
    task_status_counts = {"Орындалуда": 0, "Аяқталды": 0, "Мерзімі өткен": 0}
    for st, cnt in cur.fetchall():
        st_str = format_cell(st)
        task_status_counts[st_str] = task_status_counts.get(st_str, 0) + cnt

    if db_mode == "MS Access":
        cur.execute(
            "SELECT TOP 4 [Код_Поручения], [Текст_Поручения], [Код_Исполнителя], [Срок_Исполнения], [Код_Документа], [Статус] "
            "FROM [Порученичя] ORDER BY [Код_Поручения] DESC"
        )
    else:
        cur.execute(
            "SELECT [Код_Поручения], [Текст_Поручения], [Код_Исполнителя], [Срок_Исполнения], [Код_Документа], [Статус] "
            "FROM [Порученичя] ORDER BY [Код_Поручения] DESC LIMIT 4"
        )
    emp_map = lookups.get("Сотрудники", {}).get("map", {})
    doc_map = lookups.get("Документы", {}).get("map", {})
    recent_tasks = []
    for r in normalize_rows(cur.fetchall()):
        recent_tasks.append([
            r[0],
            r[1],
            emp_map.get(r[2], r[2]),
            r[3],
            doc_map.get(r[4], r[4]),
            r[5]
        ])

    if db_mode == "MS Access":
        cur.execute(
            "SELECT TOP 3 [Код_Заседания], [Тема_Обсуждения], [Дата_Заседания], [Код_Аудитории], [Код_Ответственного] "
            "FROM [Заседания] ORDER BY [Код_Заседания] DESC"
        )
    else:
        cur.execute(
            "SELECT [Код_Заседания], [Тема_Обсуждения], [Дата_Заседания], [Код_Аудитории], [Код_Ответственного] "
            "FROM [Заседания] ORDER BY [Код_Заседания] DESC LIMIT 3"
        )
    aud_map = lookups.get("Аудитории", {}).get("map", {})
    recent_meetings = []
    for r in normalize_rows(cur.fetchall()):
        recent_meetings.append([
            r[0],
            r[1],
            r[2],
            aud_map.get(r[3], r[3]),
            emp_map.get(r[4], r[4])
        ])

    if db_mode == "MS Access":
        cur.execute(
            "SELECT TOP 3 [Код_Документа], [Номер_Документа], [Тема], [Дата_Регистрации], [Статус_Архив] "
            "FROM [Документы] ORDER BY [Код_Документа] DESC"
        )
    else:
        cur.execute(
            "SELECT [Код_Документа], [Номер_Документа], [Тема], [Дата_Регистрации], [Статус_Архив] "
            "FROM [Документы] ORDER BY [Код_Документа] DESC LIMIT 3"
        )
    recent_docs = normalize_rows(cur.fetchall())

    if db_mode == "MS Access":
        cur.execute(
            "SELECT TOP 3 [Код_Протокола], [Номер_Протокола], [Повестка_Дня], [Дата_Заседания] "
            "FROM [Протоколы] ORDER BY [Код_Протокола] DESC"
        )
    else:
        cur.execute(
            "SELECT [Код_Протокола], [Номер_Протокола], [Повестка_Дня], [Дата_Заседания] "
            "FROM [Протоколы] ORDER BY [Код_Протокола] DESC LIMIT 3"
        )
    recent_protocols = normalize_rows(cur.fetchall())

    # Распределение студентов по группам
    grp_map = lookups.get("Группы", {}).get("map", {})
    grp_counts_dict = {}
    cur.execute("SELECT [Код_Группы] FROM [Студенты]")
    for (g_code,) in cur.fetchall():
        g_key = format_cell(g_code)
        g_name = grp_map.get(g_key, f"Топ #{g_key}" if g_key else "Басқа")
        grp_counts_dict[g_name] = grp_counts_dict.get(g_name, 0) + 1
    group_breakdown = sorted(grp_counts_dict.items(), key=lambda x: x[1], reverse=True)
    group_labels = [x[0] for x in group_breakdown]
    group_counts = [x[1] for x in group_breakdown]

    # Агрегация по месяцам (YYYY-MM) для графиков
    month_buckets = {}
    def collect_months(table_name_sql, date_col_sql, target_idx):
        try:
            cur.execute(f"SELECT {date_col_sql} FROM {table_name_sql}")
            for (dt_val,) in cur.fetchall():
                s = format_cell(dt_val)
                ym = s[:7] if len(s) >= 7 and s[4] == "-" else (
                    f"{s[6:10]}-{s[3:5]}" if len(s) >= 10 and s[2] == "." else "2026-11"
                )
                month_buckets.setdefault(ym, [0, 0, 0])
                month_buckets[ym][target_idx] += 1
        except Exception:
            pass

    collect_months("[Документы]", "[Дата_Регистрации]", 0)
    collect_months("[Порученичя]", "[Срок_Исполнения]", 1)
    collect_months("[Заседания]", "[Дата_Заседания]", 2)

    sorted_months = sorted(month_buckets.keys())[-6:]
    if not sorted_months:
        sorted_months = ["2026-09", "2026-10", "2026-11"]
    chart_docs_series = [month_buckets.get(m, [0, 0, 0])[0] for m in sorted_months]
    chart_tasks_series = [month_buckets.get(m, [0, 0, 0])[1] for m in sorted_months]
    chart_meetings_series = [month_buckets.get(m, [0, 0, 0])[2] for m in sorted_months]

    conn.close()

    users_count = 0
    if session.get("role") == "admin":
        uconn = sqlite3.connect(SQLITE_PATH)
        ucur = uconn.cursor()
        ucur.execute("SELECT COUNT(*) FROM users")
        users_count = ucur.fetchone()[0]
        uconn.close()

    return render_template(
        "dashboard.html",
        tables=TABLES,
        active_tab="dashboard",
        stats=stats,
        task_status_counts=task_status_counts,
        db_mode=db_mode,
        users_count=users_count,
        recent_tasks=recent_tasks,
        recent_meetings=recent_meetings,
        recent_docs=recent_docs,
        recent_protocols=recent_protocols,
        group_breakdown=group_breakdown,
        group_labels=group_labels,
        group_counts=group_counts,
        chart_months=sorted_months,
        chart_docs_series=chart_docs_series,
        chart_tasks_series=chart_tasks_series,
        chart_meetings_series=chart_meetings_series
    )


@app.route("/table/<table_name>")
@login_required
def table_view(table_name):
    if table_name not in TABLES:
        return redirect(url_for("table_view", table_name="tapsyrmalar"))

    meta = TABLES[table_name]
    search_q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()

    conn, db_mode = get_db_connection()
    cur = conn.cursor()
    lookups = load_fk_lookups(cur)

    tname = qid(meta["db_table"])
    pk = qid(meta["pk"])
    fields_str = ", ".join([qid(f) for f in meta["fields"]])
    cur.execute(f"SELECT {pk}, {fields_str} FROM {tname} ORDER BY {pk} ASC")
    raw_rows = normalize_rows(cur.fetchall())
    conn.close()

    fk_defs = meta.get("fk", {})
    display_rows = []
    for r in raw_rows:
        row_id = r[0]
        raw_vals = r[1:]
        disp_vals = []
        for f_name, val in zip(meta["fields"], raw_vals):
            if f_name in fk_defs:
                ref_tbl = fk_defs[f_name][0]
                label = lookups.get(ref_tbl, {}).get("map", {}).get(val, "")
                disp_vals.append(f"{label}" if label else val)
            else:
                disp_vals.append(val)
        display_rows.append({
            "id": row_id,
            "raw": raw_vals,
            "display": disp_vals
        })

    if status_filter and "Статус" in meta["fields"]:
        st_idx = meta["fields"].index("Статус")
        display_rows = [item for item in display_rows if item["raw"][st_idx] == status_filter]

    if search_q:
        q_lower = search_q.lower()
        display_rows = [
            item for item in display_rows
            if any(q_lower in cell.lower() for cell in item["display"])
            or any(q_lower in cell.lower() for cell in item["raw"])
        ]

    field_options = {}
    for f_name, (ref_tbl, _, _) in fk_defs.items():
        field_options[f_name] = lookups.get(ref_tbl, {}).get("options", [])

    return render_template(
        "index.html",
        tables=TABLES,
        active_tab=table_name,
        table_key=table_name,
        meta=meta,
        rows=display_rows,
        field_options=field_options,
        search_q=search_q,
        status_filter=status_filter,
        db_mode=db_mode
    )


@app.route("/table/<table_name>/add", methods=["POST"])
@login_required
def add_record(table_name):
    if table_name not in TABLES:
        return redirect(url_for("index"))

    meta = TABLES[table_name]
    raw_values = [request.form.get(f, "").strip() for f in meta["fields"]]

    if not any(raw_values):
        flash("Кем дегенде бір өрісті толтырыңыз!", "error")
        return redirect(url_for("table_view", table_name=table_name))

    values = [coerce_param(v, f) for v, f in zip(raw_values, meta["fields"])]

    conn, _ = get_db_connection()
    cur = conn.cursor()
    tname = qid(meta["db_table"])
    placeholders = ", ".join(["?"] * len(meta["fields"]))
    fields_str = ", ".join([qid(f) for f in meta["fields"]])
    try:
        cur.execute(f"INSERT INTO {tname} ({fields_str}) VALUES ({placeholders})", values)
        conn.commit()
        flash("Жаңа жазба сәтті қосылды!", "success")
    except Exception as e:
        flash(f"Дерек қосу қатесі: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for("table_view", table_name=table_name))


@app.route("/table/<table_name>/edit/<int:row_id>", methods=["POST"])
@login_required
def edit_record(table_name, row_id):
    if table_name not in TABLES:
        return redirect(url_for("index"))

    meta = TABLES[table_name]
    raw_values = [request.form.get(f, "").strip() for f in meta["fields"]]

    if not any(raw_values):
        flash("Кем дегенде бір өрісті толтырыңыз!", "error")
        return redirect(url_for("table_view", table_name=table_name))

    values = [coerce_param(v, f) for v, f in zip(raw_values, meta["fields"])]
    values.append(row_id)

    conn, _ = get_db_connection()
    cur = conn.cursor()
    tname = qid(meta["db_table"])
    pk = qid(meta["pk"])
    set_clause = ", ".join([f"{qid(f)} = ?" for f in meta["fields"]])
    try:
        cur.execute(f"UPDATE {tname} SET {set_clause} WHERE {pk} = ?", values)
        conn.commit()
        flash("Жазба сәтті жаңартылды!", "success")
    except Exception as e:
        flash(f"Жазбаны жаңарту қатесі: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for("table_view", table_name=table_name))


@app.route("/table/<table_name>/delete/<int:row_id>", methods=["POST"])
@login_required
def delete_record(table_name, row_id):
    if table_name not in TABLES:
        return redirect(url_for("index"))

    meta = TABLES[table_name]
    conn, _ = get_db_connection()
    cur = conn.cursor()
    tname = qid(meta["db_table"])
    pk = qid(meta["pk"])
    try:
        cur.execute(f"DELETE FROM {tname} WHERE {pk} = ?", (row_id,))
        conn.commit()
        flash("Жазба өшірілді.", "success")
    except Exception as e:
        flash(f"Жазбаны өшіру мүмкін болмады (байланысқан жазбалар бар болуы мүмкін): {e}", "error")
    finally:
        conn.close()

    return redirect(url_for("table_view", table_name=table_name))


@app.route("/table/<table_name>/export")
@login_required
def export_csv(table_name):
    if table_name not in TABLES:
        return redirect(url_for("index"))

    meta = TABLES[table_name]
    conn, _ = get_db_connection()
    cur = conn.cursor()
    lookups = load_fk_lookups(cur)
    tname = qid(meta["db_table"])
    pk = qid(meta["pk"])
    fields_str = ", ".join([qid(f) for f in meta["fields"]])
    cur.execute(f"SELECT {pk}, {fields_str} FROM {tname} ORDER BY {pk} ASC")
    rows = normalize_rows(cur.fetchall())
    conn.close()

    fk_defs = meta.get("fk", {})
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["#"] + meta["columns"])
    for idx, row in enumerate(rows, start=1):
        disp = []
        for f_name, val in zip(meta["fields"], row[1:]):
            if f_name in fk_defs:
                ref_tbl = fk_defs[f_name][0]
                disp.append(lookups.get(ref_tbl, {}).get("map", {}).get(val, val))
            else:
                disp.append(val)
        writer.writerow([idx] + disp)

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"}
    )


@app.route("/admin/users")
@admin_required
def manage_users():
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, full_name, role, role_title FROM users ORDER BY id ASC")
    users = cur.fetchall()
    conn.close()
    return render_template("users.html", tables=TABLES, active_tab="admin_users", users=users)


@app.route("/admin/users/add", methods=["POST"])
@admin_required
def add_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    full_name = request.form.get("full_name", "").strip()
    role = request.form.get("role", "secretary").strip()

    if role not in ALLOWED_ROLES:
        role = "secretary"
    role_title = ALLOWED_ROLES[role]

    if not username or not password or not full_name:
        flash("Логин, құпиясөз және аты-жөні міндетті түрде толтырылуы керек!", "error")
        return redirect(url_for("manage_users"))

    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, full_name, role, role_title) VALUES (?, ?, ?, ?, ?)",
            (username, password, full_name, role, role_title)
        )
        conn.commit()
        flash("Пайдаланушы сәтті қосылды!", "success")
    except sqlite3.IntegrityError:
        flash("Бұл логин бұрыннан тіркелген!", "error")
    finally:
        conn.close()

    return redirect(url_for("manage_users"))


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == session.get("user_id"):
        flash("Өз аккаунтыңызды өшіре алмайсыз!", "error")
        return redirect(url_for("manage_users"))

    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("Пайдаланушы өшірілді.", "success")
    return redirect(url_for("manage_users"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)