import sqlite3

conn = sqlite3.connect("warehouse.db")  # Ensure this is the same DB used in models.py
cur = conn.cursor()

# Create PO Header Table
cur.execute("""
CREATE TABLE IF NOT EXISTS po_header (
    po_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Create ASN Header Table
cur.execute("""
CREATE TABLE IF NOT EXISTS asn_header (
    asn_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Create ASN Line Table (optional for completeness)
cur.execute("""
CREATE TABLE IF NOT EXISTS asn_line (
    pallet_id TEXT,
    po_id TEXT,
    asn_id TEXT,
    quantity INTEGER,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print(" Tables created successfully.")
