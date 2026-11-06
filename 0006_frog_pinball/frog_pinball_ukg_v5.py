"""
frog_pinball_ukg_v5.py

Frog Pinball UKG — Variation 02 (Music Theory Pass v3.4 final).
New in v5 vs v4:
  - Bass: unified synth_frog_bass(preset=anchor|sub|bounce)
    anchor: 0 modulation; sub: AM 12%; bounce: bend -3%->+1.5%
    No vibrato, no FM in any preset
  - Anchor @ 0.0 every bar (verse/C1/C2), no SUB_KICK_OFFSET,
    freq=max(root*0.5, 45Hz), amp=0.7*sub
  - Core riff positions [0.75, 1.5, 2.5, 3.5] in ALL sections
  - C1: 3 sub + 1 upper-bass accent (root*2 @ 1.5)
  - C2: 2 sub + 1 upper-bass accent (root*m7 @ 1.5) +
        1 sub accent (root @ 3.5) ONLY on bars bar%4 in (1,3)
  - croak_hz fixed per section (no Cantor on croak)
  - Cantor only on dur time-warp
  - Collisions: 2 locked/cycle (C1 bar 4, C2 bar 8)

Output: /storage/emulated/0/Download/frog_pinball_ukg_v5.wav
"""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import os

np.random.seed(31)

# =============================================================================
# CONSTANTS
# =============================================================================
FS_HIGH = 48000
FS_OUT = 44100
REF_BPM = 132.0
SP_FS = 26040
SP_BITS = 12
SP_CUTOFF = 4200
SP_CUTOFF_8BIT = 7500
SWING = 0.55
NOISE_LEVEL = 0.20
NOISE_TARGET_RMS = 0.08
NOISE_PEAK_LIMIT = 0.7
REVERB_WET = 0.10

BELL_BIRTH_HZ = 440.0
BELL_ASSEMBLY_HZ = 660.0
BELL_DISSOLVE_HZ = 330.0

CANTOR_SCALE = 0.25
SUB_KICK_OFFSET = 0.035
BRIDGE_SUB_HZ = [55.00, 61.74, 65.41, 73.42, 82.41, 87.31]
DUB_FEEDBACK = 0.45
DUB_LPF_HZ = 3000.0

# v3.4: anchor floor 45 Hz (not 40) — avoids 2 Hz beat with kick tail 38
ANCHOR_FLOOR_HZ = 45.0
ANCHOR_AMP_RATIO = 0.7
CROAK_HZ = {'intro': 7.0, 'verse': 9.0, 'chorus1': 10.0,
            'chorus2': 11.0, 'bridge': 10.0, 'outro': 8.0}
AM_DEPTH = {'anchor': 0.0, 'sub': 0.12, 'bounce': 0.0,
            'intro_drone': 0.05, 'outro': 0.08}

CHORDS = [
    [261.63, 329.63, 392.00],   # Am7 upper
    [261.63, 349.23, 440.00],   # Dm7 upper
    [293.66, 349.23, 493.88],   # G7 upper
    [329.63, 392.00, 523.25],   # Cmaj upper
]
ROOTS = [110.00, 73.42, 98.00, 130.81]

# Core riff: positions shared by verse/C1/C2
CORE_RIFF_POS = [0.75, 1.5, 2.5, 3.5]
CORE_RIFF_DUR = [0.5, 0.5, 0.5, 0.5]
# Pitch multipliers per section
RIFF_PITCH = {
    'verse':   [1.0, 1.0,     1.4983, 1.0],   # root root 5th root
    'chorus1': [1.0, 2.0,     1.4983, 1.0],   # root root*2 5th root
    'chorus2': [1.0, 1.7818,  1.4983, 1.0],   # root root*m7 5th root (m7=1.7818)
}
# Preset per riff slot
RIFF_PRESET = {
    'verse':   ['sub', 'sub',    'sub', 'sub'],
    'chorus1': ['sub', 'bounce', 'sub', 'sub'],
    'chorus2': ['sub', 'bounce', 'sub', 'bounce'],  # bounce@3.5 conditional
}

MOTIF_A = [440.00, 523.25, 587.33, 659.26, 783.99]
MOTIF_A_RHYTHM = [0.075, 0.075, 0.100, 0.075, 0.125]
MOTIF_B = [783.99, 659.26, 523.25, 587.33, 440.00]
MOTIF_B_RHYTHM = [0.075, 0.075, 0.075, 0.100, 0.150]
MOTIF_A_FS = [440.00, 523.25, 587.33, 739.99, 659.26, 783.99]
MOTIF_A_FS_RHYTHM = [0.075, 0.075, 0.075, 0.075, 0.075, 0.125]
MOTIF_A_HIGH_FS = [880.00, 1046.50, 1174.66, 1479.98, 1318.51, 1567.98]
MOTIF_A_HIGH_FS_RHYTHM = [0.075, 0.075, 0.075, 0.075, 0.075, 0.125]
ECHO_NOTES = [440.00, 587.33, 783.99]

SECTIONS = [
    {'name': 'intro',   'bars': 4, 'bpm': 132.0,          'type': 'intro'},
    {'name': 'verse',   'bars': 8, 'bpm': 132.0,          'type': 'verse'},
    {'name': 'chorus1', 'bars': 8, 'bpm': 132.0,          'type': 'chorus'},
    {'name': 'bridge',  'bars': 6, 'bpm': (132.0, 144.0), 'type': 'bridge'},
    {'name': 'chorus2', 'bars': 8, 'bpm': 144.0,          'type': 'chorus_final'},
    {'name': 'outro',   'bars': 8, 'bpm': (144.0, 132.0), 'type': 'outro'},
]

STEMS_12BIT = ['kick', 'snare', 'hat', 'bass', 'chord', 'skank',
               'rave', 'vox', 'fx', 'pad']
STEMS_8BIT = ['quack', 'bumper', 'coin', 'tilt', 'motif']

# =============================================================================
# UTILITIES
# =============================================================================
def bar_dur(bpm):
    return 60.0 / bpm * 4.0

def place(buf, hit, t, fs=FS_HIGH):
    i = int(t * fs)
    if i < 0 or i >= len(buf):
        return
    end = min(i + len(hit), len(buf))
    buf[i:end] += hit[:end - i]

def hum(ms=12):
    return np.random.uniform(-ms / 1000.0, ms / 1000.0)

def _empty(n):
    d = {k: np.zeros(n) for k in STEMS_12BIT}
    d.update({k: np.zeros(n) for k in STEMS_8BIT})
    return d

