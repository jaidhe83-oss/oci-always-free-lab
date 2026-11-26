# ask 26ai what happened:  python 11_investigate.py 10:00     (the time users complained about)
import os, sys, time, oracledb

con = oracledb.connect(user="ADMIN", password=os.environ["ADB_ADMIN_PASSWORD"],
                       dsn=os.environ.get("ADB_NAME", "enlab26ai") + "_low",
                       config_dir="wallet", wallet_location="wallet",
                       wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()
t = sys.argv[1]
QUESTIONS = [
    ("narrate", f"Users say the order jobs timed out around {t} today. What happened?"),
    ("runsql",  f"For each minute between 5 minutes before and 6 minutes after {t} today, how many order job runs were OK and how many timed out?"),
    ("runsql",  "Which order job runs timed out, with their start time, elapsed time and error message?"),
    ("runsql",  "While the order jobs were waiting, which session were they blocked by, and what module and event did that blocking session have?"),
    ("runsql",  f"Which scheduled jobs started within one minute of {t} today, and how long did they run?"),
    ("runsql",  "Which session held locks on the ORDERS table for the longest time, and how many seconds?"),
    ("showsql", "Which session held locks on the ORDERS table for the longest time, and how many seconds?"),
    ("narrate", "What was the root cause of the order job timeouts, and how should we fix it?"),
]
for action, q in QUESTIONS:
    print("=" * 100)
    print(f"Q [{action}]: {q}")
    t0 = time.time()
    try:
        a = cur.callfunc("dbms_cloud_ai.generate", oracledb.DB_TYPE_CLOB,
                         keyword_parameters={"prompt": q, "profile_name": os.environ.get("AI_PROFILE", "OPS_AI"), "action": action})
        print(a.read() if a else "(no answer)")
    except oracledb.DatabaseError as e:
        print("ERROR:", str(e).splitlines()[0])
    print(f"--- {time.time() - t0:.1f} s", flush=True)
    time.sleep(20)   # free tier: stay under the requests-per-minute limit
