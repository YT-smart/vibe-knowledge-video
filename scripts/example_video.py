"""《指数的形状》—— 知识大赏示例工程（135 秒，20 个镜头）

这是一个完整可运行的项目，演示了本风格的常用镜头：
  一张纸对折（物件特写）· 侧视纸堆 + 参照物 · 提问 + 选项卡 · 对数刻度一路拉远到月球（尺度旅行）
  · 片头标题卡 · 棋盘逐格翻倍 + 数据面板 · 方格阵列计数 · 双柱对比破框 · 讲台引语打字机
  · 细菌瓶 + 时钟 + 红色警示 · 指数→S 曲线变形 · 火柴人站在曲线上 · 双曲线对比 · 金句卡 · 片尾标题卡

新项目：复制本文件为 video.py，保留需要的镜头函数作参考，改 SCENES / SUBS / LABELS / sound()。
命令见 vkit.py 顶部说明，例如：
    python video.py preview check.jpg 3 12 25
    python video.py sample 0 31
    python video.py all
"""
import os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vkit
from vkit import *          # 绘图函数、色板、工具

DUR = 135.5
MUSIC = "bgm.m4a"            # 固定背景音乐（技能 assets/bgm.m4a 复制到项目目录）；用户要换时改这里或用 --music
PAPER_B = (196, 184, 160)

def fmt(mm):
    if mm < 10: return f"{mm:.1f} mm"
    if mm < 1000: return f"{mm / 10:.1f} cm"
    m = mm / 1000
    if m < 100: return f"{m:.1f} m"
    if m < 10000: return f"{m:,.0f} m"
    return f"{m / 1000:,.0f} km"

# ---------- 时间线 ----------
SUBS = [
    (0.6, 4.0, "一张纸，厚【0.1 毫米】。"),
    (5.0, 9.0, "对折 10 次，大约【一本书】那么厚。"),
    (14.0, 17.0, "先猜一猜。"),
    (18.0, 23.6, "每对折一次，厚度就【翻一倍】。"),
    (24.9, 27.0, "答案是：它会【碰到月亮】。"),
    (31.9, 39.8, "第一格 1 粒米，第二格 2 粒，每一格都【翻倍】。"),
    (41.0, 46.8, "整张棋盘需要的大米，是全人类【近 900 年】的产量。"),
    (47.6, 54.8, "前半个棋盘，平平无奇；【后半个棋盘】，天翻地覆。"),
    (60.2, 63.8, "这场讲座，他一生讲了【1742 次】。"),
    (64.8, 71.6, "一个瓶子，细菌每分钟翻倍，【12:00】正好装满。"),
    (72.2, 77.9, "11:55，瓶子才满了 3%。细菌们觉得：【空间还多的是】。"),
    (78.6, 83.9, "一切，都发生在【最后 5 分钟】。"),
    (84.8, 91.8, "就算再找到 3 个新瓶子——也只能【多撑 2 分钟】。"),
    (92.6, 99.8, "现实里，没有永远的指数。每条曲线，【终会撞墙】。"),
    (100.6, 107.8, "可对一个人来说，撞墙之前的那一段——【足够长】。"),
    (108.6, 117.8, "每天进步 1%，一年后是【37.8】；每天退步 1%，只剩 0.03。"),
    (118.6, 125.8, "大多数人放弃的时候，才对折到【第 3 次】。"),
]
FOLD_T = [4.9 + k * 0.42 for k in range(9)]      # 第 2~10 次对折
T5A, T5B = 17.6, 24.8
PPD = 170          # 每个数量级的像素
TIP_Y = 360
MOON_H = 3.844e8

def n5(t):
    u = clamp((t - T5A) / (T5B - T5A))
    return 10 + 32 * (0.5 - 0.5 * math.cos(math.pi * u))
def logh(n): return -4 + n * math.log10(2)

T_HIT = next(T5A + i / 1000 for i in range(int((T5B - T5A) * 1000) + 1)
             if logh(n5(T5A + i / 1000)) >= math.log10(MOON_H))

LANDMARKS = [(1.7, '一个人', '1.7 m'), (100, '30 层的楼', '100 m'), (632, '上海中心大厦', '632 m'),
             (8848, '珠穆朗玛峰', '8,848 m'), (1e5, '卡门线 · 太空的边界', '100 km'),
             (4e5, '国际空间站', '400 km'), (2.02e7, 'GPS 卫星', '20,200 km')]
DEC_LABEL = {-3: '1 mm', -2: '1 cm', -1: '10 cm', 0: '1 m', 1: '10 m', 2: '100 m', 3: '1 km', 4: '10 km',
             5: '100 km', 6: '1,000 km', 7: '1 万 km', 8: '10 万 km', 9: '100 万 km'}

_rng = np.random.default_rng(7)
STARS = [(float(x), float(y), float(r), float(b)) for x, y, r, b in
         zip(_rng.uniform(0, W, 260), _rng.uniform(0, H, 260), _rng.uniform(0.6, 1.8, 260), _rng.uniform(0.3, 1, 260))]

# ---------- 公共元素 ----------
PAPER_LABEL = ([("0.1 mm", GOLD, 46, 'geo')], "一张纸 · 对折实验", "The Paper Folding Problem", "《纸张对折问题》")
# (t0, t1, 左上大字, 左上小字, 右上英文出处, 右上中文出处)
LABELS = [
    (0.6, 27.0) + PAPER_LABEL,
    (31.3, 54.8, [("约 ", GOLD, 24, 'song'), ("6", GOLD, 46, 'geo'), (" 世纪", GOLD, 24, 'song')],
     "印度 · 国王与智者", "Wheat and Chessboard Problem", "《棋盘麦粒问题》"),
    (55.3, 91.8, [("1969", GOLD, 46, 'geo')], "科罗拉多大学 · 艾伯特·巴特利特",
     "Arithmetic, Population and Energy", "《算术、人口与能源》"),
    (92.3, 99.8, [("1838", GOLD, 46, 'geo')], "比利时 · 韦吕勒", "Logistic Growth", "《逻辑斯蒂增长》"),
    (100.3, 125.8, [("2026", GOLD, 46, 'geo')], "此刻 · 你", None, None),
]

