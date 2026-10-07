# Back gear from the reference (NATO pack panel, med pouch, bedroll). Model coords: meters, grounded, -Y forward.
# Rects in reference pixels (back view of the sheet) and the box/cylinder they map onto.
PANEL = dict(x=(-0.155, 0.18), z=(1.015, 1.45), y_in=0.03, y_out=0.215, y_out_top=0.185, bevel=0.035)
MEDKIT = dict(x=(-0.130, 0.155), z=(1.02, 1.185), y_in=0.17, y_out=0.262, y_out_top=0.25, bevel=0.022)
BEDROLL = dict(x=(-0.15, 0.19), zc=0.944, yc=0.20, r=0.07)
# region whose LP faces get deleted (hidden by the panel walls)
HIDE = dict(x=(-0.145, 0.17), z=(1.025, 1.44), y_min=0.045)
# reference sheet, back view: px = BACK_CX - x * PPM, py = BACK_SOLE - z * PPM
REF_BACK = dict(cx=1050.0, sole=690.0, ppm=375.0)
REF_RECTS = {  # (x0, y0, x1, y1) in reference px
    'panel': (1007.0, 156.0, 1100.0, 309.0),
    'medkit': (1011.0, 249.0, 1094.0, 309.0),
    'bedroll': (981.0, 311.0, 1101.0, 361.0),
}
