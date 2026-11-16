/* ==========================================================================
   ThesisBridge BD — Core Module (main.js)
   State (localStorage-backed) · Toasts · Reusable Modal System · Theme
   Navbar · Auth modals · Saved Ideas panel · Idea detail modal · FAQ · Stats
   ========================================================================== */

window.TB = window.TB || {};

(function (TB) {
  'use strict';

  /* ------------------------------- Utilities ---------------------------- */

  TB.esc = function (str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  };

  TB.debounce = function (fn, ms) {
    let t;
    return function () {
      const args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  };

  TB.prefersReducedMotion = function () {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  };

  TB.diffClass = function (d) {
    return { Beginner: 'badge-beginner', Intermediate: 'badge-intermediate', Advanced: 'badge-advanced' }[d] || 'badge-soft';
  };

  TB.catIcon = function (name) {
    const c = (window.TB_DATA.categories || []).find(function (x) { return x.name === name; });
    return c ? c.icon : 'fa-lightbulb';
  };

  TB.initials = function (name) {
    return name.split(/\s+/).filter(function (w) { return !/^(dr\.?|prof\.?|md\.?|mrs\.?|ms\.?)$/i.test(w); })
      .slice(0, 2).map(function (w) { return w[0]; }).join('').toUpperCase() || name[0].toUpperCase();
  };

  /* --------------------------------- State -------------------------------
     Thin wrapper over localStorage. Swap the two functions below for API
     calls when a backend exists — every module reads/writes through here.  */

  const mem = {};
  TB.state = {
    get: function (key, def) {
      try {
        const raw = localStorage.getItem(key);
        if (raw !== null) return JSON.parse(raw);
      } catch (e) { /* storage unavailable */ }
      return key in mem ? mem[key] : (def !== undefined ? def : null);
    },
    set: function (key, val) {
      try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) { mem[key] = val; }
      document.dispatchEvent(new CustomEvent('tb:change', { detail: { key: key, value: val } }));
    }
  };

  /* --------------------------------- Toasts ------------------------------ */

  let toastStack = null;

  function ensureToastStack() {
    if (!toastStack) {
      toastStack = document.createElement('div');
      toastStack.className = 'toast-stack';
      toastStack.setAttribute('aria-live', 'polite');
      document.body.appendChild(toastStack);
    }
    return toastStack;
  }

  const TOAST_ICONS = {
    success: 'fa-circle-check',
    info: 'fa-circle-info',
    warning: 'fa-triangle-exclamation',
    error: 'fa-circle-xmark'
  };

  TB.toast = function (message, type) {
    type = type || 'success';
    const stack = ensureToastStack();
    while (stack.children.length >= 4) stack.firstElementChild.remove();

    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.setAttribute('role', 'status');
    el.innerHTML =
      '<i class="fa-solid ' + TOAST_ICONS[type] + '" aria-hidden="true"></i>' +
      '<div class="toast-msg">' + TB.esc(message) + '</div>' +
      '<button class="toast-close" aria-label="Dismiss notification"><i class="fa-solid fa-xmark"></i></button>';

    stack.appendChild(el);
    requestAnimationFrame(function () { el.classList.add('show'); });

    let gone = false;
    function dismiss() {
      if (gone) return;
      gone = true;
      el.classList.remove('show');
      setTimeout(function () { el.remove(); }, 320);
    }
    const timer = setTimeout(dismiss, 3400);
    el.querySelector('.toast-close').addEventListener('click', function () {
      clearTimeout(timer); dismiss();
    });
  };

  /* --------------------------- Reusable Modal System --------------------- */

  TB.modal = (function () {
    const stack = [];
    let root = null;

    function ensureRoot() {
      if (!root) { root = document.createElement('div'); root.id = 'modalRoot'; document.body.appendChild(root); }
      return root;
    }

    function lockScroll() { document.documentElement.classList.add('modal-open'); }
    function unlockScrollIfEmpty() {
      if (!root || !root.childElementCount) document.documentElement.classList.remove('modal-open');
    }

    function open(opts) {
      const o = Object.assign({ title: '', subtitle: '', body: '', footer: '', size: 'md', onClose: null }, opts);
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay';
      overlay.innerHTML =
        '<div class="modal modal-' + o.size + '" role="dialog" aria-modal="true"' +
        (o.title ? ' aria-label="' + TB.esc(o.title.replace(/<[^>]*>/g, '')) + '"' : '') + '>' +
        '  <div class="modal-head">' +
        '    <div class="modal-titles">' +
        (o.title ? '<h3 class="modal-title">' + o.title + '</h3>' : '') +
        (o.subtitle ? '<p class="modal-subtitle">' + o.subtitle + '</p>' : '') +
        '    </div>' +
        '    <button class="icon-btn modal-close" aria-label="Close dialog"><i class="fa-solid fa-xmark"></i></button>' +
        '  </div>' +
        '  <div class="modal-body">' + o.body + '</div>' +
        (o.footer ? '<div class="modal-footer">' + o.footer + '</div>' : '') +
        '</div>';

      ensureRoot().appendChild(overlay);
      requestAnimationFrame(function () { overlay.classList.add('show'); });

      const lastFocus = document.activeElement;
      lockScroll();

      const entry = { overlay: overlay, close: close };
      let closed = false;

      function close() {
        if (closed) return;
        closed = true;
        overlay.classList.remove('show');
        setTimeout(function () { overlay.remove(); unlockScrollIfEmpty(); }, 230);
        const i = stack.indexOf(entry);
        if (i > -1) stack.splice(i, 1);
        if (lastFocus && typeof lastFocus.focus === 'function') { try { lastFocus.focus(); } catch (e) { /* detached */ } }
        if (typeof o.onClose === 'function') o.onClose();
      }

      overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
      overlay.querySelector('.modal-close').addEventListener('click', close);

      const firstField = overlay.querySelector('.modal-body input, .modal-body select, .modal-body textarea');
      const focusTarget = firstField || overlay.querySelector('.modal-close');
      if (focusTarget) setTimeout(function () { focusTarget.focus(); }, 60);

      stack.push(entry);
      return entry;
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && stack.length) {
        e.preventDefault();
        stack[stack.length - 1].close();
      }
    });

    return {
      open: open,
      closeAll: function () { stack.slice().forEach(function (s) { s.close(); }); },
      count: function () { return stack.length; }
    };
  })();

  /* --------------------------------- Theme ------------------------------- */

  function initTheme() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;
    const apply = function (theme, persist) {
      document.documentElement.dataset.theme = theme;
      const dark = theme === 'dark';
      btn.innerHTML = '<i class="fa-solid ' + (dark ? 'fa-sun' : 'fa-moon') + '"></i>';
      btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
      if (persist) TB.state.set('tb_theme', theme);
    };
    apply(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light', false);
    btn.addEventListener('click', function () {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(next, true);
      TB.toast(next === 'dark' ? 'Dark mode enabled.' : 'Light mode enabled.', 'info');
    });
  }

  /* -------------------------------- Navbar ------------------------------- */

  function closeDrawer() {
    const links = document.getElementById('navLinks');
    const scrim = document.getElementById('navScrim');
    const burger = document.getElementById('navBurger');
    if (!links) return;
    links.classList.remove('open');
    if (scrim) scrim.classList.remove('show');
    if (burger) { burger.setAttribute('aria-expanded', 'false'); burger.innerHTML = '<i class="fa-solid fa-bars"></i>'; }
    document.documentElement.classList.remove('nav-open');
  }

  function initNav() {
    const burger = document.getElementById('navBurger');
    const links = document.getElementById('navLinks');
    const scrim = document.getElementById('navScrim');
    const navbar = document.getElementById('navbar');

    if (burger && links) {
      burger.addEventListener('click', function () {
        const open = links.classList.toggle('open');
        if (scrim) scrim.classList.toggle('show', open);
        burger.setAttribute('aria-expanded', open ? 'true' : 'false');
        burger.innerHTML = '<i class="fa-solid ' + (open ? 'fa-xmark' : 'fa-bars') + '"></i>';
        document.documentElement.classList.toggle('nav-open', open);
      });
      if (scrim) scrim.addEventListener('click', closeDrawer);
    }

    // Smart links: if the target section exists on this page, smooth-scroll;
    // otherwise navigate to the dedicated page.
    document.querySelectorAll('.nav-link').forEach(function (a) {
      a.addEventListener('click', function () {
        const sel = a.dataset.target;
        if (sel) {
          const t = document.querySelector(sel);
          if (t) {
            a.preventDefault();
            t.scrollIntoView({ behavior: TB.prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
          }
        }
        closeDrawer();
      });
    });

    // Active link for the current page.
    const page = document.body.dataset.page;
    document.querySelectorAll('.nav-link').forEach(function (a) {
      a.classList.toggle('active', a.dataset.pageMatch === page);
    });

    // Shadow when scrolled.
    if (navbar) {
      const onScroll = function () { navbar.classList.toggle('scrolled', window.scrollY > 8); };
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }

    // Scroll-spy on the homepage: highlight the section in view; when none
    // of the monitored sections is in the band, fall back to the page link.
    if (page === 'home') {
      const inBand = new Set();
      const setActive = function (id) {
        document.querySelectorAll('.nav-link').forEach(function (a) {
          a.classList.toggle('active', id ? a.dataset.target === id : a.dataset.pageMatch === page);
        });
      };
      const spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) inBand.add(en.target.id);
          else inBand.delete(en.target.id);
        });
        setActive(inBand.size ? '#' + Array.from(inBand).pop() : null);
      }, { rootMargin: '-40% 0px -55% 0px' });
      ['#research-explorer', '#supervisor-match', '#roadmap'].forEach(function (sel) {
        const el = document.querySelector(sel);
        if (el) spy.observe(el);
      });
    }
  }

  /* ------------------------------- Auth ---------------------------------- */

  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function fieldError(input, msg) {
    const wrap = input.closest('.field');
    const err = wrap ? wrap.querySelector('.field-error') : null;
    if (wrap) wrap.classList.toggle('invalid', !!msg);
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    if (err) err.textContent = msg || '';
  }

  function openLogin() {
    TB.modal.open({
      title: '<i class="fa-solid fa-right-to-bracket"></i> Welcome back',
      subtitle: 'Log in to your ThesisBridge BD account.',
      body:
        '<form class="auth-form" id="loginForm" novalidate>' +
        '  <div class="field">' +
        '    <label for="li-email">Email</label>' +
        '    <input id="li-email" name="email" type="email" autocomplete="email" placeholder="you@university.edu">' +
        '    <p class="field-error"></p>' +
        '  </div>' +
        '  <div class="field">' +
        '    <label for="li-pass">Password</label>' +
        '    <input id="li-pass" name="password" type="password" autocomplete="current-password" placeholder="Your password">' +
        '    <p class="field-error"></p>' +
        '  </div>' +
        '  <button class="btn btn-primary btn-block" type="submit">Login</button>' +
        '  <div class="auth-links">' +
        '    <button type="button" data-auth-link="forgot">Forgot Password?</button>' +
        '    <span aria-hidden="true">·</span>' +
        '    <button type="button" data-auth-link="signup">Create Account</button>' +
        '  </div>' +
        '</form>' +
        '<p class="auth-note"><i class="fa-solid fa-circle-info"></i> Accounts are stored in Supabase — passwords are handled by Supabase Auth, never by this page.</p>',
      size: 'sm',
      onClose: null
    });

    const form = document.getElementById('loginForm');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const email = form.email, pass = form.password;
      let ok = true;
      if (!email.value.trim()) { fieldError(email, 'Please enter your email address.'); ok = false; }
      else if (!EMAIL_RE.test(email.value.trim())) { fieldError(email, 'Please enter a valid email address.'); ok = false; }
      else fieldError(email, '');
      if (!pass.value) { fieldError(pass, 'Please enter your password.'); ok = false; }
      else if (pass.value.length < 6) { fieldError(pass, 'Password must be at least 6 characters.'); ok = false; }
      else fieldError(pass, '');
      if (!ok) return;

      if (!TB.auth || typeof TB.auth.login !== 'function') {
        TB.toast('The backend is not connected. Start the Python API first.', 'error');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;

      // Real login: Supabase Auth checks the password on the server.
      TB.auth.login(email.value.trim(), pass.value)
        .then(function (user) {
          TB.modal.closeAll();
          TB.toast('Welcome back, ' + (user && user.name ? user.name.split(' ')[0] : 'researcher') + '.');
        })
        .catch(function (error) {
          if (error.status === 401) {
            fieldError(pass, 'Incorrect email or password.');
          } else {
            TB.toast(error.message || 'Login failed. Please try again.', 'error');
          }
        })
        .then(function () {
          submitBtn.disabled = false;
        });
    });
    form.querySelector('[data-auth-link="forgot"]').addEventListener('click', function () {
      TB.toast('Password reset is handled by Supabase. Use the "Forgot password" email link, or ask your admin to reset it from the Supabase dashboard.', 'info');
    });
    form.querySelector('[data-auth-link="signup"]').addEventListener('click', function () {
      TB.modal.closeAll();
      setTimeout(openSignup, 260);
    });
  }

  function openSignup() {
    const uniOpts = ['<option value="">Select your university</option>']
      .concat(window.TB_DATA.universities.map(function (u) { return '<option>' + TB.esc(u) + '</option>'; }))
      .concat(['<option>Other</option>']).join('');
    const depOpts = ['<option value="">Select your department</option>']
      .concat(window.TB_DATA.departments.map(function (d) { return '<option>' + TB.esc(d) + '</option>'; }))
      .concat(['<option>Other</option>']).join('');
    const intOpts = ['<option value="">Select your research interest</option>']
      .concat(window.TB_DATA.categories.map(function (c) { return '<option>' + TB.esc(c.name) + '</option>'; })).join('');

    const m = TB.modal.open({
      title: '<i class="fa-solid fa-user-plus"></i> Create your profile',
      subtitle: 'Join ThesisBridge BD — it takes less than a minute.',
      body:
        '<form class="auth-form" id="signupForm" novalidate>' +
        '  <div class="field"><label for="su-name">Full Name</label><input id="su-name" name="name" type="text" autocomplete="name" placeholder="e.g. Nafis Ahmed"><p class="field-error"></p></div>' +
        '  <div class="field"><label for="su-email">Email</label><input id="su-email" name="email" type="email" autocomplete="email" placeholder="you@university.edu"><p class="field-error"></p></div>' +
        '  <div class="form-row">' +
        '    <div class="field"><label for="su-uni">University</label><select id="su-uni" name="university">' + uniOpts + '</select><p class="field-error"></p></div>' +
        '    <div class="field"><label for="su-dep">Department</label><select id="su-dep" name="department">' + depOpts + '</select><p class="field-error"></p></div>' +
        '  </div>' +
        '  <div class="form-row">' +
        '    <div class="field"><label for="su-sid">Student ID <span class="muted-sm">(optional)</span></label><input id="su-sid" name="sid" type="text" autocomplete="off" placeholder="e.g. CSE22 · ID 2"><p class="field-error"></p></div>' +
        '    <div class="field"><label for="su-int">Research Interest</label><select id="su-int" name="interest">' + intOpts + '</select><p class="field-error"></p></div>' +
        '  </div>' +
        '  <div class="form-row">' +
        '    <div class="field"><label for="su-pass">Password</label><input id="su-pass" name="password" type="password" autocomplete="new-password" placeholder="Min. 8 characters"><p class="field-error"></p></div>' +
        '    <div class="field"><label for="su-pass2">Confirm Password</label><input id="su-pass2" name="password2" type="password" autocomplete="new-password" placeholder="Repeat password"><p class="field-error"></p></div>' +
        '  </div>' +
        '  <button class="btn btn-primary btn-block" type="submit"><i class="fa-solid fa-rocket"></i> Create Account</button>' +
        '  <div class="auth-links"><span>Already have an account?</span><button type="button" data-auth-link="login">Login</button></div>' +
        '</form>' +
        '<p class="auth-note"><i class="fa-solid fa-circle-info"></i> Your profile is stored in Supabase, so it works on every device.</p>',
      size: 'md'
    });

    const form = m.overlay.querySelector('#signupForm');
    form.querySelector('[data-auth-link="login"]').addEventListener('click', function () {
      TB.modal.closeAll();
      setTimeout(openLogin, 260);
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // form.elements.<name> returns the input with that name attribute.
      // (We cannot write form.name because HTMLFormElement already has its
      // own `name` property, which is not the name input.)
      const nameInput = form.elements.name;
      const emailInput = form.elements.email;
      const universityInput = form.elements.university;
      const departmentInput = form.elements.department;
      const interestInput = form.elements.interest;
      const passwordInput = form.elements.password;
      const confirmInput = form.elements.password2;
      const studentIdInput = form.elements.sid;

      let ok = true;

      if (nameInput.value.trim().length < 3) { fieldError(nameInput, 'Please enter your full name (at least 3 characters).'); ok = false; } else fieldError(nameInput, '');
      if (!emailInput.value.trim()) { fieldError(emailInput, 'Please enter your email address.'); ok = false; }
      else if (!EMAIL_RE.test(emailInput.value.trim())) { fieldError(emailInput, 'Please enter a valid email address.'); ok = false; }
      else fieldError(emailInput, '');
      if (!universityInput.value) { fieldError(universityInput, 'Please select your university.'); ok = false; } else fieldError(universityInput, '');
      if (!departmentInput.value) { fieldError(departmentInput, 'Please select your department.'); ok = false; } else fieldError(departmentInput, '');
      if (!interestInput.value) { fieldError(interestInput, 'Please select a research interest.'); ok = false; } else fieldError(interestInput, '');
      if (passwordInput.value.length < 8) { fieldError(passwordInput, 'Password must be at least 8 characters.'); ok = false; } else fieldError(passwordInput, '');
      if (confirmInput.value !== passwordInput.value || !confirmInput.value) { fieldError(confirmInput, 'Passwords do not match.'); ok = false; } else fieldError(confirmInput, '');
      if (!ok) { TB.toast('Please fix the highlighted fields.', 'error'); return; }

      if (!TB.auth || typeof TB.auth.signup !== 'function') {
        TB.toast('The backend is not connected. Start the Python API first.', 'error');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;

      // These names match app/schemas.py -> SignupRequest (camelCase).
      TB.auth.signup({
        name: nameInput.value.trim(),
        email: emailInput.value.trim(),
        password: passwordInput.value,
        university: universityInput.value,
        department: departmentInput.value,
        studentId: studentIdInput.value.trim(),
        interest: interestInput.value
      })
        .then(function () {
          m.overlay.querySelector('.modal-body').innerHTML =
            '<div class="auth-success">' +
            '  <div class="auth-success-icon"><i class="fa-solid fa-check"></i></div>' +
            '  <h3>Profile created!</h3>' +
            '  <p>Your ThesisBridge BD account is ready. Your saved ideas and progress will now follow you to any device.</p>' +
            '</div>';
          const foot = m.overlay.querySelector('.modal-footer');
          if (foot) foot.remove();
          TB.toast('Profile created successfully.');
          setTimeout(function () { m.close(); }, 2200);
        })
        .catch(function (error) {
          if (error.status === 409) {
            fieldError(f.email, 'An account with this email already exists. Please log in.');
          } else {
            TB.toast(error.message || 'Could not create the account.', 'error');
          }
          submitBtn.disabled = false;
        });
    });
  }

  function openProfileMini() {
    const u = TB.state.get('tb_user', null);
    if (!u) return;
    const savedIdeas = (TB.state.get('tb_bookmarks', []) || []).length;
    const savedSups = (TB.state.get('tb_savedSupervisors', []) || []).length;
    TB.modal.open({
      title: '<i class="fa-solid fa-user-graduate"></i> ' + TB.esc(u.name),
      subtitle: 'Your profile, saved safely in Supabase.',
      body:
        '<ul class="meta-list">' +
        '  <li><span><i class="fa-solid fa-envelope"></i> Email</span><strong>' + TB.esc(u.email) + '</strong></li>' +
        (u.university ? '<li><span><i class="fa-solid fa-building-columns"></i> University</span><strong>' + TB.esc(u.university) + '</strong></li>' : '') +
        (u.department ? '<li><span><i class="fa-solid fa-sitemap"></i> Department</span><strong>' + TB.esc(u.department) + '</strong></li>' : '') +
        (u.studentId ? '<li><span><i class="fa-solid fa-id-card"></i> Student ID</span><strong>' + TB.esc(u.studentId) + '</strong></li>' : '') +
        (u.interest ? '<li><span><i class="fa-solid fa-flask"></i> Research interest</span><strong>' + TB.esc(u.interest) + '</strong></li>' : '') +
        '  <li><span><i class="fa-regular fa-bookmark"></i> Saved ideas</span><strong>' + savedIdeas + '</strong></li>' +
        '  <li><span><i class="fa-regular fa-bookmark"></i> Saved supervisors</span><strong>' + savedSups + '</strong></li>' +
        '</ul>',
      footer: '<button class="btn btn-outline" data-mini="logout"><i class="fa-solid fa-right-from-bracket"></i> Log out</button>',
      size: 'sm'
    }).overlay.querySelector('[data-mini="logout"]').addEventListener('click', function () {
      TB.modal.closeAll();

      // TB.auth.logout() removes the Supabase token and clears the local
      // copies of this user's saved lists (see js/api.js).
      if (TB.auth && typeof TB.auth.logout === 'function') {
        TB.auth.logout();
      } else {
        TB.state.set('tb_user', null);
      }

      TB.toast('You have been logged out.', 'info');
    });
  }

  function renderAuthUI() {
    const u = TB.state.get('tb_user', null);
    const wrap = document.getElementById('navAuth');
    const drawer = document.querySelector('.nav-drawer-auth');

    if (wrap) {
      if (u) {
        wrap.innerHTML =
          '<button class="user-chip" data-auth="profile" title="View your profile">' +
          '  <span class="user-avatar">' + TB.esc(TB.initials(u.name)) + '</span>' +
          '  <span class="user-name">Hi, ' + TB.esc(u.name.split(' ')[0]) + '</span>' +
          '</button>' +
          '<button class="icon-btn" data-auth="logout" aria-label="Log out"><i class="fa-solid fa-right-from-bracket"></i></button>';
      } else {
        wrap.innerHTML =
          '<button class="btn btn-ghost btn-sm" data-auth="login">Login</button>' +
          '<button class="btn btn-primary btn-sm" data-auth="signup">Get Started</button>';
      }
    }
    if (drawer) {
      drawer.innerHTML = u
        ? '<button class="btn btn-outline" data-auth="profile"><i class="fa-solid fa-user-graduate"></i> Hi, ' + TB.esc(u.name.split(' ')[0]) + '</button>' +
          '<button class="btn btn-primary" data-auth="logout"><i class="fa-solid fa-right-from-bracket"></i> Log out</button>'
        : '<button class="btn btn-outline" data-auth="login">Login</button>' +
          '<button class="btn btn-primary" data-auth="signup">Get Started</button>';
    }
  }

  /* ---------------------------- Saved ideas panel ------------------------ */

  function updateSavedBadge() {
    const badge = document.getElementById('savedCount');
    if (!badge) return;
    const n = (TB.state.get('tb_bookmarks', []) || []).length;
    badge.textContent = n;
    badge.classList.toggle('show', n > 0);
  }

  TB.toggleBookmark = function (id) {
    const ids = TB.state.get('tb_bookmarks', []) || [];
    const i = ids.indexOf(id);
    let saved;
    if (i > -1) { ids.splice(i, 1); saved = false; TB.toast('Research idea removed.', 'info'); }
    else { ids.push(id); saved = true; TB.toast('Research idea saved.'); }
    TB.state.set('tb_bookmarks', ids);
    return saved;
  };

  TB.openSavedIdeas = function () {
    const ids = TB.state.get('tb_bookmarks', []) || [];
    const ideas = (window.TB_DATA.researchIdeas || []).filter(function (r) { return ids.indexOf(r.id) > -1; });

    let body;
    if (ideas.length) {
      body =
        '<div class="saved-list">' +
        ideas.map(function (r) {
          return '<div class="saved-row">' +
            '  <div class="saved-info">' +
            '    <span class="saved-cat"><i class="fa-solid ' + TB.catIcon(r.category) + '"></i> ' + TB.esc(r.category) + '</span>' +
            '    <h4>' + TB.esc(r.title) + '</h4>' +
            '    <div class="saved-meta"><span class="badge ' + TB.diffClass(r.difficulty) + '">' + r.difficulty + '</span><span class="badge badge-soft">' + r.type + '</span></div>' +
            '  </div>' +
            '  <div class="saved-actions">' +
            '    <button class="btn btn-outline btn-sm" data-saved="view" data-id="' + r.id + '">View Details</button>' +
            '    <button class="icon-btn" data-saved="remove" data-id="' + r.id + '" aria-label="Remove ' + TB.esc(r.title) + ' from saved"><i class="fa-solid fa-trash-can"></i></button>' +
            '  </div>' +
            '</div>';
        }).join('') +
        '</div>';
    } else {
      body =
        '<div class="empty-state">' +
        '  <div class="empty-icon"><i class="fa-regular fa-bookmark"></i></div>' +
        '  <h3>No saved ideas yet.</h3>' +
        '  <p>You haven\u2019t saved any research ideas yet. Browse the explorer and tap the bookmark icon on any card.</p>' +
        '  <a class="btn btn-primary" href="research.html" data-saved="explore">Explore Research Ideas</a>' +
        '</div>';
    }

    const entry = TB.modal.open({
      title: '<i class="fa-solid fa-bookmark"></i> Saved Ideas',
      subtitle: ideas.length ? ideas.length + ' idea' + (ideas.length > 1 ? 's' : '') + ' saved' : '',
      body: body,
      size: 'md'
    });

    entry.overlay.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-saved]');
      if (!btn) return;
      if (btn.dataset.saved === 'remove') {
        TB.toggleBookmark(parseInt(btn.dataset.id, 10));
        entry.close();
        setTimeout(TB.openSavedIdeas, 240);
      } else if (btn.dataset.saved === 'view') {
        entry.close();
        setTimeout(function () { TB.openIdeaModal(parseInt(btn.dataset.id, 10)); }, 240);
      } else if (btn.dataset.saved === 'explore') {
        if (document.body.dataset.page === 'home' || document.body.dataset.page === 'research') {
          e.preventDefault();
          entry.close();
          const target = document.querySelector('#research-explorer');
          if (target) target.scrollIntoView({ behavior: TB.prefersReducedMotion() ? 'auto' : 'smooth' });
        }
      }
    });
  };

  /* --------------------------- Idea detail modal ------------------------- */

  TB.openIdeaModal = function (id) {
    const r = window.TB_DATA.researchIdeas.find(function (x) { return x.id === id; });
    if (!r) return;
    const saved = (TB.state.get('tb_bookmarks', []) || []).indexOf(r.id) > -1;

    const potential = (window.TB_DATA.supervisors || [])
      .filter(function (s) { return s.areas.indexOf(r.category) > -1; }).slice(0, 3);

    const block = function (icon, label, text) {
      return '<div class="detail-block"><span class="detail-icon"><i class="fa-solid ' + icon + '"></i></span>' +
        '<div><h4>' + label + '</h4><p>' + TB.esc(text) + '</p></div></div>';
    };
    const chips = function (arr, cls) {
      return '<div class="tag-row">' + arr.map(function (t) { return '<span class="' + (cls || 'tag') + '">' + TB.esc(t) + '</span>'; }).join('') + '</div>';
    };

    const entry = TB.modal.open({
      title: '<span class="badge ' + TB.diffClass(r.difficulty) + '" style="margin-right:8px">' + r.difficulty + '</span>' + TB.esc(r.title),
      subtitle: '<i class="fa-solid ' + TB.catIcon(r.category) + '"></i> ' + TB.esc(r.category) + ' · ' + TB.esc(r.area) + ' · ' + r.type,
      body:
        '<div class="detail-grid">' +
        block('fa-circle-exclamation', 'Research Problem', r.problem) +
        block('fa-puzzle-piece', 'Possible Research Gap', r.gap) +
        block('fa-list-check', 'Suggested Methodology', r.methodology) +
        block('fa-bullseye', 'Expected Outcome', r.outcome) +
        '</div>' +
        '<h4 class="detail-sub">At a glance</h4>' +
        '<ul class="meta-list">' +
        '  <li><span><i class="fa-solid fa-gauge-high"></i> Difficulty</span><strong>' + r.difficulty + '</strong></li>' +
        '  <li><span><i class="fa-solid fa-diagram-project"></i> Research type</span><strong>' + r.type + '</strong></li>' +
        '  <li><span><i class="fa-solid fa-building-columns"></i> University relevance</span><strong>' + r.universities.join(' · ') + '</strong></li>' +
        '</ul>' +
        '<h4 class="detail-sub">Required technologies</h4>' + chips(r.technologies, 'tag tag-tech') +
        '<h4 class="detail-sub">Suggested keywords</h4>' + chips(r.keywords) +
        (potential.length
          ? '<h4 class="detail-sub">Potential supervisors <span class="muted-sm">(suggested match)</span></h4><ul class="mini-list">' +
            potential.map(function (s) {
              return '<li><a href="supervisors.html">' + TB.esc(s.name) + '</a> — ' + TB.esc(s.title) + ', ' + TB.esc(s.university) + '</li>';
            }).join('') + '</ul>'
          : ''),
      footer:
        '<button class="btn btn-outline" data-idea-action="close">Close</button>' +
        '<button class="btn btn-primary" data-idea-action="save"><i class="fa-' + (saved ? 'solid' : 'regular') + ' fa-bookmark"></i> ' + (saved ? 'Saved — Remove' : 'Save Idea') + '</button>',
      size: 'lg'
    });

    const saveBtn = entry.overlay.querySelector('[data-idea-action="save"]');
    saveBtn.addEventListener('click', function () {
      const nowSaved = TB.toggleBookmark(r.id);
      saveBtn.innerHTML = '<i class="fa-' + (nowSaved ? 'solid' : 'regular') + ' fa-bookmark"></i> ' + (nowSaved ? 'Saved — Remove' : 'Save Idea');
    });
    entry.overlay.querySelector('[data-idea-action="close"]').addEventListener('click', entry.close);
  };

  /* --------------------------------- FAQ --------------------------------- */

  TB.renderFaq = function (container) {
    container.innerHTML =
      '<div class="faq-list">' +
      window.TB_DATA.faqs.map(function (f, i) {
        return '<div class="faq-item' + (i === 0 ? '' : '') + '">' +
          '  <button class="faq-q" aria-expanded="false" aria-controls="faq-a-' + i + '">' +
          '    <span>' + TB.esc(f.q) + '</span><i class="fa-solid fa-chevron-down" aria-hidden="true"></i>' +
          '  </button>' +
          '  <div class="faq-a" id="faq-a-' + i + '"><div class="faq-a-inner"><p>' + TB.esc(f.a) + '</p></div></div>' +
          '</div>';
      }).join('') +
      '</div>';

    container.addEventListener('click', function (e) {
      const q = e.target.closest('.faq-q');
      if (!q) return;
      const item = q.parentElement;
      const isOpen = item.classList.contains('open');
      container.querySelectorAll('.faq-item.open').forEach(function (el) {
        el.classList.remove('open');
        el.querySelector('.faq-q').setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        item.classList.add('open');
        q.setAttribute('aria-expanded', 'true');
      }
    });
  };

  /* ----------------------------- Stats counters -------------------------- */

  function initStats() {
    const nums = document.querySelectorAll('.stat-num[data-count]');
    if (!nums.length) return;
    const animate = function (el) {
      const target = parseInt(el.dataset.count, 10);
      const suffix = el.dataset.suffix || '';
      if (TB.prefersReducedMotion()) { el.textContent = target + suffix; return; }
      const dur = 1500, start = performance.now();
      const tick = function (now) {
        const p = Math.min((now - start) / dur, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * eased) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { animate(en.target); io.unobserve(en.target); }
      });
    }, { threshold: 0.4 });
    nums.forEach(function (n) { io.observe(n); });
  }

  /* ----------------------------- Scroll reveal --------------------------- */

  TB.observeReveals = function (container) {
    const root = container || document;
    const els = root.querySelectorAll('.reveal:not(.visible)');
    if (!els.length) return;
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('visible'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' });
    els.forEach(function (el) { io.observe(el); });
  };

  function initReveal() { TB.observeReveals(document); }

  /* --------------------------------- Boot -------------------------------- */

  function boot() {
    initTheme();
    initNav();
    renderAuthUI();
    initStats();
    initReveal();
    updateSavedBadge();

    document.addEventListener('tb:change', function (e) {
      if (e.detail.key === 'tb_bookmarks') updateSavedBadge();
      if (e.detail.key === 'tb_user') renderAuthUI();
    });

    // Global auth + saved-ideas actions (navbar, drawer, footer).
    document.addEventListener('click', function (e) {
      const authBtn = e.target.closest('[data-auth]');
      if (authBtn) {
        const act = authBtn.dataset.auth;
        if (act === 'login') openLogin();
        else if (act === 'signup') openSignup();
        else if (act === 'logout') {
          // Clear the Supabase token plus the local player's saved lists.
          if (TB.auth && typeof TB.auth.logout === 'function') {
            TB.auth.logout();
          } else {
            TB.state.set('tb_user', null);
          }
          TB.toast('You have been logged out.', 'info');
        }
        else if (act === 'profile') openProfileMini();
        closeDrawer();
      }
      const savedBtn = e.target.closest('[data-open-saved]');
      if (savedBtn) TB.openSavedIdeas();
    });

    document.querySelectorAll('[data-mount="faq"]').forEach(function (el) { TB.renderFaq(el); });

    const yr = document.querySelector('[data-year]');
    if (yr) yr.textContent = new Date().getFullYear();
  }

  /* ------------------------------------------------------------------
     START
     ------------------------------------------------------------------
     js/api.js runs after this file, so TB.ready only exists once the
     whole document has been parsed. We therefore start on
     DOMContentLoaded (or immediately if that already happened) and wait
     for TB.ready before the first render. TB.ready resolves after the
     database content and the logged-in user's saved lists have loaded.
     ------------------------------------------------------------------ */
  function start() {
    if (TB.ready && typeof TB.ready.then === 'function') {
      TB.ready.then(boot);
    } else {
      boot();
    }
  }

  if (document.readyState === 'complete') start();
  else document.addEventListener('DOMContentLoaded', start);

  TB.closeDrawer = closeDrawer;
})(window.TB);
