# Think Rugs Licensed Brands (Next.js)

The Licensed Brands suite as a single Next.js site: a landing page at `/` plus one
brochure route per brand, all linked together with the app router.

- `/` : Think Rugs Licensed Brands landing page (logo buttons through to each brand)
- `/scion-living` : Scion Living brochure
- `/harlequin` : Harlequin brochure
- `/clarke-and-clarke` : Clarke & Clarke brochure
- `/house-llewelyn-bowen` : House Llewelyn-Bowen brochure (brand key `LLB`)
- `/catherine-lansfield` : Catherine Lansfield brochure (brand key `Catherine Lansfield`)
- `/catherine-lansfield-kids` : Catherine Lansfield Kids brochure (brand key `CL Kids`)

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

For a quick look at one brand without running anything, generate a single file
preview brochure that opens straight from disk:

```
python3 scripts/single_file_preview.py LLB
```

It inlines the theme, logo, Excel download and any photography into one HTML file
(LLB has no photography yet, so it is about 166 KB; fully photographed brands will
be much larger). The interactions are a vanilla JS port of the React component, so
it behaves the same as the hosted page apart from the missing back links to the
landing page. It also serves as the emailable, fully offline copy.

The build is a full static export (`output: 'export'`), so `out/` can be hosted on
Vercel, Netlify, S3 or any plain web server with no Node in production.

## How it is put together

- `data/brand_data.json` : the product catalogue (same file as the legacy project,
  plus the `LLB` block built by `scripts/extract_llb.py`)
- `data/themes.json` : per brand styling and copy (colours, fonts, blurb, footer).
  Two optional fields, `SUB` and `RAIL_SUB`, override the cover, rail and footer
  collection lines; brands without them keep the original "Washable Rug Collection"
  and "Washable Rugs, New 2025" copy. LLB uses them because its collection is only
  partly washable.
- `data/img_manifest.json` : which colourways have a cutout and a lifestyle shot,
  written by the asset export script
- `public/images/products/` : `{CODE}_cut.jpg` and `{CODE}_life.jpg`
- `public/images/logos/` : brand marks, recoloured rail variants, Think Rugs cover logo
- `public/downloads/` : the per brand product info Excel files
- `components/BrandBrochure.jsx` : the whole brochure as one client component
  (search, colour filter, Photographed only / trade price / selection toggles,
  selection persisted in localStorage per brand, CSV export, designs nav with
  scrollspy and counts, product pop up with gallery, swipe and keyboard support,
  click any gallery image to open a near full screen lightbox (its own prev/next,
  dots, swipe, Escape and arrow keys; Escape closes the lightbox first, then the
  product pop up), runners sorted to the bottom of size lists)
- `app/brochure.css` : the template CSS ported verbatim; theme values arrive as CSS
  variables set on the `.brochure` wrapper, so all three brands share one stylesheet
- `app/landing.css` : the landing page styles (lp prefixed to avoid class clashes)

## Routine jobs

### Adding photography

The direct route: put the new JPGs in a folder (or zip) and run

```
python3 scripts/add_images.py incoming_images
npm run build
```

It processes shots to the suite's standard sizes (cutouts fitted and white padded
to 690 x 920, lifestyles 760 wide), writes them to `public/images/products/`, and
updates `data/img_manifest.json`. It is safe to re run (existing outputs are
skipped unless `--force` is passed) and it accepts three filename conventions:
`{CODE}_cut.jpg` / `{CODE}_life.jpg`, the legacy `{CODE}_CO1.jpg` / `{CODE}_L2.jpg`,
and the LLB photo library naming `LLB - {Design} {Colour}[ Rug]_{N}.jpg` where _1
is taken as the cutout, _2 as the lifestyle, and _1B / _3 to _5 are skipped as
alternates. Unmatched files are reported, not guessed. The Catherine Lansfield
photo library naming `{Design}_{Colour}_{N}.jpg` also matches (underscores read
as spaces, _2 is the flat cutout per the supplied batches); where the library
uses the workbook's Colour column rather than the marketing name (Blue for
Navy, Terracotta for Terra), the aliases stored on each colourway by
extract_cl.py resolve it. Blank or corrupt sources (such as an all black
export) are detected, reported and skipped.

Brands maintained in the legacy pipeline can still come through the asset export
instead:

```
python3 scripts/export_assets.py /path/to/legacy/project
npm run build
```

The export script decodes the image cache into `public/images/products/` and
refreshes `data/img_manifest.json`. New colourways appear automatically and the
Photographed only default keeps working (it is computed from the manifest).

### Refreshing product data

Replace `data/brand_data.json` (and the Excel files in `public/downloads/` if they
changed), then `npm run build`.

For House Llewelyn-Bowen specifically, the block is generated from the product
workbook rather than copied from the legacy project:

```
python3 scripts/extract_llb.py public/downloads/House_Llewelyn_Bowen_Product_Info.xlsx
npm run build
```

For Catherine Lansfield and Catherine Lansfield Kids, one supplied workbook
carries both collections and one script splits it and rebuilds both blocks:

