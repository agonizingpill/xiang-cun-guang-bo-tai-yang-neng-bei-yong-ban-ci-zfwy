from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


switchcards = Table('switchcards', metadata,
    Column('code', String(64), primary_key=True),
    Column('reserve', String(160), ForeignKey('reserves.code'), nullable=False, unique=True),
    Column('source', String(160), nullable=False),
    Column('approved_wh', Float, nullable=False),
    Column('state', String(160), nullable=False),
)