# ---------- 镜头 1：一张纸 ----------
def shot1(cv, t):
    a = ease(t / 0.9)
    cx, cy, w, h = 960, 470, 510, 360
    p = ease((t - 2.0) / 1.2)
    sh = ease((t - 3.3) / 0.7) * w / 4
    xL, xM, yT, yB = cx - w / 2 + sh, cx + sh, cy - h / 2, cy + h / 2
    rect(cv, xL, yT, xM, yB, fill=PAPER, a=a)
    s = math.cos(math.pi * p)
    x2 = xM + s * w / 2
    lift = math.sin(math.pi * p) * 0.16 * h          # 透视：翻起的外缘离镜头更近，看起来更高
    flap = [(xM * SS, yT * SS), (x2 * SS, (yT - lift) * SS), (x2 * SS, (yB + lift) * SS), (xM * SS, yB * SS)]
    if s >= 0:
        cv.d.polygon(flap, fill=mix(sc(PAPER, 0.8 + 0.2 * s), a, cv.bg))
        line(cv, [(xL, yT), (xM, yT), (x2, yT - lift), (x2, yB + lift), (xM, yB), (xL, yB), (xL, yT)],
             GOLD, 1.2, a, glow=0.8)
    else:
        line(cv, [(xL, yT), (xM, yT), (xM, yB), (xL, yB), (xL, yT)], GOLD, 1.2, a, glow=0.8)
        cv.d.polygon(flap, fill=mix(sc(PAPER_B, 0.74 + 0.22 * -s), a, cv.bg))
        line(cv, [(xM, yT), (x2, yT - lift), (x2, yB + lift), (xM, yB)], GOLD_L, 1.2, a, glow=1.0)
    if p > 0:
        line(cv, [(xM, yT), (xM, yB)], sc(GOLD, 0.7), 1, a * min(1, p * 3))

# ---------- 镜头 2~4：侧视纸堆 + 提问 + 选项 ----------
def fold_L(t): return 1 + sum(ease((t - ft) / 0.18) for ft in FOLD_T)
def fold_n(t): return 1 + sum(1 for ft in FOLD_T if t >= ft + 0.09)

def stack_scene(cv, t):
    k = (1 - 0.8 * ease((t - 9.2) / 0.6)) * (1 - ease((t - 12.9) / 0.6))
    if k <= 0: return
    yG = 760
    line(cv, [(380, yG + 1), (1540, yG + 1)], (74, 66, 54), 1, k * ease((t - 4.4) / 0.5))
    if t < 4.8:   # 俯视 → 侧视的压扁过渡
        q = ease((t - 4.2) / 0.6)
        cx, cy = lerp(960, 820, q), lerp(470, yG - 1, q)
        w, h = lerp(255, 360, q), lerp(360, 2, q)
        rect(cv, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill=PAPER)
        line(cv, [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2),
                  (cx - w / 2, cy + h / 2), (cx - w / 2, cy - h / 2)], GOLD, 1.2, 1, glow=0.8)
    else:
        L = fold_L(t)
        mm = 0.1 * 2 ** L
        px = max(2.0, mm * 3.6)
        x0, x1 = 640, 1000
        rect(cv, x0, yG - px, x1, yG, fill=PAPER, a=k)
        layers = 2 ** round(L)
        step = px / layers if px / layers >= 4 else 5.0   # 层太多时用细纹理表示纸页
        y = yG - step
        while y > yG - px + 1:
            line(cv, [(x0, y), (x1, y)], (186, 175, 154), 0.5, k)
            y -= step
        line(cv, [(x0, yG - px), (x1, yG - px)], GOLD_L, 1.5, k, glow=1.0)
        line(cv, [(x0, yG - px), (x0, yG)], GOLD, 1, k * 0.6)
        line(cv, [(x1, yG - px), (x1, yG)], GOLD, 1, k * 0.6)
        # 一本书
        ab = ease((t - 8.3) / 0.6) * k
        if ab > 0:
            rect(cv, 1090, 400, 1310, 760, fill=(46, 40, 32), outline=sc(GOLD, 0.75), w=1.2, a=ab)
            for y in range(406, 756, 7):
                line(cv, [(1290, y), (1305, y)], (118, 106, 86), 0.6, ab)
            line(cv, [(1120, 450), (1262, 450)], GOLD, 1, ab * 0.6)
            line(cv, [(1120, 458), (1262, 458)], GOLD, 0.6, ab * 0.4)
            rich(cv, [("一本书  ≈ 10 cm", DIM, 20, 'song')], 1200, 384, 'm', ab)
            dashed(cv, 1000, 1090, yG - px, GOLD, ab * 0.5, 6, 6)
        # 计数器
        ac = ease((t - 4.8) / 0.4) * k
        rich(cv, [("对折  ", DIM, 22, 'song'), ("×", GOLD, 40, 'geo', True), (str(fold_n(t)), GOLD, 64, 'geo', True)],
             200, 830, 'l', ac)
        rich(cv, [("厚度  ", DIM, 20, 'song'), (fmt(0.1 * 2 ** fold_n(t)), CREAM, 30, 'geo')], 200, 880, 'l', ac)

