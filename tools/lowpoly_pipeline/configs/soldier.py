# NATO soldier (Meshy AI), 1.83 m, -Y forward, Z up, feet on the ground
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import band
NAME = 'Soldier'
HEIGHT = 1.83
TRIS = 5000

# ---- decimation zones (grounded, scaled coords)
DEC_BASE = 0.2
DEC_REG = {
 'face':     lambda x,y,z: band(z,1.56,1.72,0.02)*band(abs(x),0,0.11,0.02)*band(y,-0.2,-0.02,0.02),
 'head':     lambda x,y,z: band(z,1.56,1.9,0.03)*band(abs(x),0,0.13,0.02),
 'neck':     lambda x,y,z: band(z,1.47,1.56,0.03)*band(abs(x),0,0.16,0.03),
 'hands':    lambda x,y,z: band(abs(x),0.70,1.0,0.02)*band(z,1.25,1.45,0.02),
 'wrists':   lambda x,y,z: band(abs(x),0.62,0.71,0.02)*band(z,1.3,1.45,0.02),
 'elbows':   lambda x,y,z: band(abs(x),0.42,0.52,0.03)*band(z,1.3,1.5,0.02),
 'shoulders':lambda x,y,z: band(abs(x),0.15,0.30,0.03)*band(z,1.3,1.56,0.03),
 'knees':    lambda x,y,z: band(z,0.42,0.62,0.04)*band(abs(x),0.05,0.4,0.02),
 'hips':     lambda x,y,z: band(z,0.78,0.98,0.04)*band(abs(x),0,0.22,0.02),
 'feet':     lambda x,y,z: band(z,0.0,0.12,0.02),
}
DEC_BOOST = {'face':0.22,'head':0.1,'neck':0.08,'hands':0.45,'wrists':0.2,'elbows':0.3,'shoulders':0.18,'knees':0.22,'hips':0.12,'feet':-0.08}

# ---- joints (Mixamo names without prefix), measured from cross-sections of the scaled mesh
J = {
 'Hips': (0, 0.02, 1.00), 'Spine': (0, 0.02, 1.09), 'Spine1': (0, 0.025, 1.19), 'Spine2': (0, 0.03, 1.30),
 'Neck': (0, 0.025, 1.50), 'Head': (0, -0.015, 1.605), 'HeadTop_End': (0, -0.035, 1.83),
 'LeftShoulder': (0.05, 0.03, 1.44), 'LeftArm': (0.19, 0.025, 1.42), 'LeftForeArm': (0.465, 0.025, 1.39), 'LeftHand': (0.70, 0.028, 1.375),
 'RightShoulder': (-0.05, 0.03, 1.44), 'RightArm': (-0.19, 0.025, 1.42), 'RightForeArm': (-0.465, 0.025, 1.39), 'RightHand': (-0.70, 0.028, 1.375),
 'LeftUpLeg': (0.095, 0.02, 0.92), 'LeftLeg': (0.155, 0.02, 0.52), 'LeftFoot': (0.22, 0.10, 0.095), 'LeftToeBase': (0.257, -0.03, 0.03), 'LeftToe_End': (0.282, -0.12, 0.03),
 'RightUpLeg': (-0.095, 0.02, 0.92), 'RightLeg': (-0.19, 0.01, 0.52), 'RightFoot': (-0.275, 0.08, 0.095), 'RightToeBase': (-0.327, -0.057, 0.03), 'RightToe_End': (-0.345, -0.145, 0.03),
}
# finger chains for the left hand: (knuckle, tip) measured on the mesh; right hand is mirrored in x
FINGERS = {
 'Index':  ((0.785, -0.014, 1.343), (0.859, -0.028, 1.317)),
 'Middle': ((0.787,  0.014, 1.348), (0.880,  0.019, 1.318)),
 'Ring':   ((0.783,  0.050, 1.354), (0.862,  0.059, 1.332)),
 'Pinky':  ((0.775,  0.076, 1.357), (0.835,  0.086, 1.345)),
 'Thumb':  ((0.725,  0.002, 1.352), (0.756, -0.067, 1.294)),
}
TIP_INSET = 0.012   # last joint (Finger4) sits this far inside the fingertip

