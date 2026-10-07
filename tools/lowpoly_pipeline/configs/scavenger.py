# Desert Scavenger (Meshy AI), original height, -Y forward, Z up. Values ported from the first version of the pipeline.
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import band
NAME = 'Scavenger'
FBX_NAME = 'Scavenger_LowPoly'
HEIGHT = None   # keep the source height
TRIS = 5000

DEC_BASE = 0.2
DEC_REG = {
 'head':     lambda x,y,z: band(z,1.62,2.0,0.05)*band(abs(x),0,0.2,0.03),
 'neck':     lambda x,y,z: band(z,1.50,1.62,0.03)*band(abs(x),0,0.14,0.03),
 'hands':    lambda x,y,z: band(abs(x),0.66,1.0,0.03)*band(z,1.3,1.6,0.02),
 'wrists':   lambda x,y,z: band(abs(x),0.60,0.68,0.02)*band(z,1.3,1.6,0.02),
 'elbows':   lambda x,y,z: band(abs(x),0.40,0.50,0.03)*band(z,1.3,1.6,0.02),
 'shoulders':lambda x,y,z: band(abs(x),0.15,0.28,0.03)*band(z,1.38,1.64,0.03),
 'knees':    lambda x,y,z: band(z,0.40,0.62,0.04)*band(abs(x),0.05,0.4,0.02),
 'shins':    lambda x,y,z: band(z,0.10,0.40,0.02)*band(abs(x),0.05,0.4,0.02),
 'feet':     lambda x,y,z: band(z,0.0,0.12,0.02),
 'hips':     lambda x,y,z: band(z,0.82,1.0,0.04)*band(abs(x),0,0.25,0.02),
}
DEC_BOOST = {'head':0.22,'neck':0.1,'hands':0.3,'wrists':0.2,'elbows':0.28,'shoulders':0.15,'knees':0.18,'shins':0.1,'feet':-0.2,'hips':0.05}

# fitted joints (grounded, meters), measured from cross-sections
J = {
 'Hips': (0, 0.03, 1.03), 'Spine': (0, 0.03, 1.13), 'Spine1': (0, 0.03, 1.24), 'Spine2': (0, 0.03, 1.36),
 'Neck': (0, 0.008, 1.565), 'Head': (0, -0.025, 1.665), 'HeadTop_End': (0, -0.03, 1.89),
 'LeftShoulder': (0.05, 0.03, 1.505), 'LeftArm': (0.18, 0.02, 1.52), 'LeftForeArm': (0.45, 0.035, 1.486), 'LeftHand': (0.665, 0.025, 1.461),
 'RightShoulder': (-0.05, 0.03, 1.50), 'RightArm': (-0.18, 0.025, 1.51), 'RightForeArm': (-0.45, 0.045, 1.473), 'RightHand': (-0.665, 0.035, 1.455),
 'LeftUpLeg': (0.095, 0.035, 0.95), 'LeftLeg': (0.14, 0.10, 0.51), 'LeftFoot': (0.19, 0.095, 0.09), 'LeftToeBase': (0.215, -0.055, 0.025), 'LeftToe_End': (0.225, -0.15, 0.025),
 'RightUpLeg': (-0.095, 0.035, 0.95), 'RightLeg': (-0.18, 0.105, 0.51), 'RightFoot': (-0.235, 0.10, 0.09), 'RightToeBase': (-0.265, -0.05, 0.025), 'RightToe_End': (-0.28, -0.145, 0.025),
}
# hand from the Mixamo template (no per-finger measurements)
HAND_SCALE = 0.86
HAND_DROOP = math.radians(14)
THUMB_TIP = {'Left': (0.777, -0.043, 1.413), 'Right': (-0.78, -0.029, 1.397)}

def uv_segments():
    J0 = {'hip': (0, 0.0, 0.95), 'chest': (0, 0.0, 1.30), 'neck': (0, 0.0, 1.55), 'headb': (0, -0.03, 1.62), 'headt': (0, -0.03, 1.86)}
    SEG = [('torso', J0['hip'], J0['chest']), ('torso', J0['chest'], J0['neck']), ('head', J0['headb'], J0['headt'])]
    for s, sx in (('L', 1), ('R', -1)):
        sh = (sx*0.19, 0.03, 1.50); el = (sx*0.45, 0.045, 1.475); wr = (sx*0.665, 0.03, 1.45); ft = (sx*0.85, 0.03, 1.41)
        hp = (sx*0.09, 0.02, 0.93)
        kn = (0.13 if sx > 0 else -0.15, 0.06, 0.50); an = (0.17 if sx > 0 else -0.21, 0.10, 0.09); toe = (0.2 if sx > 0 else -0.26, -0.12, 0.02)
        SEG += [('arm'+s, sh, el), ('arm'+s, el, wr), ('hand'+s, wr, ft), ('thigh'+s, hp, kn), ('shin'+s, kn, an), ('foot'+s, an, toe)]
    return SEG
def uv_rule(l, x, y, z):
    if l.startswith('arm') and abs(x) < 0.21: return 'torso'
    if l == 'torso' and abs(x) > 0.23 and z > 1.38: return 'armL' if x > 0 else 'armR'
    if l == 'head' and z < 1.58: return 'torso'
    if l.startswith('thigh') and z > 1.0: return 'torso'
    if l == 'torso' and z < 0.9: return 'thighL' if x > 0 else 'thighR'
    return l
UV_SPLITS = [('head', (0, -1, 0), (0, -0.03, 1.75), 'head_front', 'head_back'),
             ('torso', (0, -1, 0), (0, 0.0, 1.25), 'torso_front', 'torso_back')]
for _s, _sx in (('L', 1), ('R', -1)):
    UV_SPLITS += [('hand'+_s, (0, 0, 1), (_sx*0.75, 0.03, 1.43), 'hand'+_s+'_top', 'hand'+_s+'_bot'),
                  ('foot'+_s, (0, 0, 1), (0, 0, 0.035), 'foot'+_s+'_top', 'foot'+_s+'_bot')]
UV_CYL = []
for _s, _sx in (('L', 1), ('R', -1)):
    UV_CYL += [
     ('arm'+_s, lambda p: p[2] - 0.3 * p[1], lambda p: -1 if abs(p[0]) < 0.3 else (1 if abs(p[0]) > 0.55 else 0)),
     ('thigh'+_s, (lambda sx: lambda p: sx * p[0] + 0.3 * p[1])(_sx), lambda p: -1 if p[2] > 0.72 else (1 if p[2] < 0.62 else 0)),
     ('shin'+_s, (lambda sx: lambda p: sx * p[0] - 0.5 * p[1])(_sx), lambda p: -1 if p[2] > 0.38 else (1 if p[2] < 0.2 else 0)),
    ]
def uv_prio(c):
    x, y, z = c
    if z > 1.6 and abs(x) < 0.2: return 1.45
    if abs(x) > 0.64 and z > 1.3: return 1.2
    if z < 0.11: return 0.75
    if z > 1.3 and abs(x) < 0.25 and y < 0: return 1.1
    return 1.0

UV_PARAMS = {'method': 'MINIMUM_STRETCH', 'max_iter': 12, 'bad_frac': 0.2}
PACK_PARAMS = {'brute': True}
BAKE_PARAMS = {'res': 2048, 'ss': 2, 'samples': 1, 'ao_res': 2048, 'ao_samples': 64}