def icon(cv, kind, cx, a):
    c = sc(GOLD, 0.85)
    if kind == 0:
        rect(cv, cx - 32, 500, cx + 32, 640, outline=c, w=1.5, a=a)
        for r_ in range(7):
            for c_ in range(3):
                rect(cv, cx - 22 + c_ * 16, 512 + r_ * 17, cx - 14 + c_ * 16, 522 + r_ * 17, fill=sc(GOLD, 0.5), a=a)
    elif kind == 1:
        line(cv, [(cx - 100, 640), (cx - 30, 548), (cx, 585), (cx + 40, 528), (cx + 105, 640)], c, 1.5, a)
    else:
        line(cv, [(cx - 110, 640), (cx - 10, 500), (cx + 110, 640)], c, 1.5, a)
        line(cv, [(cx - 38, 540), (cx - 22, 552), (cx - 8, 538), (cx + 8, 552), (cx + 22, 535)], CREAM_D, 1.2, a)
        line(cv, [(cx - 10, 500), (cx - 10, 466)], c, 1.2, a)
        cv.d.polygon([((cx - 10) * SS, 466 * SS), ((cx + 14) * SS, 473 * SS), ((cx - 10) * SS, 480 * SS)],
                     fill=mix(RED, a, cv.bg))

def question_scene(cv, t):
    aq = ease((t - 9.6) / 0.6) * (1 - ease((t - 16.9) / 0.5))
    m = ease((t - 13.2) / 0.6)
    y, s = lerp(480, 300, m), lerp(1, 0.72, m)
    rich(cv, [("那么，对折 ", CREAM, 60 * s, 'song'), ("42", GOLD, 104 * s, 'geo', True),
              (" 次", GOLD, 64 * s, 'song', True), ("呢？", CREAM, 60 * s, 'song')], 960, y, 'm', aq)
    rich(cv, [("（现实里一张纸很难折过 8 次——这里只算数学）", DIM, 22, 'song')], 960, 570, 'm',
         window(t, 10.6, 13.2, 0.6, 0.4))
    labels = [("A", "一栋楼"), ("B", "一座山"), ("C", "珠穆朗玛峰")]
    for i, (ab_, name) in enumerate(labels):
        a = ease((t - 13.6 - i * 0.3) / 0.5) * (1 - ease((t - 16.9) / 0.5))
        if a <= 0: continue
        cx = 560 + i * 400
        dy = (1 - ease((t - 13.6 - i * 0.3) / 0.5)) * 20
        cv_y = dy
        rect(cv, cx - 150, 450 + cv_y, cx + 150, 730 + cv_y, fill=(20, 18, 14), outline=sc(GOLD, 0.6), w=1, a=a, r=6)
        icon(cv, i, cx, a)
        rich(cv, [(ab_, GOLD, 28, 'geo'), ("   " + name, CREAM, 28, 'song')], cx, 700 + cv_y, 'm', a)

# ---------- 镜头 5：一路到月球 ----------
def shot5(cv, t):
    n = n5(t); lh = logh(n)
    a0 = ease((t - 17.3) / 0.5)
    sp = clamp((lh - 3.6) / 2.0)
    # 星空
    for x, y0, r, b in STARS:
        y = (y0 + lh * PPD * 0.3) % H
        ellipse(cv, x, y, r, fill=CREAM, a=sp * b * a0 * (0.7 + 0.3 * math.sin(t * 2 + x)))
    # 对数刻度
    line(cv, [(1800, 170), (1800, 990)], DIM, 1, a0 * 0.5)
    rich(cv, [("对数刻度 · 每格 ×10", DIM, 14, 'song')], 1800, 160, 'm', a0 * 0.8)
    for d, lab in DEC_LABEL.items():
        y = TIP_Y - (d - lh) * PPD
        if 175 < y < 985:
            line(cv, [(1792, y), (1808, y)], DIM, 1, a0 * 0.7)
            rich(cv, [(lab, DIM, 14, 'geo')], 1786, y + 5, 'r', a0 * 0.8)
    # 地标
    for hm, name, val in LANDMARKS:
        y = TIP_Y - (math.log10(hm) - lh) * PPD
        if -40 < y < H + 40:
            crossed = lh >= math.log10(hm)
            k = 0.5 + 0.5 * math.exp(-(lh - math.log10(hm)) * 2.5) if crossed else 0.55
            dashed(cv, 260, 880, y, GOLD, a0 * k * 0.8)
            dashed(cv, 1040, 1660, y, GOLD, a0 * k * 0.8)
            rich(cv, [(name, CREAM, 24, 'song')], 262, y - 12, 'l', a0 * min(1, k + 0.2))
            rich(cv, [(val, GOLD, 22, 'geo', crossed and k > 0.8)], 1658, y - 12, 'r', a0 * min(1, k + 0.2))
    # 纸柱
    # 纸柱在下方渐隐，给字幕让位
    yb0, yb1 = 820, 950
    rect(cv, 930, TIP_Y, 990, yb0, fill=sc(PAPER, 0.9), a=a0)
    rect(cv, 954, TIP_Y, 966, yb0, fill=CREAM, a=a0)
    line(cv, [(930, TIP_Y), (930, yb0)], GOLD, 1, a0 * 0.7)
    line(cv, [(990, TIP_Y), (990, yb0)], GOLD, 1, a0 * 0.7)
    for i in range(26):
        f = 1 - i / 26
        y = yb0 + (yb1 - yb0) * i / 26
        rect(cv, 930, y, 990, y + (yb1 - yb0) / 26 + 1, fill=sc(PAPER, 0.9), a=a0 * f)
    line(cv, [(926, TIP_Y), (994, TIP_Y)], GOLD_L, 2, a0, glow=1.2)
    gdot(cv, 960, TIP_Y, 40, GOLD, a0 * 0.6)
    # 月球
    ym = TIP_Y - (math.log10(MOON_H) - lh) * PPD
    if ym > -260:
        mc = ym - 110
        dashed(cv, 260, 820, ym, GOLD, a0 * 0.7)
        dashed(cv, 1100, 1660, ym, GOLD, a0 * 0.7)
        rich(cv, [("月球", CREAM, 26, 'song')], 262, ym - 12, 'l', a0)
        rich(cv, [("384,400 km", GOLD, 22, 'geo', True)], 1658, ym - 12, 'r', a0)
        gdot(cv, 960, mc, 150, (120, 100, 60), a0 * 0.6)
        ellipse(cv, 960, mc, 110, fill=(214, 204, 180), a=a0)
        for dx, dy, rr in [(-38, -30, 22), (30, 14, 16), (-10, 40, 12), (44, -42, 10), (-55, 22, 9)]:
            ellipse(cv, 960 + dx, mc + dy, rr, fill=(188, 178, 154), a=a0)
        ellipse(cv, 960, mc, 110, outline=GOLD, w=1.2, a=a0 * 0.8)
    # 撞击闪光
    dt = t - T_HIT
    if 0 <= dt < 1.6:
        f = (1 - dt / 1.6) ** 2
        gdot(cv, 960, TIP_Y, 60 + 260 * dt, GOLD_L, f)
        ellipse(cv, 960, TIP_Y, 40 + 420 * dt, outline=GOLD_L, w=1.5, a=f * 0.8)
    # HUD：计数器
    nd = int(n + 1e-6)
    rect(cv, 110, 770, 430, 905, fill=(14, 13, 12), outline=sc(GOLD, 0.45), w=1, a=a0, r=4)
    rich(cv, [("对折", DIM, 20, 'song')], 135, 830, 'l', a0)
    rich(cv, [("×", GOLD, 30, 'geo', True), (str(nd), GOLD, 50, 'geo', True)], 405, 834, 'r', a0)
    rich(cv, [("厚度", DIM, 20, 'song')], 135, 885, 'l', a0)
    rich(cv, [(fmt(0.1 * 2 ** nd), CREAM, 26, 'geo')], 405, 887, 'r', a0)
    # 结果注释
    ar = ease((t - T_HIT - 0.6) / 0.5)
    if ar > 0:
        rect(cv, 1300, 770, 1700, 905, fill=(14, 13, 12), outline=sc(GOLD, 0.45), w=1, a=ar, r=4)
        rich(cv, [("0.1 mm × 2", CREAM, 26, 'geo'), ("42", CREAM, 16, 'geo', False, -12),
                  ("  ≈ ", CREAM, 26, 'geo'), ("44 万 km", GOLD, 28, 'song', True)], 1325, 828, 'l', ar)
        rich(cv, [("地月距离 ≈ 38.4 万 km", CREAM_D, 22, 'song')], 1325, 870, 'l', ar)
        rich(cv, [("理论值", DIM, 15, 'song')], 1680, 893, 'r', ar)

