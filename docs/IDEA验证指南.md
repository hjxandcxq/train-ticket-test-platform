# 在 IDEA 中验证本项目 — 操作指南

> 目标：让你能在 IDEA 里独立验证功能测试、性能数据、图表来源和 Profiler 火焰图，而不是只看一份报告。
> IDEA 版本：IntelliJ IDEA 2025.3.3 Ultimate；JDK 21。

## 1. 打开项目

1. IDEA → `File → Open`，选择 `D:\AIBase\测试作业\train-ticket-java`
2. 等右下角 Maven 依赖导入完成（第一次会下载依赖）
3. 确认 `File → Project Structure → Project SDK` 是 JDK 21
4. 运行配置下拉框里有：
   - `TrainTicketApplication (MySQL)`：正式模式
   - `TrainTicketApplication (H2 演示)`：无 MySQL 时看页面

## 2. 确认 MySQL 与应用

1. `services.msc` 确认 `MySQL84` 正在运行
2. 确认数据库有数据：

```sql
USE train_ticket;
SELECT COUNT(*) FROM users;        -- 3 个基础账号 + 20 个 perf 账号
SELECT COUNT(*) FROM trains;       -- 10 条基础线路 + 5 条压测线路
SELECT COUNT(*) FROM train_seats;  -- 基础 60 + 压测 15
```

3. 如果 8080 已经被命令行启动的实例占用，先停掉：

```powershell
# 找到 8080 的 PID
netstat -ano | findstr :8080
# 停掉（把 <PID> 换成实际 PID）
Stop-Process -Id <PID>
```

4. IDEA 选择 `TrainTicketApplication (MySQL)` → Run
5. 浏览器打开 http://localhost:8080/login，用 `alice01 / Pass123` 登录

## 3. 验证 JUnit 并发测试

IDEA 右侧 Maven 面板 → `Lifecycle → test`，或命令行：

```bat
"D:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\plugins\maven\lib\maven3\bin\mvn.cmd" test
```

实际跑的是 `src/test/java/com/example/trainticket/BookingConcurrencyTest.java`，2 条用例。它带
`@SpringBootTest + @ActiveProfiles("h2")`，会拉起完整 Spring 上下文和 H2 内存库、调用真实的 `BookingService`
（不是 mock），所以耗时约 25 秒。

预期输出：

