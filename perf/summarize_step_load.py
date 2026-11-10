# -*- coding: utf-8 -*-
"""汇总阶梯加压 JTL：每个线程数一行，输出 CSV/Markdown。"""
import csv
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
LABEL = "03 POST /trains/search"
STAGES = [10, 20, 50, 100, 200]


def pct(values, p):
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)


def metrics(path):
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8"))
            if r["label"] == LABEL]
    elapsed = [int(r["elapsed"]) for r in rows]
    ts = [int(r["timeStamp"]) for r in rows]
    start, end = min(ts), max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
    errors = sum(1 for r in rows if r["success"] == "false")
    return {
        "requests": len(rows),
        "tps": round(len(rows) / ((end - start) / 1000), 1),
        "avg": round(statistics.mean(elapsed), 1),
        "p90": pct(elapsed, 90),
        "p95": pct(elapsed, 95),
        "p99": pct(elapsed, 99),
        "max": max(elapsed),
        "errors": errors,
        "errpct": round(errors / len(rows) * 100, 2),
    }


def main():
    out = []
    for n in STAGES:
        path = RESULTS / f"step-{n}.jtl"
        if not path.exists():
            print(f"skip {path}（不存在）")
            continue
        row = {"threads": n, **metrics(path)}
        out.append(row)
        print(row)
    if not out:
        return

    csv_path = RESULTS / "step-load-summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)

    lines = ["| 线程数 | 查询请求数 | TPS | 平均(ms) | P90 | P95 | P99 | 最大(ms) | 错误率 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in out:
        lines.append(f"| {r['threads']} | {r['requests']} | {r['tps']} | {r['avg']} "
                     f"| {r['p90']} | {r['p95']} | {r['p99']} | {r['max']} | {r['errpct']}% |")
    md_path = RESULTS / "step-load-summary.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saved {csv_path} / {md_path}")


if __name__ == "__main__":
    main()
