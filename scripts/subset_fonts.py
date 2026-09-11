"""Subset local WOFF2 fonts to Latin, Cyrillic and the site's symbols.
Requires fonttools[woff]. Optionally pass a directory with original body.woff2 and display.woff2.
"""
from pathlib import Path
from fontTools import subset
import sys
root = Path(__file__).resolve().parent.parent
source = Path(sys.argv[1]) if len(sys.argv)>1 else root/'assets/fonts'
text = ''.join((root/p).read_text() for p in ['index.html','app.js','style.css'])
chars = set(map(ord,text)) | set(range(32,256)) | set(range(0x400,0x530))
for name in ['body','display']:
    path=source/f'{name}.woff2'
    before=path.stat().st_size
    options=subset.Options(); options.flavor='woff2';options.recalc_timestamp=False
    font=subset.load_font(str(path),options)
    worker=subset.Subsetter(options=options);worker.populate(unicodes=chars);worker.subset(font)
    target=root/f'assets/fonts/{name}.woff2'
    subset.save_font(font,str(target),options)
    print(f'{name}: {before:,} → {target.stat().st_size:,} bytes')