def cp(x, y):
    return int((x + y) * (x + y + 1) // 2 + y)

def cantor_pitch_class(seed_x, seed_y):
    nn = cp(int(seed_x), int(seed_y))
    return (nn % 11) - 5

# =============================================================================
# NOISE ALPHABET
# =============================================================================
ALPHABET = {
    'F': lambda x: x**5 * 4.0,
    'E': lambda x: x**4 * np.sign(x) * 3.0,
    'D': lambda x: x**3 * 2.5,
    'C': lambda x: x**2 * np.sign(x) * 2.0,
    'G': lambda x: np.arctanh(np.clip(x, -0.999, 0.999)) * 0.40,
    'H': lambda x: np.tanh(x * 2) * 0.7,
    'A': lambda x: np.sqrt(np.abs(x)) * np.sign(x) * 0.4,
    'B': lambda x: x * 1.0,
    'I': lambda x: np.sin(x * np.pi) * 0.4,
    'J': lambda x: x * 0.5,
    'K': lambda x: x * 0.125,
    'L': lambda x: x**6 * 5.0,
    'M': lambda x: np.tanh(x * 4) * 1.2,
    'N': lambda x: x**2 * np.sign(x) * 3.0,
}
CHAR_GAIN = {'F': 1.15, 'E': 1.10, 'D': 1.10, 'C': 1.05, 'G': 0.60,
             'H': 0.85, 'A': 0.90, 'B': 0.50, 'I': 0.85, 'J': 0.60, 'K': 0.75,
             'L': 1.20, 'M': 0.95, 'N': 1.15}
TAME_CHARS = {'B', 'J', 'K', 'I', 'H', 'A'}

SECTION_NOISE_PATTERN = {
    'intro': "BHBA", 'verse': "CDCEFDEC", 'chorus': "FEDCFEDC",
    'bridge': "CDELMGLM", 'chorus_final': "FEGLLEGM", 'outro': "FEGCDBAK",
}
SECTION_NOISE_LEVEL = {
    'intro': 0.55, 'verse': 0.75, 'chorus': 0.90,
    'bridge': (0.75, 1.10), 'chorus_final': 1.00, 'outro': (0.90, 0.15),
}

# =============================================================================
# SINC-GRAIN ENGINE
# =============================================================================
_W = {}

def wmin(x1, x2):
    k = (round(float(x1), 12), round(float(x2), 12))
    if k not in _W:
        xs = np.linspace(min(x1, x2), max(x1, x2), 2001)
        kx = np.exp(xs * xs * 0.5)
        f1, f2 = np.exp(x1 * x1 * 0.5), np.exp(x2 * x2 * 0.5)
        s = (f2 - f1) / (x2 - x1)
        _W[k] = np.min(kx - (f1 + s * (xs - x1)))
    return _W[k]

def render_continuous(n_samples, f0, Q, x1f, x2f, x1a, x2a,
                      start_phase=0.0, phi=1.0, alpha=0.0, mod=None,
                      mod_freq=0.5, f_sweep=None):
    idx = np.arange(n_samples)
    if f_sweep is None:
        f = np.full(n_samples, float(f0))
    else:
        f_end, curve = f_sweep
        t_norm = idx / max(1, n_samples - 1)
        if curve == 'exp':
            f = f0 * (f_end / f0) ** t_norm
        else:
            f = f0 + (f_end - f0) * t_norm
    q = np.full(n_samples, float(Q))
    phase = start_phase + np.cumsum(f) / FS_HIGH
    if mod == 'beat':
        phase = phase + alpha * np.sin(2.0 * np.pi * idx / (phi * FS_HIGH))
    np_ = np.floor(phase).astype(int)
    pt = phase - np_
    ramp = 1.0 - 2.0 * np.abs(pt - 0.5)
    xt = x1f + (x2f - x1f) * ramp
    fx = np.exp(xt * xt * 0.5)
    f1, f2 = np.exp(x1f * x1f * 0.5), np.exp(x2f * x2f * 0.5)
    sl = (f2 - f1) / (x2f - x1f)
    W = fx - (f1 + sl * (xt - x1f))
    Wn = W / wmin(x1f, x2f)
    qw = q * Wn
    env = np.ones(n_samples)
    m = np.abs(qw) > 1e-12
    env[m] = np.sin(qw[m]) / qw[m]
    r = np.where(np_ % 2 == 0, pt, 1.0 - pt)
    xta = x1a + (x2a - x1a) * r
    fxa = np.exp(xta * xta * 0.5)
    f1a, f2a = np.exp(x1a * x1a * 0.5), np.exp(x2a * x2a * 0.5)
    sla = (f2a - f1a) / (x2a - x1a)
    Wa = fxa - (f1a + sla * (xta - x1a))
    Wna = Wa / wmin(x1a, x2a)
    sg = np.where(np_ % 2 == 0, 1.0, -1.0)
    return env * sg * Wna, phase[-1]

# =============================================================================
# DRUMS / HARMONIC / 8-BIT (unchanged from v4)
# =============================================================================
def synth_kick(dur=0.32, fs=FS_HIGH, amp=1.0):
    n = int(dur * fs); t = np.arange(n) / fs
    f = 180.0 * np.exp(-t * 35.0) + 60.0 * np.exp(-t * 10.0) + 38.0
    phase = 2 * np.pi * np.cumsum(f) / fs
    body = np.tanh(np.sin(phase) * 1.8)
    click = np.random.randn(n) * np.exp(-t * 220) * 0.08
    env = (1 - np.exp(-t * 280)) * np.exp(-t * 12)
    core = (body + click) * env
    nb = int(0.040 * fs); tb = np.arange(nb) / fs
    fb = 400.0 * (180.0 / 400.0) ** (tb / 0.040)
    phase_b = 2 * np.pi * np.cumsum(fb) / fs
    boing = np.sin(phase_b) * np.exp(-tb * 40) * 0.20
    boing_full = np.zeros(n); boing_full[:nb] = boing
    return amp * (core + boing_full)

def synth_snare(dur=0.20, fs=FS_HIGH, amp=0.55, tone=230.0):
    n = int(dur * fs); t = np.arange(n) / fs
    tonal = (np.sin(2 * np.pi * tone * t) + 0.5 * np.sin(2 * np.pi * tone * 1.6 * t)) * np.exp(-t * 22)
    noise = np.random.randn(n)
    b, a = signal.butter(2, [1800 / (fs / 2), 8000 / (fs / 2)], btype='band')
    noise = signal.lfilter(b, a, noise)
    env = (1 - np.exp(-t * 240)) * np.exp(-t * 20)
    return amp * (tonal * 0.30 + noise * 0.70) * env

def synth_hat_closed(dur=0.08, fs=FS_HIGH, amp=0.2):
    n = int(dur * fs); t = np.arange(n) / fs
    partials = [2800, 3800, 4900, 6100, 7500, 8900]
    x = np.zeros(n)
    for p in partials:
        x += np.sin(2 * np.pi * p * t + np.random.uniform(0, 2 * np.pi))
    noise = np.random.randn(n)
    b, a = signal.butter(2, [4500 / (fs / 2), 9500 / (fs / 2)], btype='band')
    noise = signal.lfilter(b, a, noise)
    x = 0.35 * x / len(partials) + 0.65 * noise
    env = (1 - np.exp(-t * 380)) * np.exp(-t * 50)
    return amp * x * env

def synth_hat_open(dur=0.28, fs=FS_HIGH, amp=0.22):
    n = int(dur * fs); t = np.arange(n) / fs
    partials = [2800, 3800, 4900, 6100, 7500, 8900]
    x = np.zeros(n)
    for p in partials:
        x += np.sin(2 * np.pi * p * t + np.random.uniform(0, 2 * np.pi))
    noise = np.random.randn(n)
    b, a = signal.butter(2, [4500 / (fs / 2), 9500 / (fs / 2)], btype='band')
    noise = signal.lfilter(b, a, noise)
    x = 0.35 * x / len(partials) + 0.65 * noise
    env = (1 - np.exp(-t * 380)) * np.exp(-t * 7)
    return amp * x * env

def synth_shaker(dur=0.055, fs=FS_HIGH, amp=0.15):
    n = int(dur * fs); t = np.arange(n) / fs
    noise = np.random.randn(n)
    b, a = signal.butter(2, [5500 / (fs / 2), 11000 / (fs / 2)], btype='band')
    noise = signal.lfilter(b, a, noise)
    env = (1 - np.exp(-t * 900)) * np.exp(-t * 75)
    return amp * noise * env

def synth_ride(dur=0.15, fs=FS_HIGH, amp=0.15):
    n = int(dur * fs); t = np.arange(n) / fs
    partials = [4500, 5600, 6700, 7800, 8900, 10000, 11200]
    x = np.zeros(n)
    for p in partials:
        x += np.sin(2 * np.pi * p * t + np.random.uniform(0, 2 * np.pi))
    noise = np.random.randn(n)
    b, a = signal.butter(2, [6000 / (fs / 2), 12000 / (fs / 2)], btype='band')
    noise = signal.lfilter(b, a, noise)
    x = 0.6 * x / len(partials) + 0.4 * noise
    env = (1 - np.exp(-t * 450)) * np.exp(-t * 22)
    return amp * x * env

def synth_warm_stab(freqs, dur=0.09, fs=FS_HIGH, amp=0.20, detune_cents=5.0):
    n = int(dur * fs); t = np.arange(n) / fs
    x = np.zeros(n)
    dr = 2 ** (detune_cents / 1200.0)
    def osc(freq):
        y = 0.4 * (2 * ((freq * t) % 1.0) - 1) + 0.3 * np.sign(np.sin(2 * np.pi * freq * t))
        y += 0.10 * np.sin(2 * np.pi * freq * 2 * t + 0.02)
        y += 0.05 * np.sin(2 * np.pi * freq * 3 * t + 0.04)
        return y
    for f in freqs:
        x += 0.5 * (osc(f / dr) + osc(f * dr))
    b, a = signal.butter(2, 2800 / (fs / 2), btype='low')
    x = signal.lfilter(b, a, x)
    env = (1 - np.exp(-t * 1200)) * np.exp(-t * 28)
    return amp * x * env / (len(freqs) * 1.2)

def synth_skank(freqs, dur=0.060, fs=FS_HIGH, amp=0.16, detune_cents=5.0):
    n = int(dur * fs); t = np.arange(n) / fs
    x = np.zeros(n); dr = 2 ** (detune_cents / 1200.0)
    for f in freqs:
        for d in [1.0 / dr, dr]:
            fd = f * d
            x += 0.4 * (2 * ((fd * t) % 1.0) - 1)
            x += 0.3 * np.sign(np.sin(2 * np.pi * fd * t))
            x += 0.10 * np.sin(2 * np.pi * fd * 2 * t)
            x += 0.05 * np.sin(2 * np.pi * fd * 3 * t)
    b, a = signal.butter(2, 1800 / (fs / 2), btype='low')
    x = signal.lfilter(b, a, x)
    env = (1 - np.exp(-t * 1500)) * np.exp(-t * 55)
    return amp * x * env / (len(freqs) * 2 * 1.2)

def synth_rave_stab(freqs, dur=0.06, fs=FS_HIGH, amp=0.2):
    n = int(dur * fs); t = np.arange(n) / fs
    x = np.zeros(n)
    for f in freqs:
        fd = f * 2.0 * (1 + np.random.uniform(-0.001, 0.001))
        x += 2 * ((fd * t) % 1.0) - 1
    b, a = signal.butter(2, 5000 / (fs / 2), btype='low')
    x = signal.lfilter(b, a, x)
    env = np.exp(-t * 80)
    return amp * x * env / len(freqs)

def synth_whisper(f0, dur=0.15, fs=FS_HIGH, amp=0.2, formant_type='default'):
    n = int(dur * fs); t = np.arange(n) / fs
    noise = np.random.randn(n); out = np.zeros(n)
    if formant_type == 'oh':
        formants = [(450, 100), (800, 150), (2300, 200)]
    elif formant_type == 'yeah':
        formants = [(600, 100), (1200, 120), (2500, 180)]
    elif formant_type == 'hey':
        formants = [(800, 120), (1500, 150), (2800, 200)]
    else:
        formants = [(320, 90), (580, 120), (1800, 200)]
    for f_c, bw in formants:
        b, a = signal.butter(2, [(f_c - bw) / (fs / 2), (f_c + bw) / (fs / 2)], btype='band')
        out += signal.lfilter(b, a, noise)
    if formant_type == 'yeah':
        pitch_env = 1 + 0.12 * t / dur
    elif formant_type == 'hey':
        pitch_env = 1 - 0.10 * t / dur
    else:
        pitch_env = 1.0
    tone = 0.04 * np.sin(2 * np.pi * np.cumsum(f0 * pitch_env) / fs) * (1 + 0.1 * np.sin(2 * np.pi * 6 * t))
    if formant_type == 'oh':
        env = (1 - np.exp(-t * 300)) * np.exp(-t * 6)
    else:
        env = (1 - np.exp(-t * 500)) * np.exp(-t * 12)
    return amp * (out * 0.85 + tone) * env

def synth_cantor_pad(start_bar, dur, fs=FS_HIGH, amp=0.14, base=110.0):
    n = int(dur * fs); t = np.arange(n) / fs
    pc = cantor_pitch_class(start_bar * 10, start_bar * 7 + 3)
    if pc == -3:
        pc = -4  # F# -> F
    freq = base * (2 ** (pc / 12.0))
    ph = 2 * np.pi * np.cumsum(np.full(n, freq)) / fs
    tri = (2.0 / np.pi) * np.arcsin(np.sin(ph))
    fm_mod = 0.5 * np.sin(2 * ph)
    y = np.sin(ph + fm_mod) + 0.3 * tri
    env = (1 - np.exp(-t * 20)) * np.exp(-t * 1.2)
    return amp * y * env

def synth_frog_croak_sub(freq=58.0, dur=1.2, fs=FS_HIGH, amp=0.40):
    n = int(dur * fs); t = np.arange(n) / fs
    fm = 15.0
    mod_index = 2.0 * np.exp(-t * 3.0)
    phase = 2 * np.pi * np.cumsum(np.full(n, freq)) / fs
    x = np.sin(phase + mod_index * np.sin(2 * np.pi * fm * t))
    b, a = signal.butter(2, 120 / (fs / 2), btype='low')
    x = signal.lfilter(b, a, x)
    env = (1 - np.exp(-t * 30)) * np.exp(-t * 1.2)
    return amp * x * env

def breath_env(dur, fs=FS_HIGH, rate_hz=0.10, depth=0.15):
    n = int(dur * fs); t = np.arange(n) / fs
    return 1.0 + depth * np.sin(2 * np.pi * rate_hz * t)

def synth_granular_texture(dur, fs=FS_HIGH, amp=0.06, grain_ms=30, density=20):
    n = int(dur * fs); out = np.zeros(n)
    gn = int(grain_ms * fs / 1000)
    if gn < 4:
        return out
    for _ in range(int(density * dur)):
        s = np.random.randint(0, max(1, n - gn))
        src = np.random.randn(gn)
        lo = np.random.uniform(700, 2200)
        hi = np.random.uniform(lo + 700, 7500)
        b, a = signal.butter(2, [lo / (fs / 2), hi / (fs / 2)], btype='band')
        g = signal.lfilter(b, a, src)
        env = np.sin(np.pi * np.arange(gn) / gn) ** 2
        g *= env * np.random.uniform(0.4, 1.0)
        out[s:s + gn] += g
    peak = np.max(np.abs(out)) + 1e-9
    return out / peak * amp

def synth_noise_rise(dur, fs=FS_HIGH, amp=0.18):
    n = int(dur * fs); noise = np.random.randn(n); out = np.zeros(n)
    for i, (l, h) in enumerate([(200, 600), (600, 1500), (1500, 3500), (3500, 8000)]):
        b, a = signal.butter(3, [l / (fs / 2), h / (fs / 2)], btype='band')
        band = signal.lfilter(b, a, noise)
        w = np.clip(1.0 - np.abs(np.linspace(0, 1, n) - (i + 0.5) / 4) * 2.2, 0, 1)
        out += band * w
    env = np.linspace(0, 1, n) ** 1.8
    return amp * out * env / 4

def synth_riser(dur, fs=FS_HIGH, amp=0.10, f_start=200, f_end=4000):
    n = int(dur * fs); t = np.arange(n) / fs
    f = f_start * (f_end / f_start) ** (t / dur)
    phase = 2 * np.pi * np.cumsum(f) / fs
    x = np.sin(phase) + 0.3 * np.sin(2 * phase)
    env = np.linspace(0, 1, n) ** 2.5
    return amp * x * env

def _short_env(s, fs, attack=0.003, release=0.010):
    n = len(s); na = max(2, int(attack * fs)); nr = max(2, int(release * fs))
    e = np.ones(n)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return s * e

def synth_quack(base=300.0, fs=FS_HIGH, amp=0.20):
    phi = np.sqrt(2.0); alpha = 3.5; Q = 12 * np.pi
    x1f, x2f = 0.5, -2.0; x1a, x2a = -0.1, 0.1
    n1 = int(0.100 * fs)
    sig1, _ = render_continuous(n1, base, Q, x1f, x2f, x1a, x2a,
                                start_phase=0.0, phi=phi, alpha=alpha, mod='beat',
                                f_sweep=(base * 0.6, 'exp'))
    sig1 = _short_env(sig1, fs, 0.003, 0.030)
    gap = np.zeros(int(0.020 * fs))
    n2 = int(0.070 * fs)
    sig2, _ = render_continuous(n2, base * 0.69, Q, x1f, x2f, x1a, x2a,
                                start_phase=0.0, phi=phi, alpha=alpha, mod='beat',
                                f_sweep=(base * 1.15, 'exp'))
    sig2 = _short_env(sig2, fs, 0.003, 0.025)
    out = np.concatenate([sig1, gap, sig2])
    peak = np.max(np.abs(out)) + 1e-9
    return amp * out / peak

def synth_bumper(fs=FS_HIGH, amp=0.20):
    dur = 0.030; n = int(dur * fs); t = np.arange(n) / fs
    f = 400.0 * (1200.0 / 400.0) ** (t / dur)
    phase = 2 * np.pi * np.cumsum(f) / fs
    tone = np.sin(phase)
    na = max(2, int(0.002 * fs)); nr = max(2, int(0.015 * fs))
    env = np.ones(n)
    env[:na] = np.linspace(0, 1, na)
    env[-nr:] *= np.linspace(1, 0, nr)
    tone = tone * env
    cn = int(0.010 * fs)
    click = np.random.randn(cn) * np.exp(-np.arange(cn) / (cn * 0.3)) * 0.3
    out = np.zeros(n); out[:len(tone)] += tone; out[:cn] += click
    return amp * out

def synth_coin(fs=FS_HIGH, amp=0.15):
    n1 = int(0.040 * fs); t1 = np.arange(n1) / fs
    sq1 = np.sign(np.sin(2 * np.pi * 987.77 * t1)) * np.exp(-t1 * 8)
    gap = np.zeros(int(0.020 * fs))
    n2 = int(0.040 * fs); t2 = np.arange(n2) / fs
    sq2 = np.sign(np.sin(2 * np.pi * 1318.51 * t2)) * np.exp(-t2 * 8)
    out = np.concatenate([sq1, gap, sq2])
    out = _short_env(out, fs, 0.002, 0.010)
    return amp * out

def synth_tilt(fs=FS_HIGH, amp=0.20):
    dur = 0.100; n = int(dur * fs); t = np.arange(n) / fs
    nn = int(0.050 * fs)
    noise = np.random.randn(nn) * np.exp(-np.arange(nn) / (nn * 0.3)) * 0.5
    tone = np.sin(2 * np.pi * 60.0 * t) * np.exp(-t * 8) * 0.7
    out = tone.copy(); out[:nn] += noise[:len(out)]
    return amp * out

def synth_pinball_motif_rhythm(notes_hz, rhythms_s, fs=FS_HIGH, amp=0.10):
    out = []
    for f, dur_s in zip(notes_hz, rhythms_s):
        n = int(dur_s * fs); t = np.arange(n) / fs
        sq = np.sign(np.sin(2 * np.pi * f * t))
        na = max(2, int(0.002 * fs)); nr = max(2, int(0.015 * fs))
        env = np.ones(n)
        env[:na] = np.linspace(0, 1, na)
        env[-nr:] *= np.linspace(1, 0, nr)
        out.append(amp * sq * env)
    return np.concatenate(out) if out else np.zeros(0)

def motif_rhythm_variant(base, variant):
    if variant == 0:
        return base
    if variant == 1:
        return [base[0] * 0.8] + base[1:]
    return base[:2] + [base[2] * 1.25] + base[3:]

# =============================================================================
# UNIFIED BASS (v3.4)
# =============================================================================
def synth_frog_bass(freq, dur, fs=FS_HIGH, amp=0.55, preset='sub',
                    croak_hz=10.0, am_depth=None):
    """
    Unified bass synth. Presets:
      'anchor': no modulation (the "floor")
      'sub':    AM croak at croak_hz, depth 12% default
      'bounce': pitch bend -3% -> +1.5%, no AM
    No vibrato, no FM in any preset. Body layer 35% (timbre, not modulation).

    am_depth: override preset default (used for intro drone 5%, outro 8%).
    """
    n = int(dur * fs); t = np.arange(n) / fs

    if preset == 'bounce':
        # Two-phase bend: -3% at t=0 -> +1.5% at 50ms -> 0 at 250ms
        rise = np.clip(t / 0.05, 0, 1)
        fall = np.clip((t - 0.05) / 0.20, 0, 1)
        delta = -0.03 * (1 - rise) + 0.015 * rise * (1 - fall)
        pitch_mult = 1.0 + delta
        am = np.ones(n)
    else:
        pitch_mult = np.ones(n)
        depth = AM_DEPTH['anchor'] if preset == 'anchor' else AM_DEPTH['sub']
        if am_depth is not None:
            depth = am_depth
        if depth == 0:
            am = np.ones(n)
        else:
            am = (1 - depth) + depth * (0.5 + 0.5 * np.sin(2 * np.pi * croak_hz * t))

    f = freq * pitch_mult
    phase = 2 * np.pi * np.cumsum(f) / fs

    sub_layer = np.sin(phase) * am
    b_lp, a_lp = signal.butter(2, 180 / (fs / 2), btype='low')
    sub_filt = signal.lfilter(b_lp, a_lp, sub_layer)

    env_body = (1 - np.exp(-t * 200)) * np.exp(-t * 8)
    body_raw = 0.35 * np.sin(2 * phase)
    b_hp, a_hp = signal.butter(2, 100 / (fs / 2), btype='high')
    body = signal.lfilter(b_hp, a_hp, body_raw) * env_body

    attack = 1 - np.exp(-t * 60)
    release_time = min(0.05, dur / 4)
    release = np.clip((dur - t) / release_time, 0, 1)
    sustain = 0.7 + 0.3 * np.exp(-t * 1.5)
    env = attack * sustain * release

    return amp * (sub_filt + body) * env

def schedule_bass_bar(stems, bar_t, root_base, bar, bar_in_section,
                      beat_dur, fs, section, is_locked=False):
    """
    Anchor @ 0.0 (no offset) + core riff [0.75, 1.5, 2.5, 3.5] (with offset).
    section: 'verse' | 'chorus1' | 'chorus2'
    is_locked: prepend 0.0 to riff (phrase boundary reset)
    """
    croak_hz = CROAK_HZ[section if section != 'chorus2' else 'chorus2']

    # Anchor: floor at 45 Hz (v3.4 C-1-residual fix)
    anchor_freq = max(root_base * 0.5, ANCHOR_FLOOR_HZ)
    anchor_amp = 0.55 * ANCHOR_AMP_RATIO
    anchor_dur = 2.0 * beat_dur
    place(stems['bass'],
          synth_frog_bass(anchor_freq, anchor_dur, fs, anchor_amp, 'anchor', croak_hz),
          bar_t)

    # Core riff
    positions = list(CORE_RIFF_POS)
    pitches = list(RIFF_PITCH[section])
    presets = list(RIFF_PRESET[section])
    durs = list(CORE_RIFF_DUR)

    # C-2-residual: bounce @ 3.5 in C2 only on bars bar%4 in (1, 3)
    if section == 'chorus2':
        if bar % 4 not in (1, 3):
            presets[3] = 'sub'  # downgrade bounce -> sub on colliding bars

    # Locked: prepend 0.0 (phrase reset, "locked with kick")
    if is_locked:
        positions = [0.0] + positions
        pitches = [1.0] + pitches
        presets = ['sub'] + presets
        durs = [0.4] + durs

    for k, (pos, pitch, preset, dur_b) in enumerate(zip(positions, pitches, presets, durs)):
        freq = root_base * pitch
        if preset == 'bounce':
            amp = 0.50 * 0.85  # bounce amp = 0.85 * sub (per §C.10)
        else:
            amp = 0.55 if k == 0 else 0.50
        # Cantor only on dur (v3.4)
        dur_mult = 0.8 + 0.2 * (cp(bar * 7, k * 11) % 3)
        dur = dur_b * beat_dur * dur_mult
        t = bar_t + pos * beat_dur + SUB_KICK_OFFSET
        place(stems['bass'],
              synth_frog_bass(freq, dur, fs, amp, preset, croak_hz),
              t)

# =============================================================================
# HRTF / BELL / REVERB / DUB / FILL
# =============================================================================
def hrtf_place(s, az, fs=FS_HIGH, dist=1.5):
    if len(s) == 0:
        return np.zeros((0, 2))
    itd = int(round(0.00065 * np.sin(np.radians(az)) * fs))
    lg = np.cos(np.radians((az + 90) / 2)) ** 2
    rg = np.sin(np.radians((az + 90) / 2)) ** 2
    dg = 1.0 / (1.0 + dist * 0.4)
    s = s.flatten()
    L, R = s * lg * dg, s * rg * dg
    if itd > 0:
        R = np.pad(R, (itd, 0))[:-itd]
    elif itd < 0:
        L = np.pad(L, (-itd, 0))[:itd]
    return np.column_stack((L, R))

def synth_bell(freq, dur=1.5, fs=FS_OUT, amp=0.12):
    n = int(dur * fs); t = np.arange(n) / fs
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 300))
    y = np.sin(2 * np.pi * freq * t) * env
    y += 0.50 * np.sin(2 * np.pi * freq * 1.5 * t) * env
    y += 0.20 * np.sin(2 * np.pi * freq * 2.5 * t) * env
    return y * amp

