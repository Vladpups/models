# Fitted joint positions for the Golden Guardian mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.38),
 'Neck': (0, 0.02, 1.61), 'Head': (0, 0.0, 1.70), 'HeadTop_End': (0, -0.02, 1.89),
 'LeftShoulder': (0.05, 0.04, 1.56), 'LeftArm': (0.21, 0.06, 1.545), 'LeftForeArm': (0.46, 0.07, 1.55), 'LeftHand': (0.68, 0.065, 1.555),
 'RightShoulder': (-0.05, 0.04, 1.56), 'RightArm': (-0.21, 0.06, 1.545), 'RightForeArm': (-0.46, 0.07, 1.55), 'RightHand': (-0.68, 0.065, 1.555),
 'LeftUpLeg': (0.10, 0.02, 0.95), 'LeftLeg': (0.16, -0.01, 0.53), 'LeftFoot': (0.22, 0.06, 0.10), 'LeftToeBase': (0.245, -0.07, 0.03), 'LeftToe_End': (0.255, -0.17, 0.03),
 'RightUpLeg': (-0.10, 0.02, 0.95), 'RightLeg': (-0.16, -0.01, 0.53), 'RightFoot': (-0.22, 0.06, 0.10), 'RightToeBase': (-0.25, -0.07, 0.03), 'RightToe_End': (-0.26, -0.17, 0.03),
}
HAND_SCALE = 0.7
HAND_DROOP = math.radians(0)
THUMB_TIP = {'Left': (0.732, 0.003, 1.54), 'Right': (-0.734, 0.004, 1.54)}
