# Step 1 - lab compartment + what is free?
# needs: pip install oci   and   ~/.oci/config (API key)
import oci

config = oci.config.from_file()        # reads ~/.oci/config
identity = oci.identity.IdentityClient(config)
tenancy = config["tenancy"]

# a compartment just for the lab
comps = identity.list_compartments(tenancy).data
lab = next((c for c in comps if c.name == "en-lab"
            and c.lifecycle_state == "ACTIVE"), None)
if lab is None:
    lab = identity.create_compartment(
        oci.identity.models.CreateCompartmentDetails(
            compartment_id=tenancy, name="en-lab",
            description="Always Free lab")).data
print("compartment:", lab.name, lab.lifecycle_state)

# which database versions are offered on Always Free?
db = oci.database.DatabaseClient(config)
versions = db.list_autonomous_db_versions(
    tenancy, db_workload="OLTP").data
for v in versions:
    print("version", v.version,
          "| always free:", v.is_free_tier_enabled)

# how many Always Free autonomous databases may I have?
limits = oci.limits.LimitsClient(config)
for l in limits.list_limit_values(
        tenancy, service_name="database",
        name="adb-free-count").data:
    print("limit", l.name, "=", l.value,
          "per", l.scope_type.lower())
