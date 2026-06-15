import brandData from '@/data/brand_data.json';
import themes from '@/data/themes.json';
import manifest from '@/data/img_manifest.json';

// Route per brand; the legacy `file` field in themes.json is ignored here.
export const ROUTES = {
  Scion: '/scion-living',
  Harlequin: '/harlequin',
  'Clarke & Clarke': '/clarke-and-clarke',
  LLB: '/house-llewelyn-bowen',
  'Catherine Lansfield': '/catherine-lansfield',
  'CL Kids': '/catherine-lansfield-kids',
};

export const BRAND_KEYS = Object.keys(themes);

// Suite wide counts for the landing page, computed from the data so they never go stale.
export function getStats() {
  let colourways = 0;
  let options = 0;
  BRAND_KEYS.forEach((k) => {
    brandData[k].designs.forEach((d) => {
      colourways += d.colourways.length;
      d.colourways.forEach((c) => { options += c.sizes.length; });
    });
  });
  return { brands: BRAND_KEYS.length, colourways, options };
}

// Landing page cards, one per brand: identity from themes.json (so tile
// colours can never drift from the brochure covers) and live counts from the
// catalogue data. Optional theme fields tune the tile without touching the
// brochure: TILE_BG (defaults to COVER), TILE_INK (defaults to white on dark
// tiles, near black on light ones), TILE_LOGO (defaults to logo_key, lets a
// light tile use the rail variant) and TILE_LOGO_WIDTH (defaults to 78%, for
// wide, short marks that need more room).
function isLightHex(hex) {
  const h = hex.replace('#', '');
  const n = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  const r = parseInt(n.slice(0, 2), 16);
  const g = parseInt(n.slice(2, 4), 16);
  const b = parseInt(n.slice(4, 6), 16);
  return 0.299 * r + 0.587 * g + 0.114 * b > 150;
}

export function getBrandCards() {
  return BRAND_KEYS.map((k) => {
    const t = themes[k];
    let colourways = 0;
    let options = 0;
    brandData[k].designs.forEach((d) => {
      colourways += d.colourways.length;
      d.colourways.forEach((c) => { options += c.sizes.length; });
    });
    const bg = t.TILE_BG || t.COVER;
    const light = isLightHex(bg);
    return {
      key: k,
      name: t.display_name,
      href: ROUTES[k],
      logo: `/images/logos/${t.TILE_LOGO || t.logo_key}.png`,
      bg,
      ink: t.TILE_INK || (light ? '#2c332e' : '#ffffff'),
      tone: light ? 'light' : 'dark',
      logoWidth: t.TILE_LOGO_WIDTH || null,
      designs: brandData[k].designs.length,
      colourways,
      options,
    };
  });
}

export function getTheme(brandKey) {
  return themes[brandKey];
}

// Prepared brand data: runners sorted to the bottom of every size list,
// image availability merged in from the build time manifest.
export function getBrand(brandKey) {
  const src = brandData[brandKey];
  const designs = src.designs.map((d) => ({
    ...d,
    colourways: d.colourways.map((c) => {
      const sizes = [...c.sizes].sort((a, b) => (a.runner ? 1 : 0) - (b.runner ? 1 : 0));
      const m = manifest[c.code] || {};
      return {
        ...c,
        sizes,
        img: {
          cut: m.cut ? `/images/products/${c.code}_cut.jpg` : null,
          life: m.life ? `/images/products/${c.code}_life.jpg` : null,
          detail: m.detail ? `/images/products/${c.code}_detail.jpg` : null,
        },
      };
    }),
  }));
  return { brand: getTheme(brandKey).display_name, designs };
}

// Brands without a published product info file yet return null; the brochure
// hides the download link until the file lands in public/downloads/ and is
// added here.
export function getDownload(brandKey) {
  const names = {
    Scion: 'Scion_Living_Product_Info.xlsx',
    Harlequin: 'Harlequin_Product_Info.xlsx',
    'Clarke & Clarke': 'Clarke_and_Clarke_Product_Info.xlsx',
    LLB: 'House_Llewelyn_Bowen_Product_Info.xlsx',
    'Catherine Lansfield': 'Catherine_Lansfield_Product_Info.xlsx',
    'CL Kids': 'Catherine_Lansfield_Kids_Product_Info.xlsx',
  };
  return names[brandKey] ? `/downloads/${names[brandKey]}` : null;
}

export function getSelKey(brandKey) {
  return 'thinkrugs_' + brandKey.toLowerCase().replace(/[^a-z]+/g, '_') + '_selection_2025';
}

export const gbp = (v) => (v == null ? '' : '\u00A3' + v.toFixed(2));
export const eur = (v) => (v == null ? '' : '\u20AC' + v.toFixed(2));
export const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-');
