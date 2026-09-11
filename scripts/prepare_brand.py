"""Remove neutral checkerboard from supplied RGB logos without changing originals.
Usage: python3 scripts/prepare_brand.py (Pillow required).
The middle gray background is separated from navy, orange and opaque white artwork.
"""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFilter
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/brand'
OUT.mkdir(parents=True, exist_ok=True)

def extract(name):
    original = Image.open(ROOT / 'public/images' / name).convert('RGB')
    output = Image.new('RGBA', original.size)
    pixels = []
    for r, g, b in original.get_flattened_data():
        if r < 65 and g < 105 and b < 145 and b > r + 12:
            pixels.append((2, 37, 57, 255))
        elif r > 175 and 40 < g < 185 and b < 95:
            pixels.append((255, 112, 0, 255))
        elif r > 220 and g > 215 and b > 200:
            pixels.append((255, 251, 243, 255))
        else:
            pixels.append((0, 0, 0, 0))
    # Remove isolated remnants in the checkerboard; retain detached spray rays.
    from collections import deque
    width, height = original.size
    unseen = bytearray(1 if pixel[3] else 0 for pixel in pixels)
    for origin in range(len(pixels)):
        if not unseen[origin]: continue
        component = [origin]; pending = deque([origin]); unseen[origin] = 0
        while pending:
            pos = pending.popleft(); x = pos % width
            neighbours = []
            if x: neighbours.append(pos-1)
            if x < width-1: neighbours.append(pos+1)
            if pos >= width: neighbours.append(pos-width)
            if pos < width*(height-1): neighbours.append(pos+width)
            for nxt in neighbours:
                if unseen[nxt]: unseen[nxt]=0; pending.append(nxt); component.append(nxt)
        if len(component)<100:
            for pos in component: pixels[pos]=(0,0,0,0)
    output.putdata(pixels)
    alpha = output.getchannel("A").filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    # Fill pinholes with adjacent ink before downsampling to smooth the silhouette.
    output.putalpha(alpha)
    bounds = output.getbbox()
    output = output.crop(bounds)
    side = max(output.size) + 48
    canvas = Image.new('RGBA', (side, side))
    canvas.alpha_composite(output, ((side-output.width)//2, (side-output.height)//2))
    return canvas

simple, detailed = extract('logo.png'), extract('logo1.png')
for name, im in [('logo-simple', simple), ('logo-detailed', detailed)]:
    im.save(OUT / f'{name}.png', optimize=True)
for name, source, side in [('logo-small', simple, 128), ('logo-large', detailed, 480)]:
    source.resize((side, side), Image.Resampling.LANCZOS).save(OUT / f'{name}.webp', quality=90, method=6)
# Opaque cream discs keep the original navy logo readable in dark browser chrome.
for name, side in [('favicon.png',64), ('apple-touch-icon.png',180)]:
    im = Image.new('RGBA',(side,side))
    ImageDraw.Draw(im).rounded_rectangle((0,0,side-1,side-1),radius=side*.22,fill='#f6f3e9')
    art=simple.resize((side-4,side-4),Image.Resampling.LANCZOS)
    im.alpha_composite(art,(2,2)); im.save(OUT/name,optimize=True)
print('Prepared two cleaned logos, WebP display sizes, favicon and touch icon.')
