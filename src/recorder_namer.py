# CHOP Execute DAT /vj_rig/rec_namer
import datetime, os
# Each time "record" turns on, write to a new timestamped file in ~/Movies/VJ_clips
def onOffToOn(channel, sampleIndex, val, prev):
    folder = os.path.expanduser('~/Movies/VJ_clips')
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    kind = 'reel' if op('controls')['reel_vertical'] > 0.5 else 'wide'
    op('recorder').par.file = os.path.join(folder, 'vj_%s_%s.mp4' % (kind, stamp))
    return
def whileOn(channel, sampleIndex, val, prev): return
def onOnToOff(channel, sampleIndex, val, prev): return
def whileOff(channel, sampleIndex, val, prev): return
def onValueChange(channel, sampleIndex, val, prev): return
