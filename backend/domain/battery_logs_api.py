from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import battery_logs_service as service
from domain.battery_logs_model import battery_logs
from domain.battery_logs_schemas import LogCharge, ApproveMeter

router = APIRouter()

@router.get('/battery_logs')
def list_battery_logs(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, battery_logs)


@router.post('/battery_logs/log-charge')
def log_charge(data: LogCharge, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.log_charge(conn, user, data)
        record(conn, user, 'battery_logs.log_charge')
        return output


@router.post('/battery_logs/approve-meter')
def approve_meter(data: ApproveMeter, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.approve_meter(conn, user, data)
        record(conn, user, 'battery_logs.approve_meter')
        return output
