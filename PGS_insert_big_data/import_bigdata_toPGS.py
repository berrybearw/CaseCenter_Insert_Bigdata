import tkinter as tk
from tkinter import filedialog, messagebox
import psycopg2
import os

# PostgreSQL 連線設定（請填你的資料庫資訊）
DB_CONFIG = {
    "dbname": "casecenter_202108",
    "user": "AllenChang@HUB-SU0-ONE",
    "password": "admin",
    "host": "localhost",
    "port": 5438
}

TABLE_NAME = "cc_annotation"
COLUMN_NAME = "data"
ID_COLUMN = "sldid"

# 自動 Insert or Update
def upsert_file_to_postgres(file_path, sldid):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute(
            f"""
            INSERT INTO hub.{TABLE_NAME} ({ID_COLUMN}, {COLUMN_NAME})
            VALUES (%s, %s)
            ON CONFLICT ({ID_COLUMN})
            DO UPDATE SET {COLUMN_NAME} = EXCLUDED.{COLUMN_NAME}
            """,
            (sldid, content)
        )

        conn.commit()
        cur.close()
        conn.close()
        return True, f"已成功寫入（insert 或 update）sldid = {sldid}。"
    except Exception as e:
        return False, f"資料庫錯誤：{str(e)}"

# 搜尋名稱並顯示在列表
def search_name():
    keyword = entry_keyword.get().strip()
    if not keyword:
        messagebox.showwarning("提示", "請輸入搜尋關鍵字")
        return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT guid, name FROM hub.cc_slidetable WHERE name ILIKE %s LIMIT 50", (f"%{keyword}%",))
        results = cur.fetchall()
        cur.close()
        conn.close()

        listbox_results.delete(0, tk.END)
        if results:
            for row in results:
                guid, name = row
                listbox_results.insert(tk.END, f"{guid} | {name}")
        else:
            listbox_results.insert(tk.END, "無結果")
    except Exception as e:
        messagebox.showerror("錯誤", f"查詢失敗：{str(e)}")

# 選擇列表項目，自動填入 sldid
def on_select_result(event):
    selection = listbox_results.curselection()
    if selection:
        selected_text = listbox_results.get(selection[0])
        if "|" in selected_text:
            guid = selected_text.split("|")[0].strip()
            entry_sldid.delete(0, tk.END)
            entry_sldid.insert(0, guid)

# GUI：選檔 + 執行
def choose_file():
    sldid = entry_sldid.get().strip()
    if not sldid:
        messagebox.showwarning("警告", "請輸入 sldid")
        return

    file_path = filedialog.askopenfilename(
        filetypes=[("JSON or Text Files", "*.json *.txt"), ("All files", "*.*")]
    )
    if file_path and os.path.exists(file_path):
        success, msg = upsert_file_to_postgres(file_path, sldid)
        if success:
            messagebox.showinfo("成功", msg)
        else:
            messagebox.showerror("錯誤", msg)

# GUI 畫面設定
root = tk.Tk()
root.title("PostgreSQL 檔案上傳工具 (Insert or Update)")
root.geometry("500x500")

# 1. 輸入關鍵字查詢 guid/name
label_keyword = tk.Label(root, text="輸入關鍵字查詢 name：")
label_keyword.pack(pady=(10, 5))

entry_keyword = tk.Entry(root, width=40)
entry_keyword.pack()

btn_search = tk.Button(root, text="搜尋名稱", command=search_name)
btn_search.pack(pady=5)

listbox_results = tk.Listbox(root, width=60, height=10)
listbox_results.pack()
listbox_results.bind("<<ListboxSelect>>", on_select_result)

# 2. 選擇後填入 sldid
label_sldid = tk.Label(root, text="請輸入或選擇 sldid（主鍵）：")
label_sldid.pack(pady=(15, 5))

entry_sldid = tk.Entry(root, width=40)
entry_sldid.pack()

# 3. 上傳按鈕
btn_select = tk.Button(root, text="選擇檔案並上傳", command=choose_file)
btn_select.pack(pady=20)

root.mainloop()
