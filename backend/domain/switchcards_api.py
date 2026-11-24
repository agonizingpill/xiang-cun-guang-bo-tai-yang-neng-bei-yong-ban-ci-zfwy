from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import switchcards_service as service
from domain.switchcards_model import switchcards
from domain.switchcards_schemas import IssueSwitch, Handover

router = APIRouter()

@router.get('/switchcards')
def list_switchcards(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, switchcards)


@router.post('/switchcards/issue-switch')
def issue_switch(data: IssueSwitch, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.issue_switch(conn, user, data)
        record(conn, user, 'switchcards.issue_switch')
        return output


@router.post('/switchcards/handover')
def handover(data: Handover, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.handover(conn, user, data)
        record(conn, user, 'switchcards.handover')
        return output
