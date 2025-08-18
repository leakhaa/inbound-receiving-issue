import sqlite3
from tabulate import tabulate
import pandas as pd

# ----------------------------
# Connect to SQLite DB
# ----------------------------
def get_db_connection():
    conn = sqlite3.connect("D:\genai\current ai\database\warehouse.db")
    conn.row_factory = sqlite3.Row  # enables dict-like row access
    return conn

# ----------------------------
# Fetch rows from any table
# ----------------------------
def fetch_rows(table, where_clause="", params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM {table} {where_clause}"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]  # extract column names
    conn.close()
    return pd.DataFrame(rows, columns=columns)


# ----------------------------
# Record existence check
# ----------------------------
def record_exists(table, where_col, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT 1 FROM {table} WHERE {where_col} = ? LIMIT 1"
    cursor.execute(query, (value,))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

# ----------------------------
# Markdown table snippet (terminal/email)
# ----------------------------
def format_table_snippet(rows, highlight_key=None, highlight_value=None):
    if not rows:
        return "No matching records found."
    table = [dict(row) for row in rows]
    if highlight_key and highlight_value:
        for row in table:
            if str(row.get(highlight_key)) == str(highlight_value):
                row[highlight_key] = f"**{highlight_value}**"  # bold highlight
    return tabulate(table, headers="keys", tablefmt="grid")

# ----------------------------
# HTML snippet for email with highlight
# ----------------------------
def generate_html_snippet(data, highlight_column=None, highlight_value=None):
    df = pd.DataFrame(data)
    if highlight_column and highlight_value:
        df[highlight_column] = df[highlight_column].apply(
            lambda x: f"<mark>{x}</mark>" if str(x) == str(highlight_value) else x
        )
    return df.to_html(index=False, escape=False)

# ----------------------------
# Parse Excel to DataFrame
# ----------------------------
def parse_excel_to_df(filepath):
    return pd.read_excel(filepath)

# ----------------------------
# Insert pallet data from Excel
# ----------------------------
def insert_pallets_from_excel(df, po_id, asn_id):
    conn = get_db_connection()
    cur = conn.cursor()
    for _, row in df.iterrows():
        pallet_id = str(row["pallet_id"])
        qty = int(row["qty"])
        cur.execute("INSERT OR IGNORE INTO po_line (po_id, pallet_id, qty) VALUES (?, ?, ?)", (po_id, pallet_id, qty))
        cur.execute("INSERT OR IGNORE INTO asn_line (asn_id, po_id, pallet_id, qty) VALUES (?, ?, ?, ?)", (asn_id, po_id, pallet_id, qty))
    conn.commit()
    conn.close()
