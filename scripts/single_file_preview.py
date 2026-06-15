"""
single_file_preview.py

Generates a fully self contained, single file HTML brochure for one brand, for
testing and emailing without running the Next.js site. Opens straight from disk.

Usage: python3 scripts/single_file_preview.py [BRAND_KEY] [output.html]
Default brand: LLB. Default output: the theme's `file` name in the project root.

What it inlines: the brochure CSS with the brand's theme variables baked in, the
brand logo and rail mark as base64, the product info Excel as a data URI, and any
product photography listed in data/img_manifest.json as base64 (brands with full
photography will produce a large file; LLB currently has none, so it stays small).

Behaviour is a vanilla JS port of components/BrandBrochure.jsx: search, colour
filter, Photographed only / trade price / selection toggles, selection persisted
in localStorage under the same key as the site, CSV export with the Washable
column derived from design features, designs nav with scrollspy and counts, and
the product pop up with gallery, keyboard and swipe support. The two "All licensed
brands" links are omitted, there is nothing to link back to in a single file.
"""
import base64, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = sys.argv[1] if len(sys.argv) > 1 else 'LLB'

themes = json.load(open(f'{ROOT}/data/themes.json'))
brand_data = json.load(open(f'{ROOT}/data/brand_data.json'))
manifest = json.load(open(f'{ROOT}/data/img_manifest.json'))
theme = themes[BRAND]

OUT = sys.argv[2] if len(sys.argv) > 2 else f"{ROOT}/{theme['file']}"

DOWNLOAD_NAMES = {
    'Scion': 'Scion_Living_Product_Info.xlsx',
    'Harlequin': 'Harlequin_Product_Info.xlsx',
    'Clarke & Clarke': 'Clarke_and_Clarke_Product_Info.xlsx',
    'LLB': 'House_Llewelyn_Bowen_Product_Info.xlsx',
    'Catherine Lansfield': 'Catherine_Lansfield_Product_Info.xlsx',
    'CL Kids': 'Catherine_Lansfield_Kids_Product_Info.xlsx',
}


def b64(path):
    return base64.b64encode(open(path, 'rb').read()).decode()


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


# ---- data prep, mirrors lib/catalogue.js getBrand ----
designs = []
for d in brand_data[BRAND]['designs']:
    cws = []
    for c in d['colourways']:
        sizes = sorted(c['sizes'], key=lambda s: 1 if s.get('runner') else 0)
        m = manifest.get(c['code'], {})
        img = {}
        for key in ('cut', 'life', 'detail'):
            if m.get(key):
                img[key] = 'data:image/jpeg;base64,' + b64(
                    f"{ROOT}/public/images/products/{c['code']}_{key}.jpg")
            else:
                img[key] = None
        cws.append({**c, 'sizes': sizes, 'img': img})
    designs.append({**d, 'colourways': cws})

data = {'brand': theme['display_name'], 'designs': designs}
sel_key = 'thinkrugs_' + ''.join(ch if ch.isalpha() else '_' for ch in BRAND.lower()) + '_selection_2025'
# collapse runs the way the JS regex does
while '__' in sel_key:
    sel_key = sel_key.replace('__', '_')

groups = []
for d in designs:
    if d.get('group') and d['group'] not in groups:
        groups.append(d['group'])
HAS_GROUPS = len(groups) > 1
group_ctl = ('<div class="ctl"><label for="fgroup">Collection</label>'
             '<select id="fgroup"><option value="">All collections</option>'
             + ''.join(f'<option>{g}</option>' for g in groups)
             + '</select></div>') if HAS_GROUPS else ''

logo = 'data:image/png;base64,' + b64(f"{ROOT}/public/images/logos/{theme['logo_key']}.png")
logo_rail = 'data:image/png;base64,' + b64(f"{ROOT}/public/images/logos/{theme['logo_key']}_rail.png")
xlsx_uri = ('data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,'
            + b64(f"{ROOT}/public/downloads/{DOWNLOAD_NAMES[BRAND]}"))

