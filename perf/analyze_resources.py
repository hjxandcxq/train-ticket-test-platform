# -*- coding: utf-8 -*-
"""读取资源采样 CSV，生成 CPU/内存曲线和摘要。

CPU 曲线说明：压测分五档执行，档与档之间 JMeter 停止、采样器偶有 7~15 秒空档，
这段区间的 CPU 会回落到 0。旧版图把这些点直接连成"瞬间掉零"的尖谷，看起来像
采样错误或应用挂了。现在按"间隙"处理：灰底标出、曲线在间隙处断开、并在图注里
说明，避免误读。
"""
import csv
import io
import statistics
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "results" / "resources-step5min.csv"
FIG_DIR = ROOT.parent / "docs" / "figs"
FONT = "C:/Windows/Fonts/msyh.ttc"
W, H = 1200, 560
LEFT, TOP, RIGHT, BOTTOM = 95, 65, 50, 115

GAP_SECONDS = 12  # 相邻采样间隔超过该值，视为采样空档
IDLE_ZERO = 0.0   # CPU 采样为 0，视为压测间隙内的空闲，不参与连线


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def load():
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8-sig")))
    t0 = datetime.strptime(rows[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
    out = []
    for r in rows:
        t = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
        out.append({
            "sec": (t - t0).total_seconds(),
            "app_cpu": float(r["app_cpu_pct"]),
            "app_mem": float(r["app_mem_mb"]),
            "db_cpu": float(r["mysql_cpu_pct"]),
            "db_mem": float(r["mysql_mem_mb"]),
            "disk": float(r.get("disk_pct") or 0),
        })
    return out


def find_windows(rows, key):
    """返回需要断开的区间：采样空档 + 该指标为 0 的连续空闲段。"""
    wins = []
    for prev, cur in zip(rows, rows[1:]):
        if cur["sec"] - prev["sec"] > GAP_SECONDS:
            wins.append((prev["sec"], cur["sec"]))
    start = None
    for r in rows:
        if r[key] <= IDLE_ZERO:
            start = r["sec"] if start is None else start
        elif start is not None:
            wins.append((start, r["sec"]))
            start = None
    if start is not None:
        wins.append((start, rows[-1]["sec"]))
    return wins


def inside(sec, wins):
    return any(a - 0.001 <= sec <= b + 0.001 for a, b in wins)


def draw(rows, keys, labels, title, ylabel, target, out_name, colors,
         break_at_idle=False, footnote=None):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title, f_axis, f_val = font(22), font(15), font(13)
    xs = [r["sec"] for r in rows]
    ymax = max(max(r[k] for r in rows) for k in keys)
    ymax = max(ymax * 1.2, (target or 0) * 1.2, 1)
    plot_w, plot_h = W - LEFT - RIGHT, H - TOP - BOTTOM

    def x_of(sec):
        return LEFT + sec / max(xs[-1], 1) * plot_w

    def y_of(v):
        return TOP + plot_h - (v / ymax) * plot_h

    wins = find_windows(rows, keys[0]) if break_at_idle else []

    # 先铺间隙底纹，再画网格，避免网格被盖住
    for a, b in wins:
        d.rectangle([(x_of(a), TOP), (x_of(b), H - BOTTOM)], fill="#F1F3F6")

    for i in range(6):
        v = ymax * i / 5
        y = y_of(v)
        d.line([(LEFT, y), (W - RIGHT, y)], fill="#E8EDF3", width=1)
        d.text((LEFT - 10, y - 8), f"{v:.0f}", font=f_axis, fill="#5A6778", anchor="ra")
    d.line([(LEFT, TOP), (LEFT, H - BOTTOM)], fill="#8A96A8", width=2)
    d.line([(LEFT, H - BOTTOM), (W - RIGHT, H - BOTTOM)], fill="#8A96A8", width=2)

    # 阶段分隔线：每 5 分钟
    for i, name in enumerate(["10 线程", "20 线程", "50 线程", "100 线程", "200 线程"]):
        x = x_of(i * 300)
        d.line([(x, TOP), (x, H - BOTTOM)], fill="#D5DEE9", width=1)
        d.text((x + 6, TOP + 4), name, font=f_val, fill="#8A96A8")

    if target:
        yt = y_of(target)
        for x in range(LEFT, W - RIGHT, 12):
            d.line([(x, yt), (x + 6, yt)], fill="#C0392B", width=2)
        d.text((LEFT + 8, yt - 18), f"目标 {target}%", font=f_axis, fill="#C0392B", anchor="la")

    # 折线：遇到间隙就断开，不连成"掉零"尖谷
    for k, color in zip(keys, colors):
        seg = []
        for r in rows:
            if inside(r["sec"], wins):
                if len(seg) > 1:
                    d.line(seg, fill=color, width=2)
                seg = []
                continue
            seg.append((x_of(r["sec"]), y_of(r[k])))
        if len(seg) > 1:
            d.line(seg, fill=color, width=2)

    # 间隙标注：宽度够才写"间隙"，避免压住阶段标题
    for a, b in wins:
        if x_of(b) - x_of(a) > 34:
            d.text(((x_of(a) + x_of(b)) / 2, TOP + 24), "间隙", font=f_val,
                   fill="#7C8A9C", anchor="ma")

    # 图例（先铺白底，避免目标虚线从文字中间穿过）
    lx = W - RIGHT - 230
    d.rectangle([(lx - 8, TOP + 52), (W - RIGHT, TOP + 86 + len(labels) * 22)],
                fill="white", outline="#DDE3EB")
    for i, (lab, color) in enumerate(zip(labels, colors)):
        d.line([(lx, TOP + 72 + i * 22), (lx + 26, TOP + 72 + i * 22)], fill=color, width=3)
        d.text((lx + 34, TOP + 62 + i * 22), lab, font=f_axis, fill="#5A6778")
    if wins:
        y = TOP + 72 + len(labels) * 22
        d.rectangle([(lx, y - 6), (lx + 26, y + 6)], fill="#F1F3F6", outline="#C9D2DE")
        d.text((lx + 34, y - 10), "压测间隙（不连线）", font=f_axis, fill="#5A6778")

    d.text((W / 2, 22), title, font=f_title, fill="#1F2D3D", anchor="ma")
    d.text((W / 2, H - 52), "压测时间（秒）", font=f_axis, fill="#5A6778", anchor="ma")
    d.text((LEFT - 65, TOP - 30), ylabel, font=f_axis, fill="#5A6778")
    if footnote:
        for i, line in enumerate(footnote):
            d.text((LEFT, H - 34 + i * 18), line, font=f_val, fill="#8A96A8")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    (FIG_DIR / out_name).write_bytes(buf.getvalue())
    print("saved", FIG_DIR / out_name)


def main():
    rows = load()
    if not rows:
        raise SystemExit("资源采样为空")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    draw(rows, ["app_cpu", "db_cpu"], ["应用 JVM", "MySQL"],
         "阶梯加压 · CPU 使用率", "CPU %（16 核）", 80,
         "resource-cpu.png", ["#1A4D8F", "#2E8B57"], break_at_idle=True,
         footnote=[
             "灰底＝压测间隙（JMeter 停止或采样空档 7~15 秒）：曲线在此断开，",
             "间隙内 CPU 回落为真实空闲，不是采样错误，也不计入有效压测区间",
         ])
    draw(rows, ["app_mem", "db_mem"], ["应用 JVM", "MySQL"],
         "阶梯加压 · 内存使用", "内存 MB", None,
         "resource-mem.png", ["#1A4D8F", "#2E8B57"])

    app_cpu = [r["app_cpu"] for r in rows]
    db_cpu = [r["db_cpu"] for r in rows]
    app_mem = [r["app_mem"] for r in rows]
    disk = [r["disk"] for r in rows]
    app_cpu_busy = [v for v in app_cpu if v > 0]
    db_cpu_busy = [v for v in db_cpu if v > 0]
    lines = [
        f"采样点：{len(rows)}，覆盖 {rows[-1]['sec']:.0f} 秒",
        f"应用 CPU：平均 {statistics.mean(app_cpu):.1f}%，峰值 {max(app_cpu):.1f}%",
        f"应用 CPU（剔除 0 值间隙采样，n={len(app_cpu_busy)}）："
        f"平均 {statistics.mean(app_cpu_busy):.1f}%",
        f"MySQL CPU：平均 {statistics.mean(db_cpu):.1f}%，峰值 {max(db_cpu):.1f}%",
        f"MySQL CPU（剔除 0 值间隙采样，n={len(db_cpu_busy)}）："
        f"平均 {statistics.mean(db_cpu_busy):.1f}%",
        f"应用内存：{min(app_mem):.0f} ~ {max(app_mem):.0f} MB，"
        f"结束较开始增长 {app_mem[-1] - app_mem[0]:.0f} MB",
        f"磁盘 IO（_Total PercentDiskTime）：平均 {statistics.mean(disk):.1f}%，峰值 {max(disk):.1f}%",
    ]
    out = ROOT / "results" / "resource-summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
