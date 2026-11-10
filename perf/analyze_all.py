# -*- coding: utf-8 -*-
"""汇总阶梯、混合、登录对比、资源采样，输出 results/analysis.md（供写报告引用）。"""
import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def pct(values, p):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def metrics(rows):
    if not rows:
        return None
    e = [int(r["elapsed"]) for r in rows]
    ts = [int(r["timeStamp"]) for r in rows]
    start, end = min(ts), max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
    errors = sum(1 for r in rows if r["success"] == "false")
    return {
        "n": len(rows),
        "err": errors,
        "errpct": round(errors / len(rows) * 100, 2),
        "tps": round(len(rows) / ((end - start) / 1000), 1),
        "avg": round(statistics.mean(e), 1),
        "p90": pct(e, 90),
        "p95": pct(e, 95),
        "p99": pct(e, 99),
        "max": max(e),
    }


def read_jtl(name):
    path = RESULTS / name
    if not path.exists():
        return []
    return [r for r in csv.DictReader(open(path, encoding="utf-8"))
            if not r["label"].endswith("-0") and not r["label"].endswith("-1")]


def table(m):
    if not m:
        return "（无数据）"
    return (f"| {m['n']} | {m['tps']} | {m['avg']} | {m['p90']} | {m['p95']} "
            f"| {m['p99']} | {m['max']} | {m['errpct']}% |")


def main():
    lines = []
    add = lines.append

    add("# 压测数据汇总（自动生成）\n")
    add("> TPS 为 JMeter 主请求/秒，不含重定向子样本（`-0` / `-1`）。"
        "登录+查询场景 1 次迭代 = 3 个主请求，**事务/秒 = TPS ÷ 3**；"
        "不要把登录场景的 147 与查询场景的 1485 直接对比。\n")

    add("## 1. 阶梯加压（查询）\n")
    add("| 线程数 | 请求数 | TPS | 平均 | P90 | P95 | P99 | 最大 | 错误率 |")
    add("|---|---|---|---|---|---|---|---|---|")
    step_csv = RESULTS / "step-load-summary.csv"
    if step_csv.exists():
        for r in csv.DictReader(open(step_csv, encoding="utf-8")):
            add(f"| {r['threads']} | {r['requests']} | {r['tps']} | {r['avg']} "
                f"| {r['p90']} | {r['p95']} | {r['p99']} | {r['max']} | {r['errpct']}% |")

    add("\n## 2. 混合场景（查询 + 下单）\n")
    mixed = read_jtl("mixed.jtl")
    add("| 范围 | 请求数 | TPS | 平均 | P90 | P95 | P99 | 最大 | 错误率 |")
    add("|---|---|---|---|---|---|---|---|---|")
    add("| 全部 " + table(metrics(mixed)))
    by = {}
    for r in mixed:
        by.setdefault(r["label"], []).append(r)
    for label, rows in sorted(by.items()):
        add(f"| {label} " + table(metrics(rows)))

    add("\n## 3. 登录+查询（持续 50 线程）\n")
    add("| 范围 | 请求数 | TPS | 平均 | P90 | P95 | P99 | 最大 | 错误率 |")
    add("|---|---|---|---|---|---|---|---|---|")
    add("| 全部 " + table(metrics(read_jtl("sustain50.jtl"))))
    sustain = metrics(read_jtl("sustain50.jtl"))
    if sustain:
        add("")
        add(f"> 1 次迭代 = GET /login + POST /login + search 共 3 个主请求；"
            f"事务/秒 = {sustain['tps']} ÷ 3 = {round(sustain['tps'] / 3, 1)}。"
            "这是与“>200 TPS”目标同口径的数字。")

    add("\n## 4. 资源采样\n")
    res_md = RESULTS / "resource-summary.md"
    if res_md.exists():
        add(res_md.read_text(encoding="utf-8").strip())
    else:
        add("（resource-summary.md 未生成，先运行 analyze_resources.py）")

    add("\n## 5. 并发下单（book2）\n")
    add("| 范围 | 请求数 | TPS | 平均 | P90 | P95 | P99 | 最大 | 错误率 |")
    add("|---|---|---|---|---|---|---|---|---|")
    add("| 全部 " + table(metrics(read_jtl("book2.jtl"))))

    out = RESULTS / "analysis.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