css = open(f'{ROOT}/app/brochure.css').read()
theme_vars = f""".brochure{{
  --accent:{theme['ACCENT']}; --accent-text:{theme['ACCENT_TEXT']}; --accent-soft:{theme['ACCENT_SOFT']};
  --accent-on-dark:{theme['ACCENT_DARKBG']}; --cover:{theme['COVER']}; --tint:{theme['TINT']};
  --ink:{theme['INK']}; --line:{theme['LINE']}; --rail:{theme['RAIL']};
  --body-font:{theme['BODY_FONT']}; --body-ls:{theme['BODY_LS']};
  --display-font:{theme['DISPLAY']}; --display-weight:{theme['DISPLAY_WEIGHT']};
  --display-ls:{theme['DISPLAY_LS']}; --display-tt:{theme['DISPLAY_TT']};
  --selcount-ink:{theme['SELCOUNT_INK']};
}}"""

sub = theme.get('SUB', 'Washable Rug Collection')
rail_sub = theme.get('RAIL_SUB', 'Washable Rugs, New 2025')
cover_tone = theme.get('COVER_TONE', 'dark')
title = f"{theme['display_name']} | {sub} | Think Rugs"
data_json = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')

JS = r"""
'use strict';
const GBP = v => v == null ? '' : '\u00A3' + v.toFixed(2);
const EUR = v => v == null ? '' : '\u20AC' + v.toFixed(2);
const SLUG = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-');
const ESC = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

const flat = [];
DATA.designs.forEach(d => d.colourways.forEach(c => flat.push({ d, c })));
const byCode = {};
flat.forEach(e => { byCode[e.c.code] = e; });
const allColours = [...new Set(flat.map(e => e.c.c1).filter(Boolean))].sort();
const hasPhotography = flat.some(e => e.c.img.cut || e.c.img.life || e.c.img.detail);

const HAS_GROUPS = {has_groups};
const state = {
  term: '', colour: '', group: '', imgOnly: hasPhotography, selOnly: false, showTrade: true,
  selected: new Set(), modalCode: null, gIdx: 0, order: [], activeRange: null, lightbox: false,
};
try {
  const saved = localStorage.getItem(SEL_KEY);
  if (saved) state.selected = new Set(JSON.parse(saved));
} catch (e) {}
const persist = () => { try { localStorage.setItem(SEL_KEY, JSON.stringify([...state.selected])); } catch (e) {} };

const matches = e => {
  const { d, c } = e;
  const hay = (d.name + ' ' + (c.label || '') + ' ' + c.colour + ' ' + c.code + ' ' + c.title + ' ' + c.c1 + ' ' + c.c2).toLowerCase();
  return (!state.term || hay.includes(state.term.trim().toLowerCase())) &&
    (!state.colour || c.c1 === state.colour || c.c2 === state.colour) &&
    (!state.group || !HAS_GROUPS || d.group === state.group) &&
    (!state.imgOnly || !!(c.img.cut || c.img.life || c.img.detail)) &&
    (!state.selOnly || state.selected.has(c.code));
};

const visible = () => {
  const perDesign = new Map(); const codes = [];
  DATA.designs.forEach(d => {
    const vis = d.colourways.filter(c => matches({ d, c }));
    perDesign.set(d.name, vis);
    vis.forEach(c => codes.push(c.code));
  });
  return { perDesign, codes, shown: codes.length };
};

const PH = label => '<div class="ph"><svg viewBox="0 0 100 130" aria-hidden="true"><use href="#rugPh"/></svg>' +
  '<span class="pt">Image to follow</span>' + (label ? '<span class="pn">' + ESC(label) + '</span>' : '') + '</div>';

function cardHTML(d, c) {
  const img = c.img.cut || c.img.life;
  const on = state.selected.has(c.code);
  const fromT = Math.min(...c.sizes.map(s => s.trade));
  return '<article class="card' + (on ? ' selected' : '') + '" tabindex="0" role="button" data-code="' + ESC(c.code) + '"' +
    ' aria-label="View ' + ESC(c.title) + '">' +
    '<div class="card-media">' +
    (img ? '<img loading="lazy" src="' + img + '" alt="' + ESC(c.title) + ' rug">' : PH('')) +
    '<button class="pick" data-pick="' + ESC(c.code) + '" aria-pressed="' + on + '"' +
    ' title="' + (on ? 'Remove from my selection' : 'Add to my selection') + '">' +
    '<svg class="i-add"><use href="#iAdd"/></svg><svg class="i-on"><use href="#iOn"/></svg></button></div>' +
    '<div class="card-body"><span class="card-code">' + ESC(c.label || d.name) + '</span><h4>' + ESC(c.colour) + '</h4>' +
    '<p>' + ESC(c.c1) + (c.c2 && c.c2 !== c.c1 ? ' / ' + ESC(c.c2) : '') + '</p>' +
    '<div class="card-foot"><span>' + c.sizes.length + ' sizes</span>' +
    '<span class="frm">From <b>' + GBP(fromT) + '</b> <i>trade</i></span></div></div></article>';
}

let spy = null;
function render() {
  const vis = visible();
  const main = document.getElementById('sections');
  let lastGroup = null;
  main.innerHTML = DATA.designs.map(d => {
    const v = vis.perDesign.get(d.name);
    if (!v.length) return '';
    const variants = d.colourways.reduce((n, c) => n + c.sizes.length, 0);
    const startsGroup = HAS_GROUPS && d.group !== lastGroup;
    lastGroup = d.group;
    const divider = startsGroup ? '<div class="group-divider"><h2>' + ESC(d.group) + '</h2></div>' : '';
    return '<section class="range' + (startsGroup ? ' group-start' : '') + '" id="rg-' + SLUG(d.name) + '" data-range="' + ESC(d.name) + '">' + divider +
      '<header class="range-head"><div class="range-title"><h2>' + ESC(d.name) + '</h2>' +
      '<span class="range-count"><b>' + v.length + '</b> colourways, ' + variants + ' product options</span></div>' +
      '<p class="intro">' + ESC(d.intro) + '</p>' +
      '<p class="range-meta"><b>' + ESC(d.construction) + '</b> &middot; ' + ESC(d.materials) +
      '<span class="range-from"> &middot; From <b>' + GBP(d.fromTrade) + '</b> trade</span></p>' +
      '<div class="feats">' + d.features.map(f => '<span class="feat">' + ESC(f) + '</span>').join('') + '</div>' +
      '</header><div class="grid">' + v.map(c => cardHTML(d, c)).join('') + '</div></section>';
  }).join('');
  document.getElementById('noResults').style.display = vis.shown === 0 ? 'block' : 'none';
  document.getElementById('results').textContent = vis.shown + ' of ' + flat.length + ' colourways shown';
  let lastNavGroup = null;
  document.getElementById('rlinks').innerHTML = DATA.designs.map(d => {
    const n = vis.perDesign.get(d.name).length;
    let h = '';
    if (HAS_GROUPS && d.group !== lastNavGroup) { lastNavGroup = d.group; h = '<span class="rgroup">' + ESC(d.group) + '</span>'; }
    return h + '<a class="rlink' + (state.activeRange === d.name ? ' active' : '') + (n ? '' : ' dimmed') + '"' +
      ' href="#rg-' + SLUG(d.name) + '"><span>' + ESC(d.name) + '</span><small class="rcount">' + n + '</small></a>';
  }).join('');
  const selN = state.selected.size;
  const sc = document.getElementById('selcount');
  sc.textContent = selN; sc.className = 'selcount' + (selN === 0 ? ' empty' : '');
  document.getElementById('exportBtn').hidden = selN === 0;
  document.getElementById('clearSel').hidden = selN === 0;
  if (spy) spy.disconnect();
  if (typeof IntersectionObserver === 'undefined') return;
  spy = new IntersectionObserver(es => es.forEach(en => {
    if (en.isIntersecting && state.activeRange !== en.target.dataset.range) {
      state.activeRange = en.target.dataset.range;
      document.querySelectorAll('.rlink').forEach(a => a.classList.toggle('active',
        a.querySelector('span').textContent === state.activeRange));
    }
  }), { rootMargin: '-30% 0px -60% 0px' });
  document.querySelectorAll('section.range').forEach(s => spy.observe(s));
}

function toggleSelect(code) {
  if (state.selected.has(code)) state.selected.delete(code);
  else state.selected.add(code);
  persist();
  if (state.selected.size === 0 && state.selOnly) {
    state.selOnly = false; document.getElementById('tSel').checked = false;
  }
  render();
  if (state.modalCode) renderModal();
}

/* ---------- modal ---------- */
const overlay = document.getElementById('overlay');
let lastFocus = null, touchX = null;

function gImgs() {
  const { c } = byCode[state.modalCode];
  const list = [];
  if (c.img.cut) list.push({ src: c.img.cut, label: 'Cutout' });
  if (c.img.life) list.push({ src: c.img.life, label: 'Lifestyle' });
  if (c.img.detail) list.push({ src: c.img.detail, label: 'Detail' });
  return list;
}

function renderModal() {
  const { d, c } = byCode[state.modalCode];
  const imgs = gImgs();
  const galMain = document.getElementById('galMain');
  if (imgs.length) {
    const i = state.gIdx;
    galMain.innerHTML = '<img src="' + imgs[i].src + '" alt="Product image ' + (i + 1) + ' of ' + imgs.length + '" class="zoomable" data-zoom="1" role="button" tabindex="0" aria-label="Open larger image">' +
      '<span class="glabel">' + imgs[i].label + '</span>' +
      (imgs.length > 1 ?
        '<button class="gnav prev" data-g="-1" aria-label="Previous image">&larr;</button>' +
        '<button class="gnav next" data-g="1" aria-label="Next image">&rarr;</button>' +
        '<div class="gdots">' + imgs.map((_, k) => '<i class="' + (k === i ? 'on' : '') + '"></i>').join('') + '</div>' +
        '<span class="gcount">' + (i + 1) + ' / ' + imgs.length + '</span>' : '');
  } else {
    galMain.innerHTML = PH(c.title);
  }
  const on = state.selected.has(c.code);
  document.getElementById('infoScroll').innerHTML =
    '<div class="modal-nav"><button data-step="-1">&larr; Previous</button><button data-step="1">Next &rarr;</button></div>' +
    '<span class="mcode">' + ESC(c.code) + '</span><h3>' + ESC(c.title) + '</h3>' +
    '<p class="mcols">' + ESC(c.c1) + (c.c2 && c.c2 !== c.c1 ? ' / ' + ESC(c.c2) : '') + '</p>' +
    '<button class="mpick' + (on ? ' on' : '') + '" data-pick="' + ESC(c.code) + '" aria-pressed="' + on + '">' +
    (on ? '\u2713 In my selection' : '+ Add to my selection') + '</button>' +
    '<div class="feats">' + d.features.map(f => '<span class="feat">' + ESC(f) + '</span>').join('') + '</div>' +
    '<table class="sizes"><thead><tr><th>Size</th><th class="num col-ws">Trade &pound;</th>' +
    '<th class="num col-ws">Trade &euro;</th><th class="num">RRP &pound;</th><th class="num">RRP &euro;</th></tr></thead><tbody>' +
    c.sizes.map(s => '<tr><td>' + ESC(s.size) + ' cm' +
      (s.shape === 'Circle' ? ' (circle)' : s.runner ? ' (runner)' : '') + '</td>' +
      '<td class="num col-ws">' + GBP(s.trade) + '</td><td class="num col-ws">' + EUR(s.tradeEur) + '</td>' +
      '<td class="num">' + GBP(s.rrp) + '</td><td class="num">' + EUR(s.rrpEur) + '</td></tr>').join('') +
    '</tbody></table><p class="trade-note">Trade prices are wholesale prices.</p>' +
    '<p class="desc">' + ESC(c.desc) + '</p>' +
    '<div class="spec">' +
    '<div class="row"><span class="k">Design</span><span>' + ESC(c.label || d.name) + '</span></div>' +
    (d.construction ? '<div class="row"><span class="k">Construction</span><span>' + ESC(d.construction) + '</span></div>' : '') +
    (d.materials ? '<div class="row"><span class="k">Materials</span><span>' + ESC(d.materials) + '</span></div>' : '') +
    (d.pile ? '<div class="row"><span class="k">Pile height</span><span>' + ESC(d.pile) + ' cm</span></div>' : '') +
    (d.origin ? '<div class="row"><span class="k">Country of origin</span><span>' + ESC(d.origin) + '</span></div>' : '') +
    '</div>';
  document.getElementById('infoScroll').scrollTop = 0;
  if (state.lightbox) renderLightbox();
}

function renderLightbox() {
  const imgs = gImgs();
  const stage = document.getElementById('lbStage');
  if (!imgs.length) { closeLightbox(); return; }
  const i = state.gIdx;
  stage.innerHTML = '<img src="' + imgs[i].src + '" alt="Product image ' + (i + 1) + ' of ' + imgs.length + '">' +
    '<span class="glabel">' + imgs[i].label + '</span>' +
    (imgs.length > 1 ?
      '<button class="gnav prev" data-g="-1" aria-label="Previous image">&larr;</button>' +
      '<button class="gnav next" data-g="1" aria-label="Next image">&rarr;</button>' +
      '<div class="gdots">' + imgs.map((_, k) => '<i class="' + (k === i ? 'on' : '') + '"></i>').join('') + '</div>' +
      '<span class="gcount">' + (i + 1) + ' / ' + imgs.length + '</span>' : '');
}
function openLightbox() {
  if (!gImgs().length) return;
  state.lightbox = true;
  document.getElementById('lightbox').classList.add('open');
  renderLightbox();
}
function closeLightbox() {
  state.lightbox = false;
  document.getElementById('lightbox').classList.remove('open');
}

function openProduct(code) {
  if (!byCode[code]) return;
  const vis = visible();
  state.order = vis.codes.includes(code) ? vis.codes : flat.map(e => e.c.code);
  if (!document.body.classList.contains('modal-open')) {
    lastFocus = document.activeElement;
    document.body.classList.add('modal-open');
  }
  state.gIdx = 0;
  state.modalCode = code;
  overlay.classList.add('open');
  renderModal();
}
function closeModal() {
  state.modalCode = null;
  closeLightbox();
  overlay.classList.remove('open');
  document.body.classList.remove('modal-open');
  if (lastFocus) lastFocus.focus();
}
function stepProduct(dir) {
  const i = state.order.indexOf(state.modalCode);
  state.modalCode = state.order[(i + dir + state.order.length) % state.order.length];
  state.gIdx = 0;
  renderModal();
}
function gStep(d) {
  const n = gImgs().length;
  if (n < 2) return;
  state.gIdx = (state.gIdx + d + n) % n;
  renderModal();
}

/* ---------- CSV export ---------- */
const csvCell = v => { v = v == null ? '' : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
function exportSelection() {
  if (!state.selected.size) return;
  const head = ['Product Code', 'Variant Code', 'Description', 'Brand', 'Design',
    ...(HAS_GROUPS ? ['Collection'] : []), 'Colour', 'Washable',
    'Size (cm)', 'Wholesale Price (GBP)', 'RRP (GBP)', 'Wholesale Price (EUR)', 'RRP (EUR)'];
  const lines = [head.map(csvCell).join(',')];
  flat.forEach(({ d, c }) => {
    if (!state.selected.has(c.code)) return;
    c.sizes.forEach(s => {
      lines.push([c.code, s.variant, c.title + ', ' + s.size, DATA.brand, (c.label || d.name),
        ...(HAS_GROUPS ? [d.group] : []), c.colour,
        d.features.includes('Washable') ? 'Yes' : 'No',
        s.size, s.trade, s.rrp, s.tradeEur, s.rrpEur].map(csvCell).join(','));
    });
  });
  const csv = '\ufeff' + lines.join('\r\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = DATA.brand.replace(/[^A-Za-z]+/g, '_') + '_My_Selection.csv';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 0);
}

/* ---------- wiring ---------- */
document.getElementById('q').addEventListener('input', e => { state.term = e.target.value; render(); });
document.getElementById('fcolour').addEventListener('change', e => { state.colour = e.target.value; render(); });
const fGroup = document.getElementById('fgroup');
if (fGroup) fGroup.addEventListener('change', e => { state.group = e.target.value; render(); });
document.getElementById('tImg').addEventListener('change', e => { state.imgOnly = e.target.checked; render(); });
document.getElementById('tTrade').addEventListener('change', e => {
  state.showTrade = e.target.checked;
  document.getElementById('brochure').classList.toggle('hide-trade', !state.showTrade);
});
document.getElementById('tSel').addEventListener('change', e => { state.selOnly = e.target.checked; render(); });
document.getElementById('exportBtn').addEventListener('click', exportSelection);
document.getElementById('clearFilters').addEventListener('click', () => {
  state.term = ''; state.colour = ''; state.group = ''; state.imgOnly = hasPhotography; state.selOnly = false;
  document.getElementById('q').value = '';
  document.getElementById('fcolour').value = '';
  if (fGroup) fGroup.value = '';
  document.getElementById('tImg').checked = hasPhotography;
  document.getElementById('tSel').checked = false;
  render();
});
document.getElementById('clearSel').addEventListener('click', () => { state.selected.clear(); persist(); render(); });

document.getElementById('sections').addEventListener('click', e => {
  const pick = e.target.closest('.pick');
  if (pick) { e.stopPropagation(); toggleSelect(pick.dataset.pick); return; }
  const card = e.target.closest('.card');
  if (card) openProduct(card.dataset.code);
});
document.getElementById('sections').addEventListener('keydown', e => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('card')) {
    e.preventDefault();
    openProduct(e.target.dataset.code);
  }
});

overlay.addEventListener('click', e => {
  if (e.target === overlay) { closeModal(); return; }
  const g = e.target.closest('[data-g]');
  if (g) { e.stopPropagation(); gStep(parseInt(g.dataset.g, 10)); return; }
  const zoom = e.target.closest('[data-zoom]');
  if (zoom) { e.stopPropagation(); openLightbox(); return; }
  const st = e.target.closest('[data-step]');
  if (st) { stepProduct(parseInt(st.dataset.step, 10)); return; }
  const pick = e.target.closest('[data-pick]');
  if (pick) toggleSelect(pick.dataset.pick);
});
document.getElementById('closeModal').addEventListener('click', closeModal);
document.addEventListener('keydown', e => {
  if (!state.modalCode) return;
  if (e.key === 'Escape') { if (state.lightbox) closeLightbox(); else closeModal(); }
  if (e.key === 'ArrowRight') gStep(1);
  if (e.key === 'ArrowLeft') gStep(-1);
  if ((e.key === 'Enter' || e.key === ' ') && !state.lightbox && e.target.closest('[data-zoom]')) {
    e.preventDefault(); openLightbox();
  }
});
const lightboxEl = document.getElementById('lightbox');
lightboxEl.addEventListener('click', e => {
  if (e.target === lightboxEl) { closeLightbox(); return; }
  const g = e.target.closest('[data-g]');
  if (g) { e.stopPropagation(); gStep(parseInt(g.dataset.g, 10)); }
});
document.getElementById('lbClose').addEventListener('click', closeLightbox);
const lbStage = document.getElementById('lbStage');
lbStage.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; }, { passive: true });
lbStage.addEventListener('touchend', e => {
  if (touchX == null) return;
  const dx = e.changedTouches[0].clientX - touchX;
  if (Math.abs(dx) > 40) gStep(dx < 0 ? 1 : -1);
  touchX = null;
}, { passive: true });
const galEl = document.getElementById('galMain');
galEl.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; }, { passive: true });
galEl.addEventListener('touchend', e => {
  if (touchX == null) return;
  const dx = e.changedTouches[0].clientX - touchX;
  if (Math.abs(dx) > 40) gStep(dx < 0 ? 1 : -1);
  touchX = null;
}, { passive: true });

document.getElementById('tImg').checked = hasPhotography;
render();
"""

