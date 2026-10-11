"""Parameterized DB adapter. PostgreSQL in deployment; SQLite only for offline tests."""
import sqlite3
import re
from contextlib import contextmanager
import psycopg

class Row(dict):
    def __getitem__(self,key):
        return list(self.values())[key] if isinstance(key,int) else super().__getitem__(key)

def row_factory(cursor):
    names=[column.name for column in cursor.description] if cursor.description else []
    return lambda values:Row(zip(names,values))

class Postgres:
    def __init__(self,connection): self.connection=connection
    def execute(self,sql,params=()):
        if sql=='BEGIN IMMEDIATE':
            # Transaction-scoped global demo lock: shared across HTTP/MCP/workers.
            return self.connection.execute('SELECT pg_advisory_xact_lock(81973542)')
        if sql.startswith('INSERT OR IGNORE'):
            sql=sql.replace('INSERT OR IGNORE','INSERT')+' ON CONFLICT DO NOTHING'
        if isinstance(params,dict): sql=re.sub(r':([a-z_]+)',r'%(\1)s',sql)
        else: sql=sql.replace('?','%s')
        return self.connection.execute(sql,params)
    def executescript(self,sql):
        for statement in sql.split(';'):
            if statement.strip(): self.execute(statement)

@contextmanager
def connect(database):
    if database.startswith(('postgresql://','postgres://')):
        with psycopg.connect(database,row_factory=row_factory,connect_timeout=10) as db:
            yield Postgres(db)
    else:
        db=sqlite3.connect(database,timeout=10)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db: yield db
        finally: db.close()
