# app.py — concise Expense Tracker (Tkinter + SQLite)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv, os

DB = "expenses.db"

# --- Database helper (very small) ---
class DB:
    def __init__(self, path=DB):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
                             id INTEGER PRIMARY KEY, date TEXT, category TEXT,
                             description TEXT, amount REAL, created_at TEXT)""")
        self.conn.commit()
    def add(self, date, cat, desc, amt):
        self.conn.execute("INSERT INTO expenses (date,category,description,amount,created_at) VALUES (?,?,?,?,?)",
                          (date,cat,desc,amt,datetime.utcnow().isoformat()))
        self.conn.commit()
    def delete(self, id_):
        self.conn.execute("DELETE FROM expenses WHERE id=?", (id_,)); self.conn.commit()
    def all(self, where="", params=()):
        sql = "SELECT * FROM expenses " + (("WHERE " + where) if where else "") + " ORDER BY date DESC"
        return self.conn.execute(sql, params).fetchall()
    def summary(self, ym=None):
        if ym:
            return self.conn.execute("SELECT category, SUM(amount) AS total FROM expenses WHERE substr(date,1,7)=? GROUP BY category",
                                     (ym,)).fetchall()
        return self.conn.execute("SELECT category, SUM(amount) AS total FROM expenses GROUP BY category").fetchall()

# --- App ---
class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.db = DB()
        self._build()
        self._load()

    def _build(self):
        frm = ttk.Frame(self, padding=8); frm.pack(fill="x")
        self.d = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.c = tk.StringVar(); self.a = tk.StringVar(); self.s = tk.StringVar()
        ttk.Entry(frm, textvariable=self.d, width=12).grid(row=0,column=0, padx=4)
        ttk.Entry(frm, textvariable=self.c, width=16).grid(row=0,column=1, padx=4)
        ttk.Entry(frm, textvariable=self.a, width=10).grid(row=0,column=2, padx=4)
        ttk.Entry(frm, textvariable=self.s, width=40).grid(row=0,column=3, padx=4)
        ttk.Button(frm, text="Add", command=self.add).grid(row=0,column=4, padx=4)

        ctrl = ttk.Frame(self, padding=(8,0)); ctrl.pack(fill="x")
        self.filter = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.filter, width=20).pack(side="left", padx=4)
        ttk.Button(ctrl, text="Filter", command=self.apply_filter).pack(side="left")
        ttk.Button(ctrl, text="Clear", command=self.clear_filter).pack(side="left", padx=4)
        ttk.Button(ctrl, text="Export CSV", command=self.export).pack(side="right")

        cols = ("id","date","category","description","amount")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c,width in zip(cols,(50,100,120,360,80)):
            self.tree.heading(c,text=c.title()); self.tree.column(c,width=width,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=8)

        btns = ttk.Frame(self, padding=8); btns.pack(fill="x")
        ttk.Button(btns, text="Delete Selected", command=self.delete).pack(side="left")
        ttk.Button(btns, text="Monthly Summary", command=self.monthly).pack(side="right")

    def _load(self, where="", params=()):
        for r in self.tree.get_children(): self.tree.delete(r)
        for row in self.db.all(where, params):
            self.tree.insert("", "end", values=(row["id"], row["date"], row["category"], row["description"], f"{row['amount']:.2f}"))

    def add(self):
        date = self.d.get().strip(); cat = self.c.get().strip() or "Other"
        desc = self.s.get().strip()
        try:
            amt = float(self.a.get().strip())
        except:
            messagebox.showerror("Error","Enter valid amount"); return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except:
            messagebox.showerror("Error","Date format YYYY-MM-DD"); return
        self.db.add(date,cat,desc,amt); self._load(); self.c.set(""); self.a.set(""); self.s.set("")

    def delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("No selection","Select a row"); return
        id_ = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete ID {id_}?"):
            self.db.delete(id_); self._load()

    def apply_filter(self):
        f = self.filter.get().strip()
        if not f: self._load(); return
        if len(f)==7 and f[4]=="-":
            self._load("substr(date,1,7)=?", (f,))
        else:
            pat = f"%{f}%"; self._load("category LIKE ? OR date LIKE ? OR description LIKE ?", (pat,pat,pat))

    def clear_filter(self):
        self.filter.set(""); self._load()

    def export(self):
        rows = self.db.all()
        if not rows: messagebox.showinfo("No data","No rows to export"); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["id","date","category","description","amount","created_at"])
            for r in rows: w.writerow([r["id"],r["date"],r["category"],r["description"],r["amount"],r["created_at"]])
        messagebox.showinfo("Exported", f"Saved {len(rows)} rows to {os.path.basename(path)}")

    def monthly(self):
        win = tk.Toplevel(self); win.title("Monthly Summary")
        ttk.Label(win, text="Month (YYYY-MM) or leave blank:").pack(padx=8,pady=6)
        mv = tk.StringVar(); ttk.Entry(win, textvariable=mv).pack(padx=8)
        txt = tk.Text(win, width=50, height=12); txt.pack(padx=8,pady=6)
        def show():
            ym = mv.get().strip() or None
            if ym:
                try: datetime.strptime(ym+"-01","%Y-%m-%d")
                except: messagebox.showerror("Invalid","Use YYYY-MM"); return
            rows = self.db.summary(ym)
            txt.delete("1.0","end")
            if not rows: txt.insert("end","No data\n"); return
            total=0
            for r in rows:
                txt.insert("end", f"{r['category']}: {r['total']:.2f}\n"); total+=r['total']
            txt.insert("end", f"\nTotal: {total:.2f}")
        ttk.Button(win, text="Show", command=show).pack(pady=(0,8))

if __name__ == "__main__":
    ExpenseApp().mainloop()
