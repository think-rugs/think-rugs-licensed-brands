'use client';

import { Fragment, useEffect, useMemo, useRef, useState, useCallback } from 'react';
import Link from 'next/link';
import { gbp, eur, slug } from '@/lib/catalogue';

/* SVG symbols shared by cards, placeholders and pick buttons */
function SvgDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true">
      <defs>
        <symbol id="rugPh" viewBox="0 0 100 130">
          <g fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round">
            <rect x="14" y="14" width="72" height="102" rx="6" />
            <rect x="28" y="30" width="44" height="70" rx="3" />
            <path d="M14 8 v-4 M30 8 v-4 M46 8 v-4 M62 8 v-4 M78 8 v-4 M86 8 v-4" />
            <path d="M14 122 v4 M30 122 v4 M46 122 v4 M62 122 v4 M78 122 v4 M86 122 v4" />
          </g>
        </symbol>
        <symbol id="iAdd" viewBox="0 0 24 24">
          <path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
        </symbol>
        <symbol id="iOn" viewBox="0 0 24 24">
          <path d="M5 12.5l4.5 4.5L19 7" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
        </symbol>
        <symbol id="iFilter" viewBox="0 0 24 24">
          <path d="M3 5.5h18M6.5 12h11M10 18.5h4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </symbol>
      </defs>
    </svg>
  );
}

const GLABELS = ['Cutout', 'Lifestyle', 'Detail'];

