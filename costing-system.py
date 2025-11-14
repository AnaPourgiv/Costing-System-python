@ -1,243 +0,0 @@
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pandas as pd

# ------------------- دیتابیس و جداول -------------------
def init_db()
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        wage REAL DEFAULT 0,
        electricity REAL DEFAULT 0,
        gas REAL DEFAULT 0,
        water REAL DEFAULT 0,
        overhead REAL DEFAULT 0,
        production_date TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        name TEXT,
        quantity REAL DEFAULT 0,
        rate REAL DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )''')
    conn.commit()
    conn.close()

# ------------------- بارگذاری داده -------------------
def load_products()
    product_list.delete(product_list.get_children())
    conn = sqlite3.connect('data.db')
    for row in conn.execute(SELECT  FROM products)
        product_list.insert(, end, values=row)
    conn.close()

def load_materials()
    material_list.delete(material_list.get_children())
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.id, m.name, m.quantity, m.rate, p.name
        FROM materials m
        JOIN products p ON m.product_id = p.id
    ''')
    for row in cursor.fetchall()
        material_list.insert(, end, values=row)
    conn.close()

# ------------------- عملیات جست‌و‌جو -------------------
def filter_products()
    keyword = search_var.get().strip().lower()
    product_list.delete(product_list.get_children())
    conn = sqlite3.connect('data.db')
    for row in conn.execute(SELECT  FROM products)
        if keyword in row[1].lower()
            product_list.insert(, end, values=row)
    conn.close()

# ------------------- محاسبه قیمت تمام‌شده -------------------
def calculate_total_cost()
    result_tree.delete(result_tree.get_children())
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute(SELECT  FROM products)
    for p in cursor.fetchall()
        pid, name, wage, el, gas, water, overhead, date = p
        cursor.execute(SELECT name, quantity, rate FROM materials WHERE product_id=, (pid,))
        mats = cursor.fetchall()
        total_mat_cost = sum(qr for _, q, r in mats)
        total_cost = total_mat_cost + wage + el + gas + water + overhead
        mats_text = , .join(f{m[0]}({m[1]}x{m[2]}) for m in mats)
        result_tree.insert(, end, values=(pid, name, date, f{total_cost.2f}, mats_text))
    conn.close()

