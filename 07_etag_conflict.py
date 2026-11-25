# Episode 3 - does a stale ETAG really get rejected?
import os, oracledb

con = oracledb.connect(
    user="ADMIN",
    password=os.environ["ADB_ADMIN_PASSWORD"],
    dsn="enlab26ai_low",
    config_dir="wallet", wallet_location="wallet",
    wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()
ETAG = "select json_value(data, '$._metadata.etag') from cluster_dv"

cur.execute(ETAG)
old = cur.fetchone()[0]
print("app A reads the document, etag =", old)

cur.execute("update cl_nodes set state = 'DOWN' where node_id = 11")
con.commit()
cur.execute(ETAG)
print("app B changes it  -> new etag  =", cur.fetchone()[0])

stale = ('{"_metadata":{"etag":"%s"},"_id":1,'
         '"name":"stale-write","version":"23.26.4","nodes":['
         '{"nodeId":11,"host":"rac-alpha","state":"UP"},'
         '{"nodeId":12,"host":"rac-bravo","state":"UP"}]}' % old)
try:
    cur.execute("""update cluster_dv d set data = :doc
                   where d.data."_id" = 1""", doc=stale)
    con.commit()
    print("app A writes with the OLD etag -> ACCEPTED")
except oracledb.DatabaseError as e:
    con.rollback()
    print("app A writes with the OLD etag -> REJECTED:",
          str(e).splitlines()[0])

cur.execute("""select c.name, n.hostname, n.state
                 from clusters c join cl_nodes n
                   on n.cluster_id = c.cluster_id
                order by n.node_id""")
for r in cur:
    print(r)
