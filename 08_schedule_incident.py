# schedule the incident: python 08_schedule_incident.py "2026-11-27 10:00"   (time is IST)
import os, sys, oracledb

con = oracledb.connect(user="ADMIN", password=os.environ["ADB_ADMIN_PASSWORD"],
                       dsn=os.environ.get("ADB_NAME", "enlab26ai") + "_low",
                       config_dir="wallet", wallet_location="wallet",
                       wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()
cur.execute("""begin schedule_incident(
                 to_timestamp_tz(:t || ' +05:30', 'YYYY-MM-DD HH24:MI TZH:TZM')); end;""",
            t=sys.argv[1])
cur.execute("""select job_name, to_char(next_run_date, 'YYYY-MM-DD HH24:MI:SS TZH:TZM'), state
                 from user_scheduler_jobs order by next_run_date, job_name""")
for job, at, state in cur:
    print(f"{job:16} {at}  {state}")
