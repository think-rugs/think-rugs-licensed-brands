import Link from 'next/link';
import { getStats, getBrandCards } from '@/lib/catalogue';

export const metadata = { title: 'Think Rugs | Licensed Brands' };

// Number words for the subline, so the copy reads naturally as brands are added.
// Falls back to the digit beyond the planned range.
const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'];
const numberWord = (n) => (WORDS[n] ? WORDS[n][0].toUpperCase() + WORDS[n].slice(1) : String(n));

// Column count for the trellis grid. Four or fewer sit in a single row. Five or
// six balance as three by two. Seven or eight fill four by two. Every case lands
// inside one viewport, so the set is always visible without scrolling.
const columnsFor = (n) => (n <= 4 ? Math.max(n, 1) : n <= 6 ? 3 : 4);

export default function Landing() {
  const stats = getStats();
  const cards = getBrandCards();
  const cols = columnsFor(cards.length);
  return (
    <div className="landing">
      <header className="lp-canopy">
        <img className="lp-lockup" src="/images/logos/thinkrugs_cover.jpg" alt="Think Rugs, for every home" />
        <div className="lp-title">
          <p className="lp-eyebrow">Trade presentation</p>
          <h1>Licensed Brands</h1>
          <p className="lp-sub">{numberWord(stats.brands)} licensed collections, manufactured by Think Rugs. Select a brand to browse its brochure.</p>
        </div>
        <dl className="lp-meta" aria-label="Collection totals">
          <div><dt>Brands</dt><dd>{stats.brands}</dd></div>
          <div><dt>Colourways</dt><dd>{stats.colourways}</dd></div>
          <div><dt>Product options</dt><dd>{stats.options}</dd></div>
        </dl>
      </header>

      <main className="lp-doors" id="brands" data-count={cards.length} style={{ '--cols': cols }}>
        {cards.map((b) => (
          <Link className="lp-door" key={b.key} href={b.href} data-tone={b.tone}
            style={{ background: b.bg, color: b.ink, ...(b.logoWidth ? { '--logo-w': b.logoWidth } : {}) }}
            aria-label={b.designs > 0
              ? `${b.name}, ${b.designs} designs, ${b.colourways} colourways, open the brochure`
              : `${b.name}, collection to follow, open the brochure`}>
            <span className="lp-door-logo"><img src={b.logo} alt={`${b.name} logo`} /></span>
            <span className="lp-door-foot">
              <h2>{b.name}</h2>
              <p className="lp-door-meta">
                {b.designs > 0 ? `${b.designs} designs, ${b.colourways} colourways` : 'Collection to follow'}
              </p>
              <p className="lp-door-cta">View brochure</p>
            </span>
          </Link>
        ))}
      </main>

      <footer className="lp-base">
        <p>Think Rugs, Licensed Brands 2026. Prices shown in the brochures are trade prices in GBP and EUR.</p>
      </footer>
    </div>
  );
}
