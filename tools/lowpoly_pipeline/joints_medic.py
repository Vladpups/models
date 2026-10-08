# Fitted joint positions for the Combat Medic mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.01, 1.57), 'Head': (0, -0.01, 1.66), 'HeadTop_End': (0, -0.02, 1.89),
 'LeftShoulder': (0.05, 0.03, 1.51), 'LeftArm': (0.20, 0.05, 1.50), 'LeftForeArm': (0.46, 0.05, 1.47), 'LeftHand': (0.63, 0.03, 1.445),
 'RightShoulder': (-0.05, 0.03, 1.51), 'RightArm': (-0.20, 0.05, 1.50), 'RightForeArm': (-0.46, 0.05, 1.47), 'RightHand': (-0.63, 0.03, 1.445),
 'LeftUpLeg': (0.10, 0.02, 0.95), 'LeftLeg': (0.16, -0.01, 0.53), 'LeftFoot': (0.185, 0.06, 0.10), 'LeftToeBase': (0.195, -0.07, 0.03), 'LeftToe_End': (0.20, -0.17, 0.03),
 'RightUpLeg': (-0.10, 0.02, 0.95), 'RightLeg': (-0.16, -0.01, 0.53), 'RightFoot': (-0.185, 0.06, 0.10), 'RightToeBase': (-0.195, -0.07, 0.03), 'RightToe_End': (-0.20, -0.17, 0.03),
}
HAND_SCALE = 0.8
HAND_DROOP = math.radians(12)
THUMB_TIP = {'Left': (0.717, -0.057, 1.38), 'Right': (-0.721, -0.056, 1.38)}
