/* ==========================================================================
   ThesisBridge BD — Research Idea Explorer (research.js)
   Search · combined filters (category/difficulty/type/technology) · sorting
   Renders into any <section data-mount="research"> element.
   ========================================================================== */

(function (TB) {
  'use strict';

  const DIFF_ORDER = { Beginner: 1, Intermediate: 2, Advanced: 3 };

  function chip(label, group, extra) {
    return '<button type="button" class="chip" data-group="' + group + '" data-value="' + TB.esc(label) + '" aria-pressed="false">' + TB.esc(label) + '</button>';
  }

  function allChip(group) {
    return '<button type="button" class="chip active" data-group="' + group + '" data-value="All" aria-pressed="true">All</button>';
  }

  function ideaCard(r, index, savedIds) {
    const saved = savedIds.indexOf(r.id) > -1;
    const techs = r.technologies.slice(0, 3).map(function (t) { return '<span class="tag tag-tech">' + TB.esc(t) + '</span>'; }).join('') +
      (r.technologies.length > 3 ? '<span class="tag tag-more">+' + (r.technologies.length - 3) + '</span>' : '');
    return (
      '<article class="idea-card card card-in" style="animation-delay:' + Math.min(index * 45, 360) + 'ms">' +
      '  <div class="idea-top">' +
      '    <span class="cat-pill"><i class="fa-solid ' + TB.catIcon(r.category) + '"></i> ' + TB.esc(r.category) + '</span>' +
      '    <button class="icon-btn bookmark-btn' + (saved ? ' active' : '') + '" data-action="toggle-bookmark" data-id="' + r.id + '"' +
      '      aria-label="' + (saved ? 'Remove' : 'Bookmark') + ' ' + TB.esc(r.title) + '" aria-pressed="' + saved + '">' +
      '      <i class="fa-' + (saved ? 'solid' : 'regular') + ' fa-bookmark"></i>' +
      '    </button>' +
      '  </div>' +
      '  <h3 class="idea-title">' + TB.esc(r.title) + '</h3>' +
      '  <p class="idea-desc">' + TB.esc(r.description) + '</p>' +
      '  <div class="idea-meta">' +
      '    <span class="badge ' + TB.diffClass(r.difficulty) + '">' + r.difficulty + '</span>' +
      '    <span class="badge badge-soft">' + r.type + '</span>' +
      '  </div>' +
      '  <div class="tag-row">' + techs + '</div>' +
      '  <div class="idea-foot">' +
      '    <span class="idea-area"><i class="fa-solid fa-atom"></i> ' + TB.esc(r.area) + '</span>' +
      '    <button class="btn btn-outline btn-sm" data-action="view-idea" data-id="' + r.id + '">View Details</button>' +
      '  </div>' +
      '</article>'
    );
  }

  function renderExplorer(mount) {
    const D = window.TB_DATA;
    const state = { q: '', cats: [], diff: 'All', type: 'All', techs: [], sort: 'recommended' };

    mount.innerHTML =
      '<div class="explorer">' +
      '  <div class="explorer-bar">' +
      '    <div class="search-box">' +
      '      <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>' +
      '      <input type="search" class="search-input" data-role="search" placeholder="Search title, description, technology, tag…" aria-label="Search research ideas">' +
      '      <button class="search-clear" data-role="search-clear" aria-label="Clear search" hidden><i class="fa-solid fa-xmark"></i></button>' +
      '    </div>' +
      '    <div class="bar-right">' +
      '      <select class="select" data-role="sort" aria-label="Sort research ideas">' +
      '        <option value="recommended">Sort: Recommended</option>' +
      '        <option value="az">Sort: A – Z</option>' +
      '        <option value="za">Sort: Z – A</option>' +
      '        <option value="diff-asc">Sort: Beginner → Advanced</option>' +
      '        <option value="diff-desc">Sort: Advanced → Beginner</option>' +
      '      </select>' +
      '      <button class="btn btn-outline btn-sm filters-toggle" data-role="filters-toggle" aria-expanded="false" aria-controls="explorerFilters-' + mount.id + '">' +
      '        <i class="fa-solid fa-sliders"></i> Filters <span class="count-pill" data-role="filter-count" hidden>0</span>' +
      '      </button>' +
      '    </div>' +
      '  </div>' +
      '  <div class="filters-panel" id="explorerFilters-' + mount.id + '" data-role="filters">' +
      '    <div class="filter-group">' +
      '      <div class="filter-group-head"><i class="fa-solid fa-layer-group"></i> Category</div>' +
      '      <div class="chip-row">' + allChip('cats') + D.categories.map(function (c) { return chip(c.name, 'cats'); }).join('') + '</div>' +
      '    </div>' +
      '    <div class="filter-group">' +
      '      <div class="filter-group-head"><i class="fa-solid fa-gauge-high"></i> Difficulty</div>' +
      '      <div class="chip-row">' + allChip('diff') + D.difficulties.map(function (d) { return chip(d, 'diff'); }).join('') + '</div>' +
      '    </div>' +
      '    <div class="filter-group">' +
      '      <div class="filter-group-head"><i class="fa-solid fa-diagram-project"></i> Research Type</div>' +
      '      <div class="chip-row">' + allChip('type') + D.types.map(function (t) { return chip(t, 'type'); }).join('') + '</div>' +
      '    </div>' +
      '    <div class="filter-group">' +
      '      <div class="filter-group-head"><i class="fa-solid fa-microchip"></i> Technology</div>' +
      '      <div class="chip-row">' + allChip('techs') + D.technologies.map(function (t) { return chip(t, 'techs'); }).join('') + '</div>' +
      '    </div>' +
      '    <div class="filters-foot">' +
      '      <span class="results-info" data-role="count"></span>' +
      '      <button class="btn btn-ghost btn-sm" data-role="clear"><i class="fa-solid fa-rotate-left"></i> Clear All Filters</button>' +
      '    </div>' +
      '  </div>' +
      '  <div class="cards-grid" data-role="grid"></div>' +
      '</div>';

    const grid = mount.querySelector('[data-role="grid"]');
    const searchInput = mount.querySelector('[data-role="search"]');
    const searchClear = mount.querySelector('[data-role="search-clear"]');
    const sortSel = mount.querySelector('[data-role="sort"]');
    const countEl = mount.querySelector('[data-role="count"]');
    const filterCount = mount.querySelector('[data-role="filter-count"]');
    const filtersPanel = mount.querySelector('[data-role="filters"]');
    const filtersToggle = mount.querySelector('[data-role="filters-toggle"]');

    function results() {
      const q = state.q.trim().toLowerCase();
      let list = D.researchIdeas.filter(function (r) {
        if (q) {
          const hay = (r.title + ' ' + r.description + ' ' + r.category + ' ' + r.area + ' ' +
            r.technologies.join(' ') + ' ' + r.tags.join(' ') + ' ' + r.keywords.join(' ')).toLowerCase();
          if (hay.indexOf(q) === -1) return false;
        }
        if (state.cats.length && state.cats.indexOf(r.category) === -1) return false;
        if (state.diff !== 'All' && r.difficulty !== state.diff) return false;
        if (state.type !== 'All' && r.type !== state.type) return false;
        if (state.techs.length && !r.technologies.some(function (t) { return state.techs.indexOf(t) > -1; })) return false;
        return true;
      });

      const byTitle = function (a, b) { return a.title.localeCompare(b.title); };
      switch (state.sort) {
        case 'az': list = list.slice().sort(byTitle); break;
        case 'za': list = list.slice().sort(function (a, b) { return byTitle(b, a); }); break;
        case 'diff-asc': list = list.slice().sort(function (a, b) { return DIFF_ORDER[a.difficulty] - DIFF_ORDER[b.difficulty] || byTitle(a, b); }); break;
        case 'diff-desc': list = list.slice().sort(function (a, b) { return DIFF_ORDER[b.difficulty] - DIFF_ORDER[a.difficulty] || byTitle(a, b); }); break;
        default: list = list.slice().sort(function (a, b) { return (b.featured || 0) - (a.featured || 0); });
      }
      return list;
    }

    function activeFilterCount() {
      return state.cats.length + state.techs.length +
        (state.diff !== 'All' ? 1 : 0) + (state.type !== 'All' ? 1 : 0) + (state.q ? 1 : 0);
    }

    function syncChips() {
      mount.querySelectorAll('.chip').forEach(function (c) {
        const g = c.dataset.group, v = c.dataset.value;
        let on;
        if (g === 'cats') on = (v === 'All') ? state.cats.length === 0 : state.cats.indexOf(v) > -1;
        else if (g === 'techs') on = (v === 'All') ? state.techs.length === 0 : state.techs.indexOf(v) > -1;
        else on = (v === 'All') ? state[g] === 'All' : state[g] === v;
        c.classList.toggle('active', on);
        c.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }

    function renderGrid() {
      const list = results();
      const savedIds = TB.state.get('tb_bookmarks', []) || [];

      if (!list.length) {
        grid.innerHTML =
          '<div class="empty-state">' +
          '  <div class="empty-icon"><i class="fa-solid fa-magnifying-glass-minus"></i></div>' +
          '  <h3>No research ideas found.</h3>' +
          '  <p>No research ideas match your current filters. Try a different keyword or clear the filters to see all ideas.</p>' +
          '  <button class="btn btn-primary" data-role="clear"><i class="fa-solid fa-rotate-left"></i> Clear Filters</button>' +
          '</div>';
      } else {
        grid.innerHTML = list.map(function (r, i) { return ideaCard(r, i, savedIds); }).join('');
      }

      countEl.textContent = 'Showing ' + list.length + ' of ' + D.researchIdeas.length + ' research ideas';
      const n = activeFilterCount();
      filterCount.textContent = n;
      filterCount.hidden = n === 0;
      syncChips();
    }

    function clearAll() {
      state.q = ''; state.cats = []; state.diff = 'All'; state.type = 'All'; state.techs = []; state.sort = 'recommended';
      searchInput.value = '';
      searchClear.hidden = true;
      sortSel.value = 'recommended';
      renderGrid();
      TB.toast('Filters cleared — showing all ideas.', 'info');
    }

    // ---- Events ----
    searchInput.addEventListener('input', TB.debounce(function () {
      state.q = searchInput.value;
      searchClear.hidden = !searchInput.value;
      renderGrid();
    }, 140));
    searchClear.addEventListener('click', function () {
      searchInput.value = ''; state.q = ''; searchClear.hidden = true; renderGrid(); searchInput.focus();
    });
    sortSel.addEventListener('change', function () { state.sort = sortSel.value; renderGrid(); });
    filtersToggle.addEventListener('click', function () {
      const open = filtersPanel.classList.toggle('open');
      filtersToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    mount.addEventListener('click', function (e) {
      const c = e.target.closest('.chip');
      if (c) {
        const g = c.dataset.group, v = c.dataset.value;
        if (g === 'cats' || g === 'techs') {
          if (v === 'All') { state[g] = []; }
          else {
            const i = state[g].indexOf(v);
            if (i > -1) state[g].splice(i, 1); else state[g].push(v);
          }
        } else if (v === 'All') { state[g] = 'All'; }
        else { state[g] = (state[g] === v) ? 'All' : v; }
        renderGrid();
        return;
      }

      const clearBtn = e.target.closest('[data-role="clear"]');
      if (clearBtn) { clearAll(); return; }

      const bm = e.target.closest('[data-action="toggle-bookmark"]');
      if (bm) {
        const saved = TB.toggleBookmark(parseInt(bm.dataset.id, 10));
        bm.classList.toggle('active', saved);
        bm.setAttribute('aria-pressed', saved ? 'true' : 'false');
        bm.innerHTML = '<i class="fa-' + (saved ? 'solid' : 'regular') + ' fa-bookmark"></i>';
        return;
      }

      const view = e.target.closest('[data-action="view-idea"]');
      if (view) TB.openIdeaModal(parseInt(view.dataset.id, 10));
    });

    document.addEventListener('tb:change', function (e) {
      if (e.detail.key === 'tb_bookmarks') renderGrid();
    });

    renderGrid();
  }

  function boot() {
    document.querySelectorAll('[data-mount="research"]').forEach(renderExplorer);
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
