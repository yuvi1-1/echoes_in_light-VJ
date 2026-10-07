# Script CHOP callbacks for /vj_rig/dens_ctrl

TARGET = 0.10   # fraction of screen lit by the source pattern
def onSetupParameters(scriptOp): return
def onPulse(par): return
def onCook(scriptOp):
    S = scriptOp.storage
    if 'b' not in S: S['b'] = 0.6
    try: m = float(scriptOp.inputs[0][0][0])
    except Exception: m = TARGET
    # MELTADJ: sparser source in syrup scenes
    try:
        tgt = TARGET*(1-0.4*float(op('scenes')[int(op('scene_sel')['scene'])+1,'melt']))
    except Exception: tgt = TARGET
    S['b'] = min(0.97, max(0.25, S['b'] + 0.03*(m - tgt)))
    scriptOp.clear(); scriptOp.numSamples = 1
    scriptOp.appendChan('black')[0] = S['b']
    scriptOp.appendChan('density')[0] = m
