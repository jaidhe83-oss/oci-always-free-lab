# Step 3 - download the connection wallet
# (keep it private, like a password)
# set ADB_WALLET_PASSWORD first: 8+ chars, letters
# + a number or special character
import os, zipfile, oci

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

M = oci.database.models
resp = db.generate_autonomous_database_wallet(
    adb.id, M.GenerateAutonomousDatabaseWalletDetails(
        password=os.environ["ADB_WALLET_PASSWORD"],
        generate_type="SINGLE"))
with open("wallet.zip", "wb") as f:
    f.write(resp.data.content)
zipfile.ZipFile("wallet.zip").extractall("wallet")

print("wallet files:", " ".join(sorted(os.listdir("wallet"))))
aliases = [l.split("=")[0].strip()
           for l in open("wallet/tnsnames.ora")
           if "=" in l and not l.startswith(" ")]
print("services:", " ".join(aliases))