# ---------- 镜头 6 / 20：标题卡 ----------
def title(cv, t, t0=27.4):
    title_card(cv, t, t0, "指数的形状", "THE SHAPE OF THE EXPONENTIAL", "人类的直觉是线性的，世界是指数的。", expo(4))

# ---------- 镜头 7~9：棋盘麦粒 ----------
CELL_T = [31.8 + 7.0 * (i / 63) ** 0.85 for i in range(64)]
_rc = np.random.default_rng(11)
CELL_DOTS = [_rc.uniform(0.14, 0.86, (128, 2)) for _ in range(64)]
RICE = (232, 216, 178)

def cn_num(x):
    for unit, v in [("亿亿", 1e16), ("万亿", 1e12), ("亿", 1e8), ("万", 1e4)]:
        if x >= v: return f"{x / v:,.1f} {unit}"
    return f"{x:,.0f}"

def weight(g):
    if g < 1000: return f"{g:,.1f} 克" if g < 10 else f"{g:,.0f} 克"
    if g < 1e6: return f"{g / 1000:,.1f} 千克"
    tons = g / 1e6
    if tons < 1e4: return f"{tons:,.0f} 吨"
    if tons < 1e8: return f"{tons / 1e4:,.0f} 万吨"
    return f"{tons / 1e8:,.0f} 亿吨"