colour_options = ''  # built in JS? No: build statically for simplicity
all_c1 = sorted({c['c1'] for d in designs for c in d['colourways'] if c['c1']})
colour_options = ''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in all_c1)

JS = JS.replace('{has_groups}', 'true' if HAS_GROUPS else 'false')

html = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(theme['BLURB'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{theme['FONT_IMPORT']}" rel="stylesheet">
<style>
{css}
{theme_vars}
.ph .pn{{ font-size:12px; opacity:0.55; font-weight:300; }}
</style>
</head>
<body>
<div class="brochure" id="brochure" data-align="{theme['HEAD_ALIGN']}">
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="rugPh" viewBox="0 0 100 130"><g fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round">
<rect x="14" y="14" width="72" height="102" rx="6"/><rect x="28" y="30" width="44" height="70" rx="3"/>
<path d="M14 8 v-4 M30 8 v-4 M46 8 v-4 M62 8 v-4 M78 8 v-4 M86 8 v-4"/>
<path d="M14 122 v4 M30 122 v4 M46 122 v4 M62 122 v4 M78 122 v4 M86 122 v4"/></g></symbol>
<symbol id="iAdd" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></symbol>
<symbol id="iOn" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></symbol>
</defs></svg>

<header class="cover" id="top" data-cover="{cover_tone}">
  <img class="logo" src="{logo}" alt="{esc(theme['display_name'])} logo">
  <p class="sub">{esc(sub)}</p>
  <p class="season">New 2025</p>
  <a class="enter" href="#catalogue">View the collection</a>
  <p class="presented">Presented by Think Rugs</p>
</header>

<div class="wrap" id="catalogue">
  <aside class="rail" aria-label="Browse and filter">
    <img class="brandmark" src="{logo_rail}" alt="{esc(theme['display_name'])}">
    <p class="sub">{esc(rail_sub)}</p>
    <h3>Find a product</h3>
    <div class="ctl"><label for="q">Search</label>
      <input id="q" type="search" placeholder="Design, colour or code"></div>
    <div class="ctl"><label for="fcolour">Colour</label>
      <select id="fcolour"><option value="">All colours</option>{colour_options}</select></div>
    {group_ctl}
    <label class="toggle"><input type="checkbox" id="tImg"> Photographed only</label>
    <label class="toggle"><input type="checkbox" id="tTrade" checked> Show trade prices</label>
    <label class="toggle"><input type="checkbox" id="tSel"> My selection only <span class="selcount empty" id="selcount">0</span></label>
    <button class="dl" type="button" id="exportBtn" hidden>Export selection (CSV)</button>
    <div class="selrow">
      <button class="clear" id="clearFilters">Clear filters</button>
      <button class="clear" id="clearSel" hidden>Clear selection</button>
    </div>
    <p class="results" id="results"></p>
    <a class="dl" href="{xlsx_uri}" download="{DOWNLOAD_NAMES[BRAND]}">Download full product info (Excel)</a>
    <h3>Designs</h3>
    <nav class="rlinks" id="rlinks" aria-label="Designs"></nav>
  </aside>

  <main>
    <div class="pagehead">
      <h1>{esc(theme['display_name'])}</h1>
      <p>{esc(theme['BLURB'])}</p>
    </div>
    <div id="sections"></div>
    <p class="no-results" id="noResults">No products match the current filters.</p>
  </main>
</div>

<footer>
  {esc(theme['display_name'])}, {esc(sub)}, New 2025. Presented by Think Rugs.
  <br><br>
  <span>{theme['FOOTER']}</span>
</footer>

<div class="overlay" id="overlay">
  <div class="modal"><div class="modal-pos">
    <div class="gal"><div class="main" id="galMain"></div></div>
    <div class="info-side"><div class="info-scroll" id="infoScroll"></div></div>
    <button class="close" id="closeModal" aria-label="Close">&times;</button>
  </div></div>
</div>

<div class="lightbox" id="lightbox">
  <div class="lb-stage" id="lbStage"></div>
  <button class="lb-close" id="lbClose" aria-label="Close larger image">&times;</button>
</div>
</div>

<script>
const DATA = {data_json};
const SEL_KEY = {json.dumps(sel_key)};
{JS}
</script>
</body>
</html>
"""

open(OUT, 'w').write(html)
print(f'{OUT}: {os.path.getsize(OUT)/1024:.0f} KB ({BRAND}, '
      f"{sum(len(d['colourways']) for d in designs)} colourways)")
