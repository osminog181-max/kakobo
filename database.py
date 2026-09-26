import sqlite3
from pathlib import Path
from constants import DB_PATH


class Database:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS incomes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                month_id    INTEGER NOT NULL,
                date        TEXT NOT NULL,
                amount      REAL NOT NULL,
                notes       TEXT DEFAULT '',
                FOREIGN KEY (month_id) REFERENCES months(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS months (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date  TEXT NOT NULL,
                end_date    TEXT,
                salary      REAL DEFAULT 0,
                note        TEXT DEFAULT ''
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS weeks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                month_id    INTEGER NOT NULL,
                week_num    INTEGER NOT NULL,
                start_date  TEXT NOT NULL,
                end_date    TEXT,
                FOREIGN KEY (month_id) REFERENCES months(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                week_id     INTEGER NOT NULL,
                date        TEXT NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                notes       TEXT DEFAULT '',
                FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS category_budgets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                month_id    INTEGER NOT NULL,
                category    TEXT NOT NULL,
                budget      REAL DEFAULT 0,
                UNIQUE(month_id, category),
                FOREIGN KEY (month_id) REFERENCES months(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    def close(self):
        self.conn.close()

    # ---------- Месяцы ----------
    def get_all_months(self):
        return self.conn.execute(
            "SELECT * FROM months ORDER BY start_date DESC"
        ).fetchall()

    def add_month(self, start_date: str, salary: float = 0.0, note: str = ""):
        cur = self.conn.execute(
            "INSERT INTO months (start_date, salary, note) VALUES (?, ?, ?)",
            (start_date, salary, note)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_month(self, month_id: int):
        return self.conn.execute(
            "SELECT * FROM months WHERE id = ?", (month_id,)
        ).fetchone()

    # ---------- Бюджеты ----------
    def set_category_budget(self, month_id: int, category: str, budget: float):
        self.conn.execute("""
            INSERT INTO category_budgets (month_id, category, budget)
            VALUES (?, ?, ?)
            ON CONFLICT(month_id, category) DO UPDATE SET budget = excluded.budget
        """, (month_id, category, budget))
        self.conn.commit()

    def get_category_budgets(self, month_id: int) -> dict:
        cur = self.conn.execute(
            "SELECT category, budget FROM category_budgets WHERE month_id = ?",
            (month_id,)
        )
        return {row["category"]: row["budget"] for row in cur.fetchall()}

    # ---------- Недели ----------
    def get_weeks_for_month(self, month_id: int):
        return self.conn.execute(
            "SELECT * FROM weeks WHERE month_id = ? ORDER BY week_num",
            (month_id,)
        ).fetchall()

    def add_week(self, month_id: int, week_num: int, start_date: str, end_date: str = None):
        cur = self.conn.execute(
            "INSERT INTO weeks (month_id, week_num, start_date, end_date) VALUES (?, ?, ?, ?)",
            (month_id, week_num, start_date, end_date)
        )
        self.conn.commit()
        return cur.lastrowid

    # ---------- Расходы ----------
    def get_expenses_for_week(self, week_id: int):
        return self.conn.execute(
            "SELECT * FROM expenses WHERE week_id = ? ORDER BY date DESC, id DESC",
            (week_id,)
        ).fetchall()

    def add_expense(self, week_id: int, date: str, amount: float, category: str, notes: str = ""):
        cur = self.conn.execute(
            "INSERT INTO expenses (week_id, date, amount, category, notes) VALUES (?, ?, ?, ?, ?)",
            (week_id, date, amount, category, notes)
        )
        self.conn.commit()
        return cur.lastrowid

    def delete_expense(self, expense_id: int):
        self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()

    def get_spent_by_category(self, month_id: int) -> dict:
        cur = self.conn.execute("""
            SELECT e.category, SUM(e.amount) as total
            FROM expenses e
            JOIN weeks w ON e.week_id = w.id
            WHERE w.month_id = ?
            GROUP BY e.category
        """, (month_id,))
        return {row["category"]: row["total"] for row in cur.fetchall()}

    def add_income(self, month_id: int, date: str, amount: float, notes: str = ""):
        cur = self.conn.execute(
            "INSERT INTO incomes (month_id, date, amount, notes) VALUES (?, ?, ?, ?)",
            (month_id, date, amount, notes)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_incomes_for_month(self, month_id: int):
        return self.conn.execute(
            "SELECT * FROM incomes WHERE month_id = ? ORDER BY date DESC, id DESC",
            (month_id,)
        ).fetchall()

    def delete_income(self, income_id: int):
        self.conn.execute("DELETE FROM incomes WHERE id = ?", (income_id,))
        self.conn.commit()

    def get_total_incomes(self, month_id: int) -> float:
        cur = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM incomes WHERE month_id = ?",
            (month_id,)
        )
        return cur.fetchone()["total"]