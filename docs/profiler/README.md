# JProfiler 采样证据（2026-11-03）

登录场景的 JProfiler 16.3 **CPU sampling（5 ms）** 结果，与 README 中作为主证据的 JFR
（`docs/figs/cpu-flamegraph-jfr.png`，BCrypt 89.4%）相互印证。

| 文件 | 内容 |
|------|------|
| `login-5min.jps` | 快照：50 线程 × 300 圈登录+查询，约 5 分钟，错误率 0% |
| `cpu-calltree.html` | CPU 调用树（按自时间排序；`HTTP: /login` 占 92.1%） |
| `cpu-hotspots.csv` | 热点自时间明细，`BCryptPasswordEncoder.matches` 占 **91.2%** |
| `jprofiler_images/` | 上面两个导出文件引用的图标资源，不要单独删除 |

## 已知限制：VM 遥测曲线没采到

`telemetry-cpu / threads / heap`（CPU 负载、线程数、堆内存曲线）在纯命令行控制下**导不出数据**：
应用以 `-agentpath:jprofiler.dll=port=34408` 在线启动后，用 `jpcontroller` 调用
`startVMTelemetryRecording` 两次，导出的 HTML 都只有坐标轴、没有数据线。该视图只在
**JProfiler GUI 会话**里可靠记录。

如果课程要求“实时内存曲线”截图，用 GUI 走一遍即可（5 分钟）：

1. 打开 `tools\jprofiler16\bin\jprofiler.exe` → Attach → 选 `TrainTicketApplication` 的 PID；
2. 左侧“遥测 / 实时内存”面板确认有曲线；点开始记录；
3. 同期跑 `perf/load-test.jmx`（50 线程）；
4. 结束后保存快照，导出 `TelemetryCPU / TelemetryThreads / TelemetryHeap` 到本目录。

资源侧数据可以先用 `docs/figs/resource-cpu.png`、`resource-mem.png`
（PowerShell 采样，10/20/50/100/200 五档阶梯）替代，那两张是有数据的。

## 复现命令

```bat
rem 1. 数据复位
mysql -u train_app -p train_ticket < perf\00_perf_seed.sql
mysql -u train_app -p train_ticket < perf\01_perf_reset.sql

rem 2. 录制控制（连 PID，采 330 秒后停止并保存快照）
tools\jprofiler16\bin\jpcontroller.exe -n -f jpc-cmds.txt <PID>

rem 3. 同时施压
tools\apache-jmeter-5.6.3\bin\jmeter.bat -n -t perf\load-test.jmx ^
  -l perf\results\prof3-login-5min.jtl -Jthreads=50 -Jramp=5 -Jloops=300

rem 4. 导出
tools\jprofiler16\bin\jpexport.exe docs\profiler\login-5min.jps ^
  "CallTree" -format=html docs\profiler\cpu-calltree.html ^
  "HotSpots" -format=csv  docs\profiler\cpu-hotspots.csv
```

本轮数字：主请求 TPS 158.4、事务/秒 52.8、平均 310 ms、P95 930 ms、P99 1010 ms、错误率 0%
（连续两轮 157.4 / 158.4 TPS）；与报告 §7.4 的 147.6 / 49.2 / 1024 ms 同量级，可复现。
