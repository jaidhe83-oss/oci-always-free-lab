# Step 5 - destroy the database, then prove nothing is left
import time, oci

config = oci.config.from_file()
identity = oci.identity.IdentityClient(config)
db = oci.database.DatabaseClient(config)
lab = next(c for c in identity.list_compartments(
               config["tenancy"]).data
           if c.name == "en-lab"
           and c.lifecycle_state == "ACTIVE")
adb = next(a for a in db.list_autonomous_databases(
               lab.id, display_name="enlab26ai").data
           if a.lifecycle_state == "AVAILABLE")

assert adb.is_free_tier   # safety: only the Always Free DB
db.delete_autonomous_database(adb.id)
print(time.strftime("%H:%M:%S"), "delete requested")

start = time.time()
oci.wait_until(
    db, db.get_autonomous_database(adb.id),
    "lifecycle_state", "TERMINATED",
    max_wait_seconds=1800, succeed_on_not_found=True)
print(time.strftime("%H:%M:%S"),
      f"TERMINATED ({time.time() - start:.0f} s)")

left = [a for a in db.list_autonomous_databases(lab.id).data
        if a.lifecycle_state != "TERMINATED"]
print("autonomous databases left in en-lab:", len(left))
