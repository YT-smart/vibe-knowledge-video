"""vkit —— 「知识大赏」黑金纪录片风动态信息图视频引擎

坐标系统一用 1920×1080（内部 2 倍超采样抗锯齿）。所有绘制函数第一个参数是画布 cv，
a 是不透明度（0~1，通过和背景色混合实现，所以只在深色底上成立）。
glow=… 的元素会额外画到半分辨率辉光层，最后模糊叠加，形成金色发光。

项目文件（见 example_video.py）只需定义：
    DUR, SCENES, SUBS, LABELS   以及可选的 bg_color(t) / alarm(t) / sound(mixer) / MUSIC
然后在末尾调用 vkit.main(__file__)。

命令：
    python video.py preview out.jpg 3.5 10 22      抽这些秒数的帧拼成预览图（自查用）
    python video.py frames [起始秒 结束秒]            多进程渲染 PNG 帧到 build/frames
    python video.py audio [--music 路径|none]       合成音效 + 背景音乐到 build/audio.wav
    python video.py encode [输出.mp4] [--lite]        帧 + 音频 → MP4（--lite 压小体积）
    python video.py sample 0 30                     渲染并编码一段样片
    python video.py all                             全片：frames → audio → encode
背景音乐默认用项目里的 MUSIC（技能自带的 bgm.m4a）；--music 换成别的文件，--music none 不要音乐。
"""
import sys, os, math, glob, shutil, subprocess, importlib.util
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, SS, FPS = 1920, 1080, 2, 30

# ---------- 色板 ----------
BG = (11, 10, 8)          # 近黑暖底
SPACE = (6, 9, 20)        # 深蓝夜空（场景需要时用 bg_color 过渡）
GOLD = (201, 163, 91)     # 主强调色：关键词、曲线、数字
GOLD_L = (236, 204, 140)  # 亮金：高光、发光点
CREAM = (236, 228, 212)   # 正文
CREAM_D = (178, 168, 150) # 次要文字
DIM = (128, 116, 96)      # 角标、刻度、注释
PAPER = (226, 216, 196)
RED = (170, 60, 48)       # 印章；警示用 ALERT
ALERT = (214, 84, 64)

