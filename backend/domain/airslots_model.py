from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


airslots = Table('airslots', metadata,
    Column('code', String(64), primary_key=True),
    Column('title', String(160), nullable=False),
    Column('hour', Integer, nullable=False),
    Column('license', String(160), nullable=False),
    Column('offline', Boolean, nullable=False),
    CheckConstraint('hour between 0 and 23'),
)
