# Episode 2 - load Oracle's prebuilt ONNX embedding model
# from the PC into the database. Model zip: "all_MiniLM_L12_v2"
# link in the Oracle AI Vector Search User's Guide; unzip first.
import os, time, oracledb

con = oracledb.connect(
    user="ADMIN",
    password=os.environ["ADB_ADMIN_PASSWORD"],
    dsn="enlab26ai_low",
    config_dir="wallet", wallet_location="wallet",
    wallet_password=os.environ["ADB_WALLET_PASSWORD"])
cur = con.cursor()

data = open("all_MiniLM_L12_v2.onnx", "rb").read()
print(f"model file: {len(data) / 1048576:.0f} MB")

start = time.time()
blob = con.createlob(oracledb.DB_TYPE_BLOB)
blob.write(data)
cur.execute("""
  begin
    dbms_data_mining.import_onnx_model(
      'ALL_MINILM_L12_V2', :model,
      json('{"function":"embedding",
             "embeddingOutput":"embedding",
             "input":{"input":["DATA"]}}'));
  end;""", model=blob)
print(f"imported in {time.time() - start:.0f} s")