# ---------- 字体（按优先级找第一个存在的）----------
_FONT_CANDIDATES = {
    'song': [  # 中文衬线（宋体/明朝）。装了思源宋体会自动优先使用
        r"C:\Windows\Fonts\SourceHanSerifSC-Medium.otf", r"C:\Windows\Fonts\SourceHanSerifSC-Regular.otf",
        r"C:\Windows\Fonts\NotoSerifSC-Medium.otf", r"C:\Windows\Fonts\NotoSerifCJKsc-Medium.otf",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts\SourceHanSerifSC-Medium.otf"),
        os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts\NotoSerifSC-Medium.otf"),
        r"C:\Windows\Fonts\simsun.ttc", "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Medium.ttc"],
    'geo': [r"C:\Windows\Fonts\georgia.ttf", "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    'geoi': [r"C:\Windows\Fonts\georgiai.ttf", "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"],
}
FONTS = {k: next((p for p in v if os.path.exists(p)), None) for k, v in _FONT_CANDIDATES.items()}
SONG_IS_THIN = FONTS['song'] is not None and 'simsun' in FONTS['song'].lower()   # 宋体太细，描边加粗

# ---------- 数学工具 ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def lerpc(c1, c2, u): return tuple(int(lerp(c1[i], c2[i], u)) for i in range(3))
def sc(c, k): return tuple(int(v * k) for v in c)
def mix(c, a, bg): return tuple(int(bg[i] + (c[i] - bg[i]) * clamp(a)) for i in range(3))
def window(t, t0, t1, fi=0.35, fo=0.35):
    """t0~t1 之间可见，前后各 fi/fo 秒淡入淡出"""
    return clamp((t - t0) / fi) * clamp((t1 - t) / fo)

_fc = {}
def Fp(kind, px):
    px = max(4, int(px))
    if (kind, px) not in _fc:
        if FONTS[kind] is None:
            raise RuntimeError(f"找不到 {kind} 字体，请安装思源宋体/宋体与 Georgia")
        _fc[(kind, px)] = ImageFont.truetype(FONTS[kind], px)
    return _fc[(kind, px)]

# ---------- 画布与图元 ----------
class Cv:
    def __init__(s, bg=BG):
        s.bg = bg
        s.im = Image.new('RGB', (W * SS, H * SS), bg)
        s.d = ImageDraw.Draw(s.im)
        s.g = Image.new('RGB', (W // 2, H // 2), (0, 0, 0))   # 辉光层（半分辨率）
        s.gd = ImageDraw.Draw(s.g)

def rect(cv, x0, y0, x1, y1, fill=None, outline=None, w=1, a=1.0, r=0):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
    f = mix(fill, a, cv.bg) if fill else None
    o = mix(outline, a, cv.bg) if outline else None
    box = [x0 * SS, y0 * SS, x1 * SS, y1 * SS]
    if r:
        cv.d.rounded_rectangle(box, radius=r * SS, fill=f, outline=o, width=int(w * SS) if o else 0)
    else:
        cv.d.rectangle(box, fill=f, outline=o, width=int(w * SS) if o else 0)

def line(cv, pts, c, w=1.0, a=1.0, glow=0.0):
    if a <= 0 or len(pts) < 2: return
    cv.d.line([(x * SS, y * SS) for x, y in pts], fill=mix(c, a, cv.bg), width=max(1, int(w * SS)), joint='curve')
    if glow:
        cv.gd.line([(x * .5, y * .5) for x, y in pts], fill=sc(c, a * glow), width=max(1, int(w * 1.2)))

def dashed(cv, x0, x1, y, c, a, dash=10, gap=8, w=1):
    x = x0
    while x < x1:
        line(cv, [(x, y), (min(x + dash, x1), y)], c, w, a)
        x += dash + gap

def ellipse(cv, cx, cy, r, fill=None, outline=None, w=1, a=1.0):
    if a <= 0: return
    f = mix(fill, a, cv.bg) if fill else None
    o = mix(outline, a, cv.bg) if outline else None
    cv.d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=f, outline=o,
                 width=int(w * SS) if o else 0)

def polygon(cv, pts, fill=None, outline=None, a=1.0):
    if a <= 0: return
    cv.d.polygon([(x * SS, y * SS) for x, y in pts], fill=mix(fill, a, cv.bg) if fill else None,
                 outline=mix(outline, a, cv.bg) if outline else None)

def gdot(cv, x, y, r, c, a):
    """只画在辉光层的一团柔光"""
    if a <= 0: return
    cv.gd.ellipse([(x - r) * .5, (y - r) * .5, (x + r) * .5, (y + r) * .5], fill=sc(c, a))

def rich(cv, segs, x, y, anchor='m', a=1.0):
    """多段混排文字，按基线对齐。
    segs: (文字, 颜色, 字号, 字体['song'|'geo'|'geoi'][, 发光][, 上下偏移dy])；anchor: 'l'|'m'|'r'
    返回总宽度。上标写法：("42", CREAM, 16, 'geo', False, -12)"""
    items = []
    for s in segs:
        t, c, sz, k = s[:4]
        gl = s[4] if len(s) > 4 else False
        dy = s[5] if len(s) > 5 else 0
        f = Fp(k, sz * SS)
        items.append((t, c, sz, k, gl, dy, f, f.getlength(t)))
    tw = sum(i[7] for i in items)
    if a <= 0: return tw / SS
    x0 = x * SS - (tw / 2 if anchor == 'm' else (tw if anchor == 'r' else 0))
    for t, c, sz, k, gl, dy, f, w in items:
        col = mix(c, a, cv.bg)
        sw = max(1, round(sz * SS / 46)) if (k == 'song' and SONG_IS_THIN) else 0
        cv.d.text((x0, (y + dy) * SS), t, font=f, fill=col, anchor='ls', stroke_width=sw, stroke_fill=col)
        if gl:
            cv.gd.text((x0 / SS * .5, (y + dy) * .5), t, font=Fp(k, sz * .5),
                       fill=sc(c, a * (gl if gl is not True else 1)), anchor='ls')
        x0 += w
    return tw / SS

def spaced(cv, s, x, y, c, sz, k, sp, a=1.0, gl=False):
    """字间距加宽的居中标题"""
    f = Fp(k, sz * SS)
    ws = [f.getlength(ch) / SS for ch in s]
    x0 = x - (sum(ws) + sp * (len(s) - 1)) / 2
    for ch, w in zip(s, ws):
        rich(cv, [(ch, c, sz, k, gl)], x0, y, 'l', a)
        x0 += w + sp

def parse(s, hi=GOLD, base=CREAM):
    """'普通【高亮】普通' → [(文字, 颜色)…]"""
    out, on = [], False
    for part in s.replace('】', '【').split('【'):
        if part: out.append((part, hi if on else base))
        on = not on
    return out

def curve(fn, x0, x1, y0, h, n=160, upto=1.0):
    """fn: [0,1]→[0,1] 的函数，返回屏幕点列（y0 是底线，h 是高度）"""
    return [(lerp(x0, x1, i / n), y0 - fn(i / n) * h) for i in range(int(n * upto) + 1)]

def expo(k=4.0):
    return lambda u: (math.exp(k * u) - 1) / (math.exp(k) - 1)

def stick(cv, x, y, a, h=120, lean=0.0, col=CREAM):
    """火柴人（站在 (x, y) 的地面上）"""
    hx, hy = x + lean * 30, y - h
    ellipse(cv, hx, hy, h * 0.11, fill=col, a=a)
    sh = (x + lean * 22, y - h * 0.82)
    hip = (x, y - h * 0.42)
    line(cv, [sh, hip], col, 3, a, glow=0.5)
    line(cv, [hip, (x - h * 0.12, y)], col, 3, a, glow=0.5)
    line(cv, [hip, (x + h * 0.12, y)], col, 3, a, glow=0.5)
    line(cv, [sh, (x - h * 0.14, y - h * 0.5)], col, 2.5, a)
    line(cv, [sh, (x + h * 0.14, y - h * 0.5)], col, 2.5, a)

def hud_box(cv, x0, y0, x1, y1, a):
    """档案风数据框（深底 + 细金边），用来压住背后的线条"""
    rect(cv, x0, y0, x1, y1, fill=(14, 13, 12), outline=sc(GOLD, 0.45), w=1, a=a, r=4)

# ---------- 版式：角标 / 字幕 / 标题卡 ----------
WATERMARK = "◎ Vibe知识大赏"

def corner_labels(cv, t, labels, seal="算"):
    """labels: [(t0, t1, 左上大字, 左上小字, 右上英文出处|None, 右上中文书名|None), …]
    左上大字可以是字符串（用 Georgia 46 号）或 rich 的 segs 列表"""
    for t0, t1, big, sub, en, cn in labels:
        a = window(t, t0, t1, 0.8, 0.5)
        if a <= 0: continue
        segs = [(big, GOLD, 46, 'geo')] if isinstance(big, str) else big
        rich(cv, segs, 60, 96, 'l', a)
        rich(cv, [(sub, DIM, 18, 'song')], 62, 128, 'l', a)
        line(cv, [(60, 144), (250, 144)], DIM, 1, a * 0.5)
        if en:
            rich(cv, [(en, DIM, 16, 'geoi')], 1816, 64, 'r', a)
            rich(cv, [(cn, CREAM_D, 19, 'song')], 1816, 94, 'r', a)
            rect(cv, 1828, 70, 1856, 98, fill=RED, a=a * 0.9)
            rich(cv, [(seal, (240, 225, 210), 17, 'song')], 1842, 91, 'm', a)

def subtitles(cv, t, subs, y=1000, size=40):
    """subs: [(t0, t1, '文字【关键词】'), …]，关键词描金发光"""
    for t0, t1, s in subs:
        a = window(t, t0, t1)
        if a > 0:
            rich(cv, [(txt, c, size, 'song', c == GOLD) for txt, c in parse(s)], 960, y, 'm', a)

def title_card(cv, t, t0, title, en, tagline, curve_fn=None, curve_labels=("直觉", "现实")):
    """大标题卡：英文小字 → 金色大标题 → 一条生长的金色曲线（可选，对比一条虚线）→ 一句副标题。约 3.5 秒"""
    t = t - t0
    a1 = ease((t - 0.3) / 0.8)
    spaced(cv, en, 960, 330, sc(GOLD, 0.8), 22, 'geo', 9, a1)
    a2 = ease((t - 0.5) / 1.0)
    spaced(cv, title, 960, 480 - 10 * a2, GOLD, 124, 'song', 22, a2, gl=0.8)
    x0, x1, yb = 700, 1220, 730
    up = ease((t - 1.1) / 1.5)
    if curve_fn and up > 0:
        al = ease((t - 1.8) / 0.6)
        lin = [(lerp(x0, x1, u / 60), yb - 40 * u / 60) for u in range(0, int(60 * up) + 1)]
        for i in range(0, len(lin) - 1, 2):
            line(cv, [lin[i], lin[i + 1]], DIM, 1.2, al)
        pts = curve(curve_fn, x0, x1, yb, 150, 120, up)
        if len(pts) > 1:
            line(cv, pts, GOLD, 2, 1, glow=1.2)
            gdot(cv, pts[-1][0], pts[-1][1], 14, GOLD_L, 0.9)
            ellipse(cv, pts[-1][0], pts[-1][1], 3, fill=GOLD_L)
        at = ease((t - 2.4) / 0.5)
        if curve_labels:
            rich(cv, [(curve_labels[0], DIM, 18, 'song')], x1 + 18, yb - 34, 'l', at)
            rich(cv, [(curve_labels[1], GOLD, 18, 'song')], x1 + 18, yb - 144, 'l', at)
    if tagline:
        rich(cv, [(tagline, CREAM_D, 28, 'song')], 960, 830 if curve_fn else 640, 'm', ease((t - 2.3) / 0.7))

# ---------- 后期：辉光、暗角、警示泛红、颗粒 ----------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
VIG = np.clip(1 - 0.62 * _r ** 2.2, 0, 1).astype(np.float32)[..., None]
EDGE = np.clip(_r * 1.25, 0, 1).astype(np.float32)[..., None] ** 1.6
del _yy, _xx

def finish(cv, fi, master=1.0, alarm=0.0, grain=3.2):
    im = cv.im.resize((W, H), Image.LANCZOS)
    arr = np.asarray(im, np.float32)
    g1 = np.asarray(cv.g.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR), np.float32)
    g2 = np.asarray(cv.g.filter(ImageFilter.GaussianBlur(16)).resize((W, H), Image.BILINEAR), np.float32)
    arr = (arr + g1 * 0.7 + g2 * 0.9) * VIG
    if alarm > 0:   # 警示：画面四周泛红（不要整屏变红，太脏）
        arr = arr + alarm * EDGE * np.array([70, 14, 8], np.float32)
    if grain:
        arr = arr + np.random.default_rng(fi).normal(0, grain, (H, W, 1)).astype(np.float32)
    return Image.fromarray(np.clip(arr * master, 0, 255).astype(np.uint8))

# ---------- 渲染调度 ----------
P = None   # 当前项目模块

def load_project(path):
    global P
    spec = importlib.util.spec_from_file_location("vk_project", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vk_project"] = mod
    spec.loader.exec_module(mod)
    P = mod
    return mod

def master_fade(t):
    if hasattr(P, 'master'): return P.master(t)
    return ease(t / 0.5) * (1 - ease((t - (P.DUR - 0.7)) / 0.7))

def render(fi):
    t = fi / FPS
    cv = Cv(P.bg_color(t) if hasattr(P, 'bg_color') else BG)
    for t0, t1, fn in P.SCENES:
        if t0 <= t < t1:
            fn(cv, t); break
    corner_labels(cv, t, getattr(P, 'LABELS', []), getattr(P, 'SEAL', '算'))
    wm = getattr(P, 'WATERMARK', WATERMARK)
    if wm:
        rich(cv, [(wm, DIM, 16, 'song')], 1860, 1052, 'r', 0.8 * ease((t - 0.6) / 0.8))
    subtitles(cv, t, getattr(P, 'SUBS', []))
    if hasattr(P, 'overlay'): P.overlay(cv, t)
    alarm = P.alarm(t) if hasattr(P, 'alarm') else 0.0
    return finish(cv, fi, master_fade(t), alarm)

def _init(path):
    load_project(path)

def _work(args):
    fi, out = args
    render(fi).save(os.path.join(out, f"{fi:05d}.png"), compress_level=1)
    return fi

# ---------- 外部工具 ----------
def tool(name):
    env = os.environ.get(name.upper())
    if env and os.path.exists(env): return env
    p = shutil.which(name)
    if p: return p
    raise RuntimeError(f"找不到 {name}：请安装 ffmpeg 并加入 PATH，或设置环境变量 {name.upper()} 指向可执行文件")

def _build(project_path):
    return os.path.join(os.path.dirname(os.path.abspath(project_path)), "build")

def cmd_preview(path, out, times):
    ims = [render(int(float(x) * FPS)).resize((960, 540)) for x in times]
    cols = 3 if len(ims) > 2 else len(ims)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (960 * cols, 540 * rows))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 960, (i // cols) * 540))
    sheet.save(out, quality=88)
    print("preview ->", out)

def cmd_frames(path, a=0.0, b=None):
    from multiprocessing import Pool
    out = os.path.join(_build(path), "frames")
    os.makedirs(out, exist_ok=True)
    b = P.DUR if b is None else b
    idx = range(int(round(a * FPS)), int(round(b * FPS)))
    n = os.cpu_count() or 2
    print(f"渲染 {len(idx)} 帧，{n} 进程 …", flush=True)
    with Pool(n, initializer=_init, initargs=(os.path.abspath(path),)) as p:
        for i, _ in enumerate(p.imap_unordered(_work, [(fi, out) for fi in idx], chunksize=4)):
            if i % 150 == 0: print(f"  {i}/{len(idx)}", flush=True)
    print("frames ->", out)

def cmd_audio(path, music=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sfx
    m = sfx.Mixer(P.DUR)
    if hasattr(P, 'sound'): P.sound(m)
    music = music or getattr(P, 'MUSIC', None)
    if music and music.lower() == "none":
        music = None
    if music and not os.path.isabs(music):
        music = os.path.join(os.path.dirname(os.path.abspath(path)), music)
    if music and not os.path.exists(music):
        print(f"注意：找不到背景音乐 {music}，本次只输出音效"); music = None
    out = os.path.join(_build(path), "audio.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    m.render(out, music=music, **getattr(P, 'MUSIC_OPTS', {}))
    print("audio ->", out)

def cmd_encode(path, out=None, lite=False, a=0.0, b=None):
    bd = _build(path)
    out = out or os.path.join(os.path.dirname(os.path.abspath(path)), "成片.mp4")
    b = P.DUR if b is None else b
    start = int(round(a * FPS))
    q = ["-crf", "26", "-maxrate", "5M", "-bufsize", "10M"] if lite else ["-crf", "21", "-maxrate", "12M", "-bufsize", "24M"]
    cmd = [tool("ffmpeg"), "-v", "error", "-y", "-framerate", str(FPS), "-start_number", str(start),
           "-i", os.path.join(bd, "frames", "%05d.png"), "-ss", str(a), "-t", str(b - a), "-i", os.path.join(bd, "audio.wav"),
           "-frames:v", str(int(round((b - a) * FPS))), "-af", "loudnorm=I=-14:TP=-1:LRA=11",
           "-c:v", "libx264", "-preset", "medium", "-tune", "grain", *q, "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("video ->", out, f"{os.path.getsize(out) / 1e6:.1f} MB")

def main(project_file):
    for s in (sys.stdout, sys.stderr):    # 非 UTF-8 控制台打印中文会报错
        try: s.reconfigure(encoding='utf-8', errors='replace')
        except Exception: pass
    path = os.path.abspath(project_file)
    load_project(path)
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    music = None
    if "--music" in args:
        i = args.index("--music"); music = args[i + 1]; del args[i:i + 2]
    lite = "--lite" in args
    args = [x for x in args if x != "--lite"]
    c = args[0]
    if c == "preview":
        cmd_preview(path, args[1], args[2:])
    elif c == "frames":
        cmd_frames(path, *(float(x) for x in args[1:3]))
    elif c == "audio":
        cmd_audio(path, music)
    elif c == "encode":
        cmd_encode(path, args[1] if len(args) > 1 else None, lite)
    elif c == "sample":
        a, b = float(args[1]), float(args[2])
        cmd_frames(path, a, b); cmd_audio(path, music)
        out = os.path.join(os.path.dirname(path), f"样片_{a:g}-{b:g}s.mp4")
        cmd_encode(path, out, lite, a, b)
    elif c == "all":
        cmd_frames(path); cmd_audio(path, music); cmd_encode(path, None, lite)
    else:
        print(__doc__)
