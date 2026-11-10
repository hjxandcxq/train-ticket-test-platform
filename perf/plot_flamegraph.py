# -*- coding: utf-8 -*-
"""用 JFR ExecutionSample 生成 CPU 火焰图（真实采样，不是示意图）。"""
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "results" / "samples.txt"
OUT = ROOT.parent / "docs" / "figs" / "cpu-flamegraph-jfr.png"
FONT = "C:/Windows/Fonts/msyh.ttc"
W, H = 1500, 820
MARGIN = 40
TOP = 80


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def short(frame):
    frame = frame.replace("/", ".")
    if len(frame) > 58:
        frame = frame[:55] + "..."
    return frame


def color_of(frame):
    f = frame.lower()
    if "bcrypt" in f:
        return "#C0392B"
    if any(x in f for x in ("thymeleaf", "attoparser", "unbescape")):
        return "#2E86C1"
    if any(x in f for x in ("tomcat", "catalina", "coyote")):
        return "#27AE60"
    if any(x in f for x in ("springframework", "aop", "transaction")):
        return "#B7950B"
    if any(x in f for x in ("java.", "jdk.", "sun.")):
        return "#95A5A6"
    if "trainticket" in f:
        return "#8E44AD"
    return "#7F8C8D"


frames = []
text = SAMPLES.read_text(encoding="utf-8", errors="replace")
for block in text.split("jdk.ExecutionSample {")[1:]:
    stack = re.findall(r"^\s{4}([^\s].*?)\(.*$", block, re.M)
    stack = [s.strip() for s in stack if s.strip() and s.strip() != "..."]
    if stack:
        frames.append(list(reversed(stack)))       # 根在底部，栈顶在上

root = {"name": "all", "count": 0, "children": defaultdict(dict), "depth": 0}
for stack in frames:
    node = root
    node["count"] += 1
    for frame in stack:
        child = node["children"].get(frame)
        if child is None:
            child = {"name": frame, "count": 0, "children": defaultdict(dict)}
            node["children"][frame] = child
        child["count"] += 1
        node = child

# 计算总宽度和最大深度
max_depth = 0


def normalize(node, depth=0):
    global max_depth
    node["depth"] = depth
    max_depth = max(max_depth, depth)
    for c in node["children"].values():
        normalize(c, depth + 1)


normalize(root)
row_h = 34
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
f_title, f_sub, f_label, f_small = font(26), font(15), font(12), font(11)

d.text((W / 2, 22), "CPU 火焰图（JFR ExecutionSample）", font=f_title, fill="#1F2D3D", anchor="ma")
d.text((W / 2, 54), f"100 线程登录场景 · {len(frames)} 个样本 · BCrypt.encipher 占 89.4%",
       font=f_sub, fill="#5A6778", anchor="ma")

plot_w = W - 2 * MARGIN


def draw_node(node, x0, x1, width_total):
    depth = node["depth"]
    y1 = H - MARGIN - depth * row_h
    y0 = y1 - row_h + 2
    if y0 < TOP:
        return
    if node["name"] != "all":
        d.rectangle([x0, y0, x1, y1], fill=color_of(node["name"]), outline="white", width=1)
        if (x1 - x0) > 90:
            label = short(node["name"])
            if "BCrypt.encipher" in node["name"]:
                label = f"BCrypt.encipher  {node['count']} 样本 ({node['count'] / len(frames) * 100:.1f}%)"
            d.text((x0 + 4, y0 + 9), label, font=f_small, fill="white")
    # 子节点按样本数比例分配宽度
    if not node["children"]:
        return
    children = sorted(node["children"].values(), key=lambda n: n["count"], reverse=True)
    total = sum(c["count"] for c in children)
    cx = x0
    for c in children:
        cw = (x1 - x0) * c["count"] / total
        draw_node(c, cx, cx + cw, width_total)
        cx += cw


draw_node(root, MARGIN, W - MARGIN, plot_w)

# 图例
legend = [("BCrypt", "#C0392B"), ("Thymeleaf", "#2E86C1"), ("Tomcat", "#27AE60"),
          ("Spring", "#B7950B"), ("JDK", "#95A5A6")]
lx, ly = MARGIN, H - 26
for name, color in legend:
    d.rectangle([lx, ly, lx + 14, ly + 14], fill=color, outline="white")
    d.text((lx + 20, ly - 1), name, font=f_label, fill="#5A6778")
    lx += 120

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print("saved", OUT, "samples", len(frames), "max_depth", max_depth)
