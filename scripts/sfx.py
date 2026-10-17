"""sfx —— 代码合成音效 + 背景音乐混音

用法（在项目文件里定义 sound(m)）：
    def sound(m):
        m.paper(2.0)                 # 纸张翻折沙沙声
        m.blip(31.8, 520)            # 短促提示音（计数、逐格点亮）
        m.riser(17.6, 24.4)          # 上升音：从 t0 到 t1 越来越强，接一个撞击
        m.boom(24.4)                 # 低频冲击（揭晓、撞墙）
        m.thud(44.6)                 # 闷响（落定）
        m.shimmer(27.8)              # 高频余晖（标题、金句）
        m.tick(78.5)                 # 钟表滴答 / 打字
        m.grains(40.9, 3.8)          # 颗粒倾泻（米粒、沙子、数据涌入）
        m.duck(24.4)                 # 让背景音乐在这一刻避让（压低）
        m.mute(82.5, 84.5)           # 背景音乐骤停（最强烈的情绪点，全片最多用一次）
        m.piano(0.3, [220])          # 没有背景音乐时可用的钢琴单音/和弦
        m.pad(...)                   # 没有背景音乐时的低频铺底

背景音乐：整段铺底音乐通常已经是 -14 LUFS 左右的满响度，默认压低 6 dB 给音效让位；
最终成片由 encode 统一做 loudnorm 到 -14 LUFS。
"""
import os, wave, shutil, subprocess
import numpy as np

SR = 44100

def _lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y

def _ffmpeg():
    p = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if p: return p
    raise RuntimeError("找不到 ffmpeg：请安装并加入 PATH，或设置环境变量 FFMPEG")

