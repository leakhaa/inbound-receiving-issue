import sqlite3
from datetime import datetime
from faker import Faker
import random

fake = Faker()
DB_PATH = "warehouse.db"

def connect_db():
    return sqlite3.connect(DB_PATH)

def check_asn_exists(asn_id):
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM asn_header WHERE asn_id = ?", (asn_id,))
        header_exists = cur.fetchone()
        print(f"[DEBUG] asn_header check for {asn_id}: {header_exists}")

        cur.execute("SELECT 1 FROM asn_line WHERE asn_id = ?", (asn_id,))
        line_exists = cur.fetchone()
        print(f"[DEBUG] asn_line check for {asn_id}: {line_exists}")
        result = bool(header_exists and line_exists) 
        if result:
            print(f"[DEBUG] ASN {asn_id} exists in both header and line tables.")
            print(f"")
    return bool(header_exists and line_exists)


def check_po_exists(po_id):
    print(f"[DEBUG] Checking if PO {po_id} exists in any table...")
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM po_header WHERE po_id = ?", (po_id,))
        header_exists = cur.fetchone()
        cur.execute("SELECT 1 FROM po_line WHERE po_id = ?", (po_id,))
        line_exists = cur.fetchone()
        cur.execute("SELECT 1 FROM asn_line WHERE po_id = ?", (po_id,))
        asn_line_exists = cur.fetchone()

    return bool(header_exists or line_exists or asn_line_exists)

def check_pallet_exists(po_id=None, asn_id=None, pallet_id=None):
    with connect_db() as conn:
        cur = conn.cursor()
        results = []

        if po_id:
            cur.execute("SELECT 1 FROM po_line WHERE po_id = ? AND pallet_id = ?", (po_id, pallet_id))
            results.append(cur.fetchone())

        if asn_id:
            cur.execute("SELECT 1 FROM asn_line WHERE asn_id = ? AND pallet_id = ?", (asn_id, pallet_id))
            results.append(cur.fetchone())

    return any(results)

def get_po_vs_asn_qty_summary(po_id):
    with connect_db() as conn:
        cur = conn.cursor()

        # From ASN line
        cur.execute("SELECT COUNT(DISTINCT pallet_id), SUM(qty) FROM asn_line WHERE po_id = ?", (po_id,))
        asn_pallets, asn_qty = cur.fetchone()

        # From PO line
        cur.execute("SELECT COUNT(DISTINCT pallet_id), SUM(qty) FROM po_line WHERE po_id = ?", (po_id,))
        po_pallets, po_qty = cur.fetchone()

    return {
        "asn_pallets": asn_pallets or 0,
        "asn_qty": asn_qty or 0,
        "po_pallets": po_pallets or 0,
        "po_qty": po_qty or 0
    }

# Insert PO (header + line)
def insert_po_data(po_id: str):
    with connect_db() as conn:
        cursor = conn.cursor()

        # Insert into PO_HEADER
        cursor.execute(
            """
            INSERT OR IGNORE INTO po_header (po_id, supplier_name, order_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (po_id, fake.company(), fake.date(), "open"),
        )

        # Insert into PO_LINE
        for _ in range(random.randint(1, 3)):
            cursor.execute(
                """
                INSERT INTO po+line (po_id, item_description, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (po_id, fake.word(), random.randint(10, 100), round(random.uniform(10.0, 100.0), 2)),
            )

        conn.commit()

# Insert ASN (header + line)
def insert_asn_data(asn_id: str):
    with connect_db() as conn:
        cursor = conn.cursor()

        # Insert ASN header
        cursor.execute(
            """
            INSERT OR IGNORE INTO asn_header (asn_id, shipment_date, carrier)
            VALUES (?, ?, ?)
            """,
            (asn_id, fake.date(), fake.company())
        )

        # Insert ASN line
        for _ in range(random.randint(1, 3)):
            po_id = fake.uuid4()[:8]
            pallet_id = fake.uuid4()[:8]
            cursor.execute(
                """
                INSERT INTO asn_line (pallet_id, po_id, asn_id, supplier_reference, last_updated, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    pallet_id,
                    po_id,
                    asn_id,
                    fake.bothify(text="REF-####"),
                    datetime.now().isoformat(),
                    random.randint(1, 50)
                )
            )

        conn.commit()
