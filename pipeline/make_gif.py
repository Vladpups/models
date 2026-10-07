import sys, glob
from PIL import Image
out=sys.argv[1]; files=sorted(glob.glob(sys.argv[2]))
ims=[Image.open(f).convert('RGB') for f in files]
ims=[i.quantize(colors=200, method=Image.Quantize.MEDIANCUT) for i in ims]
ims[0].save(out, save_all=True, append_images=ims[1:], duration=33, loop=0, optimize=True)
print('gif frames',len(ims))
