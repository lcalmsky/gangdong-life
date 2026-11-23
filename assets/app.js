// 강동라이프: renders the hub (index.html) and a collection page (list.html?c=<id>)
// from the JSON files in data/. Content changes go in data/, not here.

const ILL = {
  food: `<svg class="ill" viewBox="0 0 128 104" fill="none" aria-hidden="true">
    <path d="M44 22c-4-6 4-10 0-16M60 22c-4-6 4-10 0-16M76 22c-4-6 4-10 0-16" stroke="var(--ill-line)" stroke-width="3" stroke-linecap="round"/>
    <path d="M84 18 116 2M88 24 120 10" stroke="var(--ill-line)" stroke-width="3" stroke-linecap="round"/>
    <ellipse cx="60" cy="44" rx="48" ry="10" fill="var(--ill-fill)" stroke="var(--ill-line)" stroke-width="3"/>
    <path d="M12 44c0 28 22 46 48 46s48-18 48-46" fill="var(--ill-white)" stroke="var(--ill-line)" stroke-width="3"/>
    <path d="M24 60h72" stroke="var(--ill-fill)" stroke-width="6" stroke-linecap="round"/>
    <path d="M44 90h32v8H44z" fill="var(--ill-fill)" stroke="var(--ill-line)" stroke-width="3" stroke-linejoin="round"/></svg>`,
  cafe: `<svg class="ill" viewBox="0 0 128 104" fill="none" aria-hidden="true">
    <path d="M46 20c-4-6 4-10 0-16M62 20c-4-6 4-10 0-16" stroke="var(--ill-line)" stroke-width="3" stroke-linecap="round"/>
    <path d="M86 46h8a12 12 0 0 1 0 24h-8" stroke="var(--ill-line)" stroke-width="3"/>
    <path d="M22 32h64v30c0 16-12 26-32 26S22 78 22 62z" fill="var(--ill-white)" stroke="var(--ill-line)" stroke-width="3" stroke-linejoin="round"/>
    <path d="M22 32h64v10H22z" fill="var(--ill-fill)"/>
    <ellipse cx="56" cy="94" rx="48" ry="6" fill="var(--ill-fill)" stroke="var(--ill-line)" stroke-width="3"/>
    <path d="M42 58c4 6 20 6 24 0" stroke="var(--ill-line)" stroke-width="3" stroke-linecap="round"/></svg>`,
  // Fallback for any kind without its own drawing yet.
  place: `<svg class="ill" viewBox="0 0 128 104" fill="none" aria-hidden="true">
    <ellipse cx="64" cy="94" rx="40" ry="6" fill="var(--ill-fill)"/>
    <path d="M64 92S30 60 30 38a34 34 0 0 1 68 0c0 22-34 54-34 54z" fill="var(--ill-white)" stroke="var(--ill-line)" stroke-width="3" stroke-linejoin="round"/>
    <circle cx="64" cy="38" r="12" fill="var(--ill-fill)" stroke="var(--ill-line)" stroke-width="3"/></svg>`,
};
const ARROW = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>';
const PIN = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>';
const REGION_ORDER = ['강동', '송파', '하남'];

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ill = (kind) => ILL[kind] || ILL.place;
const getJSON = (p) => fetch(p, { cache: 'no-cache' }).then((r) => { if (!r.ok) throw new Error(p + ' ' + r.status); return r.json(); });

function mapUrl(p) {
  const q = p.mapQuery || [p.name, p.area || '강동구'].join(' ');
  return 'https://map.naver.com/p/search/' + encodeURIComponent(q);
}

async function renderHub() {
  const site = await getJSON('data/site.json');
  const cols = await Promise.all(site.collections.map((id) => getJSON(`data/${id}.json`)));
  document.title = site.title;
  document.getElementById('hello').textContent = site.greeting;
  document.getElementById('title').innerHTML = esc(site.title).replace(/의 /, '의<br>');
  document.getElementById('cards').innerHTML = cols.map((c, i) => `
    <a class="card tone-${i % 2}" href="${c.id === 'restaurants' ? 'map/' : c.id === 'cafes' ? 'map/?c=cafes' : 'list.html?c=' + encodeURIComponent(c.id)}">
      ${ill(c.kind)}
      <h2>${esc(c.title)}</h2>
      <p>${esc(c.summary)}</p>
      <div class="row"><span class="count">${c.places.length}<small>곳</small></span><span class="go">${ARROW}</span></div>
    </a>`).join('');
}

function placeRow(p) {
  const sub = [p.area, p.note].filter(Boolean).join(' · ');
  return `<li class="place">
    <div class="p-main">
      <div class="p-name">${esc(p.name)}${p.mentions >= 2 ? `<span class="badge many">${p.mentions}명 추천</span>` : ''}${p.self ? '<span class="badge self">가게 직접</span>' : ''}</div>
      ${sub ? `<div class="p-sub">${esc(sub)}</div>` : ''}
    </div>
    <a class="map" href="${mapUrl(p)}" target="_blank" rel="noopener" aria-label="${esc(p.name)} 네이버 지도에서 보기">${PIN}지도</a>
  </li>`;
}

function heat(n) { return n >= 6 ? 3 : n >= 3 ? 2 : n >= 1 ? 1 : 0; }

