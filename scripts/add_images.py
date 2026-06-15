"""
add_images.py

Adds product photography to the site: processes JPGs into
public/images/products/{CODE}_cut.jpg and {CODE}_life.jpg at the suite's standard
sizes, and updates data/img_manifest.json. Safe to re run, existing outputs are
skipped unless --force is passed. Rebuild after running (npm run build).

Usage: python3 scripts/add_images.py <folder or zip> [--force] [--map 2=cut,1=life]

Accepted input filenames (extension case does not matter, .png also fine; spaces
in names may arrive as underscores, both are handled):
1. {CODE}_cut.jpg / {CODE}_life.jpg        this project's native naming
2. {CODE}_CO1.jpg / {CODE}_L2.jpg          the legacy single file project naming
3. LLB - {Design} {Colour}[ Rug]_{N}.jpg   the LLB photo library naming. A dot,
   slash or underscore in the colour all match (Dolce Vita Black/White). Numbered
   suffixes are mapped per batch with --map. For this library: _2 is the white
   background pack shot (cutout) and _1 is the room scene (lifestyle). _1B is an
   alternate room scene, used as the lifestyle only when no plain _1 exists for
   that colourway. Pass --map to override per batch; the default is 2=cut,1=life.

Processing, matched to the existing imagery in this project:
- cutouts: white margins trimmed off the source first (the metallic pack shots
  arrive on large square canvases), then fitted within 690 x 920 and padded onto
  pure white to exactly 690 x 920
- lifestyles: the room scenes arrive as large squares with the rug placed off
  centre, so the rug is detected and the frame is cropped to 760 x 1040 centred on
  it, keeping surrounding room context, then never upscaled. Detection uses OpenCV
  if available; without it, a fixed lower centre crop is used as a fallback.
- both saved as JPEG quality 72, optimised
"""
import json, os, re, shutil, sys, tempfile, zipfile
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUT_BOX = (690, 920)
LIFE_W = 760
LIFE_BOX = (760, 1040)   # cropped, centred-on-rug lifestyle frame
QUALITY = 72
TRIM_THRESHOLD = 248   # fallback only: pixels lighter than this count as background
BG_FLOOD_TOL = 14      # per channel tolerance when flooding the white background inward
CUT_MARGIN = 0.022     # uniform margin kept around every trimmed cutout, as a fraction of the frame

num_map = {'2': 'cut', '1': 'life', '4': 'detail'}

brand_data = json.load(open(f'{ROOT}/data/brand_data.json'))
codes = set()
namekey_to_code = {}