def chess_scene(cv, t):
    # 7：棋盘逐格翻倍
    ab = window(t, 31.0, 40.6, 0.6, 0.6)
    if ab > 0:
        cs, bx, by = 72, 512, 212
        rect(cv, bx - 6, by - 6, bx + 8 * cs + 6, by + 8 * cs + 6, outline=sc(GOLD, 0.7), w=1.2, a=ab)
        cur = -1
        for i in range(64):
            r_, c_ = divmod(i, 8)
            x0, y0 = bx + c_ * cs, by + r_ * cs
            base = (26, 23, 18) if (r_ + c_) % 2 == 0 else (36, 31, 25)
            rect(cv, x0, y0, x0 + cs, y0 + cs, fill=base, a=ab)
            ai = ease((t - CELL_T[i]) / 0.15)
            if ai <= 0: continue
            cur = i
            if i < 7:
                for u, v in CELL_DOTS[i][:2 ** i]:
                    ellipse(cv, x0 + u * cs, y0 + v * cs, 2.2, fill=RICE, a=ab * ai)
            else:
                k = min(1.0, 0.35 + (i - 7) * 0.012)
                rect(cv, x0 + 3, y0 + 3, x0 + cs - 3, y0 + cs - 3, fill=sc((200, 168, 104), k), a=ab * ai)
                for u, v in CELL_DOTS[i][:40]:
                    ellipse(cv, x0 + u * cs, y0 + v * cs, 1.4, fill=RICE, a=ab * ai * k)
                if i > 40:
                    gdot(cv, x0 + cs / 2, y0 + cs / 2, 30 + (i - 40), GOLD, ab * ai * 0.25)
        if cur >= 0:
            g = 2 ** cur
            rich(cv, [("第 ", DIM, 24, 'song'), (str(cur + 1), GOLD, 54, 'geo', True), (" 格", DIM, 24, 'song')],
                 1180, 330, 'l', ab)
            rich(cv, [(f"{g:,}", GOLD_L, 34 if g < 1e15 else 28, 'geo', True), ("  粒", DIM, 22, 'song')],
                 1180, 420, 'l', ab)
            rich(cv, [("≈ " + cn_num(g) + " 粒", CREAM_D, 24, 'song')], 1180, 470, 'l', ab if g >= 1e4 else 0)
            rich(cv, [("重量  ", DIM, 20, 'song'), (weight(g * 0.025), CREAM, 28, 'song')], 1180, 540, 'l', ab)
            line(cv, [(1180, 370), (1700, 370)], DIM, 1, ab * 0.4)
    # 8：近 900 年的产量
    ag = window(t, 40.4, 47.2, 0.6, 0.5)
    if ag > 0:
        cols, rows, pit, sz = 40, 23, 26, 20
        x0, y0 = 960 - cols * pit / 2, 300
        n = int(887 * clamp((t - 40.9) / 3.6) ** 2)
        rich(cv, [("每一格 = 全球一年的大米产量（约 5.2 亿吨）", DIM, 22, 'song')], x0, 272, 'l', ag)
        rich(cv, [("≈ ", GOLD, 30, 'song'), (str(n), GOLD, 46, 'geo', True), (" 年", GOLD, 30, 'song', True)],
             x0 + cols * pit, 276, 'r', ag)
        for i in range(cols * rows):
            r_, c_ = divmod(i, cols)
            xx, yy = x0 + c_ * pit, y0 + r_ * pit
            if i < n:
                rect(cv, xx, yy, xx + sz, yy + sz, fill=(178, 142, 80), a=ag)
            elif i < 887:
                rect(cv, xx, yy, xx + sz, yy + sz, outline=(56, 50, 40), w=1, a=ag)
        rich(cv, [("按每粒 25 mg 估算", DIM, 15, 'song')], 60, 1052, 'l', ag)
    # 9：前半 / 后半棋盘
    ah = window(t, 47.0, 55.0, 0.6, 0.6)
    if ah > 0:
        yb = 820
        line(cv, [(400, yb), (1520, yb)], (74, 66, 54), 1, ah)
        line(cv, [(560, yb - 1), (760, yb - 1)], GOLD_L, 2, ah, glow=1.2)
        gdot(cv, 660, yb, 24, GOLD, ah * 0.6)
        rich(cv, [("前 32 格", CREAM, 28, 'song')], 660, 875, 'm', ah)
        rich(cv, [("约 107 吨", GOLD, 26, 'song')], 660, 918, 'm', ah)
        g = ease((t - 49.0) / 2.6)
        g = g ** 2.2
        top = lerp(yb, -60, g)
        if g > 0:
            rect(cv, 1160, top, 1360, yb, fill=(176, 140, 78), a=ah)
            yy = yb - 6
            while yy > top:
                line(cv, [(1166, yy), (1354, yy)], (204, 170, 108), 0.5, ah)
                yy -= 7
            line(cv, [(1160, top), (1360, top)], GOLD_L, 2, ah, glow=1.2)
        rich(cv, [("后 32 格", CREAM, 28, 'song')], 1260, 875, 'm', ah)
        rich(cv, [("约 4,600 亿吨", GOLD, 26, 'song', True)], 1260, 918, 'm', ah * ease((t - 50.5) / 0.6))
        df = t - 51.6
        if 0 <= df < 1.2:
            gdot(cv, 1260, 0, 220 * (0.4 + df), GOLD_L, (1 - df / 1.2) ** 2)
        ar = ease((t - 52.2) / 0.7) * ah
        rich(cv, [("后半个棋盘", CREAM, 30, 'song'), ("  =  ", DIM, 30, 'geo')], 760, 400, 'm', ar)
        rich(cv, [("前半个的 ", CREAM, 30, 'song'), ("43 亿", GOLD, 44, 'song', True), (" 倍", CREAM, 30, 'song')],
             760, 460, 'm', ar)

# ---------- 镜头 10：巴特利特 ----------
def bartlett_scene(cv, t):
    a = window(t, 55.0, 64.0, 0.7, 0.6)
    cv.gd.polygon([(480 * .5, 0), (330 * .5, 860 * .5), (630 * .5, 860 * .5)], fill=sc((90, 76, 50), a * 0.7))
    ellipse(cv, 480, 516, 28, fill=(40, 35, 28), a=a)
    rect(cv, 428, 552, 532, 660, fill=(40, 35, 28), a=a, r=18)
    cv.d.polygon([(392 * SS, 630 * SS), (568 * SS, 630 * SS), (548 * SS, 820 * SS), (412 * SS, 820 * SS)],
                 fill=mix((30, 26, 21), a, cv.bg), outline=mix(sc(GOLD, 0.6), a, cv.bg), width=SS)
    line(cv, [(300, 821), (660, 821)], (74, 66, 54), 1, a)
    l1 = parse("「人类最大的缺陷，")
    l2 = parse("是无法理解【指数函数】。」")
    total = sum(len(s) for s, _ in l1 + l2)
    k = int(total * clamp((t - 55.8) / 3.0))
    def cut(segs, k):
        out = []
        for s, c in segs:
            if k <= 0: break
            out.append((s[:k], c)); k -= len(s)
        return out, k
    s1, k = cut(l1, k)
    s2, _ = cut(l2, k)
    for segs, y in [(s1, 450), (s2, 530)]:
        if segs:
            rich(cv, [(s, c, 50, 'song', c == GOLD) for s, c in segs], 760, y, 'l', a)
    rich(cv, [("The greatest shortcoming of the human race is our inability", DIM, 20, 'geoi')], 762, 600, 'l',
         a * ease((t - 59.0) / 0.6))
    rich(cv, [("to understand the exponential function.", DIM, 20, 'geoi')], 762, 630, 'l', a * ease((t - 59.0) / 0.6))
    rich(cv, [("—— 艾伯特·巴特利特，物理学家", CREAM_D, 22, 'song')], 762, 690, 'l', a * ease((t - 59.5) / 0.6))

