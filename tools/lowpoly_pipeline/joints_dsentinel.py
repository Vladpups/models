# Fitted joint positions for the Desert Sentinel mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.01, 1.58), 'Head': (0, 0.0, 1.68), 'HeadTop_End': (0, -0.02, 1.89),
 'LeftShoulder': (0.05, 0.03, 1.51), 'LeftArm': (0.20, 0.05, 1.49), 'LeftForeArm': (0.42, 0.04, 1.445), 'LeftHand': (0.63, 0.0, 1.425),
 'RightShoulder': (-0.05, 0.03, 1.51), 'RightArm': (-0.20, 0.05, 1.49), 'RightForeArm': (-0.42, 0.04, 1.445), 'RightHand': (-0.63, 0.0, 1.425),
 'LeftUpLeg': (0.10, 0.02, 0.95), 'LeftLeg': (0.16, -0.01, 0.53), 'LeftFoot': (0.185, 0.06, 0.10), 'LeftToeBase': (0.195, -0.07, 0.03), 'LeftToe_End': (0.20, -0.17, 0.03),
 'RightUpLeg': (-0.10, 0.02, 0.95), 'RightLeg': (-0.16, -0.01, 0.53), 'RightFoot': (-0.185, 0.06, 0.10), 'RightToeBase': (-0.195, -0.07, 0.03), 'RightToe_End': (-0.20, -0.17, 0.03),
}
HAND_SCALE = 0.6
HAND_DROOP = math.radians(5)
THUMB_TIP = {'Left': (0.641, -0.074, 1.378), 'Right': (-0.646, -0.075, 1.378)}
