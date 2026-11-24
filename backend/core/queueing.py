import json
from uuid import uuid4

from fastapi import HTTPException
from redis import Redis

from core.config import REDIS_URL

broker = Redis.from_url(REDIS_URL, decode_responses=True)
QUEUE = 'compute_requests'

def submit(user, payload):
    token = uuid4().hex
    item = {'token': token, 'owner': user['sub'], 'input': payload}
    with broker.pipeline() as pipe:
        pipe.set(f'compute:{token}', json.dumps({'owner': user['sub'], 'status': 'queued'}), ex=86400)
        pipe.rpush(QUEUE, json.dumps(item))
        pipe.execute()
    return {'token': token, 'status': 'queued'}

def view(user, token):
    raw = broker.get(f'compute:{token}')
    if raw is None:
        raise HTTPException(404, detail='计算任务不存在或已过期')
    record = json.loads(raw)
    if record.get('owner') != user['sub'] and user['role'] != 'reviewer':
        raise HTTPException(403, detail='仅提交人和复核员可查看计算')
    return {k: v for k, v in record.items() if k != 'owner'}

def result(user, token):
    data = view(user, token)
    if data['status'] == 'stale':
        raise HTTPException(409, detail='预测依据的读数已更正，请用新读数重新预测')
    if data['status'] != 'ready':
        raise HTTPException(409, detail='等待计算完成后再提交')
    return data

def is_stale(token):
    raw = broker.get(f'compute:{token}')
    return raw is not None and json.loads(raw).get('status') == 'stale'

def mark_stale(token):
    """令一个计算任务立即失效；排队中的任务算完也保持 stale。"""
    key = f'compute:{token}'
    raw = broker.get(key)
    if raw is None:
        broker.set(key, json.dumps({'status': 'stale'}), ex=86400)
        return
    record = json.loads(raw)
    record['status'] = 'stale'
    broker.set(key, json.dumps(record, allow_nan=False), ex=86400)