# ---------- 镜头 11~14：细菌瓶 ----------
_rb = np.random.default_rng(5)
BDOTS = _rb.uniform(0.04, 0.96, (700, 2))

def bottle_m(t):
    if t < 71.6: u = clamp((t - 64.6) / 7.0); return 50 * (1 - (1 - u) ** 2)
    if t < 78.5: return 50 + 5 * ease((t - 71.6) / 0.8)
    if t < 84.0: return 55 + 5 * clamp((t - 78.5) / 4.0)
    return 60 + 2 * clamp((t - 86.5) / 3.5)

def alarm(t):
    return max(window(t, 82.5, 85.0, 0.15, 0.8), window(t, 90.0, 92.0, 0.15, 0.8))

def bottle(cv, cx, yb, s, frac, a, rk):
    bw, bh = 300 * s, 440 * s
    col = lerpc(GOLD, (214, 84, 64), rk)
    if frac > 0:
        h = frac * (bh - 8 * s)
        rect(cv, cx - bw / 2 + 5 * s, yb - 4 * s - h, cx + bw / 2 - 5 * s, yb - 4 * s,
             fill=lerpc((96, 78, 44), (110, 40, 30), rk), a=a, r=min(24 * s, h / 2))
        for u, v in BDOTS:
            if v < frac:
                ellipse(cv, cx - bw / 2 + u * bw, yb - 4 * s - v * (bh - 8 * s), 1.6 * s + 0.4,
                        fill=lerpc(GOLD_L, (240, 140, 110), rk), a=a)
        ys = yb - 4 * s - h
        line(cv, [(cx - bw / 2 + 6 * s, ys), (cx + bw / 2 - 6 * s, ys)], col, 1.5, a, glow=1.0)
    rect(cv, cx - bw / 2, yb - bh, cx + bw / 2, yb, outline=col, w=1.5, a=a, r=30 * s)
    rect(cv, cx - 55 * s, yb - bh - 70 * s, cx + 55 * s, yb - bh, outline=col, w=1.2, a=a)
    rect(cv, cx - 70 * s, yb - bh - 86 * s, cx + 70 * s, yb - bh - 70 * s, outline=col, w=1.2, a=a)

def clock_text(m):
    tot = 11 * 60 + int(m + 1e-6)
    return f"{tot // 60}:{tot % 60:02d}"

def bottle_scene(cv, t):
    a = window(t, 64.0, 92.0, 0.7, 0.6)
    m = bottle_m(t)
    rk = alarm(t)
    tr = ease((t - 84.0) / 1.2)
    total = 2 ** (m - 60)
    cx, yb, s = lerp(820, 480, tr), lerp(840, 800, tr), lerp(1, 0.62, tr)
    bottle(cv, cx, yb, s, min(1, total), a, rk)
    if tr > 0:
        for i in range(3):
            ai = a * ease((t - 85.0 - i * 0.25) / 0.6)
            bottle(cv, 800 + i * 320, 800, 0.62, clamp(total - 1 - i), ai, rk)
        rich(cv, [("新发现的 3 个瓶子", DIM, 22, 'song')], 1120, 440, 'm', a * ease((t - 85.6) / 0.6))
        line(cv, [(700, 455), (1540, 455)], DIM, 1, a * 0.4 * ease((t - 85.6) / 0.6))
    # 时钟
    ac = a * (1 - tr)
    ccx, ccy, cr = 1400, 470, 120
    col = lerpc(GOLD, (214, 84, 64), rk)
    if ac > 0:
        ellipse(cv, ccx, ccy, cr, fill=(18, 16, 13), outline=sc(col, 0.8), w=1.5, a=ac)
        for i in range(12):
            ang = i / 12 * 2 * math.pi
            r0 = cr - (16 if i % 3 == 0 else 9)
            line(cv, [(ccx + math.sin(ang) * r0, ccy - math.cos(ang) * r0),
                      (ccx + math.sin(ang) * (cr - 4), ccy - math.cos(ang) * (cr - 4))], col, 1.2, ac)
        ha = (11 + m / 60) / 12 * 2 * math.pi
        ma = (m % 60) / 60 * 2 * math.pi
        line(cv, [(ccx, ccy), (ccx + math.sin(ha) * 60, ccy - math.cos(ha) * 60)], CREAM, 3, ac)
        line(cv, [(ccx, ccy), (ccx + math.sin(ma) * 96, ccy - math.cos(ma) * 96)], col, 2, ac, glow=0.8)
        ellipse(cv, ccx, ccy, 5, fill=col, a=ac)
        pct = min(1, total) * 100
        ptxt = f"{pct:.2f}%" if pct < 1 else (f"{pct:.1f}%" if pct < 10 else f"{pct:.0f}%")
        rich(cv, [("已满  ", DIM, 22, 'song'), (ptxt, col, 40, 'geo', True)], ccx, 740, 'm', ac)
    dx, dy, ds = lerp(ccx, 960, tr), lerp(660, 250, tr), lerp(54, 76, tr)
    rich(cv, [(clock_text(m), col, ds, 'geo', True)], dx, dy, 'm', a)

