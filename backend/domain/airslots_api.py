from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import airslots_service as service
from domain.airslots_model import airslots
from domain.airslots_schemas import MarkOffline

router = APIRouter()

@router.get('/airslots')
def list_airslots(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, airslots)


@router.post('/airslots/mark-offline')
def mark_offline(data: MarkOffline, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.mark_offline(conn, user, data)
        record(conn, user, 'airslots.mark_offline')
        return output
