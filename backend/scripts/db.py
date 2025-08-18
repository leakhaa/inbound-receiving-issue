import sqlite3

DB_PATH = "D:\genai\current ai\database\warehouse.db"  # Update if different

def connect_db():
    return sqlite3.connect(DB_PATH)

def check_asn_exists(asn_id):
    with connect_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM asn_header WHERE asn_id = ?", (asn_id,))
        header_exists = cur.fetchone()
        print(f" checking {asn_id} in the asn header table: {header_exists}")

        cur.execute("SELECT 1 FROM asn_line WHERE asn_id = ?", (asn_id,))
        line_exists = cur.fetchone()
        print(f"checking {asn_id} in the asn line table: {line_exists}")

        cur.execute("SELECT 1 FROM po_line WHERE asn_id = ?", (asn_id,))
        po_line_exists = cur.fetchone()
        print(f"checking {asn_id} in the po line table: {po_line_exists}")

        
    return bool(header_exists and line_exists and po_line_exists)


def check_po_exists(po_id):
    print(f" Checking if PO {po_id} exists in any table...")
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM po_header WHERE po_id = ?", (po_id,))

        header_exists = cur.fetchone()
        print(f" checking {po_id} in the PO header table: {header_exists}")

        cur.execute("SELECT 1 FROM po_line WHERE po_id = ?", (po_id,))
        line_exists = cur.fetchone()
        print(f" checking {po_id} in the po line table: {line_exists}")

        cur.execute("SELECT 1 FROM asn_line WHERE po_id = ?", (po_id,))
        asn_line_exists = cur.fetchone()
        print(f" checking {po_id} in the asn line table: {asn_line_exists}")    

    return bool(header_exists or line_exists or asn_line_exists)

def check_pallet_exists(po_id=None, asn_id=None, pallet_id=None):
    with connect_db() as conn:
        cur = conn.cursor()
        results = []

        if pallet_id:
            cur.execute("SELECT 1 FROM po_line WHERE po_id = ? AND pallet_id = ?", (po_id, pallet_id))
            results.append(cur.fetchone())

        if pallet_id:
            cur.execute("SELECT 1 FROM asn_line WHERE asn_id = ? AND pallet_id = ?", (asn_id, pallet_id))
            results.append(cur.fetchone())

        if any(results):
            row =cur.execute("select po_id from po_line where pallet_id = ?", (pallet_id))
            po_line_sumofqty = cur.execute("select sum(quantity) from po_line where po_id = ?", (row)).fetchone()
            asn_line_sumofqty = cur.execute("select sum(quantity) from asn_line where po_id = ?", (row)).fetchone()
            if po_line_sumofqty != asn_line_sumofqty:
                results = False
    return any(results)

def get_po_vs_asn_qty_summary_forasn(asn_id):
    with connect_db() as conn:
        cur = conn.cursor()

        # From ASN line
        cur.execute("SELECT COUNT(DISTINCT po_id), SUM(quantity) FROM asn_line WHERE asn_id = ?", (asn_id,))
        asn_pallets, asn_qty = cur.fetchone()

        # From PO line
        cur.execute("SELECT COUNT(DISTINCT po_id), SUM(quantity) FROM po_line WHERE asn_id = ?", (asn_id,))
        po_pallets, po_qty = cur.fetchone()

    return {
        "asn_pallets": asn_pallets or 0,
        "asn_qty": asn_qty or 0,
        "po_pallets": po_pallets or 0,
        "po_qty": po_qty or 0
    }

def get_po_vs_asn_qty_summary(po_id):
    with connect_db() as conn:
        cur = conn.cursor()

        # From ASN line
        cur.execute("SELECT COUNT(DISTINCT pallet_id), SUM(quantity) FROM asn_line WHERE po_id = ?", (po_id,))
        asn_pallets, asn_qty = cur.fetchone()

        # From PO line
        cur.execute("SELECT COUNT(DISTINCT pallet_id), SUM(quantity) FROM po_line WHERE po_id = ?", (po_id,))
        po_pallets, po_qty = cur.fetchone()

    return {
        "asn_pallets": asn_pallets or 0,
        "asn_qty": asn_qty or 0,
   
        "po_pallets": po_pallets or 0,
        "po_qty": po_qty or 0
    }

def get_existing_pallet_ids(db_path="warehouse.db") -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT pallet_id FROM ASN_LINE")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def get_all_rows_from_table(table_name, where_clause="", params=()):
    with connect_db() as conn:
        cur = conn.cursor()
        query = f"SELECT * FROM {table_name} {where_clause}"
        cur.execute(query, params)
        return cur.fetchall()
