# Fitted joint positions for the scavenger mesh (grounded, meters, -Y forward), measured from cross-sections.
import math
from mathutils import Vector, Matrix
J = {
 'Hips': (0, 0.03, 1.03), 'Spine': (0, 0.03, 1.13), 'Spine1': (0, 0.03, 1.24), 'Spine2': (0, 0.03, 1.36),
 'Neck': (0, 0.008, 1.565), 'Head': (0, -0.025, 1.665), 'HeadTop_End': (0, -0.03, 1.89),
 'LeftShoulder': (0.05, 0.03, 1.505), 'LeftArm': (0.18, 0.02, 1.52), 'LeftForeArm': (0.45, 0.035, 1.486), 'LeftHand': (0.665, 0.025, 1.461),
 'RightShoulder': (-0.05, 0.03, 1.50), 'RightArm': (-0.18, 0.025, 1.51), 'RightForeArm': (-0.45, 0.045, 1.473), 'RightHand': (-0.665, 0.035, 1.455),
 'LeftUpLeg': (0.095, 0.035, 0.95), 'LeftLeg': (0.14, 0.10, 0.51), 'LeftFoot': (0.19, 0.095, 0.09), 'LeftToeBase': (0.215, -0.055, 0.025), 'LeftToe_End': (0.225, -0.15, 0.025),
 'RightUpLeg': (-0.095, 0.035, 0.95), 'RightLeg': (-0.18, 0.105, 0.51), 'RightFoot': (-0.235, 0.10, 0.09), 'RightToeBase': (-0.265, -0.05, 0.025), 'RightToe_End': (-0.28, -0.145, 0.025),
}
HAND_SCALE = 0.86
HAND_DROOP = math.radians(14)
THUMB_TIP = {'Left': (0.777, -0.043, 1.413), 'Right': (-0.78, -0.029, 1.397)}
