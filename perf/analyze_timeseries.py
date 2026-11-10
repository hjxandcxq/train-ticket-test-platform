# -*- coding: utf-8 -*-
"""把 JTL 聚合成 10 秒粒度的 TPS / 错误率时间序列，并画曲线。"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FIG_DIR = ROOT.parent / "docs" / "figs"
FONT = "C:/Windows/Fonts/msyh.ttc"
W, H = 1100, 480
LEFT, TOP, RIGHT, BOTTOM = 90, 60, 50, 70


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def draw(xs, ys, title, ylabel, target, target_label, out_path, color):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title, f_axis, f_val = font(22), font(15), font(13)
    ymax = max(max(ys) * 1.2, target * 1.2 if target else 1)
    if ymax <= 0:
        ymax = 1
    # 错误率量级只有 0.1%，用 0 位小数会把所有刻度都显示成 0
    y_decimals = 2 if ymax < 10 else 0
    plot_w, plot_h = W - LEFT - RIGHT, H - TOP - BOTTOM

    def x_of(i):
        return LEFT + (i / max(len(xs) - 1, 1)) * plot_w

    def y_of(v):
        return TOP + plot_h - (v / ymax) * plot_h

    for i in range(6):
        v = ymax * i / 5
        y = y_of(v)
        d.line([(LEFT, y), (W - RIGHT, y)], fill="#E8EDF3", width=1)
        d.text((LEFT - 10, y - 8), f"{v:.{y_decimals}f}", font=f_axis, fill="#5A6778", anchor="ra")
    d.line([(LEFT, TOP), (LEFT, H - BOTTOM)], fill="#8A96A8", width=2)
    d.line([(LEFT, H - BOTTOM), (W - RIGHT, H - BOTTOM)], fill="#8A96A8", width=2)

    if target:
        yt = y_of(target)
        for x in range(LEFT, W - RIGHT, 12):
            d.line([(x, yt), (x + 6, yt)], fill="#C0392B", width=2)
        d.text((W - RIGHT, yt - 18), target_label, font=f_axis, fill="#C0392B", anchor="ra")

    pts = [(x_of(i), y_of(v)) for i, v in enumerate(ys)]
    if len(pts) > 1:
        d.line(pts, fill=color, width=3)
    for i, (x, y) in enumerate(pts):
        if i % max(len(pts) // 12, 1) == 0:
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=color)
            d.text((x, H - BOTTOM + 10), xs[i], font=f_val, fill="#5A6778", anchor="ma")

    d.text((W / 2, 22), title, font=f_title, fill="#1F2D3D", anchor="ma")
    d.text((W / 2, H - 34), "时间（秒）", font=f_axis, fill="#5A6778", anchor="ma")
    d.text((LEFT - 60, TOP - 30), ylabel, font=f_axis, fill="#5A6778")
    img.save(out_path)
    print("saved", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jtl", required=True)
    ap.add_argument("--prefix", default="timeseries")
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(args.jtl, encoding="utf-8"))
            if not r["label"].endswith("-0") and not r["label"].endswith("-1")]
    if not rows:
        raise SystemExit("JTL 为空")
    start = min(int(r["timeStamp"]) for r in rows)
    buckets = defaultdict(lambda: [0, 0])
    for r in rows:
        sec = (int(r["timeStamp"]) - start) // 1000
        b = sec // 10
        buckets[b][0] += 1
        if r["success"] == "false":
            buckets[b][1] += 1

    xs, tps, errs = [], [], []
    for b in sorted(buckets):
        total, errors = buckets[b]
        xs.append(str(b * 10))
        tps.append(round(total / 10, 1))
        errs.append(round(errors / total * 100, 2))

    out_csv = ROOT / "results" / f"{args.prefix}-timeseries.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(["bucket_sec", "tps", "error_pct"])
        for x, t, e in zip(xs, tps, errs):
            w.writerow([x, t, e])
    print("saved", out_csv)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    draw(xs, tps, f"{args.prefix} · TPS 时间曲线", "TPS", 200, "目标 200",
         FIG_DIR / f"{args.prefix}-tps.png", "#1A4D8F")
    draw(xs, errs, f"{args.prefix} · 错误率时间曲线", "错误率 %", 0.1, "目标 0.1%",
         FIG_DIR / f"{args.prefix}-error.png", "#C0392B")


if __name__ == "__main__":
    main()
