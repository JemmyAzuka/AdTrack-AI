import json
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).with_name("adtrack.db")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            source TEXT NOT NULL,
            event_name TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            received_at TEXT DEFAULT CURRENT_TIMESTAMP,
            value REAL DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            order_id TEXT,
            email_hash TEXT,
            fbc TEXT,
            fbp TEXT,
            ttclid TEXT,
            gclid TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            utm_campaign TEXT,
            raw_json TEXT
        )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(occurred_at)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id)")

def insert_event(event: dict):
    init_db()
    fields = ["event_id","source","event_name","occurred_at","value","currency","order_id",
              "email_hash","fbc","fbp","ttclid","gclid","utm_source","utm_medium","utm_campaign"]
    row = {k: event.get(k) for k in fields}
    row["source"] = str(row.get("source") or "unknown")[:80]
    row["event_name"] = str(row.get("event_name") or "conversion")[:120]
    row["occurred_at"] = str(row.get("occurred_at") or pd.Timestamp.utcnow().isoformat())
    row["currency"] = str(row.get("currency") or "USD")[:3].upper()
    row["value"] = float(row.get("value") or 0)
    row["raw_json"] = json.dumps(event, default=str)
    cols = list(row.keys())
    with connect() as con:
        # event_id is the idempotency key. A repeated ID is not inserted twice.
        if row["event_id"]:
            exists = con.execute("SELECT 1 FROM events WHERE event_id=?", (row["event_id"],)).fetchone()
            if exists:
                return False
        con.execute(
            f"INSERT INTO events ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            [row[c] for c in cols]
        )
    return True

def import_events(frame):
    count = skipped = 0
    for event in frame.where(pd.notna(frame), None).to_dict(orient="records"):
        try:
            if insert_event(event): count += 1
            else: skipped += 1
        except Exception:
            skipped += 1
    return count, skipped

def get_events():
    init_db()
    with connect() as con:
        return pd.read_sql_query("""
        SELECT event_id, source, event_name, occurred_at, value, currency, order_id,
               utm_source, utm_medium, utm_campaign, fbc, ttclid
        FROM events ORDER BY occurred_at DESC LIMIT 2000
        """, con)

def get_summary():
    init_db()
    with connect() as con:
        row = con.execute("""
        SELECT COUNT(*) conversions, COALESCE(SUM(value),0) value,
               COUNT(DISTINCT order_id) orders
        FROM events
        """).fetchone()
        duplicates = con.execute("""
        SELECT COUNT(*) FROM (
          SELECT event_id FROM events WHERE event_id IS NOT NULL AND event_id != ''
          GROUP BY event_id HAVING COUNT(*) > 1
        )
        """).fetchone()[0]
    return {"conversions": row["conversions"], "value": row["value"],
            "orders": row["orders"], "duplicates": duplicates}

def get_quality_report():
    df = get_events()
    if df.empty:
        return {"missing_event_id":0,"missing_campaign":0,"duplicate_groups":0,"warnings":[]}
    missing_id = int(df["event_id"].isna().sum() + (df["event_id"] == "").sum())
    missing_campaign = int(df["utm_campaign"].isna().sum() + (df["utm_campaign"] == "").sum())
    dupes = int(df[df["event_id"].notna()].duplicated("event_id").sum())
    warnings = []
    if missing_id: warnings.append(f"{missing_id} events have no event_id; browser/server deduplication may be unreliable.")
    if missing_campaign: warnings.append(f"{missing_campaign} events have no utm_campaign; campaign-level analysis may be limited.")
    return {"missing_event_id":missing_id,"missing_campaign":missing_campaign,
            "duplicate_groups":dupes,"warnings":warnings}
