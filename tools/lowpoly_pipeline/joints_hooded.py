# Fitted joint positions for the Hooded Figure mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.01, 1.59), 'Head': (0, -0.01, 1.68), 'HeadTop_End': (0, -0.02, 1.89),
 'LeftShoulder': (0.05, 0.04, 1.53), 'LeftArm': (0.20, 0.07, 1.53), 'LeftForeArm': (0.46, 0.07, 1.517), 'LeftHand': (0.70, 0.06, 1.505),
 'RightShoulder': (-0.05, 0.04, 1.53), 'RightArm': (-0.20, 0.07, 1.53), 'RightForeArm': (-0.46, 0.07, 1.517), 'RightHand': (-0.70, 0.06, 1.505),
 'LeftUpLeg': (0.10, 0.02, 0.95), 'LeftLeg': (0.16, -0.01, 0.53), 'LeftFoot': (0.22, 0.06, 0.10), 'LeftToeBase': (0.24, -0.07, 0.03), 'LeftToe_End': (0.25, -0.17, 0.03),
 'RightUpLeg': (-0.10, 0.02, 0.95), 'RightLeg': (-0.16, -0.01, 0.53), 'RightFoot': (-0.23, 0.06, 0.10), 'RightToeBase': (-0.25, -0.07, 0.03), 'RightToe_End': (-0.26, -0.17, 0.03),
}
HAND_SCALE = 0.7
HAND_DROOP = math.radians(8)
THUMB_TIP = {'Left': (0.77, -0.009, 1.472), 'Right': (-0.778, -0.005, 1.467)}
