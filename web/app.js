/* Rhythm SIP prototype: one guided flow. Each step moves on by itself once its checks pass
   (a visible countdown on the Next button; tap the pause button, or touch the page, to stay).
   The server does the thinking: the AI only reads; rules decide and verify; the user confirms. */
(() => {
'use strict';

// ------------------------------------------------------------------ helpers
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const sleep = ms => new Promise(r => setTimeout(r, ms));

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false || kid === '') continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

const P = (d, w = 2.2) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
const ICONS = {
  pulse: P('<path d="M3 12h3l3-7 4 14 3-7h5"/>'),
  arrow: P('<path d="M5 12h14M13 6l6 6-6 6"/>'),
  back: P('<path d="M19 12H5M11 6l-6 6 6 6"/>'),
  pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1.5"/><rect x="14" y="5" width="4" height="14" rx="1.5"/></svg>',
  check: P('<path d="M5 12.5l4.2 4.2L19 7"/>', 2.8),
  cross: P('<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>', 2.8),
  moved: P('<path d="M4 12h12M12 7l5 5-5 5"/>', 2.6),
  life: P('<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3.5"/><path d="M6 6l3.5 3.5M18 6l-3.5 3.5M6 18l3.5-3.5M18 18l-3.5-3.5"/>', 1.8),
  dash: P('<path d="M7 12h10"/>', 2.8),
  lock: P('<rect x="5" y="11" width="14" height="9" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'),
  chat: P('<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>'),
  eye: P('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'),
  rules: P('<path d="M4 6h16M4 12h10M4 18h7"/><path d="M15 17l2 2 4-4"/>'),
  hand: P('<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/>'),
  alert: P('<path d="M12 7.5v6M12 17h.01"/>', 2.8),
  info: P('<path d="M12 11v6M12 7.5h.01"/>', 2.8),
  shield: P('<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>'),
};
function icon(name, size = 16) {
  const t = document.createElement('template');
  t.innerHTML = (ICONS[name] || ICONS.dash).replace('<svg', `<svg width="${size}" height="${size}" aria-hidden="true" focusable="false"`);
  return t.content.firstChild;
}
function fillIcons(root = document) {
  $$('[data-icon]', root).forEach(el => {
    if (el.dataset.done) return;
    el.append(icon(el.dataset.icon, +el.dataset.size || (el.classList.contains('mark') ? 19 : 16)));
    el.dataset.done = '1';
  });
}

// safe "markdown-lite": [label](https://…), **bold**, *italic*, "- " bullets. Builds DOM nodes, never innerHTML.
function rich(text) {
  const frag = document.createDocumentFragment(), rx = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let last = 0, m;
  while ((m = rx.exec(text))) {
    if (m.index > last) frag.append(text.slice(last, m.index));
    if (m[1]) frag.append(h('a', { href: m[2], target: '_blank', rel: 'noopener noreferrer' }, m[1]));
    else if (m[3]) frag.append(h('b', null, m[3]));
    else frag.append(h('em', null, m[4]));
    last = rx.lastIndex;
  }
  if (last < text.length) frag.append(text.slice(last));
  return frag;
}
function richBlock(text) {
  const wrap = h('div', { class: 'rich' });
  let ul = null;
  for (const raw of String(text || '').split(/\n+/)) {
    const line = raw.trim();
    if (!line) continue;
    if (/^[-•]\s+/.test(line) || /^\*\s+/.test(line)) {
      if (!ul) { ul = h('ul'); wrap.append(ul); }
      ul.append(h('li', null, rich(line.replace(/^[-•*]\s+/, ''))));
    } else { ul = null; wrap.append(h('p', null, rich(line))); }
  }
  return wrap;
}

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const D = s => { const [y, m, d] = String(s).slice(0, 10).split('-').map(Number); return new Date(y, m - 1, d); };
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const fmt = d => `${DOW[d.getDay()]} ${d.getDate()} ${MON[d.getMonth()]}`;
const ord = n => n + ((n % 100 >= 11 && n % 100 <= 13) ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'));
const inr = n => Number(n).toLocaleString('en-IN');
const range = (a, b) => Array.from({ length: Math.max(0, b - a + 1) }, (_, k) => a + k);

async function api(path, data) {
  const opt = data ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) } : {};
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

// ------------------------------------------------------------------ state + navigation
const SLIDES = [
  { id: 'intro', label: 'Start' },
  { id: 'setup', label: 'Your words' },
  { id: 'rhythm', label: 'Your rhythm', needsPlan: true },
  { id: 'replay', label: 'Six months', needsPlan: true, dark: true },
  { id: 'checkin', label: 'Check-in', needsPlan: true },
  { id: 'lifeline', label: 'Lifelines', needsPlan: true },
  { id: 'learn', label: 'Learning', needsPlan: true },
  { id: 'trust', label: "How it's checked", dark: true },
];
const S = { i: 0, run: 0, plan: null, cfg: null, lifelines: 2, auto: null, ci: {}, learn: null };
const slideEl = k => document.getElementById('s-' + SLIDES[k].id);
const alive = run => run === S.run;
const wait = (ms, run) => new Promise(res => setTimeout(() => res(alive(run)), REDUCED ? Math.min(ms, 80) : ms));

function go(i, opts = {}) {
  if (i < 0 || i >= SLIDES.length) return;
  if (SLIDES[i].needsPlan && !S.plan) i = 1;
  if (i === S.i && !opts.force) return;
  cancelAuto();
  S.resume = null;
  const from = S.i, prev = slideEl(from), next = slideEl(i);
  S.run++;
  if (from !== i) {
    prev.classList.remove('is-active');
    prev.classList.toggle('is-past', i > from);
    prev.classList.toggle('is-future', i < from);
    prev.inert = true;
    prev.setAttribute('aria-hidden', 'true');
  }
  next.classList.add('no-tr');                       // start the incoming slide on the side it comes from
  next.classList.remove('is-past', 'is-future', 'is-active');
  next.classList.add(i >= from ? 'is-future' : 'is-past');
  void next.offsetWidth;
  next.classList.remove('no-tr', 'is-future', 'is-past');
  next.classList.add('is-active');
  next.inert = false;
  next.removeAttribute('aria-hidden');
  next.scrollTop = 0;
  document.body.classList.toggle('is-dark', !!SLIDES[i].dark);
  S.i = i;
  renderNav();
  try { history.replaceState(null, '', '#' + SLIDES[i].id); } catch (e) { /* file:// */ }
  $('#live').textContent = `Step ${i + 1} of ${SLIDES.length}: ${SLIDES[i].label}`;
  ENTER[SLIDES[i].id](S.run);
}

function autoNext(ms, run) {
  if (!alive(run) || S.i >= SLIDES.length - 1) return;
  cancelAuto();
  const btn = $('#next'), seg = $$('.step')[S.i];
  for (const el of [btn, seg]) { el.style.setProperty('--ms', ms + 'ms'); el.classList.remove('counting'); }
  void btn.offsetWidth;
  btn.classList.add('counting');
  seg.classList.add('counting');
  btn.disabled = false;
  $('#nextLbl').textContent = 'Next: ' + SLIDES[S.i + 1].label;
  $('#stay').hidden = false;
  S.auto = setTimeout(() => { S.auto = null; if (alive(run)) go(S.i + 1); }, ms);
}
function cancelAuto() {
  clearTimeout(S.auto);
  S.auto = null;
  $('#next').classList.remove('counting');
  $$('.step').forEach(s => s.classList.remove('counting'));
  $('#stay').hidden = true;
  renderBar();
}

function buildSteps() {
  const nav = $('#steps');
  SLIDES.forEach((s, k) => nav.append(h('button', { class: 'step', type: 'button', 'aria-label': `Step ${k + 1}: ${s.label}`, onclick: () => go(k) },
    h('i'), h('span', { class: 'tip' }, s.label))));
}
function renderNav() {
  $$('.step').forEach((el, k) => {
    el.classList.toggle('done', k < S.i);
    el.classList.toggle('active', k === S.i);
    el.disabled = !!SLIDES[k].needsPlan && !S.plan;
    if (k === S.i) el.setAttribute('aria-current', 'step'); else el.removeAttribute('aria-current');
  });
  renderBar();
}
function renderBar() {
  $('#back').style.visibility = S.i === 0 ? 'hidden' : 'visible';
  $('#where').replaceChildren(h('b', null, `${S.i + 1} / ${SLIDES.length}`), SLIDES[S.i].label);
  if (S.auto) return;
  const last = S.i === SLIDES.length - 1;
  $('#nextLbl').textContent = last ? 'Start over' : S.i === 0 ? 'Start' : 'Next';
  $('#next').disabled = S.i === 1 && !S.plan;
}

function note(target, tone, text, extra) {
  const box = typeof target === 'string' ? $(target) : target;
  const el = h('div', { class: `note ${tone} pop` },
    h('span', { class: 'ni' }, icon(tone === 'ok' ? 'check' : tone === 'warn' ? 'alert' : 'info', 14)),
    h('div', null, richBlock(text), extra ? h('div', { class: 'rc-m', style: 'margin-top:6px' }, extra) : null));
  box.append(el);
  return el;
}
// glide the active step so new content comes into view (a smooth scroll, never a jump)
function reveal(el, pad = 28) {
  const sl = slideEl(S.i);
  if (!el || !sl.contains(el)) return;
  setTimeout(() => {
    const r = el.getBoundingClientRect(), s = sl.getBoundingClientRect();
    const below = r.bottom - (s.bottom - pad), above = r.top - (s.top + pad);
    if (below > 0) sl.scrollBy({ top: Math.min(below, Math.max(0, above)), behavior: REDUCED ? 'auto' : 'smooth' });
  }, 90);
}

// ------------------------------------------------------------------ 1. intro: the rhythm line
const HERO = [['Jun', 2], ['Jul', 1], ['Aug', 6], ['Sep', 3], ['Oct', 2]];
const hpos = d => `${((d - 1) / 29) * 100}%`;
const TICKS = [['Stipend 1st–3rd', 'SIP on the 6th'], ['Salary on the last working day', 'SIP on the 5th'],
  ['Clients pay 5th–20th', 'waits for your tap'], ['Paid on the 7th, always', 'keeps your date'],
  ['salary mahine ke last mein', 'SIP on the 5th'], ['Payout every Monday', 'after the first payout']];

function buildIntro() {
  const tr = $('#hvTrack');
  [1, 5, 10, 15, 20, 25, 30].forEach(d => tr.append(h('span', { class: 'hv-tick', style: `left:${hpos(d)}` }, ord(d))));
  $('#hvFixed').style.left = hpos(5);
  const items = TICKS.map(([a, b]) => h('span', { class: 'tk' }, h('b', null, a), '   →   ', h('i', null, b)));
  $('#ticker').append(...items, ...items.map(x => x.cloneNode(true)));
}
async function setHero(month, day, run) {
  const m = $('#hvMonth'), coin = $('#hvCoin'), sip = $('#hvSip'), fx = $('#hvFixed'), st = $('#hvStatus');
  m.classList.add('flip');
  await sleep(220);
  m.textContent = month;
  m.classList.remove('flip');
  coin.style.left = hpos(day);
  coin.classList.toggle('edge', day <= 3);
  $('#hvCoinLbl').textContent = 'Money in · ' + ord(day);
  fx.classList.remove('fail');
  st.className = 'hv-status';
  st.replaceChildren('Fixed date, 5th');
  await sleep(420);
  sip.style.left = hpos(day + 1);
  sip.classList.toggle('edge', day + 1 <= 3);
  $('#hvSipLbl').textContent = 'Rhythm SIP · ' + ord(day + 1);
  await sleep(700);
  if (!alive(run)) return;
  const bad = day >= 5;
  fx.classList.toggle('fail', bad);
  st.className = 'hv-status ' + (bad ? 'bad' : 'ok');
  st.replaceChildren(icon(bad ? 'cross' : 'check', 13), bad ? 'Fixed date, 5th: bounced' : 'Fixed date, 5th: fine this month');
}
async function enterIntro(run) {
  let k = 0;
  while (alive(run)) {
    const [m, d] = HERO[k++ % HERO.length];
    setHero(m, d, run);
    if (!(await wait(2900, run))) return;
  }
}

// ------------------------------------------------------------------ 2. setup: your words → verified plan
const VLINES = ['Reading your words', 'Choosing a date that comes after your money', 'Testing it on the next 6 real months', 'Setting up the monthly check-in'];
const PH = ['My stipend comes on the 1st, sometimes the 3rd', 'salary mahine ke last mein aati hai', 'Clients pay me between the 5th and 20th', 'Uber payout every Tuesday'];

function buildSetup() {
  const sel = $('#currentDay');
  range(1, 28).forEach(d => sel.append(h('option', { value: d }, `the ${ord(d)}`)));
  sel.value = 5;
  $('#setupForm').addEventListener('submit', e => {
    e.preventDefault();
    const t = $('#setupInput').value.trim();
    if (!t) { $('#setupInput').focus(); return; }
    const ex = (S.cfg ? S.cfg.examples : []).find(x => x.text === t);
    submitSetup(t, ex ? ex.id : null);
  });
  $$('#fbSeg button').forEach(b => b.addEventListener('click', () => pickPattern(b.dataset.p)));
  $('#fbGo').addEventListener('click', submitManual);
}
function buildExamples() {
  const box = $('#exampleChips');
  box.replaceChildren();
  (S.cfg ? S.cfg.examples : []).forEach(ex => box.append(h('button', { class: 'chip', type: 'button', onclick: () => pickExample(ex) },
    h('b', null, ex.label), h('span', null, ex.hint))));
}
async function typePlaceholder(run) {
  const inp = $('#setupInput');
  for (let k = 0; alive(run); k++) {
    const t = PH[k % PH.length];
    for (let i = 1; i <= t.length; i++) { if (!alive(run)) return; inp.placeholder = t.slice(0, i); await sleep(30); }
    if (!(await wait(1800, run))) return;
    for (let i = t.length; i >= 0; i -= 2) { if (!alive(run)) return; inp.placeholder = t.slice(0, i); await sleep(12); }
  }
}
function enterSetup(run) {
  if (!S.plan && $('#verify').hidden) setTimeout(() => alive(run) && $('#setupInput').focus({ preventScroll: true }), 900);
  typePlaceholder(run);
}
async function pickExample(ex) {
  const run = S.run, inp = $('#setupInput');
  if (ex.sip) $('#currentDay').value = ex.sip;
  inp.value = '';
  for (const ch of ex.text) { inp.value += ch; if (!(await wait(11, run))) return; }
  submitSetup(ex.text, ex.id);
}
function vline(title) {
  return h('li', { class: 'v' }, h('span', { class: 'vi' }), h('div', null, h('div', { class: 'vt' }, title), h('div', { class: 'vd' }), h('div', { class: 'vm' })));
}
function setLine(li, state, title, detail, meta) {
  li.className = 'v ' + (state || '');
  const vi = $('.vi', li);
  vi.replaceChildren();
  if (state === 'ok') vi.append(icon('check', 16)); else if (state === 'warn') vi.append(icon('alert', 16));
  if (title) $('.vt', li).textContent = title;
  const vd = $('.vd', li);
  vd.replaceChildren();
  if (detail) vd.textContent = detail; else if (state === 'on') vd.append(h('span', { class: 'shimmer' }));
  $('.vm', li).textContent = meta || '';
}
function showVerifying(quote) {
  $('#setupExtras').classList.add('shut');
  $('#verify').hidden = false;
  $('#vQuote').textContent = quote;
  const list = $('#vlist');
  list.replaceChildren(...VLINES.map(vline));
  setLine(list.firstChild, 'on');
  $('#vNotes').replaceChildren();
  $('#vFoot').replaceChildren();
  $('#fallback').hidden = true;
  reveal(list);
}
async function submitSetup(text, exampleId) {
  const run = S.run;
  cancelAuto();
  showVerifying(`“${text}”`);
  let res;
  try { res = await api('/api/plan', { text, example: exampleId, current_day: +$('#currentDay').value }); }
  catch (e) { res = { status: 'fallback', reason: 'network', message: "Couldn't reach the server. Check your connection, or pick the closest pattern." }; }
  if (alive(run)) resolvePlan(res, run);
}
async function resolvePlan(res, run) {
  const lines = $$('#vlist .v');
  if (!res || res.status !== 'ok') {                     // visible fallback: the user picks, the rules still verify
    const meta = res && res.reason === 'unsure' && res.confidence != null ? `${Math.round(res.confidence * 100)}% sure, below the 60% bar` : '';
    setLine(lines[0], 'warn', null, (res && res.message) || 'Something went wrong.', meta);
    if (res && res.decline) note('#vNotes', 'info', res.decline, 'Advice requests are always declined. Rhythm only changes when money moves, never where.');
    showFallback();
    reveal($('#fallback'));
    return;
  }
  S.plan = res;
  S.lifelines = 2;
  if (res.decline) note('#vNotes', 'info', res.decline, 'Advice requests are always declined. Rhythm only changes when money moves, never where.');
  for (let k = 0; k < res.verify.length; k++) {
    const v = res.verify[k];
    if (k > 0) { setLine(lines[k], 'on'); if (!(await wait(620, run))) return; }
    setLine(lines[k], v.passed ? 'ok' : 'warn', v.title, v.detail, v.meta || '');
    reveal(lines[k]);
    if (!(await wait(160, run))) return;
  }
  renderNav();
  if (!res.plan.passed) {
    note('#vNotes', 'warn', "A rule check didn't pass, so nothing is set up. Describe your payday differently, or pick the closest pattern.");
    S.plan = null;
    renderNav();
    showFallback();
    return;
  }
  $('#vFoot').replaceChildren(h('span', { class: 'stamp' }, icon('check', 14), 'Verified by the rules'),
    h('button', { class: 'linkbtn', type: 'button', onclick: editSetup }, 'Change my answer'));
  reveal($('#vFoot'));
  if (await wait(500, run)) autoNext(3000, run);
}
function editSetup() {
  cancelAuto();
  $('#verify').hidden = true;
  $('#setupExtras').classList.remove('shut');
  const inp = $('#setupInput');
  inp.focus();
  inp.select();
}
function showFallback() {
  const fb = $('#fallback');
  fb.hidden = false;
  fb.classList.remove('pop');
  void fb.offsetWidth;
  fb.classList.add('pop');
  S.fb = null;
  $$('#fbSeg button').forEach(b => b.setAttribute('aria-pressed', 'false'));
  $('#fbDays').replaceChildren();
  $('#fbGo').disabled = true;
}
function daySelect(id, val) {
  const s = h('select', { id, 'aria-label': 'Day' });
  range(1, 31).forEach(d => s.append(h('option', { value: d }, ord(d))));
  s.value = val;
  return s;
}
function pickPattern(p) {
  S.fb = p;
  $$('#fbSeg button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.p === p)));
  const box = $('#fbDays');
  box.replaceChildren();
  if (p === 'fixed_date') box.append('Money comes on the', daySelect('fbLo', 1));
  else if (p === 'date_window') box.append('From the', daySelect('fbLo', 1), 'to the', daySelect('fbHi', 3));
  else if (p === 'weekly') {
    const s = h('select', { id: 'fbWd', 'aria-label': 'Weekday' });
    ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].forEach(w => s.append(h('option', { value: w }, w[0].toUpperCase() + w.slice(1))));
    box.append('Paid every', s);
  } else if (p === 'last_working_day') box.append('Salary lands on the last working day of the month.');
  else box.append('No fixed date: the SIP will wait for your tap.');
  $('#fbGo').disabled = false;
}
async function submitManual() {
  if (!S.fb) return;
  const run = S.run, val = id => { const el = document.getElementById(id); return el ? el.value : null; };
  const manual = { pattern: S.fb, lo: +val('fbLo') || null, hi: +(val('fbHi') || val('fbLo')) || null, weekday: val('fbWd') };
  showVerifying('Set by you');
  let res;
  try { res = await api('/api/plan', { manual, current_day: +$('#currentDay').value }); }
  catch (e) { res = { status: 'fallback', message: "Couldn't reach the server." }; }
  if (alive(run)) resolvePlan(res, run);
}

// ------------------------------------------------------------------ 3. rhythm: the calendar lights up
const MINI = { sip: 'SIP', debit: 'taken', checkin: 'check-in', tap: 'tap', invest: 'SIP', end: 'ends' };
function buildCalendar(p) {
  const c = p.calendar, el = $('#cal');
  el.classList.remove('in');
  el.replaceChildren(h('div', { class: 'cal-h' }, h('b', null, c.title), h('span', null, 'Weekends in grey · holidays ignored')));
  const g = h('div', { class: 'cal-g' });
  ['M', 'T', 'W', 'T', 'F', 'S', 'S'].forEach(x => g.append(h('div', { class: 'dow' }, x)));
  const end = D(c.end);
  for (let d = D(c.start), k = 0; d <= end; d = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1), k++) {
    const out = d.getMonth() !== c.month - 1, we = d.getDay() === 0 || d.getDay() === 6;
    g.append(h('div', { class: 'day' + (out ? ' out' : '') + (we ? ' we' : ''), 'data-date': iso(d), style: `--k:${k}`, title: fmt(d) },
      out ? h('span', { class: 'om' }, MON[d.getMonth()]) : null, h('span', { class: 'n' }, d.getDate()), h('span', { class: 'mini' })));
  }
  el.append(g);
}
function enterRhythm(run) {
  const p = S.plan;
  $('#rhTitle').textContent = p.rhythm.title;
  $('#rhSub').textContent = p.rhythm.sub;
  buildCalendar(p);
  $('#legend').replaceChildren(...p.rhythm.legend.map(it => h('li', { class: 'lgd' }, h('span', { class: 'sw hl-' + it.kind }),
    h('div', null, h('div', { class: 'w' }, it.when), h('div', { class: 't' }, it.what)))));
  (async () => {
    if (!(await wait(520, run))) return;
    $('#cal').classList.add('in');
    if (!(await wait(800, run))) return;
    const items = $$('#legend .lgd');
    for (let k = 0; k < items.length; k++) {
      items.forEach(x => x.classList.remove('now'));
      items[k].classList.add('on', 'now');
      const it = p.rhythm.legend[k];
      it.dates.forEach(d => {
        const cell = $(`#cal .day[data-date="${d}"]`);
        if (!cell) return;
        cell.classList.add('hl-' + it.kind);
        if (MINI[it.kind]) $('.mini', cell).textContent = MINI[it.kind];
      });
      if (!(await wait(1100, run))) return;
    }
    items.forEach(x => x.classList.remove('now'));
    autoNext(7000, run);
  })();
}

