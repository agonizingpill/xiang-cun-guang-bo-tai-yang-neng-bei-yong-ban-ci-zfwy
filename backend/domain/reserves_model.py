from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


reserves = Table('reserves', metadata,
    Column('code', String(64), primary_key=True),
    Column('airslot', String(160), ForeignKey('airslots.code'), nullable=False),
    Column('plan_wh', Float, nullable=False),
    Column('fallback', String(160), nullable=False),
    Column('mae', Float, nullable=False),
    Column('token', String(64), nullable=False, unique=True),
)
