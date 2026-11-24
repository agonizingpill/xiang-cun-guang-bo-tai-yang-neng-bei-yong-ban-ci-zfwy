from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import reserves_service as service
from domain.reserves_model import reserves
from domain.reserves_schemas import ForecastWh, SaveReserve

router = APIRouter()

@router.get('/reserves')
def list_reserves(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, reserves)


@router.post('/reserves/forecast-wh')
def forecast_wh(data: ForecastWh, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.forecast_wh(conn, user, data)
        record(conn, user, 'reserves.forecast_wh')
        return output


@router.post('/reserves/save-reserve')
def save_reserve(data: SaveReserve, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.save_reserve(conn, user, data)
        record(conn, user, 'reserves.save_reserve')
        return output
