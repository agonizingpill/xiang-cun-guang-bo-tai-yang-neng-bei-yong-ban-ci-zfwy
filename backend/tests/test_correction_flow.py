import json

import pytest
from fastapi import HTTPException

from core.worker import process_once
from domain import battery_logs_service as battery_service
from domain import reserves_service as reserves_service
from domain import switchcards_service as card_service
from domain.airslots_model import airslots
from domain.battery_logs_model import battery_logs
from domain.battery_logs_schemas import CorrectMeter
from domain.reserves_model import forecast_runs, reserves
from domain.reserves_schemas import ForecastWh, SaveReserve
from domain.switchcards_model import switchcards
from domain.switchcards_schemas import Handover, IssueSwitch
from core.records import insert, get, scan


SLOT = {'code': 'AIR-17', 'title': '晚间村讯', 'hour': 18, 'license': '本地插播', 'offline': True}


def seed_meter(conn, meter='BAT-04', hours=range(48), value=90.0):
    if not any(x['code'] == 'AIR-17' for x in scan(conn, airslots)):
        insert(conn, airslots, **SLOT)
    for hour in hours:
        insert(conn, battery_logs, code=f'WH-{meter}-{hour:02d}', meter=meter, hour=hour,
               load_wh=value + (hour % 3) * 5, clear=True, verified=True, revision=1)


def forecast_token(conn, user, meter='BAT-04'):
    queued = reserves_service.forecast_wh(conn, user,
                                          ForecastWh(airslot='AIR-17', meter=meter, clear=True))
    process_once(timeout=1)
    return queued['token']


def save_reserve(conn, user, token, code='RV-1'):
    return reserves_service.save_reserve(conn, user, SaveReserve(code=code, token=token))


def issue_card(conn, user, reserve='RV-1', code='SW-1', approved=1000.0):
    return card_service.issue_switch(conn, user,
        IssueSwitch(code=code, reserve=reserve, source='本地时钟', approved_wh=approved))


# ---------- 更正后旧预测立即失效，重算前各环节被拦 ----------

def test_correction_invalidates_ready_forecast_and_blocks_all_downstream(conn, redis, reviewer):
    seed_meter(conn)
    token = forecast_token(conn, reviewer)
    save_reserve(conn, reviewer, token)
    issue_card(conn, reviewer)

    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=123.0, clear=False))

    assert get(conn, forecast_runs, token, field='token')['status'] == 'stale'
    assert json.loads(redis.get(f'compute:{token}'))['status'] == 'stale'
    assert get(conn, reserves, 'RV-1')['status'] == 'stale'
    assert get(conn, switchcards, 'SW-1')['basis_status'] == 'stale'
    row = get(conn, battery_logs, 'WH-BAT-04-10')
    assert row['load_wh'] == 123.0 and row['clear'] is False and row['revision'] == 2

    # 重算前：备案被拦（旧 token 已失效）
    with pytest.raises(HTTPException) as exc:
        reserves_service.save_reserve(conn, reviewer, SaveReserve(code='RV-2', token=token))
    assert exc.value.status_code == 409

    # 重算前：签发被拦
    with pytest.raises(HTTPException) as exc:
        issue_card(conn, reviewer, reserve='RV-1', code='SW-2')
    assert exc.value.status_code == 409

    # 重算前：未交接卡的交接被退回
    with pytest.raises(HTTPException) as exc:
        card_service.handover(conn, reviewer, Handover(card='SW-1', note='WR-77 闭台交接'))
    assert exc.value.status_code == 409


