# Think Rugs Licensed Brands (Next.js)

The Licensed Brands suite as a single Next.js site: a landing page at `/` plus one
brochure route per brand, all linked together with the app router.

- `/` : Think Rugs Licensed Brands landing page (logo buttons through to each brand)
- `/scion-living` : Scion Living brochure
- `/harlequin` : Harlequin brochure
- `/clarke-and-clarke` : Clarke & Clarke brochure

This replaces the four linked single file HTML pages for hosted use. Images and the
Excel downloads are served as real static files instead of embedded base64, so pages
load fast and the build scales as photography lands. The legacy single file project
remains the right tool for emailable, fully offline copies.

## Running it

```
npm install
npm run dev        # develop at http://localhost:3000
npm run build      # static export written to out/
npm run preview    # serve the static export locally
```

The build is a full static export (`output: 'export'`), so `out/` can be hosted on
Vercel, Netlify, S3 or any plain web server with no Node in production.

## How it is put together

- `data/brand_data.json` : the product catalogue (same file as the legacy project)
- `data/themes.json` : per brand styling and copy (colours, fonts, blurb, footer)
- `data/img_manifest.json` : which colourways have a cutout and a lifestyle shot,
  written by the asset export script
- `public/images/products/` : `{CODE}_cut.jpg` and `{CODE}_life.jpg`
- `public/images/logos/` : brand marks, recoloured rail variants, Think Rugs cover logo
- `public/downloads/` : the per brand product info Excel files
- `components/BrandBrochure.jsx` : the whole brochure as one client component
  (search, colour filter, Photographed only / trade price / selection toggles,
  selection persisted in localStorage per brand, CSV export, designs nav with
  scrollspy and counts, product pop up with gallery, swipe and keyboard support,
  runners sorted to the bottom of size lists)
- `app/brochure.css` : the template CSS ported verbatim; theme values arrive as CSS
  variables set on the `.brochure` wrapper, so all three brands share one stylesheet
- `app/landing.css` : the landing page styles (lp prefixed to avoid class clashes)

## Routine jobs

### Adding photography

Process new shots with the legacy pipeline as before (it maintains `img_cache.json`),
then re run the asset export and rebuild:

```
python3 scripts/export_assets.py /path/to/legacy/project
npm run build
```

The export script decodes the image cache into `public/images/products/` and
refreshes `data/img_manifest.json`. New colourways appear automatically and the
Photographed only default keeps working (it is computed from the manifest).

Alternatively, drop processed JPGs straight into `public/images/products/` using the
`{CODE}_cut.jpg` / `{CODE}_life.jpg` naming and update `data/img_manifest.json` to
match, then rebuild.

### Refreshing product data

Replace `data/brand_data.json` (and the Excel files in `public/downloads/` if they
changed), then `npm run build`.

## Notes carried over from the single file suite

- Selections persist in localStorage under `thinkrugs_{brand}_selection_2025`, per
  browser and per site origin.
- Harlequin's design headings are left aligned (a deliberate departure from the
  centred copy in the Harlequin brand notes, per client request; flag it at licensor
  approval).
- The real brand fonts (Kamerik 105, Gill Sans, Futura BT) still need licensing;
  Poppins, Hanken Grotesk and Jost substitute as before, loaded in one request in
  `app/layout.js`.
- All artwork requires licensor marketing approval before publication.
- Copy style: no em dashes or long hyphens anywhere, only commas, colons,
  parentheses and full stops.
