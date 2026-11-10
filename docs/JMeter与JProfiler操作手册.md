# JMeter + JProfiler 压力测试操作手册

本手册对应课程 PPT《用大模型辅助做压力测试 — JMeter 与 JProfiler 实战教学》，
以本项目（火车票预订系统，Spring Boot 3.4 + MySQL 8.4）为被测对象。

- 默认口径：**PPT 口径** —— 10 线程、Ramp-Up 5 秒、循环永远、手动停止、GUI + 三个监听器
- 进阶口径：项目已有的 10/20/50/100/200 阶梯压测（CLI，见第 10 节）
- 全流程基准时长：**约 70 分钟**；课堂精简版约 45 分钟（见 1.2）

---

## 1. 总览

### 1.1 全流程时间表（完整版）

| 阶段 | 做什么 | 关键参数 | 时长 | 产出 |
|---|---|---|---|---|
| 0 | 环境检查 | JDK 21 / MySQL 3306 / 8080 空闲 | 5 min | 检查记录 |
| 1 | 数据复位 + 启动应用 | `00_perf_seed.sql`，MySQL 模式 | 8 min | 8080 可访问、应用 PID |
| 2 | JProfiler 连接 JVM | CPU sampling 5 ms | 5 min | 已连接的会话 |
| 3 | JMeter GUI 搭测试计划 | 10 线程 / 5 s / 永远 | 15 min | `.jmx` 脚本 |
| 4 | 故障复现与修复 | 登录前置 + Cookie 管理器 | 5 min | 全绿截图 |
| 5 | 正式压力测试 | 10 线程，稳态 5 min | 10 min | 汇总报告、CPU/内存曲线、快照 |
| 6 | 并发下单测试 | 10 线程 + 集合点，loop 1 | 10 min | 订单/库存核对结果 |
| 7 | 结果判读与归档 | TPS、P95、错误率、热点 | 10 min | 报告素材 |
| **合计** | | | **约 68 min** | |

### 1.2 课堂 45 分钟精简版

| 阶段 | 时长 | 精简做法 |
|---|---|---|
| 0 + 1 | 8 min | 课前已启动应用、已执行 seed |
| 2 | 5 min | JProfiler 直接 Attach |
| 3 | 10 min | 直接打开 `perf\load-test.jmx`，只改线程组参数 |
| 4 | 5 min | 用第 6 节的现象讲解，不现场重搭 |
| 5 | 8 min | 稳态只跑 3 分钟 |
| 7 | 7 min | 只看汇总报告 + 遥测曲线 |
| **合计** | **43 min** | |

### 1.3 两种口径不要混用

| 维度 | PPT 口径 | 项目正式口径 |
|---|---|---|
| 施压方式 | JMeter GUI，监听器全开 | `-n` 命令行，只写 JTL |
| 线程数 | 10 | 10 / 20 / 50 / 100 / 200 |
| 持续方式 | 循环永远，手动停 | `-Jduration=300`，每档 5 分钟 |
| 用途 | 教学演示、看曲线 | 出容量数字、写报告 |

GUI 监听器本身消耗资源，**PPT 口径的数字不能写进性能报告**；报告数字用第 10 节的 CLI 口径。

---

## 2. 工具与环境

### 2.1 软件目录（本机已核实）

| 软件 | 版本 | 目录 | 入口 |
|---|---|---|---|
| JMeter | 5.6.3 | `D:\AIBase\测试作业\tools\apache-jmeter-5.6.3` | `bin\jmeter.bat` |
| JProfiler | 16.3 | `D:\AIBase\测试作业\tools\jprofiler16` | `bin\jprofiler.exe` |
| MySQL | 8.4 | `C:\Program Files\MySQL\MySQL Server 8.4` | `bin\mysql.exe` |
| JDK | 21 | 已加入 PATH | `java -version` |

容易混淆的路径：

- `D:\AIBase\测试作业\tools\JProfiler\lib` 是 **IDEA 插件的依赖库**，不是 JProfiler 安装目录
- `D:\AIBase\测试作业\tools\JProfiler-plugin.zip` 是 IDEA 插件包
- `D:\AIBase\测试作业\tools\jprofiler_windows-x64_16_3.exe` 是安装包

