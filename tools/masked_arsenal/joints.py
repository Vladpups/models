# Hips sits at the Mixamo hips height (1.0425) and UpLeg at Mixamo's 0.975, so hips->sole matches the Mixamo
# skeleton and absolute hips curves keep the boots on the ground.
# Fitted joint positions for the Masked Arsenal mesh (1.80 m, grounded, meters, -Y forward), measured from
# cross-sections and grid renders of the Meshy model. Arms hang ~9 deg, legs splay ~8 deg in the source pose.
import math
J = {
 'Hips': (0.0, 0.01, 1.0425), 'Spine': (0.0, 0.015, 1.135), 'Spine1': (0.0, 0.02, 1.235), 'Spine2': (0.005, 0.02, 1.34),
 'Neck': (0.012, 0.005, 1.505), 'Head': (0.015, -0.005, 1.595), 'HeadTop_End': (0.018, -0.02, 1.80),
 'LeftShoulder': (0.05, 0.02, 1.465), 'LeftArm': (0.175, 0.02, 1.445), 'LeftForeArm': (0.42, 0.02, 1.39), 'LeftHand': (0.635, 0.022, 1.358),
 'RightShoulder': (-0.045, 0.02, 1.462), 'RightArm': (-0.165, 0.02, 1.44), 'RightForeArm': (-0.39, 0.02, 1.378), 'RightHand': (-0.600, 0.022, 1.360),
 'LeftUpLeg': (0.097, 0.01, 0.975), 'LeftLeg': (0.152, 0.055, 0.505), 'LeftFoot': (0.208, 0.05, 0.10), 'LeftToeBase': (0.225, -0.075, 0.03), 'LeftToe_End': (0.235, -0.17, 0.03),
 'RightUpLeg': (-0.097, 0.01, 0.975), 'RightLeg': (-0.152, 0.055, 0.505), 'RightFoot': (-0.205, 0.05, 0.10), 'RightToeBase': (-0.222, -0.075, 0.03), 'RightToe_End': (-0.232, -0.17, 0.03),
}
HAND_SCALE = 0.82
HAND_DROOP = math.radians(12)
THUMB_TIP = {'Left': (0.703, -0.042, 1.28), 'Right': (-0.671, -0.046, 1.283)}
# residual outward splay of the legs in the bind pose (deg); keeps the wide boots from touching in Mixamo walks
LEG_SPLAY = math.radians(2.0)
FINGERTIP = {'Left': (0.80, 0.034, 1.302), 'Right': (-0.767, 0.031, 1.303)}