```
python3 scripts/extract_cl.py source/Catherine_Lansfield_Product_Information.xlsx
npm run build
```

The split keys off the Description prefix ("CL Kids - ") because the workbook's
Range column mislabels most kids rows. Its other normalisation rules (marketing
colour names from the Description, construction and material splitting and
deduplication, workbook typo fixes, Turkiye spelling, shape and size cleanup,
feature chip normalisation, em dash cleanup) are documented at the top of the
script. It reports drafted copy and missing origins on every run: two Cameo
Floral colourways and Mermaid carry drafted ecommerce copy, design intros are
generated from workbook facts pending official copy, and Kelso Check, Larsson
Geo and Twilight Animals have no country of origin in the workbook (the
brochure hides empty spec rows). The slimmed per brand Excel downloads in
`public/downloads/` are values only splits of the same workbook.

The script merges only the `LLB` block and leaves the other brands alone. Its
normalisation rules (marketing colour names parsed from the Description column,
construction and materials split apart, Turkiye spelling, the 61 x 230 runner flag,
em dash cleanup) are documented at the top of the script. Note the workbook has no
ecommerce titles or descriptions for the six washable designs or Dolce Vita, so the
script carries drafted copy for those, along with all eleven design intros. Review
that copy, and replace it from the workbook once official copy exists.

The file in `public/downloads/` is a slimmed, values only copy of the supplied
master (single Product Data sheet, embedded thumbnail images, helper sheets and the
empty Thumbnail column removed), which took it from 15 MB to about 33 KB so the
customer download matches the other brands. The extractor reads either the slimmed
copy or the original master; if a new master arrives with embedded imagery, slim it
the same way before publishing it as the download.

## Notes carried over from the single file suite

- Selections persist in localStorage under `thinkrugs_{brand}_selection_2025`, per
  browser and per site origin.
- Harlequin's design headings are left aligned (a deliberate departure from the
  centred copy in the Harlequin brand notes, per client request; flag it at licensor
  approval).
- The real brand fonts (Kamerik 105, Gill Sans, Futura BT) still need licensing;
  Poppins, Hanken Grotesk and Jost substitute as before, loaded in one request in
  `app/layout.js`. LLB uses Cormorant Garamond for display and Jost for body, also
  substitutes, pending the brand's real typeface.
- The LLB (House Llewelyn-Bowen) logo at `public/images/logos/llb.png` is the official
  brand mark, an antique gold wordmark. It is rendered from the source vector PDF at
  `public/images/logos/source/house_llewelyn-bowen.pdf` by `scripts/llb_logo.py`, which
  writes both the cover mark (`llb.png`) and the rail mark (`llb_rail.png`). Gold reads
  on both the dark aubergine cover and the light cream rail, so the two outputs are the
  same transparent PNG. To refresh, drop a new PDF in that source folder and rerun the
  script.
- LLB has no photography yet, so every colourway shows the branded placeholder and
  the Photographed only toggle defaults off for that brochure (it is computed per
  brand). Add shots as `{CODE}_cut.jpg` / `{CODE}_life.jpg` plus manifest entries,
  the same as the other brands.
- The CSV export's Washable column is now derived from each design's features
  rather than hardcoded to Yes, since the LLB collection is only partly washable.
  The landing page stats are computed from the data, so they update on their own.
- The Catherine Lansfield brochure is organised by collection: designs are
  grouped Woven first then Washable (derived from construction by
  extract_cl.py), with group headings in the designs nav, group dividers in the
  catalogue, a Collection filter in the rail, and a Collection column in the
  CSV export. The grouping UI appears automatically for any brand whose designs
  carry two or more distinct `group` values in brand_data.json.
- All artwork requires licensor marketing approval before publication.
- Catherine Lansfield and Catherine Lansfield Kids (brand keys `Catherine Lansfield`
  and `CL Kids`) are wired in with empty catalogues: the landing tiles show
  "Collection to follow" and the brochures render with no products until their
  blocks in `data/brand_data.json` are populated (follow the `extract_llb.py`
  pattern when the product workbooks arrive). Their Excel download links are
  hidden until files exist in `public/downloads/` and are added to `getDownload`
  in `lib/catalogue.js`. Their theme `SUB`, `RAIL_SUB` and `BLURB` copy is
  drafted and should be replaced once collection details are confirmed.
- The Catherine Lansfield cover mark (`cl.png`) is a recoloured white on dark
  variant of the supplied packaging logo; the rail mark (`cl_rail.png`) keeps the
  original charcoal and grey. The Kids mark (`clkids.png`, same file as its rail
  variant) combines the two supplied reference logos, the coral lockup stacked
  above the kids COLLECTION line. Source TIFs live in
  `public/images/logos/source/`.
- The landing page lays brands out on a count aware grid (one row up to four
  brands, three by two at five or six, four by two at seven or eight) so the
  full set always fits one viewport without scrolling.
- Copy style: no em dashes or long hyphens anywhere, only commas, colons,
  parentheses and full stops.