项目已配置 `JMETER_HOME` 的默认回退值，`perf\*.bat` 不设环境变量也能跑。

### 2.2 前置检查（5 分钟）

逐条执行，全部符合预期再往下走：

| 检查项 | 命令 | 预期 |
|---|---|---|
| JDK | `java -version` | 21.x |
| MySQL 服务 | `sc query MySQL84` | `STATE : 4 RUNNING` |
| 3306 监听 | `netstat -ano \| findstr :3306` | `LISTENING` |
| 8080 空闲 | `netstat -ano \| findstr :8080` | 无结果（或确认是本项目） |
| JMeter | `D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat --version` | 5.6.3 |
| JProfiler | 目录存在 `bin\jprofiler.exe` | 存在 |
| 压测数据 | 见 3.2 的 seed 命令 | 15 条 `train_seats` |

> MySQL 的 `bin` 不在 PATH 时，用全路径调用：
> `"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"`。

---

## 3. 阶段 1：数据复位与启动应用（8 分钟）

### 3.1 节点动作

| 节点 | 动作 | 耗时 | 完成标志 |
|---|---|---|---|
| 3.1 | 确认 8080 没有残留 java 进程 | 1 min | 端口空闲 |
| 3.2 | 执行 seed 脚本 | 2 min | 15 条座位，`id=9001` 库存 1000 |
| 3.3 | 启动应用 | 2 min | 日志出现 `Started TrainTicketApplication` |
| 3.4 | 浏览器登录并查票 | 2 min | 能看到车次列表 |
| 3.5 | 记录应用 PID | 1 min | 供 JProfiler Attach |

### 3.2 数据复位（必须先做）

```bat
cd /d D:\AIBase\测试作业\train-ticket-java
"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u train_app -p train_ticket < perf\00_perf_seed.sql
```

执行后核对：

```sql
SELECT COUNT(*) FROM train_seats WHERE train_id BETWEEN 9001 AND 9005;  -- 15
SELECT id, travel_date, stock FROM train_seats WHERE id = 9001;        -- 明天 / 1000
```

- 查询场景虽然只读，但 `travelDate` 必须命中种子数据的日期，否则查询结果为空、断言失败
- `00_perf_seed.sql` 会先删除 9001–9005 的车次/座位/订单再重建，可反复执行
- **不要只跑 `01_perf_reset.sql`**：如果库里同时存在"旧日期"和"明天"的座位，
  `UPDATE` 会撞唯一键 `uk_seat`，报 `Duplicate entry '9001-...-一等座'`。
  遇到这个错就重跑 `00_perf_seed.sql`，不要手工改库

### 3.3 启动应用（MySQL 模式）

PowerShell：

```powershell
cd D:\AIBase\测试作业\train-ticket-java
$env:DB_USERNAME = "train_app"
$env:DB_PASSWORD = "你的本机密码"
java -jar target\train-ticket-0.0.1-SNAPSHOT.jar
```

cmd：

```bat
cd /d D:\AIBase\测试作业\train-ticket-java
set DB_USERNAME=train_app
set DB_PASSWORD=你的本机密码
java -jar target\train-ticket-0.0.1-SNAPSHOT.jar
```

也可以直接用 IDEA 的运行配置 `TrainTicketApplication_MySQL`。

**不要用 H2**（`-Dspring-boot.run.profiles=h2`）：H2 数据在内存里，压测结果不可比。

启动成功的标志：

```text
Tomcat started on port 8080 (http) with context path '/'
Started TrainTicketApplication in 13.278 seconds
```

### 3.4 人工验证一遍业务链

1. 打开 `http://localhost:8080/login`
2. 用 `perf01 / Pass123` 登录
3. 查询 `北京南 → 上海虹桥`，日期选**明天**
4. 能出现车次列表，说明数据、日期、登录都正常

### 3.5 记录 PID

```bat
jps -l | findstr TrainTicketApplication
```

或任务管理器 → 详细信息 → `java.exe`。第 4 节 Attach 时要用。

