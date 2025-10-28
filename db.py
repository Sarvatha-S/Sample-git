# db.py
import sqlite3
from datetime import datetime

DEFAULT_DB = "expenses.db"

class DB:
    """Very small sqlite wrapper to store expenses."""
    def __init__(self, path=DEFAULT_DB):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                date TEXT,
                category TEXT,
                description TEXT,
                amount REAL,
                created_at TEXT
            )
        """)
        self.conn.commit()

    def add(self, date, cat, desc, amt):
        self.conn.execute(
            "INSERT INTO expenses (date,category,description,amount,created_at) VALUES (?,?,?,?,?)",
            (date, cat, desc, amt, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def delete(self, id_):
        self.conn.execute("DELETE FROM expenses WHERE id=?", (id_,))
        self.conn.commit()

    def all(self, where="", params=()):
        sql = "SELECT * FROM expenses " + (("WHERE " + where) if where else "") + " ORDER BY date DESC"
        return self.conn.execute(sql, params).fetchall()

    def summary(self, ym=None):
        if ym:
            return self.conn.execute(
                "SELECT category, SUM(amount) AS total FROM expenses WHERE substr(date,1,7)=? GROUP BY category",
                (ym,)
            ).fetchall()
        return self.conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses GROUP BY category"
        ).fetchall()
