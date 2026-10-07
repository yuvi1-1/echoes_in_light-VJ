# Script CHOP callbacks for /vj_rig/beat_brain

# ================= BEAT ENGINE v2 =================
# Per-band spectral-flux onsets with adaptive thresholds, tempo histogram,
# phase-locked beat grid (predicts beats even when detection misses),
# and song-section detection: normal / breakdown / build / drop.
import math, random
FPS = 60.0
BANDS = ('bass', 'mid', 'high')
REFRACT = {'bass': 10, 'mid': 9, 'high': 4}
K = {'bass': 1.4, 'mid': 1.7, 'high': 1.6}

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _init(S):
    S.update(f=0, peak={b: 0.002 for b in BANDS}, prev={b: 0.0 for b in BANDS},
             hist={b: [] for b in BANDS}, last={b: -999 for b in BANDS}, env={b: 0.0 for b in BANDS},
             sm={b: 0.0 for b in BANDS}, kicks=[], bpmhist={}, bpm=120.0, phase=0.0, count=0,
             pulse=0.0, conf=0.0, matched=False, quiet=0, eS=0.0, eL=0.0, eFloor=1.0,
             section=0, sec_t=0, tension=0.0, drop=0.0, scene=0, beats_in_scene=0, pre_bd_level=0.0)

