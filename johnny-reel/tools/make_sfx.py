"""Synthesize a deterministic, license-free SFX track spotted to index.html's timeline.

Every cue is (t, kind, gain). `t` is the EVENT frame; each generator returns
(samples, t_peak) and is placed at start = t - t_peak so the transient lands on
the event, per the sfx-spotting skill.
"""
import numpy as np, wave

SR = 48000
DUR = 15.0
rng = np.random.default_rng(7)  # seeded: byte-identical rebuilds


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) / d)


def lp(x, k):
    # simple one-pole low-pass, k in (0,1]: smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc); y[i] = acc
    return y


def click(pitch=1.0):
    n = int(0.05 * SR); t = np.arange(n) / SR
    s = (rng.standard_normal(n) * 0.6 + np.sin(2 * np.pi * 3200 * pitch * t)) * env(n, 0.0005, 0.008)
    s += np.sin(2 * np.pi * 180 * pitch * t) * env(n, 0.001, 0.012) * 0.8
    return s, 0.001


def tick(pitch=1.0):
    n = int(0.06 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 1900 * pitch * t) * env(n, 0.001, 0.015), 0.001


def whoosh(length=0.6, peak=0.75, bright=0.25):
    n = int(length * SR); t = np.arange(n) / SR
    x = lp(rng.standard_normal(n), bright)
    p = peak * length
    shape = np.where(t < p, (t / p) ** 2.2, np.exp(-(t - p) / (length * 0.12)))
    return x * shape * 2.2, p


def riser(length=0.9):
    n = int(length * SR); t = np.arange(n) / SR
    f = 200 + 1400 * (t / length) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) * 0.35 + lp(rng.standard_normal(n), 0.35) * 0.8) * (t / length) ** 2.5
    return s, length - 0.001


def thump(freq=55, length=0.7):
    n = int(length * SR); t = np.arange(n) / SR
    f = freq * (1 + 2.5 * np.exp(-t / 0.03))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, 0.002, 0.18) * 1.4, 0.004


def pop(freq=520):
    n = int(0.18 * SR); t = np.arange(n) / SR
    f = freq * (1 + 1.2 * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, 0.002, 0.05), 0.003


def boing():
    n = int(0.7 * SR); t = np.arange(n) / SR
    f = 260 + 90 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.25)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, 0.003, 0.22) * 0.9, 0.004


def slot(step):
    # rising-pitch "level up" blip: each rung of the climb is higher
    n = int(0.22 * SR); t = np.arange(n) / SR
    base = 330 * 2 ** (step * 3 / 12)
    s = np.sin(2 * np.pi * base * t) + 0.5 * np.sin(2 * np.pi * base * 2 * t)
    return s * env(n, 0.002, 0.06) * 0.7, 0.002


def chime(root=523.25):
    n = int(1.8 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * root * m * t) * a for m, a in [(1, 1), (1.5, .5), (2, .35), (3, .15)])
    return s * env(n, 0.004, 0.5) * 0.45, 0.004


def shimmer():
    n = int(1.2 * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([1568, 2093, 2637, 3136]))
    return s * env(n, 0.01, 0.35) * 0.12, 0.01


out = np.zeros(int(DUR * SR))


def place(t, gen, gain):
    s, pk = gen
    start = int(round((t - pk) * SR))
    if start < 0:
        s = s[-start:]; start = 0
    end = min(len(out), start + len(s))
    out[start:end] += s[: end - start] * gain


# --- cue sheet (mirrors the GSAP timeline) ---
for i, t in enumerate([0.34, 0.45, 0.55, 0.64, 0.76, 0.98]):
    place(t, click(1 + (i % 3) * 0.07), 0.35)                    # typing "Hello."
place(1.5, whoosh(0.5, 0.7, 0.3), 0.25)                         # hello lifts
for i in range(15):
    place(1.75 + i / 15 * 0.9, tick(1 + i * 0.03), 0.10)        # bezier vertices pop
place(2.6, whoosh(0.8, 0.8, 0.15), 0.45)                        # silhouette fill wipes up
place(3.05, thump(60), 0.55)                                    # first name slams
place(3.18, thump(52), 0.35)                                    # last name
place(4.15, whoosh(0.35, 0.7, 0.4), 0.18)                       # "I make pixels"
place(4.97, boing(), 0.55)                                      # "move." lands and squashes
place(4.97, pop(420), 0.4)
for i in range(12):
    place(5.2 + i * 0.038, click(1.2), 0.08)                    # stack type-on
place(6.95, riser(0.75), 0.4)                                   # wipe build
place(6.95, whoosh(0.9, 0.85, 0.2), 0.5)                        # diamond wipe
place(7.15, thump(45, 0.9), 0.7)                                # night world lands
for i, t in enumerate([7.15, 7.95, 8.65, 9.25, 9.8]):
    place(t + 0.05, slot(i), 0.4)                               # the climb
place(10.35, thump(40, 1.1), 0.85)                              # the top
place(10.4, slot(5), 0.45)
place(10.45, shimmer(), 1.0)                                    # sparks
place(11.95, whoosh(0.6, 0.7, 0.3), 0.4)                        # iris
place(12.2, pop(600), 0.4)                                      # avatar
place(13.25, chime(), 0.5)                                      # CTA

# gentle pulse bed under the climb (120 bpm), fading in
for k in range(10):
    t = 7.15 + k * 0.5
    if t < 10.3:
        place(t, thump(48, 0.35), 0.12 + 0.03 * k)

peak = np.max(np.abs(out)); out = out / peak * 0.89
# fade tail
fade = int(0.4 * SR); out[-fade:] *= np.linspace(1, 0, fade)
pcm = (np.stack([out, out], 1) * 32767).astype('<i2')
with wave.open('assets/sfx.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote assets/sfx.wav', len(out) / SR, 's')