---

## 4. 阶段 2：JProfiler 连接 JVM（5 分钟）

### 4.1 顺序不能反

**先用第 3 节把应用跑起来，再开 JProfiler。** 顺序反了，进程列表里找不到 JVM，
这是 PPT 第 8 页点名的"新手最容易错的一步"。

### 4.2 连接四步

| 节点 | 动作 | 耗时 | 说明 |
|---|---|---|---|
| 2.1 | 打开 `D:\AIBase\测试作业\tools\jprofiler16\bin\jprofiler.exe` | 1 min | 首次启动如提示许可，选试用/评估 |
| 2.2 | Start Center → **New Session** → **Attach to a locally running JVM** | 1 min | 版本不同文案略有差异，认准 Attach/附加 |
| 2.3 | 选中 `com.example.trainticket.TrainTicketApplication` | 1 min | PID 与 3.5 记录的一致 |
| 2.4 | CPU profiling 选 **Sampling**（5 ms），点 **Connect** | 2 min | 连接过程十几秒，窗口挂着别动 |

> 也可以用 `jpenable.exe -d <PID>` 先在目标 JVM 里挂 agent，再用 GUI 连接；
> 纯命令行采集见 `docs/profiler/README.md`。

### 4.3 连上之后看什么（PPT 第 9 页）

| 视图 | 位置 | 观察点 | 截图命名 |
|---|---|---|---|
| Telemetry / 遥测 | 左侧 **Telemetry** | CPU 负载、堆内存、线程数曲线 | `telemetry-10-threads.png` |
| CPU Call Tree | **CPU** → Call Tree | 哪个方法自耗时最高 | `cpu-calltree-10-threads.png` |
| Hot Spots | **CPU** → Hot Spots | 热点方法排行 | `cpu-hotspots-10-threads.csv` |
| Heap Walker | **Heap Walker** | 哪个类的对象在堆积 | `heap-10-threads.png` |

本实验至少截两张：**CPU 曲线**、**实时内存曲线**（PPT 课后作业②）。

### 4.4 注意

- JProfiler 自身有开销，开了 profiler 的 TPS 一定低于 CLI 结果，**只用来定位瓶颈**
- 采样期间不要同时开第二个压测任务
- 项目已有证据：`docs/profiler/login-5min.jps`、`cpu-hotspots.csv`
  （`BCryptPasswordEncoder.matches` 占 91.2%），可作为结果对照
- 纯命令行导出遥测曲线不可靠，GUI 会话里录最稳（见 `docs/profiler/README.md`）

---

## 5. 阶段 3：JMeter GUI 搭测试计划（15 分钟）

### 5.1 目标结构（PPT 第 11 页）

```text
测试计划 TrainTicket-Stress
└── 线程组 列车查询（10 线程 / 5 s / 永远）
    ├── HTTP Cookie 管理器        ← 保会话，必须有
    ├── HTTP 请求默认值            ← localhost:8080 / UTF-8
    ├── HTTP 请求 01 GET /login
    ├── HTTP 请求 02 POST /login  ← 必须在查询上面
    ├── HTTP 请求 03 POST /trains/search
    ├── 查看结果树
    ├── 汇总报告
    └── 图形结果
```

### 5.2 节点动作

| 节点 | 操作 | 关键值 | 耗时 |
|---|---|---|---|
| 3.1 | 启动 GUI：`tools\apache-jmeter-5.6.3\bin\jmeter.bat` | 不要用 `-n` | 1 min |
| 3.2 | 右键 Test Plan → Add → Threads → Thread Group | 名称 `列车查询` | 1 min |
| 3.3 | 配线程组 | 线程 10 / Ramp-Up 5 / 循环勾 **Infinite** | 2 min |
| 3.4 | 加 HTTP 请求默认值 | `localhost`、`8080`、`UTF-8` | 2 min |
| 3.5 | 加 HTTP Cookie 管理器 | 默认配置即可 | 1 min |
| 3.6 | 加 `GET /login` | 方法 GET、路径 `/login` | 2 min |
| 3.7 | 加 `POST /login` | `uname` / `pword` | 3 min |
| 3.8 | 加 `POST /trains/search` | `fromStation` / `toStation` / `travelDate` | 3 min |
| 3.9 | 加三个监听器 | 查看结果树 / 汇总报告 / 图形结果 | 2 min |
| 3.10 | 保存为 `perf\ppt-10-threads.jmx` | 文件名随意，放 `perf/` | 1 min |

