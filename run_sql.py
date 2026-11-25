# helper - run a .sql file (statements separated by a line with only "/") and print results
import os, sys, time, oracledb

con = oracledb.connect(user="ADMIN", password=os.environ["ADB_ADMIN_PASSWORD"], dsn="enlab26ai_low",
                       config_dir="wallet", wallet_location="wallet",
                       wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()
for stmt in [s.strip() for s in open(sys.argv[1], encoding="utf-8-sig").read().split("\n/\n") if s.strip()]:
    print("SQL>", stmt)
    t = time.time()
    cur.execute(stmt)
    if cur.description:
        rows = cur.fetchall()
        print(" | ".join(c[0] for c in cur.description))
        for r in rows:
            print(" | ".join(str(x) for x in r))
        print(f"({len(rows)} rows, {time.time() - t:.2f} s)\n")
    else:
        con.commit()
        print(f"OK ({cur.rowcount if cur.rowcount > 0 else 'done'}, {time.time() - t:.2f} s)\n")
