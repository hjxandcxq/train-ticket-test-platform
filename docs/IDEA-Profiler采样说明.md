# 用 IDEA 自带 Profiler 采样 CPU / 内存

目标：在 100 线程压测期间定位 CPU 热点和内存分配，补充到《性能测试报告》。

## 1. 启动应用（必须是 MySQL 模式）

IDEA 右上角运行配置选择 **TrainTicketApplication (MySQL)**，点 Run，确认 8080 正常打开：

```
http://localhost:8080/login
```

不要用 H2 演示配置，否则压测数据不在 MySQL 里。

## 2. 用 Profiler 启动

IDEA Ultimate 2025.3 有两种入口：

- 菜单 **Run → Profile 'TrainTicketApplication (MySQL)'**
- 或右键运行配置 → **Profile**

在弹出的 Profiler 配置里：

- 选 **CPU Profiler**（Sampling 采样模式即可，开销小）
- 需要看内存时再勾 **Memory Profiler**（Allocation / Live objects）
- 确认 JDK 是 21

如果应用已经在跑，也可以用 **Run → Attach Profiler to Process**，选中那个 `java.exe`（主类 `com.example.trainticket.TrainTicketApplication`）。

## 3. 压测期间采样

Profiler 启动后，在项目根目录执行：

```bat
perf\run-load.bat 100 10 5 8080
```

大约 10~15 秒跑完。建议在跑到一半时观察 Profiler 的：

- **CPU**：火焰图里占比最高的调用栈
- **Memory**：堆占用、对象分配速率、GC 次数

采集 30~60 秒即可停止 Profiler（Stop）。

## 4. 重点看什么

按当前 JMeter 结果，预期热点是：

1. `org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder.matches`
   —— 登录密码校验，CPU 密集
2. `org.apache.catalina` / `org.apache.tomcat` 的 NIO 线程
   —— 请求接入与线程池排队
3. `com.zaxxer.hikari` 的连接获取
   —— 写并发升高时才明显（默认最大 10 连接）
4. `com.example.trainticket.service.*`
   —— 业务方法本身应该很薄；如果占比高，说明业务代码有问题

## 5. 保存证据

- Profiler 窗口右上角 **Export** 导出火焰图/快照
- 截图保存到 `docs/profiler/`（建议命名 `cpu-100-threads.png`、`memory-100-threads.png`）
- 在《性能测试报告》第 6 节补一句：热点方法、占比、结论

## 6. 注意

- Profiler 本身有开销，开了 Profiler 的 TPS 会比 141/s 低，这是正常的；Profiler 用来定位瓶颈，不用来出绝对性能数字
- 采样期间不要同时跑多个压测任务，避免 CPU 互相干扰
- 如果 IDEA 菜单里没有 Profile，确认用的是 Ultimate 版并安装了 Profiler 插件