### 5.3 线程组参数（PPT 第 12 页）

| 参数 | 值 | 含义 |
|---|---|---|
| Number of Threads | 10 | 10 个虚拟用户 |
| Ramp-Up Period | 5 | 5 秒内把 10 个线程全部拉起来 |
| Loop Count | Infinite（勾选） | 一直循环，手动 Stop |

Ramp-Up 不是"每个请求间隔"，是"把全部线程拉满所需时间"。

### 5.4 三个请求的真实配置

**01 GET /login**

| 字段 | 值 |
|---|---|
| 方法 | GET |
| 路径 | `/login` |

**02 POST /login**

| 字段 | 值 |
|---|---|
| 方法 | POST |
| 路径 | `/login` |
| 参数 | `uname=perf01`，`pword=Pass123` |

> **注意：本项目密码字段是 `pword`，不是 PPT 里写的 `password`。**
> 字段名以 `src/main/resources/templates/login.html` 的 `name` 属性为准，
> 或浏览器 F12 看登录请求的表单参数。填错会一直停在登录页。

**03 POST /trains/search**

| 字段 | 值 |
|---|---|
| 方法 | POST |
| 路径 | `/trains/search` |
| 参数 | `fromStation=北京南` |
| | `toStation=上海虹桥` |
| | `travelDate=${__timeShift(yyyy-MM-dd,,P1D,,)}` |

- 查询是 **POST**，不是 GET；`GET /trains` 只是车次页
- `travelDate` 必须是种子数据里的日期，用 `__timeShift` 取明天，避免手写日期过期
- 站点名必须与库里的 `from_station` / `to_station` 完全一致
- 出现 **405 Method Not Allowed**，通常是路径和方法不匹配（PPT 第 20 页的坑）

### 5.5 监听器只用于调试

| 监听器 | 用途 | 正式压测 |
|---|---|---|
| 查看结果树 | 看单条请求、响应数据 | **关掉** |
| 汇总报告 | TPS、平均、P95、错误率 | 可留 |
| 图形结果 | 响应时间/吞吐量曲线 | 可留 |

正式跑（第 10 节）一律 `-n`，监听器全部禁用，否则结果失真。

---

## 6. 阶段 4：故障复现与修复（5 分钟）

PPT 用 500 / 401 讲两个坑；本项目实际表现是 **302 跳登录页**，本质相同：
**请求没带登录态，被拦截器打回登录页。**

### 6.1 两个坑的对照

| 坑 | 复现动作 | 本项目实际现象 | 根因 | 修复 | 耗时 |
|---|---|---|---|---|---|
| ① 没登录 | 删掉 `POST /login`，只留查询 | 查询请求 302 → 跳到 `/login`，跟随后返回 200，但**响应数据是登录页** | `LoginInterceptor` 对未登录请求 `sendRedirect("/login")` | `POST /login` 排在查询前面 | 2 min |
| ② 没带 Cookie | 有登录、但没有 Cookie 管理器 | 登录成功，查询仍返回登录页 | `JSESSIONID` 没被保存/回传 | 线程组下加 HTTP Cookie 管理器 | 2 min |

### 6.2 判断方法

不要只看红绿，点开请求 → **响应数据**：

- 标题是 `user log in` / 页面含 `uname`、`pword` 输入框 → 被拦截了
- 标题是车次列表 / 含"车次查询" → 正常

### 6.3 修复后验收

| 检查项 | 预期 |
|---|---|
| 10 个线程全部启动 | 汇总报告 `# Samples` 持续增长 |
| 错误率 | 0.00% |
| 三个请求顺序 | 登录 → 查询，循环往复 |
| 响应数据 | 查询返回车次列表 |

修复清单（PPT 第 19 页）：

