# Step 4 - connect from the PC
# pip install oracledb  (thin mode: no Oracle client needed)
import os, oracledb

con = oracledb.connect(
    user="ADMIN",
    password=os.environ["ADB_ADMIN_PASSWORD"],
    dsn="enlab26ai_low",   # a service from tnsnames.ora
    config_dir="wallet",
    wallet_location="wallet",
    wallet_password=os.environ["ADB_WALLET_PASSWORD"],
)
cur = con.cursor()

cur.execute("select banner_full from v$version")
print(cur.fetchone()[0])

cur.execute("""create table lab_notes (
    id   number generated always as identity primary key,
    note varchar2(100))""")
cur.executemany(
    "insert into lab_notes (note) values (:1)",
    [("Hello from my PC to Oracle 26ai Always Free",),
     ("Cost so far: 0 rupees",)])
con.commit()

for row in cur.execute(
        "select id, note from lab_notes order by id"):
    print(row)
