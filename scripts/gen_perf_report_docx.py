# -*- coding: utf-8 -*-
"""生成《性能测试报告.docx》：11 段式，图表内嵌。数据来自 JMeter JTL / 采样 CSV。"""
import csv
import os
import statistics
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "perf" / "results"
FIG = ROOT / "docs" / "figs"
OUT = Path(os.environ.get("OUT_DOCX", str(ROOT / "docs" / "性能测试报告.docx")))


def pct(values, p):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def metrics(path, only=None):
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8"))
            if not r["label"].endswith("-0") and not r["label"].endswith("-1")]
    if only:
        rows = [r for r in rows if r["label"] in only]
    e = [int(r["elapsed"]) for r in rows]
    ts = [int(r["timeStamp"]) for r in rows]
    start, end = min(ts), max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
    errors = sum(1 for r in rows if r["success"] == "false")
    return {
        "n": len(rows), "errpct": round(errors / len(rows) * 100, 2),
        "tps": round(len(rows) / ((end - start) / 1000), 1),
        "avg": round(statistics.mean(e), 1), "p90": pct(e, 90),
        "p95": pct(e, 95), "p99": pct(e, 99), "max": max(e),
    }


def load_resources():
    rows = list(csv.DictReader(open(RES / "resources-step5min.csv", encoding="utf-8-sig")))
    app_cpu = [float(r["app_cpu_pct"]) for r in rows]
    db_cpu = [float(r["mysql_cpu_pct"]) for r in rows]
    mem = [float(r["app_mem_mb"]) for r in rows]
    disk = [float(r.get("disk_pct") or 0) for r in rows]
    return {
        "points": len(rows),
        "app_cpu_avg": round(statistics.mean(app_cpu), 1), "app_cpu_max": max(app_cpu),
        "db_cpu_avg": round(statistics.mean(db_cpu), 1), "db_cpu_max": max(db_cpu),
        "mem_min": min(mem), "mem_max": max(mem), "mem_growth": round(mem[-1] - mem[0], 1),
        "disk_avg": round(statistics.mean(disk), 1), "disk_max": max(disk),
    }


def parse_status(path):
    data = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            data[parts[0]] = parts[1]
    return data


doc = Document()
section = doc.sections[0]
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(2.0)
section.left_margin = Cm(2.2)
section.right_margin = Cm(2.2)

normal = doc.styles["Normal"]
normal.font.name = "微软雅黑"
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
normal.paragraph_format.line_spacing = 1.35
normal.paragraph_format.space_after = Pt(6)

for name, size, color in (("Heading 1", 18, "1A4D8F"),
                          ("Heading 2", 14, "1A4D8F"),
                          ("Heading 3", 12, "2F5FA8")):
    st = doc.styles[name]
    st.font.name = "微软雅黑"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor.from_string(color)


def h(text, level=1):
    doc.add_heading(text, level)


def p(text, bold=False, align=None, size=None):
    para = doc.add_paragraph()
    if align:
        para.alignment = align
    run = para.add_run(text)
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    return para


def bullet(text):
    doc.add_paragraph(text, style="List Bullet")


