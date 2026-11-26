# OCI Always Free Lab: Oracle 26ai for ₹0

Scripts from The Engineer's Notebook series *OCI Always Free Lab*, Episodes 1–4. Every run is create → test → **destroy**, so nothing is left running.

> Independent educational material, not affiliated with or endorsed by Oracle. Run at your own risk, and always check that resources are marked **Always Free**.

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

## Episode 4: Select AI on a real incident ("what happened at 3 PM?")

Order jobs time out because a batch holds row locks. Monitoring records it, then you ask the database in plain English.

1. `python run_sql.py ep4_app.sql`: orders, app log, `app_worker` (`select ... for update wait 3`), `price_batch` (one 2-minute transaction), `schedule_incident`.
2. `python run_sql.py ep4_more_evidence.sql`: `LOCK_MONITOR`, the 5-second monitor, `price_batch_fixed` (commit every 5 rows), `schedule_fixed_run`.
3. `python 08_schedule_incident.py "2026-11-26 15:00"` (IST). App jobs start 5 min before, the batch at the given time.
4. After the run: `python run_sql.py ep4_collect.sql` (copies ASH + shows the evidence).
5. Select AI with a free Gemini key (AI Studio, billing disabled):
   ```
   $env:GEMINI_API_KEY = "..."; $env:GEMINI_MODEL = "gemini-flash-lite-latest"
   python 09_select_ai_setup.py
   python 11_investigate.py 15:00
   ```
6. Optional, paid: `$env:ANTHROPIC_API_KEY = "..."; $env:CLAUDE_MODEL = "claude-opus-4-6"; python 12_select_ai_claude.py`, then `$env:AI_PROFILE = "OPS_AI_CLAUDE"; python 11_investigate.py 15:00`.
7. The fix: `begin schedule_fixed_run(timestamp '... 16:00:00 +05:30'); end;` and compare.

Set `ADB_NAME` if your database is not called `enlab26ai`.

| My result (26 Nov 2026) | |
|---|---|
| Incident | 48 timeouts at 15:00–15:01; blocker SID 2821 (PRICE_BATCH), row locks held 119 s |
| Gemini Flash-Lite (free) | 4 of 7 questions right; wrong root cause (named a victim job, not the blocker) |
| Claude Opus 4.6 (paid, est. < ₹50) | 4 of 7 right; found the real root cause |
| Both missed | "who blocked them?" (wrong wait class + self-join to the idle blocker's ASH rows; ASH did record blocker 2821); longest lock holder (`ORDER BY ... DESC` puts NULLs first) |
| Fix run | 0 timeouts, 0 ASH lock waits |

⚠️ Watch out:
- **The ADB clock is UTC.** The scripts log India time through `ist_now()`; change `Asia/Kolkata` for your zone.
- **26ai lock timeout** for `FOR UPDATE WAIT n` came back as **ORA-00054 + ORA-40097**, not ORA-30006. Catch both.
- **When a Gemini call fails, the Select AI error text contains your API key** (in the URL). Mask logs, and rotate a leaked key.
- `claude-opus-5-5` returned HTTP 400 through Select AI (likely because it rejects sampling settings such as `temperature`); `claude-opus-4-6` works.
- **Free Gemini Flash** may answer 503/429, and each failed call can block for minutes. Use Flash-Lite with pauses.
## Always finish with

```
python 05_destroy.py
```