1. `POST /login` 排在业务请求之前
2. 线程组下必须有 HTTP Cookie 管理器

---

## 7. 阶段 5：正式压力测试（PPT 口径，10 分钟）

### 7.1 时间轴

| 时刻 | 动作 | 耗时 | 备注 |
|---|---|---|---|
| T+0:00 | 确认 JProfiler 已连接，切到 Telemetry | 30 s | 曲线应为平缓 |
| T+0:30 | JProfiler 点 **Start Recording**（CPU sampling + Telemetry） | 10 s | 先开记录，避免漏掉陡增 |
| T+0:40 | JMeter 点 **Start**（绿色箭头） | 10 s | 10 线程 / 5 s ramp |
| T+0:50 | 观察：线程是否全部启动、错误率是否为 0 | 1 min | 查看结果树抽查 3 条 |
| T+2:00 | 切 JProfiler 看 CPU 曲线是否抬头、内存是否持续上涨 | 1 min | 记录峰值 |
| T+5:40 | JMeter 点 **Stop**（不是 Shutdown） | 10 s | 稳态跑满 5 分钟 |
| T+5:50 | JProfiler 点 **Stop Recording** | 10 s | 曲线保留在会话里 |
| T+6:00 | 保存快照 `File → Save Snapshot` | 30 s | 存 `docs/profiler/` |
| T+7:00 | 截图：CPU 曲线、内存曲线、汇总报告、图形结果 | 2 min | 四张图 |
| T+9:00 | 记录指标到下表 | 1 min | 完成本阶段 |

### 7.2 记录表

| 指标 | 来源 | 本次值 |
|---|---|---|
| 线程数 / Ramp-Up | 线程组 | 10 / 5 s |
| 稳态时长 | 手动计时 | 5 min |
| # Samples | 汇总报告 | |
| Average | 汇总报告 | |
| P95 / P99 | 汇总报告或 JTL | |
| Error % | 汇总报告 | 应为 0.00% |
| Throughput（TPS） | 汇总报告 | |
| 应用 CPU 峰值 | JProfiler Telemetry | |
| 堆内存峰值 / 是否回落 | JProfiler Telemetry | |
| 最热方法 | JProfiler Hot Spots | |

### 7.3 判读标准

| 现象 | 结论 |
|---|---|
| 错误率 0%，CPU 随线程上升后趋稳 | 10 线程在承载范围内 |
| CPU 接近 100%，响应时间持续上涨 | 已到瓶颈，需要降线程或优化 |
| 内存持续上涨不回落 | 疑似泄漏，去 Heap Walker 看对象 |
| 错误率 > 0 | 先看响应数据，再判断是脚本问题还是系统问题 |

### 7.4 参考基线（项目既有数据，非本次 GUI 结果）

查询场景 10 线程、每档 5 分钟的 CLI 结果：**TPS 1,221.2，平均 7.4 ms，P95 10 ms，错误率 0%**
（`README.md` 性能结果表）。GUI + JProfiler 同时开着会明显低于这个数字，属正常现象。

---

## 8. 阶段 6：并发测试（同座位抢票，10 分钟）

### 8.1 压力测试 vs 并发测试

| | 压力测试（第 7 节） | 并发测试（本节） |
|---|---|---|
| 目的 | 看吞吐和极限 | 看**同一资源**被同时争抢时是否正确 |
| 脚本 | `scenario-query.jmx` | `booking-concurrency.jmx` |
| 关键配置 | 循环永远 | **集合点 + 循环 1 次** |
| 验收 | TPS / P95 / 错误率 | 订单数、库存、是否超卖 |

### 8.2 节点动作

| 节点 | 动作 | 关键值 | 耗时 |
|---|---|---|---|
| 6.1 | 复位数据 | `00_perf_seed.sql` | 2 min |
| 6.2 | 记录初始库存 | `SELECT stock FROM train_seats WHERE id=9001` → 1000 | 1 min |
| 6.3 | 打开 `perf\booking-concurrency.jmx` | GUI 打开 | 1 min |
| 6.4 | 核对线程组 | 10 线程 / Ramp-Up 1 / 循环 1 | 1 min |
| 6.5 | 核对集合点 | Synchronizing Timer：Group Size = 0（全部线程），Timeout = 15000 ms | 1 min |
| 6.6 | 运行 | 10 个请求同时释放 | 10 s |
| 6.7 | 查库核对 | 订单 +10，库存 990 | 2 min |
| 6.8 | 再跑一次（可选） | 验证不是偶然 | 2 min |

