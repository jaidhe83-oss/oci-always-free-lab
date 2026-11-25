# OCI Always Free Lab: Oracle 26ai for ₹0

Scripts from The Engineer's Notebook series *OCI Always Free Lab*, Episodes 1–3. Every run is create → test → **destroy**, so nothing is left running.

> Independent educational material, not affiliated with or endorsed by Oracle. Oracle and Oracle Database are trademarks of Oracle and/or its affiliates. Run at your own risk, and always check that resources are marked **Always Free**.

## Before you start

- An Oracle Cloud account. An expired free trial still works on Always Free.
- An API key and `~/.oci/config`. See the *API-key* Short, or Oracle's "Required Keys and OCIDs" page.
- Python 3 with:

  ```
  pip install oci oracledb
  ```

  The OCI **CLI** did not install on Python 3.14 for me (PyYAML build failure). The **Python SDK** (`pip install oci`) works fine.
- Passwords go in environment variables, never in the scripts:

  ```
  # PowerShell
  $env:ADB_ADMIN_PASSWORD  = "..."   # 12-30 chars, upper + lower + number, no ", not "admin"
  $env:ADB_WALLET_PASSWORD = "..."   # 8+ chars, letters + a number or special character
  ```

## Episode 1: create, connect, destroy

| Step | Script | What it does | My result |
|---|---|---|---|
| 1 | `01_setup_check.py` | Finds or creates the compartment `en-lab`, lists the Always Free versions, and reads the limit `adb-free-count` | 19c / 23ai / 26ai offered; limit 2 per region |
| 2 | `02_create_adb.py` | `is_free_tier=True`, `db_version="26ai"`, `db_workload="OLTP"`, then waits for AVAILABLE | 106 s on one run, 1305 s (≈22 min) on another |
| 3 | `03_wallet.py` | Downloads and unzips the wallet into `wallet/` | 9 files; services `_high _medium _low _tp _tpurgent` |
| 4 | `04_connect.py` | python-oracledb thin mode with the wallet; prints the version, creates a table with 2 rows and reads them back | Oracle AI Database 26ai EE 23.26.4.1.0 |
| 5 | `05_destroy.py` | Checks `is_free_tier`, deletes, waits for TERMINATED, then counts what's left | 77 s / 95 s; 0 left |

⚠️ Without `is_free_tier=True` you are asking for a **paid** database.

## Episode 2: AI Vector Search

1. Open the Oracle AI Vector Search User's Guide, find the pretrained ONNX models, and download the **all_MiniLM_L12_v2** zip (Apache 2.0). Unzip it to get `all_MiniLM_L12_v2.onnx` (127 MB).
2. Run `06_load_model.py`. It sends the model as a BLOB to `dbms_data_mining.import_onnx_model`. That took 16 s and 32 s in my two runs.
3. Run `python run_sql.py ep2_vector_search.sql`. It:
   - checks the model;
   - creates a table with a `VECTOR(384, FLOAT32)` column;
   - adds 8 notes and their embeddings;
   - runs three searches;
   - creates an IVF index.

The results were identical in both sessions:

| Query | Top hit | Distance |
|---|---|---|
| "my server got kicked out of the cluster" | node eviction | 0.427 |
| (keyword `LIKE '%kicked out%'`) | (no rows) | — |
| "cannot sign in, password tried too many times" | account locked | 0.324 |
| "disk space problem" | recovery area full, then tablespace full | 0.499 / 0.568 |

Eight notes is a demo, not a benchmark, and the index was not benchmarked.

## Episode 3: JSON-Relational Duality

1. Run `python run_sql.py ep3_duality.sql`. It:
   - creates two tables and a duality view;
   - inserts one JSON document, which becomes 1 + 2 rows;
   - updates a row, which changes the JSON;
   - updates the JSON, which changes the rows.
2. Run `07_etag_conflict.py`. A write that carries a stale ETAG is **rejected** with `ORA-42699`, and nothing is silently overwritten.

## Always finish with

```
python 05_destroy.py
```

## Never commit

Your `~/.oci` key, the `wallet/` folder, the ONNX model or any passwords. The `.gitignore` here blocks the usual ones.
