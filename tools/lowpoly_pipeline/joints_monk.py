# Fitted joint positions for the Black Robed Monk mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, -0.03, 1.00), 'Spine': (0, -0.03, 1.11), 'Spine1': (0, -0.035, 1.23), 'Spine2': (0, -0.04, 1.35),
 'Neck': (0, -0.05, 1.56), 'Head': (0, -0.07, 1.65), 'HeadTop_End': (0, -0.08, 1.90),
 'LeftShoulder': (0.05, -0.04, 1.52), 'LeftArm': (0.19, -0.06, 1.51), 'LeftForeArm': (0.43, -0.08, 1.49), 'LeftHand': (0.645, -0.10, 1.465),
 'RightShoulder': (-0.05, -0.04, 1.52), 'RightArm': (-0.19, -0.06, 1.51), 'RightForeArm': (-0.43, -0.08, 1.49), 'RightHand': (-0.645, -0.10, 1.465),
 'LeftUpLeg': (0.10, -0.03, 0.93), 'LeftLeg': (0.14, -0.04, 0.52), 'LeftFoot': (0.16, 0.0, 0.10), 'LeftToeBase': (0.165, -0.13, 0.03), 'LeftToe_End': (0.17, -0.22, 0.03),
 'RightUpLeg': (-0.10, -0.03, 0.93), 'RightLeg': (-0.14, -0.04, 0.52), 'RightFoot': (-0.16, 0.0, 0.10), 'RightToeBase': (-0.165, -0.13, 0.03), 'RightToe_End': (-0.17, -0.22, 0.03),
}
HAND_SCALE = 0.9
HAND_DROOP = math.radians(4)
THUMB_TIP = {'Left': (0.68, -0.18, 1.43), 'Right': (-0.685, -0.20, 1.42)}