# ---- UV segmentation
def uv_segments():
    g = lambda n: J[n]
    SEG = [('torso', g('Hips'), g('Spine2')), ('torso', g('Spine2'), g('Neck')), ('head', (0, -0.03, 1.60), (0, -0.03, 1.80))]
    for s, side in (('L', 'Left'), ('R', 'Right')):
        sx = 1 if s == 'L' else -1
        mid = FINGERS['Middle'][1]
        SEG += [('arm'+s, g(side+'Arm'), g(side+'ForeArm')), ('arm'+s, g(side+'ForeArm'), g(side+'Hand')),
                ('hand'+s, g(side+'Hand'), (sx*mid[0], mid[1], mid[2])),
                ('thigh'+s, g(side+'UpLeg'), g(side+'Leg')), ('shin'+s, g(side+'Leg'), g(side+'Foot')),
                ('foot'+s, g(side+'Foot'), g(side+'Toe_End'))]
    return SEG
def uv_rule(l, x, y, z):
    if l.startswith('arm') and abs(x) < 0.22: return 'torso'
    if l == 'torso' and abs(x) > 0.245 and z > 1.31: return 'armL' if x > 0 else 'armR'
    if l == 'head' and z < 1.55: return 'torso'
    if l.startswith('thigh') and z > 0.98: return 'torso'
    if l == 'torso' and z < 0.80: return 'thighL' if x > 0 else 'thighR'
    if l.startswith('hand') and abs(x) < 0.69: return 'armL' if x > 0 else 'armR'
    return l
UV_SPLITS = [('head', (0, -1, 0), (0, -0.03, 1.70), 'head_front', 'head_back'),
             ('torso', (0, -1, 0), (0, 0.0, 1.20), 'torso_front', 'torso_back')]
for _s, _sx in (('L', 1), ('R', -1)):
    UV_SPLITS += [('hand'+_s, (0, 0, 1), (_sx*0.78, 0.02, 1.35), 'hand'+_s+'_top', 'hand'+_s+'_bot'),
                  ('foot'+_s, (0, 0, 1), (0, 0, 0.04), 'foot'+_s+'_top', 'foot'+_s+'_bot')]
UV_CYL = []
for _s, _sx in (('L', 1), ('R', -1)):
    UV_CYL += [
     ('arm'+_s, lambda p: p[2] - 0.3 * p[1], lambda p: -1 if abs(p[0]) < 0.3 else (1 if abs(p[0]) > 0.6 else 0)),
     ('thigh'+_s, (lambda sx: lambda p: sx * p[0] + 0.3 * p[1])(_sx), lambda p: -1 if p[2] > 0.75 else (1 if p[2] < 0.6 else 0)),
     ('shin'+_s, (lambda sx: lambda p: sx * p[0] - 0.5 * p[1])(_sx), lambda p: -1 if p[2] > 0.4 else (1 if p[2] < 0.2 else 0)),
    ]
def uv_prio(c):   # texel density multiplier per island (by island centroid)
    x, y, z = c
    if z > 1.55 and abs(x) < 0.14: return 1.5            # head / face
    if abs(x) > 0.69 and z > 1.25: return 1.15           # hands
    if z < 0.12: return 0.7                              # boots
    if 1.15 < z < 1.55 and abs(x) < 0.25 and y < 0: return 1.15   # chest: NATO patch, radio
    if 0.9 < z < 1.55 and abs(x) < 0.25 and y > 0.1: return 0.9   # backpack
    return 1.0
UV_KEEP = ('head', 'hand', 'arm')

# ---- rig: parts that must stay rigid (whole piece follows one bone), (predicate, bone)
WEIGHT_OVERRIDES = [
 (lambda x,y,z: 0.150 < x < 0.200 and -0.130 < y < -0.070 and 1.30 < z < 1.62, 'mixamorig:Spine2'),   # radio antenna, left chest
]

# ---- stage parameters
UV_PARAMS = {'method': 'MINIMUM_STRETCH', 'iters': 100, 'max_iter': 14, 'bad_frac': 0.15, 'aniso': 1.6, 'aniso_frac': 0.12}
PACK_PARAMS = {'brute': True}
BAKE_PARAMS = {'res': 2048, 'ss': 2, 'samples': 1, 'ao_res': 2048, 'ao_samples': 64}
