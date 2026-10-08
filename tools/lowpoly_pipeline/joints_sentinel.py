# Fitted joint positions for the Arctic Sentinel mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.01, 1.57), 'Head': (0, -0.005, 1.665), 'HeadTop_End': (0, -0.01, 1.90),
 'LeftShoulder': (0.05, 0.02, 1.51), 'LeftArm': (0.19, 0.04, 1.51), 'LeftForeArm': (0.43, 0.03, 1.465), 'LeftHand': (0.625, -0.035, 1.41),
 'RightShoulder': (-0.05, 0.02, 1.51), 'RightArm': (-0.19, 0.04, 1.51), 'RightForeArm': (-0.43, 0.03, 1.465), 'RightHand': (-0.625, -0.035, 1.41),
 'LeftUpLeg': (0.10, 0.01, 0.95), 'LeftLeg': (0.16, 0.04, 0.52), 'LeftFoot': (0.175, 0.055, 0.10), 'LeftToeBase': (0.185, -0.07, 0.03), 'LeftToe_End': (0.19, -0.155, 0.03),
 'RightUpLeg': (-0.10, 0.01, 0.95), 'RightLeg': (-0.16, 0.04, 0.52), 'RightFoot': (-0.175, 0.055, 0.10), 'RightToeBase': (-0.185, -0.07, 0.03), 'RightToe_End': (-0.19, -0.155, 0.03),
}
HAND_SCALE = 0.75
HAND_DROOP = math.radians(24)
THUMB_TIP = {'Left': (0.746, -0.135, 1.341), 'Right': (-0.746, -0.135, 1.341)}