class Mixer:
    def __init__(s, dur, seed=3):
        s.dur = dur
        s.N = int(dur * SR)
        s.fx = np.zeros(s.N)
        s.bed = np.zeros(s.N)       # 合成铺底（pad / piano），有背景音乐时可不用
        s.rng = np.random.default_rng(seed)
        s.ducks, s.mutes = [], []

    # ---- 基础 ----
    def _t(s, d): return np.arange(int(d * SR)) / SR

    def add(s, sig, t0, gain=1.0, bus='fx'):
        i = int(t0 * SR)
        if i >= s.N or i < 0: return
        sig = sig[:s.N - i]
        (s.fx if bus == 'fx' else s.bed)[i:i + len(sig)] += sig * gain

    # ---- 音效 ----
    def paper(s, t0, gain=0.3, d=0.16):
        t = s._t(d); n = s.rng.normal(0, 1, len(t)); n = n - _lowpass(n, 0.08)
        s.add(n * np.exp(-t * 28) * np.minimum(1, t / 0.004), t0, gain)

    def blip(s, t0, f=520, gain=0.1, d=0.07):
        t = s._t(d); s.add(np.sin(2 * np.pi * f * t) * np.exp(-t * 60), t0, gain)

    def riser(s, t0, t1, gain=0.22, f0=80, f1=320):
        d = t1 - t0; t = s._t(d); n = s.rng.normal(0, 1, len(t))
        tone = np.sin(2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR)
        s.add(((n - _lowpass(n, 0.02)) * 0.05 + tone * 0.6) * (t / d) ** 2.2, t0, gain)

    def boom(s, t0, gain=0.75, f0=58, d=3.0):
        t = s._t(d)
        s.add(np.sin(2 * np.pi * np.cumsum(f0 * np.exp(-t * 1.2) + 30) / SR) * np.exp(-t * 1.6), t0, gain)
        s.thud(t0, gain * 0.6, d)

    def thud(s, t0, gain=0.4, d=1.2):
        t = s._t(d); n = _lowpass(s.rng.normal(0, 1, len(t)), 0.05)
        s.add(n * np.exp(-t * 5), t0, gain)

    def shimmer(s, t0, gain=0.035, d=3.0):
        t = s._t(d)
        sig = sum(np.sin(2 * np.pi * f * t) for f in [1760, 2637, 3520]) * np.exp(-t * 1.3) * np.minimum(1, t / 0.02)
        s.add(sig, t0, gain)

    def tick(s, t0, gain=0.2, d=0.06):
        t = s._t(d); n = s.rng.normal(0, 1, len(t)); n = n - _lowpass(n, 0.3)
        s.add(n * np.exp(-t * 120) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90) * 0.5, t0, gain)

    def grains(s, t0, d, gain=0.35):
        t = s._t(d); n = s.rng.normal(0, 1, len(t)); n = n - _lowpass(n, 0.15)
        s.add(n * (s.rng.random(len(t)) < 0.02 + 0.2 * (t / d) ** 2) * (t / d) ** 1.5, t0, gain)

    # ---- 无背景音乐时的合成配乐 ----
    def piano(s, t0, freqs, gain=0.3, d=5.0):
        t = s._t(d)
        for f in freqs:
            sig = sum((1 / k ** 1.6) * np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k)) * np.exp(-t * (0.9 + 0.7 * k))
                      for k in range(1, 7))
            s.add(sig * np.minimum(1, t / 0.006), t0, gain, 'bed')

    def pad(s, times, levels, freqs=(55, 82.41, 110, 164.8)):
        """低频铺底：times/levels 是包络折线（例如 [0,3,20,24] / [0,.05,.06,.12]）"""
        t = np.arange(s.N) / SR
        sig = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate(freqs)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.18 * t))
        s.bed += sig * np.interp(t, times, levels)

    # ---- 背景音乐控制 ----
    def duck(s, t0, depth=0.45, release=1.4):
        s.ducks.append((t0, depth, release))

    def mute(s, t0, t1):
        s.mutes.append((t0, t1))

    # ---- 输出 ----
    def _music(s, path, gain_db):
        raw = subprocess.run([_ffmpeg(), "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        mus = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
        xf, base = int(2.0 * SR), mus
        ramp = np.linspace(0, 1, xf)[:, None]
        while len(mus) < s.N and len(base) > 2 * xf:    # 音乐比视频短：首尾 2 秒交叉淡化循环接上
            mus = np.concatenate([mus[:-xf], mus[-xf:] * (1 - ramp) + base[:xf] * ramp, base[xf:]])
        out = np.zeros((s.N, 2)); out[:min(s.N, len(mus))] = mus[:s.N]
        t = np.arange(s.N) / SR
        env = np.interp(t, [0, 1.0, s.dur - 2.5, s.dur], [0, 1, 1, 0])
        for t0, depth, rel in s.ducks:
            env *= np.interp(t, [t0 - 0.05, t0 + 0.05, t0 + rel, t0 + rel + 0.01], [1, depth, 1, 1])
        for t0, t1 in s.mutes:
            env *= np.interp(t, [t0 - 0.2, t0, t1, t1 + 1.5], [1, 0, 0, 1])
        return out * (env * 10 ** (gain_db / 20))[:, None]

    def render(s, out, music=None, gain_db=-6.0, fx_gain=0.55, reverb=0.3):
        fx = s.fx.copy()
        if reverb:
            t = s._t(1.8); ir = s.rng.normal(0, 1, len(t)) * np.exp(-t / 0.45); ir /= np.sqrt(np.sum(ir ** 2))
            L = 1 << int(np.ceil(np.log2(s.N + len(ir))))
            fx = fx + np.fft.irfft(np.fft.rfft(fx, L) * np.fft.rfft(ir, L), L)[:s.N] * reverb
            bed = s.bed + np.fft.irfft(np.fft.rfft(s.bed, L) * np.fft.rfft(ir, L), L)[:s.N] * 0.35
        else:
            bed = s.bed
        mono = fx * fx_gain + bed
        dl = int(0.012 * SR)       # 轻微 Haas 延迟让单声道音效有一点宽度
        st = np.stack([mono, np.concatenate([np.zeros(dl), mono[:-dl]]) * 0.97 + mono * 0.03], 1)
        if music:
            st = st + s._music(music, gain_db)
        st /= max(1.0, np.max(np.abs(st)) / 0.95)
        with wave.open(out, 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(st, -1, 1) * 32767).astype('<i2').tobytes())
