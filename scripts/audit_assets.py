"""Check local gallery, asset paths, HTML and source safety. Requires Pillow."""
from pathlib import Path
from html.parser import HTMLParser
import json, re
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
class Page(HTMLParser):
    def __init__(self): super().__init__();self.ids=[];self.links=[];self.assets=[];self.csp=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag=='img':assert 'alt' in a,'Image missing alt'
        if 'src' in a:self.assets.append(a['src'])
        if tag=='link':self.assets.append(a['href'])
        if tag=='meta' and a.get('http-equiv')=='Content-Security-Policy':self.csp=a['content']
        assert not any(k.startswith('on') for k in a),'Inline event handler'
        assert 'style' not in a,'Inline style violates CSP'
p=Page();p.feed((ROOT/'index.html').read_text())
assert len(p.ids)==len(set(p.ids)),'Duplicate IDs'
for link in p.links:
    assert link.startswith('#'),f'Unexpected outbound placeholder: {link}'
    if link!='#':assert link[1:] in p.ids,link
for asset in p.assets:
    assert (ROOT/asset).is_file(),asset
assert "script-src 'self'" in p.csp and "object-src 'none'" in p.csp
for file in ['app.js','theme.js']:
    code=(ROOT/file).read_text()
    assert not re.search(r'\b(?:eval|fetch|XMLHttpRequest)\s*\(|\.innerHTML\s*=',code),file
photos=json.loads((ROOT/'assets/gallery.js').read_text().split(' = ',1)[1].rstrip(';\n'))
assert len(photos)==40
assert len({p['id'] for p in photos})==40
assert len({p['category'] for p in photos})==6
assert all(p['category']!='images' for p in photos)
for photo in photos:
    for key in ['small','large']:
        with Image.open(ROOT/photo[key]) as im:
            assert im.width==photo[key+'Width'],photo
            assert im.format=='WEBP'
            assert not im.getexif(),f'Unexpected EXIF in {photo[key]}'
for name in ['logo-simple.png','logo-detailed.png','logo-small.webp','logo-large.webp']:
    im=Image.open(ROOT/'assets/brand'/name)
    assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(0,255),name
assert all('Какое-то медиа' in (ROOT/f).read_text() for f in ['index.html','app.js','README.md'])
print('PASS: HTML IDs/anchors, assets, CSP, no inline handlers/HTML injection/network code, 40 photos in 6 categories, 80 valid WebPs without EXIF, transparent brand assets.')
