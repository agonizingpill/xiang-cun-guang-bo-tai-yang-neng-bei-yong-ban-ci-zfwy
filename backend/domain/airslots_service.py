from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.airslots_model import airslots
from domain.battery_logs_model import battery_logs
from domain.reserves_model import reserves
from domain.switchcards_model import switchcards


def mark_offline(conn, user, data):
    current=get(conn,airslots,data.airslot,lock=True)
    return update(conn,airslots,current['code'],offline=data.offline)
