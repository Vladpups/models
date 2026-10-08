# Reference landmarks for the face morph (pixel coords in the reference sheet 1536x1024) and helper mappings.
# Front tile: MediaPipe 478 landmarks detected on crop (0,690)-(200,960). Side/back tiles: hand-picked points.
CROWN_3D = 1.985          # top of the hair mass on the Meshy head (grounded, scaled to 2.0 m)
CROWN_PX_FRONT = 727      # top of hair mass in the front tile (y px)
CROWN_PX_SIDE = 726
# side tile (character's left side, faces image-left): px -> (y, z) via chin/crown, y anchored on the ear centre
SIDE = {
    'nose_tip': (188.75, 847.5), 'subnasale': (200.0, 855.0), 'lip_up': (200.5, 865.0), 'lip_low': (203.0, 872.5),
    'chin_front': (207.5, 892.5), 'chin_bottom': (222.5, 900.0), 'ear_center': (300.5, 834.0),
}
# MediaPipe indices standing for the side-profile points
SIDE_MP = {'nose_tip': 1, 'subnasale': 2, 'lip_up': 0, 'lip_low': 17, 'chin_front': 199, 'chin_bottom': 152}
MIDLINE = [168, 6, 197, 195, 5, 4, 1, 2, 164, 0, 17, 18, 200, 199, 175, 152]
# crops of the four head tiles (x0, y0, x1, y1) in the sheet
TILES = {'front': (0, 690, 200, 1010), 'left': (186, 690, 360, 1010), 'back': (355, 690, 520, 1010), 'right': (515, 690, 700, 1010)}
# lower face oval (MediaPipe), used as silhouette constraints
OVAL = [454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234]
# ears: mesh points (x, y, z) on the Meshy head  ->  front-tile pixels (outer edge, top, bottom)
EARS = {
    'L': {'mesh': {'out': (0.1007, -0.019, 1.825), 'top': (0.095, -0.03, 1.856), 'bot': (0.086, -0.042, 1.782)},
          'px': {'out': (162.5, 835.0), 'top': (157.0, 817.0), 'bot': (150.0, 857.0)}},
    'R': {'mesh': {'out': (-0.1175, -0.029, 1.83), 'top': (-0.108, -0.03, 1.852), 'bot': (-0.098, -0.042, 1.782)},
          'px': {'out': (28.0, 835.0), 'top': (36.0, 817.0), 'bot': (43.0, 857.0)}},
}