export default function BrandBrochure({ theme, data, downloadHref, selKey }) {
  /* ---------- flat indexes ---------- */
  const flat = useMemo(() => {
    const list = [];
    data.designs.forEach((d) => d.colourways.forEach((c) => list.push({ d, c })));
    return list;
  }, [data]);
  const byCode = useMemo(() => Object.fromEntries(flat.map((e) => [e.c.code, e])), [flat]);
  const allColours = useMemo(
    () => [...new Set(flat.map((e) => e.c.c1).filter(Boolean))].sort(),
    [flat]
  );
  const hasPhotography = useMemo(() => flat.some((e) => e.c.img.cut || e.c.img.life || e.c.img.detail), [flat]);
  // collection groups (e.g. Woven / Washable); grouping UI appears with two or more
  const groups = useMemo(() => {
    const g = [];
    data.designs.forEach((d) => { if (d.group && !g.includes(d.group)) g.push(d.group); });
    return g;
  }, [data]);
  const hasGroups = groups.length > 1;

  /* ---------- state ---------- */
  const [term, setTerm] = useState('');
  const [colour, setColour] = useState('');
  const [group, setGroup] = useState('');
  const [imgOnly, setImgOnly] = useState(hasPhotography);
  const [selOnly, setSelOnly] = useState(false);
  const [showTrade, setShowTrade] = useState(true);
  const [selected, setSelected] = useState(() => new Set());
  const [activeRange, setActiveRange] = useState(null);
  const [railOpen, setRailOpen] = useState(false);
  const [modalCode, setModalCode] = useState(null);
  const [gIdx, setGIdx] = useState(0);
  const [lightbox, setLightbox] = useState(false);
  const lastFocus = useRef(null);
  const orderRef = useRef([]);
  const touchX = useRef(null);

  /* selection persistence */
  useEffect(() => {
    try {
      const saved = localStorage.getItem(selKey);
      if (saved) setSelected(new Set(JSON.parse(saved)));
    } catch (e) {}
  }, [selKey]);
  const persist = (set) => {
    try {
      localStorage.setItem(selKey, JSON.stringify([...set]));
    } catch (e) {}
  };

  const toggleSelect = useCallback((code) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      persist(next);
      return next;
    });
  }, [selKey]); // eslint-disable-line react-hooks/exhaustive-deps

  /* if selection empties while "My selection only" is on, release the filter */
  useEffect(() => {
    if (selected.size === 0 && selOnly) setSelOnly(false);
  }, [selected, selOnly]);

  /* ---------- filtering ---------- */
  const matches = useCallback(
    (e) => {
      const { d, c } = e;
      const hay = (d.name + ' ' + (c.label || '') + ' ' + c.colour + ' ' + c.code + ' ' + c.title + ' ' + c.c1 + ' ' + c.c2).toLowerCase();
      return (
        (!term || hay.includes(term.trim().toLowerCase())) &&
        (!colour || c.c1 === colour || c.c2 === colour) &&
        (!group || !hasGroups || d.group === group) &&
        (!imgOnly || !!(c.img.cut || c.img.life || c.img.detail)) &&
        (!selOnly || selected.has(c.code))
      );
    },
    [term, colour, group, hasGroups, imgOnly, selOnly, selected]
  );

  const visible = useMemo(() => {
    const perDesign = new Map();
    const codes = [];
    data.designs.forEach((d) => {
      const vis = d.colourways.filter((c) => matches({ d, c }));
      perDesign.set(d.name, vis);
      vis.forEach((c) => codes.push(c.code));
    });
    return { perDesign, codes, shown: codes.length };
  }, [data, matches]);

  const clearFilters = () => {
    setTerm(''); setColour(''); setGroup(''); setImgOnly(hasPhotography); setSelOnly(false);
  };
  const clearSelection = () => {
    const next = new Set(); persist(next); setSelected(next);
  };

  /* ---------- scrollspy ---------- */
  useEffect(() => {
    const sections = [...document.querySelectorAll('section.range')];
    const spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) setActiveRange(en.target.dataset.range);
        });
      },
      { rootMargin: '-30% 0px -60% 0px' }
    );
    sections.forEach((s) => spy.observe(s));
    return () => spy.disconnect();
  }, [visible]);

  /* ---------- modal ---------- */
  const openProduct = useCallback(
    (code) => {
      if (!byCode[code]) return;
      orderRef.current = visible.codes.includes(code) ? visible.codes : flat.map((e) => e.c.code);
      if (!document.body.classList.contains('modal-open')) {
        lastFocus.current = document.activeElement;
        document.body.classList.add('modal-open');
      }
      setGIdx(0);
      setModalCode(code);
    },
    [byCode, visible, flat]
  );
  const closeModal = useCallback(() => {
    setModalCode(null);
    setLightbox(false);
    document.body.classList.remove('modal-open');
    if (lastFocus.current) lastFocus.current.focus();
  }, []);
  const stepProduct = (dir) => {
    const order = orderRef.current;
    const i = order.indexOf(modalCode);
    const next = order[(i + dir + order.length) % order.length];
    setGIdx(0);
    setModalCode(next);
  };

  const gImgs = useMemo(() => {
    if (!modalCode) return [];
    const { c } = byCode[modalCode];
    const list = [];
    if (c.img.cut) list.push({ src: c.img.cut, label: GLABELS[0] });
    if (c.img.life) list.push({ src: c.img.life, label: GLABELS[1] });
    if (c.img.detail) list.push({ src: c.img.detail, label: GLABELS[2] });
    return list;
  }, [modalCode, byCode]);
  const gStep = useCallback(
    (d) => {
      if (gImgs.length < 2) return;
      setGIdx((i) => (i + d + gImgs.length) % gImgs.length);
    },
    [gImgs.length]
  );

  useEffect(() => {
    if (!modalCode) return;
    const onKey = (e) => {
      if (e.key === 'Escape') {
        if (lightbox) setLightbox(false);
        else closeModal();
      }
      if (e.key === 'ArrowRight') gStep(1);
      if (e.key === 'ArrowLeft') gStep(-1);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [modalCode, gStep, closeModal, lightbox]);

  /* ---------- CSV export ---------- */
  const csvCell = (v) => {
    v = v == null ? '' : String(v);
    return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  };
  const exportSelection = () => {
    if (!selected.size) return;
    const head = ['Product Code', 'Variant Code', 'Description', 'Brand', 'Design',
      ...(hasGroups ? ['Collection'] : []), 'Colour', 'Washable',
      'Size (cm)', 'Wholesale Price (GBP)', 'RRP (GBP)', 'Wholesale Price (EUR)', 'RRP (EUR)'];
    const lines = [head.map(csvCell).join(',')];
    flat.forEach(({ d, c }) => {
      if (!selected.has(c.code)) return;
      c.sizes.forEach((s) => {
        lines.push([c.code, s.variant, c.title + ', ' + s.size, data.brand, (c.label || d.name),
          ...(hasGroups ? [d.group] : []), c.colour,
          d.features.includes('Washable') ? 'Yes' : 'No',
          s.size, s.trade, s.rrp, s.tradeEur, s.rrpEur].map(csvCell).join(','));
      });
    });
    const csv = '\ufeff' + lines.join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = data.brand.replace(/[^A-Za-z]+/g, '_') + '_My_Selection.csv';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 0);
  };

  /* ---------- styling vars from theme ---------- */
  const vars = {
    '--accent': theme.ACCENT, '--accent-text': theme.ACCENT_TEXT, '--accent-soft': theme.ACCENT_SOFT,
    '--accent-on-dark': theme.ACCENT_DARKBG, '--cover': theme.COVER, '--tint': theme.TINT,
    '--ink': theme.INK, '--line': theme.LINE, '--rail': theme.RAIL,
    '--body-font': theme.BODY_FONT, '--body-ls': theme.BODY_LS,
    '--display-font': theme.DISPLAY, '--display-weight': theme.DISPLAY_WEIGHT,
    '--display-ls': theme.DISPLAY_LS, '--display-tt': theme.DISPLAY_TT,
    '--selcount-ink': theme.SELCOUNT_INK,
  };

  const modalEntry = modalCode ? byCode[modalCode] : null;

  return (
    <div
      className={'brochure' + (showTrade ? '' : ' hide-trade')}
      data-align={theme.HEAD_ALIGN}
      style={vars}
    >
      <SvgDefs />

      <header className="cover" id="top" data-cover={theme.COVER_TONE || 'dark'}>
        <Link className="back" href="/">&larr; All licensed brands</Link>
        <img className="logo" src={`/images/logos/${theme.logo_key}.png`} alt={`${data.brand} logo`} />
        <p className="sub">{theme.SUB || 'Washable Rug Collection'}</p>
        <p className="season">New 2025</p>
        <a className="enter" href="#catalogue">View the collection</a>
        <p className="presented">Presented by Think Rugs</p>
      </header>

      <div className="wrap" id="catalogue">
        <aside className={'rail' + (railOpen ? ' rail--open' : '')} aria-label="Browse and filter">
          <div className="rail-head">
            <img className="brandmark" src={`/images/logos/${theme.logo_key}_rail.png`} alt={data.brand} />
            <button
              type="button"
              className="rail-toggle"
              aria-expanded={railOpen}
              aria-controls="rail-panel"
              aria-label={railOpen ? 'Close filters and designs' : 'Open filters and designs'}
              onClick={() => setRailOpen((o) => !o)}
            >
              <svg className="i-filter" aria-hidden="true"><use href="#iFilter" /></svg>
              <span className="rail-toggle-label">{railOpen ? 'Close' : 'Filters'}</span>
              {selected.size > 0 && <span className="selcount">{selected.size}</span>}
            </button>
          </div>

          <div className="rail-panel" id="rail-panel">
          <p className="sub">{theme.RAIL_SUB || 'Washable Rugs, New 2025'}</p>
          <Link className="allbrands" href="/">&larr; All licensed brands</Link>

          <h3>Find a product</h3>
          <div className="ctl">
            <label htmlFor="q">Search</label>
            <input id="q" type="search" placeholder="Design, colour or code"
              value={term} onChange={(e) => setTerm(e.target.value)} />
          </div>
          <div className="ctl">
            <label htmlFor="fcolour">Colour</label>
            <select id="fcolour" value={colour} onChange={(e) => setColour(e.target.value)}>
              <option value="">All colours</option>
              {allColours.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          {hasGroups && (
            <div className="ctl">
              <label htmlFor="fgroup">Collection</label>
              <select id="fgroup" value={group} onChange={(e) => setGroup(e.target.value)}>
                <option value="">All collections</option>
                {groups.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
          )}
          <label className="toggle">
            <input type="checkbox" checked={imgOnly} onChange={(e) => setImgOnly(e.target.checked)} /> Photographed only
          </label>
          <label className="toggle">
            <input type="checkbox" checked={showTrade} onChange={(e) => setShowTrade(e.target.checked)} /> Show trade prices
          </label>
          <label className="toggle">
            <input type="checkbox" checked={selOnly} onChange={(e) => setSelOnly(e.target.checked)} /> My selection only{' '}
            <span className={'selcount' + (selected.size === 0 ? ' empty' : '')}>{selected.size}</span>
          </label>
          {selected.size > 0 && (
            <button className="dl" type="button" onClick={exportSelection}>Export selection (CSV)</button>
          )}
          <div className="selrow">
            <button className="clear" onClick={clearFilters}>Clear filters</button>
            {selected.size > 0 && (
              <button className="clear" onClick={clearSelection}>Clear selection</button>
            )}
          </div>
          <p className="results">{visible.shown} of {flat.length} colourways shown</p>
          {downloadHref && (
            <a className="dl" href={downloadHref} download>Download full product info (Excel)</a>
          )}

          <h3>Designs</h3>
          <nav className="rlinks" aria-label="Designs">
            {data.designs.map((d, i) => {
              const vis = visible.perDesign.get(d.name).length;
              const heads = hasGroups && (i === 0 || data.designs[i - 1].group !== d.group);
              return (
                <Fragment key={d.name}>
                {heads && <span className="rgroup">{d.group}</span>}
                <a href={'#rg-' + slug(d.name)}
                  onClick={() => setRailOpen(false)}
                  className={'rlink' + (activeRange === d.name ? ' active' : '') + (vis ? '' : ' dimmed')}>
                  <span>{d.name}</span><small className="rcount">{vis}</small>
                </a>
                </Fragment>
              );
            })}
          </nav>
          </div>
        </aside>

        <main>
          <div className="pagehead">
            <h1>{data.brand}</h1>
            <p>{theme.BLURB}</p>
          </div>

          <div>
            {(() => { let lastGroup = null; return data.designs.map((d) => {
              const vis = visible.perDesign.get(d.name);
              if (!vis.length) return null;
              const variants = d.colourways.reduce((n, c) => n + c.sizes.length, 0);
              const startsGroup = hasGroups && d.group !== lastGroup;
              lastGroup = d.group;
              return (
                <section className={'range' + (startsGroup ? ' group-start' : '')} key={d.name} id={'rg-' + slug(d.name)} data-range={d.name}>
                  {startsGroup && <div className="group-divider"><h2>{d.group}</h2></div>}
                  <header className="range-head">
                    <div className="range-title">
                      <h2>{d.name}</h2>
                      <span className="range-count"><b>{vis.length}</b> colourways, {variants} product options</span>
                    </div>
                    <p className="intro">{d.intro}</p>
                    <p className="range-meta">
                      <b>{d.construction}</b> &middot; {d.materials}
                      <span className="range-from"> &middot; From <b>{gbp(d.fromTrade)}</b> trade</span>
                    </p>
                    <div className="feats">
                      {d.features.map((f) => <span className="feat" key={f}>{f}</span>)}
                    </div>
                  </header>
                  <div className="grid">
                    {vis.map((c) => {
                      const cardImg = c.img.cut || c.img.life;
                      const on = selected.has(c.code);
                      const fromT = Math.min(...c.sizes.map((s) => s.trade));
                      return (
                        <article
                          key={c.code}
                          className={'card' + (on ? ' selected' : '')}
                          tabIndex={0}
                          role="button"
                          aria-label={'View ' + c.title}
                          onClick={() => openProduct(c.code)}
                          onKeyDown={(e) => {
                            if ((e.key === 'Enter' || e.key === ' ') && e.target === e.currentTarget) {
                              e.preventDefault();
                              openProduct(c.code);
                            }
                          }}
                        >
                          <div className="card-media">
                            {cardImg ? (
                              <img loading="lazy" src={cardImg} alt={c.title + ' rug'} />
                            ) : (
                              <div className="ph">
                                <svg viewBox="0 0 100 130" aria-hidden="true"><use href="#rugPh" /></svg>
                                <span className="pt">Image to follow</span>
                              </div>
                            )}
                            <button
                              className="pick"
                              aria-pressed={on}
                              aria-label={(on ? 'Remove ' : 'Add ') + c.title + (on ? ' from' : ' to') + ' my selection'}
                              title={on ? 'Remove from my selection' : 'Add to my selection'}
                              onClick={(e) => { e.stopPropagation(); toggleSelect(c.code); }}
                            >
                              <svg className="i-add"><use href="#iAdd" /></svg>
                              <svg className="i-on"><use href="#iOn" /></svg>
                            </button>
                          </div>
                          <div className="card-body">
                            <span className="card-code">{c.label || d.name}</span>
                            <h4>{c.colour}</h4>
                            <p>{c.c1}{c.c2 && c.c2 !== c.c1 ? ' / ' + c.c2 : ''}</p>
                            <div className="card-foot">
                              <span>{c.sizes.length} sizes</span>
                              <span className="frm">From <b>{gbp(fromT)}</b> <i>trade</i></span>
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                </section>
              );
            }); })()}
          </div>
          {visible.shown === 0 && (
            <p className="no-results" style={{ display: 'block' }}>No products match the current filters.</p>
          )}
        </main>
      </div>

      <footer>
        {data.brand}, {theme.SUB || 'Washable Rug Collection'}, New 2025. Presented by Think Rugs.
        <br /><br />
        <span dangerouslySetInnerHTML={{ __html: theme.FOOTER }} />
      </footer>

      {modalEntry && (
        <div className="overlay open" onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}>
          <div className="modal">
            <div className="modal-pos">
              <div className="gal">
                <div
                  className="main"
                  onTouchStart={(e) => { touchX.current = e.touches[0].clientX; }}
                  onTouchEnd={(e) => {
                    if (touchX.current == null) return;
                    const dx = e.changedTouches[0].clientX - touchX.current;
                    if (Math.abs(dx) > 40) gStep(dx < 0 ? 1 : -1);
                    touchX.current = null;
                  }}
                >
                  {gImgs.length ? (
                    <>
                      <img src={gImgs[gIdx].src} alt={`Product image ${gIdx + 1} of ${gImgs.length}`}
                        className="zoomable" role="button" tabIndex={0}
                        aria-label="Open larger image"
                        onClick={(e) => { e.stopPropagation(); setLightbox(true); }}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setLightbox(true); } }} />
                      <span className="glabel">{gImgs[gIdx].label}</span>
                      {gImgs.length > 1 && (
                        <>
                          <button className="gnav prev" aria-label="Previous image"
                            onClick={(e) => { e.stopPropagation(); gStep(-1); }}>&larr;</button>
                          <button className="gnav next" aria-label="Next image"
                            onClick={(e) => { e.stopPropagation(); gStep(1); }}>&rarr;</button>
                          <div className="gdots">
                            {gImgs.map((_, i) => <i key={i} className={i === gIdx ? 'on' : ''} />)}
                          </div>
                          <span className="gcount">{gIdx + 1} / {gImgs.length}</span>
                        </>
                      )}
                    </>
                  ) : (
                    <div className="ph">
                      <svg viewBox="0 0 100 130" aria-hidden="true"><use href="#rugPh" /></svg>
                      <span className="pt">Image to follow</span>
                      <span className="pn">{modalEntry.c.title}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="info-side">
                <div className="info-scroll" key={modalCode}>
                  <div className="modal-nav">
                    <button onClick={() => stepProduct(-1)}>&larr; Previous</button>
                    <button onClick={() => stepProduct(1)}>Next &rarr;</button>
                  </div>
                  <span className="mcode">{modalEntry.c.code}</span>
                  <h3>{modalEntry.c.title}</h3>
                  <p className="mcols">
                    {modalEntry.c.c1}
                    {modalEntry.c.c2 && modalEntry.c.c2 !== modalEntry.c.c1 ? ' / ' + modalEntry.c.c2 : ''}
                  </p>
                  <button
                    className={'mpick' + (selected.has(modalCode) ? ' on' : '')}
                    aria-pressed={selected.has(modalCode)}
                    onClick={() => toggleSelect(modalCode)}
                  >
                    {selected.has(modalCode) ? '\u2713 In my selection' : '+ Add to my selection'}
                  </button>
                  <div className="feats">
                    {modalEntry.d.features.map((f) => <span className="feat" key={f}>{f}</span>)}
                  </div>
                  <table className="sizes">
                    <thead>
                      <tr>
                        <th>Size</th>
                        <th className="num col-ws">Trade &pound;</th>
                        <th className="num col-ws">Trade &euro;</th>
                        <th className="num">RRP &pound;</th>
                        <th className="num">RRP &euro;</th>
                      </tr>
                    </thead>
                    <tbody>
                      {modalEntry.c.sizes.map((s) => (
                        <tr key={s.variant}>
                          <td>{s.size} cm{s.shape === 'Circle' ? ' (circle)' : s.runner ? ' (runner)' : ''}</td>
                          <td className="num col-ws">{gbp(s.trade)}</td>
                          <td className="num col-ws">{eur(s.tradeEur)}</td>
                          <td className="num">{gbp(s.rrp)}</td>
                          <td className="num">{eur(s.rrpEur)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="trade-note">Trade prices are wholesale prices.</p>
                  <p className="desc">{modalEntry.c.desc}</p>
                  <div className="spec">
                    <div className="row"><span className="k">Design</span><span>{modalEntry.c.label || modalEntry.d.name}</span></div>
                    {modalEntry.d.construction && <div className="row"><span className="k">Construction</span><span>{modalEntry.d.construction}</span></div>}
                    {modalEntry.d.materials && <div className="row"><span className="k">Materials</span><span>{modalEntry.d.materials}</span></div>}
                    {modalEntry.d.pile && <div className="row"><span className="k">Pile height</span><span>{modalEntry.d.pile} cm</span></div>}
                    {modalEntry.d.origin && <div className="row"><span className="k">Country of origin</span><span>{modalEntry.d.origin}</span></div>}
                  </div>
                </div>
              </div>
              <button className="close" aria-label="Close" onClick={closeModal}>&times;</button>
            </div>
          </div>
        </div>
      )}

      {modalEntry && lightbox && gImgs.length > 0 && (
        <div className="lightbox open" onClick={(e) => { if (e.target === e.currentTarget) setLightbox(false); }}>
          <div
            className="lb-stage"
            onTouchStart={(e) => { touchX.current = e.touches[0].clientX; }}
            onTouchEnd={(e) => {
              if (touchX.current == null) return;
              const dx = e.changedTouches[0].clientX - touchX.current;
              if (Math.abs(dx) > 40) gStep(dx < 0 ? 1 : -1);
              touchX.current = null;
            }}
          >
            <img src={gImgs[gIdx].src} alt={`Product image ${gIdx + 1} of ${gImgs.length}`} />
            <span className="glabel">{gImgs[gIdx].label}</span>
            {gImgs.length > 1 && (
              <>
                <button className="gnav prev" aria-label="Previous image"
                  onClick={(e) => { e.stopPropagation(); gStep(-1); }}>&larr;</button>
                <button className="gnav next" aria-label="Next image"
                  onClick={(e) => { e.stopPropagation(); gStep(1); }}>&rarr;</button>
                <div className="gdots">
                  {gImgs.map((_, i) => <i key={i} className={i === gIdx ? 'on' : ''} />)}
                </div>
                <span className="gcount">{gIdx + 1} / {gImgs.length}</span>
              </>
            )}
          </div>
          <button className="lb-close" aria-label="Close larger image" onClick={() => setLightbox(false)}>&times;</button>
        </div>
      )}
    </div>
  );
}