def onCook(scriptOp):
    S = scriptOp.storage
    if 'f' not in S: _init(S)
    S['f'] += 1; f = S['f']
    raw = {}
    for i, b in enumerate(BANDS):
        try: raw[b] = float(scriptOp.inputs[i][0][0])
        except Exception: raw[b] = 0.0

    loud = (raw['bass'] + raw['mid']) > 0.0015
    S['quiet'] = 0 if loud else S['quiet'] + 1
    live = S['quiet'] < 120

    onset = {}
    norm = {}
    for b in BANDS:
        v = raw[b]
        S['peak'][b] = max(v, S['peak'][b] * 0.998, 0.0012)
        n = min(1.0, v / S['peak'][b])
        S['sm'][b] = max(n, S['sm'][b] * 0.85)
        norm[b] = S['sm'][b]
        flux = max(0.0, n - S['prev'][b]); S['prev'][b] = n * 0.7 + S['prev'][b] * 0.3
        h = S['hist'][b]; h.append(flux)
        if len(h) > 50: h.pop(0)
        mean = sum(h) / len(h); sd = math.sqrt(sum((x - mean) ** 2 for x in h) / len(h))
        thr = mean + K[b] * sd + 0.04
        hit = live and flux > thr and n > 0.35 and (f - S['last'][b]) > REFRACT[b]
        onset[b] = hit
        if hit: S['last'][b] = f; S['env'][b] = 1.0
        else: S['env'][b] *= (0.86 if b == 'bass' else 0.80 if b == 'mid' else 0.70)

    # ---- tempo histogram from kick onsets ----
    if onset['bass']:
        for k in S['kicks']:
            dt = (f - k) / FPS
            if 0.25 < dt < 2.1:
                bpm = 60.0 / dt
                while bpm < 85: bpm *= 2
                while bpm > 175: bpm /= 2
                key = int(round(bpm))
                S['bpmhist'][key] = S['bpmhist'].get(key, 0.0) + 1.0 / (1 + abs(dt - 0.5))
        S['kicks'] = [k for k in S['kicks'] if f - k < 2.2 * FPS] + [f]
        for key in list(S['bpmhist']):
            S['bpmhist'][key] *= 0.97
            if S['bpmhist'][key] < 0.01: del S['bpmhist'][key]
        if S['bpmhist'] and not S.get('manual'):  # MANUALTEMPO: tap tempo overrides
            best = max(S['bpmhist'], key=lambda k: S['bpmhist'][k] + 0.5 * (S['bpmhist'].get(k - 1, 0) + S['bpmhist'].get(k + 1, 0)))
            S['bpm'] = S['bpm'] * 0.8 + best * 0.2

    # ---- phase-locked beat grid ----
    S['phase'] += S['bpm'] / 60.0 / FPS
    beat_now = False
    if S['phase'] >= 1.0:
        S['phase'] -= 1.0; beat_now = True
        S['count'] += 1; S['beats_in_scene'] += 1
        S['conf'] = 1.0 if S.get('manual') else S['conf'] * 0.9 + (0.1 if S['matched'] else 0.0)
        S['matched'] = False
    if onset['bass']:
        # SYNCSTATS
        _e = S['phase'] if S['phase'] < 0.5 else S['phase'] - 1.0
        st = S.setdefault('sync', [])
        st.append(_e); del st[:-200]
        err = S['phase'] if S['phase'] < 0.5 else S['phase'] - 1.0   # distance to nearest beat
        if abs(err) < 0.25:
            S['phase'] -= err * 0.35; S['matched'] = True
    S['pulse'] = 1.0 if beat_now else S['pulse'] * 0.88

    # kick that visuals use: real detection, plus predicted beat when locked or silent
    grid_w = 0.6 * S['conf'] if live else 0.8
    kick = max(S['env']['bass'], S['pulse'] * grid_w)

    # ---- sections ----
    e = raw['bass'] * 0.6 + raw['mid'] * 0.4
    S['eS'] = S['eS'] * 0.95 + e * 0.05          # ~0.3 s
    S['eL'] = S['eL'] * 0.997 + e * 0.003        # ~5 s
    ratio = S['eS'] / max(1e-6, S['eL'])
    bass_ratio = S['sm']['bass']
    S['sec_t'] += 1
    sec = S['section']
    if sec == 0 and live and ratio < 0.45 and S['sec_t'] > 4 * FPS:
        S['section'] = 1; S['sec_t'] = 0; S['pre_bd_level'] = S['eL']
    elif sec in (1, 2):
        S['tension'] = min(1.0, S['sec_t'] / (16 * FPS))
        if sec == 1 and S['sec_t'] > 3 * FPS and norm['high'] + norm['mid'] > 1.1:
            S['section'] = 2                                       # build-up
        if S['eS'] > 0.8 * S['pre_bd_level'] and onset['bass'] and S['sec_t'] > 2 * FPS:
            S['section'] = 3; S['sec_t'] = 0; S['drop'] = 1.0; S['tension'] = 0.0
            _new_scene(S)
        if S['sec_t'] > 40 * FPS: S['section'] = 0; S['sec_t'] = 0; S['tension'] = 0.0
    elif sec == 3 and S['sec_t'] > 8 * FPS:
        S['section'] = 0; S['sec_t'] = 0
    S['drop'] *= 0.975
    if S['section'] in (0, 3) and beat_now and S['beats_in_scene'] >= 32 and S['count'] % 4 == 0:
        _new_scene(S)

    # ================= MOOD ENGINE + SONG CHANGE =================
    F = S.setdefault('feat', dict(kr=0.0, hr=0.0, bs=0.33, mood=0, cand=0, cand_n=0, song=0, newsong=0.0,
                                  song_f=0, was_loud=False, gap=0, ref=None))
    a = 1.0 / (5.0 * FPS)                                   # ~5 s averaging
    F['kr'] += a * ((FPS if onset['bass'] else 0.0) - F['kr'])
    F['hr'] += a * ((FPS if onset['high'] else 0.0) - F['hr'])
    tot = raw['bass'] + raw['mid'] + raw['high'] + 1e-6
    F['bs'] += a * (raw['bass'] / tot - F['bs'])
    # song change: silence gap of >1.2 s after music, then music again
    if loud:
        if F['gap'] > 1.2 * FPS and F['was_loud']:
            _song_change(S, F, f)
        F['gap'] = 0; F['was_loud'] = True
    else:
        F['gap'] += 1
    # song change: profile shift (kick rate / bass share move a lot vs. reference for 6 s)
    if F['ref'] is None and f - F['song_f'] > 10 * FPS: F['ref'] = (F['kr'], F['bs'])
    if F['ref'] is not None:
        dk = abs(F['kr'] - F['ref'][0]) / max(0.5, F['ref'][0]); db = abs(F['bs'] - F['ref'][1])
        F['shift'] = F.get('shift', 0) + 1 if (dk > 0.7 and db > 0.12) else 0
        if F['shift'] > 6 * FPS: _song_change(S, F, f)
    # mood classification (with hysteresis: 8 beats agreeing)
    if beat_now and f - F['song_f'] > 5 * FPS and live:
        bpm = S['bpm']
        halftime = 125 <= bpm <= 160 and F['kr'] < 1.6
        syrup = (F['bs'] > 0.5 and F['kr'] < 1.9) or (F['bs'] > 0.42 and F['hr'] > 2.5 and F['kr'] < 1.9) or (halftime and F['bs'] > 0.38)
        club = F['kr'] >= 1.6 and S['conf'] > 0.35 and not syrup
        chill = F['kr'] < 0.7 and F['hr'] < 2.0
        cand = 2 if syrup else 0 if club else 1 if chill else F['mood']
        if cand == F['cand']: F['cand_n'] += 1
        else: F['cand'] = cand; F['cand_n'] = 1
        if F['cand_n'] >= 8 and cand != F['mood']:
            F['mood'] = cand; _new_scene(S)
    F['newsong'] *= 0.96
    try: lock = int(op('controls')['mood_lock'])
    except Exception: lock = -1
    S['mood_now'] = lock if lock >= 0 else F['mood']

    out = dict(kick=kick, snare=S['env']['mid'], hat=S['env']['high'],
               bass=norm['bass'], mid=norm['mid'], high=norm['high'],
               energy=(norm['bass'] + norm['mid'] + norm['high']) / 3.0,
               bpm=S['bpm'], phase=S['phase'], pulse=S['pulse'], confidence=S['conf'],
               count=S['count'], beat=S['count'] % 4, bar=(S['count'] // 4) % 4,
               section=S['section'], breakdown=1.0 if S['section'] in (1, 2) else 0.0,
               tension=S['tension'] if S['section'] in (1, 2) else 0.0, drop=S['drop'],
               scene=S['scene'], live=1.0 if live else 0.0,
               onset_kick=1.0 if onset['bass'] else 0.0,
               mood=S.get('mood_now', 0), song=F['song'], newsong=F['newsong'],
               kick_rate=F['kr'], hat_rate=F['hr'], bass_share=F['bs'])
    scriptOp.clear(); scriptOp.numSamples = 1
    for k, v in out.items():
        scriptOp.appendChan(k)[0] = v
    return

def _song_change(S, F, f):
    F['song'] += 1; F['newsong'] = 1.0; F['song_f'] = f; F['ref'] = None; F['shift'] = 0
    F['kr'] *= 0.3; F['hr'] *= 0.3
    S['bpmhist'] = {}; S['kicks'] = []; S['conf'] = 0.0
    S['section'] = 0; S['sec_t'] = 0; S['tension'] = 0.0
    _new_scene(S)

def _new_scene(S):
    try:
        tbl = op('scenes'); n = tbl.numRows - 1
        mood = S.get('mood_now', S.get('feat', {}).get('mood', 0))
        pool = [r - 1 for r in range(1, tbl.numRows) if str(mood) in tbl[r, 'mood'].val.split()]
    except Exception:
        pool = []
    if not pool: pool = list(range(6))
    choices = [i for i in pool if i != S['scene']] or pool
    S['scene'] = random.choice(choices)
    S['beats_in_scene'] = 0
