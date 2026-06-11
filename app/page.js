import Link from 'next/link';

export const metadata = { title: 'Think Rugs | Licensed Brands' };

const BRANDS = [
  { name: 'Scion Living',    href: '/scion-living',     logo: '/images/logos/scion.png',     bg: '#262626' },
  { name: 'Harlequin',       href: '/harlequin',        logo: '/images/logos/harlequin.png', bg: '#262624' },
  { name: 'Clarke & Clarke', href: '/clarke-and-clarke', logo: '/images/logos/clarke.png',   bg: '#1c1c1b' },
];

export default function Landing() {
  return (
    <div className="landing">
      <section className="lp-cover" id="top">
        <img className="lp-logo" src="/images/logos/thinkrugs_cover.jpg" alt="Think Rugs, for every home" />
        <p className="lp-eyebrow">Trade Presentation</p>
        <h1>Licensed Brands<span>Our licensed collections, each in its own interactive brochure</span></h1>
        <div className="lp-stats">
          <div className="lp-stat"><b>3</b><small>Brands</small></div>
          <div className="lp-stat"><b>91</b><small>Colourways</small></div>
          <div className="lp-stat"><b>462</b><small>Product Options</small></div>
        </div>
      </section>

      <div className="lp-intro" id="brands">
        <p className="lp-eyebrow">Licensed Collections</p>
        <h2>Select a brand to browse its brochure</h2>
        <p>Each brochure presents the brand&apos;s full range with imagery, designs, colourways, sizes, specifications and trade pricing.</p>
      </div>

      <main className="lp-grid-wrap">
        <div className="lp-grid">
          {BRANDS.map((b) => (
            <Link className="lp-card" href={b.href} key={b.name} aria-label={`${b.name}, open the brochure`}>
              <span className="lp-card-media" style={{ background: b.bg }}>
                <img src={b.logo} alt={`${b.name} logo`} />
              </span>
              <span className="lp-card-body">
                <h4>{b.name}</h4>
                <p>View brochure</p>
              </span>
            </Link>
          ))}
        </div>
      </main>

      <footer className="lp-footer">
        <img className="lp-logo" src="/images/logos/thinkrugs_cover.jpg" alt="Think Rugs, for every home" />
        <p>Think Rugs, Licensed Brands 2026. Prices shown in the brochures are trade prices in GBP and EUR.</p>
      </footer>
    </div>
  );
}
