# ThesisBridge BD

**Your Bridge to Better Research.**

A fully interactive, responsive research hub for Bangladeshi undergraduate students — thesis idea discovery, supervisor matching, research methodology, and journal publication guidance. The interface is **HTML5, CSS3 and vanilla JavaScript** with no build step, and the content, accounts and saved data are served by a **Python (FastAPI) backend with a Supabase PostgreSQL database**.

> 🆕 **Backend:** see [`SETUP.md`](SETUP.md) for installation and Vercel deployment, and [`WORK_HISTORY.md`](WORK_HISTORY.md) for a step-by-step record of the backend work.

> 📑 This README is in **two languages**: [English](#-english) first, then [বাংলা](#-বাংলা).

**Prepared by:** Nasif Shahrear — CSE22 · ID 2

---

<!-- ======================== ENGLISH ======================== -->

# 🇬🇧 English

## 1. What is this project?

ThesisBridge BD solves a real student problem: finding a thesis idea, a supervisor and publication guidance requires searching many scattered places. This platform puts the **entire journey in one website**:

> find an idea → understand the research gap → match a supervisor → follow the roadmap → write the thesis → publish the paper.

It is a **full-stack application**: the pages are still plain HTML/CSS/JS, but the content is loaded from a Python API (`GET /api/content`), accounts are handled by Supabase Auth, and bookmarks, roadmap progress, checklist ticks and connection requests are stored in Supabase PostgreSQL. `js/data.js` stays in the project as an offline fallback, so the site still renders if the API is not running.

**Inside the prototype:** 20 research ideas · 12 supervisor profiles · 20 resources · 7 publication guides · 8 roadmap steps · 8 FAQs · 6 pages · 16 database tables · 26 API endpoints.

## 2. Technologies

| Tool | Used for |
| --- | --- |
| HTML5 | Structure of the 6 pages |
| CSS3 | Design system, layout (Grid/Flexbox), animations, dark mode via CSS variables |
| Vanilla JS (ES5/ES6) | Every interaction — search, filters, modals, quiz, state |
| Font Awesome | Icons |
| Google Fonts | Sora, Inter, JetBrains Mono (+ Hind Siliguri in docs) |
| Python 3.14 + FastAPI | Backend: REST API, validation, `/docs` |
| Supabase PostgreSQL | Database (content + user data) |
| Supabase Auth | Sign-up, login, bcrypt password hashing, access tokens |
| Vercel | Hosts the website and the Python function together |

No React/Vue/Bootstrap/jQuery — every feature is hand-written, so every line can be explained.

## 3. File structure

```
thesisbridge-bd/
├── app/                      → ★ Python backend (FastAPI)
│   ├── main.py               → creates the app, CORS, routers, /api/health
│   ├── config.py             → reads Supabase settings from .env
│   ├── database.py           → the two Supabase clients
│   ├── dependencies.py       → verifies the Bearer token
│   ├── schemas.py            → Pydantic models (request/response shapes)
│   └── routers/              → content · auth · user_state · requests
├── public/                   → ★ the website served at "/"
│   ├── index.html            → Home (hero, stats, explorer, matching, roadmap, FAQ)
│   ├── research.html         → Full-page Research Idea Explorer
│   ├── supervisors.html      → Supervisor directory + matching quiz
│   ├── publication.html      → Publication guides + journal checklist
│   ├── resources.html        → Resource library
│   ├── about.html            → Mission, how-it-works, FAQ
│   ├── docs.html             → ★ Bilingual project documentation (not linked in the site)
│   ├── css/
│   │   ├── style.css         → Design system: themes, components, modals, toasts
│   │   └── responsive.css    → Breakpoints (mobile → 1440px desktop)
│   ├── js/
│   │   ├── data.js           → offline fallback content
│   │   ├── api.js            → ★ NEW: connects pages to the Python API
│   │   ├── main.js           → Core: state, toasts, modal system, theme, navbar, auth
│   │   ├── network.js        → Hero "Research Network" (draggable SVG graph + physics)
│   │   ├── research.js       → Idea explorer logic
│   │   ├── supervisors.js    → Supervisor logic + matching quiz
│   │   ├── publication.js    → Roadmap, guides, checklist
│   │   └── resources.js      → Resource library logic
│   └── assets/icons/         → Logo + favicon (SVG)
├── sql/001_create_tables.sql → 16 tables + indexes + RLS policies
├── scripts/seed_supabase.py  → fills content tables from seed/content.json
├── seed/content.json         → exact sample content exported from js/data.js
├── requirements.txt          → Python packages
├── .env.example              → copy to .env, add your Supabase keys
├── vercel.json               → Vercel function setting
├── .python-version           → Python 3.14
├── SETUP.md                  → install + deploy guide
└── WORK_HISTORY.md           → backend work record
```

## 4. Features (what each one does + how)

### 4.1 Sticky navigation + mobile drawer
Sticky navbar with 6 working links; below 1080px the links move into a right-side drawer (hamburger button). Closes on link click, scrim click, or selection.

```css
/* Real bug fixed: backdrop-filter on .navbar made it the containing block
   for the fixed drawer → the drawer rendered as a sliver. Solution: blur
   lives on a ::before pseudo-element so children stay viewport-fixed. */
.navbar::before { content:''; position:absolute; inset:0; z-index:-1;
                  backdrop-filter: blur(14px); }
```

### 4.2 Hero + interactive "Research Network" (FIG. 01)
Headline with smooth-scroll CTAs, and an SVG figure: 8 draggable nodes (Idea, Gap, Method, Experiment, Supervisor, Thesis, Paper, Journal) connected by edges, with dots travelling along the lines. Nodes spring back with physics; tapping a node shows guidance (and the graph reflows above the panel so nothing is covered).

```js
// The entire "physics engine": force toward anchor + damping
n.vx = (n.vx + (anchor.x - n.x) * 0.016) * 0.90;
n.x += n.vx;
```

### 4.3 Animated statistics
"500+ Ideas / 100+ Topics / 50+ Areas / 1 Hub" count up from 0 — triggered by `IntersectionObserver` when the section becomes visible.

```js
const io = new IntersectionObserver(entries => {
  entries.forEach(en => { if (en.isIntersecting) animate(en.target); });
}, { threshold: 0.4 });
```

### 4.4 Research Idea Explorer (search + combined filters + sorting)
Live search across title/description/category/technology/tags, plus four filters (category, difficulty, type, technology) that combine with **AND** logic, plus 5-way sorting and empty states with "Clear Filters".

```js
let list = TB_DATA.researchIdeas.filter(function (r) {
  if (q && hay.indexOf(q) === -1)                             return false; // search
  if (state.cats.length && !state.cats.includes(r.category))  return false; // category
  if (state.diff !== 'All' && r.difficulty !== state.diff)    return false; // difficulty
  if (!r.technologies.some(t => state.techs.includes(t)))     return false; // technology
  return true; // passed everything → shown
});
```

### 4.5 Idea detail modal + bookmarks
Every card opens a full brief (problem, research gap, methodology, outcome, keywords, potential supervisors). Bookmarks are an array of IDs in localStorage with a live navbar badge and a "Saved Ideas" panel.

```js
TB.toggleBookmark = function (id) {
  const ids = TB.state.get('tb_bookmarks', []);
  const i = ids.indexOf(id);
  if (i > -1) { ids.splice(i, 1); TB.toast('Research idea removed.'); }
  else        { ids.push(id);    TB.toast('Research idea saved.');   }
  TB.state.set('tb_bookmarks', ids);   // read → modify → write
};
```

### 4.6 Supervisor directory + demo matching quiz
12 profiles filterable by university/department/area/expertise (all combinable), each with publications and suggested topics. The 4-step quiz (area → technologies → type → difficulty) scores every supervisor out of 100 with a visible "demo" disclaimer:

```js
function matchScore(sup, ans) {
  let score = 0;
  if (sup.areas.includes(ans.area)) score += 45;               // area: 45%
  const hits = ans.techs.filter(t => sup.expertise.includes(t)).length;
  score += (hits / ans.techs.length) * 25;                     // tools: 25%
  if (sup.supervisionTypes.includes(ans.type)) score += 15;    // type: 15%
  score += 10;                                                 // difficulty: 10%
  return Math.min(99, Math.round(score));                      // "94% Research Match"
}
```

### 4.7 Research roadmap
8 clickable steps, each with explanation, actions and resources. "Mark as Complete" fills nodes green, advances a gradient line and updates **"Research Journey: 37% Complete"** live.

```js
const pct = Math.round((done.length / steps.length) * 100);   // 3/8 → 38%
progressFill.style.width = pct + '%';
```

### 4.8 Publication Hub + journal checklist
7 guides (open as modals, marked "Read" after opening) and an 8-item interactive checklist with a live bar: **"5 / 8 Completed — 62%"**, auto-saved.

### 4.9 Resource library
20 resources in 9 categories with live search, category chips, detail modals, and real external links for tools/datasets (Zotero, Kaggle, Overleaf, Google Scholar).

### 4.10 FAQ accordion — CSS-only animation
Only one item opens at a time; the animation uses the `grid-template-rows: 0fr → 1fr` trick (no JS height math):

```css
.faq-a               { display: grid; grid-template-rows: 0fr; transition: .32s; }
.faq-item.open .faq-a{ grid-template-rows: 1fr; }
```

### 4.11 Login & sign-up with validation
Required fields, email regex, password length, matching passwords — with red per-field errors. The form then calls the API: Supabase Auth hashes and checks the password, and the navbar greets the user by name.

```js
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!EMAIL_RE.test(email.value.trim())) fieldError(email, 'Please enter a valid email address.');
if (password2.value !== password.value) fieldError(password2, 'Passwords do not match.');
```

### 4.12 Dark mode
All colors are CSS variables; dark mode swaps one attribute (`data-theme="dark"`). Choice is persisted, and a tiny head script prevents a theme flash on load.

```css
:root               { --bg: #f5f8f6; --text: #15221d; }
[data-theme='dark'] { --bg: #0c1512; --text: #e7f0ea; }
```

### 4.13 Toasts + one reusable modal system
All dialogs (idea details, supervisor profile, guides, resources, login, sign-up, saved panels) share one modal function: open animation, X, outside-click, Escape, stacked modals, focus return, scroll lock. Toasts auto-dismiss after ~3.4s.

## 5. The two "data doors" (now connected to the backend)

Every piece of content is read from `js/data.js` *or* from the API, and every
piece of user state flows through `TB.state` (`js/main.js`). UI modules never
touch storage directly. That design is why the backend could be added without
rewriting any UI: `js/api.js` simply replaces the data source and wraps
`TB.state.set` with a sync call.

```js
// The single state door: localStorage write + API sync (js/api.js)
TB.state.set = function (key, value) {
  var previous = baseGet(key, null);
  baseSet(key, value);                       // instant UI update
  if (suppressSync) return;                  // ignore data coming FROM the API
  if (key === 'tb_connectRequests') { syncConnectionRequests(previous, value); return; }
  if (!readToken()) return;                  // guest → localStorage only
  var endpoint = LIST_ENDPOINTS[key];        // e.g. /api/me/bookmarks/ideas
  request(endpoint.url, { method: 'PUT', body: body });  // save the whole list
};
```

Every feature module now starts with `TB.ready.then(boot)`, so the first render
already uses the data from PostgreSQL.

| Feature | File | Key function |
| --- | --- | --- |
| Idea search + filters + sort | `research.js` | `results()` |
| Matching quiz + score | `supervisors.js` | `matchScore()` |
| Roadmap + progress | `publication.js` | `renderRoadmap()` |
| Checklist | `publication.js` | `renderChecklist()` |
| Resource library | `resources.js` | `renderLibrary()` |
| Modals, toasts, theme, auth, state | `main.js` | `TB.modal`, `TB.toast`, `TB.state` |
| Network figure physics | `network.js` | `physics()` |

## 6. How to run

Two processes: the API and the static site. Full details (including the Supabase
project and the seeder) are in [`SETUP.md`](SETUP.md).

```powershell
# terminal 1 — Python API on http://127.0.0.1:8000
cd thesisbridge-bd
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# terminal 2 — website on http://127.0.0.1:8417
cd thesisbridge-bd
python -m http.server 8417 --directory public
```

Open <http://127.0.0.1:8417/index.html>. Interactive API documentation:
<http://127.0.0.1:8000/docs>. If the API is not running, the site still renders
from `js/data.js` (offline fallback) but login and saving are disabled.

## 7. Testing performed

**Frontend**
- All 6 pages opened and every interactive element exercised in a real browser.
- Responsive checks at 320 / 375 / 768 / 1024 / 1440 px — including programmatic verification that no page scrolls horizontally.
- **Real bugs found & fixed:** the mobile drawer clipping (CSS containing-block rule), the zero-width hero graph (grid item `margin:auto` collapse), the guidance panel covering nodes (fixed via measured `bottomInset` reflow), rAF suspension (hybrid watchdog loop).

**Backend**
- 57 automated API checks against the live Supabase project, all passing: content counts, sign-up, token-protected routes (401 without a token), all five saved lists, partial profile updates, connection requests (member and guest), login round trip, validation (422) and the database rows themselves.
- Full browser run on the real database: sign-up → bookmark → roadmap → checklist → delete the local copies → reload → data restored from PostgreSQL → logout → login → connection request.
- **Real bugs found & fixed:** a FAQ field-name mismatch (`question`/`answer` in PostgreSQL vs `q`/`a` in the browser), and database errors escaping as an unreadable 500 instead of a 503 with instructions.

## 8. Limitations & future plan

Access tokens last one hour (no refresh rotation) · connection requests are
stored but not emailed (no SMTP) · the matching score runs in the browser ·
no admin panel yet · Supabase's free plan pauses inactive projects.
**Next phase:** an admin dashboard for content and requests, email
notifications, and refresh-token handling.

---

<!-- ======================== বাংলা ======================== -->

# 🇧🇩 বাংলা

## ১. প্রজেক্টটি কী?

ThesisBridge BD একটা বাস্তব সমস্যার সমাধান: থিসিসের আইডিয়া, সুপারভাইজার আর পাবলিকেশনের নিয়ম খুঁজতে শিক্ষার্থীদের অনেক জায়গা ঘুরতে হয়। এই ওয়েবসাইটে পুরো যাত্রাটা এক জায়গায় আছে:

> আইডিয়া খোঁজা → রিসার্চ গ্যাপ বোঝা → সুপারভাইজার মেলানো → রোডম্যাপ অনুসরণ → থিসিস লেখা → পেপার পাবলিশ।

এটি একটি **সম্পূর্ণ ফুল-স্ট্যাক অ্যাপ্লিকেশন**: পেজগুলো আগের মতোই সাধারণ HTML/CSS/JS, কিন্তু কনটেন্ট আসে Python API (`GET /api/content`) থেকে, অ্যাকাউন্ট সামলায় Supabase Auth, আর বুকমার্ক, রোডম্যাপ প্রোগ্রেস, চেকলিস্ট ও কানেকশন রিকোয়েস্ট জমা থাকে Supabase PostgreSQL-এ। `js/data.js` ফলব্যাক হিসেবে থাকে, তাই API বন্ধ থাকলেও সাইট দেখা যায়।

**ভেতরে আছে:** ২০টি রিসার্চ আইডিয়া · ১২টি সুপারভাইজার প্রোফাইল · ২০টি রিসোর্স · ৭টি পাবলিকেশন গাইড · ৮ ধাপের রোডম্যাপ · ৮টি FAQ · ৬টি পেজ · ১৬টি ডেটাবেস টেবিল · ২৬টি API endpoint।

> 🆕 **ব্যাকএন্ড:** ইনস্টল ও Vercel ডিপ্লয়মেন্টের জন্য [`SETUP.md`](SETUP.md), আর ব্যাকএন্ডের কাজের ধাপে ধাপে রেকর্ড [`WORK_HISTORY.md`](WORK_HISTORY.md)।

## ২. ব্যবহৃত টেকনোলজি

| টুল | কাজ |
| --- | --- |
| HTML5 | ৬টি পেজের গঠন |
| CSS3 | ডিজাইন, লেআউট (Grid/Flexbox), অ্যানিমেশন, CSS variables দিয়ে ডার্ক মোড |
| Vanilla JS | সব ইন্টার‍্যাকশন — সার্চ, ফিল্টার, মডাল, কুইজ, স্টেট |
| Font Awesome | আইকন |
| Google Fonts | Sora, Inter, JetBrains Mono |
| Python 3.14 + FastAPI | ব্যাকএন্ড: REST API, ভ্যালিডেশন, `/docs` |
| Supabase PostgreSQL | ডেটাবেস (কনটেন্ট + ইউজার ডেটা) |
| Supabase Auth | সাইন-আপ, লগইন, bcrypt পাসওয়ার্ড হ্যাশিং, অ্যাক্সেস টোকেন |
| Vercel | ওয়েবসাইট ও Python ফাংশন একসাথে হোস্ট করে |

কোনো React/Vue/Bootstrap/jQuery নেই — সবকিছু হাতে লেখা, তাই প্রতিটি লাইনের ব্যাখ্যা দেওয়া যায়।

## ৩. ফাইল স্ট্রাকচার

```
thesisbridge-bd/
├── app/                      → ★ Python ব্যাকএন্ড (FastAPI)
│   ├── main.py               → অ্যাপ, CORS, রাউটার, /api/health
│   ├── config.py             → .env থেকে Supabase সেটিংস পড়ে
│   ├── database.py           → দুইটি Supabase client
│   ├── dependencies.py       → Bearer টোকেন যাচাই
│   ├── schemas.py            → Pydantic মডেল (request/response)
│   └── routers/              → content · auth · user_state · requests
├── public/                   → ★ "/" এ সার্ভ হওয়া ওয়েবসাইট
│   ├── index.html            → হোম
│   ├── research.html         → রিসার্চ আইডিয়া এক্সপ্লোরার
│   ├── supervisors.html      → সুপারভাইজার তালিকা + কুইজ
│   ├── publication.html      → পাবলিকেশন গাইড + চেকলিস্ট
│   ├── resources.html        → রিসোর্স লাইব্রেরি
│   ├── about.html            → পরিচিতি
│   ├── docs.html             → দ্বিভাষিক ডকুমেন্টেশন (সাইটে লিংক নেই)
│   ├── css/                  → style.css + responsive.css
│   ├── js/                   → data.js · api.js · main.js · network.js ·
│   │                            research.js · supervisors.js ·
│   │                            publication.js · resources.js
│   └── assets/icons/         → লোগো + ফেভিকন
├── sql/001_create_tables.sql → ১৬ টেবিল + index + RLS
├── scripts/seed_supabase.py  → content টেবিল ভরে
├── seed/content.json         → js/data.js থেকে নেওয়া ডেটা
├── requirements.txt          → Python প্যাকেজ
├── .env.example              → কপি করে .env বানান
├── vercel.json               → Vercel ফাংশন সেটিং
├── .python-version           → Python 3.14
├── SETUP.md                  → ইনস্টল + ডিপ্লয় গাইড
└── WORK_HISTORY.md           → ব্যাকএন্ড কাজের রেকর্ড
```

**মূল কথা:** আলাদা দায়িত্ব আলাদা ফাইলে — HTML-এ কাঠামো, CSS-এ ডিজাইন, `data.js`-এ ডেটা, প্রতিটি ফিচারের নিজস্ব JS ফাইল।

## ৪. ফিচারগুলোর ব্যাখ্যা (কী করে + কীভাবে করে)

### ৪.১ স্টিকি নেভিগেশন + মোবাইল ড্রয়ার
স্টিকি নেভবারে ৬টি কার্যকর লিংক; ১০৮০px-এর নিচে লিংকগুলো যায় ডান পাশের ড্রয়ারে (হ্যামবার্গার বাটন)। লিংকে ক্লিক, বাইরে ক্লিক বা নির্বাচন করলেই বন্ধ হয়।

```css
/* আসল বাগ ফিক্স: .navbar-এ backdrop-filter থাকায় সেটি fixed ড্রয়ারের
   containing block হয়ে যাচ্ছিল → ড্রয়ার চিকন অংশ হয়ে দেখাত। সমাধান:
   blur-কে ::before pseudo-element-এ সরানো হয়েছে। */
.navbar::before { content:''; position:absolute; inset:0; z-index:-1;
                  backdrop-filter: blur(14px); }
```

### ৪.২ হিরো + ইন্টার‍্যাক্টিভ "রিসার্চ নেটওয়ার্ক" (FIG. 01)
শিরোনাম ও smooth-scroll বাটন, পাশে SVG ফিগার: ৮টি টেনে-সরানো-যায় এমন নোড (Idea, Gap, Method, Experiment, Supervisor, Thesis, Paper, Journal) লাইনে যুক্ত, লাইন ধরে বিন্দু চলে। নোড ছাড়লে ফিজিক্সে ফিরে আসে; নোডে ট্যাপ করলে পরামর্শ দেখায় আর গ্রাফ উপরে উঠে যায় — কিছুই ঢাকা পড়ে না।

```js
// পুরো "ফিজিক্স ইঞ্জিন" দুই লাইনে: টান + বাধা
n.vx = (n.vx + (anchor.x - n.x) * 0.016) * 0.90;
n.x += n.vx;
```

### ৪.৩ অ্যানিমেটেড পরিসংখ্যান
"৫০০+ আইডিয়া / ১০০+ টপিক / ৫০+ এরিয়া / ১ হাব" — ০ থেকে গুনে ওঠে, শুরু হয় `IntersectionObserver` দিয়ে যখন সেকশন স্ক্রিনে আসে।

```js
const io = new IntersectionObserver(entries => {
  entries.forEach(en => { if (en.isIntersecting) animate(en.target); });
}, { threshold: 0.4 });
```

### ৪.৪ রিসার্চ আইডিয়া এক্সপ্লোরার (সার্চ + ফিল্টার + সর্টিং)
টাইপ করার সাথে সাথে লাইভ সার্চ (টাইটেল/বর্ণনা/ক্যাটাগরি/টেকনোলজি/ট্যাগ), চারটি ফিল্টার (ক্যাটাগরি, ডিফিকাল্টি, টাইপ, টেকনোলজি) **AND** লজিকে একসাথে চলে, ৫ রকম সর্টিং, আর কিছু না মিললে "Clear Filters" বাটনসহ empty state।

```js
let list = TB_DATA.researchIdeas.filter(function (r) {
  if (q && hay.indexOf(q) === -1)                             return false; // সার্চ
  if (state.cats.length && !state.cats.includes(r.category))  return false; // ক্যাটাগরি
  if (state.diff !== 'All' && r.difficulty !== state.diff)    return false; // ডিফিকাল্টি
  if (!r.technologies.some(t => state.techs.includes(t)))     return false; // টেকনোলজি
  return true; // সব শর্ত পাস → দেখানো হবে
});
```

### ৪.৫ আইডিয়ার বিস্তারিত মডাল + বুকমার্ক
প্রতিটি কার্ড থেকে পুরো ব্রিফ খোলে (সমস্যা, রিসার্চ গ্যাপ, পদ্ধতি, ফলাফল, কীওয়ার্ড, সম্ভাব্য সুপারভাইজার)। বুকমার্ক localStorage-এ ID-র array, নেভবারে লাইভ ব্যাজ আর "Saved Ideas" প্যানেল আছে।

```js
TB.toggleBookmark = function (id) {
  const ids = TB.state.get('tb_bookmarks', []);
  const i = ids.indexOf(id);
  if (i > -1) { ids.splice(i, 1); TB.toast('Research idea removed.'); }
  else        { ids.push(id);    TB.toast('Research idea saved.');   }
  TB.state.set('tb_bookmarks', ids);   // পড়া → বদলানো → লেখা
};
```

### ৪.৬ সুপারভাইজার ডিরেক্টরি + ডেমো ম্যাচিং কুইজ
১২টি প্রোফাইল বিশ্ববিদ্যালয়/বিভাগ/এরিয়া/এক্সপার্টিজে ফিল্টার হয় (একসাথেও), প্রতিটিতে পাবলিকেশন ও প্রস্তাবিত টপিক আছে। ৪-ধাপের কুইজ (এরিয়া → টেকনোলজি → টাইপ → ডিফিকাল্টি)-এর পর ১০০-এর মধ্যে স্কোর দেখায়, "ডেমো" — লেখাসহ:

```js
function matchScore(sup, ans) {
  let score = 0;
  if (sup.areas.includes(ans.area)) score += 45;               // এরিয়া: ৪৫%
  const hits = ans.techs.filter(t => sup.expertise.includes(t)).length;
  score += (hits / ans.techs.length) * 25;                     // টুলস: ২৫%
  if (sup.supervisionTypes.includes(ans.type)) score += 15;    // টাইপ: ১৫%
  score += 10;                                                 // ডিফিকাল্টি: ১০%
  return Math.min(99, Math.round(score));                      // "94% Research Match"
}
```

### ৪.৭ রিসার্চ রোডম্যাপ
৮টি ক্লিকযোগ্য ধাপ, প্রতিটিতে ব্যাখ্যা, করণীয় ও রিসোর্স। "Mark as Complete" দিলে নোড সবুজ হয়, গ্রেডিয়েন্ট লাইন এগোয়, আর লাইভ দেখায় **"Research Journey: 37% Complete"**।

```js
const pct = Math.round((done.length / steps.length) * 100);   // ৩/৮ → ৩৮%
progressFill.style.width = pct + '%';
```

### ৪.৮ পাবলিকেশন হাব + জার্নাল চেকলিস্ট
৭টি গাইড (মডালে খোলে, খোলার পর "Read" ব্যাজ) আর ৮-আইটেমের ইন্টার‍্যাক্টিভ চেকলিস্ট, লাইভ বারসহ: **"5 / 8 Completed — 62%"** — নিজে থেকেই সেভ হয়।

### ৪.৯ রিসোর্স লাইব্রেরি
৯টি ক্যাটাগরিতে ২০টি রিসোর্স — লাইভ সার্চ, ক্যাটাগরি চিপ, বিস্তারিত মডাল, আর টুল/ডেটাসেটগুলোর (Zotero, Kaggle, Overleaf, Google Scholar) আসল লিংক।

### ৪.১০ FAQ অ্যাকর্ডিয়ন — শুধু CSS অ্যানিমেশন
একবারে একটাই খোলে; অ্যানিমেশনে `grid-template-rows: 0fr → 1fr` কৌশল (JS দিয়ে উচ্চতার হিসাব লাগে না):

```css
.faq-a               { display: grid; grid-template-rows: 0fr; transition: .32s; }
.faq-item.open .faq-a{ grid-template-rows: 1fr; }
```

### ৪.১১ ভ্যালিডেশনসহ লগইন ও সাইন-আপ
ঘর পূরণ, ইমেইল ফরম্যাট (regex), পাসওয়ার্ডের দৈর্ঘ্য, ম্যাচিং পাসওয়ার্ড — ভুল হলে ঘরের নিচে লাল বার্তা। এরপর ফর্ম API-তে যায়: Supabase Auth পাসওয়ার্ড হ্যাশ করে যাচাই করে, আর নেভবারে নাম ধরে শুভেচ্ছা দেখায়।

```js
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!EMAIL_RE.test(email.value.trim())) fieldError(email, 'Please enter a valid email address.');
if (password2.value !== password.value) fieldError(password2, 'Passwords do not match.');
```

### ৪.১২ ডার্ক মোড
সব রঙ CSS variable; ডার্ক মোড মানে শুধু একটা attribute বদলানো (`data-theme="dark"`)। পছন্দ সেভ হয়, আর পেজ খোলার সময় থিমের ঝলক না দেখাতে ছোট একটা স্ক্রিপ্ট আগেই থিম ঠিক করে।

```css
:root               { --bg: #f5f8f6; --text: #15221d; }
[data-theme='dark'] { --bg: #0c1512; --text: #e7f0ea; }
```

### ৪.১৩ টোস্ট + একটিই পুনর্ব্যবহারযোগ্য মডাল সিস্টেম
সব ডায়ালগ (আইডিয়ার বিস্তারিত, সুপারভাইজার প্রোফাইল, গাইড, রিসোর্স, লগইন, সাইন-আপ, সেভড প্যানেল) একটি মডাল ফাংশন ভাগ করে: খোলার অ্যানিমেশন, X, বাইরে ক্লিক, Escape, স্ট্যাকড মডাল, ফোকাস ফেরত, স্ক্রল লক। টোস্ট ~৩.৪ সেকেন্ড পর নিজে মিলিয়ে যায়।

## ৫. ডেটার "দুইটি দরজা" (এখন ব্যাকএন্ডে যুক্ত)

সব কনটেন্ট আসে `js/data.js` *অথবা* API থেকে, আর সব ইউজার-স্টেট যায় `TB.state` (`js/main.js`) দিয়ে। UI মডিউল সরাসরি storage ধরে না। এই ডিজাইনের কারণেই UI নতুন করে না লিখে ব্যাকএন্ড যোগ করা গেছে: `js/api.js` শুধু ডেটার উৎস বদলায় আর `TB.state.set`-কে sync call দিয়ে মুড়ে দেয়।

```js
// ইউজার-ডেটার একমাত্র দরজা: localStorage লেখা + API sync (js/api.js)
TB.state.set = function (key, value) {
  var previous = baseGet(key, null);
  baseSet(key, value);                       // সাথে সাথে UI আপডেট
  if (suppressSync) return;                  // API থেকে আসা ডেটা ফেরত পাঠায় না
  if (key === 'tb_connectRequests') { syncConnectionRequests(previous, value); return; }
  if (!readToken()) return;                  // গেস্ট → শুধু localStorage
  var endpoint = LIST_ENDPOINTS[key];        // যেমন /api/me/bookmarks/ideas
  request(endpoint.url, { method: 'PUT', body: body });  // পুরো লিস্ট সেভ
};
```

| ফিচার | ফাইল | মূল ফাংশন |
| --- | --- | --- |
| আইডিয়া সার্চ + ফিল্টার + সর্ট | `research.js` | `results()` |
| ম্যাচিং কুইজ + স্কোর | `supervisors.js` | `matchScore()` |
| রোডম্যাপ + প্রোগ্রেস | `publication.js` | `renderRoadmap()` |
| চেকলিস্ট | `publication.js` | `renderChecklist()` |
| রিসোর্স লাইব্রেরি | `resources.js` | `renderLibrary()` |
| মডাল, টোস্ট, থিম, লগইন, স্টেট | `main.js` | `TB.modal`, `TB.toast`, `TB.state` |
| নেটওয়ার্ক ফিগারের ফিজিক্স | `network.js` | `physics()` |

## ৬. চালানোর নিয়ম

দুটি প্রসেস: API আর স্ট্যাটিক সাইট। Supabase প্রজেক্ট ও সিডারসহ বিস্তারিত [`SETUP.md`](SETUP.md)-এ।

```powershell
# টার্মিনাল ১ — Python API: http://127.0.0.1:8000
cd thesisbridge-bd
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# টার্মিনাল ২ — ওয়েবসাইট: http://127.0.0.1:8417
cd thesisbridge-bd
python -m http.server 8417 --directory public
```

ব্রাউজারে খুলুন <http://127.0.0.1:8417/index.html>। API ডকুমেন্টেশন: <http://127.0.0.1:8000/docs>। API বন্ধ থাকলেও সাইট `js/data.js` ফলব্যাক দিয়ে দেখা যাবে, তবে লগইন ও সেভ কাজ করবে না।

## ৭. যেসব টেস্ট করা হয়েছে

**ফ্রন্টএন্ড**
- আসল ব্রাউজারে ৬টি পেজ খুলে প্রতিটি ইন্টার‍্যাক্টিভ জিনিস চালিয়ে দেখা হয়েছে।
- ৩২০ / ৩৭৫ / ৭৬৮ / ১০২৪ / ১৪৪০ px-এ রেসপনসিভ যাচাই — প্রোগ্রাম দিয়ে মেপে প্রমাণ করা যে কোনো পেজেই পাশে স্ক্রল হয় না।
- **পাওয়া ও ঠিক করা আসল বাগ:** মোবাইল ড্রয়ার ক্লিপিং (CSS containing-block নিয়ম), শূন্য-প্রস্থ হিরো গ্রাফ (grid item-এর `margin:auto` সমস্যা), পরামর্শের প্যানেলে নোড ঢাকা পড়া (`bottomInset` দিয়ে সমাধান), rAF বন্ধ হয়ে যাওয়া (hybrid watchdog লুপ)।

**ব্যাকএন্ড**
- আসল Supabase প্রজেক্টের বিরুদ্ধে ৫৭টি স্বয়ংক্রিয় API টেস্ট — সবগুলো পাস: কনটেন্টের সংখ্যা, সাইন-আপ, টোকেন-প্রোটেক্টেড রুট (টোকেন ছাড়া ৪০১), পাঁচটি সেভ-লিস্ট, প্রোফাইলের আংশিক আপডেট, কানেকশন রিকোয়েস্ট (মেম্বার ও গেস্ট), লগইন রাউন্ড ট্রিপ, ভ্যালিডেশন (৪২২) এবং ডেটাবেসের আসল রো।
- আসল ডেটাবেস নিয়ে সম্পূর্ণ ব্রাউজার টেস্ট: সাইন-আপ → বুকমার্ক → রোডম্যাপ → চেকলিস্ট → লোকাল কপি মুছে দিয়ে রিলোড → PostgreSQL থেকে ডেটা ফিরে আসা → লগআউট → লগইন → কানেকশন রিকোয়েস্ট।
- **পাওয়া ও ঠিক করা আসল বাগ:** FAQ-এর ফিল্ড-নামের অমিল (PostgreSQL-এ `question`/`answer`, ব্রাউজারে `q`/`a`) এবং ডেটাবেসের এরর অ-readable ৫০০ হিসেবে বেরিয়ে যাওয়া — এখন ৫০৩ + করণীয় লেখা থাকে।

## ৮. সীমাবদ্ধতা ও ভবিষ্যৎ পরিকল্পনা

অ্যাক্সেস টোকেন ১ ঘণ্টা টেকে (রিফ্রেশ ফ্লো নেই) · কানেকশন রিকোয়েস্ট সেভ হয় কিন্তু ইমেইল যায় না (SMTP নেই) · ম্যাচিং স্কোর ব্রাউজারে চলে · এখনো অ্যাডমিন প্যানেল নেই · Supabase ফ্রি প্ল্যান নিষ্ক্রিয় প্রজেক্ট পজ করে।
**পরবর্তী ধাপ:** কনটেন্ট ও রিকোয়েস্টের জন্য অ্যাডমিন ড্যাশবোর্ড, ইমেইল নোটিফিকেশন, রিফ্রেশ-টোকেন হ্যান্ডলিং।

---

*ThesisBridge BD — Prepared by Nasif Shahrear (CSE22 · ID 2) · HTML + CSS + Vanilla JS*