# ------------------- خروجی Excel -------------------
def export_excel()
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
          p.id AS ID, p.name AS Product, p.production_date AS Date,
          COALESCE(SUM(m.quantity  m.rate), 0) AS MaterialCost,
          (p.wage + p.electricity + p.gas + p.water + p.overhead) AS OtherCost,
          COALESCE(SUM(m.quantity  m.rate), 0) +
          (p.wage + p.electricity + p.gas + p.water + p.overhead) AS TotalCost,
          GROUP_CONCAT(m.name  '('  m.quantity  'x'  m.rate  ')', ', ') AS Materials
        FROM products p
        LEFT JOIN materials m ON p.id = m.product_id
        GROUP BY p.id
    ''')
    df = pd.DataFrame(cursor.fetchall(), columns=[d[0] for d in cursor.description])
    df.to_excel('export.xlsx', index=False)
    conn.close()
    messagebox.showinfo(موفق, فایل export.xlsx ذخیره شد)

# ------------------- فرم‌ها و عملیات افزودنویرایشحذف -------------------
def product_entry_win()
    win = tk.Toplevel(root); win.title(ثبت محصول جدید)
    vars = {k tk.DoubleVar() if k!='name' else tk.StringVar()
            for k in ('name','wage','electricity','gas','water','overhead')}
    labels = [نام محصول,دستمزد,برق,گاز,آب,سربار]
    for i, lbl in enumerate(labels)
        tk.Label(win, text=lbl).grid(row=i, column=0, sticky=e)
        tk.Entry(win, textvariable=vars[list(vars.keys())[i]]).grid(row=i, column=1)
    tk.Label(win, text=تاریخ تولید).grid(row=6, column=0)
    date_entry = DateEntry(win, date_pattern='yyyy-mm-dd'); date_entry.grid(row=6,column=1)
    def save()
        try
            conn = sqlite3.connect('data.db'); c = conn.cursor()
            c.execute('''
                INSERT INTO products(name,wage,electricity,gas,water,overhead,production_date)
                VALUES(,,,,,,)
            ''', (vars['name'].get(), vars['wage'].get(), vars['electricity'].get(),
                  vars['gas'].get(), vars['water'].get(), vars['overhead'].get(), date_entry.get()))
            conn.commit(); conn.close()
            messagebox.showinfo(موفق,محصول ثبت شد); load_products(); win.destroy()
        except sqlite3.IntegrityError
            messagebox.showerror(خطا,نام محصول تکراری‌ست)
    tk.Button(win, text=ثبت محصول, command=save).grid(row=7,column=0,columnspan=2,pady=5)

def material_entry_win()
    win = tk.Toplevel(root); win.title(ثبت ماده اولیه جدید)
    conn = sqlite3.connect('data.db'); products = conn.execute(SELECT id,name FROM products).fetchall(); conn.close()
    prod_var = tk.StringVar()
    ttk.Combobox(win, textvariable=prod_var, values=[p[1] for p in products]).grid(row=0,column=1)
    tk.Label(win,text=محصول).grid(row=0,column=0)
    name_var, qty_var, rate_var = tk.StringVar(), tk.DoubleVar(), tk.DoubleVar()
    for i, lbl in enumerate([نام ماده,مقدار,نرخ])
        tk.Label(win,text=lbl).grid(row=i+1,column=0); tk.Entry(win,
            textvariable=[name_var, qty_var, rate_var][i]).grid(row=i+1,column=1)
    def save()
        pn = prod_var.get(); pid = next((p[0] for p in products if p[1]==pn), None)
        if not pid
            return messagebox.showerror(خطا,محصول را انتخاب کنید)
        conn = sqlite3.connect('data.db'); c = conn.cursor()
        c.execute('INSERT INTO materials(product_id,name,quantity,rate) VALUES(,,,)',
                  (pid, name_var.get(), qty_var.get(), rate_var.get()))
        conn.commit(); conn.close(); messagebox.showinfo(موفق,ثبت شد)
        load_materials(); win.destroy()
    tk.Button(win,text=ثبت ماده,command=save).grid(row=4,column=0,columnspan=2,pady=5)

def delete_product()
    sel = product_list.selection()
    if not sel return messagebox.showerror(خطا,یک محصول انتخاب کنید)
    pid = product_list.item(sel[0])['values'][0]
    conn = sqlite3.connect('data.db'); c = conn.cursor()
    c.execute(DELETE FROM products WHERE id=, (pid,))
    c.execute(DELETE FROM materials WHERE product_id=, (pid,))
    conn.commit(); conn.close()
    messagebox.showinfo(موفق,حذف شد); load_products(); load_materials()

def delete_material()
    sel = material_list.selection()
    if not sel return messagebox.showerror(خطا,یک ماده انتخاب کنید)
    mid = material_list.item(sel[0])['values'][0]
    conn = sqlite3.connect('data.db'); conn.execute(DELETE FROM materials WHERE id=, (mid,))
    conn.commit(); conn.close()
    messagebox.showinfo(موفق,ماده حذف شد); load_materials()

def edit_material()
    sel = material_list.selection()
    if not sel return messagebox.showerror(خطا,یک ماده انتخاب کنید)
    vals = material_list.item(sel[0])['values']
    edit = tk.Toplevel(root); edit.title(ویرایش ماده)
    vars = {'name' tk.StringVar(value=vals[1]), 'quantity' tk.DoubleVar(value=vals[2]),
            'rate' tk.DoubleVar(value=vals[3])}
    for i, txt in enumerate([نام,مقدار,نرخ])
        tk.Label(edit,text=txt).grid(row=i,column=0)
        tk.Entry(edit,textvariable=vars[list(vars.keys())[i]]).grid(row=i,column=1)
    def save()
        conn = sqlite3.connect('data.db'); c = conn.cursor()
        c.execute('UPDATE materials SET name=, quantity=, rate= WHERE id=',
                  (vars['name'].get(), vars['quantity'].get(), vars['rate'].get(), vals[0]))
        conn.commit(); conn.close()
        messagebox.showinfo(موفق,ویرایش شد); load_materials(); edit.destroy()
    tk.Button(edit, text=ذخیره, command=save).grid(row=3,column=0,columnspan=2)

# ------------------- رابط گرافیکی -------------------
root = tk.Tk(); root.title(سیستم هزینه‌یابی); root.geometry(1000x700)

# جست‌وجو
search_var = tk.StringVar()
search_fr = tk.Frame(root); search_fr.pack(fill=x, padx=10, pady=5)
tk.Label(search_fr, text=جست‌وجو محصول).pack(side=left)
tk.Entry(search_fr, textvariable=search_var).pack(side=left, padx=5)
tk.Button(search_fr, text=اعمال فیلتر, command=filter_products).pack(side=left, padx=5)
tk.Button(search_fr, text=نمایش همه, command=load_products).pack(side=left, padx=5)

# قاب اصلی برای جدول‌ها
main_frame = tk.Frame(root)
main_frame.pack(fill=x, padx=10, pady=5)

# ----- قاب محصولات -----
product_frame = tk.LabelFrame(main_frame, text=محصولات)
product_frame.pack(side=left, fill=both, expand=True, padx=5)

product_list = ttk.Treeview(product_frame, columns=(id,name,wage,electricity,gas,water,overhead,production_date), show=headings, height=10)
for c in product_list[columns]
    product_list.heading(c, text=c)
    product_list.column(c, width=90)
product_list.pack(fill=x)

product_btns = tk.Frame(product_frame)
product_btns.pack(pady=5)
tk.Button(product_btns, text=افزودن محصول, command=product_entry_win).pack(side=left, padx=5)
tk.Button(product_btns, text=حذف محصول, command=delete_product).pack(side=left, padx=5)

# ----- قاب مواد اولیه -----
material_frame = tk.LabelFrame(main_frame, text=مواد اولیه)
material_frame.pack(side=left, fill=both, expand=True, padx=5)

material_list = ttk.Treeview(material_frame, columns=(id,name,quantity,rate,product), show=headings, height=10)
for c in material_list[columns]
    material_list.heading(c, text=c)
    material_list.column(c, width=90)
material_list.pack(fill=x)

material_btns = tk.Frame(material_frame)
material_btns.pack(pady=5)
tk.Button(material_btns, text=افزودن ماده, command=material_entry_win).pack(side=left, padx=5)
tk.Button(material_btns, text=حذف ماده, command=delete_material).pack(side=left, padx=5)
tk.Button(material_btns, text=ویرایش ماده, command=edit_material).pack(side=left, padx=5)

# گزارش هزینه
rf = tk.LabelFrame(root, text=گزارش قیمت تمام‌شده); rf.pack(fill=x, padx=10, pady=5)
result_tree = ttk.Treeview(rf, columns=(id,name,date,total_cost,materials), show=headings, height=6)
for c in result_tree[columns]
    result_tree.heading(c, text=c); result_tree.column(c, width=180)
result_tree.pack(fill=x, expand=True)

tk.Frame(root).pack(pady=10)
tk.Button(root, text=محاسبه هزینه, command=calculate_total_cost).pack(side=left, padx=5)
tk.Button(root, text=خروجی Excel, command=export_excel).pack(side=left, padx=5)

# ------------------- شروع -------------------
init_db()
load_products()
load_materials()
root.mainloop()