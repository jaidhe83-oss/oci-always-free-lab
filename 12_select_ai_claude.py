# A second Select AI profile on a PAID model (Anthropic Claude) - same 5 tables, same questions.
# Needs env ANTHROPIC_API_KEY. Costs a few cents per question (estimate before you run it).
import os, oracledb

con = oracledb.connect(user="ADMIN", password=os.environ["ADB_ADMIN_PASSWORD"],
                       dsn=os.environ.get("ADB_NAME", "enlab26ai") + "_low",
                       config_dir="wallet", wallet_location="wallet",
                       wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()
for drop in ("begin dbms_cloud_ai.drop_profile('OPS_AI_CLAUDE', force => true); end;",
             "begin dbms_cloud.drop_credential('CLAUDE_CRED'); end;"):
    try:
        cur.execute(drop)
    except oracledb.DatabaseError:
        pass

cur.execute("""begin dbms_network_acl_admin.append_host_ace(
                 host => 'api.anthropic.com',
                 ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                                     principal_name => 'ADMIN',
                                     principal_type => xs_acl.ptype_db)); end;""")
cur.execute("""begin dbms_cloud.create_credential(
                 credential_name => 'CLAUDE_CRED',
                 username        => 'ANTHROPIC',
                 password        => :k); end;""", k=os.environ["ANTHROPIC_API_KEY"])
cur.execute("""begin dbms_cloud_ai.create_profile(
  profile_name => 'OPS_AI_CLAUDE',
  attributes   => '{"provider": "anthropic",
                    "credential_name": "CLAUDE_CRED",
                    "model": "%s",
                    "comments": true,
                    "object_list": [{"owner": "ADMIN", "name": "APP_JOB_LOG"},
                                    {"owner": "ADMIN", "name": "SESSION_MONITOR"},
                                    {"owner": "ADMIN", "name": "LOCK_MONITOR"},
                                    {"owner": "ADMIN", "name": "ASH_SNAPSHOT"},
                                    {"owner": "ADMIN", "name": "JOB_HISTORY"}]}'); end;"""
            % os.environ.get("CLAUDE_MODEL", "claude-opus-5-5"))
print("Select AI profile OPS_AI_CLAUDE ready")
