from contextlib import contextmanager

from sqlalchemy import MetaData, create_engine, inspect, text

from core.config import DATABASE_URL

metadata = MetaData()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 旧版演示库的补充列；metadata.create_all 只建新表，已存在的表需显式补列
_ADDED_COLUMNS = {
    'battery_logs': [('revision', 'INTEGER NOT NULL DEFAULT 1')],
    'reserves': [('status', "VARCHAR(16) NOT NULL DEFAULT 'current'")],
    'switchcards': [('basis_status', "VARCHAR(16) NOT NULL DEFAULT 'current'")],
}

def migrate():
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in existing:
                continue
            present = {column['name'] for column in inspector.get_columns(table)}
            for name, ddl in columns:
                if name not in present:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}'))

@contextmanager
def transaction():
    with engine.begin() as conn:
        yield conn
