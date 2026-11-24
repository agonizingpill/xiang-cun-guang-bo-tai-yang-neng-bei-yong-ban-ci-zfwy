from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.airslots_model import airslots
from domain.battery_logs_model import battery_logs
from domain.reserves_model import reserves
from domain.switchcards_model import switchcards


def log_charge(conn, user, data):
    need(0<=data.hour<48 and 0<=data.load_wh<=8000,'小时或电量超界')
    need(not any(x['hour']==data.hour and x['meter']==data.meter for x in scan(conn,battery_logs)),
         '电表整点已记录')
    return insert(conn,battery_logs,**data.model_dump(),verified=False)


def approve_meter(conn, user, data):
    get(conn,battery_logs,data.record,lock=True)
    return update(conn,battery_logs,data.record,verified=True)