def make_ir(dur=2.0, decay=3.0, fs=FS_OUT):
    n = int(dur * fs); t = np.arange(n) / fs
    ir = np.random.randn(n) * np.exp(-t * decay)
    sos = signal.butter(2, 4000 / (fs / 2), btype='low', output='sos')
    ir = signal.sosfilt(sos, ir)
    ir[0] = 0.0
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-9)

def apply_reverb_stereo(x, ir, wet=REVERB_WET):
    out = np.zeros_like(x)
    for ch in range(2):
        w = signal.fftconvolve(x[:, ch], ir, mode='full')[:len(x)]
        out[:, ch] = (1 - wet) * x[:, ch] + wet * w
    return out

def dub_delay_signal(x, fs, delay_ms, feedback=DUB_FEEDBACK, lpf_hz=DUB_LPF_HZ):
    d = int(delay_ms / 1000.0 * fs)
    if d <= 0 or d >= len(x):
        return np.zeros_like(x)
    b, a = signal.butter(2, lpf_hz / (fs / 2), btype='low')
    xf = signal.lfilter(b, a, x)
    out = np.zeros_like(x)
    for i in range(1, 9):
        g = feedback ** (i - 1)
        if g < 0.005:
            break
        off = i * d
        if off >= len(x):
            break
        out[off:] += xf[:len(x) - off] * g
    return out

