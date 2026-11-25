# Step 2 - create an Always Free Oracle 26ai Autonomous Database
# set ADB_ADMIN_PASSWORD first: 12-30 chars, upper + lower
# + number, no " and not the word admin
import os, time, oci

config = oci.config.from_file()
identity = oci.identity.IdentityClient(config)
db = oci.database.DatabaseClient(config)
lab = next(c for c in identity.list_compartments(
               config["tenancy"]).data
           if c.name == "en-lab"
           and c.lifecycle_state == "ACTIVE")

details = oci.database.models.CreateAutonomousDatabaseDetails(
    compartment_id=lab.id,
    display_name="enlab26ai",
    db_name="ENLAB26AI",
    is_free_tier=True,      # <- Always Free (else: PAID)
    db_workload="OLTP",
    db_version="26ai",
    admin_password=os.environ["ADB_ADMIN_PASSWORD"],
)
adb = db.create_autonomous_database(details).data
print(time.strftime("%H:%M:%S"), adb.lifecycle_state)

start = time.time()
adb = oci.wait_until(
    db, db.get_autonomous_database(adb.id),
    "lifecycle_state", "AVAILABLE",
    max_wait_seconds=1800).data
took = time.time() - start
print(time.strftime("%H:%M:%S"), adb.lifecycle_state,
      f"({took:.0f} s)")
print("always free:", adb.is_free_tier,
      "| version:", adb.db_version)