### 8.3 命令行执行（等价）

```bat
cd /d D:\AIBase\测试作业\train-ticket-java
"D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat" -n ^
  -t perf\booking-concurrency.jmx ^
  -l perf\results\book-10.jtl ^
  -j perf\results\book-10.log ^
  -e -o perf\results\html-book ^
  -JbookThreads=10 -Jport=8080 ^
  -Jsampleresult.default.encoding=UTF-8
```

或直接：`perf\run-booking.bat 10 8080`

> 该脚本的账号和座位写在测试计划的 **User Defined Variables** 里：
> `USERNAME=alice01`、`SEAT_ID=9001`（不是 CSV 参数化）。
> 要换座位改 `SEAT_ID`；`perf\data\booking.csv` 目前没有被这个脚本引用。

### 8.4 核对 SQL

```sql
-- 库存应从 1000 变成 990
SELECT stock FROM train_seats WHERE id = 9001;

-- 该座位应正好新增 10 条订单
SELECT COUNT(*) FROM ticket_orders WHERE seat_id = 9001;

-- 不应出现负库存
SELECT id, stock FROM train_seats WHERE train_id BETWEEN 9001 AND 9005 AND stock < 0;
```

预期：

| 指标 | 预期 |
|---|---|
| 成功下单 | 10 |
| 库存 | 1000 → 990 |
| 订单数 | +10 |
| 负库存 | 0 条 |
| 错误率 | 0% |

> 本项目下单用 `UPDATE ... WHERE stock > 0` 原子扣减；
> JUnit 另有一条"50 并发抢 10 张票"用例验证不超卖（`src/test/`）。

---

## 9. 阶段 7：结果判读与归档（10 分钟）

### 9.1 汇总报告字段

| 字段 | 含义 | 怎么看 |
|---|---|---|
| `# Samples` | 总请求数 | 应随时间线性增长 |
| `Average` | 平均响应时间 | 受长尾影响，别只看它 |
| `Median` | 中位数 | 比平均值抗离群值 |
| `90% / 95% / 99% Line` | 分位响应时间 | **报告主指标** |
| `Min / Max` | 最小/最大 | Max 异常大要查毛刺 |
| `Error %` | 错误率 | 必须 0.00% |
| `Throughput` | 每秒请求数 | 即 TPS |
| `Received KB/sec` | 带宽 | 判断是否被网络限制 |

### 9.2 图形结果

- 黑线：当前样本响应时间
- 蓝点：所有样本
- 绿线：吞吐量
- 红线：偏离值

曲线整体抬升、吞吐走平 → 接近瓶颈；出现尖刺 → 看 GC 或锁等待。

### 9.3 JProfiler 结论怎么写

| 证据 | 结论句式 |
|---|---|
| Hot Spots 第一名占比 > 80% | "CPU 主要消耗在 X，占 Y%" |
| 调用树里 `BCryptPasswordEncoder.matches` 靠前 | "登录是 CPU 密集操作，BCrypt 是瓶颈" |
| Telemetry 堆内存锯齿且不回落 | "存在对象堆积，需 Heap Walker 定位" |
| HikariCP 获取连接耗时长 | "连接池可能不足，需 A/B 验证" |

项目既有结论：JProfiler 快照里 `BCryptPasswordEncoder.matches` 占 **91.2%**，
与 JFR 火焰图的 89.4% 相互印证（`docs/profiler/README.md`）。

### 9.4 归档清单

| 文件 | 存放位置 | 命名 |
|---|---|---|
| JMeter 脚本 | `perf/` | `ppt-10-threads.jmx` |
| JTL | `perf/results/` | `ppt-10.jtl` |
| HTML 报告 | `perf/results/html-ppt-10/` | `index.html` |
| JProfiler 快照 | `docs/profiler/` | `ppt-10-5min.jps` |
| CPU / 内存截图 | `docs/profiler/jprofiler_images/` | `telemetry-10-threads.png` |
| 汇总记录 | 本手册 7.2 表 | — |

