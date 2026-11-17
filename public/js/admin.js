/* ==========================================================================
   ThesisBridge BD — Administrator dashboard (js/admin.js)
   --------------------------------------------------------------------------
   This file is deliberately standalone. It does not use main.js, api.js or
   any feature module, so the public site and the dashboard cannot break each
   other.

   What it does:

     1. Finds the API (exactly like api.js: localhost -> :8000, Vercel ->
        same origin).
     2. Reuses the SAME session token as the public site (localStorage
        key "tb_token"), so logging in on the site also unlocks this page.
     3. Asks GET /api/auth/me who the token belongs to. Only a user with
        isAdmin === true gets the dashboard.
     4. Loads the three admin endpoints and renders three tables.

   IMPORTANT: the browser check below is only cosmetic. If a student edits
   localStorage or calls the API with curl, the server answers 403 because
   every /api/admin route depends on require_admin(). Hiding the page is not
   security; refusing the request is.
   ========================================================================== */

(function () {
  'use strict';

  /* ------------------------------------------------------------------
     1. WHERE IS THE BACKEND?
     ------------------------------------------------------------------ */

  var API_BASE = (function () {
    if (typeof window.TB_API_BASE === 'string' && window.TB_API_BASE) {
      return window.TB_API_BASE.replace(/\/+$/, '');
    }
    if (window.location.protocol === 'file:') {
      return 'http://127.0.0.1:8000';
    }
    if (window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000';
    }
    return ''; // production: same domain as the page
  })();

  var TOKEN_KEY = 'tb_token';

  /* ------------------------------------------------------------------
     2. TINY HELPERS
     ------------------------------------------------------------------ */

  function $(id) {
    return document.getElementById(id);
  }

  function readToken() {
    try { return localStorage.getItem(TOKEN_KEY) || null; } catch (e) { return null; }
  }

  function writeToken(token) {
    try { localStorage.setItem(TOKEN_KEY, token); } catch (e) { /* private mode */ }
  }

  function clearToken() {
    try { localStorage.removeItem(TOKEN_KEY); } catch (e) { /* ignore */ }
  }

  /**
   * Escape text before putting it in innerHTML.
   *
   * Student names, topics and messages are typed by users. Without this, a
   * topic containing <img onerror=...> would run script inside the admin
   * session — the classic stored-XSS hole. Every user-supplied value below
   * passes through here.
   */
  function esc(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** "2026-11-16T19:00:42.25+00:00" -> "16 Nov 2026" */
  function shortDate(iso) {
    if (!iso) { return '—'; }
    var d = new Date(iso);
    if (isNaN(d.getTime())) { return '—'; }
    return d.toLocaleDateString(undefined, {
      day: '2-digit', month: 'short', year: 'numeric'
    });
  }

  /**
   * One fetch wrapper for every admin call.
   * Attaches the Bearer token and turns any error body into a sentence.
   * A 401 or 403 means "this session cannot use the dashboard", which the
   * caller handles by showing the login gate again.
   */
  function api(path, options) {
    options = options || {};

    var headers = { Accept: 'application/json' };
    if (options.body !== undefined) { headers['Content-Type'] = 'application/json'; }

    var token = readToken();
    if (token) { headers.Authorization = 'Bearer ' + token; }

    return fetch(API_BASE + path, {
      method: options.method || 'GET',
      headers: headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        if (!response.ok) {
          var detail = data && data.detail;
          if (Array.isArray(detail)) {           // FastAPI 422 shape
            detail = detail.map(function (item) { return item.msg; }).join('; ');
          }
          var error = new Error(detail || ('Request failed (' + response.status + ')'));
          error.status = response.status;
          throw error;
        }
        return data;
      });
    });
  }

  /* ------------------------------------------------------------------
     3. SCREEN SWITCHING
     ------------------------------------------------------------------ */

  function showGate(message, kind) {
    $('gate').hidden = false;
    $('dash').hidden = true;
    $('logout').hidden = true;
    $('who').textContent = '';

    var box = $('gate-msg');
    if (message) {
      box.className = 'gate-msg ' + (kind || 'notice');
      box.textContent = message;
    } else {
      box.className = 'gate-msg';
      box.textContent = '';
    }
  }

  function showDashboard(user) {
    $('gate').hidden = true;
    $('dash').hidden = false;
    $('logout').hidden = false;
    $('who').textContent = user.name + ' · ' + user.email;
    loadAll();
  }

  /* ------------------------------------------------------------------
     4. RENDERING
     ------------------------------------------------------------------ */

  function renderStats(overview) {
    var cards = [
      ['Students', overview.totalStudents, 'registered accounts'],
      ['Requests', overview.totalRequests, overview.pendingRequests + ' pending'],
      ['Accepted', overview.acceptedRequests, 'supervisor contacted'],
      ['Bookmarks', overview.totalBookmarks, 'idea saves in total']
    ];

    $('stats').innerHTML = cards.map(function (card) {
      return '<div class="stat">' +
               '<div class="k">' + esc(card[0]) + '</div>' +
               '<div class="v">' + esc(card[1]) + '</div>' +
               '<div class="s">' + esc(card[2]) + '</div>' +
             '</div>';
    }).join('');

    var ideas = overview.topIdeas || [];
    $('top-ideas').innerHTML = ideas.length
      ? ideas.map(function (idea, index) {
          return '<tr>' +
                   '<td class="num">' + (index + 1) + '</td>' +
                   '<td>' + esc(idea.title) + '</td>' +
                   '<td class="num">' + esc(idea.bookmarks) + '</td>' +
                 '</tr>';
        }).join('')
      : '<tr><td colspan="3" class="empty">No bookmarks yet.</td></tr>';
  }

  function renderStudents(students) {
    $('students-count').textContent = students.length + ' account' +
      (students.length === 1 ? '' : 's');

    $('students').innerHTML = students.length
      ? students.map(function (student) {
          var details = [student.university, student.department]
            .filter(Boolean).join(' · ');

          return '<tr>' +
                   '<td><div class="who-name">' + esc(student.name) + '</div>' +
                     '<div class="who-mail">' + esc(student.email) + '</div></td>' +
                   '<td>' + (details ? esc(details) : '<span class="muted">—</span>') + '</td>' +
                   '<td class="mono">' + esc(shortDate(student.joinedAt)) + '</td>' +
                   '<td class="num">' + esc(student.bookmarks) + '</td>' +
                   '<td class="num">' + esc(student.savedSupervisors) + '</td>' +
                   '<td class="num">' + esc(student.roadmapSteps) + '</td>' +
                   '<td class="num">' + esc(student.readGuides) + '</td>' +
                   '<td class="num">' + esc(student.checklistItems) + '</td>' +
                   '<td class="num">' + esc(student.requests) + '</td>' +
                 '</tr>';
        }).join('')
      : '<tr><td colspan="9" class="empty">No students have registered yet.</td></tr>';
  }

  function renderRequests(requests) {
    $('requests').innerHTML = requests.length
      ? requests.map(function (item) {
          var guest = item.userId ? '' :
            ' <span class="muted" title="Sent without an account">(guest)</span>';

          var actions =
            '<button class="btn-mini ok" data-id="' + esc(item.id) +
              '" data-status="accepted"' +
              (item.status === 'accepted' ? ' disabled' : '') + '>Accept</button>' +
            '<button class="btn-mini no" data-id="' + esc(item.id) +
              '" data-status="declined"' +
              (item.status === 'declined' ? ' disabled' : '') + '>Decline</button>';

          return '<tr>' +
                   '<td><div class="who-name">' + esc(item.name) + guest + '</div>' +
                     '<div class="who-mail">' + esc(item.email) + '</div></td>' +
                   '<td>' + esc(item.supervisorName || ('#' + item.supervisorId)) + '</td>' +
                   '<td class="topic"><strong>' + esc(item.topic) + '</strong>' +
                     '<span>' + esc(item.message) + '</span></td>' +
                   '<td><span class="badge ' + esc(item.status) + '">' +
                     esc(item.status) + '</span>' +
                     '<div class="muted" style="font-size:11px;margin-top:4px">' +
                     esc(shortDate(item.date)) + '</div></td>' +
                   '<td><div class="actions">' + actions + '</div></td>' +
                 '</tr>';
        }).join('')
      : '<tr><td colspan="5" class="empty">No requests in this view.</td></tr>';
  }

  /* ------------------------------------------------------------------
     5. DATA LOADING
     ------------------------------------------------------------------ */

  var currentFilter = '';

  function loadOverview() {
    return api('/api/admin/overview').then(renderStats);
  }

  function loadStudents() {
    return api('/api/admin/students').then(renderStudents);
  }

  function loadRequests() {
    var path = '/api/admin/connection-requests' +
      (currentFilter ? '?status=' + encodeURIComponent(currentFilter) : '');
    return api(path).then(renderRequests);
  }

  /**
   * All three endpoints at once. Promise.all keeps the page fast: the three
   * requests travel in parallel instead of one after another.
   */
  function loadAll() {
    return Promise.all([loadOverview(), loadStudents(), loadRequests()])
      .catch(function (error) {
        if (error.status === 401 || error.status === 403) {
          clearToken();
          showGate(error.message, 'error');
          return;
        }
        // A readable error (503 because sql/002_admin.sql has not been run, or
        // the Python server is not running locally) goes next to the tables.
        $('stats').innerHTML =
          '<div class="stat"><div class="k">Could not load</div>' +
          '<div class="s" style="margin-top:8px">' + esc(error.message) + '</div></div>';
      });
  }

  /* ------------------------------------------------------------------
     6. CHANGE ONE REQUEST'S STATUS
     ------------------------------------------------------------------ */

  function setStatus(id, status, button) {
    button.disabled = true;

    api('/api/admin/connection-requests/' + encodeURIComponent(id) + '/status', {
      method: 'PUT',
      body: { status: status }
    }).then(function () {
      // Redraw from the server instead of patching the DOM by hand: the
      // active filter decides whether the row should still be visible.
      return Promise.all([loadRequests(), loadOverview()]);
    }).catch(function (error) {
      button.disabled = false;
      window.alert(error.message);
    });
  }

  /* ------------------------------------------------------------------
     7. BOOT
     ------------------------------------------------------------------ */

  function boot() {
    var token = readToken();

    if (!token) {
      showGate('Sign in with the administrator account.', 'notice');
      return;
    }

    // The token exists, but it may belong to a normal student.
    api('/api/auth/me').then(function (user) {
      if (user.isAdmin) {
        showDashboard(user);
      } else {
        clearToken();
        showGate('This account is not an administrator.', 'error');
      }
    }).catch(function (error) {
      if (error.status === 401) {
        clearToken();
        showGate('Your session expired. Please sign in again.', 'notice');
      } else {
        showGate(error.message, 'error');
      }
    });
  }

  /* ---------------------------- events ---------------------------- */

  $('gate-form').addEventListener('submit', function (event) {
    event.preventDefault();

    var email = $('email').value.trim();
    var password = $('password').value;
    var button = $('gate-submit');
    var box = $('gate-msg');

    box.className = 'gate-msg';
    box.textContent = '';

    if (!email || !password) {
      box.className = 'gate-msg error';
      box.textContent = 'Enter both the email and the password.';
      return;
    }

    button.disabled = true;
    button.textContent = 'Signing in…';

    api('/api/auth/login', {
      method: 'POST',
      body: { email: email, password: password }
    }).then(function (data) {
      writeToken(data.accessToken);

      if (!data.user.isAdmin) {
        // Do not keep a student session on the admin page: the next request
        // would only earn a 403.
        clearToken();
        throw new Error('This account is not an administrator.');
      }

      $('password').value = '';
      showDashboard(data.user);
    }).catch(function (error) {
      box.className = 'gate-msg error';
      box.textContent = error.message;
    }).then(function () {
      button.disabled = false;
      button.textContent = 'Sign in';
    });
  });

  $('logout').addEventListener('click', function () {
    clearToken();
    window.location.reload();
  });

  $('request-filters').addEventListener('click', function (event) {
    var chip = event.target.closest('.chip');
    if (!chip) { return; }

    currentFilter = chip.getAttribute('data-status') || '';

    Array.prototype.forEach.call(
      $('request-filters').querySelectorAll('.chip'),
      function (item) { item.classList.toggle('active', item === chip); }
    );

    loadRequests().catch(function (error) {
      window.alert(error.message);
    });
  });

  $('requests').addEventListener('click', function (event) {
    var button = event.target.closest('button[data-id]');
    if (!button) { return; }
    setStatus(button.getAttribute('data-id'), button.getAttribute('data-status'), button);
  });

  boot();
})();
