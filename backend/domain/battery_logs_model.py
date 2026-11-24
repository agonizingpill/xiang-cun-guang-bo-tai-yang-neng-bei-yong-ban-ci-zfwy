from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


battery_logs = Table('battery_logs', metadata,
    Column('code', String(64), primary_key=True),
    Column('meter', String(160), nullable=False),
    Column('hour', Integer, nullable=False),
    Column('load_wh', Float, nullable=False),
    Column('clear', Boolean, nullable=False),
    Column('verified', Boolean, nullable=False),
    CheckConstraint('hour between 0 and 47'),
    CheckConstraint('load_wh >= 0'),
)