# ---------- 镜头 15：S 曲线 ----------
def _lg(u): return 1 / (1 + math.exp(-12 * (u - 0.55)))
_L0, _L1 = _lg(0), _lg(1)

def scurve_scene(cv, t):
    a = window(t, 92.0, 100.0, 0.6, 0.5)
    x0, x1, yb, yt = 360, 1560, 820, 300
    line(cv, [(x0, yb), (x1 + 30, yb)], DIM, 1, a)
    line(cv, [(x0, yb), (x0, yt - 60)], DIM, 1, a)
    rich(cv, [("时间", DIM, 18, 'song')], x1 + 30, yb + 34, 'r', a)
    rich(cv, [("数量", DIM, 18, 'song')], x0 - 14, yt - 70, 'r', a)
    p = ease((t - 92.4) / 2.6)
    mph = ease((t - 95.6) / 1.6)
    ac = ease((t - 95.3) / 0.5) * a
    if ac > 0:
        dashed(cv, x0, x1, yt, (214, 84, 64), ac * 0.9, 12, 8, 1.5)
        rich(cv, [("天花板：资源 · 空间 · 物理极限", (214, 110, 90), 20, 'song')], x1, yt - 16, 'r', ac)
    pts = []
    for i in range(int(200 * p) + 1):
        u = i / 200
        ye = (math.exp(12 * (u - 0.55)) - _L0) / (_L1 - _L0)
        yl = (_lg(u) - _L0) / (_L1 - _L0)
        y = yb - lerp(ye, yl, mph) * (yb - yt)
        if y < -40: break
        pts.append((lerp(x0, x1, u), y))
    if len(pts) > 1:
        line(cv, pts, GOLD, 2.2, a, glow=1.2)
        gdot(cv, pts[-1][0], pts[-1][1], 14, GOLD_L, a)
    for i, s in enumerate(["培养皿里的细菌", "一个国家的人口", "芯片上的晶体管"]):
        ai = a * ease((t - 97.2 - i * 0.4) / 0.5)
        ellipse(cv, 392, 352 + i * 44, 3, fill=GOLD, a=ai)
        rich(cv, [(s, CREAM_D, 22, 'song')], 408, 360 + i * 44, 'l', ai)

# ---------- 镜头 16~18：你 ----------
def person_scene(cv, t):
    a = window(t, 100.0, 108.0, 0.7, 0.6)
    z = lerp(1.0, 1.08, ease((t - 100) / 8))
    def T(x, y): return 960 + (x - 960) * z, 600 + (y - 600) * z
    pts = [T(lerp(200, 1760, i / 160), 770 - 330 * (math.exp(5 * i / 160) - 1) / (math.exp(5) - 1)) for i in range(161)]
    pr = ease((t - 100.3) / 2.0)
    n = max(2, int(len(pts) * pr))
    line(cv, pts[:n], GOLD, 2, a, glow=1.0)
    px, py = T(440, 770)
    gdot(cv, px, py - 60, 90, (110, 92, 60), a * 0.6)
    stick(cv, px, py, a * ease((t - 101.0) / 0.8), 120 * z)
    rich(cv, [("你在这里", DIM, 20, 'song')], px, py + 44, 'm', a * ease((t - 102.0) / 0.6))
    ex, ey = pts[-1]
    rich(cv, [("撞墙", (214, 110, 90), 20, 'song')], ex - 10, max(ey + 40, 160), 'r', a * ease((t - 103.0) / 0.6))

def compound_scene(cv, t):
    a = window(t, 108.0, 118.0, 0.6, 0.6)
    x0, x1, y0, ppu = 360, 1520, 780, 13.6
    line(cv, [(x0, y0), (x1 + 20, y0)], DIM, 1, a)
    line(cv, [(x0, y0), (x0, 220)], DIM, 1, a)
    rich(cv, [("第 1 天", DIM, 18, 'song')], x0, y0 + 32, 'm', a)
    rich(cv, [("第 365 天", DIM, 18, 'song')], x1, y0 + 32, 'm', a)
    dashed(cv, x0, x1, y0 - ppu, DIM, a * 0.5, 6, 6)
    rich(cv, [("1", DIM, 18, 'geo')], x0 - 12, y0 - ppu + 6, 'r', a)
    p = ease((t - 108.6) / 5.4)
    nd = int(365 * p)
    up = [(lerp(x0, x1, d / 365), y0 - ppu * 1.01 ** d) for d in range(0, nd + 1, 3)]
    dn = [(lerp(x0, x1, d / 365), y0 - ppu * 0.99 ** d) for d in range(0, nd + 1, 3)]
    if len(up) > 1:
        line(cv, dn, (140, 132, 120), 2, a)
        line(cv, up, GOLD, 2.4, a, glow=1.2)
        gdot(cv, up[-1][0], up[-1][1], 14, GOLD_L, a)
    ae = a * ease((t - 114.0) / 0.6)
    rich(cv, [("1.01", GOLD, 34, 'geo', True), ("365", GOLD, 20, 'geo', True, -16), ("  ≈ ", GOLD, 30, 'geo'),
              ("37.8", GOLD_L, 50, 'geo', True)], x1 + 30, y0 - ppu * 37.8 + 16, 'l', ae)
    rich(cv, [("0.99", (150, 142, 130), 28, 'geo'), ("365", (150, 142, 130), 17, 'geo', False, -13),
              ("  ≈ 0.03", (150, 142, 130), 28, 'geo')], x1 + 30, y0 + 6, 'l', ae)

