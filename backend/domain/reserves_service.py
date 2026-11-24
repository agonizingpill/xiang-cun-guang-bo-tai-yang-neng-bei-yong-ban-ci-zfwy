from core.queueing import submit, result
from core.records import get, insert, need, scan
from domain.airslots_model import airslots
from domain.battery_logs_model import battery_logs
from domain.reserves_model import reserves, forecast_runs


def forecast_wh(conn, user, data):
    slot=get(conn,airslots,data.airslot)
    rows=sorted([x for x in scan(conn,battery_logs) if x['meter']==data.meter and x['verified']],
                key=lambda x:x['hour'])
    need(len(rows)>=36 and all(y['hour']-x['hour']==1 for x,y in zip(rows,rows[1:])), '要有连续三十六小时审签读数')
    queued=submit(user,{'window':slot,'rows':rows,'clear':data.clear})
    # 登记读数血缘，更正其中任一读数时即令本预测失效
    insert(conn,forecast_runs,token=queued['token'],meter=data.meter,
           basis=[{'code':x['code'],'hour':x['hour'],'load_wh':x['load_wh'],'clear':x['clear']} for x in rows],
           status='queued')
    return queued


def save_reserve(conn, user, data):
    run=result(user,data.token)
    lineage=get(conn,forecast_runs,data.token,lock=True,field='token')
    need(lineage['status']!='stale','预测依据的读数已更正，请用新读数重新预测')
    window=run['input']['window']; stats=run['result']
    need(get(conn,airslots,window['code'])['hour']==window['hour'], '节目时间已变')
    conn.execute(forecast_runs.update().where(forecast_runs.c.token==data.token).values(status='ready'))
    return insert(conn,reserves,code=data.code,airslot=window['code'],plan_wh=stats['plan_wh'],
                  fallback='本地优先' if window['offline'] else '受控中继',mae=stats['mae'],token=data.token,
                  status='current')