// ------------------------------------------------------------------ 4. replay: six months, two SIPs
const STATUS = { invested: ['check', 'Invested'], bounced: ['cross', 'Bounced'], cancelled: ['dash', 'Cancelled'],
  moved: ['moved', 'Moved'], lifeline: ['life', 'Lifeline used'], missed: ['dash', 'Skipped'] };
function pct(dateStr, y, m) {
  if (!dateStr) return null;
  const d = D(dateStr), at = d.getFullYear() * 12 + d.getMonth(), cur = y * 12 + m - 1;
  if (at < cur) return 1.5;
  if (at > cur) return 98.5;
  return 3 + (d.getDate() - 1) * (94 / 30);
}
const short = d => `${DOW[d.getDay()]} ${d.getDate()}`;
function buildMonths(r) {
  const g = $('#mgrid');
  g.replaceChildren(h('div', { class: 'lab' }, h('div'), h('div', null, 'Fixed date'), h('div', { class: 'lab-r' }, 'Rhythm SIP')));
  r.months.forEach(mo => {
    const money = pct(mo.money.date, mo.year, mo.month), md = D(mo.money.date);
    const moneyTxt = md.getMonth() + 1 !== mo.month ? fmt(md) : short(md);
    const cell = (lane, x) => {
      const mv = x.status === 'moved', bad = x.status === 'bounced' || x.status === 'cancelled';
      const take = pct(x.date, mo.year, mo.month), from = mv ? pct(x.planned, mo.year, mo.month) : take;
      const [ic, word] = STATUS[x.status] || ['dash', x.status];
      const dd = x.date ? D(x.date) : null;
      const sub = x.status === 'bounced' ? `₹${inr(r.fee)} bank charge` : mv && dd ? `to ${short(dd)}` : dd ? `taken ${short(dd)}` : '';
      const marks = [h('i', { class: 'mk money', style: `left:${money}%` })];
      if (mv) marks.push(h('i', { class: 'trail', style: `left:${from}%;width:${Math.max(0, take - from)}%` }));
      if (take != null) marks.push(h('i', { class: 'mk take', style: `left:${from}%`, 'data-to': take }));
      return h('div', { class: `cell ${lane}${bad ? ' bad' : ''}${mv ? ' mv' : ''}`, title: x.text },
        h('div', { class: 'mt' }, marks), h('div', { class: 'st ' + x.status }, icon(ic, 14), h('span', null, word, sub ? h('small', null, sub) : null)));
    };
    g.append(h('div', { class: 'mcol' }, h('div', { class: 'mh' }, h('b', null, mo.label), h('span', null, h('i', { class: 'k-dot' }), moneyTxt)),
      cell('f', mo.fixed), cell('r', mo.rhythm)));
  });
}
function tick(sel, to, money) {
  const el = $(sel), from = +el.dataset.v || 0;
  el.dataset.v = to;
  if (from === to) return;
  const t0 = performance.now(), dur = 520;
  const step = t => {
    const p = Math.min(1, (t - t0) / dur), v = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
    el.textContent = money ? inr(v) : v;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
  const n = el.closest('.tl-n');
  if (n) { n.classList.remove('bump'); void n.offsetWidth; n.classList.add('bump'); }
}
function enterReplay(run) {
  const r = S.plan.replay;
  $('#rpStory').textContent = r.story;
  $('#tfL').textContent = r.fixed_label;
  $('#trL').textContent = r.rhythm_label;
  ['#tfN', '#tfB', '#tfF', '#trN', '#trM'].forEach(s => { $(s).textContent = '0'; $(s).dataset.v = 0; });
  $('#rpSummary').textContent = r.summary;
  $('#rpFine').textContent = `Illustrative bank charge: ₹${inr(r.fee)} per failed auto-debit (₹500 + 18% GST). Groww itself charges nothing. "Moved" months assume the check-in was answered. Bank holidays ignored.`;
  $('#rpSummary').classList.remove('in');
  $('#rpFine').classList.remove('in');
  buildMonths(r);
  (async () => {
    if (!(await wait(900, run))) return;
    const t = { fi: 0, fb: 0, ri: 0, rm: 0 };
    const cols = $$('#mgrid .mcol');
    for (let k = 0; k < cols.length; k++) {
      const mo = r.months[k], col = cols[k];
      col.classList.add('in');
      if (!(await wait(260, run))) return;
      $('.mh', col).classList.add('in');
      $$('.mk.money', col).forEach(x => x.classList.add('in'));
      if (!(await wait(320, run))) return;
      $('.cell.f', col).classList.add('in');
      if (mo.fixed.status === 'invested') t.fi++;
      if (mo.fixed.status === 'bounced') t.fb++;
      tick('#tfN', t.fi); tick('#tfB', t.fb); tick('#tfF', t.fb * r.fee, true);
      if (!(await wait(320, run))) return;
      const rc = $('.cell.r', col);
      rc.classList.add('in');
      const moved = mo.rhythm.status === 'moved';
      if (moved) setTimeout(() => { if (!alive(run)) return; rc.classList.add('shift'); const mk = $('.mk.take', rc); if (mk) mk.style.left = mk.dataset.to + '%'; }, 450);
      if (mo.rhythm.status === 'invested' || moved) t.ri++;
      if (moved) t.rm++;
      tick('#trN', t.ri); tick('#trM', t.rm);
      if (!(await wait(moved ? 1100 : 420, run))) return;
    }
    $('#rpSummary').classList.add('in');
    $('#rpFine').classList.add('in');
    reveal($('#replayAgain'));
    if (await wait(700, run)) autoNext(9000, run);
  })();
}

// ------------------------------------------------------------------ 5. check-in: the notification
function lifeChip() { $('#lifeChip').replaceChildren(icon('life', 15), `Lifelines left this year: ${S.lifelines} of 2`); }
function say(who, text) {
  $('#thread').append(h('div', { class: 'bub ' + who }, text));
  const pb = $('#phoneBody');
  setTimeout(() => pb.scrollTo({ top: pb.scrollHeight, behavior: REDUCED ? 'auto' : 'smooth' }), 60);
}
function rcRow(key, content, cls) {
  const rc = $('#readCard');
  rc.hidden = false;
  if (cls) $$('.rc-row.' + cls, rc).forEach(x => x.remove());
  const row = h('div', { class: 'rc-row on pop' + (cls ? ' ' + cls : '') }, h('div', { class: 'rc-k' }, key), h('div', { class: 'rc-v' }, content));
  rc.append(row);
  reveal(row);
  return row;
}
const rulesRow = content => { $$('#readCard .rc-row.you').forEach(x => x.remove()); return rcRow('Rules', content, 'rules'); };
const youRow = buttons => rcRow('You', h('div', { class: 'row' }, buttons), 'you');
const T = (title, body) => h('div', null, h('div', { class: 't' }, title), body ? h('div', null, body) : null);
function checksList(checks) {
  return h('div', { class: 'cks' }, checks.map(c => h('div', { class: 'ck' + (c.passed ? '' : ' no') }, h('span', { class: 'ci' }, icon(c.passed ? 'check' : 'alert', 11)), c.label)));
}
function answerBlock(r) {
  const kids = [richBlock(r.message)];
  if (r.kind === 'answer') kids.push(h('span', { class: 'badge ok' }, icon('check', 12), 'Safety check passed · official sources only'));
  else if (r.kind === 'decline') kids.push(h('span', { class: 'badge info' }, icon('shield', 12), 'Advice requests are always declined'));
  else kids.push(h('span', { class: 'badge warn' }, icon('alert', 12), r.kind === 'limit' ? 'AI limit reached' : 'Not sure, so it says so (safe fallback)'));
  if (r.sources && r.sources.length) kids.push(h('div', { class: 'srcs' }, 'Sources:', r.sources.map(s => h('a', { href: s.url, target: '_blank', rel: 'noopener noreferrer' }, s.title))));
  return h('div', null, kids);
}
function nudge() { const a = $('#nActions'); a.classList.remove('nudge'); void a.offsetWidth; a.classList.add('nudge'); }
function resetCheckinCard() { const rc = $('#readCard'); rc.replaceChildren(); rc.hidden = true; $$('#nActions button').forEach(b => b.classList.remove('sel')); }

function enterCheckin(run) {
  const c = S.plan.checkin;
  $('#ciTitle').textContent = c.title;
  $('#ciSub').textContent = c.sub;
  $('#lsDate').textContent = c.lock_date;
  $('#nTitle').textContent = c.notif.title;
  $('#nBody').textContent = c.notif.body;
  $('#nActions').replaceChildren(...c.actions.map(a => h('button', { type: 'button', 'data-id': a.id, onclick: () => ciAction(a.id, a.label) }, a.label)));
  $('#thread').replaceChildren();
  resetCheckinCard();
  $('#replyInput').value = '';
  $('#replyInput').placeholder = 'e.g. ' + c.examples[0];
  $('#replyChips').replaceChildren(...c.examples.map(t => h('button', { class: 'chip', type: 'button', onclick: () => { $('#replyInput').value = t; sendReply(t); } }, t)));
  lifeChip();
  S.ci = { busy: false };
  $('#notif').classList.remove('in');
  wait(850, run).then(ok => ok && $('#notif').classList.add('in'));
}
function ciAction(id, label) {
  const run = S.run, c = S.plan.checkin;
  if (S.ci.busy) return;
  cancelAuto();
  resetCheckinCard();
  $$('#nActions button').forEach(b => b.classList.toggle('sel', b.dataset.id === id));
  say('me', label);
  rcRow('You tapped', T(label, h('span', { class: 'rc-m' }, 'A button, so no AI is needed')), 'heard');
  if (id === 'yes') {
    finish(c.mode === 'one_tap' ? `Done. ₹${inr(c.amount)} will be invested on ${c.invest_txt}. Your bank also sends its standard notice the day before.`
      : `Great. Nothing changes: ₹${inr(c.amount)} goes on ${c.sip_txt}.`, run);
  } else if (id === 'notyet') finish("No problem. I'll ask again in 2 days. Nothing is taken before you tap yes.", run);
  else if (id === 'move') askDay(run, 'When will your money arrive this month?');
  else if (id === 'lifeline') confirmLifeline(run);
  else if (id === 'stop') confirmStop(run);
}
async function sendReply(text) {
  const run = S.run, c = S.plan.checkin;
  text = (text || '').trim();
  if (!text || S.ci.busy) return;
  cancelAuto();
  S.ci.busy = true;
  resetCheckinCard();
  say('me', text);
  const aiRow = rcRow('AI read', h('span', { class: 'shimmer' }), 'heard');
  let r;
  try { r = await api('/api/reply', { text, mode: c.mode, sip: c.sip, sip_day: S.plan.plan.sip_day, tap: c.tap }); }
  catch (e) { r = { kind: 'error', message: "Couldn't reach the server. The options in the notification still work." }; }
  S.ci.busy = false;
  if (!alive(run)) return;
  const v = $('.rc-v', aiRow);
  if (r.read) {
    const meta = r.read.rule ? 'Caught by the advice rule, before any AI' : `${Math.round(r.read.confidence * 100)}% sure` + (r.read.provider ? ` · read by ${r.read.provider}` : '');
    v.replaceChildren(h('div', { class: 't' }, r.read.text), h('div', { class: 'rc-m' }, meta));
  } else v.replaceChildren(h('div', null, 'Not read'));
  if (await wait(380, run)) outcome(r, run);
}
function outcome(r, run) {
  const c = S.plan.checkin;
  switch (r.kind) {
    case 'done': return finish(r.message, run);
    case 'propose_move':
      rulesRow(h('div', null, T(r.title, r.body), checksList(r.checks)));
      youRow([h('button', { class: 'pill primary sm', type: 'button', disabled: !r.passed, onclick: () => { say('me', 'Yes, move it'); finish(r.done, run); } }, 'Yes, move it'),
        h('button', { class: 'pill sm', type: 'button', onclick: resetCheckinCard }, 'Cancel')]);
      return say('app', `Move ${c.month}'s SIP to ${r.new_txt}? The money would be taken on ${r.taken_txt}.`);
    case 'ask_day': return askDay(run, r.message, r.days);
    case 'too_late':
      rulesRow(T('Too late to move within this month', r.message));
      return youRow([h('button', { class: 'pill primary sm', type: 'button', onclick: () => confirmLifeline(run) }, 'Use a Lifeline'),
        h('button', { class: 'pill sm', type: 'button', onclick: () => askDay(run, 'When will your money arrive this month?') }, 'Pick another day')]);
    case 'lifeline': return confirmLifeline(run);
    case 'stop': return confirmStop(run);
    case 'decline':
      rulesRow(h('div', null, richBlock(r.message), h('span', { class: 'badge info' }, icon('shield', 12), 'Advice is always declined: a rule check, then an AI check')));
      say('app', "I can't advise on funds or on whether to invest. I can help with when your SIP goes in.");
      return nudge();
    case 'answer': case 'fallback':
      rulesRow(answerBlock(r));
      say('app', r.kind === 'answer' ? 'Answered from official sources (shown alongside).' : "I'm not sure about that one, so I've shared where to get a reliable answer.");
      return nudge();
    default:
      rulesRow(T(r.kind === 'unclear' ? "I didn't catch that" : 'Fallback', r.message || 'Pick one of the options in the notification.'));
      return nudge();
  }
}
function askDay(run, msg, days) {
  const c = S.plan.checkin, sd = S.plan.plan.sip_day;
  days = days || range(Math.max(1, sd - 2), 26);
  rulesRow(h('div', null, T(msg), h('div', { class: 'rc-m' }, `Pick the day your ${c.noun} will arrive. The rules work out a safe new date.`),
    h('div', { class: 'days' }, days.map(d => h('button', { type: 'button', 'aria-label': `the ${ord(d)}`, onclick: () => pickDay(d, run) }, d)))));
}
async function pickDay(d, run) {
  const c = S.plan.checkin;
  say('me', `It comes on the ${ord(d)}`);
  let r;
  try { r = await api('/api/move', { money_day: d, sip_day: S.plan.plan.sip_day, sip: c.sip }); }
  catch (e) { r = { kind: 'error', message: "Couldn't reach the server." }; }
  if (alive(run)) outcome(r, run);
}
function confirmLifeline(run) {
  const c = S.plan.checkin;
  if (S.lifelines <= 0) return rulesRow(T('No Lifelines left this year', "You can move this month's date, invest manually when the money arrives, or stop the SIP."));
  rulesRow(T(`Use a Lifeline to skip ${c.month}?`, `Your SIP stays active and continues next month. Lifelines left after this: ${S.lifelines - 1} of 2 this year.`));
  youRow([h('button', { class: 'pill primary sm', type: 'button', onclick: () => {
    S.lifelines--; lifeChip(); say('me', 'Use a Lifeline');
    finish(`${c.month} skipped with a Lifeline. Your SIP is still active. Lifelines left: ${S.lifelines}.`, run);
  } }, 'Use Lifeline'), h('button', { class: 'pill sm', type: 'button', onclick: resetCheckinCard }, 'Cancel')]);
}
function confirmStop(run) {
  rulesRow(T('Stop this SIP?', "Future instalments stop. Money you already invested stays invested until you redeem it. If it's only about this month, a Lifeline also keeps the SIP active."));
  youRow([h('button', { class: 'pill sm', type: 'button', onclick: () => { say('me', 'Stop SIP'); finish('Stopped (simulated). Your invested money stays invested. You can start a new SIP any time.', run); } }, 'Stop SIP'),
    h('button', { class: 'pill sm', type: 'button', onclick: resetCheckinCard }, 'Keep it')]);
}
function finish(msg, run) {
  say('app', msg);
  $$('#readCard .rc-row.you').forEach(x => x.remove());
  rcRow('Done', h('div', null, h('div', { class: 't' }, msg), h('span', { class: 'badge ok' }, icon('check', 12), 'Confirmed by you')), 'you');
  autoNext(5200, run);
}

// ------------------------------------------------------------------ 6. Lifelines
function ring() {
  const t = document.createElement('template');
  t.innerHTML = '<svg viewBox="0 0 54 54" aria-hidden="true"><circle class="bg" cx="27" cy="27" r="23" fill="none" stroke-width="5"/><circle class="ring" cx="27" cy="27" r="23" fill="none" stroke-width="5" stroke-linecap="round"/></svg>';
  return t.content.firstChild;
}
function renderTokens() {
  $('#tokens').replaceChildren(h('span', { class: 'tok-l' + (S.lifelines ? '' : ' none') }, `${S.lifelines} of 2 left`), ...[0, 1].map(k => {
    const used = k >= S.lifelines;
    return h('div', { class: 'tok' + (used ? ' used' : ''), title: used ? 'Lifeline used' : 'Lifeline available' }, ring(), h('span', null, icon('life', 20)));
  }));
}
function buildFail(L) {
  const out = h('div');
  const opts = [['Pay now', "Groww shows a 'Pay Now' option for 2 working days after a low-balance failure, so this month can still be invested."],
    ['Use a Lifeline', 'This month becomes a planned skip. Your SIP stays active.'],
    ['Change my date', 'Rhythm suggests a date that fits when your money comes in (step 1).'],
    ['Stop SIP', 'Stopped. Money you already invested stays invested until you redeem it.']];
  $('#failBody').replaceChildren(
    h('div', { class: 'msg' }, h('div', { class: 'h' }, `Your ₹${inr(S.plan.checkin.amount)} SIP payment didn't go through`),
      h('div', null, h('b', null, 'Why: '), `on ${L.fail_debit} your account didn't have enough balance. The money is taken one working day before your SIP date.`),
      h('div', null, h('b', null, 'Nothing is lost: '), "your SIP is still active and next month's payment will go ahead."),
      h('div', null, h('b', null, 'Good to know: '), 'a SIP only stops after 3 failed payments in a row. This was the first.')),
    h('div', { class: 'row', style: 'margin-top:14px' }, opts.map(([l, t]) => h('button', { class: 'pill sm', type: 'button', onclick: () => { out.replaceChildren(); note(out, 'info', t + ' (Simulated.)'); } }, l))),
    out);
}
function enterLifeline(run) {
  const L = S.plan.lifeline;
  $('#year').replaceChildren(...L.months.map((m, k) => h('div', { class: 'ym' + (k === 0 ? ' cur' : '') },
    h('div', { class: 'o' }, k === 0 ? icon('dash', 14) : null), h('div', { class: 'l' }, m), h('div', { class: 's' }, k === 0 ? 'tight month' : ''))));
  renderTokens();
  const btn = $('#llBtn');
  btn.replaceChildren(icon('life', 16), `Use a Lifeline for ${L.month}`);
  btn.disabled = S.lifelines <= 0;
  $('#llOut').replaceChildren();
  if (S.lifelines <= 0) note('#llOut', 'warn', "No Lifelines left this year. You can still move this month's date, invest manually when the money arrives, or stop the SIP.");
  $('#failBox').open = false;
  buildFail(L);
}
async function useLifeline() {
  const run = S.run, L = S.plan.lifeline;
  if (S.lifelines <= 0) return;
  $('#llBtn').disabled = true;
  S.lifelines--;
  $$('#tokens .tok')[S.lifelines].classList.add('used');
  const lbl = $('#tokens .tok-l');
  lbl.textContent = `${S.lifelines} of 2 left`;
  lbl.classList.toggle('none', !S.lifelines);
  if (!(await wait(750, run))) return;
  const yms = $$('#year .ym');
  yms[0].classList.remove('cur');
  yms[0].classList.add('skip');
  $('.o', yms[0]).replaceChildren(icon('pause', 13));
  $('.s', yms[0]).textContent = 'skipped';
  if (!(await wait(650, run))) return;
  yms[1].classList.add('go');
  $('.o', yms[1]).replaceChildren(icon('check', 14));
  $('.s', yms[1]).textContent = 'continues';
  if (!(await wait(450, run))) return;
  const when = L.next_txt.startsWith('after') ? L.next_txt : 'on ' + L.next_txt;
  note('#llOut', 'ok', `${L.month} skipped. Your SIP is still active and continues ${when}. ${S.lifelines} Lifeline${S.lifelines === 1 ? '' : 's'} left this year.`);
  reveal($('#llOut'));
  autoNext(5500, run);
}

// ------------------------------------------------------------------ 7. learning from taps
const dayPos = d => `calc(14px + (100% - 28px) * ${(d - 1) / 30})`;      // one 1–31 scale for every month, so dots line up
function placeDot(k) {
  const row = $$('#taps .tr')[k], d = S.learn.days[k];
  $('.dot', row).style.left = dayPos(d);
  $('.tr-t', row).setAttribute('aria-valuenow', d);
  $('.tr-t', row).setAttribute('aria-valuetext', `the ${ord(d)}`);
  $('.tr-d', row).replaceChildren('the ', h('b', null, ord(d)));
}
function showBand(v) {
  $$('#taps .tr').forEach((row, k) => {
    const band = $('.band', row);
    if (!v.lo) { band.classList.remove('show'); return; }
    band.style.left = `calc(14px + (100% - 28px) * ${(v.lo - 1) / 30} - 13px)`;
    band.style.width = `calc((100% - 28px) * ${(v.hi - v.lo) / 30} + 26px)`;
    band.classList.add('show');
    band.classList.toggle('wide', v.verdict !== 'lock');
  });
}
function bindTrack(track, k) {
  const set = x => {
    const b = track.getBoundingClientRect(), n = S.learn.rows[k].days;
    const d = Math.min(n, Math.round(1 + Math.min(1, Math.max(0, (x - b.left - 14) / (b.width - 28))) * 30));
    if (d !== S.learn.days[k]) { S.learn.days[k] = d; placeDot(k); relearn(); }
  };
  track.addEventListener('pointerdown', e => {
    track.setPointerCapture(e.pointerId);
    set(e.clientX);
    const mv = ev => set(ev.clientX);
    const up = () => { track.removeEventListener('pointermove', mv); track.removeEventListener('pointerup', up); };
    track.addEventListener('pointermove', mv);
    track.addEventListener('pointerup', up);
  });
  track.addEventListener('keydown', e => {
    const n = S.learn.rows[k].days;
    let d = S.learn.days[k];
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') d = Math.min(n, d + 1);
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') d = Math.max(1, d - 1);
    else return;
    e.preventDefault();
    S.learn.days[k] = d;
    placeDot(k);
    relearn();
  });
}
function relearn() {
  cancelAuto();
  const run = S.run;
  clearTimeout(S.learn.timer);
  S.learn.timer = setTimeout(async () => {
    const p = S.plan.plan;
    let v;
    try { v = await api('/api/learn', { days: S.learn.days, mode: p.mode, sip_day: p.sip_day, noun: p.noun }); } catch (e) { return; }
    if (!alive(run)) return;
    showBand(v);
    renderVerdict(v, run, false);
  }, 240);
}
function renderVerdict(v, run, first) {
  const lock = v.verdict === 'lock', out = h('div');
  const acts = (v.actions || []).map((a, k) => h('button', { class: 'pill sm' + (k === 0 ? ' primary' : ''), type: 'button', onclick: () => {
    $$('#verdictBox button').forEach(b => { b.disabled = true; });
    note(out, 'ok', (v.done && v.done[a.id]) || 'Done.');
    autoNext(4600, run);
  } }, a.id === 'lock' ? icon('lock', 14) : null, a.label));
  $('#verdictBox').replaceChildren(h('div', { class: 'verdict pop ' + (lock ? 'lock' : 'keep') },
    h('div', { class: 'vic' }, icon(lock ? 'lock' : 'rules', 22)),
    h('div', null, h('div', { class: 'vt' }, v.title), h('div', { class: 'vb' }, v.body),
      lock && v.checks && v.checks.length ? checksList(v.checks) : null,
      acts.length ? h('div', { class: 'row', style: 'margin-top:14px' }, acts) : null, out)));
  reveal($('#verdictBox'));
  if (!lock && first) autoNext(8000, run);
}
function enterLearn(run) {
  const L = S.plan.learn;
  S.learn = { rows: L.rows, days: L.rows.map(r => r.day), timer: null };
  const box = $('#taps');
  box.replaceChildren();
  L.rows.forEach((r, k) => {
    const track = h('div', { class: 'tr-t', role: 'slider', tabindex: '0', 'aria-label': `${r.label}: the day your money came in`, 'aria-valuemin': 1, 'aria-valuemax': r.days },
      h('i', { class: 'band' }), h('i', { class: 'dot' }));
    box.append(h('div', { class: 'tr' }, h('div', { class: 'tr-m' }, r.label), track, h('div', { class: 'tr-d' })));
    bindTrack(track, k);
    placeDot(k);
  });
  box.append(h('div', { class: 'tr-scale', 'aria-hidden': 'true' }, h('span'),
    h('div', null, [1, 10, 20, 31].map(d => h('span', { style: `left:${dayPos(d)}` }, ord(d)))), h('span')));
  $('#verdictBox').replaceChildren();
  (async () => {
    if (!(await wait(700, run))) return;
    for (const row of $$('#taps .tr')) { row.classList.add('in'); if (!(await wait(540, run))) return; }
    showBand(L);
    if (await wait(600, run)) renderVerdict(L, run, true);
  })();
}

// ------------------------------------------------------------------ 8. how it's checked
const ASK_EX = ['will the bank charge me if it bounces?', 'what happens if I skip a month?', 'which fund should I pick?'];
function buildStats() {
  const box = $('#stats');
  if (box.childElementCount || !S.cfg) return;
  S.cfg.evals.forEach(t => box.append(h('div', { class: 'stat', 'data-v': t.value },
    h('div', { class: 'n' }, h('span', { class: 'num' }, '0'), t.suffix ? h('small', null, t.suffix) : null),
    h('div', { class: 'l' }, t.label), h('div', { class: 'd' }, t.detail))));
}
function countUp(el, to) {
  const t0 = performance.now(), dur = 1100;
  const step = t => { const p = Math.min(1, (t - t0) / dur); el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}
function enterTrust(run) {
  buildStats();
  const pipe = $('#pipe');
  pipe.classList.remove('run');
  $$('.pn', pipe).forEach(n => n.classList.remove('on'));
  $$('#stats .stat').forEach(s => { s.classList.remove('in'); $('.num', s).textContent = '0'; });
  (async () => {
    if (!(await wait(800, run))) return;
    pipe.classList.add('run');
    for (const n of $$('.pn', pipe)) { n.classList.add('on'); if (!(await wait(580, run))) return; }
    $$('#stats .stat').forEach((s, k) => setTimeout(() => { if (!alive(run)) return; s.classList.add('in'); countUp($('.num', s), +s.dataset.v); }, k * 130));
  })();
}
async function ask(text) {
  text = (text || '').trim();
  if (!text) return;
  const run = S.run, out = $('#askOut');
  out.replaceChildren(h('div', { class: 'ans pop' }, h('span', { class: 'shimmer' })));
  let r;
  try { r = await api('/api/ask', { text }); } catch (e) { r = { kind: 'fallback', message: "Couldn't reach the server." }; }
  if (alive(run)) { out.replaceChildren(h('div', { class: 'ans pop' }, answerBlock(r))); reveal(out); }
}

function restart() {
  S.plan = null;
  S.lifelines = 2;
  $('#setupInput').value = '';
  $('#verify').hidden = true;
  $('#setupExtras').classList.remove('shut');
  $('#currentDay').value = 5;
  $('#askOut').replaceChildren();
  $('#askInput').value = '';
  go(0, { force: true });
}

const ENTER = { intro: enterIntro, setup: enterSetup, rhythm: enterRhythm, replay: enterReplay, checkin: enterCheckin,
  lifeline: enterLifeline, learn: enterLearn, trust: enterTrust };

// ------------------------------------------------------------------ boot
async function boot() {
  fillIcons();
  buildSteps();
  buildIntro();
  buildSetup();
  SLIDES.forEach((s, k) => { if (k) { const el = slideEl(k); el.classList.add('is-future'); el.inert = true; el.setAttribute('aria-hidden', 'true'); } });
  slideEl(0).classList.add('is-active');
  $$('[data-go]').forEach(b => b.addEventListener('click', () => go(+b.dataset.go)));
  $('#next').addEventListener('click', () => (S.i === SLIDES.length - 1 ? restart() : go(S.i + 1)));
  $('#back').addEventListener('click', () => go(S.i - 1));
  $('#stay').addEventListener('click', cancelAuto);
  $('#replayAgain').addEventListener('click', () => { cancelAuto(); S.run++; enterReplay(S.run); });
  $('#replyForm').addEventListener('submit', e => { e.preventDefault(); sendReply($('#replyInput').value); });
  $('#llBtn').addEventListener('click', useLifeline);
  $('#askForm').addEventListener('submit', e => { e.preventDefault(); ask($('#askInput').value); });
  $('#restart').addEventListener('click', restart);
  $('#deck').addEventListener('pointerdown', () => { S.resume = null; if (S.auto) cancelAuto(); }, true);   // touching the page = "let me stay"
  document.addEventListener('keydown', e => {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.target.closest && e.target.closest('input, textarea, select, [role="slider"]')) return;
    if (e.key === 'ArrowRight' && !$('#next').disabled) $('#next').click();
    else if (e.key === 'ArrowLeft' && S.i > 0) go(S.i - 1);
  });
  document.addEventListener('visibilitychange', () => {        // pause the countdown while the tab is away, resume on return
    if (document.hidden && S.auto) { const run = S.run; cancelAuto(); S.resume = run; }
    else if (!document.hidden && S.resume != null) { const run = S.resume; S.resume = null; if (alive(run)) autoNext(3500, run); }
  });
  S.run++;
  renderNav();
  enterIntro(S.run);
  try { S.cfg = await api('/api/config'); } catch (e) { S.cfg = { examples: [], evals: [], amount: 500 }; }
  buildExamples();
  buildStats();
  $('#askChips').replaceChildren(...ASK_EX.map(t => h('button', { class: 'chip', type: 'button', onclick: () => { $('#askInput').value = t; ask(t); } }, t)));
  const k = SLIDES.findIndex(s => s.id === location.hash.slice(1));
  if (k > 0 && !SLIDES[k].needsPlan) go(k);
}
boot();
})();