def table(headers, rows, widths=None, font_size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = not bool(widths)
    for i, htext in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        r = cell.paragraphs[0].add_run(str(htext))
        r.bold = True
        r.font.size = Pt(font_size)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(value))
            r.font.size = Pt(font_size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()


def pic(name, caption, width=16.0):
    path = FIG / name
    if not path.exists():
        p(f"[缺少图片：{name}]")
        return
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.add_run().add_picture(str(path), width=Cm(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x5A, 0x67, 0x78)


# ---------------- 封面 ----------------
p("火车票预订系统", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=24)
p("性能测试报告", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=22)
p("JMeter 5.6.3 · Spring Boot 3.4.4 · MySQL 8.4.6", align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
p("测试日期：2026-10-26 ～ 2026-10-28（各场景见第 5 节；连接池 A/B 见第 7.8 节）",
  align=WD_ALIGN_PARAGRAPH.CENTER, size=11)
p("被测代码 commit：f56cd15", align=WD_ALIGN_PARAGRAPH.CENTER, size=11)
p("报告中的曲线均由 JMeter JTL / 资源采样 CSV 生成；原始数据、脚本与 JMeter 原生 HTML 报告见第 11 节。",
  align=WD_ALIGN_PARAGRAPH.CENTER, size=9)
doc.add_page_break()

# ---------------- 1 ----------------
h("1. 测试背景")
p("本项目是《性能测试项目实战》课程的实战作业。被测系统是一个自建的火车票预订 Java Web 应用"
  "（Spring Boot + MySQL），核心业务包括登录、车次查询、下单、退票和管理后台。")
p("课程 PPT 的演示案例是电商系统（商品查询 + 创建订单）。本项目按同一套方法论换成火车票系统，"
  "指标阈值沿用 PPT 第 9 页的通用指标（平均 < 500 ms、P95 < 1000 ms、TPS > 200、错误率 < 0.1%、"
  "CPU < 80%），没有照搬案例 A/B 的 250/300 TPS、300/500 ms 阈值。", size=9)
p("本次压测回答三个问题：")
bullet("当前系统在并发访问下是否稳定？")
bullet("平均响应、P95、TPS、错误率、CPU 是否达到目标？")
bullet("如果不达标，瓶颈在应用、数据库还是其他资源？")

# ---------------- 2 ----------------
h("2. 测试环境")
table(["项目", "配置"], [
    ["操作系统", "Windows 11，16 逻辑核"],
    ["JDK", "Oracle JDK 21.0.11"],
    ["应用", "Spring Boot 3.4.4，内嵌 Tomcat 10.1.39"],
    ["数据库", "MySQL 8.4.6，本机 3306"],
    ["连接池", "HikariCP 默认最大 10 连接"],
    ["压测工具", "Apache JMeter 5.6.3（非 GUI）"],
    ["监控", "JFR（主证据）、JProfiler 16.3 CPU sampling（2026-11-03 登录场景复测）、PowerShell（CPU/内存/磁盘 IO）、MySQL 慢查询状态"],
    ["应用端口", "8080（MySQL 模式）"],
    ["Thymeleaf", "spring.thymeleaf.cache=false（开发配置，结果偏保守）"],
    ["资源采样", "名义 2 秒/点，实际约 4.6 秒/点（1715 秒 / 374 点）"],
], widths=[3.2, 12.0], font_size=9)
p("压测机与被测应用同机，JMeter 自身会占用 CPU；结果偏保守。阶梯压测期间没有单独采集 JMeter 进程 CPU "
  "与整机 CPU（JFR 的 35 秒窗口不能代表 25 分钟阶梯），因此“应用未打满”不能直接推出“系统还有余量”。", size=9)

# ---------------- 3 ----------------
h("3. 测试范围")
table(["业务", "接口", "读/写"], [
    ["登录", "GET /login、POST /login", "读"],
    ["车次查询", "POST /trains/search", "读"],
    ["下单", "POST /orders", "写"],
    ["退票 / 管理后台", "POST /orders/{id}/refund、/admin/**", "写/管理"],
], widths=[4.0, 9.5, 2.0])
p("不纳入本次压测：第三方支付回调、真实外部依赖、多节点集群、网络延迟模拟。"
  "下单/退票的正确性用 JUnit 并发测试单独验证；JUnit 运行在 H2 内存库上，不覆盖 MySQL 行锁行为。")

# ---------------- 4 ----------------
h("4. 性能指标")
table(["指标", "目标", "说明"], [
    ["平均响应时间", "< 500 ms", "所有主请求平均耗时"],
    ["P95 响应时间", "< 1000 ms", "95% 请求低于该值"],
    ["TPS", "> 200", "每秒完成的主请求数；口径见下"],
    ["错误率", "< 0.1%", "断言失败 / HTTP 异常占比"],
    ["CPU 使用率", "稳定 < 80%", "应用进程 CPU（16 核总量）"],
    ["数据一致性", "不超卖、不丢单", "库存与订单数一致"],
], widths=[3.2, 4.0, 8.0])
p("TPS 口径（重要）：本报告的 TPS 一律指 JMeter 主请求/秒，不含重定向子样本（-0 / -1）。"
  "查询场景 1 次业务 = 1 个 POST /trains/search；登录+查询场景 1 次业务 = 3 个主请求"
  "（GET /login、POST /login、POST /trains/search），因此另列“事务/秒”= TPS ÷ 3；"
  "混合场景按全部主请求计。不能把登录场景的 147.6 与查询场景的 1485 直接当成同一口径比较。"
  "百分位算法：P90/P95/P99 用线性插值（k=(n-1)·p/100，在相邻两样本之间取值），与 perf/analyze_*.py、summarize_step_load.py 一致。JMeter 原生 HTML 报告用另一套取样算法，"
  "同一份 step-100.jtl 两边 P90/P95/P99 为 115/138/188 与 117/140/194，差 2~6 ms，属算法差异而非数据错误。")

# ---------------- 5 ----------------
h("5. 测试场景")
table(["场景", "并发", "时长 / 循环", "执行时间", "说明"], [
    ["基准 + 阶梯（查询）", "10/20/50/100/200", "每档 5 分钟", "2026-10-27", "登录一次后循环查询"],
    ["混合（查询 + 下单）", "50 查询 + 10 下单", "60 秒", "2026-10-26", "两个独立线程组"],
    ["登录+查询对比", "10/50/100/200", "10/10/5/5 圈", "2026-10-26", "每次迭代重新登录"],
    ["登录+查询持续", "50", "100 圈 / 102 秒", "2026-10-26", "唯一的稳态登录场景"],
    ["并发下单", "10", "集合点 / 约 1 秒", "2026-10-26", "同一座位 9001，库存 1000"],
    ["并发正确性", "50 抢 10 张票", "JUnit（H2）", "2026-10-26", "成功数必须等于 10"],
], widths=[3.4, 3.2, 3.2, 2.6, 4.2], font_size=8.5)
p("脚本结构：Test Plan → 线程组（查询 / 下单分开）→ HTTP Request Defaults + Cookie Manager + "
  "CSV Data Set → HTTP 请求 → Response Assertion。")
p("正式压测用 -n 非 GUI，关闭 View Results Tree 等 GUI 监听器，只保留 JTL 和 -e -o HTML 报告。"
  "登录请求排在业务请求之前，Cookie Manager 保持 JSESSIONID。")
p("断言：JMeter 默认把 4xx/5xx 判为失败；脚本还对响应体断言“车次查询 / 查询结果 / 购票成功”，"
  "并断言查询结果不能是空结果。被测系统返回 HTML、没有业务 code，关键字段断言就是业务成功判据。")
p("场景执行时间不统一是本次局限：阶梯在 10-27，混合/登录/下单在 10-26；机器负载与 JVM 状态没有控制，"
  "跨场景的绝对 TPS 不宜直接比较。", size=9)

# ---------------- 6 ----------------
h("6. 测试数据")
table(["数据", "内容"], [
    ["用户", "perf01 ~ perf20，密码统一 Pass123"],
    ["线路", "5 条：北京南↔上海虹桥、广州南→深圳北、成都东→重庆北、武汉→长沙南"],
    ["席别/价格", "每条线路 二等座 / 一等座 / 商务座，价格不同"],
    ["座位", "5 条线路 × 3 席别 = 15 行 train_seats"],
    ["库存", "二等座 1000、一等座 200、商务座 50"],
    ["参数化", "users.csv、routes.csv、booking.csv，均设置 ignoreFirstLine=true"],
], widths=[3.2, 12.0])
p("数据规模与代表性：")
bullet("users.csv 有 20 行，但放在 Once Only Controller 里、shareMode=thread；每个线程各自从第 1 行开始，"
       "而登录只读一次，所以 200 个线程实际都读 perf01。名义 20 账号，实际单账号。")
bullet("booking.csv 同理：下单组只跑 1 圈，10 个线程都读第一行 perf01 / 9001，实际同一账号、同一座位；"
       "booking.csv 其余行未使用。")
bullet("routes.csv 放在 Loop Controller 里，每次查询读下一行，线路会轮换；但所有线程都从同一条线路开始，"
       "按同一顺序推进，仍是一个很小的热点集合。")
bullet("load-test.jmx 更直接：所有线程固定 alice01 和“北京南→上海虹桥”，用于隔离 BCrypt 成本，不是多用户场景。")
bullet("15 行座位可以全部驻留 InnoDB buffer pool，查询路径没有磁盘 IO 压力。")
bullet("因此 1485 TPS 是“单账号/小线路集合 + 全缓存 + 无思考时间”下的上限，不能外推为生产容量。")

# ---------------- 7 ----------------
h("7. 执行结果")
h("7.1 阶梯加压（查询，每档 5 分钟）", 2)
step_rows = list(csv.DictReader(open(RES / "step-load-summary.csv", encoding="utf-8")))
table(["线程数", "请求数", "TPS", "平均", "P90", "P95", "P99", "最大", "错误率"],
      [[r["threads"], f"{int(r['requests']):,}", r["tps"], r["avg"],
        r["p90"], r["p95"], r["p99"], r["max"], f"{r['errpct']}%"] for r in step_rows],
      widths=[2.2, 2.0, 1.8, 1.6, 1.4, 1.4, 1.4, 1.8, 1.6], font_size=8.5)
pic("step-load-tps.png", "图 7-1  阶梯加压 TPS 曲线（10/20/50/100/200，每档 5 分钟）")
pic("step-load-p95.png", "图 7-2  阶梯加压 P95 响应时间曲线")
p("20 线程后 TPS 见顶（1473.9），50/100/200 维持在 1463~1485；平均响应从 12.7 ms 涨到 132.7 ms，"
  "P95 从 25 ms 涨到 295 ms，是明显的“吞吐见顶、延迟上升”。五档共 2,131,310 个查询，错误率 0%。")
p("关于 4～5 秒最大响应：10/50/100/200 档都在某一秒出现一批 4～5 秒请求——10 档 10 个、50 档 50 个、"
  "100 档 100 个、200 档 200 个，恰好都是“每线程 1 个”；20 档没有。资源采样在 15:49:25→15:49:34 出现 9 秒空档，"
  "100/200 档也有 7～15 秒空档，而应用 CPU 没有掉到 0。这个形态更像 JMeter 或整机的 stop-the-world，"
  "不是应用持续变慢：P99 只有 14～417 ms，错误率仍为 0。本轮没有采 GC 日志，无法区分 JMeter GC、"
  "应用 GC 还是系统调度，因此不下“应用 GC 抖动”的结论。")

h("7.1.1 为什么 TPS 远高于目标 200？", 3)
bullet("200 是准入下限，不是上限。超过 200 表示查询接口容量足够。")
bullet("这是轻量只读接口的容量测试：登录一次后循环查询，没有写库、支付或外部依赖，数据只有 5 条线路；"
       "10 线程时单请求 7.4 ms，20 线程时 12.7 ms。")
bullet("脚本没有加思考时间，线程连续发请求；TPS 衡量服务端吞吐上限，不是真实用户点击频率。")
bullet("完整业务链路：登录+查询主请求 TPS 147.6、事务 49.2/s（未达标）；混合 535；纯查询 1485。")
bullet("1485 是当前配置下的实测平台，不是系统容量：第 7.8 节的 pool 10→30 对照只提升约 6%，"
       "说明连接池不是主限制器；最可能是同机 JMeter 客户端（未量化），其次是应用 CPU/模板渲染。")

h("7.2 TPS / 错误率时间曲线（100 线程档）", 2)
pic("step-100-tps.png", "图 7-3  100 线程 5 分钟 TPS 时间曲线")
pic("step-100-error.png", "图 7-4  100 线程 5 分钟错误率时间曲线（全程 0%）")
p("100 线程 5 分钟内，除 250 秒附近一个 10 秒窗口掉到约 905 TPS（与 4.2 秒毛刺同源）外，"
  "TPS 稳定在 1500 左右，错误率全程 0%，没有出现随时间恶化。第一段 0–10 秒是 5 秒 ramp-up，"
  "TPS 只有 807，不计入稳态。")

h("7.3 混合场景（50 查询 + 10 下单，60 秒）", 2)
mixed = metrics(RES / "mixed.jtl")
table(["范围", "请求数", "TPS", "平均", "P90", "P95", "P99", "最大", "错误率"], [
    ["全部", mixed["n"], mixed["tps"], mixed["avg"], mixed["p90"], mixed["p95"],
     mixed["p99"], mixed["max"], f"{mixed['errpct']}%"],
], widths=[2.2, 2.0, 1.8, 1.6, 1.4, 1.4, 1.4, 1.8, 1.6], font_size=8.5)
p("10 个并发下单全部成功，订单数 10，库存 1000 → 990（10 个线程都读 booking.csv 第一行，实际同一账号 perf01、"
  "同一座位 9001；库存/订单数以数据库为准，本轮没有单独落盘 SQL 快照）。混合场景 TPS 535.4、平均 89.7 ms、"
  "P95 166 ms、错误率 0%，在 60 秒短跑口径下达标。")
p("TPS 按 JTL 主请求统计；JMeter 原生 HTML 汇总显示 530.0（32,077 个样本，含重定向子样本），"
  "差异来自重定向样本过滤与计时口径。")
p("与阶梯 50 线程档不可直接比较：同样是 50 个查询线程，阶梯档是 1463 TPS / 33.1 ms，"
  "混合场景只有 538 TPS / 88.3 ms，相差约 2.7 倍。按 10 秒粒度检查，60 秒内每段都是 82～108 ms，"
  "不是“登录启动瞬间”造成的；两次执行时间不同（混合 10-26、阶梯 10-27），JVM 状态、机器负载没有控制。"
  "本场景只用于验证“混合负载下无错误、下单成功”，不作为容量数字。")

h("7.4 登录+查询对比（每次迭代重新登录）", 2)
table(["线程数", "主请求数", "TPS（主请求/秒）", "事务/秒", "平均(ms)", "P95(ms)", "错误率"], [
    ["10", "300", "49.2", "16.4", "54.2", "145", "0%"],
    ["50", "1500", "132.7", "44.2", "48.1", "138", "0%"],
    ["100", "1500", "141.1", "47.0", "47.9", "142", "0%"],
    ["200", "3000", "131.9", "44.0", "256.6", "892", "0%"],
    ["50（持续 102s）", "15000", "147.6", "49.2", "324.5", "1024", "0%"],
], widths=[2.6, 2.2, 2.6, 2.2, 2.2, 2.2, 2.0], font_size=8.5)
p("每次迭代做 3 个主请求，因此事务/秒 = TPS ÷ 3；稳态下每秒只有约 49 次登录+查询，"
  "与 200 的目标差距很大。持续压测主请求 TPS 147.6 < 200、P95 1024 ms > 1000 ms，两种口径都未达标。"
  "加线程到 200，TPS 反而下降，说明不是线程不够，而是登录计算把 CPU 吃满。")
p("10/50/100/200 四行分别只有 10/10/5/5 圈，且 10 线程那档总时长仅 6.1 秒、约一半是 5 秒 ramp-up；"
  "只有 50 线程持续 102 秒那行是稳态，其余行的 TPS 不宜当作稳态容量。本场景固定使用 alice01 和单条线路，"
  "用于隔离 BCrypt 成本；多账号/多线路版本是 scenario-query.jmx。")

h("7.5 并发下单与数据一致性", 2)
book = metrics(RES / "book2.jtl")
p(f"10 线程集合点同时下单：30 个主请求，TPS {book['tps']}，平均 {book['avg']} ms，"
  f"P95 {book['p95']} ms，错误率 0%。10 个线程都使用同一座位 9001、同一账号 alice01，库存 1000；"
  "10 单全部成功，不是“抢最后几张票”的竞争场景，不能证明 MySQL 下的超卖行为。")
p("JUnit：余票 10，50 并发抢，成功 10 单、40 个“余票不足”、库存 0、订单 10 条；"
  "退票后库存回补，重复退票被拒绝。JUnit 使用 @ActiveProfiles(\"h2\")，验证的是 H2 上的原子 "
  "UPDATE ... WHERE stock > 0；MySQL 行锁/事务隔离下的同一行为没有在 JUnit 中覆盖，"
  "建议补一条 MySQL 版用例。")

h("7.6 资源监控", 2)
res = load_resources()
pic("resource-cpu.png", "图 7-5  应用 JVM 与 MySQL CPU 曲线（目标线 80%；灰底为档间间隙，曲线在此断开）")
pic("resource-mem.png", "图 7-6  应用 JVM 与 MySQL 内存曲线")
before = parse_status(RES / "db-status-before.txt")
after = parse_status(RES / "db-status-after.txt")
table(["资源", "采样结果", "判断"], [
    ["应用 CPU", f"平均 {res['app_cpu_avg']}%（含档间空闲；仅计有效压测区间约 32.1%），峰值 {res['app_cpu_max']}%", "有压力，但未打满"],
    ["MySQL CPU", f"平均 {res['db_cpu_avg']}%（仅计有效压测区间约 19.7%），峰值 {res['db_cpu_max']}%", "不高"],
    ["磁盘 IO", f"平均 {res['disk_avg']}%，峰值 {res['disk_max']}%", "平均很低，不是瓶颈"],
    ["应用内存", f"{res['mem_min']:.0f} ~ {res['mem_max']:.0f} MB，增长 {res['mem_growth']:.0f} MB", "需持续观察，但未 OOM"],
    ["慢查询", f"long_query_time={float(after.get('long_query_time', '10')):g}s，"
               f"Slow_queries={after.get('Slow_queries', '0')}", "只能说明没有 >10s 的 SQL"],
    ["行锁", f"Innodb_row_lock_waits={after.get('Innodb_row_lock_waits', '28')}", "读场景为主，不能代表写并发"],
    ["数据库吞吐", f"Questions {int(before.get('Questions', 0)):,} → {int(after.get('Questions', 0)):,}",
     "25 分钟测试期估算约 12,714 QPS"],
    ["每请求 SQL", "19,070,870 ÷ 2,131,310 ≈ 8.9 条/请求", "3 次只读查询 + 事务开销"],
    ["连接池", f"Threads_connected={after.get('Threads_connected', '11')}（pool10）；第 7.8 节 pool30 为 31", "池确实被占满，但扩到 30 只 +6%，不是主限制器"],
], widths=[3.0, 8.4, 4.4], font_size=8)
p("资源采样名义 2 秒，实际约 4.6 秒/点，且阶段切换处有 7～15 秒空档；峰值可能被漏采。"
  "应用 JVM 与 MySQL 都远低于 80%，这恰恰说明限制器不在“CPU 打满”，需要继续往下找（见第 8 节）。")
pic("jmeter-html-step-100-fullhd.png", "图 7-7  JMeter 原生 HTML 报告 1920×1080 全屏截图（100 线程档）")

h("7.7 本报告的局限与未验证项", 2)
bullet("连接池对照已补做，客户端限制仍未量化：2026-10-28 的 A/B（第 7.8 节）显示 pool 10→30 只提升约 6%，"
       "排除连接池作为主限制器；但本轮仍未单独采 JMeter 进程 CPU 和整机 CPU，无法定量确认“同机客户端”就是剩余限制器，"
       "也没有做第二台压测机/分布式压测。")
bullet("慢查询阈值过粗：long_query_time=10s，不能证明没有 100ms～1s 的慢 SQL。")
bullet("数据规模小，且 CSV 参数化实际未生效：名义 20 账号、5 线路、15 座位；但 users.csv / booking.csv "
       "放在 Once Only 或单圈下单组里、shareMode=thread，所有线程都读第一行——CSV 场景的登录实际全是 perf01"
       "（load-test.jmx 固定 alice01），下单全是 perf01/9001；routes.csv 在循环里会轮换，但所有线程从同一条线路开始。"
       "1485 TPS 是单账号/小线路集合 + 全缓存下的上限，不是生产容量。")
bullet("场景执行时间不统一：阶梯 10-27，混合/登录/下单 10-26；混合与阶梯的 50 线程结果相差 2.7 倍，未做根因分析。")
bullet("4～5 秒毛刺未根因定位：没有 GC 日志，无法区分 JMeter GC、应用 GC 与主机暂停。")
bullet("写路径未做容量测试：只有 10 单的链路验证和 H2 上的 50 抢 10 正确性测试；MySQL 行锁、"
       "连接池在写并发下的表现未验证。")
bullet("JProfiler 采样已补采，但 VM 遥测曲线缺采：2026-11-03 对登录场景（50 线程、5 分钟、0% 错误）做 CPU sampling，"
       "快照 docs/profiler/login-5min.jps，自时间统计中 BCryptPasswordEncoder.matches 占 91.2%（12,270s/13,447s），与 JFR 的 89.4% 相互印证；"
       "该轮主请求 TPS 158.4、事务/秒 52.8、P95 930 ms。遥测（CPU/线程/堆）曲线在纯命令行控制下导出为空图，"
       "只可靠记录于 GUI 会话，因此资源侧证据仍以 JFR + PowerShell 采样为准。")
bullet("库存/订单数没有独立证据文件：1000→990、10 条订单来自 JTL 成功样本与数据库查询，本轮没有把前后 SQL 快照落盘。")
bullet("Questions 增量窗口未严格对齐：压测前后状态采集跨越 14:30→16:19（约 109 分钟），不是严格 25 分钟；"
       "增量 19,070,870 与 2,131,310 × 8.9 吻合，空闲期贡献可忽略，但 QPS 只能写成“按约 25 分钟测试期估算”。")
bullet("JMeter 共享模式选择不当：users.csv / booking.csv 用 shareMode=thread，在“每线程只读一次”的场景里"
       "不会分流行，正确做法是 shareMode=group（组内共享指针）或按线程号预分配账号。本轮结果保留原样，"
       "下一轮复测需改。")
p("这些局限不影响“登录 BCrypt 是登录场景瓶颈”的结论（JFR 89.4%，证据强），"
  "但会影响“查询容量 1485”的表述。报告按“当前配置下的实测上限”处理，并给出复测方法。", size=9)

h("7.8 连接池对照实验（2026-10-28）", 2)
p("为验证“1485 是 HikariCP 10 连接上限”的假设，在同一台机器、同一份数据、同样 thymeleaf.cache=false 下做 A/B：")
bullet("对照组：--spring.datasource.hikari.maximum-pool-size=10；实验组：30。")
bullet("每档 50 / 100 线程 × 5 分钟；keep_awake + 关闭 AC 睡眠；取 60–300 秒稳态，避免 JIT 预热段。")
table(["连接池", "线程", "请求数", "稳态 TPS", "平均(ms)", "P95", "P99", "错误率", "应用 CPU", "MySQL CPU"], [
    ["10", "50", "351258", "1471.6", "33.2", "75", "103", "0%", "34.4%", "20.0%"],
    ["30", "50", "374571", "1573.4", "30.8", "83", "113", "0%", "35.2%", "21.2%"],
    ["10", "100", "359521", "1503.8", "65.8", "163", "237", "0%", "34.5%", "20.8%"],
    ["30", "100", "380398", "1590.7", "61.9", "162", "219", "0%", "35.2%", "21.3%"],
], widths=[1.6, 1.4, 1.9, 1.8, 1.7, 1.2, 1.2, 1.4, 1.7, 1.7], font_size=7.5)
p("50 线程稳态 TPS 1471.6 → 1573.4（+6.9%），100 线程 1503.8 → 1590.7（+5.8%）；"
  "平均 RT 只降 5.9%–7.2%，50 线程 P95 反而从 75 ms 升到 83 ms；应用 CPU 34.4%→35.2%，MySQL 20.0%→21.2%。")
p("结论：连接池不是 1485/1504 平台期的主限制器；之前“10 连接 ÷ 6.74 ms ≈ 1483 TPS”只是数字巧合。"
  "扩池只带来约 6% 提升，限制器最可能是同机 JMeter 客户端（本轮未采客户端 CPU），其次是应用 CPU/模板渲染。")
p("数据：perf/results/pool10-*.jtl、pool30-*.jtl、pool-ab.md、*-resources.csv。", size=9)

def _mono(text):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.35)
    for i, line in enumerate(text.strip("\n").split("\n")):
        if i:
            para.add_run("\n")
        r = para.add_run(line)
        r.font.name = "Consolas"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        r.font.size = Pt(9)


h("7.9 功能正确性测试（Selenium 25 条）", 2)
p("本节回答的不是“多快”，而是“对不对”。性能数字只在功能正确的前提下有意义："
  "如果下单接口在高并发下返回 200 却没有落库，TPS 再高也是无效吞吐。")
p("用例在 functional_tests/，25 条，用 Selenium + pytest 驱动真实浏览器（Chrome/Edge，默认无头）。"
  "覆盖：登录 4、注册 5、查票 5、下单 5、退票 2、管理后台 4。运行方式：")
_mono("cd functional_tests\n"
      "..\\.venv-tests\\Scripts\\python.exe -m pytest -v --html=report.html --self-contained-html")
p("实测结果 25 passed（35.5 秒）。报告 functional_tests/report.html 由 pytest-html 插件在运行结束时自动生成，"
  "--self-contained-html 把样式与脚本内联成单文件；重跑即整份覆盖。它是运行快照，不含结论文字，"
  "结论需要按下面的断言层级去读。")
p("每条用例都是四步：按 id / name / css 定位元素 → 填表点击 → 显式等待（WebDriverWait，不用 sleep）→ 断言。"
  "断言分四层，越往下越硬：")
table(["层级", "断言对象", "例子"], [
    ["页面跳转", "current_url", "下单后 URL 变成 /orders"],
    ["页面内容", "DOM 文本 / 提示条", ".msg.success 含“购票成功”、页面出现“已支付”"],
    ["数据库", "MySQL 实际值", "点单前后各查一次 train_seats.stock，断言正好少 1（座位 9101）"],
    ["接口响应", "HTTP 响应体", "带登录 Cookie POST /orders 打座位 9102，断言含“该车次余票不足”"],
], widths=[2.6, 4.6, 8.4], font_size=8.5)
p("数据层断言是这套用例最关键的部分：它把 浏览器点击 → Controller → BookingService → "
  "UPDATE ... WHERE stock > 0 → MySQL 整条链路锁死，页面提示成功但事务回滚会被判失败。"
  "退票用例同样断言库存回补、重复退票不再加库存。")
p("3 条失败分支用例通过接口而非 UI 触发：座位 9102 余票为 0，页面按钮点不动，"
  "只能用 api_session 把浏览器 Cookie 复制到 requests.Session 后直接 POST /orders，"
  "验证后端校验分支的提示文案（余票不足、座位不存在、乘客姓名必填）。")
p("选择器与 Java 模板是同一份契约（如 By.ID \"btn-login\" ↔ templates/login.html:50，"
  ".nav .user ↔ templates/fragments/layout.html:10，.msg.error ↔ 各页面提示条），模板改 id 用例即失败。"
  "这正是 JUnit 覆盖不到的部分：Controller 路由、Spring Security 过滤器链、Thymeleaf 渲染。", size=9)
p("三者分工：JUnit（第 7.5 节）验并发控制与退票幂等（H2）；Selenium 验端到端行为（真实 MySQL + 浏览器）；"
  "JMeter 验容量（第 7.1～7.4 节）。三份证据互不替代。", size=9)

# ---------------- 8 ----------------
h("8. 瓶颈分析")
p("四步判断的顺序不能颠倒，否则容易误判：")
bullet("第一步看错误率：出现 5xx / 连接池耗尽说明系统已经硬失败，先修可用性，谈延迟没有意义。")
bullet("第二步看延迟：错误率为 0 但 P95 超阈值，说明系统在工作但用户已感知慢。")
bullet("第三步看吞吐拐点：加线程 TPS 不再涨，说明到达平台期，继续加线程只会堆延迟。")
bullet("第四步才看资源：定位这个平台期被谁卡住。")
p("顺序的依据：只有先把“失败 / 慢 / 到顶”区分开，资源数据才有解释力。"
  "CPU 不高既可能是“还有余量”，也可能是“瓶颈在别处”（本轮就是后者），"
  "必须先有吞吐拐点，才能判断资源指标的归属。")
p("四步的具体判断结果：")
p("第一步：错误率是否超标？否。查询、混合、下单场景错误率均为 0%，没有连接池耗尽报错、限流或 5xx。")
p("第二步：P95 是否超标？查询 200 线程 P95 295 ms，混合 166 ms，均低于 1000 ms；"
  "登录+查询持续 50 线程 P95 1024 ms，超过目标 2.4%，是唯一超标场景。这个 P95 是 3 个主请求混合后的分布，"
  "主要由 POST /login（P95 1103 ms）贡献。")
p("第三步：并发增加时 TPS 还涨吗？查询 10→20 线程 TPS 1221→1474；20→50→100→200 基本平在 "
  "1463~1485，20 线程后进入平台区。登录+查询主请求 TPS 在 132~148 徘徊，事务率 44~49/s，"
  "继续加线程没有收益。")
p("第四步：服务器资源是否异常？应用 CPU 平均 27.3%（含档间空闲，仅计有效压测区间约 32.1%）、峰值 43.2%；MySQL CPU 平均 16.7%、"
  "峰值 27.8%；磁盘 IO 平均 4.6%；没有 >10s 的 SQL；行锁无新增。应用和 MySQL 都没有打满。")
p("平台期的归因（已做对照，结论反转）：第 7.8 节在同一台机器、同一份数据上把 HikariCP 从 10 扩到 30，"
  "50 线程稳态 TPS 1471.6 → 1573.4（+6.9%），100 线程 1503.8 → 1590.7（+5.8%）；"
  "平均 RT 只降 5.9%–7.2%，50 线程 P95 反而从 75ms 升到 83ms；应用 CPU 34.4%→35.2%，MySQL 20.0%→21.2%。"
  "连接池不是 1485/1504 平台期的主限制器；之前“10 连接 ÷ 6.74ms ≈ 1483 TPS”只是数字巧合。")
table(["候选", "证据", "强度"], [
    ["同机 JMeter 客户端", "扩池只 +6%；应用/MySQL 均未饱和；平台期与线程数无关；本轮未采客户端 CPU", "最可能（未量化）"],
    ["应用 CPU / Thymeleaf 渲染", "35% 应用 CPU；thymeleaf.cache=false", "中"],
    ["其他共享资源（网络/OS/磁盘）", "未单独采", "低"],
    ["HikariCP 10 连接", "第 7.8 节扩到 30 只 +6%", "已排除"],
    ["登录 BCrypt", "JFR 89.4%；登录场景事务率仅 49/s", "强（仅对登录场景）"],
    ["MySQL 服务 CPU / 慢 SQL", "CPU 平均 20–21%；没有 >10s 的 SQL", "强（MySQL 服务本身不是 CPU 瓶颈）"],
], widths=[5.2, 7.6, 3.4], font_size=8)
table(["JFR 项目", "数据"], [
    ["ExecutionSample", "1646 个"],
    ["栈顶为 BCrypt.encipher", "1472 个（89.4%）"],
    ["包含 BCryptPasswordEncoder.matches", "1546 个（93.9%）"],
    ["JVM 用户态 CPU", "平均 23.5%，峰值 40.6%"],
    ["机器总 CPU（含 JFR/JMeter）", "平均 59.9%，峰值 77.2%"],
    ["压测后堆", "48 MB used / 180 MB total"],
], widths=[7.0, 8.4])
pic("cpu-flamegraph-jfr.png", "图 8-1  CPU 火焰图（1646 个 JFR ExecutionSample，条宽=样本数，BCrypt.encipher 占 89.4%）")
p("主证据是 JFR；2026-11-03 的 JProfiler CPU sampling（docs/profiler/）给出 91.2% 的独立印证。", size=9)
p("证据链结论：")
bullet("查询路径 TPS 能到约 1500；第 7.8 节把连接池从 10 扩到 30 只提升 6%，说明 Tomcat 线程数和连接池都不是主限制；"
       "限制器最可能在同一台机器上的 JMeter 客户端（本轮未量化）或另一个未采的共享资源。")
bullet("登录场景的事务率只有约 49/s，主请求 TPS 147.6；把登录移出循环后，查询能到 1400+（事务率约 1485/s），"
       "差距约 30 倍（不是 10 倍）。")
bullet("JFR 显示应用 CPU 的 89.4% 花在 BCrypt.encipher，MySQL CPU 只有 16.7%，没有 >10s 的 SQL。")
bullet("因此：登录场景的瓶颈是应用层 BCrypt 密码校验（强证据）；查询场景的连接池假设已被第 7.8 节的 A/B 推翻，"
       "剩余最可能是同机 JMeter 客户端（待采客户端 CPU/分布式压测确认），"
       "不是 MySQL 服务 CPU、不是磁盘 IO、不是线程不足。")
p("应用进程 CPU 只有 43.2%，是因为压测机同时跑 JMeter、MySQL、IDE 等；43.2% × 16 核≈6.9 核，"
  "已经集中在登录计算上。JFR 比整体 CPU 百分比更能说明问题。但不能用“应用 CPU 没到 80%”"
  "直接推出“系统还有余量”，因为同机客户端也在这 16 核里。")

# ---------------- 9 ----------------
h("9. 风险结论")
p("这张表怎么读：三列分别对应“结论（能不能上线）”“依据（实测数字）”“风险（这个结论的边界条件）”。"
  "“达标”一律以第 4 节的阈值为准，不随场景另立标准；风险列写的是数字之外的前提，"
  "例如“库存充足、单账号同座位”意味着下单并发只验证了链路，没验证竞争。")
table(["场景", "结论", "风险"], [
    ["查询（20~200 并发）", "达标，阶梯基线 TPS 1463~1485，P95 25~295 ms",
     "1485 是同机压测配置下的实测平台；pool 10→30 只 +6%，连接池不是主限制器，客户端限制待量化"],
    ["混合（50 查询 + 10 下单）", "60 秒短跑达标，TPS 535、P95 166 ms",
     "与阶梯 50 线程档相差 2.7 倍，绝对 TPS 不可比"],
    ["登录+查询", "不达标，事务 49/s、主请求 147.6/s、P95 1024 ms",
     "登录高峰会抢占 CPU，可能拖慢查询/下单；BCrypt 占 89.4% CPU"],
    ["下单并发", "10 单成功、不超卖",
     "库存充足、单账号同座位，不是竞争场景；MySQL 写并发容量未测"],
], widths=[4.0, 6.0, 6.0], font_size=8.5)
p("总体判断：查询和混合业务的功能链路可以上线；连接池对照已完成（+6%，排除池），但客户端 CPU 仍未采，"
  "当前只能写“同机压测配置下实测约 1500 TPS，不能称为系统容量”。登录链路需要先优化/限流，"
  "否则登录高峰会把事务率限制在 50 左右。本次为单机单实例，且压测机与应用同机；集群容量需另测。"
  "应用内存 28 分钟增长 135 MB，建议上线后持续观察 Full GC 和堆曲线。")

# ---------------- 10 ----------------
h("10. 优化建议与复压验收")
p("优先级按“先保可用性、再挤吞吐、最后扩数据”排：P0 是不做就会在高峰出故障的（登录不限流会打满 CPU、"
  "把查询一起拖垮，且必须采客户端 CPU 才能判断平台期归属）；P1 是确定性收益的优化（缓存站点下拉、"
  "打开模板缓存、降 BCrypt cost、多实例化）；P2 / P3 是让结论更可信的验证项（扩数据、复核索引）。"
  "P0 不做，P1 的收益会被登录高峰吃掉。")
table(["优先级", "措施", "预期"], [
    ["P0", "登录限流：/login 单实例限制请求速率，超限 429 + Retry-After", "防止登录高峰打满 CPU、拖垮查询"],
    ["P0", "读场景复用会话：登录一次后查询", "事务率从 49/s 提升到 1400+/s（约 30 倍）"],
    ["P0", "采 JMeter 进程 CPU + 整机 CPU；或用第二台压测机/分布式压测", "判断 ~1500 TPS 平台期是否同机客户端限制（连接池已排除）"],
    ["P1", "缓存站点下拉：fromStations / toStations 改为启动加载或本地缓存", "每请求 SQL 从 ~9 条降到 ~3 条"],
    ["P1", "压测/生产 profile 打开 spring.thymeleaf.cache=true", "减少模板解析 CPU"],
    ["P1", "压测专用 profile 把 BCrypt cost 从 10 降到 8；生产保持 10", "降低登录单次 CPU"],
    ["P1", "多实例 + Nginx，Session 放 Redis", "登录吞吐水平扩展"],
    ["P1", "补 MySQL 写场景：50 线程、库存 20、持续 5 分钟", "验证行锁、连接池与超卖"],
    ["P2", "数据扩到 200+ 账号、20+ 线路、1 万+ 座位后复跑", "验证小数据集结论"],
    ["P3", "EXPLAIN 复核 trains / train_seats 索引", "数据量增长后保持查询稳定"],
], widths=[1.6, 9.0, 5.6], font_size=8.5)
p("连接池对照已于 2026-10-28 执行（第 7.8 节）：pool 10→30 只提升约 6%，连接池不是主限制器。"
  "本轮只确认没有 >10s 的 SQL；每请求 3 次查询仍是可优化点，但不是当前平台期的主因。"
  "下一步优先采客户端 CPU 或换第二台压测机。")
p("负压（限流/降级）方案：CPU > 80% 或 P95 > 1s 时关闭管理后台统计等非核心功能，优先保障查询/下单；"
  "登录失败率/超时率超阈值时熔断；请求队列设上限；超过单实例容量先扩容再放开并发。")
p("复压验收标准（优化后按同样口径复测：10/20/50/100/200，每档 5 分钟；混合 50+10，60 秒；"
  "登录 50 持续 5 分钟）：")
table(["场景", "TPS（口径）", "P95", "错误率", "CPU"], [
    ["查询", "≥ 1500（请求/秒）", "≤ 100 ms", "< 0.1%", "< 80%"],
    ["混合", "≥ 500（主请求/秒）", "≤ 200 ms", "< 0.1%", "< 80%"],
    ["登录+查询", "≥ 200（事务/秒）", "≤ 1000 ms", "< 0.1%", "< 80%"],
], widths=[3.4, 4.0, 3.0, 2.8, 2.8])
p("三项全部达标才算复压通过；未通过则回到瓶颈分析，继续定位。")
p("连接池对照实验（2026-10-28 已执行）：对照组 pool=10，实验组 pool=30；同一份数据、同一台机器、"
  "thymeleaf.cache=false，50/100 线程各 5 分钟。结果：50 线程稳态 1471.6→1573.4（+6.9%），"
  "100 线程 1503.8→1590.7（+5.8%）；应用 CPU 34.4%→35.2%，MySQL 20.0%→21.2%。"
  "结论：连接池不是平台期主限制器；下一步应采 JMeter PID/整机 CPU，或换第二台压测机/分布式压测。")

# ---------------- 11 ----------------
h("11. 附件")
table(["文件", "内容"], [
    ["perf/scenario-query.jmx", "查询场景（登录一次 + 循环查询，阶梯加压）"],
    ["perf/scenario-mixed.jmx", "查询 + 下单两个独立线程组"],
    ["perf/load-test.jmx", "登录+查询对比场景（单账号、单线路）"],
    ["perf/booking-concurrency.jmx", "并发下单（同一座位 9001）"],
    ["perf/data/*.csv", "参数化数据（用户/线路/座位）"],
    ["perf/step-load.bat", "10/20/50/100/200 × 5 分钟"],
    ["perf/keep_awake.ps1", "防止压测期间系统睡眠"],
    ["perf/monitor_resources.ps1", "CPU/内存/磁盘 IO 采样（名义 2s，实际约 4.6s）"],
    ["perf/analyze_resources.py / analyze_timeseries.py / analyze_all.py", "资源/时间序列/汇总分析"],
    ["perf/results/step-load-summary.csv / .md", "阶梯指标汇总"],
    ["perf/results/step-*.jtl / html-step-*", "阶梯原始数据与 JMeter HTML 报告"],
    ["perf/results/resources-step5min.csv / resource-summary.md", "资源采样"],
    ["perf/results/perf100.jfr / samples.txt / jfr-hotspots.txt", "JFR 热点"],
    ["perf/results/db-status-before.txt / after.txt", "MySQL 慢查询/连接/锁状态（阈值 10s）"],
    ["perf/results/pool-ab.md", "连接池 A/B 汇总（2026-10-28，pool 10/30 × 50/100）"],
    ["perf/results/pool10-*.jtl / pool30-*.jtl / *-resources.csv", "A/B 原始 JTL 与资源采样"],
    ["perf/analyze_pool_ab.py", "连接池 A/B 汇总脚本"],
    ["docs/figs/*.png", "TPS/P95/错误率/CPU/内存曲线和 JMeter 报告截图"],
    ["functional_tests/", "25 条 Selenium 功能用例（全部通过）"],
    ["docs/evidence/", "关键证据副本：阶梯汇总、资源摘要、DB 状态、JFR 热点、连接池 A/B、综合分析"],
    ["docs/profiler/", "IDEA Profiler 可选截图目录（本轮未采集）"],
], widths=[9.5, 6.7], font_size=8.5)
p("附件怎么用：每条结论都能顺着“结论 → 表格 → 中间产物 → 原始数据”倒查到文件，这是本报告可复核的基础。"
  "例如“查询约 1485 TPS”来自第 7.1 节表格 ← step-load-summary.csv ← step-10..200.jtl；"
  "“BCrypt 占 89.4%”来自第 8 节 ← perf100.jfr 的 samples.txt / jfr-hotspots.txt；"
  "“连接池不是限制器”来自第 7.8 节 ← pool10/pool30 四个 JTL；"
  "“25 条功能用例通过”来自functional_tests/report.html（pytest-html 自动生成，重跑即覆盖）。")
p("图表数据来源：")
bullet("step-load-tps.png / step-load-p95.png ← perf/results/step-load-summary.csv ← step-10..200.jtl（JMeter 5 分钟档）")
bullet("step-100-tps.png / step-100-error.png ← perf/results/step-100.jtl（100 线程 5 分钟）")
bullet("resource-cpu.png / resource-mem.png ← perf/results/resources-step5min.csv（PowerShell 采样）")
bullet("jmeter-html-step-100-fullhd.png ← perf/results/html-step-100/index.html（JMeter 原生报告截图）")

doc.save(OUT)
print("saved", OUT, "inline shapes:", len(doc.inline_shapes))
