from core.records import get, insert, need, update
from domain.airslots_model import airslots
from domain.reserves_model import reserves
from domain.switchcards_model import switchcards


def issue_switch(conn, user, data):
    plan=get(conn,reserves,data.reserve,lock=True)
    need(plan['status']=='current','评估依据的读数已更正，请用新预测重新备案后再签发')
    slot=get(conn,airslots,plan['airslot'],lock=True)
    need(data.source in ('本地时钟','台外校时'),'时钟源不在电台名录')
    need(not slot['offline'] or data.source=='本地时钟','版权离线期间只能接本地时钟')
    need(plan['plan_wh']<=data.approved_wh<=1000,'锁定电量必须覆盖建议且在额度内')
    return insert(conn,switchcards,**data.model_dump(),state='值守签发',basis_status='current')


def handover(conn, user, data):
    item=get(conn,switchcards,data.card,lock=True)
    need(item['state']=='值守签发','此备播卡已交接')
    need(item['basis_status']=='current','读数已更正、旧预测失效，本卡待重算，请凭新预测另签新卡后再交接')
    need(data.note.startswith('WR-'),'缺少值守纸本回执编号')
    return update(conn,switchcards,data.card,state='已闭台 '+data.note)
