# Select AI with a FREE Gemini API key (AI Studio, billing disabled). The key comes from an env variable.
import os, oracledb

con = oracledb.connect(user="ADMIN", password=os.environ["ADB_ADMIN_PASSWORD"],
                       dsn=os.environ.get("ADB_NAME", "enlab26ai") + "_low",
                       config_dir="wallet", wallet_location="wallet",
                       wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()

# re-runnable: remove an older profile / credential first
for drop in ("begin dbms_cloud_ai.drop_profile('OPS_AI', force => true); end;",
             "begin dbms_cloud.drop_credential('GEMINI_CRED'); end;"):
    try:
        cur.execute(drop)
    except oracledb.DatabaseError:
        pass

# 1) allow the database to call the Gemini endpoint
cur.execute("""begin dbms_network_acl_admin.append_host_ace(
                 host => 'generativelanguage.googleapis.com',
                 ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                                     principal_name => 'ADMIN',
                                     principal_type => xs_acl.ptype_db)); end;""")

# 2) store the key as a credential (stored encrypted, never in a script)
cur.execute("""begin dbms_cloud.create_credential(
                 credential_name => 'GEMINI_CRED',
                 username        => 'GOOGLE',
                 password        => :k); end;""", k=os.environ["GEMINI_API_KEY"])

# 3) an AI profile: which model, and which tables it may look at
cur.execute("""begin dbms_cloud_ai.create_profile(
  profile_name => 'OPS_AI',
  attributes   => '{"provider": "google",
                    "credential_name": "GEMINI_CRED",
                    "model": "%s",
                    "comments": true,
                    "object_list": [{"owner": "ADMIN", "name": "APP_JOB_LOG"},
                                    {"owner": "ADMIN", "name": "SESSION_MONITOR"},
                                    {"owner": "ADMIN", "name": "LOCK_MONITOR"},
                                    {"owner": "ADMIN", "name": "ASH_SNAPSHOT"},
                                    {"owner": "ADMIN", "name": "JOB_HISTORY"}]}'); end;"""
            % os.environ.get("GEMINI_MODEL", "gemini-flash-latest"))
print("Select AI profile OPS_AI ready")
