# 乡村广播太阳能备用班次

岭声乡村广播的节目组和电源值守共用一张备播卡，在版权离线时段安排本地校时与蓄电余量。

## 现场工作与联系人

模拟客户为岭声乡村广播合作社。广播时刻表、蓄电日志、用量周期预测、备用机优先级；节目版权离线时段只能接本地时钟。

- 节目时段表 `airslots`，字段为 `title`（节目）、`hour`（起播小时）、`license`（节目源许可）、`offline`（离线时段）。模型约束位于 `backend/domain/airslots_model.py`，规则位于 `airslots_service.py`。
- 蓄电班记与测量 `battery_logs`，字段为 `meter`（电表编号）、`hour`（两日内整点）、`load_wh`（用量 Wh）、`clear`（天空晴）、`verified`（抄表审核）、`revision`（更正版次）。模型约束位于 `backend/domain/battery_logs_model.py`，规则位于 `battery_logs_service.py`。
- 备用分钟核算 `reserves`，字段为 `airslot`（节目时段）、`plan_wh`（计划备用 Wh）、`fallback`（备用源优先级）、`mae`（时间验证MAE Wh）、`token`（计算号）、`status`（评估状态）。预测任务的读数血缘登记在 `forecast_runs`。模型约束位于 `backend/domain/reserves_model.py`，规则位于 `reserves_service.py`。
- 班组备播卡 `switchcards`，字段为 `reserve`（备用评估）、`source`（实际时钟源）、`approved_wh`（锁定备用 Wh）、`state`（状态）、`basis_status`（预测依据，待重算时为 stale）。模型约束位于 `backend/domain/switchcards_model.py`，规则位于 `switchcards_service.py`。

团队为模拟的6 人广播合作社值守组，负责两个电源档位的备播。

值守员用节目表和电池抄数安排断电时段。周期负荷难从表格读出，漏掉一小时会扭曲拟合，离线版权段容易误选台外时钟。

节目时刻表和已签电量日志进入估计，接班人拿到有限额与时钟源的备用卡。

### 一天的业务操作

1. 07:00 确认 AIR-17 晚间村讯版权离线。
2. 08:00 班组登记 BAT-11 整点 88.4 Wh。
3. 09:00 核对 BAT-04 两日班记。
4. 11:20 用 24 小时 Fourier 基回测末 6 小时。
5. 15:00 签发 RV-24 备用电量评估。
6. 17:45 台外时钟请求被拦后改用本地时钟。
7. 22:10 持 WR-77 完成闭台交接。

### 读数更正与重算

值守组发现已审签电量抄错时，由复核员在蓄电班记页提交更正（`/battery_logs/correct-meter`），版次 `revision` 累加：

1. 更正一生效，`forecast_runs` 中用过该电表读数的旧预测全部标记失效（含 Redis 计算任务，排队中的任务算完也保持 `stale`）。
2. 重算完成前，旧评估的备案、依据旧评估签发备播卡、以及未交接卡的闭台交接都会被拦下并返回 409。
3. 更正与交接同时提交时，由行锁顺序决定：先交接成功的卡连同原预测依据留档、不再回退；先更正则交接被退回，备播卡标出“待重算”。
4. 备播卡页面对待重算的卡高亮标注，复核员用更正后的读数重新预测、备案后可签发新卡并正常交接。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://127.0.0.1:18317`。FastAPI OpenAPI 在 `http://127.0.0.1:19317/docs`。
Compose 运行 Nginx、Python FastAPI、独立 Redis 消费进程、SQL 数据库和 Redis，SQL 与 Redis 使用命名卷。
本机开发时，在 Python 3.11 环境安装 `backend/requirements.txt` 后从 backend 目录运行 `uvicorn core.app:app`。须提供 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，`SEED_DEMO` 控制演示初始化。

| 演示账号 | 权限 |
|---|---|
| operator@demo.test | 提交领域记录和计算请求 |
| reviewer@demo.test | 提交记录并执行有业务约束的复核操作 |
| viewer@demo.test | 浏览业务台账 |

三个本地演示账号均使用 `DemoC0de!2026`。角色在 `backend/core/roles.py` 和 `frontend/src/store.js` 中声明。计算状态在 worker、queueing、API 和同一前端 store 中使用。

## 页面与接口

| 业务任务 | FastAPI 路由 | 页面 |
|---|---|---|
| 节目时段表 | `/airslots` /airslots/mark-offline | `frontend/src/pages/airslots.js` |
| 蓄电班记与测量 | `/battery_logs` /battery_logs/log-charge，/battery_logs/approve-meter，/battery_logs/correct-meter | `frontend/src/pages/battery_logs.js` |
| 备用分钟核算 | `/reserves` /reserves/forecast-wh，/reserves/save-reserve | `frontend/src/pages/reserves.js` |
| 班组备播卡 | `/switchcards` /switchcards/issue-switch，/switchcards/handover | `frontend/src/pages/switchcards.js` |

SQL 实体与约束在 `backend/domain` 下维护。前端使用原生 ES modules。核心算子为 Fourier 基 + OLS。OLS 在训练时段拟合一、二阶谐波和晴天标记。备用量为截零后的点预测加末 6 小时 MAE。

后端测试（SQLite + fakeredis，无需启动容器）：在 `backend` 目录安装 `requirements.txt`、pytest、fakeredis、httpx 后运行 `python -m pytest tests/`。

按模拟广播班记推演。卡片供人工值守查阅，应用只处理纸本条件的数字记录。

[MIT](LICENSE)
