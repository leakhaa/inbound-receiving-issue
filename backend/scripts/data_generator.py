print("Script started")
import sqlite3
from faker import Faker
import random
from datetime import datetime


fake = Faker()
conn = sqlite3.connect("database/edittrack.db")
cursor = conn.cursor()

def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS PO_Header (
        po_id TEXT PRIMARY KEY,
        status TEXT,
        last_updated TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS PO_Line (
        pallet_id TEXT PRIMARY KEY,
        po_id TEXT,
        asn TEXT,
        last_updated TEXT,
        quantity INTEGER)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ASN_Header (
        asn TEXT PRIMARY KEY,
        supplier_reference TEXT,
        last_updated TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ASN_Line (
        pallet_id TEXT PRIMARY KEY,
        po_id TEXT,
        asn TEXT,
        supplier_reference TEXT,
        last_updated TEXT,
        quantity INTEGER)''')
    conn.commit()

def generate_data():
    print("Generating synthetic warehouse data...\n")
    for _ in range(5):  # 5 ASNs
        asn = f"0{fake.random_number(digits=4)}"
        supplier_ref = fake.bothify(text='???###')
        cursor.execute("INSERT INTO ASN_Header VALUES (?, ?, ?)", 
                       (asn, supplier_ref, str(datetime.now())))
        print(f"[OK] Created ASN: {asn} with supplier_ref: {supplier_ref}")

        for _ in range(2):  # 2 POs per ASN
            po_id = f"2{fake.random_number(digits=9)}"
            status = random.choice(['inprogress', 'received', 'hold'])
            cursor.execute("INSERT INTO PO_Header VALUES (?, ?, ?)", 
                           (po_id, status, str(datetime.now())))
            print(f"   PO: {po_id} ({status})")

            for _ in range(random.randint(2, 4)):  # pallets per PO
                pallet_id = f"5{fake.random_number(digits=14)}"
                quantity = random.randint(1, 5)
                cursor.execute("INSERT INTO PO_Line VALUES (?, ?, ?, ?, ?)", 
                               (pallet_id, po_id, asn, str(datetime.now()), quantity))
                cursor.execute("INSERT INTO ASN_Line VALUES (?, ?, ?, ?, ?, ?)", 
                               (pallet_id, po_id, asn, supplier_ref, str(datetime.now()), quantity))
                print(f"      Pallet: {pallet_id}, Qty: {quantity}")

    conn.commit()
    print("\n Data inserted successfully!")

create_tables()
generate_data()
conn.close()