```
Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

- 两条用例：`fiftyConcurrentBookingsOnlySellTenTickets`（并发下单）、`refundRestoresStockAndCannotBeRepeated`（退票幂等）
- “50 个线程同时下单”不是顺序提交：50 个任务进 32 线程池，再用 `ready / start / done` 三个 `CountDownLatch`
  让它们在同一个瞬间起跑（测试类 `:101-153`）。否则线程池排队执行，测不出并发。
- 断言是四条硬约束（`:146-152`）：成功 10 单、余票不足 40 次、非预期异常 0、库存归 0 且订单 10 条。
  只“没抛异常”不算通过 —— 抛的必须是“余票不足”这个业务异常，抛出锁冲突或超时都会计入非预期异常而失败。

不超卖的原因在被测代码里，不在测试里：

```java
// TrainSeatRepository.java:30-32
@Modifying(clearAutomatically = true, flushAutomatically = true)
@Query("update TrainSeat s set s.stock = s.stock - 1 where s.id = :id and s.stock > 0")
int decrementStock(@Param("id") Long id);
```

条件 `stock > 0` 与自减压在同一条 UPDATE 里，由数据库保证“判定 + 扣减”原子完成；返回受影响行数 0 就抛
“该车次余票不足”（`BookingService.java:50-53`）。不存在“先查库存、再判断、再减”的竞态窗口。

> 输出里的 Mockito self-attaching、byte-buddy 动态 agent、CDS sharing 三类 WARNING 是 JDK 21 的例行提示，
> 与结果无关，不必处理。
>
> 边界：本测试跑在 H2 上，只证明代码逻辑与该条 SQL 的原子性，**不覆盖 MySQL 的 InnoDB 行锁**；
> MySQL 写并发容量属于未验证项（见《性能测试报告》第 7.7 节）。

## 4. 验证 Selenium 功能用例

### 4.1 运行命令与报告生成机制

保持 8080 应用运行（MySQL 模式），在 IDEA 内置 Terminal 中执行：

```bat
cd D:\AIBase\测试作业\train-ticket-java\functional_tests
..\.venv-tests\Scripts\python.exe -m pytest -v --html=report.html --self-contained-html
```

前置只有两条：应用在 8080 且是 MySQL profile；数据库口令用环境变量传入。

```powershell
$env:DB_PASSWORD="train_app 的本机密码"
```

`conftest.py` 先读环境变量，再读可选的 `.env`，两者都没有才报错，所以 `.env` 不是必需的。不设口令时的
报错形态是 **25 条全部 ERROR**（fixture 阶段失败），不是 FAIL（断言失败）—— 看到一排 ERROR 先查口令和 8080。

`report.html` 是自动生成的：pytest-html 插件在运行结束时把本次结果渲染成静态 HTML。`--html=report.html`
指定输出路径，`--self-contained-html` 把 CSS/JS 内联成单文件，便于直接外发；重跑一次整份覆盖。页面默认
收起明细，点右上角 `Show all details` 可展开每条用例的 setup/call/teardown、耗时、失败截图链接和标准输出。

换句话说，报告是“运行快照”，不含任何结论文字，只有结果和耗时；结论要按 4.4 节的断言层级去读。

### 4.2 25 条用例的分布

| 文件 | 条数 | 覆盖 |
|------|------|------|
| `test_login.py` | 4 | 登录成功、密码错、账号不存在、空字段 |
| `test_register.py` | 5 | 注册后可登录、用户名重复、两次密码不一致、弱密码、用户名过短 |
| `test_search.py` | 5 | 查询成功、同站出发到达、缺站点、无结果、过去日期 |
| `test_booking.py` | 5 | 下单成功（校验库存 -1）、未登录被拦、座位不存在、余票不足、空乘客名 |
| `test_refund.py` | 2 | 退票成功且重复退票被拒、退他人订单被拒 |
| `test_admin.py` | 4 | 普通用户进后台被拦、后台首页、加车次成功、重复线路被拒 |

套件启动时先执行 `functional_tests/00_test_seed.sql`，把功能测试专用车次 `FUNC01`（id=9100）和三个座位重置：
9101 二等座余票 50（下单成功）、9102 一等座余票 0（余票不足）、9103 商务座余票 50（退票）。这是“每条用例
预期结果固定”的前提，也是这套用例必须连真实 MySQL 的原因。

### 4.3 Selenium 到底在验什么

机制：用 WebDriver 协议遥控一个真实浏览器（Chrome 或 Edge），像人一样填表、点按钮，然后断言 URL、页面
文本和数据库里的数。浏览器由 `browser.py` 的 `create_driver()` 启动，默认 `--headless=new` 无头运行；
Selenium 4.x 自带 Selenium Manager 会自动匹配 chromedriver，无需手动下载。整个会话共用一个浏览器实例，
每条用例前清 Cookie，避免登录态互相污染。

单条用例都是四步：定位元素 → 操作 → 显式等待 → 断言。以登录为例：

```python
driver.get(base_url + "/login")
WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.NAME, "uname")))
driver.find_element(By.NAME, "uname").send_keys("alice01")
driver.find_element(By.NAME, "pword").send_keys("Pass123")
driver.find_element(By.ID, "btn-login").click()
wait_url_contains(driver, "/trains")
```

全部使用 `WebDriverWait` 显式等待，没有 `time.sleep`：点击后页面要重定向、模板要渲染，元素是过一会儿才
出现的，写死等待既慢又不稳。

这些选择器不是随手编的，它们和 Java 侧模板是同一份契约 —— 模板改 id，Python 用例立刻红：

| Python 中的定位 | 对应的 Java / Thymeleaf 代码 |
|-----------------|------------------------------|
| `By.NAME "uname" / "pword"` | `templates/login.html` 的登录表单字段 |
| `By.ID "btn-login"` | `templates/login.html:50` |
| `By.CSS_SELECTOR ".msg.error"` | `login.html:36`、`trains.html:15`、`orders.html:16` |
| `By.CSS_SELECTOR ".nav .user"` | `templates/fragments/layout.html:10` |
| `By.ID "trainTable"` | `templates/trains.html:48` |

这正是功能测试的价值：它锁的是“页面结构 + 后端行为”的整体契约。JUnit 直接调 Service，绕过了 Controller
路由、Spring Security 过滤器链和 Thymeleaf 渲染，这三层只有浏览器测试能覆盖。

### 4.4 三层断言，一层比一层硬

- **URL 层**：`wait_url_contains(driver, "/orders")` —— 下单后确实跳到了订单页
- **页面层**：`wait_success()` 取 `.msg.success` 文本断言含“购票成功”；断言页面里出现“已支付”
- **数据层（最有力）**：`test_booking.py:28-51` 在点单前后各查一次 MySQL，断言 `stock` 正好少 1。
  这条把 浏览器点击 → Controller → BookingService → UPDATE → MySQL 整条链路锁死，页面提示成功但事务
  回滚会被抓出来。退票用例同理：断言库存回补、重复退票不再加库存

另有 3 条用例故意绕过 UI 直接打接口：先 `api_session(driver)` 把浏览器 Cookie 复制到 `requests.Session`，
再 `POST /orders`。因为 9102 余票为 0，页面按钮点不动，UI 走不到“余票不足”分支；要验这条业务规则只能带
登录态打接口，断言响应文本含“该车次余票不足”。同类还有“座位不存在”“乘客姓名必填”。

失败时留证据：`fail_with_screenshot()` 把当时页面截到 `functional_tests/screenshots/` 并把路径拼进断言消息，
报告里能直接看到失败现场。

### 4.5 想亲眼看到它操作

关掉无头模式，只跑一条用例：

```powershell
$env:DB_PASSWORD="本机密码"
$env:TT_HEADLESS="0"
..\.venv-tests\Scripts\python.exe -m pytest test_booking.py::test_booking_success -v
```

会看到浏览器自己打开、输账号密码、选站点、点查询、填乘客名、点下单。看完这一条，上面“定位 → 操作 →
等待 → 断言”四步就全对上了。

## 5. 验证性能数据与图表

### 5.1 看现成结果

先看这三处，分别对应原始报告、汇总和结论：

1. 打开 `perf/results/html-step-100/index.html`（JMeter 原生 HTML 报告，100 线程 5 分钟），
   `Statistics` 表直接看 TPS/平均/P95
2. 打开 `perf/results/step-load-summary.md`（阶梯五档汇总，对应《性能测试报告》7.1 的表）
3. 打开 `perf/results/analysis.md`（混合/登录/下单三个场景的汇总）

> 注意 JMeter 原生报告的样本数包含重定向子样本（label 以 `-0` / `-1` 结尾），而报告口径是“主请求/秒”，
> 已把子样本过滤掉；对数前先统一口径，否则 TPS 会差几个百分点。

### 5.2 从 JTL 重新生成图表

```bat
cd perf
python summarize_step_load.py       :: step-*.jtl → step-load-summary.csv/md
python plot_step_load.py            :: csv → docs/figs/step-load-tps.png / p95.png
python analyze_timeseries.py --jtl results/step-100.jtl --prefix step-100
python analyze_resources.py         :: 资源 csv → resource-cpu.png / mem.png
```

为什么能从 JTL 重算：JTL 是 JMeter 的原始结果，每个请求一行（timeStamp、elapsed、label、success），本身
不含任何汇总；上面几个脚本只是对同一份原始数据做分组统计和画图。所以图、表、报告三者可以互相校验，
这也是“结论可复核”的依据。

| 图 / 表 | ← 中间产物 | ← 原始数据 |
|---------|-----------|-----------|
| `step-load-tps.png` / `step-load-p95.png` | `step-load-summary.csv` | `step-10 ~ step-200.jtl`（每档 5 分钟） |
| `step-100-tps.png` / `step-100-error.png` | 脚本直接计算 | `step-100.jtl` |
| `resource-cpu.png` / `resource-mem.png` | `resources-step5min.csv` | `monitor_resources.ps1` 采样（约 4.6 秒/点） |
| 《性能测试报告》全部表格 | 上述 csv / jtl | `gen_perf_report_docx.py` 重新计算 |

### 5.3 自己重跑阶梯加压（可选，约 25 分钟）

顺序不能乱：先灌压测数据 → 防睡眠 → 起资源监控 → 最后压测。少起监控，资源和图就对不上。

```bat
cd perf
mysql -u train_app -p train_ticket < 00_perf_seed.sql
powershell -NoProfile -ExecutionPolicy Bypass -File keep_awake.ps1 -Seconds 2000
powershell -NoProfile -ExecutionPolicy Bypass -File monitor_resources.ps1 ^
  -AppPid <8080 PID> -MysqlPid <mysqld PID> -Seconds 2000 ^
  -Out results\resources-step5min.csv