def apply_dub_mix(x, fs, delay_ms, wet=0.25):
    return x + wet * dub_delay_signal(x, fs, delay_ms)

def bridge_fill_positions(bar_num, n_hits):
    bar_len = bar_dur(REF_BPM)
    base_gap = bar_len / n_hits
    out = []
    for i in range(n_hits):
        amp = 0.10 + 0.30 * (i / max(1, n_hits - 1))
        dur = 0.08
        if i == n_hits - 1:
            amp = 0.45; dur = 0.12
        if i < n_hits - 4:
            t = i * base_gap
        else:
            idx = i - (n_hits - 4)
            t = (n_hits - 4) * base_gap + idx * base_gap * 1.5
        out.append((t, amp, dur))
    return out

# =============================================================================
# SECTION RENDERERS
# =============================================================================
def render_intro(n_bars):
    fs = FS_HIGH
    dur = n_bars * bar_dur(REF_BPM)
    n = int(dur * fs)
    stems = _empty(n)
    beat_dur = 60.0 / REF_BPM

    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        pad = synth_cantor_pad(bar, bar_dur(REF_BPM) * 1.2, fs, amp=0.18)
        place(stems['pad'], pad, bar_t)

    stems['fx'] += synth_granular_texture(dur, fs, amp=0.10, density=10)
    # Intro drone: sub preset with am_depth=5%, croak_hz=7
    drone = synth_frog_bass(55.0, dur, fs, 0.22, 'sub', CROAK_HZ['intro'],
                             am_depth=AM_DEPTH['intro_drone'])
    stems['bass'][:len(drone)] += drone

    third = beat_dur * 4 / 3
    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        for k in range(3):
            place(stems['hat'], synth_shaker(0.05, fs, 0.04), bar_t + k * third)

    for bar in range(n_bars):
        if np.random.rand() < 0.7:
            bar_t = bar * bar_dur(REF_BPM)
            place(stems['vox'], synth_whisper(160.0, 0.25, fs, 0.11, 'oh'),
                  bar_t + np.random.uniform(0.5, 3.5) * beat_dur)

    bar3_t = 2 * bar_dur(REF_BPM)
    place(stems['hat'], synth_hat_closed(0.3, fs, 0.08), bar3_t + 2.0 * beat_dur)
    place(stems['skank'], synth_skank(CHORDS[0], fs=fs, amp=0.09),
          bar3_t + 1.5 * beat_dur)

    bar4_t = 3 * bar_dur(REF_BPM)
    place(stems['hat'], synth_hat_closed(0.3, fs, 0.08), bar4_t + 2.0 * beat_dur)
    place(stems['quack'], synth_quack(base=300.0, fs=fs, amp=0.06),
          bar4_t + 2.5 * beat_dur)

    bar2_t = 1 * bar_dur(REF_BPM)
    place(stems['coin'], synth_coin(fs=fs, amp=0.04), bar2_t + 2.75 * beat_dur)

    stems['fx'] *= breath_env(dur, fs, 0.08, 0.18)
    stems['vox'] *= breath_env(dur, fs, 0.06, 0.20)
    stems['pad'] *= breath_env(dur, fs, 0.05, 0.22)
    return stems