function renderMap(places, onPick) {
  const m = GANGDONG_MAP;
  const counts = {};
  places.forEach((p) => { if (p.dong) counts[p.dong] = (counts[p.dong] || 0) + 1; });
  const shapes = Object.entries(m.dongs).map(([k, v], i) => `<path class="dong h${heat(counts[k] || 0)}${counts[k] ? '' : ' empty'}" data-dong="${k}" d="${v.d}" style="fill:var(--d${i + 1}, revert-layer)"/>`).join('');
  const pins = Object.entries(m.dongs).map(([k, v]) => {
    const n = counts[k] || 0;
    const pos = `left:${(v.x / m.w) * 100}%;top:${(v.y / m.h) * 100}%`;
    return n
      ? `<button class="pin" type="button" data-dong="${k}" style="${pos}" aria-pressed="false">${k}<b>${n}</b></button>`
      : `<span class="pin-label" style="${pos}">${k}</span>`;
  }).join('');
  const stage = document.getElementById('map');
  stage.innerHTML = `<div class="map-inner">
    <svg viewBox="0 0 ${m.w} ${m.h}" aria-hidden="true">
      <path class="water" d="${m.water}"/>${shapes}
      <text class="water-label" x="150" y="330" transform="rotate(-38 150 330)">한강</text>
    </svg>${pins}</div>`;
  stage.addEventListener('click', (e) => {
    const b = e.target.closest('.pin'); if (b) onPick(b.dataset.dong);
  });
  return (dong) => {
    stage.querySelectorAll('.pin').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.dong === dong)));
    stage.querySelectorAll('.dong').forEach((x) => x.classList.toggle('on', x.dataset.dong === dong));
  };
}

async function renderList() {
  document.body.dataset.palette = new URLSearchParams(location.search).get('p') || 'sunset';
  const id = new URLSearchParams(location.search).get('c');
  const site = await getJSON('data/site.json');
  if (!id || !site.collections.includes(id)) { location.replace('./'); return; }
  const c = await getJSON(`data/${id}.json`);
  document.title = `${c.title} · ${site.title}`;
  document.getElementById('head').innerHTML = `
    <h1>${esc(c.title)}<span>${c.places.length}곳</span></h1><p>${esc(c.summary)}</p>`;

  const places = [...c.places].sort((a, b) => b.mentions - a.mentions || a.name.localeCompare(b.name, 'ko'));
  const regions = REGION_ORDER.filter((r) => places.some((p) => p.region === r));
  const hasUnknown = places.some((p) => !p.region);
  const chipDefs = regions.length > 1 || (regions.length && hasUnknown)
    ? [['', '전체'], ...regions.map((r) => [r, r]), ...(hasUnknown ? [['?', '위치 모름']] : [])] : [];
  let region = '', query = '', dong = '';

  const chips = document.getElementById('chips');
  const paintChips = () => chips.querySelectorAll('.chip[data-v]').forEach((x) => x.setAttribute('aria-pressed', String(!dong && x.dataset.v === region)));
  chips.innerHTML = chipDefs.map(([v, label]) => {
    const n = v === '' ? places.length : places.filter((p) => (v === '?' ? !p.region : p.region === v)).length;
    return `<button class="chip" type="button" data-v="${v}">${label}<span>${n}</span></button>`;
  }).join('');
  const setDong = renderMap(places, (d) => {
    dong = dong === d ? '' : d; region = '';
    setDong(dong); paintChips(); draw();
    if (dong) document.getElementById('sheet').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  });
  chips.addEventListener('click', (e) => {
    const b = e.target.closest('.chip'); if (!b) return;
    if (b.dataset.clear !== undefined) { dong = ''; setDong(''); }
    else { region = b.dataset.v; dong = ''; setDong(''); }
    paintChips(); draw();
  });
  document.getElementById('q').addEventListener('input', (e) => { query = e.target.value.trim(); draw(); });
  paintChips();

  function draw() {
    const old = chips.querySelector('[data-clear]'); if (old) old.remove();
    if (dong) chips.insertAdjacentHTML('afterbegin', `<button class="chip" type="button" data-clear aria-pressed="true">${dong}동만 보는 중<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-label="해제"><path d="M18 6 6 18M6 6l12 12"/></svg></button>`);
    const hit = places.filter((p) =>
      (dong ? p.dong === dong : (region === '' || (region === '?' ? !p.region : p.region === region))) &&
      (!query || (p.name + ' ' + p.area + ' ' + p.note).includes(query)));
    const picked = hit.filter((p) => p.mentions >= 2);
    const rest = hit.filter((p) => p.mentions < 2);
    let html = '';
    if (picked.length) html += `<h2 class="sec-title">여러 명이 꼽은 곳<small>${picked.length}</small></h2><ul class="places picked">${picked.map(placeRow).join('')}</ul>`;
    if (rest.length) html += `<h2 class="sec-title">${picked.length ? '한 명이 꼽은 곳' : '전체'}<small>${rest.length}</small></h2><ul class="places">${rest.map(placeRow).join('')}</ul>`;
    document.getElementById('results').innerHTML = html || '<p class="empty">찾는 가게가 없어요</p>';
  }
  draw();
}

const fail = (e) => { console.error(e); document.querySelector('main').insertAdjacentHTML('beforeend', '<p class="empty">목록을 불러오지 못했어요. 새로고침해 주세요.</p>'); };
(document.body.dataset.page === 'list' ? renderList() : renderHub()).catch(fail);
