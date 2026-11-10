# perf — JMeter 压测

> 完整操作手册（含 JProfiler 连接、逐节点动作与耗时）：
> [../docs/JMeter与JProfiler操作手册.md](../docs/JMeter与JProfiler操作手册.md)

## 正式测试资产

| 文件 | 说明 |
|------|------|
| `scenario-query.jmx` | 查询场景（登录一次 + 循环查询），用于阶梯加压；CSV 名义 20 用户 / 5 线路，实际登录读第一行 `perf01`、线路在循环内轮换 |
| `scenario-mixed.jmx` | 查询 + 下单两个独立线程组（混合场景）；实际单账号 `perf01`、单座位 `9001` |
| `load-test.jmx` | 登录+查询（每次迭代重新登录，用于对比 BCrypt 代价）；**固定单账号 `alice01` + 单线路**，不是多用户场景 |
| `booking-concurrency.jmx` | 独立并发下单（同一座位 9001，集合点） |
| `00_perf_seed.sql` | 20 用户 / 5 线路 / 3 席别 / 充足库存 |
| `01_perf_reset.sql` | 每轮前复位订单、库存、车票日期 |
| `data/users.csv` | 20 个压测账号 |
| `data/routes.csv` | 5 条线路（from/to） |
| `data/booking.csv` | 用户 + 座位参数化 |
| `step-load.bat` | 一键跑 10/20/50/100/200 阶梯加压 |
| `summarize_step_load.py` | 汇总各阶段 TPS/P90/P95/P99 |
| `plot_step_load.py` | 生成 TPS/P95 曲线图到 `docs/figs/` |
| `run-load.bat` / `run-booking.bat` | 单场景快捷脚本 |

结果在 `results/`：JTL、`html-*/index.html`、`step-load-summary.md`。

## 口径（先看这一段）

- **TPS = JMeter 主请求/秒**，不含重定向子样本（`-0` / `-1`）；
- 查询场景 1 次业务 = 1 个 `POST /trains/search`；
- 登录+查询场景 1 次业务 = 3 个主请求（`GET /login`、`POST /login`、`POST /trains/search`），
  **事务/秒 = TPS ÷ 3**；持续 50 线程时 TPS 147.6，事务率只有 49.2/s；
- 混合场景按全部主请求计；
- 跨场景比较必须用同一口径。不要把登录场景的 147 与查询场景的 1485 直接对比。

## 前置

- 8080 上的应用以 MySQL 模式运行
- 已执行 `00_perf_seed.sql`
- JMeter 在 `D:\AIBase\测试作业\tools\apache-jmeter-5.6.3`（可用 `JMETER_HOME` 覆盖）

## 阶梯加压

```bat
mysql -u train_app -p train_ticket < 00_perf_seed.sql
step-load.bat
```

等价于对 `scenario-query.jmx` 依次执行 10/20/50/100/200 线程、ramp 5s、**每档持续 5 分钟**（全套约 25 分钟）。
跑完自动生成：

- `results/step-load-summary.csv` / `.md`
- `docs/figs/step-load-tps.png`、`step-load-p95.png`

> 20 线程后的 1485 TPS 平台期曾被怀疑是 HikariCP 10 连接上限；2026-10-28 的 A/B 把 pool 扩到 30，
> 50 线程稳态只从 1471.6 升到 1573.4（+6.9%），100 线程 1503.8→1590.7（+5.8%），**连接池不是主限制器**。
> 详见 `results/pool-ab.md`；最可能是同机 JMeter 客户端，下一步采客户端 CPU 或换第二台压测机。

## 资源监控（压测期间另开一个窗口）

先防睡眠，再采 CPU/内存/磁盘 IO：

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File keep_awake.ps1 -Seconds 2000

powershell -NoProfile -ExecutionPolicy Bypass -File monitor_resources.ps1 ^
  -AppPid <8080 的 java 进程 PID> -MysqlPid <mysqld PID> ^
  -Seconds 2000 -Out results\resources-step5min.csv
