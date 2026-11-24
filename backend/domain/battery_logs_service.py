from sqlalchemy import select

from core.queueing import mark_stale
from core.records import get, insert, need, scan, update
from domain.battery_logs_model import battery_logs
from domain.reserves_model import reserves, forecast_runs
from domain.switchcards_model import switchcards


def log_charge(conn, user, data):
    need(0<=data.hour<48 and 0<=data.load_wh<=8000,'小时或电量超界')
    need(not any(x['hour']==data.hour and x['meter']==data.meter for x in scan(conn,battery_logs)),
         '电表整点已记录')
    return insert(conn,battery_logs,**data.model_dump(),verified=False,revision=1)


def approve_meter(conn, user, data):
    get(conn,battery_logs,data.record,lock=True)
    return update(conn,battery_logs,data.record,verified=True)


def correct_meter(conn, user, data):
    """复核员更正已审签读数；更正一生效，用过该读数的旧预测全部失效。"""
    row=get(conn,battery_logs,data.record,lock=True)
    need(row['verified'],'只能更正已审签的抄表读数，未审签记录请先核对签认')
    need(0<=data.load_wh<=8000,'电量超界')
    corrected=update(conn,battery_logs,data.record,load_wh=data.load_wh,clear=data.clear,
                     revision=row['revision']+1)

    runs=[dict(x) for x in conn.execute(
            select(forecast_runs).where(forecast_runs.c.meter==row['meter'],
                                        forecast_runs.c.status!='stale').with_for_update()).mappings()]
    tokens=[x['token'] for x in runs]
    for token in tokens:
        conn.execute(forecast_runs.update().where(forecast_runs.c.token==token).values(status='stale'))
        # 排队中的任务算完也保持 stale
        mark_stale(token)

    if tokens:
        # 已备案的旧评估失效，拦住重算前的签发与交接
        conn.execute(reserves.update().where(reserves.c.token.in_(tokens)).values(status='stale'))
        # 已闭台交接的卡不动：连同原预测依据留档；只退回未交接卡
        conn.execute(switchcards.update()
                     .where(switchcards.c.reserve.in_(select(reserves.c.code).where(reserves.c.token.in_(tokens))),
                            switchcards.c.state=='值守签发',
                            switchcards.c.basis_status=='current')
                     .values(basis_status='stale'))
    return corrected
