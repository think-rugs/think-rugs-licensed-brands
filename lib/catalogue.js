import brandData from '@/data/brand_data.json';
import themes from '@/data/themes.json';
import manifest from '@/data/img_manifest.json';

// Route per brand; the legacy `file` field in themes.json is ignored here.
export const ROUTES = {
  Scion: '/scion-living',
  Harlequin: '/harlequin',
  'Clarke & Clarke': '/clarke-and-clarke',
};

export const BRAND_KEYS = Object.keys(themes);

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
        },
      };
    }),
  }));
  return { brand: getTheme(brandKey).display_name, designs };
}

export function getDownload(brandKey) {
  const names = {
    Scion: 'Scion_Living_Product_Info.xlsx',
    Harlequin: 'Harlequin_Product_Info.xlsx',
    'Clarke & Clarke': 'Clarke_and_Clarke_Product_Info.xlsx',
  };
  return `/downloads/${names[brandKey]}`;
}

export function getSelKey(brandKey) {
  return 'thinkrugs_' + brandKey.toLowerCase().replace(/[^a-z]+/g, '_') + '_selection_2025';
}

export const gbp = (v) => (v == null ? '' : '\u00A3' + v.toFixed(2));
export const eur = (v) => (v == null ? '' : '\u20AC' + v.toFixed(2));
export const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-');
