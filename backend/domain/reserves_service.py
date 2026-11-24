from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.airslots_model import airslots
from domain.battery_logs_model import battery_logs
from domain.reserves_model import reserves
from domain.switchcards_model import switchcards


def forecast_wh(conn, user, data):
    slot=get(conn,airslots,data.airslot)
    rows=sorted([x for x in scan(conn,battery_logs) if x['meter']==data.meter and x['verified']],
                key=lambda x:x['hour'])
    need(len(rows)>=36 and all(y['hour']-x['hour']==1 for x,y in zip(rows,rows[1:])), '要有连续三十六小时审签读数')
    return submit(user,{'window':slot,'rows':rows,'clear':data.clear})


def save_reserve(conn, user, data):
    run=result(user,data.token)
    window=run['input']['window']; stats=run['result']
    need(get(conn,airslots,window['code'])['hour']==window['hour'], '节目时间已变')
    return insert(conn,reserves,code=data.code,airslot=window['code'],plan_wh=stats['plan_wh'],
                  fallback='本地优先' if window['offline'] else '受控中继',mae=stats['mae'],token=data.token)