def fold3_scene(cv, t):
    a = window(t, 118.0, 126.0, 0.7, 0.6)
    z = lerp(1.15, 0.88, ease((t - 118) / 8))
    def T(x, y): return 960 + (x - 960) * z, 640 + (y - 640) * z
    gx0, gy = T(300, 760); gx1, _ = T(1620, 760)
    line(cv, [(gx0, gy), (gx1, gy)], (74, 66, 54), 1, a)
    sx0, sy0 = T(700, 750); sx1, sy1 = T(1000, 760)
    rect(cv, sx0, sy0, sx1, sy1, fill=PAPER, a=a)
    for i in range(1, 8):
        yy = lerp(sy0, sy1, i / 8)
        line(cv, [(sx0, yy), (sx1, yy)], (186, 175, 154), 0.5, a)
    line(cv, [(sx0, sy0), (sx1, sy0)], GOLD_L, 1.5, a, glow=1.0)
    rich(cv, [("×3", GOLD, 34, 'geo', True), ("  0.8 mm", CREAM_D, 22, 'geo')], (sx0 + sx1) / 2, sy0 - 26, 'm', a)
    ag = a * ease((t - 119.5) / 1.5)
    for xx in (sx0, sx1):
        y = sy0 - 70
        while y > -20:
            line(cv, [(xx, y), (xx, y - 10)], sc(GOLD, 0.6), 1, ag * 0.6)
            y -= 20
    rich(cv, [("×42  →  月球", sc(GOLD, 0.8), 22, 'song')], (sx0 + sx1) / 2, 150, 'm', ag * 0.8)
    px, py = T(1120, 760)
    stick(cv, px, py, a, 120 * z, lean=-0.3)

def sentence_scene(cv, t):
    a = window(t, 126.0, 131.6, 0.7, 0.5)
    pts = [(lerp(200, 1720, i / 120), 900 - 260 * (math.exp(4 * i / 120) - 1) / (math.exp(4) - 1)) for i in range(121)]
    line(cv, pts, sc(GOLD, 0.35), 1.5, a * 0.6)
    rich(cv, [("不是努力没有用，", CREAM, 54, 'song')], 960, 470, 'm', a * ease((t - 126.3) / 0.8))
    rich(cv, [(s, c, 54, 'song', c == GOLD) for s, c in parse("是指数的前半段，【看起来就像没用】。")], 960, 570, 'm',
         a * ease((t - 127.6) / 0.8))

# ---------- 项目配置 ----------
SCENES = [
    (0.0, 4.2, shot1),
    (4.2, 17.4, lambda cv, t: (stack_scene(cv, t), t >= 9.2 and question_scene(cv, t))),
    (17.4, 27.4, shot5),
    (27.4, 31.0, title),
    (31.0, 55.0, chess_scene),
    (55.0, 64.0, bartlett_scene),
    (64.0, 92.0, bottle_scene),
    (92.0, 100.0, scurve_scene),
    (100.0, 108.0, person_scene),
    (108.0, 118.0, compound_scene),
    (118.0, 126.0, fold3_scene),
    (126.0, 131.6, sentence_scene),
    (131.6, DUR, lambda cv, t: title(cv, t, 131.6)),
]

def bg_color(t):
    if 17.3 <= t < 27.4:     # 越过 100 km 后背景从暖黑过渡到夜空蓝
        return lerpc(BG, SPACE, clamp((logh(n5(t)) - 3.6) / 2.0))
    return BG

def master(t):               # 两处整屏淡出淡入：进入片头标题卡前后
    if t < 27.4: return ease(t / 0.5) * (1 - ease((t - 26.9) / 0.5))
    if t < 31.0: return ease((t - 27.4) / 0.4) * (1 - ease((t - 30.6) / 0.4))
    return 1 - ease((t - (DUR - 0.7)) / 0.7)

def sound(m):
    # 1. 纸
    m.paper(2.0, 0.35, 0.3)
    for ft in FOLD_T: m.paper(ft, 0.28)
    # 5. 一路到月球：每对折一次一声，音高随次数上升；上升音接撞击
    prev = 10
    for i in range(int((T5B - T5A) * 1000)):
        tk = T5A + i / 1000
        n = int(n5(tk) + 1e-6)
        if n > prev and tk < T_HIT:
            m.blip(tk, 520 * 2 ** ((n - 10) / 32 * 1.6), 0.10); prev = n
    m.riser(17.6, T_HIT)
    m.boom(T_HIT); m.shimmer(T_HIT, 0.05, 3.5); m.duck(T_HIT)
    m.shimmer(27.8, 0.03)
    # 7-9. 棋盘
    for i, ct in enumerate(CELL_T): m.blip(ct, 400 * 2 ** (i / 63 * 2.0), 0.07)
    m.grains(40.9, 3.8); m.thud(44.6)
    m.riser(49.0, 51.6, 0.2, 60, 240); m.boom(51.6, 0.6, 50, 2.5)
    # 10. 打字机
    for k in range(22): m.tick(55.8 + k * 3.0 / 22, 0.05)
    # 11-14. 细菌瓶：最后 5 分钟滴答，12:00 撞墙时音乐骤停
    for mm in range(56, 61): m.tick(78.5 + (mm - 55) * 0.8, 0.22, 0.08)
    m.boom(82.5, 0.8, 45); m.mute(82.5, 84.5)
    for mm in (61, 62): m.tick(86.5 + (mm - 60) * 1.75, 0.22, 0.08)
    m.boom(90.0, 0.6, 45, 2.5)
    # 15. S 曲线撞上天花板
    m.thud(95.6, 0.45, 1.5); m.blip(95.6, 180, 0.2, 0.4)
    # 19-20. 金句 / 片尾
    m.shimmer(127.6); m.shimmer(132.0)

if __name__ == '__main__':
    vkit.main(__file__)
