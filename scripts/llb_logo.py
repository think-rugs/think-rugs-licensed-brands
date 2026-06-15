"""
llb_logo.py

Renders the official House Llewelyn-Bowen brand mark (a vector PDF lockup) into
the two PNGs the brochure uses:
- public/images/logos/llb.png       the cover and landing card mark
- public/images/logos/llb_rail.png  the rail mark

The artwork is an antique gold wordmark on a transparent ground. Gold reads well
both on the dark aubergine cover (#231335) and on the light cream rail (#faf7f2),
so both outputs are the same trimmed, transparent PNG. Source of truth is the
PDF under public/images/logos/source, so this is fully reproducible: drop a new
PDF there and rerun.

Requires PyMuPDF (pip install pymupdf).
Usage: python3 scripts/llb_logo.py [path/to/logo.pdf]
"""
import os, sys
import fitz
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/public/images/logos/source/house_llewelyn-bowen.pdf'
OUT_DIR = f'{ROOT}/public/images/logos'
RENDER_SCALE = 4        # supersample the vector art for a crisp edge
TARGET_W = 1200         # final width in px (a wide wordmark needs little height)
MARGIN_FRAC = 0.04      # small transparent margin around the trimmed mark


def render_pdf(path):
    page = fitz.open(path)[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=True)
    return Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)


def trim_and_pad(im):
    im = im.crop(im.split()[3].getbbox())          # trim to the artwork's alpha bounds
    m = round(max(im.size) * MARGIN_FRAC)
    canvas = Image.new('RGBA', (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
    canvas.alpha_composite(im, (m, m))
    if canvas.width > TARGET_W:
        h = round(canvas.height * TARGET_W / canvas.width)
        canvas = canvas.resize((TARGET_W, h), Image.LANCZOS)
    return canvas


logo = trim_and_pad(render_pdf(SRC))
logo.save(f'{OUT_DIR}/llb.png')
logo.save(f'{OUT_DIR}/llb_rail.png')
print(f'wrote llb.png and llb_rail.png at {logo.width} x {logo.height} from {os.path.basename(SRC)}')
