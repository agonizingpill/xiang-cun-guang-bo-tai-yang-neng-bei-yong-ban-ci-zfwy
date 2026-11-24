from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, JSON, String, Table

from core.db import metadata


reserves = Table('reserves', metadata,
    Column('code', String(64), primary_key=True),
    Column('airslot', String(160), ForeignKey('airslots.code'), nullable=False),
    Column('plan_wh', Float, nullable=False),
    Column('fallback', String(160), nullable=False),
    Column('mae', Float, nullable=False),
    Column('token', String(64), nullable=False, unique=True),
    Column('status', String(16), nullable=False, server_default='current'),
    CheckConstraint("status in ('current','stale')"),
)


# 每次预测任务的读数血缘：登记任务所用的抄表记录，更正读数时据此令旧预测失效
forecast_runs = Table('forecast_runs', metadata,
    Column('token', String(64), primary_key=True),
    Column('meter', String(160), nullable=False, index=True),
    Column('basis', JSON, nullable=False),
    Column('status', String(16), nullable=False, server_default='queued'),
    CheckConstraint("status in ('queued','ready','stale','rejected')"),
)
