import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, date

from database import Database
from constants import CATEGORIES, FOOD_CATEGORIES

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class KekoboApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Кекобо — учёт расходов")
        self.geometry("1100x780")
        self.minsize(900, 650)

        self.db = Database()
        self.current_month_id = None
        self.current_week_id = None
        self.tree_item_to_id = {}

        self._build_ui()
        self._load_months_into_combobox()

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_main = self.tabview.add("Кекобо")
        self.tab_charts = self.tabview.add("Графики")

        self._build_main_tab()
        self._build_charts_tab()

    def _build_main_tab(self):
        # Выбор месяца / недели
        top_frame = ctk.CTkFrame(self.tab_main)
        top_frame.pack(fill="x", padx=5, pady=(5, 10))

        ctk.CTkLabel(top_frame, text="Месяц (дата начала):").pack(side="left", padx=(10, 5))
        self.month_combo = ctk.CTkComboBox(
            top_frame, values=["— нет месяцев —"], width=220, command=self._on_month_selected
        )
        self.month_combo.pack(side="left", padx=5)

        ctk.CTkLabel(top_frame, text="Неделя:").pack(side="left", padx=(20, 5))
        self.week_combo = ctk.CTkComboBox(
            top_frame, values=["— выберите месяц —"], width=180, command=self._on_week_selected
        )
        self.week_combo.pack(side="left", padx=5)

        # --- Итоги: Всего потрачено + 3 остатка ---
        total_frame = ctk.CTkFrame(self.tab_main)
        total_frame.pack(fill="x", padx=5, pady=(0, 8))

        # Первая строка
        row1 = ctk.CTkFrame(total_frame, fg_color="transparent")
        row1.pack(pady=(10, 4))

        ctk.CTkLabel(row1, text="Всего потрачено:", font=ctk.CTkFont(size=15)).pack(side="left", padx=(15, 5))
        self.total_spent_label = ctk.CTkLabel(row1, text="0.00 €", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_spent_label.pack(side="left", padx=(0, 30))

        ctk.CTkLabel(row1, text="Общий остаток:", font=ctk.CTkFont(size=15)).pack(side="left", padx=(10, 5))
        self.total_remain_label = ctk.CTkLabel(row1, text="0.00 €", font=ctk.CTkFont(size=16, weight="bold"))
        self.total_remain_label.pack(side="left")

        # Вторая строка — остатки по еде
        row2 = ctk.CTkFrame(total_frame, fg_color="transparent")
        row2.pack(pady=(4, 10))

        ctk.CTkLabel(row2, text="Еда домашняя:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(15, 5))
        self.food_home_remain_label = ctk.CTkLabel(row2, text="0.00 €", font=ctk.CTkFont(size=14, weight="bold"))
        self.food_home_remain_label.pack(side="left", padx=(0, 30))

        ctk.CTkLabel(row2, text="Еда работа:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 5))
        self.food_work_remain_label = ctk.CTkLabel(row2, text="0.00 €", font=ctk.CTkFont(size=14, weight="bold"))
        self.food_work_remain_label.pack(side="left")

        # По категориям
        summary_frame = ctk.CTkFrame(self.tab_main)
        summary_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(summary_frame, text="По категориям", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=10, pady=(8, 5)
        )

        cols_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        cols_frame.pack(fill="x", padx=10, pady=5)

        # Потрачено
        left = ctk.CTkFrame(cols_frame)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(left, text="Потрачено", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        self.spent_labels = {}
        for cat in CATEGORIES:
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(row, text=cat, width=140, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="0.00 €", width=100, anchor="e")
            lbl.pack(side="right")
            self.spent_labels[cat] = lbl

        # Осталось
        right = ctk.CTkFrame(cols_frame)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(right, text="Осталось", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        self.remain_labels = {}
        for cat in CATEGORIES:
            row = ctk.CTkFrame(right, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(row, text=cat, width=140, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text="— €", width=100, anchor="e")
            lbl.pack(side="right")
            self.remain_labels[cat] = lbl

        # Кнопка добавить
        btn_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=8)

        ctk.CTkButton(
            btn_frame, text="➕ Добавить запись",
            command=self._open_add_expense_dialog, width=180
        ).pack(side="left", padx=5)

        # Таблица
        table_frame = ctk.CTkFrame(self.tab_main)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(table_frame, text="Записи", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=10, pady=(8, 4)
        )

        columns = ("date", "amount", "category", "notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=11, selectmode="browse")

        self.tree.heading("date", text="Дата")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("category", text="Категория")
        self.tree.heading("notes", text="Примечания")

        self.tree.column("date", width=110, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("category", width=150)
        self.tree.column("notes", width=350)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=5)

        # Нижние кнопки
        bottom_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=5, pady=10)

        ctk.CTkButton(
            bottom_frame, text="📅 Начать новую неделю",
            command=self._start_new_week, width=180
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            bottom_frame, text="💰 Начать новый месяц",
            command=self._start_new_month, width=180,
            fg_color="#2d6a4f", hover_color="#1b4332"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            bottom_frame, text="🗑 Удалить выбранную запись",
            command=self._delete_selected_expense, width=200,
            fg_color="#9b2226", hover_color="#660708"
        ).pack(side="right", padx=5)

    def _build_charts_tab(self):
        ctk.CTkLabel(
            self.tab_charts,
            text="Здесь будут графики\n(пока заглушка)",
            font=ctk.CTkFont(size=18)
        ).pack(expand=True)

    # ==================== ЛОГИКА ====================
    def _load_months_into_combobox(self):
        months = self.db.get_all_months()
        if not months:
            self.month_combo.configure(values=["— нет месяцев —"])
            self.month_combo.set("— нет месяцев —")
            return

        values = []
        self.month_id_map = {}
        for m in months:
            label = f"{m['start_date']}"
            if m["note"]:
                label += f" — {m['note']}"
            values.append(label)
            self.month_id_map[label] = m["id"]

        self.month_combo.configure(values=values)
        self.month_combo.set(values[0])
        self._on_month_selected(values[0])

    def _on_month_selected(self, choice: str):
        if choice not in getattr(self, "month_id_map", {}):
            self.current_month_id = None
            self.week_combo.configure(values=["— выберите месяц —"])
            self.week_combo.set("— выберите месяц —")
            return

        self.current_month_id = self.month_id_map[choice]
        self._load_weeks_into_combobox()

    def _load_weeks_into_combobox(self):
        if not self.current_month_id:
            return

        weeks = self.db.get_weeks_for_month(self.current_month_id)
        if not weeks:
            self.week_combo.configure(values=["— нет недель —"])
            self.week_combo.set("— нет недель —")
            self.current_week_id = None
            self._clear_table()
            self._update_summary()
            return

        values = []
        self.week_id_map = {}
        for w in weeks:
            label = f"Неделя {w['week_num']} ({w['start_date']})"
            values.append(label)
            self.week_id_map[label] = w["id"]

        self.week_combo.configure(values=values)
        self.week_combo.set(values[-1])
        self._on_week_selected(values[-1])

    def _on_week_selected(self, choice: str):
        if choice not in getattr(self, "week_id_map", {}):
            self.current_week_id = None
            self._clear_table()
            self._update_summary()
            return

        self.current_week_id = self.week_id_map[choice]
        self._load_expenses_table()
        self._update_summary()

    def _clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_item_to_id.clear()

    def _load_expenses_table(self):
        self._clear_table()
        if not self.current_week_id:
            return

        for e in self.db.get_expenses_for_week(self.current_week_id):
            item = self.tree.insert("", "end", values=(
                e["date"],
                f"{e['amount']:.2f} €",
                e["category"],
                e["notes"] or ""
            ))
            self.tree_item_to_id[item] = e["id"]

    def _update_summary(self):
        if not self.current_month_id:
            self.total_spent_label.configure(text="0.00 €")
            self.total_remain_label.configure(text="0.00 €")
            self.food_home_remain_label.configure(text="0.00 €")
            self.food_work_remain_label.configure(text="0.00 €")
            for cat in CATEGORIES:
                self.spent_labels[cat].configure(text="0.00 €")
                self.remain_labels[cat].configure(text="— €")
            return

        month = self.db.get_month(self.current_month_id)
        salary = month["salary"] if month else 0.0
        budgets = self.db.get_category_budgets(self.current_month_id)
        spent = self.db.get_spent_by_category(self.current_month_id)

        # Бюджеты еды (отложенные кошельки)
        food_home_budget = budgets.get("Еда домашняя", 0.0)
        food_work_budget = budgets.get("Еда работа", 0.0)

        # Фактические траты
        spent_food_home = spent.get("Еда домашняя", 0.0)
        spent_food_work = spent.get("Еда работа", 0.0)
        total_spent = sum(spent.values())
        spent_other = total_spent - spent_food_home - spent_food_work

        # === Остатки ===
        # 1. Общий остаток = (зарплата - еда) - траты по остальным категориям
        main_available = salary - food_home_budget - food_work_budget
        total_remain = main_available - spent_other

        # 2 и 3. Остатки по еде
        remain_food_home = food_home_budget - spent_food_home
        remain_food_work = food_work_budget - spent_food_work

        # Обновляем верхние цифры
        self.total_spent_label.configure(text=f"{total_spent:.2f} €")
        self.total_remain_label.configure(text=f"{total_remain:.2f} €")
        self.food_home_remain_label.configure(text=f"{remain_food_home:.2f} €")
        self.food_work_remain_label.configure(text=f"{remain_food_work:.2f} €")

        # По категориям
        for cat in CATEGORIES:
            amount = spent.get(cat, 0.0)
            self.spent_labels[cat].configure(text=f"{amount:.2f} €")

            if cat == "Еда домашняя":
                self.remain_labels[cat].configure(text=f"{remain_food_home:.2f} €")
            elif cat == "Еда работа":
                self.remain_labels[cat].configure(text=f"{remain_food_work:.2f} €")
            else:
                self.remain_labels[cat].configure(text="— €")

    def _open_add_expense_dialog(self):
        if not self.current_week_id:
            messagebox.showwarning("Нет недели", "Сначала выберите или создайте неделю.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить запись")
        dialog.geometry("420x380")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Дата (ГГГГ-ММ-ДД):").pack(pady=(15, 0))
        date_entry = ctk.CTkEntry(dialog, width=200)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Сумма (€):").pack(pady=(10, 0))
        amount_entry = ctk.CTkEntry(dialog, width=200)
        amount_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Категория:").pack(pady=(10, 0))
        cat_combo = ctk.CTkComboBox(dialog, values=CATEGORIES, width=200)
        cat_combo.set(CATEGORIES[0])
        cat_combo.pack(pady=5)

        ctk.CTkLabel(dialog, text="Примечания:").pack(pady=(10, 0))
        notes_entry = ctk.CTkEntry(dialog, width=300)
        notes_entry.pack(pady=5)

        def save():
            try:
                amount = float(amount_entry.get().replace(",", "."))
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректную сумму.")
                return

            d = date_entry.get().strip()
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД.")
                return

            self.db.add_expense(
                week_id=self.current_week_id,
                date=d,
                amount=amount,
                category=cat_combo.get(),
                notes=notes_entry.get().strip()
            )
            dialog.destroy()
            self._load_expenses_table()
            self._update_summary()

        ctk.CTkButton(dialog, text="Сохранить", command=save, width=150).pack(pady=20)

    def _delete_selected_expense(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Нет выбора", "Выберите запись в таблице.")
            return

        item = selected[0]
        expense_id = self.tree_item_to_id.get(item)
        if not expense_id:
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            self.db.delete_expense(expense_id)
            self._load_expenses_table()
            self._update_summary()

    def _start_new_week(self):
        if not self.current_month_id:
            messagebox.showwarning("Нет месяца", "Сначала создайте месяц.")
            return

        weeks = self.db.get_weeks_for_month(self.current_month_id)
        next_num = len(weeks) + 1
        today = date.today().isoformat()

        self.db.add_week(month_id=self.current_month_id, week_num=next_num, start_date=today)
        self._load_weeks_into_combobox()
        messagebox.showinfo("Готово", f"Создана Неделя {next_num} (начало {today})")

    def _start_new_month(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Новый месяц")
        dialog.geometry("420x420")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Дата начала месяца:").pack(pady=(20, 0))
        date_entry = ctk.CTkEntry(dialog, width=200)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Зарплата (€):").pack(pady=(12, 0))
        salary_entry = ctk.CTkEntry(dialog, width=200)
        salary_entry.insert(0, "0")
        salary_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Еда работа (€) — откладывается:").pack(pady=(12, 0))
        food_work_entry = ctk.CTkEntry(dialog, width=200)
        food_work_entry.insert(0, "0")
        food_work_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Еда домашняя (€) — откладывается:").pack(pady=(12, 0))
        food_home_entry = ctk.CTkEntry(dialog, width=200)
        food_home_entry.insert(0, "0")
        food_home_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Заметка (необязательно):").pack(pady=(12, 0))
        note_entry = ctk.CTkEntry(dialog, width=250)
        note_entry.pack(pady=5)

        def create():
            d = date_entry.get().strip()
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты.")
                return

            try:
                salary = float(salary_entry.get().replace(",", ".") or 0)
                food_work = float(food_work_entry.get().replace(",", ".") or 0)
                food_home = float(food_home_entry.get().replace(",", ".") or 0)
            except ValueError:
                messagebox.showerror("Ошибка", "Неверные суммы.")
                return

            month_id = self.db.add_month(
                start_date=d,
                salary=salary,
                note=note_entry.get().strip()
            )

            # Откладываем еду в отдельные кошельки
            self.db.set_category_budget(month_id, "Еда работа", food_work)
            self.db.set_category_budget(month_id, "Еда домашняя", food_home)

            # Первая неделя
            self.db.add_week(month_id=month_id, week_num=1, start_date=d)

            dialog.destroy()
            self._load_months_into_combobox()
            messagebox.showinfo("Готово", f"Новый месяц создан с {d}")

        ctk.CTkButton(dialog, text="Создать месяц", command=create, width=160).pack(pady=25)

    def on_closing(self):
        self.db.close()
        self.destroy()