# db.py
import sqlite3
import json

class DBManager:
    def __init__(self, dbfile='netinspector.db'):
        self.dbfile = dbfile
        self.conn = sqlite3.connect(self.dbfile, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER,
            data TEXT
        )
        ''')
        self.conn.commit()

    def insert_record(self, ts, payload_dict):
        c = self.conn.cursor()
        c.execute('INSERT INTO packets (ts, data) VALUES (?, ?)', (ts, json.dumps(payload_dict)))
        self.conn.commit()
        return c.lastrowid

    def fetch_latest(self, limit=100):
        c = self.conn.cursor()
        c.execute('SELECT id, ts, data FROM packets ORDER BY id DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        return [{'id': r[0], 'ts': r[1], 'data': json.loads(r[2])} for r in rows]