def render_verse(n_bars):
    fs = FS_HIGH
    beat_dur = 60.0 / REF_BPM
    stems = _empty(int(n_bars * bar_dur(REF_BPM) * fs))

    kick_patterns = [
        [0.0, 1.75, 2.5, 3.75],
        [0.0, 1.75, 2.5],
        [0.0, 2.5, 3.75],
        [0.0, 1.75, 2.5, 3.75],
    ]
    ghost_positions = [0.75, 1.25, 1.75, 2.5, 3.25]

    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        ch = CHORDS[bar % 4]
        root_base = ROOTS[bar % 4]
        is_intro_verse = (bar < 4)

        pad = synth_cantor_pad(bar, bar_dur(REF_BPM), fs, amp=0.08)
        place(stems['pad'], pad, bar_t)

        for off in kick_patterns[bar % 4]:
            t = bar_t + off * beat_dur + hum(8)
            if off not in (0.0, 3.0):
                t += SWING * beat_dur * 0.25
            place(stems['kick'], synth_kick(0.32, fs, 0.88), t)

        for off in [1.0, 3.0]:
            place(stems['snare'], synth_snare(0.20, fs, 0.58),
                  bar_t + off * beat_dur + hum(15))

        ghost_p = 0.20 if (is_intro_verse and bar < 2) else (0.25 if is_intro_verse else 0.45)
        for off in ghost_positions:
            if np.random.rand() < ghost_p:
                place(stems['snare'], synth_snare(0.07, fs, 0.10),
                      bar_t + off * beat_dur + SWING * beat_dur * 0.25 + hum(15))

        if bar % 2 == 0:
            for i in range(8):
                t = bar_t + i * beat_dur * 0.5
                if i % 2 == 1:
                    t += SWING * beat_dur * 0.25
                amp = 0.16 if i in (0, 4) else 0.09
                place(stems['hat'], synth_hat_closed(0.08, fs, amp), t)
        else:
            for i in range(16):
                t = bar_t + i * beat_dur * 0.25
                if i % 2 == 1:
                    t += SWING * beat_dur * 0.25
                amp = 0.16 if i in (0, 8) else 0.09
                place(stems['hat'], synth_hat_closed(0.08, fs, amp), t)

        # Unified bass: anchor + core riff, no locked bars in verse
        schedule_bass_bar(stems, bar_t, root_base, bar, bar, beat_dur, fs,
                          'verse', is_locked=False)

        if not is_intro_verse:
            place(stems['chord'], synth_warm_stab(ch, 0.09, fs, 0.16),
                  bar_t + (0.5 + SWING * 0.25) * beat_dur)

        if bar == 5:
            place(stems['skank'], synth_skank(ch, fs=fs, amp=0.10),
                  bar_t + 1.5 * beat_dur)
            place(stems['skank'], synth_skank(ch, fs=fs, amp=0.10),
                  bar_t + 3.5 * beat_dur)

        if bar % 2 == 0:
            pc_w = cantor_pitch_class(bar * 3, bar * 5)
            w_pitch = 180.0 * (2 ** (pc_w / 12.0))
            place(stems['vox'], synth_whisper(w_pitch, 0.15, fs, 0.13, 'default'),
                  bar_t + 1.5 * beat_dur + hum(10))

        if bar in (1, 5):
            place(stems['coin'], synth_coin(fs=fs, amp=0.05),
                  bar_t + 2.75 * beat_dur)

    dur = n_bars * bar_dur(REF_BPM)
    stems['vox'] *= breath_env(dur, fs, 0.10, 0.12)
    stems['fx'] *= breath_env(dur, fs, 0.08, 0.15)
    return stems


def render_chorus(n_bars, final=False):
    fs = FS_HIGH
    beat_dur = 60.0 / REF_BPM
    stems = _empty(int(n_bars * bar_dur(REF_BPM) * fs))

    kp_regular = [
        [0.0, 1.25, 2.5, 3.75],
        [0.0, 1.25, 1.75, 2.5, 3.75],
        [0.0, 1.25, 2.5, 3.25, 3.75],
        [0.0, 1.25, 1.75, 2.5, 3.25, 3.75],
    ]
    kp_final = [
        [0.0, 1.25, 1.75, 2.5, 3.5, 3.75],
        [0.0, 1.25, 2.0, 2.5, 3.25, 3.75],
        [0.0, 1.25, 1.75, 2.5, 3.0, 3.5, 3.75],
        [0.0, 1.25, 1.75, 2.5, 3.0, 3.25, 3.75],
    ]
    kp = kp_final if final else kp_regular
    ghost_positions = [0.75, 1.25, 1.75, 2.5, 3.25]

    if final:
        skank_bars = [1, 3, 5, 7]; quack_bars = [1, 3, 5, 7]
        coin_bars = [0, 4]; bumper_bars = [2]; locked_bars = [3, 7]
        section_name = 'chorus2'
    else:
        skank_bars = [1, 5]; quack_bars = [0, 2, 4, 6]
        coin_bars = []; bumper_bars = []; locked_bars = [3]
        section_name = 'chorus1'

    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        ch = CHORDS[bar % 4]
        root_base = ROOTS[bar % 4]

        for off in kp[bar % 4]:
            t = bar_t + off * beat_dur + hum(6)
            if off not in (0.0, 3.0):
                t += SWING * beat_dur * 0.25
            place(stems['kick'], synth_kick(0.32, fs, 0.92), t)

        for off in [1.0, 3.0]:
            place(stems['snare'], synth_snare(0.20, fs, 0.65),
                  bar_t + off * beat_dur + hum(10))

        for off in ghost_positions:
            if np.random.rand() < 0.5:
                t = bar_t + off * beat_dur + SWING * beat_dur * 0.25 + hum(15)
                place(stems['snare'], synth_snare(0.08, fs, 0.13), t)

        if bar % 4 == 3:
            for k in range(6):
                t = bar_t + 3.5 * beat_dur + k * (beat_dur / 6)
                place(stems['snare'], synth_snare(0.06, fs, 0.35 - k * 0.04), t)

        if bar % 2 == 0:
            for i in range(16):
                t = bar_t + i * beat_dur * 0.25
                if i % 2 == 1:
                    t += SWING * beat_dur * 0.25
                if i in (6, 14):
                    place(stems['hat'], synth_hat_open(0.25, fs, 0.20), t)
                else:
                    amp = 0.20 if i % 4 == 0 else 0.10
                    place(stems['hat'], synth_hat_closed(0.08, fs, amp), t)
            for i in [3, 5, 7, 9]:
                t = bar_t + i * beat_dur * 0.5 + SWING * beat_dur * 0.25
                place(stems['hat'], synth_ride(0.12, fs, 0.10), t)
        else:
            triplet_pos = [0.0, 1/3, 2/3, 1.0, 4/3, 5/3,
                          2.0, 7/3, 8/3, 3.0, 10/3, 11/3]
            for pos in triplet_pos:
                t = bar_t + pos * beat_dur
                is_q = abs(pos - round(pos)) < 0.01
                amp = 0.18 if is_q else 0.07
                place(stems['hat'], synth_hat_closed(0.08, fs, amp), t)

        third = beat_dur * 4 / 3
        for k in range(3):
            place(stems['hat'], synth_shaker(0.05, fs, 0.05), bar_t + k * third)

        # Unified bass (v3.4): anchor + core riff, locked bars per section
        is_locked = bar in locked_bars
        schedule_bass_bar(stems, bar_t, root_base, bar, bar, beat_dur, fs,
                          section_name, is_locked=is_locked)

        place(stems['chord'], synth_warm_stab(ch, 0.09, fs, 0.20),
              bar_t + (0.5 + SWING * 0.25) * beat_dur)
        if not final and bar % 2 == 1:
            place(stems['chord'], synth_warm_stab(ch, 0.09, fs, 0.18),
                  bar_t + 2.0 * beat_dur)

        # Motif
        is_bar4 = (bar == 4)
        is_even = (bar % 2 == 0)
        if is_bar4:
            if final:
                notes = MOTIF_A_HIGH_FS; rhythm_base = MOTIF_A_HIGH_FS_RHYTHM; amp = 0.12
            else:
                notes = MOTIF_A_FS; rhythm_base = MOTIF_A_FS_RHYTHM; amp = 0.10
        elif is_even:
            notes = MOTIF_A; rhythm_base = MOTIF_A_RHYTHM
            amp = 0.11 if final else 0.09
        else:
            notes = MOTIF_B; rhythm_base = MOTIF_B_RHYTHM
            amp = 0.10 if final else 0.09
        rhythm = motif_rhythm_variant(rhythm_base, cp(bar, 7) % 3)
        motif = synth_pinball_motif_rhythm(notes, rhythm, fs, amp)
        place(stems['motif'], motif, bar_t + 2.0 * beat_dur)

        play_echo = (final and not is_even) or (not final and bar == 7)
        if play_echo:
            echo = synth_pinball_motif_rhythm(ECHO_NOTES, [0.055, 0.055, 0.080], fs, 0.08)
            place(stems['motif'], echo, bar_t + 3.75 * beat_dur)

        if final and bar % 2 == 0:
            place(stems['rave'], synth_rave_stab(ch, 0.06, fs, 0.18),
                  bar_t + 3.5 * beat_dur + SWING * beat_dur * 0.25)
        elif (not final) and bar % 4 == 3:
            place(stems['rave'], synth_rave_stab(ch, 0.06, fs, 0.18),
                  bar_t + 3.5 * beat_dur + SWING * beat_dur * 0.25)

        if bar in skank_bars:
            place(stems['skank'], synth_skank(ch, fs=fs, amp=0.14),
                  bar_t + 1.5 * beat_dur)
            place(stems['skank'], synth_skank(ch, fs=fs, amp=0.14),
                  bar_t + 3.5 * beat_dur)

        chop_type = ['oh', 'yeah', 'hey'][bar % 3]
        chop_pos = [1.5, 3.5, 2.5][bar % 3]
        pc_w = cantor_pitch_class(bar * 7, bar * 11)
        w_pitch = 180.0 * (2 ** (pc_w / 12.0))
        place(stems['vox'], synth_whisper(w_pitch, 0.20, fs, 0.15, chop_type),
              bar_t + chop_pos * beat_dur + hum(10))
        if bar % 2 == 1:
            place(stems['vox'], synth_whisper(220.0, 0.12, fs, 0.14, 'hey'),
                  bar_t + 3.5 * beat_dur + hum(10))

        if bar in quack_bars:
            pc_q = cantor_pitch_class(bar * 13, bar * 11)
            base = 300.0 * (2 ** (pc_q * CANTOR_SCALE / 12.0))
            place(stems['quack'], synth_quack(base=base, fs=fs, amp=0.16),
                  bar_t + 1.5 * beat_dur)

        if bar in coin_bars:
            place(stems['coin'], synth_coin(fs=fs, amp=0.10),
                  bar_t + 3.75 * beat_dur)

        if bar in bumper_bars:
            place(stems['bumper'], synth_bumper(fs=fs, amp=0.14),
                  bar_t + 1.5 * beat_dur)

        if final and bar == n_bars - 1:
            place(stems['bass'],
                  synth_frog_croak_sub(freq=62.0, dur=1.5, fs=fs, amp=0.42),
                  bar_t + 3.0 * beat_dur)

    dur = n_bars * bar_dur(REF_BPM)
    stems['vox'] *= breath_env(dur, fs, 0.11, 0.10)
    return stems