step-load.bat
```

跑完依次执行 `summarize_step_load.py`、`plot_step_load.py`、`analyze_resources.py`，再重新生成 Word。
每轮压测前必须执行 `01_perf_reset.sql`，否则库存和订单跨轮累积，下单场景的数字不可比。

## 6. 用 IDEA Profiler 采集 CPU 火焰图（可选）

> 本报告的主证据是 `perf/results/perf100.jfr` 生成的 `docs/figs/cpu-flamegraph-jfr.png`。
> IDEA Profiler 截图是**可选交叉验证材料**，不采集不影响报告结论。

### 6.1 用 Profiler 启动应用

1. 运行配置选择 `TrainTicketApplication (MySQL)`
2. 菜单 **Run → Profile 'TrainTicketApplication (MySQL)'**
3. 选 **CPU Profiler**（Sampling 模式即可，开销小）
4. 应用启动后，浏览器/接口确认 8080 正常

> 如果菜单里没有 Profile：用 **Run → Attach Profiler to Process**，选择 8080 的 `java.exe`（主类 `com.example.trainticket.TrainTicketApplication`）。

### 6.2 产生负载

另开一个终端，跑登录+查询场景（这样才能看到 BCrypt 热点）：

```bat
cd D:\AIBase\测试作业\train-ticket-java
"D:\AIBase\测试作业\tools\apache-jmeter-5.6.3\bin\jmeter.bat" ^
  -n -t perf\load-test.jmx -l perf\results\profile.jtl ^
  -e -o perf\results\html-profile ^
  -Jthreads=100 -Jramp=5 -Jloops=10 -Jport=8080
