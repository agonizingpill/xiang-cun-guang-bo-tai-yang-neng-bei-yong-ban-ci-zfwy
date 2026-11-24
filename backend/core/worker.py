import json
from pathlib import Path
from traceback import print_exc

from core.queueing import QUEUE, broker, is_stale
from domain.learning import calculate

pulse = Path('/tmp/compute-heartbeat')

def process_once(timeout=2):
    """处理一个排队任务，返回是否取到任务。读数更正后排队任务算完也保持 stale。"""
    broker.ping()
    pulse.touch()
    item = broker.blmove(QUEUE, f'{QUEUE}:processing', timeout=timeout, src='LEFT', dest='RIGHT')
    if item is None:
        return False
    job = json.loads(item)
    # 读数更正可能在任务排队期间生效：落结果前再核对一次失效标记
    if is_stale(job['token']):
        broker.lrem(f'{QUEUE}:processing', 1, item)
        pulse.touch()
        return True
    status = {'owner': job['owner'], 'input': job['input']}
    try:
        status.update(status='ready', result=calculate(job['input']))
    except ValueError as exc:
        status.update(status='rejected', detail=str(exc))
    except Exception:
        print_exc()
        status.update(status='rejected', detail='计算失败，请检查输入和 worker 日志')
    if is_stale(job['token']):
        status['status'] = 'stale'
    with broker.pipeline() as pipe:
        pipe.set(f'compute:{job["token"]}', json.dumps(status, allow_nan=False), ex=86400)
        pipe.lrem(f'{QUEUE}:processing', 1, item)
        pipe.execute()
    pulse.touch()
    return True

def serve():
    while True:
        process_once()

if __name__ == '__main__':
    for raw in broker.lrange(f'{QUEUE}:processing', 0, -1):
        with broker.pipeline() as pipe:
            pipe.lpush(QUEUE, raw)
            pipe.lrem(f'{QUEUE}:processing', 1, raw)
            pipe.execute()
    serve()