def render_bridge(n_bars):
    fs = FS_HIGH
    beat_dur = 60.0 / REF_BPM
    stems = _empty(int(n_bars * bar_dur(REF_BPM) * fs))
    dur = n_bars * bar_dur(REF_BPM)

    stems['fx'] += synth_noise_rise(dur, fs, amp=0.08)[:len(stems['fx'])]
    stems['fx'] += synth_riser(dur, fs, amp=0.10, f_start=150, f_end=3500)[:len(stems['fx'])]

    stutter_rates = [4, 8, 16, 32, 32, 8]
    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        rate = stutter_rates[min(bar, len(stutter_rates) - 1)]
        for k in range(rate):
            t = bar_t + k * (bar_dur(REF_BPM) / rate)
            amp = 0.85 * (0.5 + 0.5 * k / rate)
            place(stems['kick'], synth_kick(0.18, fs, amp), t)

    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        if bar <= 3:
            for k in range(16):
                t = bar_t + k * beat_dur * 0.25
                amp = 0.15 + 0.4 * ((bar * 16 + k) / (n_bars * 16))
                place(stems['snare'], synth_snare(0.08, fs, amp), t)
        elif bar == 4:
            for t_rel, amp, d in bridge_fill_positions(bar, 8):
                place(stems['snare'], synth_snare(d, fs, amp), bar_t + t_rel)
        else:
            for t_rel, amp, d in bridge_fill_positions(bar, 16):
                place(stems['snare'], synth_snare(d, fs, amp), bar_t + t_rel)

    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        if bar == n_bars - 1:
            place(stems['bass'],
                  synth_frog_croak_sub(freq=58.0, dur=1.2, fs=fs, amp=0.40),
                  bar_t)
        else:
            freq = BRIDGE_SUB_HZ[min(bar, len(BRIDGE_SUB_HZ) - 1)]
            place(stems['bass'],
                  synth_frog_bass(freq, 2.0 * beat_dur, fs, 0.48, 'sub',
                                   CROAK_HZ['bridge']),
                  bar_t + SUB_KICK_OFFSET)

    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        ch = CHORDS[bar % 2] if bar < n_bars - 1 else CHORDS[1]
        place(stems['chord'], synth_warm_stab(ch, 0.4, fs, 0.18), bar_t)
        pad = synth_cantor_pad(bar, bar_dur(REF_BPM), fs, amp=0.10 + 0.04 * bar)
        place(stems['pad'], pad, bar_t)

    for bar in [0, 3, 5]:
        if bar < n_bars:
            bar_t = bar * bar_dur(REF_BPM)
            place(stems['vox'], synth_whisper(140.0, 0.5, fs, 0.15, 'oh'),
                  bar_t + 1.5 * beat_dur)

    place(stems['tilt'], synth_tilt(fs=fs, amp=0.16),
          0 * bar_dur(REF_BPM) + 2.0 * beat_dur)
    place(stems['bumper'], synth_bumper(fs=fs, amp=0.16),
          1 * bar_dur(REF_BPM) + 2.0 * beat_dur)
    place(stems['quack'], synth_quack(base=320.0, fs=fs, amp=0.18),
          2 * bar_dur(REF_BPM) + 1.5 * beat_dur)
    place(stems['quack'], synth_quack(base=310.0, fs=fs, amp=0.16),
          2 * bar_dur(REF_BPM) + 3.0 * beat_dur)
    place(stems['quack'], synth_quack(base=300.0, fs=fs, amp=0.18),
          4 * bar_dur(REF_BPM) + 1.5 * beat_dur)
    place(stems['bumper'], synth_bumper(fs=fs, amp=0.14),
          4 * bar_dur(REF_BPM) + 2.5 * beat_dur)

    stems['pad'] *= breath_env(dur, fs, 0.12, 0.25)
    stems['vox'] *= breath_env(dur, fs, 0.09, 0.18)
    return stems


def render_outro(n_bars):
    fs = FS_HIGH
    beat_dur = 60.0 / REF_BPM
    stems = _empty(int(n_bars * bar_dur(REF_BPM) * fs))
    for bar in range(n_bars):
        bar_t = bar * bar_dur(REF_BPM)
        d = max(0.0, 1.0 - bar / max(1, n_bars))

        if bar < 2:
            place(stems['kick'], synth_kick(0.3, fs, 0.7 * d), bar_t)
            place(stems['kick'], synth_kick(0.3, fs, 0.5 * d), bar_t + 2.5 * beat_dur)
            place(stems['snare'], synth_snare(0.18, fs, 0.4 * d), bar_t + beat_dur)
        if bar < 3:
            for i in range(8):
                place(stems['hat'], synth_hat_closed(0.08, fs, 0.10 * d),
                      bar_t + i * beat_dur * 0.5)
        if bar < 4:
            for i in [1, 3, 5, 7]:
                place(stems['hat'], synth_ride(0.12, fs, 0.08 * d),
                      bar_t + i * beat_dur * 0.5)

        if bar < 4:
            place(stems['bass'],
                  synth_frog_bass(55.0, 1.8 * beat_dur, fs, 0.38 * d, 'sub',
                                   CROAK_HZ['outro'],
                                   am_depth=AM_DEPTH['outro']),
                  bar_t + SUB_KICK_OFFSET)
            place(stems['bass'],
                  synth_frog_bass(55.0, 1.0 * beat_dur, fs, 0.30 * d, 'sub',
                                   CROAK_HZ['outro'],
                                   am_depth=AM_DEPTH['outro']),
                  bar_t + 2.5 * beat_dur + SUB_KICK_OFFSET)

        if bar < 4:
            place(stems['chord'],
                  synth_warm_stab(CHORDS[bar % 4], 0.09, fs, 0.15 * d),
                  bar_t + 1.5 * beat_dur)

        if bar >= 2:
            pad = synth_cantor_pad(bar, bar_dur(REF_BPM), fs,
                                    amp=0.10 + 0.05 * (1 - d))
            place(stems['pad'], pad, bar_t)

        if bar >= 2:
            place(stems['fx'],
                  synth_granular_texture(bar_dur(REF_BPM), fs,
                                          amp=0.05 * (1 - d + 0.4), density=8),
                  bar_t)

        if bar < 4:
            place(stems['vox'], synth_whisper(160.0, 0.25, fs, 0.11 * d, 'oh'),
                  bar_t + 2.0 * beat_dur)

        if bar == n_bars - 1:
            place(stems['quack'], synth_quack(base=280.0, fs=fs, amp=0.14),
                  bar_t + 3.5 * beat_dur)

    dur = n_bars * bar_dur(REF_BPM)
    stems['pad'] *= breath_env(dur, fs, 0.06, 0.22)
    stems['vox'] *= breath_env(dur, fs, 0.07, 0.18)
    stems['fx'] *= breath_env(dur, fs, 0.05, 0.20)
    return stems

# =============================================================================
# TIME WARP, SP-1200, NOISE, EFFECTS, MASTER
# =============================================================================
def time_warp(x, bpm_target, n_bars, fs=FS_HIGH):
    n_in = len(x)
    if isinstance(bpm_target, tuple):
        bpm_s, bpm_e = bpm_target; avg = (bpm_s + bpm_e) / 2.0
    else:
        bpm_s = bpm_e = avg = bpm_target
    total_beats = n_bars * 4
    target_dur = total_beats * 60.0 / avg
    n_out = int(target_dur * fs)
    if abs(bpm_s - bpm_e) < 1e-6:
        return signal.resample(x, n_out)
    t = np.arange(n_out) / fs
    bpm_t = bpm_s + (bpm_e - bpm_s) * (t / target_dur)
    beats_cum = np.cumsum(bpm_t / 60.0 / fs)
    src_pos = np.clip(beats_cum * (60.0 / REF_BPM) * fs, 0, n_in - 1)
    return np.interp(src_pos, np.arange(n_in), x)

def solve_bpm_ramp_time(target_beats, bpm_s, bpm_e, total_beats):
    if abs(bpm_s - bpm_e) < 1e-6:
        return target_beats * 60.0 / bpm_s
    total_dur = total_beats * 60.0 / ((bpm_s + bpm_e) / 2.0)
    a = 0.5 * (bpm_e - bpm_s) / (60.0 * total_dur)
    b = bpm_s / 60.0; c = -target_beats
    disc = b * b - 4 * a * c
    if disc < 0:
        return target_beats * 60.0 / ((bpm_s + bpm_e) / 2.0)
    if abs(a) < 1e-12:
        return target_beats / b
    return (-b + np.sqrt(disc)) / (2 * a)

