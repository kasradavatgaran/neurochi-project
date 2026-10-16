"""Persistent float32 cache, separate from the application's SQLite database."""
import sqlite3
import struct
from pathlib import Path


class EmbeddingCache:
    def __init__(self, path=None):
        self.path = str(path or Path(__file__).with_name('rag_embeddings.db'))
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS embeddings (cache_key TEXT PRIMARY KEY, vector BLOB NOT NULL)')

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def get_many(self, keys):
        if not keys:
            return {}
        with self.connect() as db:
            rows = db.execute('SELECT cache_key,vector FROM embeddings WHERE cache_key IN (' + ','.join('?' for _ in keys) + ')', keys).fetchall()
        return {key: list(struct.unpack('<' + str(len(data)//4) + 'f', data)) for key, data in rows}

    def put_many(self, values):
        with self.connect() as db:
            db.executemany('INSERT OR REPLACE INTO embeddings VALUES (?,?)',
                [(key, struct.pack('<' + str(len(vector)) + 'f', *vector)) for key, vector in values.items()])
