/* ==========================================================================
   ThesisBridge BD - API connection layer (js/api.js)
   --------------------------------------------------------------------------
   This file is the bridge between the existing HTML/CSS/JS interface and the
   new Python backend.

   What it does, in order:

     1. Finds the backend URL (localhost:8000 in development, same domain
        on Vercel).
     2. Loads the public content from GET /api/content and puts it into
        window.TB_DATA. If the backend is offline, it keeps the bundled
        js/data.js copy so the site still works.
     3. Replaces TB.state.get/set so that saved ideas, saved supervisors,
        roadmap progress, read guides and checklist ticks are stored in
        Supabase for logged-in users. Guests keep the old localStorage
        behaviour.
     4. Exposes TB.auth.login / signup / logout and TB.ready.

   Load order in every HTML page:
        js/data.js  ->  js/main.js  ->  js/api.js  ->  feature modules
   Feature modules wait for TB.ready before they render, so they always read
   the data that came from the database.
   ========================================================================== */

window.TB = window.TB || {};

(function (TB) {
  'use strict';

  /* ------------------------------------------------------------------
     1. WHERE IS THE BACKEND?
     ------------------------------------------------------------------ */

  var API_BASE = (function () {
    // A page may override the URL by setting window.TB_API_BASE before this
    // file loads (useful when the API is deployed somewhere else).
    if (typeof window.TB_API_BASE === 'string' && window.TB_API_BASE) {
      return window.TB_API_BASE.replace(/\/+$/, '');
    }

    // Opened directly from disk (file://) -> the local uvicorn server.
    if (window.location.protocol === 'file:') {
      return 'http://127.0.0.1:8000';
    }

    // Local development: HTML on port 8417, FastAPI on port 8000.
    if (window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000';
    }

    // Production (Vercel): the API is on the same domain, so a relative URL
    // is enough. "" + "/api/content" becomes "/api/content".
    return '';
  })();

  TB.API_BASE = API_BASE;

  /* ------------------------------------------------------------------
     2. SESSION TOKEN STORAGE
     ------------------------------------------------------------------
     Supabase returns an access token after login. We keep it in
     localStorage and send it as "Authorization: Bearer <token>".
     The token is NOT a password: it expires (one hour by default) and can
     be revoked by Supabase.
     ------------------------------------------------------------------ */

  var TOKEN_KEY = 'tb_token';

  function readToken() {
    try {
      return localStorage.getItem(TOKEN_KEY) || null;
    } catch (error) {
      return null;
    }
  }

  function writeToken(token) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch (error) {
      // Private browsing can block storage; the session then lasts one page.
    }
  }

  function clearToken() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (error) {
      // Nothing to do.
    }
  }

  /* ------------------------------------------------------------------
     3. SMALL ERROR CLASS + REQUEST HELPER
     ------------------------------------------------------------------ */

  function ApiError(message, status) {
    this.name = 'ApiError';
    this.message = message;
    this.status = status || 0;
  }

  ApiError.prototype = Object.create(Error.prototype);
  ApiError.prototype.constructor = ApiError;
  TB.ApiError = ApiError;

  /**
   * Turn FastAPI's error body into one readable sentence.
   *
   * FastAPI sends {"detail": "text"} for normal errors and
   * {"detail": [{"msg": "..."}]} for validation errors (HTTP 422).
   */
  function readableError(data) {
    if (!data) {
      return '';
    }

    var detail = data.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Object.prototype.toString.call(detail) === '[object Array]' && detail.length) {
      var first = detail[0];
      if (first && first.msg) {
        return first.msg;
      }
    }

    return '';
  }

  /**
   * One function for every HTTP call.
   *
   * @param {string} path    e.g. "/api/content"
   * @param {object} options { method, body, auth }
   * @returns {Promise}      resolves with the parsed JSON
   */
  function request(path, options) {
    options = options || {};

    var headers = { Accept: 'application/json' };

    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }

    // auth !== false means "attach the token when we have one".
    var token = readToken();
    if (options.auth !== false && token) {
      headers.Authorization = 'Bearer ' + token;
    }

    var settings = {
      method: options.method || 'GET',
      headers: headers
    };

    if (options.body !== undefined) {
      settings.body = JSON.stringify(options.body);
    }

    return fetch(API_BASE + path, settings).then(
      function (response) {
        var contentType = response.headers.get('content-type') || '';
        var isJson = contentType.indexOf('application/json') > -1;

        var bodyPromise = isJson
          ? response.json()
          : response.text().then(function (text) {
              return { detail: text };
            });

        return bodyPromise
          .catch(function () {
            return {};
          })
          .then(function (data) {
            if (!response.ok) {
              throw new ApiError(
                readableError(data) || 'Request failed with status ' + response.status,
                response.status
              );
            }
            return data;
          });
      },
      function () {
        // The second function handles a network failure (server not running).
        throw new ApiError(
          'Cannot reach the backend at ' + (API_BASE || window.location.origin) +
            '. Is the Python server running?',
          0
        );
      }
    );
  }

  TB.apiRequest = request;

  /* ------------------------------------------------------------------
     4. PUBLIC CONTENT
     ------------------------------------------------------------------
     GET /api/content returns the same object shape as the old js/data.js.
     Replacing window.TB_DATA means no rendering code had to change.
     ------------------------------------------------------------------ */

  function loadContent() {
    return request('/api/content', { auth: false })
      .then(function (content) {
        window.TB_DATA = content;
        return content;
      })
      .catch(function (error) {
        // Offline fallback: js/data.js already filled window.TB_DATA.
        console.warn(
          '[ThesisBridge] Using the bundled data.js because the API is unavailable:',
          error.message
        );
        return window.TB_DATA;
      });
  }

  /* ------------------------------------------------------------------
     5. SYNCING USER STATE TO SUPABASE
     ------------------------------------------------------------------
     The rest of the frontend calls TB.state.set('tb_bookmarks', [...]) etc.
     We keep that API, write to localStorage first (instant UI), then send
     the whole list to the backend in the background.
     ------------------------------------------------------------------ */

  var suppressSync = false; // true while we load data FROM the server

  var baseGet = TB.state.get.bind(TB.state);
  var baseSet = TB.state.set.bind(TB.state);

  // localStorage key -> API endpoint + JSON field name
  var LIST_ENDPOINTS = {
    tb_bookmarks: { url: '/api/me/bookmarks/ideas', field: 'ideaIds' },
    tb_savedSupervisors: { url: '/api/me/bookmarks/supervisors', field: 'supervisorIds' },
    tb_roadmap: { url: '/api/me/roadmap', field: 'stepIds' },
    tb_readGuides: { url: '/api/me/read-guides', field: 'guideIds' },
    tb_checklist: { url: '/api/me/checklist', field: 'itemIds' }
  };

  /**
   * Send a connection request / withdraw it.
   *
   * The frontend stores requests as an array in tb_connectRequests.
   * We compare the old and the new array and send only the difference:
   *   - supervisor id present now but not before -> POST
   *   - supervisor id present before but not now -> DELETE
   */
  function syncConnectionRequests(previous, next) {
    var before = {};
    var after = {};

    (previous || []).forEach(function (item) {
      before[item.supId] = true;
    });

    (next || []).forEach(function (item) {
      after[item.supId] = true;
    });

    (next || []).forEach(function (item) {
      if (before[item.supId]) {
        return; // already on the server
      }

      request('/api/connection-requests', {
        method: 'POST',
        body: {
          supervisorId: item.supId,
          name: item.name,
          email: item.email,
          topic: item.topic,
          message: item.message
        }
      }).catch(function (error) {
        console.warn('[ThesisBridge] Connection request was not saved:', error.message);
      });
    });

    Object.keys(before).forEach(function (supervisorId) {
      if (after[supervisorId]) {
        return; // still requested
      }

      if (!readToken()) {
        return; // guest: the request only existed in localStorage
      }

      request('/api/me/connection-requests/' + supervisorId, {
        method: 'DELETE'
      }).catch(function (error) {
        console.warn('[ThesisBridge] Could not withdraw the request:', error.message);
      });
    });
  }

  // Replace the localStorage-only writer with a localStorage + API writer.
  TB.state.set = function (key, value) {
    var previous = baseGet(key, null);

    // 1. Always update the local copy first so the UI reacts immediately.
    baseSet(key, value);

    // 2. Do not echo server data back to the server while hydrating.
    if (suppressSync) {
      return;
    }

    // 3. Connection requests are public, so they sync even for guests.
    if (key === 'tb_connectRequests') {
      syncConnectionRequests(previous || [], value || []);
      return;
    }

    // 4. Everything else needs a logged-in user.
    if (!readToken()) {
      return;
    }

    var endpoint = LIST_ENDPOINTS[key];

    if (!endpoint) {
      return;
    }

    var body = {};
    body[endpoint.field] = value || [];

    request(endpoint.url, { method: 'PUT', body: body }).catch(function (error) {
      console.warn('[ThesisBridge] Could not save ' + key + ':', error.message);
    });
  };

  /* ------------------------------------------------------------------
     6. LOADING THE USER'S STATE AFTER LOGIN / PAGE REFRESH
     ------------------------------------------------------------------ */

  function hydrate() {
    return request('/api/me/state').then(function (state) {
      suppressSync = true;

      try {
        // tb_user drives the navbar ("Hi, name") and the profile modal.
        TB.state.set('tb_user', state.user);

        TB.state.set('tb_bookmarks', state.bookmarkIdeaIds || []);
        TB.state.set('tb_savedSupervisors', state.savedSupervisorIds || []);
        TB.state.set('tb_roadmap', state.roadmapStepIds || []);
        TB.state.set('tb_readGuides', state.readGuideIds || []);
        TB.state.set('tb_checklist', state.checklistItemIds || []);

        // Convert the API shape { supervisorId, date } into the shape the
        // supervisors.js module already understands: { supId, date }.
        TB.state.set(
          'tb_connectRequests',
          (state.connectionRequests || []).map(function (item) {
            return {
              supId: item.supervisorId,
              name: item.name,
              email: item.email,
              topic: item.topic,
              message: item.message,
              date: item.date
            };
          })
        );
      } finally {
        // Always switch syncing back on, even if one line above throws.
        suppressSync = false;
      }

      return state.user;
    });
  }

  /* ------------------------------------------------------------------
     7. AUTHENTICATION HELPERS USED BY main.js
     ------------------------------------------------------------------ */

  TB.auth = {
    isLoggedIn: function () {
      return !!readToken();
    },

    /**
     * Log in, store the token, then download the user's saved lists.
     * Returns a Promise with the user object.
     */
    login: function (email, password) {
      return request('/api/auth/login', {
        method: 'POST',
        auth: false,
        body: { email: email, password: password }
      }).then(function (data) {
        writeToken(data.accessToken);
        TB.state.set('tb_user', data.user); // update the navbar immediately

        return hydrate()
          .catch(function () {
            return data.user; // the login worked; the lists can wait
          });
      });
    },

    /**
     * Create an account. The payload already uses the API's camelCase names:
     * { name, email, password, university, department, studentId, interest }
     */
    signup: function (payload) {
      return request('/api/auth/signup', {
        method: 'POST',
        auth: false,
        body: payload
      }).then(function (data) {
        writeToken(data.accessToken);
        TB.state.set('tb_user', data.user);

        return hydrate()
          .catch(function () {
            return data.user;
          });
      });
    },

    /**
     * Log out: forget the token and empty the local lists so the next visitor
     * on this computer cannot read the previous user's saved ideas.
     */
    logout: function () {
      clearToken();
      suppressSync = true;

      try {
        TB.state.set('tb_user', null);
        TB.state.set('tb_bookmarks', []);
        TB.state.set('tb_savedSupervisors', []);
        TB.state.set('tb_roadmap', []);
        TB.state.set('tb_readGuides', []);
        TB.state.set('tb_checklist', []);
        TB.state.set('tb_connectRequests', []);
      } finally {
        suppressSync = false;
      }
    }
  };

  /* ------------------------------------------------------------------
     8. TB.ready - the promise every module waits for
     ------------------------------------------------------------------
     Feature modules call:  TB.ready.then(boot)
     That guarantees the database content is already in window.TB_DATA and a
     returning user's bookmarks are already loaded, so nothing "jumps" after
     the first paint.
     ------------------------------------------------------------------ */

  TB.ready = loadContent().then(function () {
    if (!readToken()) {
      return null; // guest: nothing else to load
    }

    return hydrate().catch(function (error) {
      // A stale token must not break the page; behave like a guest instead.
      if (error.status === 401) {
        clearToken();
        TB.state.set('tb_user', null);
      }
      return null;
    });
  });

  // Expose the internals for debugging in the browser console.
  TB.api = {
    request: request,
    loadContent: loadContent,
    hydrate: hydrate
  };
})(window.TB);