def test_queued_forecast_stays_stale_after_worker_finishes(conn, redis, reviewer):
    seed_meter(conn)
    queued = reserves_service.forecast_wh(conn, reviewer,
                                          ForecastWh(airslot='AIR-17', meter='BAT-04', clear=True))
    token = queued['token']
    # 任务还在队列里时更正读数
    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-05', load_wh=42.0, clear=True))
    assert get(conn, forecast_runs, token, field='token')['status'] == 'stale'

    process_once(timeout=1)  # worker 此时才算完
    assert json.loads(redis.get(f'compute:{token}'))['status'] == 'stale'

    with pytest.raises(HTTPException) as exc:
        reserves_service.save_reserve(conn, reviewer, SaveReserve(code='RV-X', token=token))
    assert exc.value.status_code == 409


def test_new_forecast_allows_new_card_after_correction(conn, redis, reviewer):
    seed_meter(conn)
    old_token = forecast_token(conn, reviewer)
    save_reserve(conn, reviewer, old_token)
    issue_card(conn, reviewer)
    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=123.0, clear=True))

    new_token = forecast_token(conn, reviewer)
    assert new_token != old_token
    assert get(conn, forecast_runs, new_token, field='token')['status'] == 'queued'
    save_reserve(conn, reviewer, new_token, code='RV-2')
    issue_card(conn, reviewer, reserve='RV-2', code='SW-2', approved=1000.0)
    assert get(conn, switchcards, 'SW-2')['basis_status'] == 'current'
    # 旧卡仍留档并保持待重算标记
    assert get(conn, switchcards, 'SW-1')['basis_status'] == 'stale'


# ---------- 更正与交接并发：行锁决定先后 ----------

def test_handover_first_then_correction_keeps_card_archived(conn, redis, reviewer):
    seed_meter(conn)
    token = forecast_token(conn, reviewer)
    save_reserve(conn, reviewer, token)
    issue_card(conn, reviewer)
    # 先交接成功
    card_service.handover(conn, reviewer, Handover(card='SW-1', note='WR-77 闭台交接'))

    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=123.0, clear=True))

    card = get(conn, switchcards, 'SW-1')
    assert card['state'].startswith('已闭台 WR-77')
    assert card['basis_status'] == 'current'  # 已交接卡连同原预测依据留档，不回退


def test_correction_first_then_handover_is_rejected(conn, redis, reviewer):
    seed_meter(conn)
    token = forecast_token(conn, reviewer)
    save_reserve(conn, reviewer, token)
    issue_card(conn, reviewer)
    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=123.0, clear=True))

    with pytest.raises(HTTPException) as exc:
        card_service.handover(conn, reviewer, Handover(card='SW-1', note='WR-78 闭台交接'))
    assert exc.value.status_code == 409
    assert get(conn, switchcards, 'SW-1')['state'] == '值守签发'


# ---------- 更正接口自身的约束 ----------

def test_correction_requires_verified_row(conn, redis, reviewer, operator):
    seed_meter(conn)
    insert(conn, battery_logs, code='WH-NEW', meter='BAT-99', hour=0, load_wh=10.0,
           clear=True, verified=False, revision=1)
    with pytest.raises(HTTPException) as exc:
        battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-NEW', load_wh=11.0, clear=True))
    assert exc.value.status_code == 409


def test_correction_only_touches_forecasts_of_same_meter(conn, redis, reviewer):
    seed_meter(conn, meter='BAT-04')
    seed_meter(conn, meter='BAT-11')
    token_04 = forecast_token(conn, reviewer, meter='BAT-04')
    token_11 = forecast_token(conn, reviewer, meter='BAT-11')

    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=123.0, clear=True))

    assert get(conn, forecast_runs, token_04, field='token')['status'] == 'stale'
    assert get(conn, forecast_runs, token_11, field='token')['status'] != 'stale'


def test_repeated_correction_bumps_revision(conn, redis, reviewer):
    seed_meter(conn)
    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=123.0, clear=True))
    battery_service.correct_meter(conn, reviewer, CorrectMeter(record='WH-BAT-04-10', load_wh=124.0, clear=False))
    row = get(conn, battery_logs, 'WH-BAT-04-10')
    assert row['revision'] == 3 and row['load_wh'] == 124.0 and row['clear'] is False
