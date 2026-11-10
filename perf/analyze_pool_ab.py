# -*- coding: utf-8 -*-
"""连接池 A/B 分析：pool10 vs pool30，50/100 线程。

- TPS/延迟只统计 POST /trains/search（与报告阶梯口径一致）。
- full = 0~300s；steady = 60~300s（排除重启后的 JIT 预热段）。
"""
import csv
import math
import statistics
from pathlib import Path

RES = Path(__file__).resolve().parent / "results"
TAGS = ["pool10-50", "pool10-100", "pool30-50", "pool30-100"]


def pct(values, p):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return round(s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def metrics(tag, skip_first_s=0):
    path = RES / f"{tag}.jtl"
    if not path.exists():
        return None
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8", errors="replace"))
            if r["label"] == "03 POST /trains/search"]
    if not rows:
        return None
    t0 = min(int(r["timeStamp"]) for r in rows)
    rows = [r for r in rows if (int(r["timeStamp"]) - t0) / 1000 >= skip_first_s]
    if not rows:
        return None
    e = [int(r["elapsed"]) for r in rows]
    start = min(int(r["timeStamp"]) for r in rows)
    end = max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
    span = (end - start) / 1000
    errors = sum(1 for r in rows if r["success"] == "false")
    return {
        "n": len(rows), "span": round(span, 1), "tps": round(len(rows) / span, 1),
        "avg": round(statistics.mean(e), 1), "p95": pct(e, 95), "p99": pct(e, 99),
        "max": max(e), "errpct": round(errors / len(rows) * 100, 2),
    }


def resources(tag):
    path = RES / f"{tag}-resources.csv"
    if not path.exists():
        return None
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    if not rows:
        return None
    app = [float(r["app_cpu_pct"]) for r in rows]
    db = [float(r["mysql_cpu_pct"]) for r in rows]
    mem = [float(r["app_mem_mb"]) for r in rows]
    # 去掉阶段切换的 0 值（应用空闲/采样空档），只看有负载的点
    app_load = [x for x in app if x > 0] or app
    db_load = [x for x in db if x > 0] or db
    return {
        "points": len(rows),
        "app_avg": round(statistics.mean(app_load), 1), "app_max": max(app),
        "db_avg": round(statistics.mean(db_load), 1), "db_max": max(db),
        "mem_growth": round(mem[-1] - mem[0], 1),
    }


lines = ["# 连接池 A/B（pool=10 vs pool=30）", ""]
lines.append("| 场景 | 窗口 | 请求数 | 时长(s) | TPS | 平均(ms) | P95 | P99 | 最大(ms) | 错误率 |")
lines.append("|---|---|---|---|---|---|---|---|---|---|")
for tag in TAGS:
    for label, skip in (("full", 0), ("steady", 60)):
        m = metrics(tag, skip)
        if not m:
            lines.append(f"| {tag} | {label} | 缺数据 | | | | | | | |")
            continue
        lines.append(f"| {tag} | {label} | {m['n']} | {m['span']} | {m['tps']} | {m['avg']} "
                     f"| {m['p95']} | {m['p99']} | {m['max']} | {m['errpct']}% |")

lines += ["", "| 场景 | 采样点 | 应用 CPU 平均/峰值 | MySQL CPU 平均/峰值 | 应用内存增长 |",
          "|---|---|---|---|---|"]
for tag in TAGS:
    r = resources(tag)
    if not r:
        lines.append(f"| {tag} | 缺数据 | | | |")
    else:
        lines.append(f"| {tag} | {r['points']} | {r['app_avg']}% / {r['app_max']}% "
                     f"| {r['db_avg']}% / {r['db_max']}% | {r['mem_growth']} MB |")

lines += ["", "判读规则：", "- pool30 的 steady TPS 明显高于 pool10 → 1485 是连接池上限；",
          "- 两者接近，且 JMeter/整机 CPU 高 → 限制器在客户端；",
          "- 两者接近，且应用 CPU 高 → 限制器在应用 CPU/模板渲染。", ""]

out = RES / "pool-ab.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print("saved", out)
