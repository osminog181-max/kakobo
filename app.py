import streamlit as st
from datetime import date, datetime
from database import Database
from constants import CATEGORIES, FOOD_CATEGORIES

st.set_page_config(
    page_title="Кекобо",
    page_icon="📒",
    layout="wide"
)

# ---------- Инициализация ----------
@st.cache_resource
def get_db():
    return Database()

db = get_db()

# ---------- Хелперы ----------
def format_money(value: float) -> str:
    return f"{value:,.2f} €".replace(",", " ")


def get_month_label(m):
    label = m["start_date"]
    if m["note"]:
        label += f" — {m['note']}"
    return label


# ---------- Боковая панель ----------
st.sidebar.title("Кекобо 📒")

months = db.get_all_months()
month_options = {get_month_label(m): m["id"] for m in months}

if not month_options:
    st.sidebar.info("Пока нет ни одного месяца")
    selected_month_id = None
else:
    selected_label = st.sidebar.selectbox(
        "Месяц (дата начала)",
        options=list(month_options.keys()),
        index=0
    )
    selected_month_id = month_options[selected_label]

# Недели
selected_week_id = None
if selected_month_id:
    weeks = db.get_weeks_for_month(selected_month_id)
    week_options = {
        f"Неделя {w['week_num']} ({w['start_date']})": w["id"]
        for w in weeks
    }

    if week_options:
        selected_week_label = st.sidebar.selectbox(
            "Неделя",
            options=list(week_options.keys()),
            index=len(week_options) - 1  # последняя неделя по умолчанию
        )
        selected_week_id = week_options[selected_week_label]
    else:
        st.sidebar.warning("В этом месяце ещё нет недель")

st.sidebar.divider()

# Кнопки создания
with st.sidebar.expander("➕ Создать новый месяц", expanded=False):
    with st.form("new_month_form"):
        new_date = st.date_input("Дата начала месяца", value=date.today())
        new_salary = st.number_input("Зарплата (€)", min_value=0.0, step=10.0, value=0.0)
        new_food_home = st.number_input("Еда домашняя (€) — откладывается", min_value=0.0, step=5.0, value=0.0)
        new_food_work = st.number_input("Еда работа (€) — откладывается", min_value=0.0, step=5.0, value=0.0)
        new_note = st.text_input("Заметка (необязательно)")

        submitted = st.form_submit_button("Создать месяц")
        if submitted:
            month_id = db.add_month(
                start_date=new_date.isoformat(),
                salary=new_salary,
                note=new_note.strip()
            )
            db.set_category_budget(month_id, "Еда домашняя", new_food_home)
            db.set_category_budget(month_id, "Еда работа", new_food_work)
            db.add_week(month_id=month_id, week_num=1, start_date=new_date.isoformat())
            st.success("Месяц создан!")
            st.rerun()

if selected_month_id:
    if st.sidebar.button("📅 Начать новую неделю"):
        weeks = db.get_weeks_for_month(selected_month_id)
        next_num = len(weeks) + 1
        today = date.today().isoformat()
        db.add_week(month_id=selected_month_id, week_num=next_num, start_date=today)
        st.success(f"Создана Неделя {next_num}")
        st.rerun()

# ---------- Основная часть ----------
st.title("Кекобо")

if not selected_month_id:
    st.info("Создай первый месяц в боковой панели →")
    st.stop()

# ===== Расчёт итогов =====
month = db.get_month(selected_month_id)
salary = month["salary"] or 0.0
budgets = db.get_category_budgets(selected_month_id)
spent = db.get_spent_by_category(selected_month_id)

food_home_budget = budgets.get("Еда домашняя", 0.0)
food_work_budget = budgets.get("Еда работа", 0.0)

spent_food_home = spent.get("Еда домашняя", 0.0)
spent_food_work = spent.get("Еда работа", 0.0)
total_spent = sum(spent.values())
spent_other = total_spent - spent_food_home - spent_food_work

main_available = salary - food_home_budget - food_work_budget
total_remain = main_available - spent_other
remain_food_home = food_home_budget - spent_food_home
remain_food_work = food_work_budget - spent_food_work

# ===== Метрики =====
col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего потрачено", format_money(total_spent))
col2.metric("Общий остаток", format_money(total_remain))
col3.metric("Еда домашняя", format_money(remain_food_home))
col4.metric("Еда работа", format_money(remain_food_work))

st.divider()

# ===== По категориям =====
st.subheader("По категориям")

left, right = st.columns(2)

with left:
    st.markdown("**Потрачено**")
    for cat in CATEGORIES:
        amount = spent.get(cat, 0.0)
        st.write(f"{cat}: **{format_money(amount)}**")

with right:
    st.markdown("**Осталось**")
    for cat in CATEGORIES:
        if cat == "Еда домашняя":
            st.write(f"{cat}: **{format_money(remain_food_home)}**")
        elif cat == "Еда работа":
            st.write(f"{cat}: **{format_money(remain_food_work)}**")
        else:
            st.write(f"{cat}: —")

st.divider()

# ===== Добавление записи =====
st.subheader("Добавить запись")

if not selected_week_id:
    st.warning("Сначала выбери или создай неделю")
else:
    with st.form("add_expense_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            exp_date = st.date_input("Дата", value=date.today())
        with c2:
            exp_amount = st.number_input("Сумма (€)", min_value=0.01, step=1.0, format="%.2f")
        with c3:
            exp_category = st.selectbox("Категория", CATEGORIES)

        exp_notes = st.text_input("Примечания")

        if st.form_submit_button("💾 Сохранить"):
            db.add_expense(
                week_id=selected_week_id,
                date=exp_date.isoformat(),
                amount=exp_amount,
                category=exp_category,
                notes=exp_notes.strip()
            )
            st.success("Запись добавлена")
            st.rerun()

# ===== Таблица записей =====
st.subheader("Записи текущей недели")

if selected_week_id:
    expenses = db.get_expenses_for_week(selected_week_id)

    if expenses:
        import pandas as pd

        df = pd.DataFrame([
            {
                "Дата": e["date"],
                "Сумма": f"{e['amount']:.2f} €",
                "Категория": e["category"],
                "Примечания": e["notes"] or "",
                "id": e["id"]
            }
            for e in expenses
        ])

        # Показываем без id
        st.dataframe(
            df.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True
        )

        # Удаление
        with st.expander("🗑 Удалить запись"):
            ids = {f"{row['Дата']} | {row['Сумма']} | {row['Категория']}": row["id"] for _, row in df.iterrows()}
            to_delete = st.selectbox("Выбери запись для удаления", options=list(ids.keys()))
            if st.button("Удалить", type="primary"):
                db.delete_expense(ids[to_delete])
                st.success("Удалено")
                st.rerun()
    else:
        st.info("В этой неделе пока нет записей")
else:
    st.info("Выбери неделю")