```

大约 20 秒跑完。也可以在 Profiler 里先点 Start，再跑这条命令。

> 为什么选 Sampling：它按固定间隔抓调用栈，开销小、能长时间采，代价是样本量有限；Tracing 记录每次调用，
> 精度高但开销大，压测时会把被测应用本身拖慢，结论失真。报告只需要“谁最宽”，Sampling 足够。
>
> 为什么 20 秒负载就够：100 线程 × 10 圈 ≈ 1646 个 CPU 样本，热点占比已经稳定（BCrypt 89.4%），
> 继续压只增加样本数，不改变排名。

### 6.3 看火焰图并截图（可选）

1. Profiler 窗口切到 **CPU → Flame Graph**
2. 预期最宽的热点：
   - `org.springframework.security.crypto.bcrypt.BCrypt.encipher`
   - 其上层调用 `BCryptPasswordEncoder.matches`、`AuthService.login`
3. 点击 `BCrypt.encipher` 可以看调用栈和占比
4. 截图：`Win + Shift + S`，保存为：

```
docs\profiler\idea-profiler-cpu.png
```

如果 Profiler 支持 **Export**，也可以导出 `.jfr`/快照到 `docs/profiler/`。

> 参考图：`docs/figs/cpu-flamegraph-jfr.png` 是用同一批 JFR 样本（1646 个）画的火焰图，BCrypt 占 89.4%。
> IDEA 的截图会更直观，但数据结论一致。

### 6.4 如果你 profiling 的是查询场景

用 `perf/scenario-query.jmx`（会话复用、只查询）时，热点会是 Thymeleaf/HTTP，而不是 BCrypt。
这是正常的：查询路径很轻，登录才是瓶颈。要复现报告里的 BCrypt 热点，请用 `load-test.jmx`。

## 7. 验证资源监控

1. 看 `perf/results/resources-step5min.csv`：应用 CPU、MySQL CPU、内存、磁盘 IO
   （名义 2 秒/点，实际约 4.6 秒/点，阶段切换处有 7～15 秒空档）
2. 看 `perf/results/resource-summary.md`：平均/峰值
3. 看 `docs/figs/resource-cpu.png`、`resource-mem.png`
4. 看 `perf/results/db-status-before.txt` / `after.txt`：
   - `Slow_queries=0`（阈值是 10s，只能说明没有 >10s 的 SQL）
   - `Threads_connected=11`（Hikari 10 + 监控连接；这恰好是 10 连接池占满的形态）
   - `Innodb_row_lock_waits` 前后都是 28（读场景为主，不能代表写并发）

这些指标各自的陷阱，读之前必须知道：

- `Slow_queries=0` ≠ 没有慢 SQL：阈值是 `long_query_time=10s`，100ms～1s 的查询不会计入
- `Threads_connected=11` 说明池被占满，但第 7.8 节的 A/B 已证明扩池只提升 6%，**占满不等于瓶颈**
- `Innodb_row_lock_waits` 前后不变：阶梯与登录场景以读为主，这个计数不能代表写并发表现
- 采样是 4.6 秒/点而不是 2 秒，峰值可能被漏采，所以只能写“未观测到超阈值”，不能写“峰值就是 43%”

应用 CPU 只有 43%、MySQL 27.8%，都不能推出“系统还有余量”：压测机同机跑 JMeter，那 16 核里有客户端在抢 CPU。

## 8. 重新生成 Word 报告

两份 docx 都是脚本生成的，不是手写文档：`scripts/gen_idea_guide_docx.py` 生成本指南，
`scripts/gen_perf_report_docx.py` 生成性能测试报告（正文硬编码在脚本里，表格数字从 `perf/results/*.csv`、
`*.jtl` 现算）。所以要改文档内容，改脚本；要改数字，改原始数据后重跑脚本。

先**关闭 Word**（否则文件被占用），然后：

```bat
cd D:\AIBase\测试作业\train-ticket-java
.venv-tests\Scripts\python.exe scripts\gen_perf_report_docx.py
```

预期：

- 生成 `docs/性能测试报告.docx`
- 8 张图内嵌
- 11 个一级标题（生成时会打印 `inline shapes` 数量，可据此确认图都嵌进去了）

> Word 没关会报 `PermissionError: 另一个程序正在使用此文件` —— 这不是脚本的问题。

## 9. 验证清单

| 验证项 | 预期 |
|--------|------|
| MySQL 数据 | users=23、trains=15、train_seats=75（基础+压测） |
| JUnit | 2 条通过，50 并发只成功 10 单（H2） |
| Selenium | 25 条通过 |
| 阶梯 100 线程 | TPS≈1485、平均≈66ms、P95≈140ms、错误率 0 |
| 混合场景 | TPS≈535、P95≈166ms、10 个订单（60 秒短跑） |
| 登录+查询 | 主请求 TPS≈147.6、事务≈49.2/s、P95≈1024ms（未达标） |
| 资源 | 应用 CPU 峰值≈43%、MySQL CPU 峰值≈28%、慢查询 0（阈值 10s） |
| 连接池 A/B | pool30 稳态 1573/1591 TPS，较 pool10 +6%，连接池不是主限制器 |
| Profiler | JProfiler 16.3 CPU 热点 `BCryptPasswordEncoder.matches` 91.2%；JFR 火焰图 `BCrypt.encipher` 约 89%；IDEA Profiler 截图可选 |

## 10. 注意事项

- **不要同时启动两个 8080 实例**：IDEA 启动前先停掉命令行 jar
- Selenium 套件连的是真实 MySQL，口令用 `DB_PASSWORD` 环境变量传，别把口令提交进仓库
- 正式压测不要开 View Results Tree，用 `-n` + JTL + `-e -o`
- 压测前执行 `01_perf_reset.sql`，否则库存/订单会累积
- Word 报告生成前先关闭 Word，否则会报 `PermissionError`
- JMeter 路径：`D:\AIBase\测试作业\tools\apache-jmeter-5.6.3`
