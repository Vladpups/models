# Fitted joint positions for the Stone Age mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.02, 1.58), 'Head': (0, 0.0, 1.68), 'HeadTop_End': (0, -0.02, 1.89),
 'LeftShoulder': (0.05, 0.03, 1.51), 'LeftArm': (0.21, 0.06, 1.51), 'LeftForeArm': (0.46, 0.07, 1.49), 'LeftHand': (0.66, 0.05, 1.47),
 'RightShoulder': (-0.05, 0.03, 1.51), 'RightArm': (-0.21, 0.06, 1.51), 'RightForeArm': (-0.46, 0.07, 1.49), 'RightHand': (-0.66, 0.05, 1.47),
 'LeftUpLeg': (0.10, 0.02, 0.95), 'LeftLeg': (0.16, -0.01, 0.53), 'LeftFoot': (0.22, 0.05, 0.08), 'LeftToeBase': (0.235, -0.07, 0.03), 'LeftToe_End': (0.24, -0.17, 0.03),
 'RightUpLeg': (-0.10, 0.02, 0.95), 'RightLeg': (-0.16, -0.01, 0.53), 'RightFoot': (-0.22, 0.05, 0.08), 'RightToeBase': (-0.235, -0.07, 0.03), 'RightToe_End': (-0.24, -0.17, 0.03),
}
HAND_SCALE = 0.86
HAND_DROOP = math.radians(8)
THUMB_TIP = {'Left': (0.77, -0.038, 1.436), 'Right': (-0.774, -0.038, 1.436)}