def pre_sp1200_eq(x, fs):
    sos_hp = signal.butter(2, 40 / (fs / 2), btype='high', output='sos')
    x = signal.sosfiltfilt(sos_hp, x)
    sos_lm = signal.butter(2, [150 / (fs / 2), 400 / (fs / 2)], btype='band', output='sos')
    low_mid = signal.sosfiltfilt(sos_lm, x) * 0.15
    sos_p = signal.butter(2, [2500 / (fs / 2), 4000 / (fs / 2)], btype='band', output='sos')
    presence = signal.sosfiltfilt(sos_p, x) * 0.20
    return x + low_mid + presence

def sp1200_chain(x, fs_in, target_fs, bits, out_cutoff):
    fs_mid = target_fs * 4
    x_mid = signal.resample(x, int(len(x) * fs_mid / fs_in))
    sos_in = signal.butter(2, 14000 / (fs_mid / 2), btype='low', output='sos')
    x_mid = signal.sosfiltfilt(sos_in, x_mid)
    x_low = x_mid[::4]
    levels = 2 ** (bits - 1)
    dither = (np.random.rand(len(x_low)) - 0.5) / levels * 1.8
    x_q = np.round((x_low + dither) * levels) / levels
    nyq = target_fs / 2
    sos_out = signal.butter(6, min(out_cutoff / nyq, 0.95), btype='low', output='sos')
    x_filt = signal.sosfiltfilt(sos_out, x_q)
    return signal.resample(x_filt, int(len(x_filt) * FS_OUT / target_fs))

