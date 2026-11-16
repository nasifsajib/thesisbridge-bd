/* ==========================================================================
   ThesisBridge BD — Publication module (publication.js)
   Research Roadmap (interactive timeline + completion tracking) ·
   Publication Hub (7 guide cards) · Journal Checklist (interactive).
   Mounts: [data-mount="roadmap"], [data-mount="pub-hub"], [data-mount="checklist"]
   ========================================================================== */

(function (TB) {
  'use strict';

  /* ------------------------------ Roadmap -------------------------------- */

  function renderRoadmap(mount) {
    const steps = window.TB_DATA.roadmapSteps;
    let selected = 1;

    mount.innerHTML =
      '<div class="roadmap-progress card reveal">' +
      '  <div class="rp-top">' +
      '    <span class="rp-label"><i class="fa-solid fa-route"></i> Research Journey</span>' +
      '    <strong data-role="rp-pct">0% Complete</strong>' +
      '  </div>' +
      '  <div class="progress-track"><div class="progress-fill" data-role="rp-fill" style="width:0%"></div></div>' +
      '  <p class="rp-sub" data-role="rp-sub">0 of ' + steps.length + ' steps completed</p>' +
      '</div>' +
      '<div class="timeline" role="tablist" aria-label="Research roadmap steps" data-role="timeline"></div>' +
      '<div class="roadmap-panel card" data-role="panel"></div>';

    const timeline = mount.querySelector('[data-role="timeline"]');
    const panel = mount.querySelector('[data-role="panel"]');
    const pctEl = mount.querySelector('[data-role="rp-pct"]');
    const subEl = mount.querySelector('[data-role="rp-sub"]');
    const fillEl = mount.querySelector('[data-role="rp-fill"]');

    const doneIds = function () { return TB.state.get('tb_roadmap', []) || []; };
    const isDone = function (id) { return doneIds().indexOf(id) > -1; };

    function renderTimeline() {
      const done = doneIds();
      // Progress line reaches the furthest completed step.
      let furthest = 0;
      steps.forEach(function (s) { if (done.indexOf(s.id) > -1) furthest = Math.max(furthest, s.id); });
      timeline.style.setProperty('--tl-progress', ((furthest) / steps.length) * 100 + '%');

      timeline.innerHTML = steps.map(function (s) {
        const complete = done.indexOf(s.id) > -1;
        const active = s.id === selected;
        return '<button class="tl-node' + (complete ? ' done' : '') + (active ? ' active' : '') + '" role="tab"' +
          ' aria-selected="' + active + '" data-action="select-step" data-id="' + s.id + '">' +
          '  <span class="tl-dot">' + (complete ? '<i class="fa-solid fa-check"></i>' : '<i class="fa-solid ' + s.icon + '"></i>') + '</span>' +
          '  <span class="tl-num">Step ' + s.id + '</span>' +
          '  <span class="tl-title">' + TB.esc(s.title) + '</span>' +
          '</button>';
      }).join('');
    }

    function renderProgress() {
      const done = doneIds().length;
      const pct = Math.round((done / steps.length) * 100);
      pctEl.textContent = pct + '% Complete';
      subEl.textContent = done + ' of ' + steps.length + ' steps completed';
      fillEl.style.width = pct + '%';
    }

    function renderPanel() {
      const s = steps.find(function (x) { return x.id === selected; });
      const complete = isDone(s.id);
      panel.innerHTML =
        '<div class="rp-head">' +
        '  <div class="rp-head-text">' +
        '    <h3><span class="tl-num-inline">' + s.id + '</span> ' + TB.esc(s.title) + '</h3>' +
        '    <span class="badge ' + (complete ? 'badge-success' : 'badge-soft') + '">' +
        (complete ? '<i class="fa-solid fa-check"></i> Completed' : '<i class="fa-regular fa-circle"></i> Not completed') + '</span>' +
        '  </div>' +
        '  <button class="btn ' + (complete ? 'btn-outline' : 'btn-primary') + ' btn-sm" data-action="toggle-step" data-id="' + s.id + '">' +
        (complete ? '<i class="fa-solid fa-rotate-left"></i> Mark as Incomplete' : '<i class="fa-solid fa-check"></i> Mark as Complete') +
        '  </button>' +
        '</div>' +
        '<p class="rp-explain">' + TB.esc(s.explanation) + '</p>' +
        '<div class="rp-cols">' +
        '  <div>' +
        '    <h4><i class="fa-solid fa-list-check"></i> Recommended actions</h4>' +
        '    <ul class="rp-list">' + s.actions.map(function (a) { return '<li><i class="fa-solid fa-arrow-right"></i> ' + TB.esc(a) + '</li>'; }).join('') + '</ul>' +
        '  </div>' +
        '  <div>' +
        '    <h4><i class="fa-solid fa-link"></i> Useful resources</h4>' +
        '    <ul class="rp-links">' + s.resources.map(function (r) {
            return '<li><a href="' + TB.esc(r.url) + '">' + TB.esc(r.label) + ' <i class="fa-solid fa-arrow-up-right-from-square"></i></a></li>';
          }).join('') + '</ul>' +
        '  </div>' +
        '</div>';
    }

    function renderAll() { renderTimeline(); renderProgress(); renderPanel(); }

    mount.addEventListener('click', function (e) {
      const sel = e.target.closest('[data-action="select-step"]');
      if (sel) {
        selected = parseInt(sel.dataset.id, 10);
        renderTimeline(); renderPanel();
        if (window.innerWidth < 840) {
          panel.scrollIntoView({ behavior: TB.prefersReducedMotion() ? 'auto' : 'smooth', block: 'nearest' });
        }
        return;
      }
      const tog = e.target.closest('[data-action="toggle-step"]');
      if (tog) {
        const id = parseInt(tog.dataset.id, 10);
        const ids = doneIds();
        const i = ids.indexOf(id);
        if (i > -1) { ids.splice(i, 1); TB.toast('Step marked as incomplete.', 'info'); }
        else {
          ids.push(id);
          const left = steps.length - ids.length;
          TB.toast('Roadmap step completed.' + (left > 0 ? ' ' + left + ' to go!' : ' That\u2019s the full journey!'));
        }
        TB.state.set('tb_roadmap', ids);
        renderTimeline(); renderProgress(); renderPanel();
      }
    });

    renderAll();
    if (typeof TB.observeReveals === 'function') TB.observeReveals(mount);
  }

  /* --------------------------- Publication hub ---------------------------- */

  function renderPubHub(mount) {
    const guides = window.TB_DATA.publicationGuides;

    function readIds() { return TB.state.get('tb_readGuides', []) || []; }

    function renderGrid() {
      const read = readIds();
      mount.innerHTML = '<div class="cards-grid pub-grid">' + guides.map(function (g, i) {
        const isRead = read.indexOf(g.id) > -1;
        return '<article class="pub-card card card-in" style="animation-delay:' + Math.min(i * 50, 350) + 'ms" tabindex="0" role="button"' +
          ' data-action="open-guide" data-id="' + TB.esc(g.id) + '" aria-label="Open guide: ' + TB.esc(g.title) + '">' +
          '  <div class="pub-top">' +
          '    <span class="pub-icon"><i class="fa-solid ' + g.icon + '"></i></span>' +
          (isRead ? '<span class="badge badge-success"><i class="fa-solid fa-check"></i> Read</span>' : '') +
          '  </div>' +
          '  <h3>' + TB.esc(g.title) + '</h3>' +
          '  <p>' + TB.esc(g.summary) + '</p>' +
          '  <span class="pub-open">Open Guide <i class="fa-solid fa-arrow-right"></i></span>' +
          '</article>';
      }).join('') + '</div>';
    }

    function openGuide(id) {
      const g = guides.find(function (x) { return x.id === id; });
      if (!g) return;
      TB.modal.open({
        title: '<span class="pub-icon-sm"><i class="fa-solid ' + g.icon + '"></i></span> ' + TB.esc(g.title),
        subtitle: 'Publication Hub guide',
        body:
          g.sections.map(function (s) {
            return '<div class="detail-block"><span class="detail-icon"><i class="fa-solid fa-book-open"></i></span>' +
              '<div><h4>' + TB.esc(s.heading) + '</h4><p>' + TB.esc(s.body) + '</p></div></div>';
          }).join('') +
          '<div class="tips-box">' +
          '  <h4><i class="fa-solid fa-lightbulb"></i> Practical tips</h4>' +
          '  <ul class="rp-list">' + g.tips.map(function (t) { return '<li><i class="fa-solid fa-check"></i> ' + TB.esc(t) + '</li>'; }).join('') + '</ul>' +
          '</div>',
        footer: '<button class="btn btn-outline" data-guide="close">Close Guide</button>',
        size: 'lg'
      }).overlay.querySelector('[data-guide="close"]').addEventListener('click', function () {
        TB.modal.closeAll();
      });

      const read = readIds();
      if (read.indexOf(id) === -1) {
        read.push(id);
        TB.state.set('tb_readGuides', read);
      }
    }

    mount.addEventListener('click', function (e) {
      const card = e.target.closest('[data-action="open-guide"]');
      if (card) openGuide(card.dataset.id);
    });
    mount.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        const card = e.target.closest('[data-action="open-guide"]');
        if (card) { e.preventDefault(); openGuide(card.dataset.id); }
      }
    });

    document.addEventListener('tb:change', function (ev) {
      if (ev.detail.key === 'tb_readGuides') renderGrid();
    });

    renderGrid();
  }

  /* ------------------------------- Checklist ------------------------------ */

  function renderChecklist(mount) {
    const items = window.TB_DATA.journalChecklist;

    mount.innerHTML =
      '<div class="checklist card">' +
      '  <div class="cl-head">' +
      '    <div>' +
      '      <h3><i class="fa-solid fa-clipboard-check"></i> Journal Submission Checklist</h3>' +
      '      <p class="cl-count" data-role="cl-count">0 / ' + items.length + ' Completed — 0%</p>' +
      '    </div>' +
      '    <button class="btn btn-ghost btn-sm" data-role="cl-reset"><i class="fa-solid fa-rotate-left"></i> Reset</button>' +
      '  </div>' +
      '  <div class="progress-track cl-track"><div class="progress-fill" data-role="cl-fill" style="width:0%"></div></div>' +
      '  <ul class="cl-items">' +
      items.map(function (it) {
        return '<li><label class="cl-item">' +
          '<input type="checkbox" data-role="cl-box" data-id="' + TB.esc(it.id) + '">' +
          '<span class="cl-box"><i class="fa-solid fa-check"></i></span>' +
          '<span class="cl-text">' + TB.esc(it.label) + '</span>' +
          '</label></li>';
      }).join('') +
      '  </ul>' +
      '</div>';

    const countEl = mount.querySelector('[data-role="cl-count"]');
    const fillEl = mount.querySelector('[data-role="cl-fill"]');

    const doneIds = function () { return TB.state.get('tb_checklist', []) || []; };

    function render() {
      const ids = doneIds();
      mount.querySelectorAll('[data-role="cl-box"]').forEach(function (box) {
        box.checked = ids.indexOf(box.dataset.id) > -1;
      });
      const pct = Math.round((ids.length / items.length) * 100);
      countEl.textContent = ids.length + ' / ' + items.length + ' Completed — ' + pct + '%';
      fillEl.style.width = pct + '%';
    }

    mount.addEventListener('change', function (e) {
      const box = e.target.closest('[data-role="cl-box"]');
      if (!box) return;
      const ids = doneIds();
      const i = ids.indexOf(box.dataset.id);
      if (box.checked && i === -1) ids.push(box.dataset.id);
      if (!box.checked && i > -1) ids.splice(i, 1);
      TB.state.set('tb_checklist', ids);
      render();
      TB.toast('Checklist updated.');
    });

    mount.addEventListener('click', function (e) {
      if (!e.target.closest('[data-role="cl-reset"]')) return;
      TB.state.set('tb_checklist', []);
      render();
      TB.toast('Checklist reset.', 'info');
    });

    render();
  }

  /* --------------------------------- Boot --------------------------------- */

  function boot() {
    document.querySelectorAll('[data-mount="roadmap"]').forEach(renderRoadmap);
    document.querySelectorAll('[data-mount="pub-hub"]').forEach(renderPubHub);
    document.querySelectorAll('[data-mount="checklist"]').forEach(renderChecklist);
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
