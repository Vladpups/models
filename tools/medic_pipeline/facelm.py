# detect 478 face landmarks; args: model img [crop x0 y0 x1 y1] [upscale]; prints JSON of pixel coords (in original image)
import sys, json, numpy as np, mediapipe as mp
from PIL import Image
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision
model, img = sys.argv[1], sys.argv[2]
crop = list(map(int, sys.argv[3:7])) if len(sys.argv) > 6 else None
up = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
im = Image.open(img)
if im.mode == 'RGBA':
    bg = Image.new('RGB', im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[3]); im = bg
im = im.convert('RGB')
x0 = y0 = 0
if crop: x0, y0 = crop[0], crop[1]; im = im.crop(crop)
if up != 1: im = im.resize((int(im.width * up), int(im.height * up)), Image.LANCZOS)
opts = vision.FaceLandmarkerOptions(base_options=mpp.BaseOptions(model_asset_path=model), num_faces=1, min_face_detection_confidence=0.1, min_face_presence_confidence=0.1)
det = vision.FaceLandmarker.create_from_options(opts)
res = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(im)))
if not res.face_landmarks: print('NOFACE'); sys.exit(1)
pts = [(x0 + l.x * im.width / up, y0 + l.y * im.height / up, l.z * im.width / up) for l in res.face_landmarks[0]]
json.dump(pts, open(sys.argv[-1] if sys.argv[-1].endswith('.json') else '/dev/stdout', 'w'))
print('OK', len(pts))
