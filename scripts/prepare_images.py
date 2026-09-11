"""Regenerate local gallery assets: python3 scripts/prepare_images.py (Pillow required)."""
from pathlib import Path
from PIL import Image, ImageOps
import json
root = Path(__file__).resolve().parent.parent
out = root / 'assets' / 'photos'
out.mkdir(parents=True, exist_ok=True)
files = sorted(p for p in (root / 'public/images').rglob('*') if p.parent != root / 'public/images' and p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
photos = []
for i, path in enumerate(files):
    with Image.open(path) as source:
        img = ImageOps.exif_transpose(source).convert('RGB')
        w, h = img.size
        widths = {}
        for label, size, quality in [('small', 720, 78), ('large', 1600, 85)]:
            result = img.copy()
            result.thumbnail((size, size))
            widths[label] = result.width
            result.save(out / f'{i:02d}-{label}.webp', 'WEBP', quality=quality, method=6)
    photos.append(dict(id=i, category=path.parent.name, width=w, height=h, smallWidth=widths["small"], largeWidth=widths["large"], small=f'assets/photos/{i:02d}-small.webp', large=f'assets/photos/{i:02d}-large.webp'))
(root / 'assets/gallery.js').write_text('window.galleryPhotos = ' + json.dumps(photos, ensure_ascii=False) + ';\n')
print(f'Prepared {len(photos)} photos')
