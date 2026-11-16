/* ==========================================================================
   ThesisBridge BD — Supervisor Matching (supervisors.js)
   Search + combined filters · profile modal · saved supervisors ·
   4-step match questionnaire with demo scoring algorithm.
   Renders into any <section data-mount="supervisors"> element.
   ========================================================================== */

(function (TB) {
  'use strict';

  function hueFor(id) { return (id * 77) % 360; }

  function avatarHTML(s, cls) {
    return '<span class="avatar' + (cls ? ' ' + cls : '') + '" style="--h:' + hueFor(s.id) + '">' + TB.esc(TB.initials(s.name)) + '</span>';
  }

  /* ------------------------------ Cards ---------------------------------- */

  function supCard(s, index, savedIds) {
    const saved = savedIds.indexOf(s.id) > -1;
    const reqs = TB.state.get('tb_connectRequests', []) || [];
    const requested = reqs.some(function (r) { return r.supId === s.id; });
    return (
      '<article class="sup-card card card-in" style="animation-delay:' + Math.min(index * 45, 360) + 'ms">' +
      '  <div class="sup-head">' +
      '    ' + avatarHTML(s) +
      '    <div class="sup-id">' +
      '      <h3>' + TB.esc(s.name) + '</h3>' +
      '      <p class="sup-title">' + TB.esc(s.title) + '</p>' +
      '      <p class="sup-affil"><i class="fa-solid fa-building-columns"></i> ' + TB.esc(s.university) + ' · ' + TB.esc(s.department) + '</p>' +
      '    </div>' +
      (s.accepting ? '<span class="badge badge-success sup-accept"><i class="fa-solid fa-circle"></i> Accepting</span>' : '') +
      (requested ? '<span class="req-pill"><i class="fa-solid fa-paper-plane"></i> Requested</span>' : '') +
      '  </div>' +
      '  <div class="tag-row">' + s.interests.map(function (i) { return '<span class="tag">' + TB.esc(i) + '</span>'; }).join('') + '</div>' +
      '  <div class="sup-stats">' +
      '    <div><strong>' + s.publications + '</strong><span>Publications</span></div>' +
      '    <div><strong>' + s.areas.length + '</strong><span>Areas</span></div>' +
      '    <div><strong>' + s.supervisionTypes.length + '</strong><span>Types</span></div>' +
      '  </div>' +
      '  <div class="sup-actions">' +
      '    <button class="btn btn-primary btn-sm" data-action="view-sup" data-id="' + s.id + '">View Profile</button>' +
      '    <button class="icon-btn bookmark-btn' + (saved ? ' active' : '') + '" data-action="toggle-save-sup" data-id="' + s.id + '"' +
      '      aria-label="' + (saved ? 'Remove' : 'Save') + ' ' + TB.esc(s.name) + '" aria-pressed="' + saved + '">' +
      '      <i class="fa-' + (saved ? 'solid' : 'regular') + ' fa-bookmark"></i></button>' +
      '  </div>' +
      '</article>'
    );
  }

  /* --------------------------- Profile modal ------------------------------ */

  function openSupervisorModal(id, onCloseCb) {
    const s = window.TB_DATA.supervisors.find(function (x) { return x.id === id; });
    if (!s) return;
    const saved = (TB.state.get('tb_savedSupervisors', []) || []).indexOf(s.id) > -1;

    const entry = TB.modal.open({
      title: TB.esc(s.name),
      subtitle: TB.esc(s.title) + ' · ' + TB.esc(s.university) + ' · ' + TB.esc(s.department),
      body:
        '<div class="sup-modal-head">' +
        '  ' + avatarHTML(s, 'avatar-lg') +
        '  <div>' +
        '    <p>' + TB.esc(s.bio) + '</p>' +
        '    <div class="tag-row" style="margin-top:10px">' +
        (s.accepting ? '<span class="badge badge-success"><i class="fa-solid fa-circle"></i> Accepting students</span>' : '<span class="badge badge-soft">Not accepting right now</span>') +
        '    <span class="badge badge-soft"><i class="fa-solid fa-envelope"></i> ' + TB.esc(s.email) + '</span>' +
        '    <span class="badge badge-soft"><i class="fa-solid fa-location-dot"></i> ' + TB.esc(s.office) + '</span>' +
        '    </div>' +
        '  </div>' +
        '</div>' +

        '<h4 class="detail-sub"><i class="fa-solid fa-flask"></i> Research interests</h4>' +
        '<div class="tag-row">' + s.interests.map(function (i) { return '<span class="tag tag-tech">' + TB.esc(i) + '</span>'; }).join('') + '</div>' +

        '<h4 class="detail-sub"><i class="fa-solid fa-sitemap"></i> Research areas</h4>' +
        '<div class="tag-row">' + s.areas.map(function (a) { return '<span class="tag">' + TB.esc(a) + '</span>'; }).join('') + '</div>' +

        '<h4 class="detail-sub"><i class="fa-solid fa-file-lines"></i> Selected publications</h4>' +
        '<ul class="mini-list">' + s.selectedPubs.map(function (p) { return '<li><i class="fa-regular fa-file-lines"></i> ' + TB.esc(p) + '</li>'; }).join('') + '</ul>' +

        '<h4 class="detail-sub"><i class="fa-solid fa-user-check"></i> Areas for supervision</h4>' +
        '<ul class="mini-list">' + s.supervisionAreas.map(function (a) { return '<li><i class="fa-solid fa-check"></i> ' + TB.esc(a) + '</li>'; }).join('') + '</ul>' +

        '<h4 class="detail-sub"><i class="fa-solid fa-lightbulb"></i> Suggested thesis topics</h4>' +
        '<ul class="mini-list numbered">' + s.suggestedTopics.map(function (t, i) { return '<li><span class="num">' + (i + 1) + '</span> ' + TB.esc(t) + '</li>'; }).join('') + '</ul>',

      footer:
        '<button class="btn btn-outline" data-sup-action="save"><i class="fa-' + (saved ? 'solid' : 'regular') + ' fa-bookmark"></i> ' + (saved ? 'Saved — Remove' : 'Save Supervisor') + '</button>' +
        '<button class="btn btn-primary" data-sup-action="connect"><i class="fa-solid fa-paper-plane"></i> ' + (hasRequested(s.id) ? 'Requested — View' : 'Connect') + '</button>' +
        '<button class="btn btn-accent" data-sup-action="match"><i class="fa-solid fa-wand-magic-sparkles"></i> Match With Me</button>',
      size: 'lg',
      onClose: onCloseCb || null
    });

    entry.overlay.querySelector('[data-sup-action="save"]').addEventListener('click', function () {
      const now = TB.toggleSaveSupervisor(s.id);
      this.innerHTML = '<i class="fa-' + (now ? 'solid' : 'regular') + ' fa-bookmark"></i> ' + (now ? 'Saved — Remove' : 'Save Supervisor');
      refreshSectionHeader();
    });
    entry.overlay.querySelector('[data-sup-action="match"]').addEventListener('click', function () {
      entry.close();
      setTimeout(function () { openMatchQuiz(); }, 260);
    });
    entry.overlay.querySelector('[data-sup-action="connect"]').addEventListener('click', function () {
      openConnectModal(s.id, function () {
        // Refresh the Connect button label if the profile is still open.
        const btn = entry.overlay.querySelector('[data-sup-action="connect"]');
        if (btn && document.body.contains(btn)) {
          const now = hasRequested(s.id);
          btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> ' + (now ? 'Requested — View' : 'Connect');
        }
        refreshSectionHeader();
        renderGrids();
      });
    });
    return entry;
  }

  TB.toggleSaveSupervisor = function (id) {
    const ids = TB.state.get('tb_savedSupervisors', []) || [];
    const i = ids.indexOf(id);
    let saved;
    if (i > -1) { ids.splice(i, 1); saved = false; TB.toast('Supervisor removed from saved.', 'info'); }
    else { ids.push(id); saved = true; TB.toast('Supervisor saved.'); }
    TB.state.set('tb_savedSupervisors', ids);
    return saved;
  };

  /* --------------------------- Matching (demo) ---------------------------- */

  function matchScore(sup, ans) {
    let score = 0;
    // 1. Research area alignment (max 45).
    if (sup.areas.indexOf(ans.area) > -1) score += 45;
    else {
      const key = ans.area.toLowerCase();
      if (sup.interests.some(function (i) { return key.indexOf(i.toLowerCase()) > -1 || i.toLowerCase().indexOf(key.split(' ')[0]) > -1; })) score += 12;
    }
    // 2. Technology overlap with expertise (max 25).
    if (ans.techs.length) {
      const hits = ans.techs.filter(function (t) { return sup.expertise.indexOf(t) > -1; }).length;
      score += Math.round((hits / ans.techs.length) * 25);
    }
    // 3. Research type (max 15).
    score += sup.supervisionTypes.indexOf(ans.type) > -1 ? 15 : 4;
    // 4. Difficulty vs seniority heuristic (max 10).
    const senior = /Professor/i.test(sup.title) && !/Assistant/i.test(sup.title);
    if (ans.difficulty === 'Advanced') score += senior ? 10 : 7;
    else if (ans.difficulty === 'Intermediate') score += 9;
    else score += senior ? 8 : 10;
    return Math.max(8, Math.min(99, Math.round(score)));
  }

  const QUIZ_STEPS = [
    {
      key: 'area',
      question: 'Select your research area.',
      sub: 'Which broad field do you want to work in?',
      multi: false,
      options: window.TB_DATA.categories.map(function (c) { return { value: c.name, label: c.name, icon: c.icon }; })
    },
    {
      key: 'techs',
      question: 'Select technologies you know.',
      sub: 'Pick every tool you are comfortable with — at least one.',
      multi: true,
      options: window.TB_DATA.quizTechnologies.map(function (t) { return { value: t, label: t, icon: 'fa-microchip' }; })
    },
    {
      key: 'type',
      question: 'Select preferred research type.',
      sub: 'How do you want to spend the next year?',
      multi: false,
      options: [
        { value: 'Thesis', label: 'Thesis', icon: 'fa-book-open', hint: 'Full research with defence' },
        { value: 'Project', label: 'Project', icon: 'fa-diagram-project', hint: 'Build a working system' },
        { value: 'Review', label: 'Review', icon: 'fa-magnifying-glass', hint: 'Survey the literature' },
        { value: 'Experimental', label: 'Experimental', icon: 'fa-flask', hint: 'Run controlled experiments' }
      ]
    },
    {
      key: 'difficulty',
      question: 'Select preferred difficulty.',
      sub: 'Be honest — supervisors notice.',
      multi: false,
      options: [
        { value: 'Beginner', label: 'Beginner', icon: 'fa-seedling', hint: 'First research experience' },
        { value: 'Intermediate', label: 'Intermediate', icon: 'fa-gauge-high', hint: 'Comfortable, some challenge' },
        { value: 'Advanced', label: 'Advanced', icon: 'fa-rocket', hint: 'Ambitious, publication-ready' }
      ]
    }
  ];

  function openMatchQuiz() {
    const answers = { area: null, techs: [], type: null, difficulty: null };
    let step = 0;

    const entry = TB.modal.open({
      title: '<i class="fa-solid fa-wand-magic-sparkles"></i> Supervisor Matching',
      subtitle: 'Answer 4 quick questions — takes under a minute.',
      body: '<div class="quiz" data-role="quiz"></div>',
      size: 'md'
    });
    const quizEl = entry.overlay.querySelector('[data-role="quiz"]');

    function valid() {
      const k = QUIZ_STEPS[step].key;
      if (k === 'techs') return answers.techs.length > 0;
      return !!answers[k];
    }

    function renderStep() {
      const st = QUIZ_STEPS[step];
      const dots = QUIZ_STEPS.map(function (s, i) {
        const active = i === step;
        const complete = i < step;
        return '<span class="q-dot' + (active ? ' active' : '') + (complete ? ' done' : '') + '">' +
          (complete ? '<i class="fa-solid fa-check"></i>' : (i + 1)) + '</span>' +
          (i < QUIZ_STEPS.length - 1 ? '<span class="q-line' + (i < step ? ' done' : '') + '"></span>' : '');
      }).join('');

      const opts = st.options.map(function (o) {
        const on = st.multi ? answers.techs.indexOf(o.value) > -1 : answers[st.key] === o.value;
        return '<button type="button" class="quiz-opt' + (on ? ' sel' : '') + '" data-value="' + TB.esc(o.value) + '" aria-pressed="' + on + '">' +
          '  <span class="quiz-opt-icon"><i class="fa-solid ' + o.icon + '"></i></span>' +
          '  <span class="quiz-opt-label">' + TB.esc(o.label) + (o.hint ? '<small>' + TB.esc(o.hint) + '</small>' : '') + '</span>' +
          '  <i class="fa-solid fa-circle-check quiz-check" aria-hidden="true"></i>' +
          '</button>';
      }).join('');

      quizEl.innerHTML =
        '<div class="q-dots">' + dots + '</div>' +
        '<h3 class="quiz-q">' + TB.esc(st.question) + '</h3>' +
        '<p class="quiz-sub">' + TB.esc(st.sub) + '</p>' +
        '<div class="quiz-options' + (st.multi ? ' quiz-options-chips' : '') + '">' + opts + '</div>' +
        '<p class="quiz-hint" data-role="hint" hidden>Please select at least one option to continue.</p>' +
        '<div class="quiz-nav">' +
        (step > 0 ? '<button class="btn btn-ghost" data-quiz="back"><i class="fa-solid fa-chevron-left"></i> Back</button>' : '<span></span>') +
        '<span class="quiz-step-label">Step ' + (step + 1) + ' of ' + QUIZ_STEPS.length + '</span>' +
        (step < QUIZ_STEPS.length - 1
          ? '<button class="btn btn-primary" data-quiz="next">Next <i class="fa-solid fa-chevron-right"></i></button>'
          : '<button class="btn btn-accent" data-quiz="submit"><i class="fa-solid fa-wand-magic-sparkles"></i> See My Matches</button>') +
        '</div>';
    }

    function renderResults() {
      const scored = window.TB_DATA.supervisors
        .map(function (s) { return { sup: s, score: matchScore(s, answers) }; })
        .filter(function (m) { return m.score >= 40; })
        .sort(function (a, b) { return b.score - a.score; });

      const rows = scored.length ? scored.map(function (m, i) {
        const req = hasRequested(m.sup.id);
        return '<div class="match-row card-in" style="animation-delay:' + (i * 70) + 'ms">' +
          '  ' + avatarHTML(m.sup, 'avatar-sm') +
          '  <div class="match-info">' +
          '    <h4>' + TB.esc(m.sup.name) + '</h4>' +
          '    <p>' + TB.esc(m.sup.title) + ' · ' + TB.esc(m.sup.university) + '</p>' +
          '    <div class="match-bar-track"><div class="match-bar-fill" style="width:0%" data-w="' + m.score + '%"></div></div>' +
          '  </div>' +
          '  <div class="match-score"><strong>' + m.score + '%</strong><span>Research Match</span></div>' +
          '  <div class="match-actions">' +
          '    <button class="btn btn-outline btn-sm" data-match-view="' + m.sup.id + '">View Profile</button>' +
          '    <button class="btn btn-sm ' + (req ? 'btn-outline' : 'btn-primary') + '" data-match-connect="' + m.sup.id + '">' +
          (req ? '<i class="fa-solid fa-check"></i> Requested' : '<i class="fa-solid fa-paper-plane"></i> Connect') + '</button>' +
          '  </div>' +
          '</div>';
      }).join('') :
        '<div class="empty-state">' +
        '  <div class="empty-icon"><i class="fa-solid fa-user-slash"></i></div>' +
        '  <h3>No strong matches.</h3>' +
        '  <p>No supervisors scored above 40% for your combination. Try different answers — or browse all supervisors manually.</p>' +
        '  <button class="btn btn-primary" data-quiz="restart"><i class="fa-solid fa-rotate-left"></i> Restart Questionnaire</button>' +
        '</div>';

      quizEl.innerHTML =
        '<div class="match-results">' +
        '  <div class="match-disclaimer"><i class="fa-solid fa-circle-info"></i> Demo matching based on selected research interests. This is a frontend prototype — not an actual academic recommendation system.</div>' +
        (scored.length ? '<p class="match-summary">Based on your answers, these supervisors align best with your research profile:</p>' : '') +
        '  ' + rows +
        (scored.length ? '<div class="quiz-nav"><span></span><span></span><button class="btn btn-ghost" data-quiz="restart"><i class="fa-solid fa-rotate-left"></i> Retake Questionnaire</button></div>' : '') +
        '</div>';

      requestAnimationFrame(function () {
        setTimeout(function () {
          quizEl.querySelectorAll('.match-bar-fill').forEach(function (b) {
            b.style.width = b.dataset.w;
          });
        }, 60);
      });

      // Update modal title for the results step.
      const t = entry.overlay.querySelector('.modal-title');
      if (t) t.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Your Matches';
      const st = entry.overlay.querySelector('.modal-subtitle');
      if (st) st.textContent = scored.length ? scored.length + ' supervisor' + (scored.length > 1 ? 's' : '') + ' matched above 40%' : 'No matches above 40%';
    }

    quizEl.addEventListener('click', function (e) {
      const opt = e.target.closest('.quiz-opt');
      if (opt) {
        const st = QUIZ_STEPS[step];
        if (st.multi) {
          const v = opt.dataset.value;
          const i = answers.techs.indexOf(v);
          if (i > -1) answers.techs.splice(i, 1); else answers.techs.push(v);
        } else {
          answers[st.key] = (answers[st.key] === opt.dataset.value) ? null : opt.dataset.value;
        }
        quizEl.querySelector('[data-role="hint"]').hidden = true;
        renderStep();
        return;
      }

      const nav = e.target.closest('[data-quiz]');
      if (!nav) return;
      const act = nav.dataset.quiz;
      if (act === 'back' && step > 0) { step--; renderStep(); }
      else if (act === 'next') {
        if (!valid()) { const h = quizEl.querySelector('[data-role="hint"]'); if (h) h.hidden = false; return; }
        step++; renderStep();
      } else if (act === 'submit') {
        if (!valid()) { const h = quizEl.querySelector('[data-role="hint"]'); if (h) h.hidden = false; return; }
        renderResults();
      } else if (act === 'restart') {
        answers.area = null; answers.techs = []; answers.type = null; answers.difficulty = null; step = 0;
        const t = entry.overlay.querySelector('.modal-title');
        if (t) t.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Supervisor Matching';
        const st = entry.overlay.querySelector('.modal-subtitle');
        if (st) st.textContent = 'Answer 4 quick questions — takes under a minute.';
        renderStep();
      } else if (act === 'view-profile' || nav.dataset.matchView) {
        // handled below via data-match-view
      }
    });

    quizEl.addEventListener('click', function (e) {
      const v = e.target.closest('[data-match-view]');
      if (v) { openSupervisorModal(parseInt(v.dataset.matchView, 10)); return; }
      const c = e.target.closest('[data-match-connect]');
      if (c) {
        const id = parseInt(c.dataset.matchConnect, 10);
        openConnectModal(id, function () {
          // Re-render results so the Connect button flips to "Requested".
          if (document.body.contains(quizEl)) {
            const cur = entry.overlay.querySelector('.modal-title');
            const onResults = cur && cur.textContent.indexOf('Matches') > -1;
            if (onResults) renderResults();
          }
          refreshSectionHeader();
          renderGrids();
        });
      }
    });

    renderStep();
  }

  /* ------------------------- Connect / request flow ----------------------- */
  /* The request is validated here, stored in localStorage for instant UI
     feedback, and then synced to Supabase by js/api.js
     (POST /api/connection-requests). */

  const CONNECT_EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function getConnectRequests() {
    return TB.state.get('tb_connectRequests', []) || [];
  }

  function hasRequested(supId) {
    return getConnectRequests().some(function (r) { return r.supId === supId; });
  }

  function connectFieldError(input, msg) {
    const wrap = input.closest('.field');
    const err = wrap ? wrap.querySelector('.field-error') : null;
    if (wrap) wrap.classList.toggle('invalid', !!msg);
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    if (err) err.textContent = msg || '';
  }

  function openConnectModal(supId, onDoneCb) {
    const s = window.TB_DATA.supervisors.find(function (x) { return x.id === supId; });
    if (!s) return null;

    const existing = getConnectRequests().filter(function (r) { return r.supId === supId; })[0];

    const topicOpts = s.suggestedTopics.map(function (t) {
      return '<option>' + TB.esc(t) + '</option>';
    }).join('');

    const entry = TB.modal.open({
      title: '<i class="fa-solid fa-paper-plane"></i> Connect with ' + TB.esc(s.name),
      subtitle: TB.esc(s.title) + ' · ' + TB.esc(s.university),
      body: '<div data-role="connect-body"></div>',
      size: 'md',
      onClose: onDoneCb || null
    });
    const bodyEl = entry.overlay.querySelector('[data-role="connect-body"]');

    function renderForm() {
      // If the visitor is logged in, prefill their own name and email. This is
      // only possible because accounts now live in Supabase: js/api.js stores
      // the profile in `tb_user` after login / sign-up.
      const me = TB.state.get('tb_user', null) || {};
      const nameValue = me.name ? ' value="' + TB.esc(me.name) + '"' : '';
      const emailValue = me.email ? ' value="' + TB.esc(me.email) + '"' : '';

      bodyEl.innerHTML =
        '<div class="connect-target">' +
        '  ' + avatarHTML(s, 'avatar-sm') +
        '  <div><h4>' + TB.esc(s.name) + '</h4>' +
        '  <p><i class="fa-solid fa-envelope"></i> ' + TB.esc(s.email) + ' · <i class="fa-solid fa-location-dot"></i> ' + TB.esc(s.office) + '</p></div>' +
        '</div>' +
        '<form class="auth-form" data-role="connect-form" novalidate>' +
        '  <div class="field"><label for="cf-name">Your name</label>' +
        '    <input id="cf-name" name="name" type="text" autocomplete="name"' + nameValue + ' placeholder="e.g. Nasif Shahrear"><p class="field-error"></p></div>' +
        '  <div class="field"><label for="cf-email">Your email</label>' +
        '    <input id="cf-email" name="email" type="email" autocomplete="email"' + emailValue + ' placeholder="you@university.edu"><p class="field-error"></p></div>' +
        '  <div class="field"><label for="cf-topic">Proposed topic</label>' +
        '    <select id="cf-topic" name="topic"><option value="">Select one of their suggested topics…</option>' + topicOpts + '<option value="__other">Other — I will describe it below</option></select><p class="field-error"></p></div>' +
        '  <div class="field"><label for="cf-msg">Message to supervisor</label>' +
        '    <textarea id="cf-msg" name="message" placeholder="Who are you, what do you want to work on, and why them? (min 20 characters)"></textarea><p class="field-error"></p></div>' +
        '  <p class="quiz-sub" style="margin:0"><i class="fa-solid fa-circle-info"></i> Your request is saved to ThesisBridge BD’s database. It is not emailed automatically — the supervisor’s address is shown above so you can email them directly too.</p>' +
        '  <div class="quiz-nav"><span></span><span></span>' +
        '    <button type="submit" class="btn btn-primary"><i class="fa-solid fa-paper-plane"></i> Send Request</button></div>' +
        '</form>';

      bodyEl.querySelector('[data-role="connect-form"]').addEventListener('submit', function (ev) {
        ev.preventDefault();
        const f = ev.target;
        let ok = true;
        if (f.name.value.trim().length < 3) { connectFieldError(f.name, 'Please enter your full name (at least 3 characters).'); ok = false; }
        else connectFieldError(f.name, '');
        if (!f.email.value.trim()) { connectFieldError(f.email, 'Please enter your email address.'); ok = false; }
        else if (!CONNECT_EMAIL_RE.test(f.email.value.trim())) { connectFieldError(f.email, 'Please enter a valid email address.'); ok = false; }
        else connectFieldError(f.email, '');
        if (!f.topic.value) { connectFieldError(f.topic, 'Please select a proposed topic.'); ok = false; }
        else connectFieldError(f.topic, '');
        if (f.message.value.trim().length < 20) { connectFieldError(f.message, 'Please write at least 20 characters so the supervisor takes you seriously.'); ok = false; }
        else connectFieldError(f.message, '');
        if (!ok) { TB.toast('Please fix the highlighted fields.', 'error'); return; }

        const reqs = getConnectRequests().filter(function (r) { return r.supId !== supId; });
        reqs.push({
          supId: supId,
          name: f.name.value.trim(),
          email: f.email.value.trim(),
          topic: f.topic.options[f.topic.selectedIndex].text,
          message: f.message.value.trim(),
          date: new Date().toISOString()
        });
        TB.state.set('tb_connectRequests', reqs);
        TB.toast('Connection request sent to ' + s.name + '.');
        renderSuccess();
      });
    }

    function renderSuccess() {
      const r = getConnectRequests().filter(function (x) { return x.supId === supId; })[0] || {};
      const when = r.date ? new Date(r.date).toLocaleString() : '';
      bodyEl.innerHTML =
        '<div class="connect-success">' +
        '  <div class="ok-icon"><i class="fa-solid fa-check"></i></div>' +
        '  <h4>Request sent!</h4>' +
        '  <p>' + TB.esc(s.name) + ' can now see your proposal. ' +
        (when ? 'Sent ' + TB.esc(when) + '.' : '') + '</p>' +
        '  <div class="req-summary"><strong>Topic:</strong> ' + TB.esc(r.topic || '—') +
        '  <br><strong>From:</strong> ' + TB.esc(r.name || '—') + ' (' + TB.esc(r.email || '—') + ')</div>' +
        '  <p>Tip: email them directly at <strong>' + TB.esc(s.email) + '</strong> and mention one of their papers.</p>' +
        '  <div class="quiz-nav"><button class="btn btn-ghost" data-role="connect-withdraw">Withdraw request</button>' +
        '  <span></span><button class="btn btn-primary" data-role="connect-done">Done</button></div>' +
        '</div>';
      bodyEl.querySelector('[data-role="connect-done"]').addEventListener('click', function () { entry.close(); });
      bodyEl.querySelector('[data-role="connect-withdraw"]').addEventListener('click', function () {
        TB.state.set('tb_connectRequests', getConnectRequests().filter(function (x) { return x.supId !== supId; }));
        TB.toast('Connection request withdrawn.', 'info');
        entry.close();
      });
    }

    if (existing) renderSuccess();
    else renderForm();
    return entry;
  }

  /* ------------------------- Saved supervisors modal ---------------------- */

  function openSavedSupervisors() {
    const ids = TB.state.get('tb_savedSupervisors', []) || [];
    const list = window.TB_DATA.supervisors.filter(function (s) { return ids.indexOf(s.id) > -1; });

    const body = list.length
      ? '<div class="saved-list">' + list.map(function (s) {
          return '<div class="saved-row">' +
            '  <div class="saved-info sup-id">' + avatarHTML(s, 'avatar-sm') +
            '    <div><h4>' + TB.esc(s.name) + '</h4><p class="sup-title">' + TB.esc(s.title) + ' · ' + TB.esc(s.university) + '</p></div>' +
            '  </div>' +
            '  <div class="saved-actions">' +
            '    <button class="btn btn-outline btn-sm" data-supsaved="view" data-id="' + s.id + '">View Profile</button>' +
            '    <button class="icon-btn" data-supsaved="remove" data-id="' + s.id + '" aria-label="Remove ' + TB.esc(s.name) + '"><i class="fa-solid fa-trash-can"></i></button>' +
            '  </div>' +
            '</div>';
        }).join('') + '</div>'
      : '<div class="empty-state">' +
        '  <div class="empty-icon"><i class="fa-regular fa-bookmark"></i></div>' +
        '  <h3>No saved supervisors.</h3>' +
        '  <p>You haven\u2019t saved any supervisors yet. Browse profiles and tap the bookmark icon.</p>' +
        '  <button class="btn btn-primary" data-supsaved="close">Browse Supervisors</button>' +
        '</div>';

    const entry = TB.modal.open({
      title: '<i class="fa-solid fa-bookmark"></i> Saved Supervisors',
      subtitle: list.length ? list.length + ' saved' : '',
      body: body,
      size: 'md'
    });

    entry.overlay.addEventListener('click', function (e) {
      const b = e.target.closest('[data-supsaved]');
      if (!b) return;
      const act = b.dataset.supsaved;
      if (act === 'remove') {
        TB.toggleSaveSupervisor(parseInt(b.dataset.id, 10));
        entry.close(); refreshSectionHeader(); renderGrids();
      } else if (act === 'view') {
        entry.close();
        setTimeout(function () { openSupervisorModal(parseInt(b.dataset.id, 10)); }, 240);
      } else if (act === 'close') entry.close();
    });
  }

  /* ------------------------------ Section -------------------------------- */

  const grids = [];

  function renderGrids() { grids.forEach(function (fn) { fn(); }); }

  function refreshSectionHeader() {
    document.querySelectorAll('[data-role="saved-sup-count"]').forEach(function (el) {
      const n = (TB.state.get('tb_savedSupervisors', []) || []).length;
      el.textContent = n;
      el.hidden = n === 0 && el.hasAttribute('data-hide-zero');
    });
  }

  function renderSupervisors(mount) {
    const D = window.TB_DATA;
    const unis = Array.from(new Set(D.supervisors.map(function (s) { return s.university; }))).sort();
    const deps = Array.from(new Set(D.supervisors.map(function (s) { return s.department; }))).sort();
    const state = { q: '', university: 'All', department: 'All', areas: [], exps: [] };

    mount.innerHTML =
      '<div class="match-cta card reveal">' +
      '  <div class="match-cta-text">' +
      '    <h3><i class="fa-solid fa-wand-magic-sparkles"></i> Not sure which supervisor fits you?</h3>' +
      '    <p>Answer 4 quick questions about your area, tools and style — we\u2019ll rank supervisors by match percentage.</p>' +
      '  </div>' +
      '  <button class="btn btn-accent" data-action="start-match">Match Me With a Supervisor</button>' +
      '</div>' +

      '<div class="explorer-bar sup-bar">' +
      '  <div class="search-box">' +
      '    <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>' +
      '    <input type="search" class="search-input" data-role="sup-search" placeholder="Search name, interest, expertise, university…" aria-label="Search supervisors">' +
      '    <button class="search-clear" data-role="sup-search-clear" aria-label="Clear search" hidden><i class="fa-solid fa-xmark"></i></button>' +
      '  </div>' +
      '  <div class="bar-right">' +
      '    <select class="select" data-role="f-university" aria-label="Filter by university"><option value="All">All Universities</option>' +
      unis.map(function (u) { return '<option>' + TB.esc(u) + '</option>'; }).join('') + '</select>' +
      '    <select class="select" data-role="f-department" aria-label="Filter by department"><option value="All">All Departments</option>' +
      deps.map(function (d) { return '<option>' + TB.esc(d) + '</option>'; }).join('') + '</select>' +
      '    <button class="btn btn-outline btn-sm filters-toggle" data-role="sup-filters-toggle" aria-expanded="false">' +
      '      <i class="fa-solid fa-sliders"></i> Filters <span class="count-pill" data-role="sup-filter-count" hidden>0</span>' +
      '    </button>' +
      '  </div>' +
      '</div>' +

      '<div class="filters-panel" data-role="sup-filters">' +
      '  <div class="filter-group">' +
      '    <div class="filter-group-head"><i class="fa-solid fa-flask"></i> Research Area</div>' +
      '    <div class="chip-row">' + D.categories.map(function (c) { return '<button type="button" class="chip" data-g="areas" data-value="' + TB.esc(c.name) + '" aria-pressed="false">' + TB.esc(c.name) + '</button>'; }).join('') + '</div>' +
      '  </div>' +
      '  <div class="filter-group">' +
      '    <div class="filter-group-head"><i class="fa-solid fa-star"></i> Expertise</div>' +
      '    <div class="chip-row">' + D.expertiseOptions.map(function (x) { return '<button type="button" class="chip" data-g="exps" data-value="' + TB.esc(x) + '" aria-pressed="false">' + TB.esc(x) + '</button>'; }).join('') + '</div>' +
      '  </div>' +
      '  <div class="filters-foot">' +
      '    <span class="results-info" data-role="sup-count"></span>' +
      '    <div class="filters-foot-btns">' +
      '      <button class="btn btn-ghost btn-sm" data-role="sup-saved"><i class="fa-regular fa-bookmark"></i> Saved (<span data-role="saved-sup-count">0</span>)</button>' +
      '      <button class="btn btn-ghost btn-sm" data-role="sup-clear"><i class="fa-solid fa-rotate-left"></i> Reset Filters</button>' +
      '    </div>' +
      '  </div>' +
      '</div>' +

      '<div class="cards-grid" data-role="sup-grid"></div>';

    const grid = mount.querySelector('[data-role="sup-grid"]');
    const search = mount.querySelector('[data-role="sup-search"]');
    const searchClear = mount.querySelector('[data-role="sup-search-clear"]');
    const uniSel = mount.querySelector('[data-role="f-university"]');
    const depSel = mount.querySelector('[data-role="f-department"]');
    const countEl = mount.querySelector('[data-role="sup-count"]');
    const filterCount = mount.querySelector('[data-role="sup-filter-count"]');
    const filtersPanel = mount.querySelector('[data-role="sup-filters"]');
    const filtersToggle = mount.querySelector('[data-role="sup-filters-toggle"]');

    function results() {
      const q = state.q.trim().toLowerCase();
      return D.supervisors.filter(function (s) {
        if (q) {
          const hay = (s.name + ' ' + s.title + ' ' + s.university + ' ' + s.department + ' ' +
            s.interests.join(' ') + ' ' + s.expertise.join(' ') + ' ' + s.areas.join(' ')).toLowerCase();
          if (hay.indexOf(q) === -1) return false;
        }
        if (state.university !== 'All' && s.university !== state.university) return false;
        if (state.department !== 'All' && s.department !== state.department) return false;
        if (state.areas.length && !s.areas.some(function (a) { return state.areas.indexOf(a) > -1; })) return false;
        if (state.exps.length && !s.expertise.some(function (x) { return state.exps.indexOf(x) > -1; })) return false;
        return true;
      });
    }

    function renderGrid() {
      const list = results();
      const savedIds = TB.state.get('tb_savedSupervisors', []) || [];

      grid.innerHTML = list.length
        ? list.map(function (s, i) { return supCard(s, i, savedIds); }).join('')
        : '<div class="empty-state">' +
          '  <div class="empty-icon"><i class="fa-solid fa-user-slash"></i></div>' +
          '  <h3>No supervisors found.</h3>' +
          '  <p>No supervisors match your current criteria. Try widening your filters.</p>' +
          '  <button class="btn btn-primary" data-role="sup-clear-inline"><i class="fa-solid fa-rotate-left"></i> Reset Filters</button>' +
          '</div>';

      countEl.textContent = 'Showing ' + list.length + ' of ' + D.supervisors.length + ' supervisors';
      const n = state.areas.length + state.exps.length +
        (state.university !== 'All' ? 1 : 0) + (state.department !== 'All' ? 1 : 0) + (state.q ? 1 : 0);
      filterCount.textContent = n;
      filterCount.hidden = n === 0;

      mount.querySelectorAll('.chip[data-g]').forEach(function (c) {
        const on = state[c.dataset.g].indexOf(c.dataset.value) > -1;
        c.classList.toggle('active', on);
        c.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }

    function clearAll(toast) {
      state.q = ''; state.university = 'All'; state.department = 'All'; state.areas = []; state.exps = [];
      search.value = ''; searchClear.hidden = true;
      uniSel.value = 'All'; depSel.value = 'All';
      renderGrid();
      if (toast !== false) TB.toast('Filters reset — showing all supervisors.', 'info');
    }

    search.addEventListener('input', TB.debounce(function () {
      state.q = search.value; searchClear.hidden = !search.value; renderGrid();
    }, 140));
    searchClear.addEventListener('click', function () {
      search.value = ''; state.q = ''; searchClear.hidden = true; renderGrid(); search.focus();
    });
    uniSel.addEventListener('change', function () { state.university = uniSel.value; renderGrid(); });
    depSel.addEventListener('change', function () { state.department = depSel.value; renderGrid(); });
    filtersToggle.addEventListener('click', function () {
      const open = filtersPanel.classList.toggle('open');
      filtersToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    mount.addEventListener('click', function (e) {
      const c = e.target.closest('.chip[data-g]');
      if (c) {
        const arr = state[c.dataset.g];
        const i = arr.indexOf(c.dataset.value);
        if (i > -1) arr.splice(i, 1); else arr.push(c.dataset.value);
        renderGrid();
        return;
      }
      if (e.target.closest('[data-role="sup-clear"], [data-role="sup-clear-inline"]')) { clearAll(); return; }
      if (e.target.closest('[data-role="sup-saved"]')) { openSavedSupervisors(); return; }
      if (e.target.closest('[data-action="start-match"]')) { openMatchQuiz(); return; }

      const view = e.target.closest('[data-action="view-sup"]');
      if (view) { openSupervisorModal(parseInt(view.dataset.id, 10)); return; }

      const save = e.target.closest('[data-action="toggle-save-sup"]');
      if (save) {
        TB.toggleSaveSupervisor(parseInt(save.dataset.id, 10));
        renderGrid(); refreshSectionHeader();
      }
    });

    grids.push(renderGrid);
    document.addEventListener('tb:change', function (e) {
      if (e.detail.key === 'tb_savedSupervisors' || e.detail.key === 'tb_connectRequests') { renderGrid(); refreshSectionHeader(); }
    });

    refreshSectionHeader();
    renderGrid();
    if (typeof TB.observeReveals === 'function') TB.observeReveals(mount);
  }

  TB.openSupervisorModal = openSupervisorModal;
  TB.openMatchQuiz = openMatchQuiz;
  TB.openConnectModal = openConnectModal;
  TB.hasRequestedSupervisor = hasRequested;
  TB.getConnectRequests = getConnectRequests;

  function boot() {
    document.querySelectorAll('[data-mount="supervisors"]').forEach(renderSupervisors);
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