```

采样名义 2 秒/点，实际约 4.6 秒/点（1715 秒 / 374 点），阶段切换处有 7～15 秒空档；
峰值可能被漏采，报告里已注明。

跑完执行：

```bat
python analyze_resources.py
python analyze_timeseries.py --jtl results\step-100.jtl --prefix step-100
```

生成 `docs/figs/resource-cpu.png`、`resource-mem.png`、`step-100-tps.png`、`step-100-error.png`。

## 混合场景

```bat
mysql -u train_app -p train_ticket < 01_perf_reset.sql
D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat ^
  -n -t scenario-mixed.jmx -l results\mixed.jtl ^
  -e -o results\html-mixed ^
  -JqueryThreads=50 -JbookThreads=10 -Jduration=60 -JbookDelay=5 -Jport=8080
```

> 混合场景 60 秒、与阶梯场景执行时间不同（10-26 vs 10-27），50 线程查询只有 538 TPS / 88ms，
> 阶梯 50 档是 1463 TPS / 33ms，相差约 2.7 倍；绝对 TPS 不可直接比较，只能用于验证混合行为。

## 登录+查询对比

```bat
D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat ^
  -n -t load-test.jmx -l results\sustain50.jtl ^
  -e -o results\html-sustain50 ^
  -Jthreads=50 -Jramp=5 -Jloops=100 -Jport=8080
```

> `load-test.jmx` 固定 `alice01` + “北京南→上海虹桥”，用于隔离 BCrypt；
> 10/50/100/200 短跑分别 10/10/5/5 圈，含 5 秒 ramp-up，只有 50×100 圈（102 秒）是稳态。

## 数据库侧

压测前后对比（阈值不要用 10s，否则 100ms～10s 的慢 SQL 全部漏掉）：

```sql
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';   -- 建议 0.1
SHOW GLOBAL STATUS LIKE 'Slow_queries';
SHOW GLOBAL STATUS LIKE 'Questions';
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW GLOBAL STATUS LIKE 'Innodb_row_lock_waits';
```

## 连接池对照（已执行 2026-10-28）

结果：pool 10→30，50 线程稳态 **1471.6→1573.4 TPS（+6.9%）**，100 线程 **1503.8→1590.7（+5.8%）**；
应用 CPU 34.4%→35.2%，MySQL 20.0%→21.2%。**连接池不是 1485/1504 平台期的主限制器**；
之前“10 连接 ≈ 1483 TPS”只是数字巧合。详见 `results/pool-ab.md`。

复现时只改 pool，保持 `thymeleaf.cache=false`，避免两个变量同时变：

```bat
rem 用 30 连接池重启应用：
rem   --spring.datasource.hikari.maximum-pool-size=30
D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat ^
  -n -t scenario-query.jmx -l results\pool30-50.jtl ^
  -e -o results\html-pool30-50 ^
  -Jthreads=50 -Jramp=5 -Jduration=300 -Jport=8080
```

下一步：采 JMeter PID 与整机 CPU，或换第二台压测机/分布式压测；应用和 JMeter 都加 `-Xlog:gc`，排除 4～5 秒毛刺。

## 注意

- 正式压测不要启用 View Results Tree / 聚合报告等 GUI 监听器，用 `-n` + JTL + `-e -o`
- 参数化 CSV 都设置了 `ignoreFirstLine=true`，表头不会被当成数据
- **CSV 共享模式的坑**：`users.csv` / `booking.csv` 用 `shareMode=thread`，但登录在 `Once Only` 里、下单组只跑 1 圈——“每线程只读一次”时所有线程都读第 1 行，实际是 `perf01` / `perf01 + 9001`，20 行数据没有分流。要分流请改 `shareMode=group` 或按线程号预分配
- 查询场景只读；混合/下单场景每轮前执行 `01_perf_reset.sql`
- 压测机与应用同机时，JMeter 自身也会占 CPU，结果偏保守；本轮没有单独采客户端 CPU，无法排除客户端限制
- 数据规模名义 20 账号 / 5 线路 / 15 座位，实际单账号；全部可缓存，容量结论偏乐观
- 写路径只做了 10 单链路验证；JUnit 超卖测试在 H2 上，不覆盖 MySQL 行锁
