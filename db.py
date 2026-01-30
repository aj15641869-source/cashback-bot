import sqlite3

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
phone TEXT UNIQUE,
referred_by INTEGER,
referral_count INTEGER DEFAULT 0,
balance INTEGER DEFAULT 0,
joined_date TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments(
user_id INTEGER,
txn_id TEXT,
proof TEXT,
status TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS channels(
channel_id TEXT,
invite TEXT
)
""")

conn.commit()

