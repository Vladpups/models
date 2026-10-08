# Fitted joint positions for the Civilian mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.01, 1.58), 'Head': (0, -0.01, 1.68), 'HeadTop_End': (0, -0.02, 1.89),
 'LeftShoulder': (0.05, 0.03, 1.51), 'LeftArm': (0.20, 0.06, 1.52), 'LeftForeArm': (0.45, 0.04, 1.485), 'LeftHand': (0.64, -0.03, 1.455),
 'RightShoulder': (-0.05, 0.03, 1.51), 'RightArm': (-0.20, 0.06, 1.52), 'RightForeArm': (-0.45, 0.04, 1.485), 'RightHand': (-0.64, -0.03, 1.455),
 'LeftUpLeg': (0.10, 0.02, 0.95), 'LeftLeg': (0.16, 0.03, 0.52), 'LeftFoot': (0.185, 0.06, 0.10), 'LeftToeBase': (0.195, -0.07, 0.03), 'LeftToe_End': (0.20, -0.17, 0.03),
 'RightUpLeg': (-0.10, 0.02, 0.95), 'RightLeg': (-0.16, 0.03, 0.52), 'RightFoot': (-0.185, 0.06, 0.10), 'RightToeBase': (-0.195, -0.07, 0.03), 'RightToe_End': (-0.20, -0.17, 0.03),
}
HAND_SCALE = 0.75
HAND_DROOP = math.radians(10)
THUMB_TIP = {'Left': (0.707, -0.133, 1.399), 'Right': (-0.711, -0.133, 1.402)}
