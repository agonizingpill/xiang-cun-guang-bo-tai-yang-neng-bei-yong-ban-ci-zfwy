import json
from sqlalchemy import func, select

from core.db import transaction
from domain.demo import FIXTURES
from domain.battery_logs_model import battery_logs
from domain.reserves_model import forecast_runs, reserves

def seed():
    sizes = {}
    with transaction() as conn:
        for table, rows in FIXTURES:
            for row in rows:
                present = conn.scalar(select(table.c.code).where(table.c.code == row['code']))
                if present is None:
                    conn.execute(table.insert().values(**row))
            sizes[table.name] = conn.scalar(select(func.count()).select_from(table))
        # 为预置评估补登记读数血缘，使读数更正规则对演示数据同样生效
        run_tokens = {x[0] for x in conn.execute(select(forecast_runs.c.token)).all()}
        logs = [dict(x) for x in conn.execute(
            select(battery_logs).order_by(battery_logs.c.meter, battery_logs.c.hour)).mappings()]
        for reserve in conn.execute(select(reserves)).mappings():
            if reserve['token'] in run_tokens:
                continue
            basis = [{'code': x['code'], 'hour': x['hour'], 'load_wh': x['load_wh'], 'clear': x['clear']}
                     for x in logs]
            meter = logs[0]['meter'] if logs else ''
            conn.execute(forecast_runs.insert().values(token=reserve['token'], meter=meter,
                                                       basis=basis, status='ready'))
        sizes[forecast_runs.name] = conn.scalar(select(func.count()).select_from(forecast_runs))
    return sizes

if __name__ == '__main__':
    print(json.dumps(seed(), ensure_ascii=False, sort_keys=True))
