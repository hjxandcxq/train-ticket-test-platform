# -*- coding: utf-8 -*-
"""根据 step-load-summary.csv 生成 TPS / P95 阶梯曲线（Pillow，无额外依赖）。"""
import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "results" / "step-load-summary.csv"
OUT_DIR = ROOT.parent / "docs" / "figs"
FONT = "C:/Windows/Fonts/msyh.ttc"

W, H = 1000, 560
LEFT, TOP, RIGHT, BOTTOM = 90, 70, 50, 80


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def x_of(n, max_n):
    lo, hi = math.log10(10), math.log10(max_n)
    return LEFT + (math.log10(n) - lo) / (hi - lo) * (W - LEFT - RIGHT)


def draw_chart(rows, key, title, y_max, target, target_label, out_name, color):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title, f_axis, f_val = font(24), font(16), font(14)
    max_n = max(r["threads"] for r in rows)
    plot_w = W - LEFT - RIGHT
    plot_h = H - TOP - BOTTOM

    # 自动缩放：不能低于数据最大值和目标线，否则数据会画到画布外
    if y_max is None:
        data_max = max(float(r[key]) for r in rows)
        y_max = math.ceil(max(data_max * 1.2, target * 1.2, 100) / 100) * 100

    def y_of(v):
        return TOP + plot_h - (v / y_max) * plot_h

    # 网格 + Y 轴刻度
    for i in range(6):
        v = y_max * i / 5
        y = y_of(v)
        d.line([(LEFT, y), (W - RIGHT, y)], fill="#E8EDF3", width=1)
        d.text((LEFT - 12, y - 8), f"{v:.0f}", font=f_axis, fill="#5A6778", anchor="ra")

    # 坐标轴
    d.line([(LEFT, TOP), (LEFT, H - BOTTOM)], fill="#8A96A8", width=2)
    d.line([(LEFT, H - BOTTOM), (W - RIGHT, H - BOTTOM)], fill="#8A96A8", width=2)

    # 目标线
    yt = y_of(target)
    for x in range(LEFT, W - RIGHT, 12):
        d.line([(x, yt), (x + 6, yt)], fill="#C0392B", width=2)
    d.text((W - RIGHT, yt - 20), target_label, font=f_axis, fill="#C0392B", anchor="ra")

    # X 轴刻度
    for r in rows:
        x = x_of(r["threads"], max_n)
        d.line([(x, H - BOTTOM), (x, H - BOTTOM + 6)], fill="#8A96A8", width=2)
        d.text((x, H - BOTTOM + 12), str(r["threads"]), font=f_axis, fill="#5A6778", anchor="ma")

    # 折线 + 点 + 数值
    pts = [(x_of(r["threads"], max_n), y_of(float(r[key]))) for r in rows]
    d.line(pts, fill=color, width=3)
    for (x, y), r in zip(pts, rows):
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=color)
        d.text((x, y - 22), f"{float(r[key]):.0f}", font=f_val, fill=color, anchor="ma")

    d.text((W / 2, 24), title, font=f_title, fill="#1F2D3D", anchor="ma")
    d.text((W / 2, H - 38), "并发线程数", font=f_axis, fill="#5A6778", anchor="ma")
    img.save(OUT_DIR / out_name)
    print("saved", OUT_DIR / out_name)


def main():
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8")))
    rows = [{"threads": int(r["threads"]), "tps": r["tps"], "p95": r["p95"]} for r in rows]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    draw_chart(rows, "tps", "阶梯加压 · TPS 曲线", None, 200, "目标 200", "step-load-tps.png", "#1A4D8F")
    draw_chart(rows, "p95", "阶梯加压 · P95 响应时间", None, 1000, "目标 1000ms", "step-load-p95.png", "#B26A00")


if __name__ == "__main__":
    main()
