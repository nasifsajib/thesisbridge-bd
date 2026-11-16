/* ==========================================================================
   ThesisBridge BD — Resource Library (resources.js)
   Search + category filtering + resource detail modal.
   Renders into any <section data-mount="resources"> element.
   ========================================================================== */

(function (TB) {
  'use strict';

  function resCard(r, index) {
    return (
      '<article class="res-card card card-in" style="animation-delay:' + Math.min(index * 45, 360) + 'ms" tabindex="0" role="button"' +
      ' data-action="open-resource" data-id="' + r.id + '" aria-label="Open resource: ' + TB.esc(r.title) + '">' +
      '  <div class="res-top">' +
      '    <span class="res-type"><i class="fa-solid ' + r.typeIcon + '"></i> ' + TB.esc(r.type) + '</span>' +
      '    <span class="badge badge-soft">' + TB.esc(r.level) + '</span>' +
      '  </div>' +
      '  <h3>' + TB.esc(r.title) + '</h3>' +
      '  <p class="res-desc">' + TB.esc(r.description) + '</p>' +
      '  <div class="res-foot">' +
      '    <span class="res-time"><i class="fa-regular fa-clock"></i> ' + r.minutes + ' min</span>' +
      '    <span class="res-cat"><i class="fa-solid fa-folder-open"></i> ' + TB.esc(r.category) + '</span>' +
      '  </div>' +
      '</article>'
    );
  }

  function openResource(id) {
    const r = window.TB_DATA.resources.find(function (x) { return x.id === parseInt(id, 10); });
    if (!r) return;

    TB.modal.open({
      title: '<span class="pub-icon-sm"><i class="fa-solid ' + r.typeIcon + '"></i></span> ' + TB.esc(r.title),
      subtitle: TB.esc(r.category) + ' · ' + TB.esc(r.type) + ' · ' + r.minutes + ' min read',
      body:
        '<p class="res-detail-desc">' + TB.esc(r.description) + '</p>' +
        '<p>' + TB.esc(r.details) + '</p>' +
        '<h4 class="detail-sub"><i class="fa-solid fa-graduation-cap"></i> What you\u2019ll learn</h4>' +
        '<ul class="mini-list">' + r.learnPoints.map(function (p) { return '<li><i class="fa-solid fa-check"></i> ' + TB.esc(p) + '</li>'; }).join('') + '</ul>' +
        '<h4 class="detail-sub">Tags</h4>' +
        '<div class="tag-row">' + r.tags.map(function (t) { return '<span class="tag">' + TB.esc(t) + '</span>'; }).join('') + '</div>' +
        (r.url
          ? '<a class="btn btn-primary res-visit" href="' + TB.esc(r.url) + '" target="_blank" rel="noopener noreferrer">Visit Resource <i class="fa-solid fa-arrow-up-right-from-square"></i></a>'
          : '<p class="auth-note"><i class="fa-solid fa-circle-info"></i> This guide opens inline — all of its content is stored in the database.</p>'),
      footer: '<button class="btn btn-outline" data-res="close">Close</button>',
      size: 'md'
    }).overlay.querySelector('[data-res="close"]').addEventListener('click', function () {
      TB.modal.closeAll();
    });
  }

  function renderLibrary(mount) {
    const D = window.TB_DATA;
    const cats = ['All'].concat(Array.from(new Set(D.resources.map(function (r) { return r.category; }))));
    const state = { q: '', cat: 'All' };

    mount.innerHTML =
      '<div class="explorer-bar">' +
      '  <div class="search-box">' +
      '    <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>' +
      '    <input type="search" class="search-input" data-role="res-search" placeholder="Search resources by title, description or tag…" aria-label="Search resources">' +
      '    <button class="search-clear" data-role="res-search-clear" aria-label="Clear search" hidden><i class="fa-solid fa-xmark"></i></button>' +
      '  </div>' +
      '  <div class="bar-right"><span class="results-info" data-role="res-count"></span></div>' +
      '</div>' +
      '<div class="filters-panel open res-filters">' +
      '  <div class="filter-group">' +
      '    <div class="filter-group-head"><i class="fa-solid fa-folder-open"></i> Category</div>' +
      '    <div class="chip-row">' + cats.map(function (c) {
        return '<button type="button" class="chip' + (c === 'All' ? ' active' : '') + '" data-cat="' + TB.esc(c) + '" aria-pressed="' + (c === 'All') + '">' + TB.esc(c) + '</button>';
      }).join('') + '</div>' +
      '  </div>' +
      '  <div class="filters-foot">' +
      '    <span class="muted-sm">Filter by category, or search everything.</span>' +
      '    <button class="btn btn-ghost btn-sm" data-role="res-clear"><i class="fa-solid fa-rotate-left"></i> Clear All Filters</button>' +
      '  </div>' +
      '</div>' +
      '<div class="cards-grid" data-role="res-grid"></div>';

    const grid = mount.querySelector('[data-role="res-grid"]');
    const search = mount.querySelector('[data-role="res-search"]');
    const searchClear = mount.querySelector('[data-role="res-search-clear"]');
    const countEl = mount.querySelector('[data-role="res-count"]');

    function render() {
      const q = state.q.trim().toLowerCase();
      const list = D.resources.filter(function (r) {
        if (state.cat !== 'All' && r.category !== state.cat) return false;
        if (q) {
          const hay = (r.title + ' ' + r.description + ' ' + r.category + ' ' + r.type + ' ' + r.tags.join(' ')).toLowerCase();
          if (hay.indexOf(q) === -1) return false;
        }
        return true;
      });

      grid.innerHTML = list.length
        ? list.map(resCard).join('')
        : '<div class="empty-state">' +
          '  <div class="empty-icon"><i class="fa-solid fa-folder-open"></i></div>' +
          '  <h3>No resources found.</h3>' +
          '  <p>No resources match your search or category. Clear the filters to see the full library.</p>' +
          '  <button class="btn btn-primary" data-role="res-clear"><i class="fa-solid fa-rotate-left"></i> Clear All Filters</button>' +
          '</div>';

      countEl.textContent = list.length + ' of ' + D.resources.length + ' resources';

      mount.querySelectorAll('.chip[data-cat]').forEach(function (c) {
        const on = c.dataset.cat === state.cat;
        c.classList.toggle('active', on);
        c.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }

    function clearAll(toast) {
      state.q = ''; state.cat = 'All';
      search.value = ''; searchClear.hidden = true;
      render();
      if (toast !== false) TB.toast('Filters cleared — showing all resources.', 'info');
    }

    search.addEventListener('input', TB.debounce(function () {
      state.q = search.value; searchClear.hidden = !search.value; render();
    }, 140));
    searchClear.addEventListener('click', function () {
      search.value = ''; state.q = ''; searchClear.hidden = true; render(); search.focus();
    });

    mount.addEventListener('click', function (e) {
      const chipEl = e.target.closest('.chip[data-cat]');
      if (chipEl) { state.cat = chipEl.dataset.cat; render(); return; }
      if (e.target.closest('[data-role="res-clear"]')) { clearAll(); return; }
      const card = e.target.closest('[data-action="open-resource"]');
      if (card) openResource(card.dataset.id);
    });
    mount.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        const card = e.target.closest('[data-action="open-resource"]');
        if (card) { e.preventDefault(); openResource(card.dataset.id); }
      }
    });

    render();
  }

  function boot() {
    document.querySelectorAll('[data-mount="resources"]').forEach(renderLibrary);
  }
  /* Wait for js/api.js: TB.ready resolves after the database content has
     loaded, so the first render already uses real data. */
  function start() {
    if (TB.ready && typeof TB.ready.then === 'function') {
      TB.ready.then(boot);
    } else {
      boot();
    }
  }

  if (document.readyState === 'complete') start();
  else document.addEventListener('DOMContentLoaded', start);
})(window.TB);
