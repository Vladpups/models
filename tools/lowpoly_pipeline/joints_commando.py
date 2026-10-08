# Fitted joint positions for the Calendar Commando mesh (grounded, meters, -Y forward)
import math
J = {
 'Hips': (0, 0.0, 1.03), 'Spine': (0, 0.0, 1.13), 'Spine1': (0, 0.0, 1.24), 'Spine2': (0, 0.0, 1.36),
 'Neck': (0, 0.01, 1.56), 'Head': (0, -0.02, 1.67), 'HeadTop_End': (0, -0.03, 1.88),
 'LeftShoulder': (0.05, 0.03, 1.49), 'LeftArm': (0.21, 0.05, 1.49), 'LeftForeArm': (0.42, 0.03, 1.45), 'LeftHand': (0.58, -0.06, 1.41),
 'RightShoulder': (-0.05, 0.03, 1.49), 'RightArm': (-0.21, 0.05, 1.49), 'RightForeArm': (-0.42, 0.03, 1.45), 'RightHand': (-0.58, -0.06, 1.41),
 'LeftUpLeg': (0.11, 0.01, 0.95), 'LeftLeg': (0.17, 0.02, 0.50), 'LeftFoot': (0.21, 0.04, 0.11), 'LeftToeBase': (0.215, -0.09, 0.03), 'LeftToe_End': (0.215, -0.19, 0.03),
 'RightUpLeg': (-0.11, 0.01, 0.95), 'RightLeg': (-0.17, 0.02, 0.50), 'RightFoot': (-0.21, 0.04, 0.11), 'RightToeBase': (-0.215, -0.09, 0.03), 'RightToe_End': (-0.215, -0.19, 0.03),
}
HAND_SCALE = 0.85
HAND_DROOP = math.radians(20)
THUMB_TIP = {'Left': (0.719, -0.211, 1.351), 'Right': (-0.73, -0.211, 1.349)}
HAND_YAW = math.radians(25)