def normkey(s):
    s = re.sub(r'[./_]', ' ', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    return re.sub(r'\s+rug$', '', s)


for brand in brand_data.values():
    for d in brand['designs']:
        for c in d['colourways']:
            codes.add(c['code'])
            namekey_to_code[normkey(f"{d['name']} {c['colour']}")] = c['code']
            # photo library names sometimes use the workbook's Colour column
            # (Navy is "Blue", Terra is "Terracotta"); the extractors store
            # those as aliases on the colourway
            for a in c.get('aliases', []):
                namekey_to_code.setdefault(normkey(f"{d['name']} {a}"), c['code'])

NAMED_KIND = {'cut': 'cut', 'life': 'life', 'CO1': 'cut', 'L2': 'life'}


def identify(fname, plain_pairs):
    """Return (code, kind) or ('skip'|'unmatched', detail).
    plain_pairs: set of (code, number) that have a plain _N file in this batch, used
    to decide whether a _NB alternate should stand in (only when plain _N absent)."""
    base = re.sub(r'\.(jpe?g|png)$', '', fname, flags=re.I)
    m = re.match(r'^([A-Z0-9&]+)_(cut|life|CO1|L2)$', base)
    if m and m.group(1) in codes:
        return m.group(1), NAMED_KIND[m.group(2)]
    m = re.match(r'^(.*)[_ ](\d+)([A-Z]?)$', base)
    if m:
        name, num, alt = m.group(1), m.group(2), m.group(3)
        name = re.sub(r'^LLB[\s_]*-[\s_]*', '', name.replace('_', ' ').strip())
        code = namekey_to_code.get(normkey(name))
        if code:
            kind = num_map.get(num)
            if kind not in ('cut', 'life', 'detail'):
                return 'skip', f'{fname} (suffix _{num}{alt} not mapped, pass --map to include)'
            if alt:
                # an alternate like _1B: use it only as a lifestyle stand in when
                # there is no plain _{num} for this colourway in the batch
                if kind == 'life' and (code, num) not in plain_pairs:
                    return code, 'life'
                return 'skip', f'{fname} (alternate _{num}{alt}, plain _{num} preferred)'
            return code, kind
    return 'unmatched', fname


def rug_bbox(im):
    """Return the tight rug rectangle on a white pack shot.

    Detects the rug by flooding the white background inward from the four
    corners with a tolerance, so soft drop shadows (smooth gradients that
    connect to the background) get consumed up to the rug's hard edge, while
    pale rug interiors are kept because they are enclosed by the rug body and
    never reached from a corner. This is far steadier across shots than a
    single luminance threshold, which catches a one sided shadow as if it were
    rug and skews the crop. Falls back to a threshold bbox if OpenCV is absent.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        mask = im.convert('L').point(lambda p: 255 if p < TRIM_THRESHOLD else 0)
        return mask.getbbox()
    import numpy as np
    arr = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()  # to BGR for cv2
    h, w = arr.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    tol = (BG_FLOOD_TOL,) * 3
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        # only flood from a corner that is actually background (near white)
        if arr[seed[1], seed[0]].min() >= 235:
            cv2.floodFill(arr, mask, seed, (0, 0, 0),
                          loDiff=tol, upDiff=tol, flags=4 | (255 << 8))
    background = mask[1:-1, 1:-1] > 0
    content = ~background
    ys, xs = np.where(content)
    if len(xs) == 0:
        return im.convert('L').point(lambda p: 255 if p < TRIM_THRESHOLD else 0).getbbox()
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def flatten_white(im):
    if im.mode in ('RGBA', 'P', 'LA'):
        rgba = im.convert('RGBA')
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.getchannel('A'))
        return bg
    return im.convert('RGB')


def save_cut(im, path):
    im = flatten_white(ImageOps.exif_transpose(im))
    box = rug_bbox(im)
    if box:
        im = im.crop(box)
    # fit the tight rug into the frame minus a uniform margin, then centre it,
    # so every cutout sits identically regardless of source resolution or any
    # leftover shadow. Margin is a fraction of the frame, not the source.
    margin = round(min(CUT_BOX) * CUT_MARGIN)
    inner = (CUT_BOX[0] - 2 * margin, CUT_BOX[1] - 2 * margin)
    im = ImageOps.contain(im, inner)
    canvas = Image.new('RGB', CUT_BOX, (255, 255, 255))
    canvas.paste(im, ((CUT_BOX[0] - im.width) // 2, (CUT_BOX[1] - im.height) // 2))
    canvas.save(path, 'JPEG', quality=QUALITY, optimize=True)


def rug_centroid(path):
    """Normalised (cx, cy) of the rug in a room scene, via floor-zone texture.
    Falls back to a fixed lower centre point if OpenCV is unavailable."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return 0.5, 0.62
    img = cv2.imread(path)
    if img is None:
        return 0.5, 0.62
    H, W = img.shape[:2]
    s = 700 / max(H, W)
    sm = cv2.resize(img, (int(W * s), int(H * s)))
    h, w = sm.shape[:2]
    gray = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype('float32')
    mean = cv2.blur(gray, (13, 13))
    sq = cv2.blur(gray * gray, (13, 13))
    std = cv2.sqrt(np.maximum(sq - mean * mean, 0))
    tex = (std > std.mean() * 1.25).astype('uint8')
    tex[:int(h * 0.35), :] = 0   # exclude walls, windows, furniture backs
    tex = cv2.morphologyEx(tex, cv2.MORPH_CLOSE, np.ones((21, 21), 'uint8'))
    tex = cv2.morphologyEx(tex, cv2.MORPH_OPEN, np.ones((11, 11), 'uint8'))
    cnts, _ = cv2.findContours(tex, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return 0.5, 0.62
    M = cv2.moments(max(cnts, key=cv2.contourArea))
    if M['m00'] == 0:
        return 0.5, 0.62
    return M['m10'] / M['m00'] / w, M['m01'] / M['m00'] / h


def save_life(im, path, src_path, centre=False):
    im = ImageOps.exif_transpose(im).convert('RGB')
    W, Ht = im.size
    ratio = LIFE_BOX[0] / LIFE_BOX[1]
    cw = W
    ch = int(cw / ratio)
    if ch > Ht:
        ch = Ht
        cw = int(ch * ratio)
    # room scenes are cropped onto the detected rug; full frame detail shots
    # (a texture close up that fills the frame) are simply centre cropped
    cx, cy = (0.5, 0.5) if centre else rug_centroid(src_path)
    left = max(0, min(int(cx * W - cw / 2), W - cw))
    top = max(0, min(int(cy * Ht - ch / 2), Ht - ch))
    im = im.crop((left, top, left + cw, top + ch))
    if im.width > LIFE_BOX[0]:
        im = im.resize(LIFE_BOX, Image.LANCZOS)
    im.save(path, 'JPEG', quality=QUALITY, optimize=True)


def main(argv):
    global num_map
    force = '--force' in argv
    args = [a for a in argv[1:] if a != '--force']
    if '--map' in args:
        i = args.index('--map')
        num_map = dict(p.split('=') for p in args[i + 1].split(','))
        del args[i:i + 2]
    if not args:
        sys.exit('usage: python3 scripts/add_images.py <folder or zip> [--force] [--map 2=cut,1=life]')
    src = args[0]

    tmp = None
    if src.lower().endswith('.zip'):
        tmp = tempfile.mkdtemp()
        zipfile.ZipFile(src).extractall(tmp)
        src = tmp

    manifest_path = f'{ROOT}/data/img_manifest.json'
    manifest = json.load(open(manifest_path))
    added, skipped_existing, skipped_alt, unmatched = [], [], [], []

    files = sorted(f for f in os.listdir(src) if re.search(r'\.(jpe?g|png)$', f, re.I))

    # which (code, number) pairs have a plain _N (no alternate letter), so a _NB
    # alternate is only used as a stand in when the plain _N shot is absent
    plain_pairs = set()
    for fname in files:
        base = re.sub(r'\.(jpe?g|png)$', '', fname, flags=re.I)
        m = re.match(r'^(.*)[_ ](\d+)$', base)
        if m:
            name = re.sub(r'^LLB[\s_]*-[\s_]*', '', m.group(1).replace('_', ' ').strip())
            code = namekey_to_code.get(normkey(name))
            if code:
                plain_pairs.add((code, m.group(2)))

    for fname in files:
        code, kind = identify(fname, plain_pairs)
        if code == 'skip':
            skipped_alt.append(kind)
            continue
        if code == 'unmatched':
            unmatched.append(kind)
            continue
        out = f'{ROOT}/public/images/products/{code}_{kind}.jpg'
        if os.path.exists(out) and not force:
            skipped_existing.append(f'{code}_{kind}')
            continue
        in_path = os.path.join(src, fname)
        im = Image.open(in_path)
        # blank source guard: a uniform frame (like an all black export) is a bad
        # file; report it instead of embedding a blank rug shot
        lo, hi = im.convert('L').getextrema()
        if hi - lo < 8:
            unmatched.append(f'{fname} (blank or corrupt source, re export needed)')
            continue
        if kind == 'cut':
            save_cut(im, out)
        elif kind == 'detail':
            save_life(im, out, in_path, centre=True)
        else:
            save_life(im, out, in_path)
        manifest.setdefault(code, {})[kind] = True
        added.append(f'{code}_{kind}  ({fname}, {os.path.getsize(out) // 1024} KB)')

    # reconcile: ensure every processed file already on disk has its manifest
    # entry, healing any earlier run that was interrupted before saving
    products_dir = f'{ROOT}/public/images/products'
    healed = []
    for f in os.listdir(products_dir):
        m = re.match(r'^(.+)_(cut|life|detail)\.jpg$', f)
        if m and m.group(1) in codes and not manifest.get(m.group(1), {}).get(m.group(2)):
            manifest.setdefault(m.group(1), {})[m.group(2)] = True
            healed.append(f'{m.group(1)}_{m.group(2)}')
    json.dump(manifest, open(manifest_path, 'w'))
    if healed:
        print(f'healed {len(healed)} manifest entries for files already on disk: ' + ', '.join(sorted(healed)))
    if tmp:
        shutil.rmtree(tmp)

    print(f'added {len(added)}:')
    for a in added:
        print('  ' + a)
    if skipped_existing:
        print(f'already present, skipped {len(skipped_existing)} (use --force to redo): ' + ', '.join(skipped_existing))
    if skipped_alt:
        print(f'skipped {len(skipped_alt)} (alternate or unmapped suffix):')
        for s in skipped_alt:
            print('  ' + s)
    if unmatched:
        print(f'UNMATCHED, no product code found for {len(unmatched)}:')
        for u in unmatched:
            print('  ' + u)
    print('done. rebuild with: npm run build')


if __name__ == '__main__':
    main(sys.argv)
