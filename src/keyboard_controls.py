# Keyboard In DAT callbacks for /vj_rig/esc_key
# PERFORMANCE KEYS (TouchDesigner window must be focused)
#  R = start/stop recording      V = vertical reel / widescreen
#  1-6 = lock scene   0 = auto scenes   K = kaleidoscope on/off
#  B = blackout       ESC = close projector window
#  T = tap tempo (4+ taps locks the beat grid)   Y = back to automatic tempo
def onKey(dat, key, character, alt, lAlt, rAlt, ctrl, lCtrl, rCtrl, shift, lShift, rShift, state, time, cmd, lCmd, rCmd):
    if not state: return
    k = str(key).lower()
    c = op('controls').par
    if k in ('esc', 'escape'):
        op('projector_window').par.winclose.pulse()
    elif k == 'r':
        c.const10value = 0 if c.const10value.eval() > 0.5 else 1
    elif k == 'v':
        c.const11value = 0 if c.const11value.eval() > 0.5 else 1
    elif k == 'k':
        c.const7value = 0 if c.const7value.eval() > 0.5 else 1
    elif k == 'b':
        c.const9value = 0 if c.const9value.eval() > 0.5 else 1
    elif k == 't':
        # TAP TEMPO: tap on the beat 4+ times
        S = op('beat_brain').storage
        now = absTime.seconds
        taps = [x for x in S.get('taps', []) if now - x < 2.5 * (len(S.get('taps', [])) + 1)][-7:] + [now]
        if len(taps) >= 2 and now - taps[-2] > 2.0: taps = [now]
        S['taps'] = taps
        if len(taps) >= 4:
            iv = sorted(taps[i+1] - taps[i] for i in range(len(taps)-1))[(len(taps)-1)//2]
            S['bpm'] = 60.0 / iv; S['manual'] = True; S['conf'] = 1.0
        S['phase'] = 0.0
    elif k == 'y':
        op('beat_brain').storage['manual'] = False
    elif k == '0':
        c.const8value = -1
    elif k in ('1','2','3','4','5','6'):
        c.const8value = int(k) - 1
    return

def onShortcut(dat, shortcutName, time):
    return