---

## 10. 命令行复跑（可选，5 分钟）

### 10.1 查询场景（10 线程 × 5 分钟，与阶梯口径一致）

```bat
cd /d D:\AIBase\测试作业\train-ticket-java
"D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat" -n ^
  -t perf\scenario-query.jmx ^
  -l perf\results\ppt-10.jtl ^
  -j perf\results\ppt-10.log ^
  -e -o perf\results\html-ppt-10 ^
  -Jthreads=10 -Jramp=5 -Jduration=300 -Jport=8080 ^
  -Jsampleresult.default.encoding=UTF-8
```

打开 `perf\results\html-ppt-10\index.html` 看原生 HTML 报告。

### 10.2 登录+查询（观察 BCrypt 代价）

```bat
perf\run-load.bat 10 5 100 8080
```

参数依次为：线程数、Ramp-Up 秒、循环次数、端口。

### 10.3 全阶梯

```bat
perf\step-load.bat
```

10/20/50/100/200 五档、每档 5 分钟，全套约 25 分钟，跑完自动生成汇总和曲线。

### 10.4 JProfiler 纯命令行采集

参考 `docs/profiler/README.md` 的复现命令：

```bat
tools\jprofiler16\bin\jpcontroller.exe -n -f jpc-cmds.txt <PID>
tools\jprofiler16\bin\jpexport.exe docs\profiler\login-5min.jps ^
  "CallTree" -format=html docs\profiler\cpu-calltree.html ^
  "HotSpots" -format=csv  docs\profiler\cpu-hotspots.csv
```

---

## 11. 自查清单

PPT 五条（第 21 页）：

1. 先在浏览器里手动跑通一遍业务流程
2. JMeter 请求顺序 = 真实用户操作顺序
3. 有登录的系统，必加 Cookie 管理器
4. 报错先看"响应数据"，别急着重跑
5. 大模型给骨架，业务逻辑自己补

本项目补充五条：

6. 压测前重跑 `00_perf_seed.sql`，日期必须是明天
7. 密码字段是 `pword`，查询是 `POST /trains/search`
8. GUI 监听器只在调试开，正式跑用 `-n`
9. 并发测试要查库，不只看 JMeter 错误率
10. JProfiler 开着时的 TPS 不能当容量数字

---

## 12. 常见问题

**Q1：8080 被占用**
`netstat -ano | findstr :8080` 找 PID，确认是本项目旧进程后再结束。

**Q2：启动报 `Access denied`**
检查 `DB_USERNAME` / `DB_PASSWORD`，MySQL 里是否存在 `'train_app'@'127.0.0.1'`。

**Q3：JProfiler 进程列表里找不到应用**
应用没启动，或 PID 选错。先启动应用，再开 JProfiler。

**Q4：JMeter 全部是 200，但响应内容是登录页**
没登录或没 Cookie。按第 6 节加 `POST /login` 前置 + Cookie 管理器。

**Q5：查询结果为空、断言失败**
`travelDate` 不是种子数据日期，或站点名写错。重跑 `00_perf_seed.sql`，
日期用 `${__timeShift(yyyy-MM-dd,,P1D,,)}`。

**Q6：`01_perf_reset.sql` 报 `Duplicate entry`**
库里有历史日期残留。重跑 `00_perf_seed.sql`，不要手改唯一键。

**Q7：405 Method Not Allowed**
方法或路径与真实请求不一致。用 F12 对照浏览器里的请求。

**Q8：CSV 参数化看起来没生效**
`users.csv` / `booking.csv` 用 `shareMode=thread`，在"每线程只读一次"的场景里
所有线程都读第一行。这是已知限制（`perf/README.md`），不是脚本坏了。

**Q9：JProfiler 导不出遥测曲线**
命令行导出 Telemetry 不可靠，用 GUI 会话录并截图（`docs/profiler/README.md`）。