def noise_for_section(duration, fs, pattern, level=1.0):
    n = int(duration * fs)
    n_slots = len(pattern); slot = n // n_slots
    raw = np.random.uniform(-1, 1, n)
    raw = np.convolve(raw, np.ones(11) / 11, mode='same')
    raw = np.clip(raw / (np.max(np.abs(raw)) + 1e-9), -1, 1)
    sos_pre = signal.butter(3, [180 / (fs / 2), 6500 / (fs / 2)], btype='band', output='sos')
    raw = signal.sosfiltfilt(sos_pre, raw)
    raw = np.clip(raw / (np.max(np.abs(raw)) + 1e-9), -1, 1)
    sos_tame = signal.butter(2, 4000 / (fs / 2), btype='low', output='sos')
    out = np.zeros(n)
    for i, c in enumerate(pattern):
        s = i * slot; e = s + slot if i < n_slots - 1 else n
        if c not in ALPHABET:
            continue
        shaped = ALPHABET[c](raw[s:e])
        if c in TAME_CHARS:
            shaped = signal.sosfiltfilt(sos_tame, shaped)
        rms = np.sqrt(np.mean(shaped ** 2))
        if rms > 1e-6:
            shaped = shaped * (NOISE_TARGET_RMS / rms)
        shaped = shaped * CHAR_GAIN.get(c, 1.0)
        peak = np.max(np.abs(shaped))
        if peak > NOISE_PEAK_LIMIT:
            shaped = shaped * (NOISE_PEAK_LIMIT / peak)
        fade = min(int(0.04 * fs), (e - s) // 8)
        if fade > 2:
            shaped[:fade] *= np.linspace(0, 1, fade)
            shaped[-fade:] *= np.linspace(1, 0, fade)
        out[s:e] = shaped
    if isinstance(level, tuple):
        out = out * np.linspace(level[0], level[1], n)
    else:
        out = out * level
    return out

def wow_flutter(x, fs, depth=0.0014):
    n = len(x); t = np.arange(n) / fs
    mod = 1.0 + depth * (np.sin(2 * np.pi * 0.3 * t) + 0.5 * np.sin(2 * np.pi * 5.0 * t))
    pos = np.cumsum(mod); pos = pos / pos[-1] * (n - 1)
    return np.interp(pos, np.arange(n), x)

def apply_stutter(x, fs, t_start, n_repeats=3, chunk_ms=60, decay=0.75):
    out = x.copy(); chunk = int(chunk_ms * fs / 1000); i = int(t_start * fs)
    if i + chunk * (n_repeats + 1) >= len(out):
        return out
    seg = out[i:i + chunk].copy()
    for r in range(1, n_repeats + 1):
        s = i + r * chunk
        out[s:s + chunk] = seg * (decay ** r)
    return out

def apply_silence(x, fs, t_start, dur_ms=80):
    out = x.copy(); i = int(t_start * fs); d = int(dur_ms * fs / 1000)
    if i + d <= len(out):
        out[i:i + d] = 0
    return out

def equal_power_concat(parts, xf):
    out = parts[0].copy()
    for p in parts[1:]:
        k = min(xf, len(out), len(p))
        if k > 2:
            t = np.linspace(0, 1, k)
            fo = np.cos(t * np.pi / 2); fi = np.sin(t * np.pi / 2)
            out[-k:] *= fo
            out = np.concatenate([out[:-k], out[-k:] + p[:k] * fi, p[k:]])
        else:
            out = np.concatenate([out, p])
    return out

def pad_2d(a, n):
    if len(a) >= n:
        return a[:n]
    out = np.zeros((n, a.shape[1]))
    out[:len(a)] = a
    return out

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("frog_pinball_ukg_v5 — Variation 02 (Music Theory Pass v3.4 final)")
    total_bars = sum(s['bars'] for s in SECTIONS)
    print(f"Sections: {len(SECTIONS)} / total bars: {total_bars}")

    print("1/8 Rendering sections (DNA=%d BPM)..." % int(REF_BPM))
    rendered = []
    for sec in SECTIONS:
        name, n_bars, bpm, typ = sec['name'], sec['bars'], sec['bpm'], sec['type']
        if typ == 'intro':          stems = render_intro(n_bars)
        elif typ == 'verse':        stems = render_verse(n_bars)
        elif typ == 'chorus':       stems = render_chorus(n_bars, final=False)
        elif typ == 'bridge':       stems = render_bridge(n_bars)
        elif typ == 'chorus_final': stems = render_chorus(n_bars, final=True)
        elif typ == 'outro':        stems = render_outro(n_bars)
        else: raise ValueError(typ)

        for k in list(stems.keys()):
            stems[k] = time_warp(stems[k], bpm, n_bars)

        if typ == 'chorus':
            delay_ms = 0.75 * 60.0 / 132.0 * 1000.0
            stems['vox'] = apply_dub_mix(stems['vox'], FS_HIGH, delay_ms, wet=0.25)
            stems['skank'] = apply_dub_mix(stems['skank'], FS_HIGH, delay_ms, wet=0.25)
        elif typ == 'chorus_final':
            delay_ms = 0.75 * 60.0 / 144.0 * 1000.0
            stems['vox'] = apply_dub_mix(stems['vox'], FS_HIGH, delay_ms, wet=0.30)
            stems['skank'] = apply_dub_mix(stems['skank'], FS_HIGH, delay_ms, wet=0.30)
        elif typ == 'outro':
            delay_ms = 0.75 * 60.0 / 138.0 * 1000.0
            stems['vox'] = apply_dub_mix(stems['vox'], FS_HIGH, delay_ms, wet=0.15)

        mono_12 = (stems['kick'] * 0.95 + stems['snare'] * 0.85
                   + stems['hat'] * 0.75 + stems['bass'] * 0.78)
        ch_hrtf = hrtf_place(stems['chord'] * 0.65 + stems['skank'] * 0.55
                              + stems['rave'] * 0.60, az=8, dist=2.0)
        vox_hrtf = hrtf_place(stems['vox'], az=-15, dist=1.6)
        pad_hrtf = hrtf_place(stems['pad'], az=0, dist=2.2)
        fx_hrtf = hrtf_place(stems['fx'], az=25, dist=2.5)
        n_s = len(mono_12)
        music_stereo = np.zeros((n_s, 2))
        music_stereo[:, 0] = mono_12 * 0.65
        music_stereo[:, 1] = mono_12 * 0.65
        music_stereo += ch_hrtf[:n_s] * 0.65
        music_stereo += vox_hrtf[:n_s] * 0.75
        music_stereo += pad_hrtf[:n_s] * 0.70
        music_stereo += fx_hrtf[:n_s] * 0.60

        rendered.append({
            'name': name, 'type': typ, 'bpm': bpm,
            'music': music_stereo,
            '8bit': {k: stems[k] for k in STEMS_8BIT},
            'len': n_s,
        })
        bpm_str = f"{bpm[0]:.0f}->{bpm[1]:.0f}" if isinstance(bpm, tuple) else f"{bpm:.0f}"
        print(f"    {name:12s} {n_bars:2d} bars @ {bpm_str:>7s} -> {n_s / FS_HIGH:.2f}s")

    print("2/8 Assembling music with section-aware crossfades...")
    xf_def = int(0.050 * FS_HIGH); xf_soft = int(0.150 * FS_HIGH); xf_hard = int(0.005 * FS_HIGH)

    music = rendered[0]['music'].copy()
    eight_bit = {k: rendered[0]['8bit'][k].copy() for k in STEMS_8BIT}
    section_starts_h = [0]
    for r in rendered[:-1]:
        section_starts_h.append(section_starts_h[-1] + r['len'])
    section_starts_h.append(section_starts_h[-1] + rendered[-1]['len'])

    for i in range(1, len(rendered)):
        nxt = rendered[i]['music']
        prev_t = rendered[i - 1]['type']; cur_t = rendered[i]['type']
        if prev_t == 'bridge' and cur_t == 'chorus_final':
            xf = xf_hard
        elif prev_t == 'verse' and cur_t == 'chorus':
            xf = xf_soft
        else:
            xf = xf_def
        if len(music) >= xf and len(nxt) >= xf:
            fo = np.linspace(1, 0, xf).reshape(-1, 1)
            fi = np.linspace(0, 1, xf).reshape(-1, 1)
            head = music[-xf:] * fo + nxt[:xf] * fi
            music = np.concatenate([music[:-xf], head, nxt[xf:]])
        else:
            music = np.concatenate([music, nxt])
        for k in STEMS_8BIT:
            nxt_b = rendered[i]['8bit'][k]; cur_b = eight_bit[k]
            if len(cur_b) >= xf and len(nxt_b) >= xf:
                fo = np.linspace(1, 0, xf); fi = np.linspace(0, 1, xf)
                head = cur_b[-xf:] * fo + nxt_b[:xf] * fi
                eight_bit[k] = np.concatenate([cur_b[:-xf], head, nxt_b[xf:]])
            else:
                eight_bit[k] = np.concatenate([cur_b, nxt_b])

    total_dur = len(music) / FS_HIGH
    print(f"    total (FS_HIGH): {total_dur:.2f}s")

    print("3/8 Character EQ + 12-bit SP-1200 (music, cutoff=%d)..." % SP_CUTOFF)
    mL = pre_sp1200_eq(music[:, 0], FS_HIGH)
    mR = pre_sp1200_eq(music[:, 1], FS_HIGH)
    mL_sp = sp1200_chain(mL, FS_HIGH, SP_FS, SP_BITS, SP_CUTOFF)
    mR_sp = sp1200_chain(mR, FS_HIGH, SP_FS, SP_BITS, SP_CUTOFF)
    target_len = int(total_dur * FS_OUT)

    def fit1d(a, n):
        return a[:n] if len(a) >= n else np.pad(a, (0, n - len(a)))

    mL_sp = fit1d(mL_sp, target_len)
    mR_sp = fit1d(mR_sp, target_len)

    print("4/8 Generating noise arc...")
    noise_L_parts, noise_R_parts = [], []
    for r in rendered:
        sec_dur = r['len'] / FS_HIGH
        pat = SECTION_NOISE_PATTERN[r['type']]; lvl = SECTION_NOISE_LEVEL[r['type']]
        noise_L_parts.append(noise_for_section(sec_dur, FS_HIGH, pat, lvl))
        noise_R_parts.append(noise_for_section(sec_dur, FS_HIGH, pat, lvl))
    nL_raw = equal_power_concat(noise_L_parts, int(0.15 * FS_HIGH))
    nR_raw = equal_power_concat(noise_R_parts, int(0.15 * FS_HIGH))
    nL_sp = sp1200_chain(nL_raw, FS_HIGH, SP_FS, SP_BITS, SP_CUTOFF)
    nR_sp = sp1200_chain(nR_raw, FS_HIGH, SP_FS, SP_BITS, SP_CUTOFF)
    nL_sp = fit1d(nL_sp, target_len); nR_sp = fit1d(nR_sp, target_len)

    print("5/8 Mixing music + noise...")
    final_L = mL_sp + NOISE_LEVEL * nL_sp
    final_R = mR_sp + NOISE_LEVEL * nR_sp

    print("6/8 8-bit arcade bus (SP-1200, cutoff=%d)..." % SP_CUTOFF_8BIT)
    for k in STEMS_8BIT:
        sig = eight_bit[k]
        sig_sp = sp1200_chain(sig, FS_HIGH, SP_FS, SP_BITS, SP_CUTOFF_8BIT)
        sig_sp = fit1d(sig_sp, target_len)
        if k == 'tilt':
            st = pad_2d(hrtf_place(sig_sp, az=-15, fs=FS_OUT, dist=2.0), target_len)
            final_L += st[:, 0] * 0.85; final_R += st[:, 1] * 0.85
        elif k == 'motif':
            st = pad_2d(hrtf_place(sig_sp, az=+15, fs=FS_OUT, dist=2.0), target_len)
            final_L += st[:, 0] * 0.85; final_R += st[:, 1] * 0.85
        else:
            final_L += sig_sp * 0.85; final_R += sig_sp * 0.85

    print("7/8 Placing pearl bells (birth / assembly / dissolution)...")
    scale_h_to_out = FS_OUT / FS_HIGH
    intro_start_t = section_starts_h[0] * scale_h_to_out / FS_OUT
    chorus2_start_t = section_starts_h[4] * scale_h_to_out / FS_OUT
    outro_start_t = section_starts_h[5] * scale_h_to_out / FS_OUT
    t_bar8_beat1 = solve_bpm_ramp_time(28, 144.0, 132.0, 32)
    assembly_time = chorus2_start_t + (1.0 + 0.15) * (60.0 / 144.0)
    dissolve_time = outro_start_t + t_bar8_beat1

    for tb, freq, amp in [
        (intro_start_t + 1.5, BELL_BIRTH_HZ, 0.10),
        (assembly_time, BELL_ASSEMBLY_HZ, 0.14),
        (dissolve_time, BELL_DISSOLVE_HZ, 0.10),
    ]:
        bell = synth_bell(freq, dur=1.5, fs=FS_OUT, amp=amp)
        bell_st = hrtf_place(bell, az=0, fs=FS_OUT, dist=1.0)
        p = int(tb * FS_OUT)
        if p < 0 or p >= target_len: continue
        end = min(p + len(bell_st), target_len)
        final_L[p:end] += bell_st[:end - p, 0]
        final_R[p:end] += bell_st[:end - p, 1]
        print(f"    bell {freq:>5.0f} Hz @ {tb:6.2f}s  amp={amp}")

    print("8/8 Reverb (wet=%.2f), glitch cuts, fades, normalize..." % REVERB_WET)
    ir = make_ir(dur=2.0, decay=3.0)
    stacked = np.stack([final_L, final_R], axis=-1)
    stacked = apply_reverb_stereo(stacked, ir, wet=REVERB_WET)
    final_L, final_R = stacked[:, 0], stacked[:, 1]

    boundary = [s * scale_h_to_out for s in section_starts_h]
    verse_end_s = boundary[2] / FS_OUT
    chorus1_end_s = boundary[3] / FS_OUT
    bridge_end_s = boundary[4] / FS_OUT
    chorus2_end_s = boundary[5] / FS_OUT

    final_L = apply_stutter(final_L, FS_OUT, verse_end_s - 0.45, n_repeats=2, chunk_ms=55)
    final_R = apply_stutter(final_R, FS_OUT, verse_end_s - 0.45, n_repeats=2, chunk_ms=55)
    final_L = apply_silence(final_L, FS_OUT, bridge_end_s - 0.09, dur_ms=90)
    final_R = apply_silence(final_R, FS_OUT, bridge_end_s - 0.09, dur_ms=90)
    final_L = apply_stutter(final_L, FS_OUT, chorus1_end_s - 0.30, n_repeats=2, chunk_ms=45)
    final_R = apply_stutter(final_R, FS_OUT, chorus1_end_s - 0.30, n_repeats=2, chunk_ms=45)
    final_L = apply_stutter(final_L, FS_OUT, chorus2_end_s - 0.30, n_repeats=3, chunk_ms=45)
    final_R = apply_stutter(final_R, FS_OUT, chorus2_end_s - 0.30, n_repeats=3, chunk_ms=45)

    final_L = wow_flutter(final_L, FS_OUT); final_R = wow_flutter(final_R, FS_OUT)

    f_in = int(0.05 * FS_OUT); f_out = int(2.5 * FS_OUT)
    final_L[:f_in] *= np.linspace(0, 1, f_in); final_R[:f_in] *= np.linspace(0, 1, f_in)
    final_L[-f_out:] *= np.linspace(1, 0, f_out); final_R[-f_out:] *= np.linspace(1, 0, f_out)

    rms = np.sqrt((np.mean(final_L ** 2) + np.mean(final_R ** 2)) / 2)
    if rms > 0:
        g = 10 ** (-16 / 20) / rms
        final_L *= g; final_R *= g
    peak = max(np.max(np.abs(final_L)), np.max(np.abs(final_R)))
    if peak > 10 ** (-1 / 20):
        g = 10 ** (-1 / 20) / peak
        final_L *= g; final_R *= g

    stereo = np.stack([final_L, final_R], axis=-1)
    out_int16 = np.int16(np.clip(stereo, -1, 1) * 32767)
    out_dir = '/storage/emulated/0/Download/'
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        out_dir = './'
    path = os.path.join(out_dir, 'frog_pinball_ukg_v5.wav')
    wavfile.write(path, FS_OUT, out_int16)
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"\nSaved: {path} ({size_mb:.1f} MB)")
    print(f"Total duration: {len(final_L) / FS_OUT:.2f}s")
    print("v3.4 final applied:")
    print("  - anchor floor 45 Hz (not 40) - no 2Hz beat with kick 38 Hz")
    print("  - anchor @ 0.0 every bar, no SUB_KICK_OFFSET, amp 0.7*sub")
    print("  - core riff [0.75,1.5,2.5,3.5] in ALL sections")
    print("  - C1: 3 sub + 1 upper-bass accent (root*2 @ 1.5)")
    print("  - C2: 2 sub + 1 upper (root*m7 @ 1.5) + 1 sub accent (root @ 3.5)")
    print("    sub accent only on bar%4 in (1,3) - 0 collisions with kick@3.5")
    print("  - croak_hz fixed: intro 7 / verse 9 / C1 10 / C2 11 / bridge 10 / outro 8")
    print("  - AM: anchor 0%, sub 12%, bounce 0%")
    print("  - no vibrato, no FM, no Cantor on croak_hz (only on dur)")

if __name__ == '__main__':
    main()
