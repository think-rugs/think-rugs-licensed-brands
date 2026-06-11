"""
export_assets.py

One time (or re runnable) asset export from the legacy single file project caches
into this Next.js project:
- img_cache.json     -> public/images/products/{CODE}_cut.jpg / {CODE}_life.jpg
- logos.json         -> public/images/logos/{key}.png (brand marks),
                        recoloured rail variants {key}_rail.png,
                        and the trimmed Think Rugs cover logo thinkrugs_cover.jpg
- xlsx_payloads.json -> public/downloads/{fname}
Also writes data/img_manifest.json (code -> which shots exist) used at build time.

Usage: python3 scripts/export_assets.py /path/to/legacy/project
"""
import json, base64, io, os, sys, re
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '../work/project'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

img_cache = json.load(open(f'{SRC}/img_cache.json'))
logos = json.load(open(f'{SRC}/logos.json'))
xlsx = json.load(open(f'{SRC}/xlsx_payloads.json'))
themes = json.load(open(f'{SRC}/themes.json'))

def decode(uri):
    return base64.b64decode(uri.split(',', 1)[1])

manifest = {}
for code, shots in img_cache.items():
    entry = {}
    for key in ('cut', 'life'):
        if shots.get(key):
            open(f'{ROOT}/public/images/products/{code}_{key}.jpg', 'wb').write(decode(shots[key]))
            entry[key] = True
    manifest[code] = entry
json.dump(manifest, open(f'{ROOT}/data/img_manifest.json', 'w'))

def recolour(uri, hexcol):
    im = Image.open(io.BytesIO(decode(uri))).convert('RGBA')
    r, g, b = (int(hexcol[i:i+2], 16) for i in (1, 3, 5))
    solid = Image.new('RGBA', im.size, (r, g, b, 255))
    solid.putalpha(im.getchannel('A'))
    buf = io.BytesIO(); solid.save(buf, 'PNG', optimize=True)
    return buf.getvalue()

for key in ('scion', 'harlequin', 'clarke'):
    open(f'{ROOT}/public/images/logos/{key}.png', 'wb').write(decode(logos[key]))
for bkey, th in themes.items():
    open(f"{ROOT}/public/images/logos/{th['logo_key']}_rail.png", 'wb').write(
        recolour(logos[th['logo_key']], th['RAIL_INK']))

# The trimmed white-on-sage Think Rugs cover logo lives in the landing master.
landing = open(f'{SRC}/Think_Rugs_Licensed_Brands.html').read()
m = re.search(r'class="logo" src="(data:image/[a-z]+;base64,[A-Za-z0-9+/=]+)"', landing)
Image.open(io.BytesIO(decode(m.group(1)))).convert('RGB').save(
    f'{ROOT}/public/images/logos/thinkrugs_cover.jpg', 'JPEG', quality=85)

for bkey, p in xlsx.items():
    open(f"{ROOT}/public/downloads/{p['fname']}", 'wb').write(base64.b64decode(p['b64']))

co = len([f for f in os.listdir(f'{ROOT}/public/images/products') if f.endswith('_cut.jpg')])
li = len([f for f in os.listdir(f'{ROOT}/public/images/products') if f.endswith('_life.jpg')])
print(f'exported {co} cutouts, {li} lifestyles, {len(os.listdir(f"{ROOT}/public/downloads"))} downloads, logos OK')