**Q10：JProfiler 提示许可**
选试用/评估；课堂演示够用。正式长期使用需按学校授权安装。

---

## 13. 与 PPT 的差异（照做前先看）

| PPT 写法 | 本项目实际 | 处理 |
|---|---|---|
| 被测系统是 `TrainBook_war_exploded` | Spring Boot 内嵌 Tomcat，根路径 `/` | 路径直接用 `/login`、`/trains/search` |
| 登录参数 `uname` / `password` | `uname` / **`pword`** | 用 `pword` |
| 未登录返回 500 / 401 | 拦截器 302 跳 `/login`，跟随后 200 登录页 | 看响应数据判断，不看颜色 |
| 查询可用 GET | 查询是 **POST** `/trains/search` | 方法选 POST，参数放 Parameters |
| JProfiler 会话类型 "Tomcat on localhost" | 本机 Attach 到 `java.exe` | New Session → Attach to a locally running JVM |
| 10 线程循环永远 | 阶梯用 10–200 线程、每档 5 分钟 | 教学用 10，报告用阶梯 |

这些差异不影响 PPT 的方法论：**JMeter 施压、JProfiler 观察、大模型给骨架、人补业务**。

---

## 14. 本次实测验证记录

| 项目 | 结果 |
|---|---|
| 应用启动 | `Started TrainTicketApplication in 13.278 seconds`，8080 监听 |
| 登录链路 | `POST /login` → 302 `/trains`，Cookie 正常 |
| 查询链路 | 带 Cookie `POST /trains/search` → 200，含"车次查询" |
| 未登录行为 | 302 → `/login`（与 PPT 的 401 不同，已在本手册注明） |
| 10 线程 / 60 秒 CLI | 见下表 |

### 14.1 环境

- JDK 21.0.11，MySQL 8.4（`MySQL84` 服务运行中），应用启动耗时 13.278 s
- 应用 PID 50264（本次验证时）

### 14.2 10 线程 / 60 秒实测（2026-11-08 15:18）

| 指标 | 值 |
|---|---|
| 脚本 | `perf\scenario-query.jmx` |
| 参数 | `-Jthreads=10 -Jramp=5 -Jduration=60 -Jport=8080` |
| 主请求样本 | 65,939 |
| TPS | 1,097.9 |
| 平均响应 | 7 ms（查询样本 7.83 ms） |
| P90 / P95 / P99 | 10 / 11 / 16 ms |
| 最大响应 | 405 ms（启动首秒）；查询样本 76 ms |
| 错误率 | 0.00%（含 10 条登录 302 跳转，非失败） |
| 结果文件 | `perf\temp\verify-10b.jtl`（临时验证，未入库） |

> 这是 CLI 口径、无 GUI 监听器、无 JProfiler 的数字，仅用于证明手册命令可用。
> 按第 5 节用 GUI + JProfiler 重跑，TPS 会更低，属正常现象。

### 14.3 验证时踩到的坑（已写进 3.2 / 问题 Q5）

第一次跑出 **100% 错误**，但响应码全是 200：查询结果为空，
断言 `查询到了空结果，检查参数化线路` 失败。原因是库里的 `travel_date`
还是上一轮的历史日期。重跑 `00_perf_seed.sql` 后立刻恢复 0% 错误。
这正好说明第 6 节的原则：**先看响应数据，不要只看红绿。**

### 14.4 并发下单实测（2026-11-08 15:20）

| 指标 | 值 |
|---|---|
| 脚本 | `perf\booking-concurrency.jmx`，`run-booking.bat 10 8080` |
| 采样数 | 30（10 线程 × GET 登录 + POST 登录 + POST 下单） |
| 错误率 | 0.00% |
| 平均响应 | 273 ms |
| 最大响应 | 623 ms |
| 库存 | 1000 → **990** |
| 订单数（seat 9001） | **10** |
| 负库存 | 0 |

### 14.5 结论

手册中的启动、登录、查询、10 线程压测、并发下单五条命令均已实跑通过。
唯一需要提前处理的是数据日期：**先 `00_perf_seed.sql`，再压测**。
