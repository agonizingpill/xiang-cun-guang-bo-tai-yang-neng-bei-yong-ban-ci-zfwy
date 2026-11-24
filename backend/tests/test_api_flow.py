from fastapi.testclient import TestClient

from core.app import app
from core.db import engine, metadata, transaction
from core.records import insert
from core.worker import process_once
from domain.airslots_model import airslots


def make_client():
    metadata.drop_all(engine)
    return TestClient(app)


def login(client, role):
    resp = client.post('/auth/login', json={'email': f'{role}@demo.test', 'password': 'DemoC0de!2026'})
    assert resp.status_code == 200
    return {'Authorization': 'Bearer ' + resp.json()['token']}


def prepare_meter(client, headers, meter='BAT-T'):
    with transaction() as conn:
        insert(conn, airslots, code='AIR-17', title='晚间村讯', hour=18, license='本地插播', offline=True)
    for hour in range(48):
        body = {'code': f'WH-T-{hour:02d}', 'meter': meter, 'hour': hour,
                'load_wh': 90.0 + (hour % 3) * 5, 'clear': True}
        assert client.post('/battery_logs/log-charge', json=body, headers=headers).status_code == 200
        assert client.post('/battery_logs/approve-meter', json={'record': body['code']},
                           headers=headers).status_code == 200


def forecast_and_save(client, headers, reserve_code):
    resp = client.post('/reserves/forecast-wh',
                       json={'airslot': 'AIR-17', 'meter': 'BAT-T', 'clear': True}, headers=headers)
    assert resp.status_code == 200, resp.text
    token = resp.json()['token']
    process_once(timeout=1)
    detail = client.get('/compute/' + token, headers=headers).json()
    assert detail['status'] == 'ready'
    resp = client.post('/reserves/save-reserve', json={'code': reserve_code, 'token': token}, headers=headers)
    assert resp.status_code == 200, resp.text
    return token


def test_full_correction_lifecycle_over_http(conn, redis):
    with make_client() as client:
        reviewer = login(client, 'reviewer')
        operator = login(client, 'operator')
        prepare_meter(client, reviewer)
        token = forecast_and_save(client, reviewer, 'RV-T1')

        resp = client.post('/switchcards/issue-switch',
                           json={'code': 'SW-T1', 'reserve': 'RV-T1', 'source': '本地时钟',
                                 'approved_wh': 1000}, headers=reviewer)
        assert resp.status_code == 200, resp.text

        # 更正接口仅复核员可用
        forbidden = client.post('/battery_logs/correct-meter',
                                json={'record': 'WH-T-10', 'load_wh': 123.0, 'clear': True}, headers=operator)
        assert forbidden.status_code == 403

        # 复核员更正生效
        resp = client.post('/battery_logs/correct-meter',
                           json={'record': 'WH-T-10', 'load_wh': 123.0, 'clear': False}, headers=reviewer)
        assert resp.status_code == 200
        assert resp.json()['revision'] == 2

        # 旧预测任务在 Redis 中已失效
        assert client.get('/compute/' + token, headers=reviewer).json()['status'] == 'stale'
        # 旧评估与未交接卡被标出待重算
        assert client.get('/reserves', headers=reviewer).json()[0]['status'] == 'stale'
        card = next(x for x in client.get('/switchcards', headers=reviewer).json() if x['code'] == 'SW-T1')
        assert card['basis_status'] == 'stale'

        # 重算前：备案、签发、交接全部被拦
        assert client.post('/reserves/save-reserve', json={'code': 'RV-TX', 'token': token},
                           headers=reviewer).status_code == 409
        assert client.post('/switchcards/issue-switch',
                           json={'code': 'SW-T2', 'reserve': 'RV-T1', 'source': '本地时钟',
                                 'approved_wh': 1000}, headers=reviewer).status_code == 409
        assert client.post('/switchcards/handover', json={'card': 'SW-T1', 'note': 'WR-77 闭台交接'},
                           headers=operator).status_code == 409

        # 用新读数重新预测、备案、签发新卡
        forecast_and_save(client, reviewer, 'RV-T2')
        resp = client.post('/switchcards/issue-switch',
                           json={'code': 'SW-T2', 'reserve': 'RV-T2', 'source': '本地时钟',
                                 'approved_wh': 1000}, headers=reviewer)
        assert resp.status_code == 200, resp.text
        new_card = next(x for x in client.get('/switchcards', headers=reviewer).json() if x['code'] == 'SW-T2')
        assert new_card['basis_status'] == 'current'

        # 新卡可正常交接；旧卡仍保留待重算标记留档
        resp = client.post('/switchcards/handover', json={'card': 'SW-T2', 'note': 'WR-78 闭台交接'},
                           headers=operator)
        assert resp.status_code == 200
        assert resp.json()['state'].startswith('已闭台 WR-78')
        old_card = next(x for x in client.get('/switchcards', headers=reviewer).json() if x['code'] == 'SW-T1')
        assert old_card['basis_status'] == 'stale' and old_card['state'] == '值守签发'


def test_handover_before_correction_is_archived_with_original_basis(conn, redis):
    with make_client() as client:
        reviewer = login(client, 'reviewer')
        prepare_meter(client, reviewer)
        forecast_and_save(client, reviewer, 'RV-H1')
        client.post('/switchcards/issue-switch',
                    json={'code': 'SW-H1', 'reserve': 'RV-H1', 'source': '本地时钟', 'approved_wh': 1000},
                    headers=reviewer)
        resp = client.post('/switchcards/handover', json={'card': 'SW-H1', 'note': 'WR-77 闭台交接'},
                           headers=reviewer)
        assert resp.status_code == 200

        resp = client.post('/battery_logs/correct-meter',
                           json={'record': 'WH-T-10', 'load_wh': 123.0, 'clear': True}, headers=reviewer)
        assert resp.status_code == 200

        card = next(x for x in client.get('/switchcards', headers=reviewer).json() if x['code'] == 'SW-H1')
        assert card['state'].startswith('已闭台 WR-77')
        assert card['basis_status'] == 'current'


def test_queued_job_marked_stale_when_worker_finishes(conn, redis):
    with make_client() as client:
        reviewer = login(client, 'reviewer')
        prepare_meter(client, reviewer)
        resp = client.post('/reserves/forecast-wh',
                           json={'airslot': 'AIR-17', 'meter': 'BAT-T', 'clear': True}, headers=reviewer)
        token = resp.json()['token']
        # 任务仍在排队时更正读数
        assert client.post('/battery_logs/correct-meter',
                           json={'record': 'WH-T-10', 'load_wh': 123.0, 'clear': True},
                           headers=reviewer).status_code == 200
        process_once(timeout=1)  # worker 此刻才算完
        assert client.get('/compute/' + token, headers=reviewer).json()['status'] == 'stale'
        assert client.post('/reserves/save-reserve', json={'code': 'RV-Q1', 'token': token},
                           headers=reviewer).status_code == 409
