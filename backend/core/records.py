from fastapi import HTTPException
from sqlalchemy import select

def need(condition, explanation):
    if not condition:
        raise HTTPException(409, detail=explanation)

def get(conn, table, key, lock=False):
    query = select(table).where(table.c.code == key)
    if lock:
        query = query.with_for_update()
    row = conn.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, detail=f'找不到 {key}')
    return dict(row)

def scan(conn, table):
    return [dict(row) for row in conn.execute(select(table).order_by(table.c.code)).mappings()]

def insert(conn, table, **data):
    conn.execute(table.insert().values(**data))
    return data

def update(conn, table, key, **data):
    conn.execute(table.update().where(table.c.code == key).values(**data))
    return get(conn, table, key)
