# ask the database in plain English:  python 10_ask.py showsql "which jobs timed out?"
# actions: showsql (the SQL it wrote) | runsql (the result) | narrate (an answer in words) | explainsql
import os, sys, oracledb

con = oracledb.connect(user="ADMIN", password=os.environ["ADB_ADMIN_PASSWORD"],
                       dsn=os.environ.get("ADB_NAME", "enlab26ai") + "_low",
                       config_dir="wallet", wallet_location="wallet",
                       wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()
action, question = sys.argv[1], sys.argv[2]
print("Q:", question, f"[{action}]")
answer = cur.callfunc("dbms_cloud_ai.generate", oracledb.DB_TYPE_CLOB,
                      keyword_parameters={"prompt": question, "profile_name": "OPS_AI", "action": action})
print(answer.read())
