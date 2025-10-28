# utils.py
import csv, os
from tkinter import messagebox
from tkinter import filedialog

def validate_amount(amount_s):
    """Return (ok, value_or_msg)."""
    try:
        val = float(amount_s.strip())
        return True, val
    except Exception:
        return False, "Enter valid amount"

def validate_date(date_s):
    """Return (ok, msg). Caller can use datetime.strptime to be strict if needed."""
    if not date_s or len(date_s.strip()) != 10:
        return False, "Date format YYYY-MM-DD"
    return True, ""

def export_to_csv(rows, parent):
    """
    rows: iterable of sqlite3.Row or dict-like with keys:
      id, date, category, description, amount, created_at
    parent: tkinter parent window passed to filedialog
    """
    rows = list(rows)
    if not rows:
        messagebox.showinfo("No data", "No rows to export", parent=parent)
        return None

    path = filedialog.asksaveasfilename(parent=parent, defaultextension=".csv",
                                        filetypes=[("CSV","*.csv")])
    if not path:
        return None

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","date","category","description","amount","created_at"])
        for r in rows:
            # r can be sqlite3.Row: supports dict-style access
            w.writerow([r["id"], r["date"], r["category"], r["description"], r["amount"], r["created_at"]])

    # return saved path for caller to show message
    return path
