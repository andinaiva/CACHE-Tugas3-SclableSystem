import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('bank_data.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaksi (
        trx_id TEXT PRIMARY KEY,
        no_rekening TEXT,
        tipe_transaksi TEXT,
        nominal REAL,
        tanggal TEXT,
        status TEXT,
        keterangan TEXT
    )
''')

print("Generating 50,000 banking transactions... please wait.")
types = ["TRANSFER", "WITHDRAWAL", "DEPOSIT", "PAYMENT"]
statuses = ["SUCCESS", "PENDING", "FAILED"]
data = []

for i in range(1, 50001):
    trx_id = f"TRX-{random.randint(100000, 999999)}-{i}"
    rek = f"10584-{random.randint(111000, 111999)}"
    tipe = random.choice(types)
    amt = round(random.uniform(10000, 5000000), 2)
    stat = random.choice(statuses)
    # Generate random date in last 30 days
    date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
    desc = f"Transaction for service code {random.randint(100, 999)}"
    data.append((trx_id, rek, tipe, amt, date, stat, desc))

cursor.executemany('INSERT OR REPLACE INTO transaksi VALUES (?, ?, ?, ?, ?, ?, ?)', data)
conn.commit()
conn.close()
print("Database 'bank_data.db' with 50,000 records is READY!")