/* ==========================================================================
   ThesisBridge BD — Interactive Research Network (network.js)
   The hero "FIG. 01" card: an SVG node graph with spring physics,
   traveling pulses, draggable nodes and tap-for-guidance.
   Pure SVG + requestAnimationFrame — no libraries. Mounts into
   [data-mount="network"] (expects .net-body / .net-tip placeholders).
   ========================================================================== */

(function (TB) {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';

  /* Anchor positions are relative (0–1) inside the card body. */
  const NODES = [
    { label: 'Idea',       ax: 0.13, ay: 0.20, tip: 'Every journey starts with a question. Browse the explorer and shortlist what genuinely excites you.', cta: 'Explore Research Ideas', href: 'research.html' },
    { label: 'Gap',        ax: 0.38, ay: 0.08, tip: 'Find the hole in the literature nobody has filled — an untested method or an unstudied local context.', cta: 'Learn to Find Gaps', href: 'resources.html' },
    { label: 'Method',     ax: 0.66, ay: 0.22, tip: 'Decide how you will answer the question: datasets, models, tests and success metrics.', cta: 'Methodology Guide', href: 'resources.html' },
    { label: 'Experiment', ax: 0.45, ay: 0.45, tip: 'Run small, verifiable experiments. Reproduce one baseline before building anything new.', cta: 'See the Roadmap', href: 'index.html#roadmap' },
    { label: 'Thesis',     ax: 0.76, ay: 0.55, tip: 'Write while you research — chapters drafted alongside experiments are twice as accurate.', cta: 'Roadmap Step 6', href: 'index.html#roadmap' },
    { label: 'Supervisor', ax: 0.13, ay: 0.58, tip: 'Find faculty whose expertise covers your methods. Preparation beats enthusiasm.', cta: 'Match a Supervisor', href: 'supervisors.html' },
    { label: 'Paper',      ax: 0.27, ay: 0.82, tip: 'Turn the thesis into one tight argument, written directly in the venue\u2019s template.', cta: 'Publication Hub', href: 'publication.html' },
    { label: 'Journal',    ax: 0.58, ay: 0.84, tip: 'Verify the journal is indexed, prepare the submission package, then submit and track it.', cta: 'Journal Checklist', href: 'publication.html#journal-checklist' }
  ];

  /* [from, to] index pairs — mirrors the reference figure. */
  const EDGES = [
    [0, 1], [1, 2], [2, 3], [2, 4], [3, 4],
    [3, 5], [0, 5], [5, 6], [6, 7], [7, 4]
  ];

  const SPRING = 0.016;   // pull toward anchor
  const DAMP = 0.90;      // velocity damping
  const FLOAT_AMP = 3;    // idle drift (px)
  const MAX_PULSES = 4;

  function el(name, cls) {
    const e = document.createElementNS(NS, name);
    if (cls) e.setAttribute('class', cls);
    return e;
  }

  function mountNetwork(card) {
    const body = card.querySelector('.net-body');
    if (!body || body.dataset.netReady) return;
    body.dataset.netReady = '1';

    const reduced = TB.prefersReducedMotion();

    const svg = el('svg', 'net-svg');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Interactive research network. Drag the nodes, or tap one for guidance.');
    const gEdges = el('g', 'net-edges');
    const gPulses = el('g', 'net-pulses');
    const gNodes = el('g', 'net-nodes');
    svg.append(gEdges, gPulses, gNodes);
    body.appendChild(svg);

    const tip = document.createElement('div');
    tip.className = 'net-tip';
    tip.hidden = true;
    body.appendChild(tip);

    /* ------------------------------ nodes ------------------------------ */

    const nodes = NODES.map(function (n, i) {
      const g = el('g', 'net-node');
      g.dataset.index = i;
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', n.label + ' — ' + n.cta);
      const c = el('circle');
      const t = el('text');
      t.textContent = n.label;
      g.append(c, t);
      gNodes.appendChild(g);
      return Object.assign({}, n, {
        g: g, circle: c, x: 0, y: 0, vx: 0, vy: 0,
        phase: Math.random() * Math.PI * 2, drag: false
      });
    });

    const edgeEls = EDGES.map(function () {
      const l = el('line', 'net-edge');
      gEdges.appendChild(l);
      return l;
    });

    /* ---------------------------- geometry ----------------------------- */

    let W = 0, H = 0, R = 29, PAD = 40;
    let bottomInset = 0; // space reserved for the guidance tip when open

    function measure() {
      const r = body.getBoundingClientRect();
      W = Math.max(r.width, 100);
      H = Math.max(r.height, 100);
      R = W < 430 ? 23 : 29;
      PAD = R + 16;
      nodes.forEach(function (n) { n.circle.setAttribute('r', R); });
    }
    measure();
    if (typeof ResizeObserver !== 'undefined') new ResizeObserver(measure).observe(body);
    else window.addEventListener('resize', measure);

    function anchor(n, t) {
      const fx = reduced ? 0 : Math.sin(t * 0.7 + n.phase) * FLOAT_AMP;
      const fy = reduced ? 0 : Math.cos(t * 0.55 + n.phase * 1.3) * FLOAT_AMP;
      return {
        x: PAD + n.ax * (W - PAD * 2) + fx,
        y: PAD + n.ay * (H - PAD * 2 - bottomInset) + fy
      };
    }

    function clampNode(n) {
      n.x = Math.min(Math.max(n.x, R + 2), W - R - 2);
      n.y = Math.min(Math.max(n.y, R + 2), H - bottomInset - R - 2);
    }

    /* Seed nodes at their anchors with a tiny random kick. */
    function seed() {
      const t = 0;
      nodes.forEach(function (n) {
        const a = anchor(n, t);
        n.x = a.x + (Math.random() - 0.5) * 14;
        n.y = a.y + (Math.random() - 0.5) * 14;
        n.vx = (Math.random() - 0.5) * 2.2;
        n.vy = (Math.random() - 0.5) * 2.2;
      });
    }
    seed();

    /* ------------------------------ pulses ----------------------------- */

    const pulses = [];
    let nextSpawn = 900;

    function spawnPulse() {
      if (reduced || pulses.length >= MAX_PULSES) return;
      const ei = Math.floor(Math.random() * EDGES.length);
      const dot = el('circle', 'net-pulse');
      dot.setAttribute('r', 3);
      gPulses.appendChild(dot);
      pulses.push({ ei: ei, t: 0, dir: Math.random() < 0.5 ? 1 : -1, speed: 0.55 + Math.random() * 0.5, el: dot });
    }

    function updatePulses(dt) {
      nextSpawn -= dt * 1000;
      if (nextSpawn <= 0) { spawnPulse(); nextSpawn = 650 + Math.random() * 750; }
      for (let i = pulses.length - 1; i >= 0; i--) {
        const p = pulses[i];
        p.t += p.speed * dt;
        if (p.t >= 1) { p.el.remove(); pulses.splice(i, 1); continue; }
        const pair = EDGES[p.ei];
        const A = nodes[p.dir === 1 ? pair[0] : pair[1]];
        const B = nodes[p.dir === 1 ? pair[1] : pair[0]];
        const x = A.x + (B.x - A.x) * p.t;
        const y = A.y + (B.y - A.y) * p.t;
        p.el.setAttribute('cx', x);
        p.el.setAttribute('cy', y);
        const fade = Math.sin(p.t * Math.PI);
        p.el.setAttribute('opacity', (0.35 + fade * 0.5).toFixed(2));
      }
    }

    /* ---------------------------- animation ---------------------------- */

    let raf = 0, last = 0, visible = true, simT = 0, lastTick = 0;

    function render() {
      nodes.forEach(function (n) {
        n.g.setAttribute('transform', 'translate(' + n.x.toFixed(1) + ' ' + n.y.toFixed(1) + ')');
      });
      EDGES.forEach(function (pair, i) {
        const A = nodes[pair[0]], B = nodes[pair[1]];
        const l = edgeEls[i];
        l.setAttribute('x1', A.x.toFixed(1)); l.setAttribute('y1', A.y.toFixed(1));
        l.setAttribute('x2', B.x.toFixed(1)); l.setAttribute('y2', B.y.toFixed(1));
      });
    }

    function physics(dt) {
      const t = simT += dt;

      nodes.forEach(function (n) {
        if (!n.drag) {
          const a = anchor(n, t);
          if (reduced) { n.x = a.x; n.y = a.y; n.vx = n.vy = 0; }
          else {
            n.vx = (n.vx + (a.x - n.x) * SPRING) * DAMP;
            n.vy = (n.vy + (a.y - n.y) * SPRING) * DAMP;
            n.x += n.vx; n.y += n.vy;
            clampNode(n);
          }
        }
      });

      render();
      updatePulses(dt);
      lastTick = performance.now();
    }

    function frame(now) {
      const dt = Math.min((now - (last || now)) / 1000, 0.05);
      last = now;
      physics(dt);
      if (visible && !document.hidden) raf = requestAnimationFrame(frame);
      else raf = 0;
    }

    function wake() {
      if (!raf && visible && !document.hidden) { last = 0; raf = requestAnimationFrame(frame); }
    }

    if (typeof IntersectionObserver !== 'undefined') {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { visible = en.isIntersecting; });
        wake();
      }, { threshold: 0.02 }).observe(card);
    }
    document.addEventListener('visibilitychange', wake);
    /* Self-healing hybrid loop: some hosts suspend rAF indefinitely for
       occluded panes. If no frame has ticked for 500ms while the card is
       on screen, a timer drives the physics instead. */
    setInterval(function () {
      if (!visible || document.hidden) return;
      const now = performance.now();
      if (now - lastTick > 500) physics(Math.min((now - (lastTick || now)) / 1000, 0.25));
      else if (!raf) wake();
    }, 250);
    wake();

    /* ------------------------------ guidance --------------------------- */

    let activeNode = null;

    function hideTip() {
      bottomInset = 0;
      tip.hidden = true;
      tip.classList.remove('show');
      if (activeNode) { activeNode.g.classList.remove('active'); activeNode = null; }
    }

    function showTip(n) {
      if (activeNode) activeNode.g.classList.remove('active');
      activeNode = n;
      n.g.classList.add('active');
      tip.innerHTML =
        '<button class="net-tip-close" type="button" aria-label="Close guidance"><i class="fa-solid fa-xmark"></i></button>' +
        '<p class="net-tip-text"><span class="net-tip-k">' + TB.esc(n.label.toUpperCase()) + '</span> ' + TB.esc(n.tip) + '</p>' +
        '<a class="net-tip-link" href="' + TB.esc(n.href) + '">' + TB.esc(n.cta) + ' <i class="fa-solid fa-arrow-right"></i></a>';
      tip.hidden = false;
      /* Reserve the tip's height so the graph reflows above it instead of
         being covered — nodes spring up out of the way. */
      bottomInset = Math.min(tip.offsetHeight + 28, Math.round(H * 0.45));
      requestAnimationFrame(function () { tip.classList.add('show'); });
      tip.querySelector('.net-tip-close').addEventListener('click', hideTip);
    }

    /* ------------------------------- drag ------------------------------ */

    let dragIndex = -1, moved = 0, px = 0, py = 0;

    svg.addEventListener('pointerdown', function (e) {
      const g = e.target.closest ? e.target.closest('.net-node') : null;
      if (!g) { hideTip(); return; }
      const i = parseInt(g.dataset.index, 10);
      const n = nodes[i];
      dragIndex = i; moved = 0;
      px = e.clientX; py = e.clientY;
      n.drag = true;
      g.classList.add('dragging');
      try { svg.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events */ }
      e.preventDefault();
    });

    svg.addEventListener('pointermove', function (e) {
      if (dragIndex < 0) return;
      const n = nodes[dragIndex];
      const dx = e.clientX - px, dy = e.clientY - py;
      px = e.clientX; py = e.clientY;
      moved += Math.abs(dx) + Math.abs(dy);
      if (moved > 6 && tip.hidden === false) hideTipSoft();
      n.x += dx; n.y += dy;
      n.vx = dx * 0.35; n.vy = dy * 0.35;
      clampNode(n);
      render(); // respond instantly even if rAF is throttled
    });

    function endDrag(commitTap) {
      if (dragIndex < 0) return;
      const n = nodes[dragIndex];
      n.drag = false;
      n.g.classList.remove('dragging');
      if (commitTap && moved < 8) showTip(n);
      else hideTipSoft();
      dragIndex = -1;
    }

    svg.addEventListener('pointerup', function () { endDrag(true); });
    svg.addEventListener('pointercancel', function () { endDrag(false); });

    /* Soft-hide keeps the active highlight removal, without animation jump. */
    function hideTipSoft() { hideTip(); }

    /* Keyboard access: Enter/Space on a focused node shows guidance. */
    gNodes.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const g = e.target.closest('.net-node');
      if (g) { e.preventDefault(); showTip(nodes[parseInt(g.dataset.index, 10)]); }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !tip.hidden) hideTip();
    });
  }

  function boot() {
    document.querySelectorAll('[data-mount="network"]').forEach(mountNetwork);
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
