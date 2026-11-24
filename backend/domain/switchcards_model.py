from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


switchcards = Table('switchcards', metadata,
    Column('code', String(64), primary_key=True),
    Column('reserve', String(160), ForeignKey('reserves.code'), nullable=False, unique=True),
    Column('source', String(160), nullable=False),
    Column('approved_wh', Float, nullable=False),
    Column('state', String(160), nullable=False),
    # current 表示依据的预测仍有效；stale 表示读数已更正、等待重算后另签新卡
    Column('basis_status', String(16), nullable=False, server_default='current'),
    CheckConstraint("basis_status in ('current','stale')"),
)
