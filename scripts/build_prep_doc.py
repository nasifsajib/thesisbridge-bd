#!/usr/bin/env python3
"""
scripts/build_prep_doc.py
-------------------------
Builds `iit-preparation.html` - one self-contained study document that explains
the whole database + backend build: the steps, the design, every file's code with
its explanation, the API, the flows, the bugs we fixed and the deployment.

Why a generator instead of hand-written HTML?
    The code blocks are read from the REAL project files at build time, so the
    document can never drift from the code. Re-run it after any change:

        .\\.venv\\Scripts\\python.exe scripts\\build_prep_doc.py

Output: iit-preparation.html in the project root (outside public/, so it is not
served by the website and never deployed). The file works offline: no fonts, no
CDNs, no external CSS or JavaScript.
"""

import datetime
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "iit-preparation.html"

BILINGUAL = True


# =============================================================================
# Helpers used while building the page
# =============================================================================


def bi(en: str, bn: str) -> str:
    """Inline pair: English and Bangla side by side (CSS decides what shows)."""
    return (
        f'<span class="en">{en}</span>'
        f'<span class="bn" lang="bn">{bn}</span>'
    )


def para(en: str, bn: str) -> str:
    """Two paragraphs; the language switch shows one of them."""
    return (
        f'<p class="en">{en}</p>'
        f'<p class="bn" lang="bn">{bn}</p>'
    )


def bullets(items) -> str:
    """items = list of (english, bangla) tuples."""
    out = []
    for en, bn in items:
        out.append(
            '<li><span class="en">%s</span>'
            '<span class="bn" lang="bn">%s</span></li>' % (en, bn)
        )
    return "<ul>" + "".join(out) + "</ul>"


def steps_list(items) -> str:
    """items = list of (english, bangla) tuples, rendered as an ordered list."""
    out = []
    for en, bn in items:
        out.append(
            '<li><span class="en">%s</span>'
            '<span class="bn" lang="bn">%s</span></li>' % (en, bn)
        )
    return "<ol>" + "".join(out) + "</ol>"


def _cell(value) -> str:
    if isinstance(value, tuple):
        en, bn = value
        return (
            f'<span class="en">{en}</span>'
            f'<span class="bn" lang="bn">{bn}</span>'
        )
    return str(value)


def table(headers, rows, cls: str = "") -> str:
    """
    headers = list of (english, bangla)
    rows    = list of lists; a cell may be a string or an (english, bangla) tuple
    """
    head = "".join(f"<th>{_cell(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{_cell(c)}</td>" for c in row) + "</tr>"
    return (
        f'<div class="tablewrap"><table class="{cls}">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def note(en: str, bn: str, kind: str = "info") -> str:
    """A coloured callout box. kind = info | warn | good."""
    icon = {"info": "i", "warn": "!", "good": "✓"}.get(kind, "i")
    return (
        f'<div class="note {kind}"><span class="note-icon">{icon}</span>'
        f'<div><span class="en">{en}</span>'
        f'<span class="bn" lang="bn">{bn}</span></div></div>'
    )


def cmd(text: str) -> str:
    """A shell command (no translation needed)."""
    return f'<pre class="cmd"><code>{html.escape(text)}</code></pre>'


def h3(en: str, bn: str, anchor: str = "") -> str:
    a = f' id="{anchor}"' if anchor else ""
    return f"<h3{a}>{bi(en, bn)}</h3>"


def code(path: str, cap_en: str, cap_bn: str, collapsed=None, lang: str = "") -> str:
    """
    Embed a real project file inside a collapsible block.

    `collapsed`: True = start closed, False = start open, None = decide by size.
    """
    full = ROOT / path
    if not full.exists():
        return note(
            f"File not found: <code>{path}</code>",
            f"ফাইল পাওয়া যায়নি: <code>{path}</code>",
            "warn",
        )

    text = full.read_text(encoding="utf-8").replace("\r\n", "\n")
    lines = len(text.splitlines())

    if collapsed is None:
        open_now = lines <= 90
    else:
        open_now = not collapsed

    open_attr = " open" if open_now else ""
    lang_attr = f' data-lang-type="{lang}"' if lang else ""

    return (
        f'<details class="code"{open_attr}{lang_attr}>'
        f"<summary>{bi(cap_en, cap_bn)}"
        f'<span class="filemeta">{path} · {lines} lines</span></summary>'
        f'<div class="codewrap"><button class="copy" type="button">Copy</button>'
        f"<pre><code>{html.escape(text)}</code></pre></div>"
        f"</details>"
    )


def step(num: int, en: str, bn: str, body: str) -> str:
    return (
        f'<section class="step"><div class="stephead">'
        f'<span class="stepnum">{num}</span>'
        f"<h3>{bi(en, bn)}</h3></div>{body}</section>"
    )


def qa(items) -> str:
    """items = list of (question_en, question_bn, answer_en, answer_bn)."""
    out = []
    for q_en, q_bn, a_en, a_bn in items:
        out.append(
            '<div class="qa-item"><div class="qa-q">'
            f'<span class="en">{q_en}</span>'
            f'<span class="bn" lang="bn">{q_bn}</span></div>'
            '<div class="qa-a">'
            f'<span class="en">{a_en}</span>'
            f'<span class="bn" lang="bn">{a_bn}</span></div></div>'
        )
    return '<div class="qa">' + "".join(out) + "</div>"


# =============================================================================
# Stylesheet (plain string - no f-string, because CSS contains braces)
# =============================================================================

CSS = """
:root{
  --ink:#14231d; --muted:#5b6f66; --line:#dbe6e0; --paper:#f4f7f5; --card:#ffffff;
  --green:#0b6e4f; --green-2:#0e8a63; --green-soft:#e4f2ec; --amber:#8a6200;
  --red:#a4231f; --code-bg:#0f231b; --code-ink:#e8f3ed; --radius:14px;
  --mono: ui-monospace, "Cascadia Code", Consolas, "Courier New", monospace;
  --sans: system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --bnfont: "Hind Siliguri", "Nirmala UI", "Noto Sans Bengali", var(--sans);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 var(--sans)}

/* ---------- language switching ---------- */
.bn{font-family:var(--bnfont);line-height:1.85}
body[data-lang="en"] .bn{display:none !important}
body[data-lang="bn"] .en{display:none !important}
body[data-lang="both"] p.bn,body[data-lang="both"] div.bn{margin-top:.35rem;color:#3d554b}
body[data-lang="both"] li .bn{display:block;color:#3d554b;font-size:.96em}

/* ---------- top bar ---------- */
.topbar{position:sticky;top:0;z-index:50;background:rgba(11,110,79,.97);
  color:#fff;padding:10px 20px;display:flex;gap:16px;align-items:center;
  flex-wrap:wrap;box-shadow:0 2px 14px rgba(0,0,0,.14)}
.brand{font-weight:700;font-size:15px;letter-spacing:.2px}
.brand small{display:block;font-weight:400;font-size:11.5px;opacity:.85}
.langswitch{margin-left:auto;display:flex;background:rgba(255,255,255,.14);
  border-radius:999px;padding:3px;gap:2px}
.langswitch button{background:transparent;border:0;color:#fff;font:600 13px/1 var(--sans);
  padding:8px 14px;border-radius:999px;cursor:pointer;font-family:var(--sans)}
.langswitch button[aria-pressed="true"]{background:#fff;color:var(--green)}
.langswitch button:focus-visible{outline:2px solid #ffe08a;outline-offset:2px}

/* ---------- layout ---------- */
.shell{display:grid;grid-template-columns:250px minmax(0,1fr);gap:34px;
  max-width:1250px;margin:0 auto;padding:26px 22px 80px}
.toc{position:sticky;top:70px;align-self:start;max-height:calc(100vh - 90px);
  overflow:auto;font-size:13.5px;border-right:1px solid var(--line);padding-right:14px}
.toc h2{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
  margin:0 0 10px}
.toc ol{list-style:none;margin:0;padding:0}
.toc a{display:block;padding:6px 9px;border-radius:8px;color:#33473d;text-decoration:none;
  border-left:3px solid transparent}
.toc a:hover{background:var(--green-soft);color:var(--green)}
.toc a.active{background:var(--green-soft);color:var(--green);border-left-color:var(--green);
  font-weight:600}
main{min-width:0}

/* ---------- headings ---------- */
h1{font-size:30px;line-height:1.25;margin:0 0 8px;letter-spacing:-.4px}
h2{font-size:22px;margin:52px 0 6px;padding-top:14px;border-top:1px solid var(--line);
  scroll-margin-top:76px}
h2 .secnum{display:inline-block;background:var(--green);color:#fff;border-radius:8px;
  font:700 13px/1 var(--sans);padding:6px 9px;margin-right:9px;vertical-align:2px}
h3{font-size:17px;margin:26px 0 6px}
h4{font-size:15px;margin:18px 0 4px}
p{margin:.55rem 0}
ul,ol{margin:.5rem 0 .9rem;padding-left:1.35rem}
li{margin:.28rem 0}
code{font-family:var(--mono);font-size:.88em;background:#e8efeb;color:#134a37;
  padding:1px 5px;border-radius:5px;word-break:break-word}
a{color:var(--green)}
.lead{font-size:17px;color:#2d423a}

/* ---------- cards / notes ---------- */
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px 20px;margin:14px 0}
.note{display:flex;gap:11px;align-items:flex-start;background:#fff;border:1px solid var(--line);
  border-left:4px solid var(--green);border-radius:10px;padding:12px 14px;margin:14px 0}
.note.warn{border-left-color:#c98a00;background:#fffdf4}
.note.good{border-left-color:#0b6e4f;background:#f4fbf7}
.note-icon{flex:0 0 22px;height:22px;border-radius:50%;background:var(--green);color:#fff;
  font:700 13px/22px var(--sans);text-align:center}
.note.warn .note-icon{background:#c98a00}
.note div{min-width:0}

/* ---------- tables ---------- */
.tablewrap{overflow-x:auto;margin:14px 0;border:1px solid var(--line);border-radius:12px;
  background:#fff}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);
  vertical-align:top}
th{background:#eef5f1;font-size:12.5px;letter-spacing:.03em;text-transform:uppercase;
  color:#3d554b}
tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fafcfb}

/* ---------- code ---------- */
details.code{background:var(--card);border:1px solid var(--line);border-radius:12px;
  margin:14px 0;overflow:hidden}
details.code>summary{cursor:pointer;padding:12px 14px;font-size:14px;font-weight:600;
  display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;list-style:none}
details.code>summary::-webkit-details-marker{display:none}
details.code>summary::before{content:"▸";color:var(--green);font-size:12px}
details.code[open]>summary::before{content:"▾"}
details.code>summary:hover{background:#f6faf8}
.filemeta{margin-left:auto;font:400 11.5px var(--mono);color:var(--muted)}
.codewrap{position:relative;background:var(--code-bg);max-height:34rem;overflow:auto}
.codewrap pre{margin:0;padding:16px 18px;color:var(--code-ink);
  font:13px/1.6 var(--mono);tab-size:4;white-space:pre}
.codewrap code{background:none;color:inherit;padding:0;font:inherit}
.copy{position:sticky;top:8px;float:right;margin:8px 8px 0 0;background:rgba(255,255,255,.12);
  color:#dff0e8;border:1px solid rgba(255,255,255,.28);border-radius:7px;
  font:600 11px/1 var(--sans);padding:6px 9px;cursor:pointer;z-index:2}
.copy:hover{background:rgba(255,255,255,.24)}
pre.cmd{background:var(--code-bg);color:var(--code-ink);border-radius:10px;
  padding:13px 16px;overflow-x:auto;font:13px/1.6 var(--mono);margin:10px 0}
pre.cmd code{background:none;color:inherit;padding:0}
pre.diagram{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;
  overflow-x:auto;font:12.5px/1.5 var(--mono);color:#274036;margin:16px 0}

/* ---------- steps ---------- */
.step{background:#fff;border:1px solid var(--line);border-radius:var(--radius);
  padding:6px 20px 14px;margin:16px 0}
.stephead{display:flex;gap:13px;align-items:center;margin:12px 0 2px}
.stepnum{flex:0 0 30px;height:30px;border-radius:9px;background:var(--green-soft);
  color:var(--green);font:700 14px/30px var(--sans);text-align:center}
.stephead h3{margin:0}

/* ---------- qa ---------- */
.qa{display:grid;gap:10px;margin:14px 0}
.qa-item{background:#fff;border:1px solid var(--line);border-radius:12px;padding:13px 16px}
.qa-q{font-weight:700;color:#12452f;margin-bottom:5px}
.qa-a{color:#33473d}

/* ---------- misc ---------- */
.badges{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 4px}
.badge{background:var(--green-soft);color:var(--green);border-radius:999px;
  font:700 12px/1 var(--sans);padding:7px 11px}
footer{max-width:1250px;margin:0 auto;padding:28px 22px 60px;color:var(--muted);
  font-size:13px;border-top:1px solid var(--line)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}

@media (max-width:900px){
  .shell{grid-template-columns:1fr;padding-top:16px}
  .toc{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line);
    padding:0 0 12px}
  .toc ol{display:flex;flex-wrap:wrap;gap:4px}
  .toc a{border-left:0;padding:5px 8px;background:#eef5f1}
  h1{font-size:25px}
}
@media print{
  .topbar,.toc,.copy{display:none !important}
  .shell{display:block;max-width:none;padding:0}
  .codewrap{max-height:none;overflow:visible}
  details.code{page-break-inside:avoid}
  body[data-lang="both"] .bn{color:#000}
}
"""


# =============================================================================
# Behaviour (plain string - no braces conflicts)
# =============================================================================

JS = """
(function () {
  var KEY = 'tb_prep_lang';
  var body = document.body;
  var buttons = Array.prototype.slice.call(document.querySelectorAll('[data-set-lang]'));

  function apply(lang) {
    body.setAttribute('data-lang', lang);
    document.documentElement.lang = (lang === 'bn') ? 'bn' : 'en';
    buttons.forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-set-lang') === lang));
    });
    try { localStorage.setItem(KEY, lang); } catch (e) { /* file:// may block */ }
  }

  buttons.forEach(function (b) {
    b.addEventListener('click', function () { apply(b.getAttribute('data-set-lang')); });
  });

  var saved = 'both';
  try { saved = localStorage.getItem(KEY) || 'both'; } catch (e) { saved = 'both'; }
  apply(saved);

  // Copy-to-clipboard for every code block.
  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.copy') : null;
    if (!btn) return;
    var box = btn.closest('details');
    var node = box ? box.querySelector('code') : null;
    if (!node) return;
    var label = btn.textContent;
    function done(text) {
      btn.textContent = text;
      setTimeout(function () { btn.textContent = label; }, 1500);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(node.textContent)
        .then(function () { done('Copied'); })
        .catch(function () { done('Select & Ctrl+C'); });
    } else {
      done('Select & Ctrl+C');
    }
  });

  // Highlight the section you are reading.
  // A heading is a thin box, so watching headings with IntersectionObserver
  // would almost never report one as visible. Instead: on scroll, find the
  // last heading whose top has passed 20% of the viewport height.
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var heads = Array.prototype.slice.call(document.querySelectorAll('h2[id]'));

  function updateSpy() {
    if (!heads.length) return;
    var line = window.innerHeight * 0.2;
    var current = heads[0];
    heads.forEach(function (h) {
      if (h.getBoundingClientRect().top <= line) current = h;
    });
    var id = '#' + current.id;
    links.forEach(function (a) {
      var on = a.getAttribute('href') === id;
      a.classList.toggle('active', on);
      if (on) { a.setAttribute('aria-current', 'true'); }
      else { a.removeAttribute('aria-current'); }
    });
  }

  // Only 15 headings are measured, so running this on every scroll event is
  // cheap. Scroll events are already coalesced by the browser, and avoiding
  // requestAnimationFrame keeps it working in background or occluded tabs.
  window.addEventListener('scroll', updateSpy, { passive: true });
  window.addEventListener('hashchange', updateSpy);
  updateSpy();

  // Printing: open every code block, then put it back.
  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('details').forEach(function (d) {
      d.dataset.wasopen = d.open ? '1' : '0';
      d.open = true;
    });
  });
  window.addEventListener('afterprint', function () {
    document.querySelectorAll('details').forEach(function (d) {
      d.open = d.dataset.wasopen === '1';
    });
  });
})();
"""


# =============================================================================
# Page assembly
# =============================================================================


def sections():
    """Every section, in reading order: (id, number, english, bangla, html)."""
    return [
        ("overview", "1", "What we built", "কী বানিয়েছি", s_overview()),
        ("architecture", "2", "Architecture", "আর্কিটেকচার", s_architecture()),
        ("steps", "3", "The build, step by step", "ধাপে ধাপে নির্মাণ", s_steps()),
        ("database", "4", "Database design (16 tables)", "ডেটাবেস ডিজাইন (১৬ টেবিল)", s_database()),
        ("backend", "5", "Backend files, one by one", "ব্যাকএন্ড ফাইল, এক এক করে", s_backend()),
        ("api", "6", "API reference (26 endpoints)", "API তালিকা (২৬টি endpoint)", s_api()),
        ("auth", "7", "Sign-up, login and tokens", "সাইন-আপ, লগইন ও টোকেন", s_auth()),
        ("sync", "8", "Saved data: browser ↔ database", "সেভ করা ডেটা: ব্রাউজার ↔ ডেটাবেস", s_sync()),
        ("verification", "9", "What we verified", "যা যাচাই করা হয়েছে", s_verification()),
        ("bugs", "10", "Bugs found and fixed", "যে বাগগুলো ধরা পড়েছে", s_bugs()),
        ("deploy", "11", "Deploy to Vercel", "Vercel-এ ডিপ্লয়", s_deploy()),
        ("troubleshoot", "12", "Troubleshooting", "সমস্যা ও সমাধান", s_troubleshoot()),
        ("viva", "13", "Viva questions", "ভাইভা প্রশ্ন", s_viva()),
        ("glossary", "14", "Glossary", "শব্দকোষ", s_glossary()),
        ("next", "15", "Limitations and next steps", "সীমাবদ্ধতা ও পরবর্তী কাজ", s_next()),
    ]


def build() -> None:
    secs = sections()

    toc = "".join(
        f'<li><a href="#{sid}">{bi(en, bn)}</a></li>'
        for sid, num, en, bn, _ in secs
    )

    body = "".join(
        f'<h2 id="{sid}"><span class="secnum">{num}</span>{bi(en, bn)}</h2>{content}'
        for sid, num, en, bn, content in secs
    )

    today = datetime.date.today().strftime("%d %B %Y")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ThesisBridge BD — Database &amp; Backend Build Guide</title>
<meta name="description" content="Step-by-step record of building the ThesisBridge BD database and Python backend, with full code and bilingual explanations.">
<style>{CSS}</style>
</head>
<body data-lang="both">

<header class="topbar">
  <div class="brand">ThesisBridge BD — Database &amp; Backend Build Guide
    <small>Python · FastAPI · Supabase PostgreSQL · Vercel · built {today}</small>
  </div>
  <div class="langswitch" role="group" aria-label="Language / ভাষা">
    <button type="button" data-set-lang="en">EN</button>
    <button type="button" data-set-lang="bn">বাংলা</button>
    <button type="button" data-set-lang="both" aria-pressed="true">Both</button>
  </div>
</header>

<div class="shell">
  <nav class="toc" aria-label="Contents">
    <h2>Contents / সূচি</h2>
    <ol>{toc}</ol>
  </nav>

  <main>
    <h1>{bi("How the backend was built", "ব্যাকএন্ড যেভাবে বানানো হলো")}</h1>
    {para(
        "This file is the complete record of the database and backend work: what we did, in what order, "
        "what the code looks like, and why each decision was made. It is written so that you can explain "
        "every part to an examiner without opening another file.",
        "এই ফাইলটিতে ডেটাবেস ও ব্যাকএন্ডের সম্পূর্ণ কাজের রেকর্ড আছে: কী করেছি, কোন ক্রমে করেছি, কোড দেখতে কেমন, "
        "আর প্রতিটি সিদ্ধান্ত কেন নিয়েছি। পরীক্ষকের সামনে অন্য কোনো ফাইল না খুলেও প্রতিটি অংশ ব্যাখ্যা করা যাবে।"
    )}
    {note(
        "Use the <b>EN / বাংলা / Both</b> buttons at the top right. Your choice is remembered next time you "
        "open this file. Code is shown once (in Python/SQL/JavaScript) because code is the same in any language — "
        "the explanation around it switches language.",
        "উপরের ডান দিকের <b>EN / বাংলা / Both</b> বোতাম দিয়ে ভাষা বদলান। আপনার পছন্দ মনে থাকবে। কোড একবারই দেখানো হয়েছে "
        "(Python/SQL/JavaScript) কারণ কোড সব ভাষায় একই থাকে — এর আশপাশের ব্যাখ্যাই ভাষা বদলায়।"
    )}
    {note(
        "This document deliberately contains <b>no API keys</b>. The Supabase URL and keys live only in "
        "<code>.env</code> (never committed) and in Vercel's environment variables.",
        "এই ডকুমেন্টে ইচ্ছাকৃতভাবে <b>কোনো API key নেই</b>। Supabase URL ও কী শুধু <code>.env</code> ফাইলে "
        "(কখনো Git-এ যায় না) এবং Vercel-এর environment variables-এ থাকে।",
        "warn"
    )}

    {body}
  </main>
</div>

<footer>
  {bi(
     "Generated from the live project files by <code>scripts/build_prep_doc.py</code>. Re-run that script after changing the backend so this page stays accurate.",
     "জীবন্ত প্রজেক্ট ফাইল থেকে <code>scripts/build_prep_doc.py</code> দিয়ে তৈরি। ব্যাকএন্ড বদলালে আবার স্ক্রিপ্টটি চালালে এই পেজ হালনাগাদ থাকবে।"
  )}
</footer>

<script>{JS}</script>
</body>
</html>
"""

    OUT.write_text(page, encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT}")
    print(f"  {len(secs)} sections · {size_kb:.0f} KB")


# =============================================================================
# Extra helpers used only by the sections below
# =============================================================================


def pre(text: str, cls: str = "diagram") -> str:
    """A plain preformatted block: ASCII diagrams and file trees."""
    return f'<pre class="{cls}"><code>{html.escape(text.strip())}</code></pre>'


def snippet(text: str, cap_en: str = "", cap_bn: str = "") -> str:
    """A dark code panel for a short excerpt, with an optional bilingual caption."""
    head = f"<p><strong>{bi(cap_en, cap_bn)}</strong></p>" if cap_en else ""
    return (
        head
        + '<div class="card" style="padding:0;overflow:hidden">'
        + '<div class="codewrap" style="max-height:24rem;border-radius:12px">'
        + "<pre><code>"
        + html.escape(text.strip())
        + "</code></pre></div></div>"
    )


# =============================================================================
# 1. OVERVIEW
# =============================================================================


def s_overview() -> str:
    return (
        para(
            "ThesisBridge BD began as six static HTML pages. Every research idea, "
            "supervisor and FAQ lived inside <code>public/js/data.js</code>, and anything "
            "the visitor saved (bookmarks, roadmap ticks, checklist ticks) went into the "
            "browser's <code>localStorage</code>. That had three consequences: the data "
            "was invisible to a teacher reading the source, it disappeared when the "
            "browser storage was cleared, and two students could not share anything.",
            "ThesisBridge BD শুরু হয়েছিল ছয়টি স্ট্যাটিক HTML পেজ দিয়ে। প্রতিটি গবেষণা "
            "আইডিয়া, সুপারভাইজার ও FAQ থাকত <code>public/js/data.js</code>-এর ভিতরে, আর "
            "ইউজার যা সেভ করত (বুকমার্ক, রোডম্যাপ টিক, চেকলিস্ট টিক) তা যেত ব্রাউজারের "
            "<code>localStorage</code>-এ। এতে তিনটি সমস্যা ছিল: ডেটা সোর্স পড়ে দেখা যেত না, "
            "ব্রাউজার স্টোরেজ মুছলে সব হারিয়ে যেত, আর দুইজন শিক্ষার্থী একে অন্যের কিছু "
            "দেখতে পারত না।",
        )
        + '<div class="badges">'
        + "".join(
            f'<span class="badge">{b}</span>'
            for b in [
                "Python 3.14",
                "FastAPI",
                "Supabase Auth",
                "PostgreSQL",
                "Vercel",
                "26 endpoints",
                "16 tables",
            ]
        )
        + "</div>"
        + h3("Before and after", "আগে ও এখন")
        + table(
            [("Area", "বিষয়"), ("Before (static site)", "আগে (স্ট্যাটিক সাইট)"), ("Now", "এখন")],
            [
                (
                    ("Content", "কনটেন্ট"),
                    ("Hard-coded in js/data.js", "js/data.js-এ হার্ডকোড করা"),
                    ("150 rows in PostgreSQL, served by one API call", "PostgreSQL-এ ১৫০টি রো, একটি API কলে আসে"),
                ),
                (
                    ("Accounts", "অ্যাকাউন্ট"),
                    ("Fake: only a name in localStorage", "ভুয়া: localStorage-এ শুধু একটি নাম"),
                    ("Real Supabase Auth users with hashed passwords", "আসল Supabase Auth ইউজার, পাসওয়ার্ড হ্যাশ করা"),
                ),
                (
                    ("Saved data", "সেভ করা ডেটা"),
                    ("This browser only", "শুধু এই ব্রাউজারে"),
                    ("PostgreSQL, restored on any device after login", "PostgreSQL-এ, লগইন করলে যেকোনো ডিভাইসে ফিরে আসে"),
                ),
                (
                    ("Connection requests", "কানেকশন রিকোয়েস্ট"),
                    ("Stored locally, never left the laptop", "লোকালে থাকত, ল্যাপটপ ছেড়ে যেত না"),
                    ("Rows in connection_requests, with user_id and status", "connection_requests-এ রো, user_id ও status সহ"),
                ),
                (
                    ("Testability", "পরীক্ষণযোগ্যতা"),
                    ("Click around and hope", "ক্লিক করে দেখতে হতো"),
                    ("57 automated checks + /docs interactive page", "৫৭টি স্বয়ংক্রিয় চেক + /docs ইন্টার‍্যাকটিভ পেজ"),
                ),
            ],
        )
        + h3("The numbers behind this document", "এই ডকুমেন্টের সংখ্যা")
        + table(
            [("Item", "বিষয়"), ("Count", "সংখ্যা"), ("Where it comes from", "কোথা থেকে")],
            [
                ("Database tables", "ডেটাবেস টেবিল", "16", "sql/001_create_tables.sql"),
                ("Seeded content rows", "সিড করা কনটেন্ট রো", "150", "scripts/seed_supabase.py"),
                ("API endpoints", "API endpoint", "26", "/docs (OpenAPI)"),
                ("Backend Python files", "ব্যাকএন্ড Python ফাইল", "11", "app/ + scripts/"),
                ("Automated API checks", "স্বয়ংক্রিয় API চেক", "57", "all passed, 0 failed"),
                ("Real bugs fixed", "আসল বাগ", "3", "section 10"),
                ("Website pages kept working", "সচল রাখা পেজ", "6", "public/*.html"),
            ],
        )
        + h3("What you can demonstrate to an examiner", "পরীক্ষককে যা দেখাতে পারবেন")
        + bullets(
            [
                (
                    "Open <code>/docs</code> and click <i>Try it out</i> on any endpoint — FastAPI documents the API automatically from the Python code.",
                    "<code>/docs</code> খুলে যেকোনো endpoint-এ <i>Try it out</i> চাপুন — FastAPI নিজেই Python কোড থেকে API ডকুমেন্টেশন বানায়।",
                ),
                (
                    "Sign up in the browser, then reload the Supabase Table Editor: a row appears in <code>profiles</code> instantly.",
                    "ব্রাউজারে সাইন-আপ করে Supabase Table Editor রিলোড করুন: সাথে সাথে <code>profiles</code>-এ একটি রো দেখা যাবে।",
                ),
                (
                    "Bookmark an idea, clear <code>localStorage</code>, reload: the bookmark returns from PostgreSQL.",
                    "একটি আইডিয়া বুকমার্ক করে <code>localStorage</code> মুছে রিলোড করুন: বুকমার্ক PostgreSQL থেকে ফিরে আসবে।",
                ),
                (
                    "Send a connection request, then show the row with <code>user_id</code> filled in — and a guest request with <code>user_id = NULL</code>.",
                    "একটি কানেকশন রিকোয়েস্ট পাঠিয়ে <code>user_id</code> ভরা রো দেখান — আর গেস্ট রিকোয়েস্টে <code>user_id = NULL</code>।",
                ),
            ]
        )
    )


# =============================================================================
# 2. ARCHITECTURE
# =============================================================================


def s_architecture() -> str:
    return (
        para(
            "The important design choice: the API is a separate application. Vercel hosts "
            "two things side by side — the static pages from <code>public/</code> and the "
            "Python function from <code>app/main.py</code> — so the browser talks to the "
            "same domain and no CORS problem exists in production.",
            "সবচেয়ে গুরুত্বপূর্ণ সিদ্ধান্ত: API আলাদা একটি অ্যাপ্লিকেশন। Vercel একসাথে দুটি "
            "জিনিস হোস্ট করে — <code>public/</code> থেকে স্ট্যাটিক পেজ আর "
            "<code>app/main.py</code> থেকে Python ফাংশন — তাই ব্রাউজার একই ডোমেইনে কথা বলে, "
            "প্রোডাকশনে CORS সমস্যা থাকে না।",
        )
        + pre(
            """
+------------------------------+          +------------------------------+
|  Browser                     |          |  Supabase project            |
|  6 HTML pages                |          |                              |
|  public/js/*.js              |          |  Auth   (accounts, tokens)   |
|                              |          |  PostgreSQL (16 tables)      |
|  localStorage cache          |          |  Row Level Security ON       |
+--------------+---------------+          +--------------+---------------+
               |                                         ^
               |  fetch('/api/...')                      |  supabase-py
               |  Authorization: Bearer <token>          |  HTTPS + secret key
               v                                         |
+------------------------------+                         |
|  Vercel                      |                         |
|                              |                         |
|  /            -> public/     |                         |
|  /api/...     -> app/main.py +-------------------------+
|                              |
|  env vars: SUPABASE_URL,     |
|            ANON_KEY,         |
|            SERVICE_ROLE_KEY  |
+------------------------------+
"""
        )
        + h3("One request, step by step", "একটি রিকোয়েস্ট, ধাপে ধাপে")
        + steps_list(
            [
                (
                    "The student clicks <i>Bookmark</i>. <code>research.js</code> updates the JavaScript array and writes it to <code>localStorage</code> immediately, so the button answers instantly.",
                    "শিক্ষার্থী <i>Bookmark</i> চাপে। <code>research.js</code> সাথে সাথে JavaScript অ্যারে আপডেট করে <code>localStorage</code>-এ লেখে, তাই বোতামটি তৎক্ষণাৎ সাড়া দেয়।",
                ),
                (
                    "<code>api.js</code> then calls <code>PUT /api/me/bookmarks/ideas</code> with the whole list and the token from <code>localStorage</code>.",
                    "এরপর <code>api.js</code> পুরো লিস্ট আর <code>localStorage</code>-এর টোকেন নিয়ে <code>PUT /api/me/bookmarks/ideas</code> কল করে।",
                ),
                (
                    "Vercel runs the FastAPI application itself, defined in <code>app/main.py</code>. FastAPI matches the path, validates the JSON with a Pydantic model, and rejects bad input with 422 before any code runs.",
                    "Vercel নিজেই <code>app/main.py</code>-তে সংজ্ঞায়িত FastAPI অ্যাপ্লিকেশনটি চালায়। FastAPI পাথ মিলিয়ে, Pydantic মডেল দিয়ে JSON যাচাই করে, আর ভুল ইনপুটে কোড চলার আগেই 422 ফেরত দেয়।",
                ),
                (
                    "<code>dependencies.py</code> reads the <code>Authorization</code> header and asks Supabase Auth who the token belongs to. Invalid token → 401, and the route never runs.",
                    "<code>dependencies.py</code> <code>Authorization</code> হেডার পড়ে Supabase Auth-কে জিজ্ঞেস করে টোকেনটি কার। টোকেন ভুল হলে → 401, রুটটি আর চলে না।",
                ),
                (
                    "The router upserts the requested ids, then deletes rows that are no longer in the list — so the table ends up exactly matching the browser array.",
                    "রাউটার চাওয়া id-গুলো upsert করে, তারপর লিস্টে নেই এমন রো ডিলিট করে — ফলে টেবিল হুবহু ব্রাউজার অ্যারের মতো হয়।",
                ),
                (
                    "A JSON answer returns to the browser. If it fails, <code>api.js</code> logs one warning and the screen keeps working from the local cache.",
                    "JSON উত্তর ব্রাউজারে ফেরে। ব্যর্থ হলে <code>api.js</code> একটি ওয়ার্নিং লগ করে আর স্ক্রিন লোকাল ক্যাশ থেকেই কাজ চালিয়ে যায়।",
                ),
            ]
        )
        + h3("Two Supabase clients — and why", "দুটি Supabase ক্লায়েন্ট — কেন")
        + table(
            [("Client", "ক্লায়েন্ট"), ("Key used", "কোন কী"), ("Used for", "কী কাজে"), ("Leaves the server?", "সার্ভার ছাড়ে?")],
            [
                (
                    "<code>get_auth_client()</code>",
                    ("Public / anon key", "পাবলিক / anon কী"),
                    ("Sign up, sign in, verify a token", "সাইন-আপ, সাইন-ইন, টোকেন যাচাই"),
                    ("No", "না"),
                ),
                (
                    "<code>get_admin_client()</code>",
                    ("Secret / service-role key", "সিক্রেট / service-role কী"),
                    ("Reading and writing the 16 tables; bypasses Row Level Security", "১৬টি টেবিল পড়া-লেখা; Row Level Security বাইপাস করে"),
                    ("Never", "কখনো না"),
                ),
            ],
        )
        + note(
            "The secret key bypasses Row Level Security, so it must never appear in HTML or JavaScript. "
            "That is exactly why the browser calls our Python API instead of calling Supabase directly: "
            "the key stays in the server's environment variables.",
            "সিক্রেট কী Row Level Security বাইপাস করে, তাই এটি কখনো HTML বা JavaScript-এ থাকতে পারে না। "
            "ঠিক এ কারণেই ব্রাউজার সরাসরি Supabase-কে কল না করে আমাদের Python API-কে কল করে: কী-টি "
            "সার্ভারের environment variables-এ থাকে।",
            "warn",
        )
        + h3("Where each piece lives", "কোন অংশ কোথায়")
        + pre(
            """
thesisbridge-bd/
├── app/                    <- the Python API (never served as files)
│   ├── main.py             <- builds the FastAPI app; Vercel enters here
│   ├── config.py           <- reads environment variables
│   ├── database.py         <- the two Supabase clients
│   ├── dependencies.py     <- token checking for protected routes
│   ├── schemas.py          <- Pydantic models (request/response shapes)
│   └── routers/
│       ├── content.py      <- 12 public GET endpoints
│       ├── auth.py         <- signup, login, me
│       ├── user_state.py   <- the saved lists + profile
│       └── requests.py     <- connection requests
├── public/                 <- the website, served at the domain root
│   ├── *.html              <- the 6 pages
│   ├── css/, assets/
│   └── js/api.js           <- the bridge between the pages and the API
├── sql/001_create_tables.sql
├── scripts/seed_supabase.py
├── requirements.txt
├── vercel.json
└── .env                    <- secrets, gitignored, never deployed
"""
        )
    )


# =============================================================================
# 3. THE BUILD, STEP BY STEP
# =============================================================================


def s_steps() -> str:
    return (
        para(
            "This is the real order the work happened in. Each step ends with the evidence "
            "that it actually worked, because \"it looked fine\" is not proof.",
            "কাজটি আসলে যে ক্রমে হয়েছে সেটাই এখানে। প্রতিটি ধাপের শেষে প্রমাণ দেওয়া আছে যে এটি "
            "সত্যিই কাজ করেছে, কারণ \"দেখতে ঠিক লাগছিল\" কোনো প্রমাণ নয়।",
        )
        + step(
            1,
            "Split the site from the server",
            "সাইট ও সার্ভার আলাদা করা",
            para(
                "Everything the browser needs moved into <code>public/</code>. Vercel serves "
                "that folder at <code>/</code> and treats <code>app/main.py</code> as the "
                "serverless function. Relative links like <code>css/style.css</code> kept "
                "working unchanged.",
                "ব্রাউজারের যা কিছু দরকার সব <code>public/</code>-এ সরানো হলো। Vercel সেই ফোল্ডার "
                "<code>/</code>-এ সার্ভ করে আর <code>app/main.py</code>-কে সার্ভারলেস ফাংশন ধরে। "
                "<code>css/style.css</code>-এর মতো রিলেটিভ লিংক অপরিবর্তিত কাজ করে।",
            ),
        )
        + step(
            2,
            "Create a Python environment and install the packages",
            "Python এনভায়রনমেন্ট তৈরি ও প্যাকেজ ইনস্টল",
            para(
                "A virtual environment keeps this project's packages separate from the rest "
                "of the machine. Five packages are enough for the whole backend.",
                "ভার্চুয়াল এনভায়রনমেন্ট এই প্রজেক্টের প্যাকেজ মেশিনের বাকি অংশ থেকে আলাদা রাখে। "
                "পুরো ব্যাকএন্ডের জন্য পাঁচটি প্যাকেজই যথেষ্ট।",
            )
            + cmd(
                "python -m venv .venv\n"
                ".\\.venv\\Scripts\\Activate.ps1\n"
                "pip install -r requirements.txt"
            )
            + code(
                "requirements.txt",
                "requirements.txt — the five dependencies",
                "requirements.txt — পাঁচটি ডিপেন্ডেন্সি",
            )
            + note(
                "Vercel reads this exact file during deployment, so the local and live "
                "environments install the same versions.",
                "ডিপ্লয়ের সময় Vercel ঠিক এই ফাইলটিই পড়ে, তাই লোকাল ও লাইভ পরিবেশে একই ভার্সন "
                "ইনস্টল হয়।",
                "good",
            ),
        )
        + step(
            3,
            "Put the secrets in one file",
            "সব সিক্রেট একটি ফাইলে রাখা",
            para(
                "Credentials live in <code>.env</code>, which is listed in "
                "<code>.gitignore</code>. <code>.env.example</code> is the committed template "
                "with empty values, so anyone cloning the repo knows which names to fill in.",
                "ক্রেডেনশিয়াল থাকে <code>.env</code>-এ, যা <code>.gitignore</code>-এ আছে। "
                "<code>.env.example</code> হলো কমিট করা টেমপ্লেট, খালি মানসহ — তাই রিপো ক্লোন "
                "করা যে কেউ জানে কোন নামগুলো পূরণ করতে হবে।",
            )
            + cmd("Copy-Item .env.example .env\nnotepad .env")
            + code(
                ".env.example",
                ".env.example — the committed template (no real keys)",
                ".env.example — কমিট করা টেমপ্লেট (আসল কী নেই)",
            )
        )
        + step(
            4,
            "Read the settings in exactly one place",
            "সেটিংস পড়া ঠিক এক জায়গায়",
            para(
                "<code>app/config.py</code> is the only file that touches "
                "<code>os.environ</code>. It also defines <code>missing_settings()</code>, "
                "which both the health check and the client factory use — so a missing key "
                "produces one clear sentence instead of a confusing Supabase traceback.",
                "<code>app/config.py</code>-ই একমাত্র ফাইল যা <code>os.environ</code> স্পর্শ করে। "
                "এতে <code>missing_settings()</code> আছে, যা হেলথ চেক ও ক্লায়েন্ট ফ্যাক্টরি "
                "দুটোই ব্যবহার করে — তাই কী না থাকলে ঝাপসা Supabase ট্রেসব্যাকের বদলে একটি "
                "স্পষ্ট বাক্য পাওয়া যায়।",
            )
            + code(
                "app/config.py",
                "app/config.py — all environment settings",
                "app/config.py — সব environment সেটিংস",
            )
        )
        + step(
            5,
            "Create the Supabase project",
            "Supabase প্রজেক্ট তৈরি",
            para(
                "On supabase.com: create a project, then copy three values from "
                "<i>Project Settings → API</i>: the project URL, the publishable (anon) key "
                "and the secret (service_role) key. This project used the newer key format "
                "<code>sb_publishable_…</code> / <code>sb_secret_…</code>, which "
                "supabase-py 2.34 accepts.",
                "supabase.com-এ: একটি প্রজেক্ট খুলে <i>Project Settings → API</i> থেকে তিনটি মান "
                "কপি করুন: প্রজেক্ট URL, publishable (anon) কী আর secret (service_role) কী। এই "
                "প্রজেক্টে নতুন ফরম্যাট <code>sb_publishable_…</code> / <code>sb_secret_…</code> "
                "ব্যবহার করা হয়েছে, যা supabase-py 2.34 গ্রহণ করে।",
            )
            + note(
                "Both keys were tested before writing any code: the publishable key against "
                "<code>/auth/v1/health</code> (200) and the secret key against "
                "<code>/rest/v1/</code> (200). The table API answered \"Secret API key "
                "required\" for the publishable key, which proved the two are different and "
                "correctly assigned.",
                "কোড লেখার আগেই দুটি কী পরীক্ষা করা হয়েছে: publishable কী "
                "<code>/auth/v1/health</code>-এ (২০০) আর secret কী <code>/rest/v1/</code>-এ "
                "(২০০)। publishable কী দিয়ে টেবিল API বলেছিল \"Secret API key required\" — "
                "এতে প্রমাণ হয় দুটি আলাদা এবং সঠিকভাবে বসানো।",
                "good",
            ),
        )
        + step(
            6,
            "Create the schema in the SQL Editor",
            "SQL Editor-এ স্কিমা তৈরি",
            para(
                "The whole schema is one paste. It is written to be safe to run twice: "
                "tables use <code>IF NOT EXISTS</code> and every policy is dropped before it "
                "is recreated.",
                "পুরো স্কিমা একবার পেস্ট করলেই হয়। এটি দুইবার চালালেও নিরাপদ: টেবিলগুলো "
                "<code>IF NOT EXISTS</code> ব্যবহার করে আর প্রতিটি পলিসি নতুন করে বানানোর আগে "
                "ড্রপ করা হয়।",
            )
            + steps_list(
                [
                    (
                        "Supabase dashboard → <b>SQL Editor</b> → <b>New query</b>.",
                        "Supabase ড্যাশবোর্ড → <b>SQL Editor</b> → <b>New query</b>।",
                    ),
                    (
                        "Paste all of <code>sql/001_create_tables.sql</code> → <b>Run</b>.",
                        "পুরো <code>sql/001_create_tables.sql</code> পেস্ট → <b>Run</b>।",
                    ),
                    (
                        "Expected answer: <code>Success. No rows returned</code> — that is normal for DDL statements.",
                        "প্রত্যাশিত উত্তর: <code>Success. No rows returned</code> — DDL স্টেটমেন্টে এটি স্বাভাবিক।",
                    ),
                ]
            )
            + note(
                "Before this step the API returned <code>404 PGRST205 — Could not find the "
                "table</code>. That error is now translated by the API into a sentence "
                "telling you to run this file.",
                "এই ধাপের আগে API <code>404 PGRST205 — Could not find the table</code> ফেরত "
                "দিত। সেই এররটি এখন API অনুবাদ করে বলে দেয় এই ফাইলটি চালাতে হবে।",
            ),
        )
        + step(
            7,
            "Fill the content tables with the seeder",
            "সিডার দিয়ে কনটেন্ট টেবিল ভরা",
            para(
                "<code>scripts/seed_supabase.py</code> reads <code>seed/content.json</code> "
                "(exported from the old <code>data.js</code>), inserts every table, then "
                "queries each table again and compares the real row count with the expected "
                "one.",
                "<code>scripts/seed_supabase.py</code> <code>seed/content.json</code> পড়ে "
                "(পুরোনো <code>data.js</code> থেকে নেওয়া), প্রতিটি টেবিলে ইনসার্ট করে, তারপর "
                "আবার প্রতিটি টেবিল কোয়েরি করে আসল রো-সংখ্যা প্রত্যাশিত সংখ্যার সাথে মেলায়।",
            )
            + cmd(r".\.venv\Scripts\python.exe scripts\seed_supabase.py")
            + note(
                "The verification block printed <b>OK</b> for all nine content tables: "
                "categories 9, filter_options 58, research_ideas 20, supervisors 12, "
                "resources 20, publication_guides 7, roadmap_steps 8, faqs 8, "
                "journal_checklist_items 8 — 150 rows in total.",
                "যাচাই ব্লকটি নয়টি কনটেন্ট টেবিলের সবগুলোতেই <b>OK</b> দেখিয়েছে: "
                "categories ৯, filter_options ৫৮, research_ideas ২০, supervisors ১২, "
                "resources ২০, publication_guides ৭, roadmap_steps ৮, faqs ৮, "
                "journal_checklist_items ৮ — মোট ১৫০টি রো।",
                "good",
            ),
        )
        + step(
            8,
            "Describe the data with Pydantic models",
            "Pydantic মডেল দিয়ে ডেটার আকার বর্ণনা",
            para(
                "<code>app/schemas.py</code> is the contract. It does three jobs at once: "
                "validates incoming JSON, converts database snake_case to browser camelCase, "
                "and documents the API in <code>/docs</code> automatically.",
                "<code>app/schemas.py</code> হলো চুক্তি। এটি একসাথে তিনটি কাজ করে: আসা JSON "
                "যাচাই করে, ডেটাবেসের snake_case-কে ব্রাউজারের camelCase-এ বদলায়, আর "
                "<code>/docs</code>-এ API ডকুমেন্টেশন নিজে থেকে বানায়।",
            )
            + code(
                "app/schemas.py",
                "app/schemas.py — 27 models plus the CamelModel base",
                "app/schemas.py — CamelModel বেস + ২৭টি মডেল",
            )
        )
        + step(
            9,
            "Write the routers",
            "রাউটার লেখা",
            para(
                "Four small files, each with one responsibility: public content, accounts, "
                "the user's own saved data, and connection requests. Keeping them separate "
                "means a change to bookmarks cannot accidentally break login.",
                "চারটি ছোট ফাইল, প্রতিটির একটি দায়িত্ব: পাবলিক কনটেন্ট, অ্যাকাউন্ট, ইউজারের "
                "নিজের সেভ করা ডেটা, আর কানেকশন রিকোয়েস্ট। আলাদা রাখায় বুকমার্ক বদলালে ভুলে "
                "লগইন ভাঙার সুযোগ কম।",
            )
            + table(
                [("File", "ফাইল"), ("Endpoints", "endpoint"), ("Needs a token?", "টোকেন লাগে?")],
                [
                    ("routers/content.py", "12", ("No", "না")),
                    ("routers/auth.py", "3", ("Only /me", "শুধু /me")),
                    ("routers/user_state.py", "7", ("Yes", "হ্যাঁ")),
                    ("routers/requests.py", "3", ("1 public, 2 protected", "১টি পাবলিক, ২টি প্রোটেক্টেড")),
                ],
            )
        )
        + step(
            10,
            "Assemble the app and add a health check",
            "অ্যাপ জোড়া লাগানো ও হেলথ চেক",
            para(
                "<code>app/main.py</code> creates the FastAPI object, enables CORS, registers "
                "the four routers under <code>/api</code>, and adds two friendly error "
                "handlers. The object is named <code>app</code> because Vercel looks for a "
                "FastAPI instance with exactly that name in this file, so the label is a "
                "contract rather than a preference.",
                "<code>app/main.py</code> FastAPI অবজেক্ট বানায়, CORS চালু করে, চারটি রাউটার "
                "<code>/api</code>-এর নিচে যোগ করে, আর দুটি বন্ধুত্বপূর্ণ এরর হ্যান্ডলার দেয়। "
                "অবজেক্টের নাম <code>app</code> কারণ Vercel এই ফাইলে ঠিক ওই নামের FastAPI "
                "ইনস্ট্যান্স খোঁজে, তাই নামটি পছন্দ নয়, চুক্তি।",
            )
            + cmd(
                r".\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
                "\n"
                "curl http://127.0.0.1:8000/api/health"
            )
            + note(
                "The health answer was <code>{status: ok, databaseConfigured: true, "
                "missingSettings: []}</code> — the proof that <code>config.py</code> read the "
                "new key format correctly.",
                "হেলথ উত্তর ছিল <code>{status: ok, databaseConfigured: true, "
                "missingSettings: []}</code> — এটাই প্রমাণ যে <code>config.py</code> নতুন "
                "কী-ফরম্যাট ঠিকভাবে পড়েছে।",
                "good",
            )
        )
        + step(
            11,
            "Connect the website to the API",
            "ওয়েবসাইটকে API-তে যুক্ত করা",
            para(
                "<code>public/js/api.js</code> is the only new frontend file. It is loaded "
                "with <code>defer</code> on all six pages, exposes <code>TB.ready</code>, and "
                "replaces <code>window.TB_DATA</code> with the API response. If the API is "
                "unreachable it logs one warning and the site falls back to the bundled "
                "<code>data.js</code> instead of breaking.",
                "<code>public/js/api.js</code> একমাত্র নতুন ফ্রন্টএন্ড ফাইল। ছয়টি পেজেই "
                "<code>defer</code> দিয়ে লোড হয়, <code>TB.ready</code> দেয়, আর "
                "<code>window.TB_DATA</code>-কে API উত্তর দিয়ে বদলে দেয়। API না পেলে একটি "
                "ওয়ার্নিং লগ করে সাইট ভাঙার বদলে বান্ডল করা <code>data.js</code>-এ ফিরে যায়।",
            )
            + table(
                [("Old line", "পুরোনো"), ("New behaviour", "নতুন"), ("User sees", "ইউজার দেখে")],
                [
                    ("<code>window.TB_DATA</code> from data.js", ("Built from GET /api/content", "GET /api/content থেকে তৈরি"), ("Nothing different", "কিছুই আলাদা নয়")),
                    ("Bookmark saved to localStorage", ("localStorage + PUT to the API", "localStorage + API-তে PUT"), ("Saved badge, survives reload", "সেভ ব্যাজ, রিলোডেও থাকে")),
                    ("Login was a fake form", ("Supabase Auth token", "Supabase Auth টোকেন"), ("Real account, real 401s", "আসল অ্যাকাউন্ট, আসল ৪০১")),
                ],
            )
        )
        + step(
            12,
            "Prove it works, then clean up",
            "কাজ করছে প্রমাণ করা, তারপর পরিষ্কার করা",
            para(
                "Two layers of testing: a 57-assertion HTTP test against the live Supabase "
                "project, and a real browser run through the actual forms. Test data was "
                "deleted afterwards so the Table Editor is clean for a demo.",
                "দুই স্তরের পরীক্ষা: আসল Supabase প্রজেক্টের বিরুদ্ধে ৫৭টি assertion-এর HTTP "
                "টেস্ট, আর আসল ফর্ম দিয়ে সত্যিকারের ব্রাউজার রান। পরে টেস্ট-ডেটা মুছে ফেলা "
                "হয়, যাতে ডেমোর জন্য Table Editor পরিষ্কার থাকে।",
            )
            + bullets(
                [
                    (
                        "API suite: content counts, camelCase shape, sign-up, 401 without a token, all five lists, partial profile update, member and guest requests, withdraw, login round trip, 422 validation, direct table reads.",
                        "API স্যুট: কনটেন্ট সংখ্যা, camelCase আকার, সাইন-আপ, টোকেন ছাড়া ৪০১, পাঁচটি লিস্ট, প্রোফাইলের আংশিক আপডেট, মেম্বার ও গেস্ট রিকোয়েস্ট, উইথড্র, লগইন রাউন্ড ট্রিপ, ৪২২ ভ্যালিডেশন, সরাসরি টেবিল পড়া।",
                    ),
                    (
                        "Browser run: signup → bookmark → roadmap → checklist → delete the local lists → reload → restored from PostgreSQL → logout → login → connection request.",
                        "ব্রাউজার রান: সাইনআপ → বুকমার্ক → রোডম্যাপ → চেকলিস্ট → লোকাল লিস্ট মুছে দেওয়া → রিলোড → PostgreSQL থেকে ফিরে আসা → লগআউট → লগইন → কানেকশন রিকোয়েস্ট।",
                    ),
                ]
            )
            + note(
                "Full evidence, with the exact numbers, is in section 9.",
                "সম্পূর্ণ প্রমাণ ও সঠিক সংখ্যা section ৯-এ আছে।",
                "good",
            ),
        )
    )


# =============================================================================
# 4. DATABASE DESIGN
# =============================================================================


def s_database() -> str:
    return (
        para(
            "Sixteen tables, in three groups that behave very differently: <b>reference</b> "
            "tables (small vocabularies used by filters), <b>content</b> tables (the public "
            "library, read by everyone, written only by the seeder), and <b>user</b> tables "
            "(one row per account per item, protected by Row Level Security).",
            "ষোলটি টেবিল, তিনটি ভাগে — এদের আচরণ সম্পূর্ণ আলাদা: <b>reference</b> টেবিল (ফিল্টারে "
            "ব্যবহৃত ছোট ভোকাবুলারি), <b>content</b> টেবিল (পাবলিক লাইব্রেরি, সবাই পড়ে, লেখে শুধু "
            "সিডার), আর <b>user</b> টেবিল (প্রতি অ্যাকাউন্টে প্রতি আইটেমে একটি রো, Row Level "
            "Security দিয়ে সুরক্ষিত)।",
        )
        + h3("All 16 tables", "সব ১৬টি টেবিল")
        + table(
            [("#", "ক্র."), ("Table", "টেবিল"), ("Group", "ভাগ"), ("What it stores", "কী রাখে"), ("Rows", "রো")],
            [
                ("1", "categories", ("reference", "রেফারেন্স"), ("Filter chips: AI, IoT, Cybersecurity…", "ফিল্টার চিপ: AI, IoT, Cybersecurity…"), "9"),
                ("2", "filter_options", ("reference", "রেফারেন্স"), ("Every simple filter list, separated by a kind column", "সব সাধারণ ফিল্টার-লিস্ট, kind কলাম দিয়ে আলাদা"), "58"),
                ("3", "research_ideas", ("content", "কনটেন্ট"), ("The 20 idea cards, with text[] and jsonb details", "২০টি আইডিয়া কার্ড, text[] ও jsonb বিস্তারিতসহ"), "20"),
                ("4", "supervisors", ("content", "কনটেন্ট"), ("The 12 teacher profiles and their topics", "১২টি শিক্ষক প্রোফাইল ও তাদের টপিক"), "12"),
                ("5", "resources", ("content", "কনটেন্ট"), ("The 20 learning resources", "২০টি লার্নিং রিসোর্স"), "20"),
                ("6", "publication_guides", ("content", "কনটেন্ট"), ("The 7 Publication Hub guides; id is a slug", "৭টি পাবলিকেশন গাইড; id হলো slug"), "7"),
                ("7", "roadmap_steps", ("content", "কনটেন্ট"), ("The 8 thesis roadmap steps", "৮টি থিসিস রোডম্যাপ ধাপ"), "8"),
                ("8", "faqs", ("content", "কনটেন্ট"), ("The 8 questions; columns are question/answer", "৮টি প্রশ্ন; কলাম question/answer"), "8"),
                ("9", "journal_checklist_items", ("content", "কনটেন্ট"), ("The 8 checkpoint items", "৮টি চেকপয়েন্ট আইটেম"), "8"),
                ("10", "profiles", ("user", "ইউজার"), ("One row per account; id equals the auth user id", "প্রতি অ্যাকাউন্টে একটি রো; id = auth user id"), "0*"),
                ("11", "idea_bookmarks", ("user", "ইউজার"), ("user_id + idea_id, unique together", "user_id + idea_id, একসাথে unique"), "0*"),
                ("12", "saved_supervisors", ("user", "ইউজার"), ("user_id + supervisor_id", "user_id + supervisor_id"), "0*"),
                ("13", "roadmap_progress", ("user", "ইউজার"), ("user_id + step_id", "user_id + step_id"), "0*"),
                ("14", "read_guides", ("user", "ইউজার"), ("user_id + guide_id (text)", "user_id + guide_id (text)"), "0*"),
                ("15", "checklist_progress", ("user", "ইউজার"), ("user_id + item_id (text)", "user_id + item_id (text)"), "0*"),
                ("16", "connection_requests", ("user", "ইউজার"), ("Sent requests, pending by default; guests allowed", "পাঠানো রিকোয়েস্ট, ডিফল্ট pending; গেস্টও পারে"), "0*"),
            ],
        )
        + note(
            "<b>0*</b> means the table is empty right now on purpose: the automated tests created "
            "rows, and those test accounts were deleted afterwards so the demo database starts clean. "
            "The content tables were never touched (150 rows intact).",
            "<b>0*</b> মানে টেবিলটি এখন ইচ্ছাকৃতভাবে খালি: স্বয়ংক্রিয় টেস্ট রো তৈরি করেছিল, "
            "পরে সেই টেস্ট অ্যাকাউন্টগুলো মুছে ফেলা হয়েছে যাতে ডেমো ডেটাবেস পরিষ্কার থাকে। "
            "কনটেন্ট টেবিলে হাত পড়েনি (১৫০টি রো অক্ষত)।",
        )
        + h3("Relationships", "সম্পর্ক")
        + pre(
            """
categories.name  <-- research_ideas.category        (text reference)
supervisors.id   <-- connection_requests.supervisor_id   (FK, on delete cascade)
auth.users.id    <-- profiles.id                     (FK, on delete cascade)
auth.users.id    <-- idea_bookmarks.user_id          (FK, on delete cascade)
auth.users.id    <-- connection_requests.user_id     (FK, NULL for guests,
                                                       on delete set null)

research_ideas.id      --(no FK, on purpose)--> hand-typed ids from the old
research_ideas             data file are reused, so the frontend's saved
supervisors.id             localStorage values keep pointing at the same row
roadmap_steps.id
publication_guides.id  (slug text)
journal_checklist_items.id (text)
"""
        )
        + bullets(
            [
                (
                    "<b>Deliberate omission:</b> the user tables have no foreign key to <code>research_ideas</code> or <code>supervisors</code>. The ids came from the old <code>data.js</code>, and keeping the same numbers means a bookmark saved before the migration still resolves to the right idea.",
                    "<b>ইচ্ছাকৃত বাদ:</b> user টেবিলে <code>research_ideas</code> বা <code>supervisors</code>-এর FK নেই। id-গুলো পুরোনো <code>data.js</code> থেকে এসেছে, আর একই সংখ্যা রাখায় মাইগ্রেশনের আগে সেভ করা বুকমার্কও সঠিক আইডিয়ায় মেলে।",
                ),
                (
                    "<b>Guests:</b> <code>connection_requests.user_id</code> is nullable, so a visitor can send a request without an account. A member's request stores their id; a guest's stores <code>NULL</code>.",
                    "<b>গেস্ট:</b> <code>connection_requests.user_id</code> nullable, তাই ইউজার অ্যাকাউন্ট ছাড়াই রিকোয়েস্ট পাঠাতে পারে। মেম্বারের রিকোয়েস্টে তার id থাকে; গেস্টের ক্ষেত্রে <code>NULL</code>।",
                ),
                (
                    "<b>Uniqueness:</b> every saved-list table has <code>unique (user_id, &lt;item&gt;)</code>. That is what makes <code>upsert(on_conflict=…)</code> possible, and it makes double-clicking a bookmark harmless.",
                    "<b>ইউনিকনেস:</b> প্রতিটি সেভ-লিস্ট টেবিলে <code>unique (user_id, &lt;item&gt;)</code> আছে। এ কারণেই <code>upsert(on_conflict=…)</code> সম্ভব, আর বুকমার্কে দুইবার ক্লিক করলেও ক্ষতি হয় না।",
                ),
            ]
        )
        + h3("Row Level Security (RLS)", "Row Level Security (RLS)")
        + para(
            "RLS is a PostgreSQL feature: even if someone obtained the <b>publishable</b> key "
            "and called Supabase directly, the database itself refuses to return another "
            "student's rows. Our API uses the secret key, which bypasses RLS — so the "
            "policies protect the direct path, and the Python code protects the API path.",
            "RLS হলো PostgreSQL-এর একটি বৈশিষ্ট্য: কেউ <b>publishable</b> কী নিয়ে সরাসরি "
            "Supabase-কে কল করলেও ডেটাবেস নিজেই অন্য শিক্ষার্থীর রো ফেরত দিতে অস্বীকার করে। "
            "আমাদের API সিক্রেট কী ব্যবহার করে, যা RLS বাইপাস করে — তাই পলিসিগুলো সরাসরি পথ "
            "রক্ষা করে, আর Python কোড API পথ রক্ষা করে।",
        )
        + snippet(
            """-- Content: anybody may read, nobody may write through the public key
create policy "Public content is readable" on public.research_ideas
  for select to anon, authenticated using (true);

-- Profiles: you only see and edit your own row
create policy "Users read their own profile" on public.profiles
  for select to authenticated using (auth.uid() = id);

create policy "Users update their own profile" on public.profiles
  for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);""",
            "A representative sample of the policies",
            "পলিসিগুলোর একটি প্রতিনিধিত্বমূলক নমুনা",
        )
        + h3("The updated_at trigger", "updated_at ট্রিগার")
        + para(
            "<code>profiles.updated_at</code> should change automatically whenever a row is "
            "edited, so no Python code has to remember to set it.",
            "<code>profiles.updated_at</code> রো এডিট হলেই নিজে থেকে বদলানো উচিত, যাতে Python "
            "কোডে আলাদা করে সেট করতে না হয়।",
        )
        + snippet(
            """create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_touch_updated_at
  before update on public.profiles
  for each row execute function public.touch_updated_at();""",
            "A trigger that runs before every UPDATE",
            "প্রতিটি UPDATE-এর আগে চলা একটি ট্রিগার",
        )
        + h3("The complete schema file", "সম্পূর্ণ স্কিমা ফাইল")
        + para(
            "372 lines, commented in the same style as the Python code. Safe to re-run.",
            "৩১০ লাইন, Python কোডের মতোই কমেন্ট করা। আবার চালানো নিরাপদ।",
        )
        + code(
            "sql/001_create_tables.sql",
            "sql/001_create_tables.sql — tables, indexes, RLS, trigger",
            "sql/001_create_tables.sql — টেবিল, ইনডেক্স, RLS, ট্রিগার",
            collapsed=False,
            lang="sql",
        )
    )


# =============================================================================
# 5. BACKEND FILES, ONE BY ONE
# =============================================================================


def s_backend() -> str:
    return (
        para(
            "Every file is listed below with its real contents. The pattern is the same in "
            "each one: a module docstring says <i>why</i> the file exists, the code follows, "
            "and comments explain the non-obvious lines. Read them in this order and the "
            "request path makes sense.",
            "প্রতিটি ফাইল তার আসল কনটেন্টসহ নিচে দেওয়া। প্রতিটিতে একই ধরন: মডিউল ডকস্ট্রিং বলে "
            "<i>কেন</i> ফাইলটি আছে, তারপর কোড, আর কমেন্ট অস্পষ্ট লাইনগুলো বোঝায়। এই ক্রমে পড়লে "
            "রিকোয়েস্টের পথ পরিষ্কার হয়ে যায়।",
        )
        + h3("Load order", "লোড হওয়ার ক্রম")
        + pre(
            """
main.py           creates FastAPI, adds CORS, registers routers, error handlers
  |
  +-- config.py          reads .env / Vercel env vars  -> 3 strings
  +-- database.py        builds 2 Supabase clients (anon + secret)
  +-- dependencies.py    turns "Authorization: Bearer ..." into a user dict
  +-- schemas.py         validates input, shapes output (camelCase)
  +-- routers/
        content.py       public reads   (12)
        auth.py          signup/login/me (3)
        user_state.py    saved lists + profile (7)
        requests.py      connection requests (3)
"""
        )
        + h3("File map", "ফাইল তালিকা")
        + table(
            [("File", "ফাইল"), ("Lines", "লাইন"), ("Responsibility", "দায়িত্ব")],
            [
                ("app/main.py", "208", ("Builds the app, CORS, routers, health, error handlers", "অ্যাপ, CORS, রাউটার, হেলথ, এরর হ্যান্ডলার")),
                ("app/config.py", "93", ("The only place that reads environment variables", "একমাত্র জায়গা যেখানে env পড়া হয়")),
                ("app/database.py", "63", ("Two reusable Supabase clients", "দুটি পুনর্ব্যবহারযোগ্য Supabase ক্লায়েন্ট")),
                ("app/dependencies.py", "122", ("Token extraction and verification", "টোকেন বের করা ও যাচাই")),
                ("app/schemas.py", "323", ("27 Pydantic models and the camelCase base", "২৭টি Pydantic মডেল ও camelCase বেস")),
                ("app/routers/content.py", "410", ("12 public content endpoints", "১২টি পাবলিক কনটেন্ট endpoint")),
                ("app/routers/auth.py", "270", ("Signup, login, current user", "সাইনআপ, লগইন, বর্তমান ইউজার")),
                ("app/routers/user_state.py", "270", ("Saved lists and profile edits", "সেভ করা লিস্ট ও প্রোফাইল এডিট")),
                ("app/routers/requests.py", "139", ("Connection requests", "কানেকশন রিকোয়েস্ট")),
                ("scripts/seed_supabase.py", "375", ("Fills content tables and verifies counts", "কনটেন্ট টেবিল ভরে ও সংখ্যা যাচাই করে")),
            ],
        )
        + h3("1. app/main.py — the entry point", "১. app/main.py — প্রবেশদ্বার")
        + para(
            "Creates the <code>FastAPI</code> object, names it <code>app</code> (Vercel requires "
            "that name), enables CORS, registers four routers under <code>/api</code>, and "
            "defines <code>/api/health</code>. The two exception handlers are what turn a "
            "Python crash into a readable JSON message.",
            "<code>FastAPI</code> অবজেক্ট বানায়, নাম দেয় <code>app</code> (Vercel-এর জন্য বাধ্যতামূলক), "
            "CORS চালু করে, <code>/api</code>-এর নিচে চারটি রাউটার যোগ করে, আর "
            "<code>/api/health</code> দেয়। দুটি exception handler-ই Python ক্র্যাশকে পাঠযোগ্য "
            "JSON বার্তায় বদলায়।",
        )
        + bullets(
            [
                (
                    "<b>CORS:</b> <code>allow_credentials=False</code> because the frontend sends a Bearer token, not cookies — and browsers forbid <code>*</code> together with credentials.",
                    "<b>CORS:</b> <code>allow_credentials=False</code> কারণ ফ্রন্টএন্ড Bearer টোকেন পাঠায়, কুকি নয় — আর ব্রাউজার <code>*</code>-এর সাথে credentials নিষেধ করে।",
                ),
                (
                    "<b>Order matters:</b> routers are included before the health route is defined, but FastAPI matches by path, so ordering does not shadow anything.",
                    "<b>ক্রম:</b> হেলথ রুটের আগে রাউটার যোগ হয়, তবে FastAPI পাথ দিয়ে মেলায়, তাই কোনো রুট ঢাকা পড়ে না।",
                ),
                (
                    "<b>APIError handler:</b> reads <code>exc.code</code> and <code>exc.message</code> as attributes — <code>exc.args[0]</code> is only a string and cannot be parsed reliably.",
                    "<b>APIError হ্যান্ডলার:</b> <code>exc.code</code> ও <code>exc.message</code> অ্যাট্রিবিউট হিসেবে পড়ে — <code>exc.args[0]</code> শুধু স্ট্রিং, নির্ভরযোগ্যভাবে পার্স করা যায় না।",
                ),
            ]
        )
        + code(
            "app/main.py",
            "app/main.py — full source",
            "app/main.py — সম্পূর্ণ সোর্স",
            collapsed=False,
        )
        + h3("2. app/config.py — settings in one place", "২. app/config.py — এক জায়গায় সেটিংস")
        + para(
            "<code>load_dotenv()</code> reads a local <code>.env</code> if one exists; on Vercel "
            "there is no such file, so the call does nothing and the values come from the "
            "platform. The same code works in both places.",
            "<code>load_dotenv()</code> লোকাল <code>.env</code> থাকলে পড়ে; Vercel-এ এমন ফাইল "
            "থাকে না, তাই কলটি কিছুই করে না আর মান আসে প্ল্যাটফর্ম থেকে। একই কোড দুই জায়গায় "
            "কাজ করে।",
        )
        + code(
            "app/config.py",
            "app/config.py — full source",
            "app/config.py — সম্পূর্ণ সোর্স",
        )
        + h3("3. app/database.py — two reusable clients", "৩. app/database.py — দুটি পুনর্ব্যবহারযোগ্য ক্লায়েন্ট")
        + para(
            "A module-level variable acts as a lazy singleton: the client is created the first "
            "time a request needs it and reused afterwards. Creating a client per request "
            "would add a network round-trip to every page load.",
            "মডিউল-লেভেল ভ্যারিয়েবল lazy singleton-এর কাজ করে: প্রথম রিকোয়েস্টে ক্লায়েন্ট তৈরি "
            "হয়, পরে পুনর্ব্যবহার হয়। প্রতি রিকোয়েস্টে নতুন ক্লায়েন্ট বানালে প্রতিটি পেজ "
            "লোডে অতিরিক্ত নেটওয়ার্ক রাউন্ড-ট্রিপ লাগত।",
        )
        + code(
            "app/database.py",
            "app/database.py — full source",
            "app/database.py — সম্পূর্ণ সোর্স",
        )
        + h3("4. app/dependencies.py — the token gate", "৪. app/dependencies.py — টোকেনের দরজা")
        + para(
            "A FastAPI <i>dependency</i> is a function that runs before the route. "
            "<code>get_current_user</code> is the strict version (401 when the token is "
            "missing or bad); <code>get_optional_user</code> is the lenient version used by "
            "the public connection-request form, where a broken token simply means \"treat "
            "this visitor as a guest\".",
            "FastAPI <i>dependency</i> হলো এমন ফাংশন যা রুটের আগে চলে। "
            "<code>get_current_user</code> কঠোর সংস্করণ (টোকেন না থাকলে বা ভুল হলে ৪০১); "
            "<code>get_optional_user</code> নমনীয় সংস্করণ, পাবলিক কানেকশন-রিকোয়েস্ট ফর্মে "
            "ব্যবহৃত — সেখানে ভাঙা টোকেন মানে \"এই ভিজিটরকে গেস্ট ধরো\"।",
        )
        + note(
            "The token is verified by asking Supabase (<code>auth.get_user(token)</code>), not by "
            "decoding it locally. That means an expired token, a deleted account and a forged "
            "signature all fail the same way, without us managing a JWT secret.",
            "টোকেন যাচাই হয় Supabase-কে জিজ্ঞেস করে (<code>auth.get_user(token)</code>), লোকালি "
            "ডিকোড করে নয়। তাই মেয়াদোত্তীর্ণ টোকেন, মুছে ফেলা অ্যাকাউন্ট আর জাল সিগনেচার — "
            "সবই একভাবেই ব্যর্থ হয়, আমাদের JWT সিক্রেট সামলাতে হয় না।",
            "good",
        )
        + code(
            "app/dependencies.py",
            "app/dependencies.py — full source",
            "app/dependencies.py — সম্পূর্ণ সোর্স",
        )
        + h3("5. app/schemas.py — the data contract", "৫. app/schemas.py — ডেটার চুক্তি")
        + para(
            "Every model inherits <code>CamelModel</code>, which sets two options: "
            "<code>alias_generator=to_camel</code> makes JSON camelCase, and "
            "<code>populate_by_name=True</code> lets the code build a model from database rows "
            "that use snake_case. One class definition therefore serves the database and the "
            "browser at the same time.",
            "প্রতিটি মডেল <code>CamelModel</code> থেকে উত্তরাধিকার নেয়, যা দুটি অপশন দেয়: "
            "<code>alias_generator=to_camel</code> JSON-কে camelCase করে, আর "
            "<code>populate_by_name=True</code> ডেটাবেসের snake_case রো থেকে মডেল বানাতে দেয়। "
            "তাই একটি ক্লাসই একসাথে ডেটাবেস ও ব্রাউজার — দুটোর কাজ করে।",
        )
        + table(
            [("Group", "ভাগ"), ("Models", "মডেল")],
            [
                (("Content", "কনটেন্ট"), "Category, ResearchIdea, Supervisor, Resource, GuideSection, PublicationGuide, RoadmapResource, RoadmapStep, Faq, ChecklistItem, ContentBundle"),
                (("List wrappers", "লিস্ট র‍্যাপার"), "IdeaListResponse, SupervisorListResponse, ResourceListResponse"),
                (("Auth", "অথ"), "SignupRequest, LoginRequest, UserOut, AuthResponse, ProfileUpdate"),
                (("List payloads", "লিস্ট পেলোড"), "IdeaIdsPayload, SupervisorIdsPayload, StepIdsPayload, GuideIdsPayload, ChecklistIdsPayload"),
                (("Requests", "রিকোয়েস্ট"), "ConnectionRequestCreate, ConnectionRequestOut, UserStateResponse"),
            ],
        )
        + code(
            "app/schemas.py",
            "app/schemas.py — full source",
            "app/schemas.py — সম্পূর্ণ সোর্স",
        )
        + h3("6. app/routers/content.py — the public library", "৬. app/routers/content.py — পাবলিক লাইব্রেরি")
        + para(
            "Twelve read-only endpoints. Three helpers do all the work: <code>_fetch</code> "
            "reads a whole table, <code>_safe_search</code> sanitises search text before it "
            "enters a PostgREST filter, and <code>_single</code> returns one row or a clean 404.",
            "বারোটি রিড-ওনলি endpoint। তিনটি হেল্পার সব কাজ করে: <code>_fetch</code> পুরো "
            "টেবিল পড়ে, <code>_safe_search</code> PostgREST ফিল্টারে ঢোকার আগে সার্চ-টেক্সট "
            "পরিষ্কার করে, আর <code>_single</code> একটি রো বা পরিষ্কার ৪০৪ দেয়।",
        )
        + note(
            "<code>_safe_search</code> replaces <code>, ( ) *</code> with spaces. Without it a "
            "search for <code>AI, ML (2024)</code> would break the query — and, worse, could "
            "inject extra filter clauses.",
            "<code>_safe_search</code> <code>, ( ) *</code>-কে স্পেস দিয়ে বদলায়। এটি না থাকলে "
            "<code>AI, ML (2024)</code> সার্চটি কোয়েরি ভেঙে দিত — আরও খারাপ, অতিরিক্ত ফিল্টার "
            "ক্লজ ইনজেক্ট করতে পারত।",
            "warn",
        )
        + code(
            "app/routers/content.py",
            "app/routers/content.py — full source",
            "app/routers/content.py — সম্পূর্ণ সোর্স",
        )
        + h3("7. app/routers/auth.py — accounts", "৭. app/routers/auth.py — অ্যাকাউন্ট")
        + para(
            "Sign-up is a three-step transaction: create the auth user, insert the profile "
            "row, then log the user in. If step 2 fails, step 1 is rolled back with "
            "<code>delete_user</code> so the database never contains an account without a "
            "profile.",
            "সাইন-আপ তিন ধাপের একটি লেনদেন: auth ইউজার তৈরি, প্রোফাইল রো ইনসার্ট, তারপর "
            "ইউজারকে লগইন করানো। ধাপ ২ ব্যর্থ হলে <code>delete_user</code> দিয়ে ধাপ ১ "
            "রোলব্যাক হয়, তাই ডেটাবেসে প্রোফাইলহীন অ্যাকাউন্ট কখনো থাকে না।",
        )
        + code(
            "app/routers/auth.py",
            "app/routers/auth.py — full source",
            "app/routers/auth.py — সম্পূর্ণ সোর্স",
        )
        + h3("8. app/routers/user_state.py — the saved lists", "৮. app/routers/user_state.py — সেভ করা লিস্ট")
        + para(
            "One GET returns everything (<code>/state</code>), and five PUTs each replace one "
            "list. The clever part is <code>_replace_rows</code>, explained in section 8.",
            "একটি GET সবকিছু ফেরত দেয় (<code>/state</code>), আর পাঁচটি PUT প্রতিটি একটি লিস্ট "
            "বদলায়। মূল কৌশল <code>_replace_rows</code>, যা section ৮-এ ব্যাখ্যা করা হয়েছে।",
        )
        + code(
            "app/routers/user_state.py",
            "app/routers/user_state.py — full source",
            "app/routers/user_state.py — সম্পূর্ণ সোর্স",
        )
        + h3("9. app/routers/requests.py — connection requests", "৯. app/routers/requests.py — কানেকশন রিকোয়েস্ট")
        + para(
            "Sending is public, listing and withdrawing need a token. Before inserting, the "
            "router checks that the supervisor actually exists — so a typo returns 404 instead "
            "of creating a row that points nowhere.",
            "পাঠানো পাবলিক, তালিকা ও প্রত্যাহারে টোকেন লাগে। ইনসার্টের আগে রাউটার যাচাই করে "
            "সুপারভাইজার সত্যিই আছে কি না — তাই ভুল id-তে ৪০৪ আসে, কোথাও না পৌঁছানো রো তৈরি হয় না।",
        )
        + code(
            "app/routers/requests.py",
            "app/routers/requests.py — full source",
            "app/routers/requests.py — সম্পূর্ণ সোর্স",
        )
        + h3("10. scripts/seed_supabase.py — filling the tables", "১০. scripts/seed_supabase.py — টেবিল ভরা")
        + para(
            "Reads the JSON export, inserts each content table, then re-queries every table and "
            "prints expected vs found. A seeder that does not verify itself is a seeder you "
            "cannot trust.",
            "JSON এক্সপোর্ট পড়ে, প্রতিটি কনটেন্ট টেবিলে ইনসার্ট করে, তারপর আবার প্রতিটি টেবিল "
            "কোয়েরি করে প্রত্যাশিত ও প্রাপ্ত সংখ্যা ছাপে। যে সিডার নিজেকে যাচাই করে না, তাকে "
            "বিশ্বাস করা যায় না।",
        )
        + code(
            "scripts/seed_supabase.py",
            "scripts/seed_supabase.py — full source",
            "scripts/seed_supabase.py — সম্পূর্ণ সোর্স",
        )
    )


# =============================================================================
# 6. API REFERENCE
# =============================================================================


def s_api() -> str:
    return (
        para(
            "All 26 endpoints, grouped by router. <b>Token</b> means the route needs "
            "<code>Authorization: Bearer &lt;access_token&gt;</code>; without it the answer is "
            "401 with a message, never a crash.",
            "সব ২৬টি endpoint, রাউটার অনুযায়ী সাজানো। <b>টোকেন</b> মানে রুটটিতে "
            "<code>Authorization: Bearer &lt;access_token&gt;</code> লাগে; না থাকলে উত্তর ৪০১ "
            "এবং একটি বার্তা — ক্র্যাশ নয়।",
        )
        + h3("Public content — 12 endpoints", "পাবলিক কনটেন্ট — ১২টি endpoint")
        + table(
            [("Method", "মেথড"), ("Path", "পাথ"), ("Token", "টোকেন"), ("Returns", "ফেরত দেয়")],
            [
                ("GET", "/api/content", ("No", "না"), ("Everything in one call — the shape the frontend already used", "সবকিছু এক কলে — ফ্রন্টএন্ডের পুরোনো আকারেই")),
                ("GET", "/api/ideas", ("No", "না"), ("Paginated list; filters q, category, difficulty, type, technology, sort, limit, offset", "পেজিনেটেড লিস্ট; ফিল্টার q, category, difficulty, type, technology, sort, limit, offset")),
                ("GET", "/api/ideas/{id}", ("No", "না"), ("One idea, or 404", "একটি আইডিয়া, নয়তো ৪০৪")),
                ("GET", "/api/supervisors", ("No", "না"), ("Paginated list; filters q, university, expertise, accepting", "পেজিনেটেড লিস্ট; ফিল্টার q, university, expertise, accepting")),
                ("GET", "/api/supervisors/{id}", ("No", "না"), ("One supervisor", "একজন সুপারভাইজার")),
                ("GET", "/api/resources", ("No", "না"), ("Paginated list; filters q, category, type, level", "পেজিনেটেড লিস্ট; ফিল্টার q, category, type, level")),
                ("GET", "/api/resources/{id}", ("No", "না"), ("One resource", "একটি রিসোর্স")),
                ("GET", "/api/publication-guides", ("No", "না"), ("The 7 guides, ordered by position", "৭টি গাইড, position অনুযায়ী")),
                ("GET", "/api/publication-guides/{id}", ("No", "না"), ("One guide by slug", "slug দিয়ে একটি গাইড")),
                ("GET", "/api/roadmap", ("No", "না"), ("The 8 roadmap steps", "৮টি রোডম্যাপ ধাপ")),
                ("GET", "/api/faqs", ("No", "না"), ("The 8 questions as q/a", "৮টি প্রশ্ন q/a আকারে")),
                ("GET", "/api/checklist", ("No", "না"), ("The 8 checklist items", "৮টি চেকলিস্ট আইটেম")),
            ],
        )
        + h3("Accounts — 3 endpoints", "অ্যাকাউন্ট — ৩টি endpoint")
        + table(
            [("Method", "মেথড"), ("Path", "পাথ"), ("Token", "টোকেন"), ("Does", "কাজ")],
            [
                ("POST", "/api/auth/signup", ("No", "না"), ("Creates the auth user + profile, returns a token (201)", "auth ইউজার + প্রোফাইল তৈরি, টোকেন দেয় (২০১)")),
                ("POST", "/api/auth/login", ("No", "না"), ("Checks email/password, returns a fresh token", "ইমেইল/পাসওয়ার্ড যাচাই, নতুন টোকেন দেয়")),
                ("GET", "/api/auth/me", ("Yes", "হ্যাঁ"), ("The logged-in user's profile", "লগইন করা ইউজারের প্রোফাইল")),
            ],
        )
        + h3("My data — 7 endpoints", "আমার ডেটা — ৭টি endpoint")
        + table(
            [("Method", "মেথড"), ("Path", "পাথ"), ("Token", "টোকেন"), ("Does", "কাজ")],
            [
                ("GET", "/api/me/state", ("Yes", "হ্যাঁ"), ("Every saved list + profile + requests, in one call", "সব সেভ-লিস্ট + প্রোফাইল + রিকোয়েস্ট, এক কলে")),
                ("PUT", "/api/me/bookmarks/ideas", ("Yes", "হ্যাঁ"), ("Replaces the saved-idea list", "সেভ করা আইডিয়া লিস্ট বদলায়")),
                ("PUT", "/api/me/bookmarks/supervisors", ("Yes", "হ্যাঁ"), ("Replaces the saved-supervisor list", "সেভ করা সুপারভাইজার লিস্ট বদলায়")),
                ("PUT", "/api/me/roadmap", ("Yes", "হ্যাঁ"), ("Replaces the completed-step list", "সম্পন্ন ধাপের লিস্ট বদলায়")),
                ("PUT", "/api/me/read-guides", ("Yes", "হ্যাঁ"), ("Replaces the read-guide list", "পড়া গাইডের লিস্ট বদলায়")),
                ("PUT", "/api/me/checklist", ("Yes", "হ্যাঁ"), ("Replaces the checklist list", "চেকলিস্ট লিস্ট বদলায়")),
                ("PUT", "/api/me/profile", ("Yes", "হ্যাঁ"), ("Updates only the fields you send", "শুধু পাঠানো ফিল্ডগুলো আপডেট করে")),
            ],
        )
        + h3("Connection requests — 3 endpoints", "কানেকশন রিকোয়েস্ট — ৩টি endpoint")
        + table(
            [("Method", "মেথড"), ("Path", "পাথ"), ("Token", "টোকেন"), ("Does", "কাজ")],
            [
                ("POST", "/api/connection-requests", ("Optional", "ঐচ্ছিক"), ("Sends a request; a member's id is attached, a guest's is NULL", "রিকোয়েস্ট পাঠায়; মেম্বারের id যুক্ত হয়, গেস্টের NULL")),
                ("GET", "/api/me/connection-requests", ("Yes", "হ্যাঁ"), ("Lists my requests, newest first", "আমার রিকোয়েস্ট, নতুন আগে")),
                ("DELETE", "/api/me/connection-requests/{supervisorId}", ("Yes", "হ্যাঁ"), ("Withdraws my request to one supervisor", "একজন সুপারভাইজারকে পাঠানো রিকোয়েস্ট প্রত্যাহার")),
            ],
        )
        + h3("Health — 1 endpoint", "হেলথ — ১টি endpoint")
        + table(
            [("Method", "মেথড"), ("Path", "পাথ"), ("Token", "টোকেন"), ("Does", "কাজ")],
            [
                ("GET", "/api/health", ("No", "না"), ("Reports whether the three Supabase settings are present", "তিনটি Supabase সেটিং আছে কি না জানায়")),
            ],
        )
        + h3("Try them without writing code", "কোড না লিখেই চেষ্টা")
        + para(
            "FastAPI generates an interactive page at <code>/docs</code> from the Python "
            "signatures. Click any endpoint → <i>Try it out</i> → <i>Execute</i>. For "
            "protected routes, first call <code>/api/auth/login</code>, copy "
            "<code>accessToken</code>, and paste it into the <b>Authorize</b> button.",
            "FastAPI Python সিগনেচার থেকে <code>/docs</code>-এ একটি ইন্টার‍্যাকটিভ পেজ বানায়। "
            "যেকোনো endpoint-এ ক্লিক → <i>Try it out</i> → <i>Execute</i>। প্রোটেক্টেড "
            "রুটের জন্য আগে <code>/api/auth/login</code> কল করে <code>accessToken</code> "
            "কপি করুন, তারপর <b>Authorize</b> বোতামে পেস্ট করুন।",
        )
        + h3("curl examples", "curl উদাহরণ")
        + snippet(
            """# 1. Public content, no token needed
curl http://127.0.0.1:8000/api/content

# 2. Sign up (returns accessToken + user)
curl -X POST http://127.0.0.1:8000/api/auth/signup `
  -H "Content-Type: application/json" `
  -d '{"name":"Test Student","email":"test@example.com","password":"Passw0rd!"}'

# 3. Read everything saved by that student
curl http://127.0.0.1:8000/api/me/state `
  -H "Authorization: Bearer PASTE_TOKEN_HERE"

# 4. Replace the bookmark list with two ideas
curl -X PUT http://127.0.0.1:8000/api/me/bookmarks/ideas `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer PASTE_TOKEN_HERE" `
  -d '{"ideaIds":[1,2]}'

# 5. Send a connection request as a guest (no Authorization header)
curl -X POST http://127.0.0.1:8000/api/connection-requests `
  -H "Content-Type: application/json" `
  -d '{"supervisorId":1,"name":"Guest","email":"g@example.com","topic":"Bangla OCR","message":"Hello"}'
""",
            "PowerShell uses a backtick (`) to continue a line; bash uses a backslash",
            "PowerShell-এ লাইন চালু রাখতে ব্যাকটিক (`), bash-এ ব্যাকস্ল্যাশ",
        )
        + note(
            "Every error answer is JSON with a single <code>detail</code> string, because "
            "<code>api.js</code> reads that field and shows it in a toast. Validation errors are "
            "the one exception: FastAPI returns 422 with a list of field problems.",
            "প্রতিটি এরর উত্তর JSON, একটি <code>detail</code> স্ট্রিংসহ — কারণ "
            "<code>api.js</code> সেই ফিল্ড পড়ে টোস্টে দেখায়। একমাত্র ব্যতিক্রম ভ্যালিডেশন "
            "এরর: FastAPI ৪২২ ফেরত দেয় ফিল্ড-সমস্যার তালিকাসহ।",
        )
    )


# =============================================================================
# 7. AUTHENTICATION
# =============================================================================


def s_auth() -> str:
    return (
        para(
            "Passwords are the one thing this project never touches. We send them to Supabase "
            "Auth, which hashes them with bcrypt and keeps them in its own schema. Our "
            "database has no password column at all.",
            "পাসওয়ার্ড হলো একমাত্র জিনিস যা এই প্রজেক্ট কখনো স্পর্শ করে না। আমরা সেটি Supabase "
            "Auth-এ পাঠাই, যা bcrypt দিয়ে হ্যাশ করে নিজের স্কিমায় রাখে। আমাদের ডেটাবেসে "
            "পাসওয়ার্ডের কোনো কলামই নেই।",
        )
        + h3("Sign-up: three steps that must all succeed", "সাইন-আপ: তিনটি ধাপ, সবগুলো সফল হতে হবে")
        + pre(
            """
POST /api/auth/signup
        |
        1. admin.auth.admin.create_user({ email, password, email_confirm: True })
             |
             +-- fails if the email is already used  -> 409 Conflict
        |
        2. insert into profiles { id, name, email, university, ... }
             |
             +-- if this fails, step 1 is undone      -> 500 + no orphan account
        |
        3. auth.sign_in_with_password({ email, password })
             |
             +-- returns session.access_token
        |
        --> 201 { accessToken, user }
"""
        )
        + bullets(
            [
                (
                    "<b>Why the admin API?</b> A normal Supabase sign-up sends a confirmation email. Without an email sender configured, that account could never log in — so <code>email_confirm=True</code> marks the address confirmed immediately and the demo always works.",
                    "<b>কেন admin API?</b> সাধারণ Supabase সাইন-আপ একটি কনফার্মেশন ইমেইল পাঠায়। ইমেইল সেন্ডার না থাকলে সেই অ্যাকাউন্ট কখনো লগইন করতে পারত না — তাই <code>email_confirm=True</code> ঠিকানা সাথে সাথে কনফার্মড করে, ডেমো সবসময় কাজ করে।",
                ),
                (
                    "<b>Why a separate profile table?</b> <code>auth.users</code> belongs to Supabase and holds email/password. Our fields (university, department, student_id, interest) are application data, so they live in <code>public.profiles</code> with the same uuid as primary key.",
                    "<b>কেন আলাদা প্রোফাইল টেবিল?</b> <code>auth.users</code> Supabase-এর, সেখানে ইমেইল/পাসওয়ার্ড থাকে। আমাদের ফিল্ড (বিশ্ববিদ্যালয়, ডিপার্টমেন্ট, স্টুডেন্ট আইডি, আগ্রহ) অ্যাপ্লিকেশনের ডেটা, তাই সেগুলো <code>public.profiles</code>-এ, একই uuid প্রাইমারি কীসহ।",
                ),
                (
                    "<b>Rollback:</b> if the profile insert fails, <code>delete_user</code> removes the auth user, so the system never contains a login without a profile.",
                    "<b>রোলব্যাক:</b> প্রোফাইল ইনসার্ট ব্যর্থ হলে <code>delete_user</code> auth ইউজার মুছে দেয়, তাই সিস্টেমে প্রোফাইলহীন লগইন কখনো থাকে না।",
                ),
            ]
        )
        + snippet(
            """# ---- Step 1: create the authentication record ------------------------
created = admin.auth.admin.create_user(
    {
        "email": email,
        "password": payload.password,
        "email_confirm": True,
        "user_metadata": {"name": payload.name},
    }
)

# ---- Step 2: create the public profile row ---------------------------
admin.table("profiles").insert(profile_row).execute()

# ---- Step 3: log the new user in ------------------------------------
session_result = get_auth_client().auth.sign_in_with_password(
    {"email": email, "password": payload.password}
)""",
            "The three steps in app/routers/auth.py",
            "app/routers/auth.py-এর তিনটি ধাপ",
        )
        + h3("Login and the error message that hides information", "লগইন ও তথ্য গোপন করা এরর বার্তা")
        + para(
            "A wrong password and an unknown email return the <b>same</b> 401 message: "
            "<i>Incorrect email or password.</i> If the messages differed, anyone could use "
            "the login form to discover which students have accounts.",
            "ভুল পাসওয়ার্ড আর অজানা ইমেইল <b>একই</b> ৪০১ বার্তা দেয়: <i>Incorrect email or "
            "password.</i> বার্তা আলাদা হলে যে কেউ লগইন ফর্ম দিয়ে জেনে ফেলত কোন শিক্ষার্থীর "
            "অ্যাকাউন্ট আছে।",
        )
        + snippet(
            """except Exception:
    # We deliberately do not say whether the email or the password was
    # wrong: that would let an attacker discover registered addresses.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )""",
            "One message for both mistakes — and the test asserts they are identical",
            "দুই ভুলের জন্য একই বার্তা — আর টেস্ট নিশ্চিত করে দুটি হুবহু এক",
        )
        + h3("The token on every protected request", "প্রতিটি প্রোটেক্টেড রিকোয়েস্টে টোকেন")
        + steps_list(
            [
                (
                    "The browser stores the token in <code>localStorage.tb_token</code> and the public profile in <code>localStorage.tb_user</code>.",
                    "ব্রাউজার টোকেন রাখে <code>localStorage.tb_token</code>-এ আর পাবলিক প্রোফাইল <code>localStorage.tb_user</code>-এ।",
                ),
                (
                    "<code>api.js</code> adds <code>Authorization: Bearer &lt;token&gt;</code> to every protected call.",
                    "<code>api.js</code> প্রতিটি প্রোটেক্টেড কলে <code>Authorization: Bearer &lt;token&gt;</code> যোগ করে।",
                ),
                (
                    "<code>get_current_user</code> splits the header, rejects anything that is not exactly <code>Bearer …</code>, and asks Supabase to verify the token.",
                    "<code>get_current_user</code> হেডার ভাগ করে, <code>Bearer …</code> ছাড়া সব বাতিল করে, আর Supabase-কে টোকেন যাচাই করতে বলে।",
                ),
                (
                    "Supabase answers with the user id, which the router uses to filter every query: <code>.eq(\"user_id\", current_user[\"id\"])</code>. A user can therefore never read someone else's rows, even if they send another id.",
                    "Supabase ইউজার id ফেরত দেয়, যা দিয়ে রাউটার প্রতিটি কোয়েরি ফিল্টার করে: <code>.eq(\"user_id\", current_user[\"id\"])</code>। তাই কেউ অন্য id পাঠালেও অন্যের রো পড়তে পারে না।",
                ),
            ]
        )
        + note(
            "<b>Important limitation:</b> Supabase access tokens expire after one hour and this "
            "project has no refresh flow. After an hour the API answers 401 with \"Your session "
            "has expired. Please log in again.\" — the website clears the token and shows the "
            "login button. Adding refresh tokens is listed as future work in section 15.",
            "<b>গুরুত্বপূর্ণ সীমাবদ্ধতা:</b> Supabase অ্যাক্সেস টোকেন এক ঘণ্টায় মেয়াদোত্তীর্ণ হয় আর "
            "এই প্রজেক্টে রিফ্রেশ ফ্লো নেই। এক ঘণ্টা পর API ৪০১ দেয় \"Your session has expired. "
            "Please log in again.\" — সাইট টোকেন মুছে দিয়ে লগইন বোতাম দেখায়। রিফ্রেশ টোকেন "
            "যোগ করা section ১৫-এ ভবিষ্যৎ কাজ হিসেবে আছে।",
            "warn",
        )
    )


# =============================================================================
# 8. SAVED DATA: BROWSER <-> DATABASE
# =============================================================================


def s_sync() -> str:
    return (
        para(
            "This is the part that makes the site feel instant while still being durable. "
            "The rule is: <b>write locally first, then send the whole list to the API</b>. "
            "The screen never waits for the network, and the database is corrected a moment "
            "later.",
            "এই অংশটাই সাইটকে সাথে সাথে সাড়া দেওয়ানোর সাথে সাথে টেকসই করে। নিয়ম হলো: "
            "<b>আগে লোকালি লেখো, তারপর পুরো লিস্ট API-তে পাঠাও</b>। স্ক্রিন কখনো নেটওয়ার্কের "
            "জন্য অপেক্ষা করে না, আর ডেটাবেস কিছুক্ষণ পরে ঠিক হয়ে যায়।",
        )
        + h3("Which key talks to which endpoint", "কোন কী কোন endpoint-এ যায়")
        + table(
            [("localStorage key", "localStorage কী"), ("Endpoint", "endpoint"), ("Database column", "ডেটাবেস কলাম")],
            [
                ("tb_bookmarks", "PUT /api/me/bookmarks/ideas", "idea_bookmarks.idea_id"),
                ("tb_savedSupervisors", "PUT /api/me/bookmarks/supervisors", "saved_supervisors.supervisor_id"),
                ("tb_roadmap", "PUT /api/me/roadmap", "roadmap_progress.step_id"),
                ("tb_readGuides", "PUT /api/me/read-guides", "read_guides.guide_id"),
                ("tb_checklist", "PUT /api/me/checklist", "checklist_progress.item_id"),
                ("tb_connectRequests", "POST / DELETE /api/connection-requests", "connection_requests (whole row)"),
                ("tb_token", ("Sent as the Authorization header", "Authorization হেডার হিসেবে যায়"), ("—", "—")),
                ("tb_user", ("Shown in the navbar and prefilled in forms", "নেভবারে দেখানো ও ফর্মে প্রি-ফিল"), ("—", "—")),
            ],
        )
        + h3("Why the whole list, not one item at a time?", "কেন পুরো লিস্ট, একবারে একটি নয়?")
        + para(
            "Adding and removing an item is two different API calls (POST and DELETE), and "
            "they can arrive out of order. Sending the whole array makes the operation "
            "<b>idempotent</b>: sending <code>[1,2]</code> twice leaves exactly the same two "
            "rows, and the browser array and the table can never drift apart.",
            "আইটেম যোগ ও বাদ দেওয়া দুটি আলাদা API কল (POST ও DELETE), আর সেগুলো উল্টো ক্রমে "
            "পৌঁছাতে পারে। পুরো অ্যারে পাঠালে কাজটি <b>idempotent</b> হয়: <code>[1,2]</code> "
            "দুইবার পাঠালেও ঠিক একই দুটি রো থাকে, আর ব্রাউজার অ্যারে ও টেবিল কখনো আলাদা হয়ে "
            "যেতে পারে না।",
        )
        + h3("The replace algorithm (upsert, then delete the rest)", "রিপ্লেস অ্যালগরিদম (upsert, তারপর বাকিগুলো ডিলিট)")
        + pre(
            """
Browser sends [1, 2]        table currently holds [1, 2, 3]

STEP 1  upsert rows (user_id, 1) and (user_id, 2)
        on conflict (user_id, idea_id) do nothing
        -> table: [1, 2, 3]          (nothing lost yet)

STEP 2  delete from idea_bookmarks
        where user_id = me and idea_id NOT IN (1, 2)
        -> table: [1, 2]             (exactly what the browser has)

If STEP 1 fails (for example idea 99 does not exist), we stop
before STEP 2, so the user still has their old [1, 2, 3].
"""
        )
        + snippet(
            """if ids:
    rows = [{"user_id": user_id, id_column: value} for value in ids]
    try:
        db.table(table).upsert(rows, on_conflict=f"user_id,{id_column}").execute()
    except Exception:
        raise HTTPException(status_code=400, detail="One or more values ... do not exist.")

delete_query = db.table(table).delete().eq("user_id", user_id)
if ids:
    # Keep the rows we just upserted; delete every other row.
    delete_query = delete_query.not_.in_(id_column, ids)
delete_query.execute()""",
            "app/routers/user_state.py — _replace_rows",
            "app/routers/user_state.py — _replace_rows",
        )
        + h3("Coming back: hydrate()", "ফিরে আসা: hydrate()")
        + para(
            "After login, and on every page load when a token exists, <code>api.js</code> "
            "calls <code>GET /api/me/state</code> once. The answer is written into the same "
            "localStorage keys the old code already used — so no feature module needed to "
            "change. This is the call that brought the deleted bookmark lists back from "
            "PostgreSQL during testing.",
            "লগইনের পর, আর টোকেন থাকলে প্রতিটি পেজ লোডে, <code>api.js</code> একবার "
            "<code>GET /api/me/state</code> কল করে। উত্তরটি সেই একই localStorage কী-গুলোতে "
            "লেখা হয় যা পুরোনো কোড আগে থেকেই ব্যবহার করত — তাই কোনো ফিচার মডিউল বদলাতে হয়নি। "
            "এই কলটিই টেস্টের সময় মুছে ফেলা বুকমার্ক লিস্ট PostgreSQL থেকে ফিরিয়ে এনেছিল।",
        )
        + h3("Guests vs members", "গেস্ট বনাম মেম্বার")
        + table(
            [("Action", "কাজ"), ("Guest (no token)", "গেস্ট (টোকেন নেই)"), ("Member (token)", "মেম্বার (টোকেন)")],
            [
                (("Browse all pages", "সব পেজ দেখা"), ("Works", "কাজ করে"), ("Works", "কাজ করে")),
                (("Bookmark / roadmap / checklist", "বুকমার্ক / রোডম্যাপ / চেকলিস্ট"), ("Saved in localStorage only", "শুধু localStorage-এ সেভ"), ("localStorage + PostgreSQL", "localStorage + PostgreSQL")),
                (("Send a connection request", "কানেকশন রিকোয়েস্ট পাঠানো"), ("Stored with user_id = NULL", "user_id = NULL দিয়ে সংরক্ষিত"), ("Stored with user_id set", "user_id দিয়ে সংরক্ষিত")),
                (("See my requests", "আমার রিকোয়েস্ট দেখা"), ("Only in this browser", "শুধু এই ব্রাউজারে"), ("From the database, any device", "ডেটাবেস থেকে, যেকোনো ডিভাইসে")),
                (("Data after clearing storage", "স্টোরেজ মুছলে ডেটা"), ("Lost", "হারায়"), ("Restored on next login", "পরের লগইনে ফিরে আসে")),
            ],
        )
        + note(
            "If the API is down, every <code>saveList</code> call catches the error, logs one "
            "warning, and keeps the local value. The site stays usable instead of showing a "
            "broken screen — which is exactly what happened when the tables did not exist yet.",
            "API ডাউন থাকলে প্রতিটি <code>saveList</code> কল এরর ধরে, একটি ওয়ার্নিং লগ করে, আর "
            "লোকাল মান রেখে দেয়। সাইট ভাঙা স্ক্রিন দেখানোর বদলে ব্যবহারযোগ্য থাকে — টেবিল "
            "তৈরি হওয়ার আগে ঠিক এটাই ঘটেছিল।",
            "good",
        )
        + h3("The complete bridge file", "সম্পূর্ণ ব্রিজ ফাইল")
        + para(
            "486 lines: base-URL detection, a single <code>request()</code> helper, content "
            "loading, the five save functions, auth helpers, and <code>TB.ready</code>.",
            "৪১১ লাইন: বেস-URL শনাক্তকরণ, একটি <code>request()</code> হেল্পার, কনটেন্ট লোড, "
            "পাঁচটি সেভ ফাংশন, auth হেল্পার, আর <code>TB.ready</code>।",
        )
        + code(
            "public/js/api.js",
            "public/js/api.js — full source",
            "public/js/api.js — সম্পূর্ণ সোর্স",
        )
    )


# =============================================================================
# 9. WHAT WE VERIFIED
# =============================================================================


def s_verification() -> str:
    return (
        para(
            "Testing happened at two levels, because they catch different bugs. The HTTP "
            "suite catches wrong status codes, wrong field names and broken SQL. The browser "
            "run catches the things only a real page can reveal: a button that does nothing, "
            "a form that never closes, data that vanishes on reload.",
            "পরীক্ষা দুই স্তরে হয়েছে, কারণ দুটি আলাদা ধরনের বাগ ধরে। HTTP স্যুট ভুল স্টেটাস কোড, "
            "ভুল ফিল্ড-নাম ও ভাঙা SQL ধরে। ব্রাউজার রান ধরে সেগুলো যা শুধু আসল পেজেই ধরা পড়ে: "
            "কোনো কাজ না করা বোতাম, না বন্ধ হওয়া ফর্ম, রিলোডে হারিয়ে যাওয়া ডেটা।",
        )
        + h3("Layer 1 — 57 HTTP assertions, 0 failures", "স্তর ১ — ৫৭টি HTTP assertion, ০টি ব্যর্থ")
        + table(
            [("Group", "ভাগ"), ("Checks", "চেক"), ("Examples", "উদাহরণ")],
            [
                (("Public content", "পাবলিক কনটেন্ট"), "10", ("9 categories, 20 ideas, 12 supervisors, camelCase field names", "৯ ক্যাটেগরি, ২০ আইডিয়া, ১২ সুপারভাইজার, camelCase ফিল্ড")),
                (("Sign-up", "সাইন-আপ"), "7", ("201, token returned, profile saved, /me works, 401 without a token", "২০১, টোকেন, প্রোফাইল সেভ, /me কাজ করে, টোকেন ছাড়া ৪০১")),
                (("Saved lists", "সেভ করা লিস্ট"), "9", ("Five PUTs, returned ids match, partial profile update, blank → NULL", "পাঁচটি PUT, ফেরত id মেলে, আংশিক প্রোফাইল আপডেট, খালি → NULL")),
                (("Full state", "সম্পূর্ণ স্টেট"), "8", ("All five lists + profile in one call, 401 without a token", "পাঁচটি লিস্ট + প্রোফাইল এক কলে, টোকেন ছাড়া ৪০১")),
                (("Connection requests", "কানেকশন রিকোয়েস্ট"), "6", ("Member + guest, list, withdraw, empty afterwards", "মেম্বার + গেস্ট, তালিকা, প্রত্যাহার, পরে খালি")),
                (("Login round trip", "লগইন রাউন্ড ট্রিপ"), "7", ("Fresh token, data still there, wrong password and unknown email give the SAME message, 422 on bad input", "নতুন টোকেন, ডেটা অক্ষত, ভুল পাসওয়ার্ড ও অজানা ইমেইলে একই বার্তা, ভুল ইনপুটে ৪২২")),
                (("Direct table reads", "সরাসরি টেবিল পড়া"), "7", ("Service-role read of profiles, bookmarks, roadmap, checklist, guest request", "service-role দিয়ে profiles, bookmarks, roadmap, checklist, গেস্ট রিকোয়েস্ট পড়া")),
            ],
        )
        + note(
            "Two of my own assertions failed on the first run and both were <b>test</b> bugs, not "
            "app bugs: I used the wrong bundle key (<code>journalChecklistItems</code> instead of "
            "<code>journalChecklist</code>) and hard-coded an error message the app had worded "
            "differently. The app was right; the test was wrong.",
            "প্রথম রানে আমার নিজের দুটি assertion ব্যর্থ হয়েছিল, দুটোই <b>টেস্টের</b> বাগ — অ্যাপের নয়: "
            "ভুল বান্ডল কী ব্যবহার করেছিলাম (<code>journalChecklistItems</code> বদলে "
            "<code>journalChecklist</code>) আর অ্যাপের ভিন্ন ভাষায় লেখা এরর বার্তা হার্ডকোড করেছিলাম। "
            "অ্যাপ ঠিক ছিল, টেস্ট ভুল ছিল।",
        )
        + h3("Layer 2 — the browser run", "স্তর ২ — ব্রাউজার রান")
        + table(
            [("Flow", "ফ্লো"), ("What was done", "কী করা হলো"), ("Evidence", "প্রমাণ")],
            [
                (("Home page", "হোম পেজ"), ("Opened with the API running", "API চালু রেখে খোলা"), ("9 categories, 20 ideas, 12 supervisors, 8 steps, 8 FAQs, <b>zero console warnings</b> = database, not the fallback", "৯ ক্যাটেগরি, ২০ আইডিয়া, ১২ সুপারভাইজার, ৮ ধাপ, ৮ FAQ, <b>শূন্য কনসোল ওয়ার্নিং</b> = ডেটাবেস, ফলব্যাক নয়")),
                (("Sign-up", "সাইন-আপ"), ("Real modal form, real submit", "আসল মোডাল ফর্ম, আসল সাবমিট"), ("Toast \"Profile created successfully.\", 856-char token, row in profiles", "টোস্ট \"Profile created successfully.\", ৮৫৬ অক্ষরের টোকেন, profiles-এ রো")),
                (("Saving", "সেভ করা"), ("Bookmark, roadmap step, checklist tick", "বুকমার্ক, রোডম্যাপ ধাপ, চেকলিস্ট টিক"), ("Rows in idea_bookmarks [1], roadmap_progress [1], checklist_progress [\"q1\"]; \"13% Complete\"", "idea_bookmarks [1], roadmap_progress [1], checklist_progress [\"q1\"]-এ রো; \"13% Complete\"")),
                (("Server restore", "সার্ভার থেকে ফেরা"), ("Deleted the three localStorage lists, then reloaded", "তিনটি localStorage লিস্ট মুছে রিলোড"), ("All three came back as [1], [1], [\"q1\"] — from PostgreSQL", "তিনটিই [1], [1], [\"q1\"] হিসেবে ফিরে এল — PostgreSQL থেকে")),
                (("Logout", "লগআউট"), ("Real navbar logout button", "আসল নেভবার লগআউট বোতাম"), ("Token null, every list [], tb_user cleared", "টোকেন null, প্রতিটি লিস্ট [], tb_user খালি")),
                (("Login", "লগইন"), ("Real login form", "আসল লগইন ফর্ম"), ("Token + all three lists restored, toast \"Welcome back, Browser.\"", "টোকেন + তিনটি লিস্ট ফিরে এল, টোস্ট \"Welcome back, Browser.\"")),
                (("Connection request", "কানেকশন রিকোয়েস্ট"), ("Profile modal → Connect → Send", "প্রোফাইল মোডাল → Connect → Send"), ("Row with user_id set and status = pending", "user_id ভরা ও status = pending রো")),
                (("Guest request", "গেস্ট রিকোয়েস্ট"), ("POST with no Authorization header", "Authorization হেডার ছাড়া POST"), ("201, stored with user_id = NULL", "২০১, user_id = NULL দিয়ে সংরক্ষিত")),
            ],
        )
        + h3("The server log is proof too", "সার্ভার লগও প্রমাণ")
        + snippet(
            """POST /auth/v1/admin/users                       200 OK
POST /rest/v1/profiles                          201 Created
POST /auth/v1/token?grant_type=password         200 OK
GET  /rest/v1/idea_bookmarks?user_id=eq...      200 OK
POST /rest/v1/idea_bookmarks?on_conflict=...     201 Created
DELETE /rest/v1/idea_bookmarks?user_id=eq...&idea_id=not.in.(1)   200 OK
POST /rest/v1/connection_requests?on_conflict=... 201 Created
GET  /api/me/state                              200 OK""",
            "Uvicorn's log during the browser run (trimmed)",
            "ব্রাউজার রানের সময় Uvicorn-এর লগ (সংক্ষিপ্ত)",
        )
        + h3("Reproduce everything", "সবকিছু আবার চালানো")
        + cmd(
            r".\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
            "\n"
            r"python -m http.server 8417 --directory public"
            "\n"
            "# then open http://127.0.0.1:8417/index.html"
            "\n"
            "# API docs: http://127.0.0.1:8000/docs"
        )
        + note(
            "All test accounts (<code>e2e-*</code>, <code>browser-*</code>) and guest requests were "
            "deleted afterwards; the seven user tables are back to 0 rows and the 150 content rows "
            "are untouched. A clean database is easier to demo from.",
            "সব টেস্ট অ্যাকাউন্ট (<code>e2e-*</code>, <code>browser-*</code>) ও গেস্ট রিকোয়েস্ট পরে "
            "মুছে ফেলা হয়েছে; সাতটি user টেবিল আবার ০ রো, আর ১৫০টি কনটেন্ট রো অক্ষত। পরিষ্কার "
            "ডেটাবেস থেকে ডেমো দেখানো সহজ।",
            "good",
        )
    )


# =============================================================================
# 10. BUGS FOUND AND FIXED
# =============================================================================


def s_bugs() -> str:
    return (
        para(
            "Three real bugs surfaced only because the code ran against a real database and a "
            "real browser. Each one is a good viva story: the symptom, the cause, the fix, and "
            "the lesson.",
            "তিনটি আসল বাগ ধরা পড়েছিল শুধু এই কারণে যে কোড আসল ডেটাবেস ও আসল ব্রাউজারে চলেছিল। "
            "প্রতিটিই ভাইভার জন্য ভালো গল্প: উপসর্গ, কারণ, সমাধান আর শিক্ষা।",
        )
        + h3("Bug 1 — the FAQ page broke the whole content call", "বাগ ১ — FAQ পেজ পুরো কনটেন্ট কল ভেঙে দিয়েছিল")
        + table(
            [("", ""), ("Detail", "বিস্তারিত")],
            [
                (("Symptom", "উপসর্গ"), ("<code>GET /api/content</code> returned <b>500 Internal Server Error</b>, so every page fell back to the bundled data.", "<code>GET /api/content</code> <b>৫০০ Internal Server Error</b> দিত, তাই প্রতিটি পেজ বান্ডল করা ডেটায় ফিরে যেত।")),
                (("Cause", "কারণ"), ("The PostgreSQL columns are <code>question</code> / <code>answer</code>, but the Pydantic model declared <code>q</code> / <code>a</code> — the shape the JavaScript renders. Pydantic raised a validation error.", "PostgreSQL কলাম <code>question</code> / <code>answer</code>, কিন্তু Pydantic মডেলে ছিল <code>q</code> / <code>a</code> — যা JavaScript রেন্ডার করে। Pydantic ভ্যালিডেশন এরর দিয়েছিল।")),
                (("Fix", "সমাধান"), ("<code>validation_alias=AliasChoices(\"question\", \"q\")</code>: read either name, still emit <code>q</code> and <code>a</code>. <b>Zero frontend changes.</b>", "<code>validation_alias=AliasChoices(\"question\", \"q\")</code>: যেকোনো নাম পড়ে, আউটপুটে <code>q</code> ও <code>a</code>-ই দেয়। <b>ফ্রন্টএন্ডে শূন্য পরিবর্তন।</b>")),
                (("Lesson", "শিক্ষা"), ("A database column name and a JSON field name are two different contracts. Aliases let one model satisfy both.", "ডেটাবেস কলামের নাম আর JSON ফিল্ডের নাম দুটি আলাদা চুক্তি। alias দিয়ে একটি মডেলই দুটো মানে।")),
            ],
        )
        + snippet(
            """class Faq(CamelModel):
    \"\"\"
    The browser renders `q` and `a`, but the PostgreSQL columns are
    `question` and `answer`. validation_alias lets Pydantic *read* the
    database row while the JSON we send back still uses `q` / `a`.
    \"\"\"
    q: str = Field(validation_alias=AliasChoices("question", "q"))
    a: str = Field(validation_alias=AliasChoices("answer", "a"))""",
            "The fix in app/schemas.py",
            "app/schemas.py-তে সমাধান",
        )
        + h3("Bug 2 — a database error looked like a crash", "বাগ ২ — ডেটাবেস এরর ক্র্যাশের মতো দেখাচ্ছিল")
        + para(
            "Before the tables existed, a query raised <code>postgrest.exceptions.APIError</code>. "
            "FastAPI had no handler for it, so the browser received a bare "
            "<i>Internal Server Error</i> with no explanation — the worst kind of error message.",
            "টেবিল তৈরি হওয়ার আগে কোয়েরি <code>postgrest.exceptions.APIError</code> ছুড়ত। FastAPI-তে "
            "তার হ্যান্ডলার ছিল না, তাই ব্রাউজার কোনো ব্যাখ্যা ছাড়া শুধু "
            "<i>Internal Server Error</i> পেত — সবচেয়ে খারাপ ধরনের এরর বার্তা।",
        )
        + snippet(
            """@app.exception_handler(APIError)
async def database_error_handler(request: Request, exc: APIError) -> JSONResponse:
    code = exc.code or ""
    message = exc.message or "Unknown database error."

    if code == "PGRST205":
        detail = ("The database tables do not exist yet. Open the Supabase dashboard, "
                  "go to SQL Editor, and run the file sql/001_create_tables.sql ...")
    elif code == "42501":
        detail = ("The database refused this query for permission reasons. Check that "
                  "SUPABASE_SERVICE_ROLE_KEY holds the secret key, not the publishable one.")
    else:
        detail = f"Database error ({code or 'unknown'}): {message}"

    return JSONResponse(status_code=503, content={"detail": detail})""",
            "The handler added in app/main.py",
            "app/main.py-তে যোগ করা হ্যান্ডলার",
        )
        + bullets(
            [
                (
                    "<b>503, not 500:</b> the service is temporarily unable to do its job, which is exactly what 503 means.",
                    "<b>৫০৩, ৫০০ নয়:</b> সার্ভিস সাময়িকভাবে কাজ করতে পারছে না — ৫০৩-এর অর্থ ঠিক তাই।",
                ),
                (
                    "<b>Read the attributes:</b> <code>APIError</code> exposes <code>.code</code>, <code>.message</code>, <code>.hint</code>, <code>.details</code>. Its <code>args[0]</code> is only a string and cannot be parsed reliably.",
                    "<b>অ্যাট্রিবিউট পড়া:</b> <code>APIError</code>-তে <code>.code</code>, <code>.message</code>, <code>.hint</code>, <code>.details</code> আছে। এর <code>args[0]</code> শুধু স্ট্রিং, নির্ভরযোগ্যভাবে পার্স করা যায় না।",
                ),
                (
                    "<b>The frontend benefits for free:</b> <code>api.js</code> already displays <code>detail</code>, so the student sees the instruction instead of a blank failure.",
                    "<b>ফ্রন্টএন্ড বিনা পরিশ্রমে উপকৃত:</b> <code>api.js</code> আগেই <code>detail</code> দেখায়, তাই শিক্ষার্থী ফাঁকা ব্যর্থতার বদলে করণীয় দেখে।",
                ),
            ]
        )
        + h3("Bug 3 — asking a logged-in student to retype their own email", "বাগ ৩ — লগইন করা শিক্ষার্থীকে নিজের ইমেইল আবার লিখতে বলা")
        + para(
            "This one is a UX bug that only became visible once real accounts existed. The "
            "connection form was always empty, even though the site already knew the student's "
            "name and email.",
            "এটি একটি UX বাগ, যা আসল অ্যাকাউন্ট তৈরি হওয়ার পরেই চোখে পড়ে। সাইট শিক্ষার্থীর নাম ও "
            "ইমেইল জানা সত্ত্বেও কানেকশন ফর্ম সবসময় খালি থাকত।",
        )
        + snippet(
            """// If the visitor is logged in, prefill their own name and email.
const me = TB.state.get('tb_user', null) || {};
const nameValue = me.name ? ' value="' + TB.esc(me.name) + '"' : '';
const emailValue = me.email ? ' value="' + TB.esc(me.email) + '"' : '';""",
            "The fix in public/js/supervisors.js",
            "public/js/supervisors.js-এ সমাধান",
        )
        + note(
            "Note the <code>TB.esc()</code> call: the value comes from a database, so it is "
            "HTML-escaped before being placed in an attribute. Trusting stored data is how "
            "stored XSS happens.",
            "<code>TB.esc()</code> লক্ষ্য করুন: মানটি ডেটাবেস থেকে আসে, তাই অ্যাট্রিবিউটে বসানোর আগে "
            "HTML-escape করা হয়েছে। সংরক্ষিত ডেটাকে বিশ্বাস করাই stored XSS-এর কারণ।",
            "warn",
        )
    )


# =============================================================================
# 11. DEPLOY TO VERCEL
# =============================================================================


def s_deploy() -> str:
    return (
        para(
            "One Vercel project hosts both halves: the six HTML pages at the domain "
            "root and the Python API under <code>/api</code>. Because they share a "
            "domain, the browser's <code>fetch('/api/...')</code> needs no absolute URL "
            "and production has no CORS problem at all.",
            "একটি Vercel প্রজেক্টেই দুই অংশ থাকে: ছয়টি HTML পেজ ডোমেইনের রুটে আর Python "
            "API <code>/api</code>-এর নিচে। একই ডোমেইন হওয়ায় ব্রাউজারের "
            "<code>fetch('/api/...')</code>-এ সম্পূর্ণ URL লাগে না, আর প্রোডাকশনে CORS "
            "সমস্যাই থাকে না।",
        )
        + pre(
            """
GitHub repo  ──push──>  Vercel build  ──>  https://<project>.vercel.app
                                          |
                        +-----------------+------------------+
                        |                                    |
                   public/  ->  /                     /api/*  ->  app/main.py
                   (static files, served                (one Python function)
                    from the CDN)                                 |
                                                                  v
                                                        Supabase (Auth + PostgreSQL)
"""
        )
        + h3("One-time setup — six steps", "একবারের সেটআপ — ছয় ধাপ")
        + steps_list(
            [
                (
                    "Push the project to GitHub. This is already done: the repo is <code>nasifsajib/thesisbridge-bd</code>, branch <code>main</code>, and <code>.env</code> is gitignored so no secret is uploaded.",
                    "প্রজেক্ট GitHub-এ পুশ করুন। এটি হয়ে গেছে: রিপো <code>nasifsajib/thesisbridge-bd</code>, ব্রাঞ্চ <code>main</code>, আর <code>.env</code> gitignore-এ আছে তাই কোনো সিক্রেট আপলোড হয় না।",
                ),
                (
                    "Go to <b>vercel.com/new</b> and choose <b>Import Git Repository</b>. Authorise GitHub the first time and pick the repo.",
                    "<b>vercel.com/new</b>-এ যান এবং <b>Import Git Repository</b> বেছে নিন। প্রথমবার GitHub অনুমোদন করে রিপোটি বেছে নিন।",
                ),
                (
                    "On the import screen the <b>Framework Preset</b> must be <b>FastAPI</b>. Vercel detects it from <code>fastapi</code> in <code>requirements.txt</code> plus the <code>app</code> object in <code>app/main.py</code>, and <code>vercel.json</code> pins the same value so the dropdown cannot change it. Leave <b>Root Directory</b> on <code>./</code> and both build fields empty: there is nothing to compile.",
                    "ইমপোর্ট স্ক্রিনে <b>Framework Preset</b> অবশ্যই <b>FastAPI</b> হতে হবে। Vercel এটি শনাক্ত করে <code>requirements.txt</code>-এর <code>fastapi</code> আর <code>app/main.py</code>-এর <code>app</code> অবজেক্ট থেকে, এবং <code>vercel.json</code>-ও একই মান পিন করে রাখে তাই ড্রপডাউন তা বদলাতে পারে না। <b>Root Directory</b> <code>./</code>-এ আর দুটি build ঘর খালি রাখুন: কম্পাইল করার কিছু নেই।",
                ),
                (
                    "Open <b>Environment Variables</b> and add the three Supabase values from the table below. Tick all three environments (Production, Preview, Development) so a preview deploy also works.",
                    "<b>Environment Variables</b> খুলে নিচের টেবিল থেকে তিনটি Supabase মান যোগ করুন। তিনটি environment-ই (Production, Preview, Development) টিক দিন, যাতে প্রিভিউ ডিপ্লয়ও কাজ করে।",
                ),
                (
                    "Press <b>Deploy</b>. The first build takes one to three minutes: Vercel installs <code>requirements.txt</code>, bundles the function, and uploads the static files.",
                    "<b>Deploy</b> চাপুন। প্রথম বিল্ডে এক থেকে তিন মিনিট লাগে: Vercel <code>requirements.txt</code> ইনস্টল করে, ফাংশন বান্ডল করে, আর স্ট্যাটিক ফাইল আপলোড করে।",
                ),
                (
                    "Verify with the four checks in the next heading before showing anyone the link.",
                    "কাউকে লিংক দেখানোর আগে পরের শিরোনামের চারটি যাচাই সম্পন্ন করুন।",
                ),
            ]
        )
        + h3("The same thing from the terminal (optional)", "টার্মিনাল থেকে একই কাজ (ঐচ্ছিক)")
        + para(
            "The dashboard is enough, but the CLI is faster for repeat deploys. It asks "
            "the same questions once and remembers them in a hidden <code>.vercel</code> "
            "folder.",
            "ড্যাশবোর্ডই যথেষ্ট, তবে বারবার ডিপ্লয়ের জন্য CLI দ্রুত। এটি একবার একই প্রশ্ন "
            "করে আর একটি লুকানো <code>.vercel</code> ফোল্ডারে মনে রাখে।",
        )
        + cmd(
            "npm install -g vercel\n"
            "vercel login\n"
            "vercel            # first deploy, answers a few questions\n"
            "vercel --prod     # promote to the public production URL\n"
            "\n"
            "# add the secrets without retyping them into a web form\n"
            "vercel env add SUPABASE_URL production\n"
            "vercel env add SUPABASE_ANON_KEY production\n"
            "vercel env add SUPABASE_SERVICE_ROLE_KEY production"
        )
        + h3("What Vercel actually reads", "Vercel আসলে কী পড়ে")
        + table(
            [("File", "ফাইল"), ("Why it matters", "কেন দরকার")],
            [
                (
                    "<code>app/main.py</code>",
                    ("The application entry point. Vercel looks for a FastAPI object named <code>app</code> in <code>app/main.py</code>, <code>app.py</code>, <code>index.py</code>, <code>server.py</code>, <code>main.py</code>, <code>wsgi.py</code> or <code>asgi.py</code> — and <code>app/main.py</code> is one of those names. Every <code>/api/...</code> request reaches this single function.", "অ্যাপ্লিকেশনের প্রবেশদ্বার। Vercel <code>app/main.py</code>, <code>app.py</code>, <code>index.py</code>, <code>server.py</code>, <code>main.py</code>, <code>wsgi.py</code> বা <code>asgi.py</code>-তে <code>app</code> নামের FastAPI অবজেক্ট খোঁজে — আর <code>app/main.py</code> তাদের একটি। প্রতিটি <code>/api/...</code> রিকোয়েস্ট এই একটিমাত্র ফাংশনে পৌঁছায়।"),
                ),
                (
                    "<code>vercel.json</code>",
                    ("Pins the framework to <code>fastapi</code> and raises the function timeout to 30 seconds. The default is 10, which is tight for a cold start plus a Supabase round trip.", "ফ্রেমওয়ার্ক <code>fastapi</code>-তে পিন করে আর ফাংশনের সময়সীমা ৩০ সেকেন্ড করে। ডিফল্ট ১০, যা কোল্ড স্টার্ট যোগ Supabase রাউন্ড ট্রিপের জন্য কম।"),
                ),
                (
                    "<code>requirements.txt</code>",
                    ("Vercel installs these five packages into the function. No pinning beyond <code>&gt;=</code>, so a rebuild picks up patch fixes.", "Vercel এই পাঁচটি প্যাকেজ ফাংশনে ইনস্টল করে। <code>&gt;=</code>-এর বাইরে পিন নেই, তাই রিবিল্ডে প্যাচ ঠিকানা পায়।"),
                ),
                (
                    "<code>.python-version</code>",
                    ("Pins Python 3.14, which Vercel offers (3.12 is the default, 3.13 and 3.14 are available). If a version were ever unsupported, Vercel would quietly use 3.12 instead of failing the build.", "Python ৩.১৪ পিন করে, যা Vercel দেয় (ডিফল্ট ৩.১২, ৩.১৩ ও ৩.১৪ পাওয়া যায়)। কোনো ভার্সন অসমর্থিত হলে Vercel বিল্ড ব্যর্থ না করে চুপচাপ ৩.১২ ব্যবহার করত।"),
                ),
                (
                    "<code>public/</code>",
                    ("Served at the domain root with no build step. Relative links such as <code>css/style.css</code> keep working because the folder structure is unchanged.", "কোনো বিল্ড ছাড়াই ডোমেইন রুটে সার্ভ হয়। <code>css/style.css</code>-এর মতো রিলেটিভ লিংক অপরিবর্তিত কাজ করে, কারণ ফোল্ডার-গঠন বদলায়নি।"),
                ),
            ],
        )
        + h3("The settings files", "সেটিংস ফাইল")
        + code(
            "vercel.json",
            "vercel.json — framework, entry point and timeout in one place",
            "vercel.json — ফ্রেমওয়ার্ক, প্রবেশদ্বার ও সময়সীমা এক জায়গায়",
        )
        + code(
            "requirements.txt",
            "requirements.txt — installed on every deploy",
            "requirements.txt — প্রতিটি ডিপ্লয়ে ইনস্টল হয়",
        )
        + h3("The four environment variables", "চারটি environment variable")
        + table(
            [("Name", "নাম"), ("Value comes from", "মান কোথা থেকে"), ("Secret?", "সিক্রেট?")],
            [
                (
                    "SUPABASE_URL",
                    ("Supabase → Project Settings → API → Project URL", "Supabase → Project Settings → API → Project URL"),
                    ("No. It is public.", "না। এটি পাবলিক।"),
                ),
                (
                    "SUPABASE_ANON_KEY",
                    ("The publishable key (<code>sb_publishable_…</code>). Used only for Auth calls.", "publishable কী (<code>sb_publishable_…</code>)। শুধু Auth কলে ব্যবহৃত।"),
                    ("No. It is designed for browsers.", "না। এটি ব্রাউজারের জন্যই তৈরি।"),
                ),
                (
                    "SUPABASE_SERVICE_ROLE_KEY",
                    ("The secret key (<code>sb_secret_…</code>). Used for table reads and writes.", "secret কী (<code>sb_secret_…</code>)। টেবিল পড়া-লেখায় ব্যবহৃত।"),
                    ("<b>Yes.</b> It bypasses Row Level Security.", "<b>হ্যাঁ।</b> এটি Row Level Security বাইপাস করে।"),
                ),
                (
                    "CORS_ORIGINS",
                    ("Optional. Only needed if a page is hosted on another domain; leave it unset when the site and API share one domain.", "ঐচ্ছিক। শুধু পেজ অন্য ডোমেইনে থাকলে দরকার; সাইট ও API এক ডোমেইনে হলে খালি রাখুন।"),
                    ("No.", "না।"),
                ),
            ],
        )
        + note(
            "Never paste the secret key into HTML, JavaScript, a screenshot or this document. "
            "It belongs in exactly two places: your local <code>.env</code> and Vercel's "
            "Environment Variables screen. If it ever leaks, rotate it in Supabase immediately.",
            "সিক্রেট কী কখনো HTML, JavaScript, স্ক্রিনশট বা এই ডকুমেন্টে পেস্ট করবেন না। এটি থাকা "
            "উচিত ঠিক দুই জায়গায়: আপনার লোকাল <code>.env</code> আর Vercel-এর Environment "
            "Variables স্ক্রিনে। কখনো ফাঁস হলে সাথে সাথে Supabase-এ রোটেট করুন।",
            "warn",
        )
        + h3("How to know the deploy worked", "ডিপ্লয় কাজ করেছে কীভাবে বুঝবেন")
        + table(
            [("Check", "যাচাই"), ("Open", "খুলুন"), ("Expected answer", "প্রত্যাশিত উত্তর")],
            [
                (
                    ("1. Function is alive", "১. ফাংশন সচল"),
                    "<code>/api/health</code>",
                    ("<code>{\"status\":\"ok\",\"databaseConfigured\":true,\"missingSettings\":[]}</code>", "<code>{\"status\":\"ok\",\"databaseConfigured\":true,\"missingSettings\":[]}</code>"),
                ),
                (
                    ("2. Static site is served", "২. স্ট্যাটিক সাইট সার্ভ হচ্ছে"),
                    "<code>/</code>",
                    ("The home page with 20 idea cards, no console warning about the fallback", "হোম পেজে ২০টি আইডিয়া কার্ড, ফলব্যাক নিয়ে কনসোল ওয়ার্নিং নেই"),
                ),
                (
                    ("3. Content comes from PostgreSQL", "৩. কনটেন্ট PostgreSQL থেকে আসছে"),
                    "<code>/api/content</code>",
                    ("JSON with <code>categories</code>, <code>ideas</code>, <code>supervisors</code> and 150 rows in total", "<code>categories</code>, <code>ideas</code>, <code>supervisors</code> সহ JSON, মোট ১৫০ রো"),
                ),
                (
                    ("4. The API documents itself", "৪. API নিজের ডকুমেন্টেশন দেয়"),
                    "<code>/docs</code>",
                    ("Swagger UI listing 26 endpoints, all clickable", "Swagger UI-তে ২৬টি endpoint, সব ক্লিকযোগ্য"),
                ),
            ],
        )
        + note(
            "If check 1 says <code>databaseConfigured: false</code>, the variable names are "
            "misspelled or were added only to Preview. Check the <code>missingSettings</code> "
            "array — it names exactly which one is absent — then redeploy, because values are "
            "read when the function starts.",
            "যাচাই ১ যদি <code>databaseConfigured: false</code> বলে, তবে ভ্যারিয়েবলের নাম ভুল "
            "অথবা শুধু Preview-তে যোগ করা হয়েছে। <code>missingSettings</code> অ্যারে দেখুন — "
            "কোনটি অনুপস্থিত ঠিক তা বলে দেয় — তারপর আবার ডিপ্লয় করুন, কারণ মান ফাংশন চালু "
            "হওয়ার সময় পড়া হয়।",
            "warn",
        )
        + h3("Every update after that", "এর পরের প্রতিটি আপডেট")
        + para(
            "The GitHub integration makes deployment automatic: push to <code>main</code> and "
            "Vercel rebuilds. Every branch and pull request gets its own preview URL, which is "
            "useful for showing a change before it reaches the main link.",
            "GitHub ইন্টিগ্রেশন ডিপ্লয় স্বয়ংক্রিয় করে: <code>main</code>-এ পুশ করলেই Vercel "
            "রিবিল্ড করে। প্রতিটি ব্রাঞ্চ ও pull request নিজের প্রিভিউ URL পায়, যা মূল লিংকে "
            "পৌঁছানোর আগে পরিবর্তন দেখানোর জন্য কাজে লাগে।",
        )
        + cmd(
            "git add .\n"
            "git commit -m \"Describe the change\"\n"
            "git push origin main\n"
            "# Vercel rebuilds automatically; watch it in the dashboard"
        )
        + note(
            "<b>Free-plan facts worth knowing before the viva:</b> a function that has been "
            "idle cold-starts in roughly one second, and a Supabase free project is paused after "
            "about a week of inactivity. Open the site the morning of the demo so both are warm.",
            "<b>ভাইভার আগে জানা দরকারি ফ্রি-প্ল্যান তথ্য:</b> অনেকক্ষণ নিষ্ক্রিয় ফাংশন প্রায় এক "
            "সেকেন্ডে কোল্ড-স্টার্ট হয়, আর Supabase ফ্রি প্রজেক্ট প্রায় এক সপ্তাহ নিষ্ক্রিয় থাকলে "
            "পজ হয়ে যায়। ডেমোর সকালে সাইটটি একবার খুলে নিন, যাতে দুটোই গরম থাকে।",
            "info",
        )
    )


# =============================================================================
# 12. TROUBLESHOOTING
# =============================================================================


def s_troubleshoot() -> str:
    return (
        para(
            "Every entry below is a problem that actually occurred during this build, or the "
            "direct consequence of a decision in it. The pattern is always the same: find the "
            "layer that failed, then read the message that layer produced.",
            "নিচের প্রতিটি এন্ট্রি এই নির্মাণকালে সত্যিই ঘটেছে, অথবা এখানকার কোনো সিদ্ধান্তের "
            "সরাসরি ফল। ধরন সবসময় এক: কোন স্তর ব্যর্থ হয়েছে তা খুঁজুন, তারপর সেই স্তরের দেওয়া "
            "বার্তাটি পড়ুন।",
        )
        + h3("Read an error in three steps", "তিন ধাপে এরর পড়া")
        + steps_list(
            [
                (
                    "<b>Which layer?</b> Browser console = JavaScript and network. Vercel function log = Python. Supabase SQL = database. The same 500 can come from any of the three.",
                    "<b>কোন স্তর?</b> ব্রাউজার কনসোল = JavaScript ও নেটওয়ার্ক। Vercel ফাংশন লগ = Python। Supabase SQL = ডেটাবেস। একই ৫০০ তিনটির যেকোনোটি থেকে আসতে পারে।",
                ),
                (
                    "<b>What is the status code?</b> 401 = identity, 404 = path or missing row, 422 = my JSON did not match the model, 503 = the database is not usable right now.",
                    "<b>স্টেটাস কোড কী?</b> ৪০১ = পরিচয়, ৪০৪ = পাথ বা রো নেই, ৪২২ = আমার JSON মডেলের সাথে মেলেনি, ৫০৩ = ডেটাবেস এখন ব্যবহারযোগ্য নয়।",
                ),
                (
                    "<b>Read <code>detail</code>.</b> Every error answer in this project carries a sentence written for a human. If it says nothing useful, the handler itself is the bug.",
                    "<b><code>detail</code> পড়ুন।</b> এই প্রজেক্টের প্রতিটি এরর উত্তরে মানুষের জন্য লেখা একটি বাক্য থাকে। কিছু কাজের কথা না বললে হ্যান্ডলারটাই বাগ।",
                ),
            ]
        )
        + h3("The table to keep open during the demo", "ডেমোর সময় খোলা রাখার টেবিল")
        + table(
            [("Symptom", "উপসর্গ"), ("Real cause", "আসল কারণ"), ("Fix", "সমাধান")],
            [
                (
                    ("<code>503</code> · <code>PGRST205 — Could not find the table</code>", "<code>৫০৩</code> · <code>PGRST205 — Could not find the table</code>"),
                    ("The schema was never run in this Supabase project, so PostgREST has no tables to expose.", "এই Supabase প্রজেক্টে স্কিমা কখনো চালানো হয়নি, তাই PostgREST-এর কাছে দেখানোর টেবিল নেই।"),
                    ("Paste <code>sql/001_create_tables.sql</code> into the SQL Editor and run it. Then reload.", "SQL Editor-এ <code>sql/001_create_tables.sql</code> পেস্ট করে চালান। তারপর রিলোড।"),
                ),
                (
                    ("<code>503</code> · permission denied (<code>42501</code>)", "<code>৫০৩</code> · permission denied (<code>42501</code>)"),
                    ("<code>SUPABASE_SERVICE_ROLE_KEY</code> holds the publishable key, so Row Level Security blocks the write.", "<code>SUPABASE_SERVICE_ROLE_KEY</code>-এ publishable কী আছে, তাই Row Level Security লেখা আটকায়।"),
                    ("Copy the secret key (<code>sb_secret_…</code>) again, update the variable, redeploy.", "আবার secret কী (<code>sb_secret_…</code>) কপি করুন, ভ্যারিয়েবল আপডেট করুন, রিডিপ্লয় করুন।"),
                ),
                (
                    ("<code>503</code> · <code>databaseConfigured: false</code> on <code>/api/health</code>", "<code>৫০৩</code> · <code>/api/health</code>-এ <code>databaseConfigured: false</code>"),
                    ("One of the three variables is missing, misspelled, or was added only to the Preview environment.", "তিনটি ভ্যারিয়েবলের একটি অনুপস্থিত, বানান ভুল, অথবা শুধু Preview environment-এ যোগ করা।"),
                    ("Read <code>missingSettings</code> in the health answer, fix that name, redeploy.", "হেলথ উত্তরে <code>missingSettings</code> পড়ুন, সেই নাম ঠিক করুন, রিডিপ্লয় করুন।"),
                ),
                (
                    ("<code>401</code> · <i>Your session has expired</i>", "<code>৪০১</code> · <i>Your session has expired</i>"),
                    ("The access token is one hour old. This project deliberately has no refresh flow.", "অ্যাক্সেস টোকেন এক ঘণ্টা পুরোনো। এই প্রজেক্টে ইচ্ছাকৃতভাবে রিফ্রেশ ফ্লো নেই।"),
                    ("Log in again. Section 15 lists refresh tokens as future work.", "আবার লগইন করুন। Section ১৫-এ রিফ্রেশ টোকেন ভবিষ্যৎ কাজ হিসেবে আছে।"),
                ),
                (
                    ("<code>401</code> on a route that should be public", "যে রুট পাবলিক হওয়ার কথা সেখানে <code>৪০১</code>"),
                    ("<code>get_current_user</code> was used instead of <code>get_optional_user</code>, so a missing token is an error instead of a guest.", "<code>get_optional_user</code>-এর বদলে <code>get_current_user</code> ব্যবহার হয়েছে, তাই টোকেন না থাকলে গেস্ট ধরা না হয়ে এরর হয়।"),
                    ("Only the POST connection-request route should use the optional dependency.", "শুধু POST connection-request রুটে ঐচ্ছিক dependency ব্যবহার করা উচিত।"),
                ),
                (
                    ("Browser console: <i>blocked by CORS policy</i>", "ব্রাউজার কনসোল: <i>blocked by CORS policy</i>"),
                    ("The page was opened as <code>file://</code>, or from a different port than the API, and that origin is not allowed.", "পেজটি <code>file://</code> হিসেবে খোলা হয়েছে, বা API-এর ভিন্ন পোর্ট থেকে, আর সেই origin অনুমোদিত নয়।"),
                    ("Serve the site with <code>python -m http.server 8417 --directory public</code>, or add the origin to <code>CORS_ORIGINS</code>.", "<code>python -m http.server 8417 --directory public</code> দিয়ে সার্ভ করুন, বা <code>CORS_ORIGINS</code>-এ origin যোগ করুন।"),
                ),
                (
                    ("Site works but every number is the old bundled data", "সাইট কাজ করে কিন্তু সব সংখ্যা পুরোনো বান্ডল করা ডেটা"),
                    ("<code>api.js</code> could not reach the API and fell back to <code>data.js</code> — by design, so the site never breaks.", "<code>api.js</code> API-তে পৌঁছাতে পারেনি এবং <code>data.js</code>-এ ফিরে গেছে — এটি ইচ্ছাকৃত, যাতে সাইট কখনো না ভাঙে।"),
                    ("Find the one warning in the console, fix that URL/status, reload. The fallback is a symptom, not the disease.", "কনসোলে থাকা একটি ওয়ার্নিং খুঁজুন, সেই URL/স্টেটাস ঠিক করুন, রিলোড। ফলব্যাক উপসর্গ, রোগ নয়।"),
                ),
                (
                    ("<code>422 Unprocessable Entity</code>", "<code>৪২২ Unprocessable Entity</code>"),
                    ("The JSON did not match the Pydantic model — wrong field name, wrong type, or a password shorter than the minimum.", "JSON Pydantic মডেলের সাথে মেলেনি — ভুল ফিল্ড-নাম, ভুল ধরন, বা সর্বনিম্ন দৈর্ঘ্যের চেয়ে ছোট পাসওয়ার্ড।"),
                    ("Open <code>/docs</code>, expand the route, read the schema. The 422 body names the exact field.", "<code>/docs</code> খুলে রুটটি প্রসারিত করে স্কিমা পড়ুন। ৪২২ বডি ঠিক কোন ফিল্ড তা বলে দেয়।"),
                ),
                (
                    ("<code>409</code> · <i>An account with this email already exists</i>", "<code>৪০৯</code> · <i>An account with this email already exists</i>"),
                    ("Supabase Auth refused to create a duplicate user.", "Supabase Auth ডুপ্লিকেট ইউজার তৈরি করতে অস্বীকার করেছে।"),
                    ("Log in instead, or delete the test user in Authentication → Users.", "পরিবর্তে লগইন করুন, বা Authentication → Users-এ টেস্ট ইউজার মুছুন।"),
                ),
                (
                    ("<code>404</code> · <code>{\"detail\":\"Not Found\"}</code> on every <code>/api/...</code>", "প্রতিটি <code>/api/...</code>-এ <code>৪০৪</code> · <code>{\"detail\":\"Not Found\"}</code>"),
                    ("Vercel did not treat the project as a FastAPI app, so no function was created. That happens when <code>app/main.py</code> is not at the repo root, or when the framework was set to <i>Other</i> in the import screen.", "Vercel প্রজেক্টটিকে FastAPI অ্যাপ ধরেনি, তাই কোনো ফাংশন তৈরি হয়নি। এটি ঘটে যখন <code>app/main.py</code> রিপো-রুটে থাকে না, বা ইমপোর্ট স্ক্রিনে ফ্রেমওয়ার্ক <i>Other</i> সেট থাকে।"),
                    ("Confirm <code>app/main.py</code> sits at the root of the repo and that <code>vercel.json</code> says <code>\"framework\": \"fastapi\"</code> with <code>functions</code> keyed <code>app/main.py</code>. Redeploy.", "নিশ্চিত করুন <code>app/main.py</code> রিপোর রুটে আছে এবং <code>vercel.json</code>-এ <code>\"framework\": \"fastapi\"</code> আর <code>functions</code>-এ <code>app/main.py</code> লেখা আছে। রিডিপ্লয় করুন।"),
                ),
                (
                    ("The HTML pages return 404 but <code>/api/health</code> works", "HTML পেজ ৪০৪ কিন্তু <code>/api/health</code> কাজ করে"),
                    ("Vercel is not serving the static folder at the domain root. With the FastAPI preset, a <code>public/</code> directory at the repo root is published to the CDN automatically; anything else is left out of the deployment.", "Vercel স্ট্যাটিক ফোল্ডার ডোমেইন রুটে সার্ভ করছে না। FastAPI প্রিসেটে রিপো-রুটের <code>public/</code> ফোল্ডার স্বয়ংক্রিয়ভাবে CDN-এ যায়; অন্য কিছু ডিপ্লয়মেন্টে বাদ পড়ে।"),
                    ("Check that the folder is named exactly <code>public</code>, at the repo root, with <code>index.html</code> inside it. Redeploy.", "ফোল্ডারের নাম হুবহু <code>public</code>, রিপো-রুটে, ভিতরে <code>index.html</code> — তা যাচাই করে রিডিপ্লয় করুন।"),
                ),
                (
                    ("Build log: <i>ModuleNotFoundError: No module named 'app'</i>", "বিল্ড লগ: <i>ModuleNotFoundError: No module named 'app'</i>"),
                    ("Root Directory points at a subfolder, so the <code>app</code> package is outside the build.", "Root Directory একটি সাবফোল্ডারে, তাই <code>app</code> প্যাকেজ বিল্ডের বাইরে।"),
                    ("Set Root Directory back to <code>./</code>.", "Root Directory আবার <code>./</code> করুন।"),
                ),
                (
                    ("Build log: unknown framework, or the deploy stops before bundling", "বিল্ড লগ: unknown framework, বা বান্ডল হওয়ার আগেই ডিপ্লয় থেমে যায়"),
                    ("The <code>\"framework\"</code> value in <code>vercel.json</code> was edited to something Vercel does not know.", "কেউ <code>vercel.json</code>-এর <code>\"framework\"</code> মান এমন কিছুতে বদলেছে যা Vercel চেনে না।"),
                    ("Restore <code>\"framework\": \"fastapi\"</code>, or delete that line entirely — Vercel detects FastAPI on its own from <code>requirements.txt</code>.", "<code>\"framework\": \"fastapi\"</code> ফিরিয়ে আনুন, অথবা লাইনটি পুরো মুছে দিন — Vercel নিজেই <code>requirements.txt</code> থেকে FastAPI শনাক্ত করে।"),
                ),
                (
                    ("First request takes about a second", "প্রথম রিকোয়েস্টে প্রায় এক সেকেন্ড লাগে"),
                    ("Cold start: the function container was asleep and must boot, import FastAPI and build the Supabase client.", "কোল্ড স্টার্ট: ফাংশন কনটেইনার ঘুমিয়ে ছিল, তাকে জাগতে, FastAPI আমদানি করতে ও Supabase ক্লায়েন্ট বানাতে হয়।"),
                    ("Not a bug. Open the site once before the demo so the container is warm.", "বাগ নয়। ডেমোর আগে একবার সাইট খুলুন, যাতে কনটেইনার গরম থাকে।"),
                ),
                (
                    ("Supabase dashboard says the project is paused", "Supabase ড্যাশবোর্ড বলে প্রজেক্ট পজ করা"),
                    ("Free projects pause after about a week with no queries.", "ফ্রি প্রজেক্ট প্রায় এক সপ্তাহ কোনো কোয়েরি না হলে পজ হয়।"),
                    ("Press <i>Restore project</i> and wait about a minute. Then reload the site.", "<i>Restore project</i> চেপে প্রায় এক মিনিট অপেক্ষা করুন। তারপর সাইট রিলোড করুন।"),
                ),
            ],
        )
        + h3("Where the logs are", "লগ কোথায়")
        + table(
            [("Layer", "স্তর"), ("Where to look", "কোথায় দেখবেন")],
            [
                (("Browser", "ব্রাউজার"), ("DevTools → Console for warnings, → Network for the failing request and its status", "DevTools → Console-এ ওয়ার্নিং, → Network-এ ব্যর্থ রিকোয়েস্ট ও স্টেটাস")),
                (("Vercel", "Vercel"), ("Deployments → the deployment → Functions → Logs (or <code>vercel logs &lt;url&gt;</code>)", "Deployments → ডিপ্লয়মেন্ট → Functions → Logs (বা <code>vercel logs &lt;url&gt;</code>)")),
                (("Supabase", "Supabase"), ("Logs → API / Postgres, and the SQL Editor for a direct query", "Logs → API / Postgres, আর সরাসরি কোয়েরির জন্য SQL Editor")),
                (("Local", "লোকাল"), ("The Uvicorn terminal — it prints every request and every traceback", "Uvicorn টার্মিনাল — প্রতিটি রিকোয়েস্ট ও ট্রেসব্যাক ছাপে")),
            ],
        )
        + note(
            "A useful habit: reproduce the bug locally first. If it appears locally, the fix is "
            "in the code. If it appears only on Vercel, the difference is an environment variable, "
            "a missing file, or the free-plan cold start — in other words, configuration.",
            "কাজের অভ্যাস: আগে লোকালি বাগটি reproduce করুন। লোকালে দেখা গেলে সমাধান কোডে। শুধু "
            "Vercel-এ দেখা গেলে পার্থক্য হলো একটি environment variable, একটি অনুপস্থিত ফাইল, "
            "অথবা ফ্রি-প্ল্যান কোল্ড স্টার্ট — অর্থাৎ কনফিগারেশন।",
            "good",
        )
    )


# =============================================================================
# 13. VIVA QUESTIONS
# =============================================================================


def s_viva() -> str:
    return (
        para(
            "The questions an examiner is most likely to ask, with answers short enough to "
            "say out loud and specific enough to be checked against the code. Where the honest "
            "answer is \"this is a limitation\", it says so.",
            "পরীক্ষক সবচেয়ে বেশি যে প্রশ্নগুলো করতে পারেন, উত্তরগুলো এত ছোট যে মুখে বলা যায় "
            "আর এত নির্দিষ্ট যে কোডের সাথে মিলিয়ে দেখা যায়। যেখানে সৎ উত্তর \"এটি একটি "
            "সীমাবদ্ধতা\", সেখানে তা-ই লেখা আছে।",
        )
        + h3("Architecture and choices", "আর্কিটেকচার ও সিদ্ধান্ত")
        + qa(
            [
                (
                    "Why FastAPI instead of Flask or Django?",
                    "Flask বা Django-র বদলে FastAPI কেন?",
                    "Three reasons. It is async, so a request waiting on Supabase does not block the others. It validates every request with Pydantic automatically, so bad JSON is rejected before my code runs. And it generates the <code>/docs</code> page from the code, which gave me a testable API on day one. Django would have brought an admin panel and an ORM I did not need for 26 endpoints.",
                    "তিনটি কারণ। এটি async, তাই Supabase-এর জন্য অপেক্ষারত একটি রিকোয়েস্ট বাকিগুলো আটকায় না। এটি Pydantic দিয়ে প্রতিটি রিকোয়েস্ট স্বয়ংক্রিয়ভাবে যাচাই করে, তাই আমার কোড চলার আগেই ভুল JSON বাতিল হয়। আর এটি কোড থেকে <code>/docs</code> পেজ বানায়, যা প্রথম দিনেই পরীক্ষণযোগ্য API দিয়েছে। Django একটি admin panel ও ORM আনত, যা ২৬টি endpoint-এর জন্য দরকার ছিল না।",
                ),
                (
                    "Why is the API a separate application instead of PHP inside the HTML?",
                    "HTML-এর ভিতরে PHP না করে API আলাদা অ্যাপ্লিকেশন কেন?",
                    "Because the secret database key must never reach the browser. With a server-side API the key lives in an environment variable and the browser only ever holds a short-lived user token. Separation also means the six static pages did not have to be rewritten — only <code>api.js</code> was added.",
                    "কারণ সিক্রেট ডেটাবেস কী কখনো ব্রাউজারে পৌঁছানো যাবে না। সার্ভার-সাইড API-তে কী থাকে environment variable-এ, আর ব্রাউজার শুধু স্বল্পমেয়াদি ইউজার টোকেন ধরে। আলাদা রাখায় ছয়টি স্ট্যাটিক পেজ নতুন করে লিখতে হয়নি — শুধু <code>api.js</code> যোগ হয়েছে।",
                ),
                (
                    "Why two Supabase clients?",
                    "দুটি Supabase ক্লায়েন্ট কেন?",
                    "They have different permissions. Auth endpoints are designed for the publishable key, so signing in uses that. Table reads and writes need to bypass Row Level Security, which only the secret key can do — so those use the second client, and it never leaves the server.",
                    "দুটির অনুমতি আলাদা। Auth endpoint publishable কী-এর জন্য তৈরি, তাই সাইন-ইন সেটি ব্যবহার করে। টেবিল পড়া-লেখায় Row Level Security বাইপাস দরকার, যা শুধু secret কী পারে — তাই সেগুলো দ্বিতীয় ক্লায়েন্ট ব্যবহার করে, আর এটি কখনো সার্ভার ছাড়ে না।",
                ),
                (
                    "Why not query Supabase directly from JavaScript?",
                    "JavaScript থেকে সরাসরি Supabase-এ কোয়েরি কেন নয়?",
                    "You can, and for a read-only site it would be shorter. But then all business rules — the sign-up transaction, the list replacement, the guest-versus-member rule — would either live in the browser, where they can be edited, or in RLS policies, which are harder to explain. And the secret key could not be used at all.",
                    "করা যায়, আর শুধু পড়ার সাইটে তা ছোট হতো। কিন্তু তখন সব ব্যবসায়িক নিয়ম — সাইন-আপ লেনদেন, লিস্ট রিপ্লেস, গেস্ট-বনাম-মেম্বার নিয়ম — হয় ব্রাউজারে থাকত, যেখানে সম্পাদনা করা যায়, নয়তো RLS পলিসিতে, যা ব্যাখ্যা করা কঠিন। আর secret কী ব্যবহারই করা যেত না।",
                ),
                (
                    "Why is <code>public/</code> a separate folder from <code>app/</code>?",
                    "<code>app/</code> থেকে <code>public/</code> আলাদা ফোল্ডার কেন?",
                    "It is a security boundary made visible in the file tree. Everything in <code>public/</code> is downloadable by anyone; nothing in <code>app/</code> is. Keeping the two apart means a Python file can never be served by accident.",
                    "এটি ফাইল-গাছে দৃশ্যমান একটি নিরাপত্তা-সীমানা। <code>public/</code>-এর সবকিছু যে কেউ নামাতে পারে; <code>app/</code>-এর কিছুই নয়। আলাদা রাখায় কোনো Python ফাইল ভুলে সার্ভ হওয়ার সুযোগ নেই।",
                ),
            ]
        )
        + h3("Database and data modelling", "ডেটাবেস ও ডেটা মডেলিং")
        + qa(
            [
                (
                    "What is Row Level Security and why does it matter if your API uses the secret key?",
                    "Row Level Security কী, আর আপনার API secret কী ব্যবহার করলে এটি কেন দরকার?",
                    "RLS makes PostgreSQL filter rows per user by policy. My API bypasses it by design, so its value is defence in depth: if the publishable key leaks — and that key is in every browser by nature — an attacker calling Supabase directly still cannot read another student's bookmarks. The policies are the second lock.",
                    "RLS পলিসি অনুযায়ী PostgreSQL-কে প্রতি ইউজারে রো ফিল্টার করায়। আমার API ইচ্ছাকৃতভাবে এটি বাইপাস করে, তাই এর মূল্য defence in depth: publishable কী ফাঁস হলে — আর সেই কী স্বভাবতই প্রতিটি ব্রাউজারে থাকে — সরাসরি Supabase-কে কল করা আক্রমণকারী তবুও অন্য শিক্ষার্থীর বুকমার্ক পড়তে পারে না। পলিসিগুলো দ্বিতীয় তালা।",
                ),
                (
                    "Why a separate <code>profiles</code> table instead of adding columns to the auth table?",
                    "auth টেবিলে কলাম যোগ না করে আলাদা <code>profiles</code> টেবিল কেন?",
                    "<code>auth.users</code> belongs to Supabase and holds credentials. Application fields such as university and department are mine, so they live in <code>public.profiles</code> with the same uuid as the primary key — a one-to-one relationship. Upgrading Supabase then cannot overwrite my data.",
                    "<code>auth.users</code> Supabase-এর, সেখানে ক্রেডেনশিয়াল থাকে। বিশ্ববিদ্যালয় ও ডিপার্টমেন্টের মতো অ্যাপ্লিকেশন ফিল্ড আমার, তাই সেগুলো <code>public.profiles</code>-এ, একই uuid প্রাইমারি কীসহ — এক-থেকে-এক সম্পর্ক। তখন Supabase আপগ্রেড আমার ডেটা মুছে দিতে পারে না।",
                ),
                (
                    "Why do the bookmark tables have no foreign key to <code>research_ideas</code>?",
                    "বুকমার্ক টেবিলে <code>research_ideas</code>-এর foreign key নেই কেন?",
                    "A deliberate trade-off for the migration. The integer ids were reused from the old <code>data.js</code> so bookmarks saved before the backend existed still resolve to the right idea. The API validates the id on write and returns 400 for an unknown one, which covers the same ground without a hard constraint.",
                    "মাইগ্রেশনের জন্য ইচ্ছাকৃত সমঝোতা। পূর্ণসংখ্যা id পুরোনো <code>data.js</code> থেকে পুনর্ব্যবহৃত, যাতে ব্যাকএন্ডের আগে সেভ করা বুকমার্কও সঠিক আইডিয়ায় মেলে। API লেখার সময় id যাচাই করে আর অজানা id-তে ৪০০ দেয়, যা কঠোর constrain ছাড়াই একই কাজ করে।",
                ),
                (
                    "Why is <code>unique (user_id, idea_id)</code> important?",
                    "কেন <code>unique (user_id, idea_id)</code> গুরুত্বপূর্ণ?",
                    "It is what makes <code>upsert</code> possible: PostgreSQL needs a unique constraint to know which row to update instead of inserting a duplicate. It also makes a double-click harmless — the second insert becomes a no-op.",
                    "এটাই <code>upsert</code> সম্ভব করে: কোন রো আপডেট করতে হবে তা জানতে PostgreSQL-এর unique constraint দরকার, নইলে ডুপ্লিকেট ইনসার্ট হয়। এটি দুইবার ক্লিককেও নিরীহ করে — দ্বিতীয় ইনসার্ট কিছুই করে না।",
                ),
                (
                    "What is an index and where did you use one?",
                    "ইনডেক্স কী, আর কোথায় ব্যবহার করেছেন?",
                    "An index is a lookup structure that lets PostgreSQL find rows without scanning the table. Every user table is indexed on <code>user_id</code>, because every query filters by it, and content tables are indexed on the columns used for sorting and filtering.",
                    "ইনডেক্স হলো একটি খোঁজার গঠন, যা PostgreSQL-কে টেবিল স্ক্যান না করে রো খুঁজতে দেয়। প্রতিটি user টেবিল <code>user_id</code>-তে ইনডেক্সড, কারণ প্রতিটি কোয়েরি তা দিয়ে ফিল্টার করে, আর কনটেন্ট টেবিল সাজানো ও ফিল্টারে ব্যবহৃত কলামে ইনডেক্সড।",
                ),
                (
                    "Why no ORM such as SQLAlchemy?",
                    "SQLAlchemy-র মতো ORM কেন নয়?",
                    "The Supabase client already speaks PostgREST, so a second abstraction layer would add code without removing any. Every query in this project is short and readable as it is, and there are no complex joins to manage.",
                    "Supabase ক্লায়েন্ট আগেই PostgREST-এর সাথে কথা বলে, তাই দ্বিতীয় abstraction স্তর কোড বাড়াত কিন্তু কিছু কমাত না। এখানে প্রতিটি কোয়েরি ছোট ও পাঠযোগ্য, আর সামলানোর মতো জটিল join নেই।",
                ),
            ]
        )
        + h3("Security", "নিরাপত্তা")
        + qa(
            [
                (
                    "How are passwords stored?",
                    "পাসওয়ার্ড কীভাবে সংরক্ষিত হয়?",
                    "They are never stored by my code. They go to Supabase Auth, which hashes them with bcrypt inside its own schema. My database has no password column, so a dump of my tables contains no credential at all.",
                    "আমার কোড সেগুলো কখনো সংরক্ষণ করে না। সেগুলো Supabase Auth-এ যায়, যা নিজের স্কিমায় bcrypt দিয়ে হ্যাশ করে। আমার ডেটাবেসে পাসওয়ার্ড কলামই নেই, তাই আমার টেবিলের ডাম্পে কোনো ক্রেডেনশিয়ালই থাকে না।",
                ),
                (
                    "What is the difference between authentication and authorisation here?",
                    "এখানে authentication ও authorisation-এর পার্থক্য কী?",
                    "Authentication is proving who you are — login, and the token on each request. Authorisation is what you may touch — every query is filtered by <code>.eq(\"user_id\", current_user[\"id\"])</code>, so even a valid token cannot read another user's rows.",
                    "Authentication হলো আপনি কে তা প্রমাণ করা — লগইন, আর প্রতিটি রিকোয়েস্টে টোকেন। Authorisation হলো আপনি কী স্পর্শ করতে পারেন — প্রতিটি কোয়েরি <code>.eq(\"user_id\", current_user[\"id\"])</code> দিয়ে ফিল্টার করা, তাই বৈধ টোকেনও অন্যের রো পড়তে পারে না।",
                ),
                (
                    "Why does a wrong password and an unknown email give the same message?",
                    "ভুল পাসওয়ার্ড ও অজানা ইমেইল একই বার্তা কেন দেয়?",
                    "To prevent account enumeration. Different messages would turn the login form into a tool for discovering which students have accounts. The test suite asserts that the two responses are byte-identical.",
                    "অ্যাকাউন্ট enumeration আটকাতে। আলাদা বার্তা লগইন ফর্মকে এমন হাতিয়ার বানাত যা দিয়ে জানা যেত কোন শিক্ষার্থীর অ্যাকাউন্ট আছে। টেস্ট স্যুট নিশ্চিত করে দুটি উত্তর হুবহু এক।",
                ),
                (
                    "Is the search box safe from SQL injection?",
                    "সার্চ বক্স কি SQL injection থেকে নিরাপদ?",
                    "Yes, for two reasons. Values are sent to PostgREST as parameters, not concatenated into SQL, so quoting cannot break out. On top of that, <code>_safe_search</code> strips comma, parenthesis and asterisk, because those characters are PostgREST filter syntax rather than SQL.",
                    "হ্যাঁ, দুই কারণে। মানগুলো PostgREST-এ প্যারামিটার হিসেবে যায়, SQL-এ জোড়া লাগে না, তাই কোট দিয়ে বেরোনো যায় না। তার উপর <code>_safe_search</code> কমা, বন্ধনী ও অ্যাস্টেরিস্ক সরায়, কারণ সেগুলো SQL নয়, PostgREST ফিল্টার সিনট্যাক্স।",
                ),
                (
                    "Where could stored XSS come from, and what did you do about it?",
                    "Stored XSS কোথা থেকে আসতে পারত, আর আপনি কী করেছেন?",
                    "A student's name is stored in the database and rendered into HTML. Every such value passes through <code>TB.esc()</code> before it enters the page, including the prefilled form attributes. Trusting stored data is exactly how stored XSS happens.",
                    "শিক্ষার্থীর নাম ডেটাবেসে থাকে এবং HTML-এ রেন্ডার হয়। এমন প্রতিটি মান পেজে ঢোকার আগে <code>TB.esc()</code>-এর মধ্য দিয়ে যায়, প্রি-ফিল করা ফর্ম অ্যাট্রিবিউটসহ। সংরক্ষিত ডেটাকে বিশ্বাস করাই stored XSS-এর কারণ।",
                ),
                (
                    "Is there rate limiting?",
                    "rate limiting আছে কি?",
                    "No, and that is a real gap. A public sign-up endpoint without a limit can be abused. The fix is a small counter in PostgreSQL or Vercel's firewall rules; it is listed as future work rather than pretended to exist.",
                    "না, এবং এটি সত্যিকারের ঘাটতি। সীমা ছাড়া পাবলিক সাইন-আপ endpoint-এর অপব্যবহার সম্ভব। সমাধান PostgreSQL-এ ছোট কাউন্টার বা Vercel-এর firewall নিয়ম; এটি থাকার ভান না করে ভবিষ্যৎ কাজ হিসেবে লেখা আছে।",
                ),
            ]
        )
        + h3("API design", "API ডিজাইন")
        + qa(
            [
                (
                    "Why send the whole list instead of adding one bookmark at a time?",
                    "একবারে একটি বুকমার্ক যোগ না করে পুরো লিস্ট কেন পাঠানো?",
                    "Because add and remove are two different calls that can arrive out of order, and then the browser and the database disagree. Sending the whole array makes the operation idempotent: the same request twice leaves the same rows.",
                    "কারণ যোগ ও বাদ দেওয়া দুটি আলাদা কল, যা উল্টো ক্রমে পৌঁছাতে পারে, তখন ব্রাউজার ও ডেটাবেস একমত থাকে না। পুরো অ্যারে পাঠালে কাজটি idempotent হয়: একই রিকোয়েস্ট দুইবার পাঠালেও একই রো থাকে।",
                ),
                (
                    "What does idempotent mean, and why does <code>PUT</code> fit?",
                    "idempotent মানে কী, আর <code>PUT</code> কেন মানানসই?",
                    "Idempotent means repeating the request produces the same final state. <code>PUT</code> means \"make this resource look like this\", which is exactly the replace-the-list semantics. <code>POST</code> would imply \"add another one\", which is not what the button does.",
                    "Idempotent মানে রিকোয়েস্ট পুনরাবৃত্তি করলে চূড়ান্ত অবস্থা একই থাকে। <code>PUT</code> মানে \"এই রিসোর্সকে এমন করো\", যা হুবহু লিস্ট-রিপ্লেস অর্থ। <code>POST</code> বোঝাত \"আরেকটি যোগ করো\", যা বোতামটি করে না।",
                ),
                (
                    "Why does the API use camelCase when PostgreSQL uses snake_case?",
                    "PostgreSQL snake_case ব্যবহার করলে API camelCase কেন?",
                    "The database follows SQL convention and the JavaScript follows its own. Instead of rewriting the six pages, <code>CamelModel</code> converts on the way out, and <code>populate_by_name</code> lets the same model read database rows. One class serves both sides.",
                    "ডেটাবেস SQL রীতি মানে আর JavaScript নিজের রীতি। ছয়টি পেজ নতুন করে লেখার বদলে <code>CamelModel</code> বেরোনোর পথে রূপান্তর করে, আর <code>populate_by_name</code> একই মডেলকে ডেটাবেস রো পড়তে দেয়। একটি ক্লাসই দুই পক্ষের কাজ করে।",
                ),
                (
                    "Why 503 for a database error instead of 500?",
                    "ডেটাবেস এররে ৫০০-এর বদলে ৫০৩ কেন?",
                    "500 means the code itself is broken. 503 means the service is temporarily unable to do its job, which is what a missing table or a refused permission is. The distinction tells the reader whether to fix the code or the configuration.",
                    "৫০০ মানে কোড নিজেই ভাঙা। ৫০৩ মানে সার্ভিস সাময়িকভাবে কাজ করতে পারছে না, আর অনুপস্থিত টেবিল বা প্রত্যাখ্যাত অনুমতি ঠিক তাই। এই পার্থক্য পাঠককে বলে কোড না কনফিগারেশন ঠিক করতে হবে।",
                ),
                (
                    "What is a dependency in FastAPI?",
                    "FastAPI-তে dependency কী?",
                    "A function FastAPI runs before the route and injects the result into it. <code>get_current_user</code> reads the header, verifies the token and returns the user — so no route repeats that code, and a route that declares it cannot accidentally run unauthenticated.",
                    "এমন ফাংশন যা FastAPI রুটের আগে চালায় এবং ফলাফল রুটে ইনজেক্ট করে। <code>get_current_user</code> হেডার পড়ে, টোকেন যাচাই করে ইউজার ফেরত দেয় — তাই কোনো রুট সেই কোড পুনরাবৃত্তি করে না, আর যে রুট এটি ঘোষণা করে সে ভুলে অনুমতিহীন চলতেও পারে না।",
                ),
                (
                    "Why <code>AliasChoices</code> on the FAQ model?",
                    "FAQ মডেলে <code>AliasChoices</code> কেন?",
                    "The database columns are <code>question</code> and <code>answer</code>, but the frontend has always rendered <code>q</code> and <code>a</code>. Aliases let Pydantic read either name while still emitting the shorter one, so a schema change needed zero frontend edits. That was a real bug I hit.",
                    "ডেটাবেস কলাম <code>question</code> ও <code>answer</code>, কিন্তু ফ্রন্টএন্ড সবসময় <code>q</code> ও <code>a</code> রেন্ডার করত। alias Pydantic-কে যেকোনো নাম পড়তে দেয় আর ছোটটিই দেয়, তাই স্কিমা বদলে ফ্রন্টএন্ডে শূন্য এডিট লাগে। এটি আমার ধরা পড়া আসল বাগ।",
                ),
            ]
        )
        + h3("Deployment and production", "ডিপ্লয় ও প্রোডাকশন")
        + qa(
            [
                (
                    "What is a serverless function, and what is a cold start?",
                    "serverless function কী, আর cold start কী?",
                    "A function that runs in a container Vercel starts only when a request arrives and stops when it is idle. A cold start is the first request after that idle period, which has to boot Python, import FastAPI and build the Supabase client — about a second here.",
                    "এমন ফাংশন যা Vercel-এর কনটেইনারে চলে, রিকোয়েস্ট এলে চালু হয় আর নিষ্ক্রিয় হলে বন্ধ হয়। cold start হলো সেই নিষ্ক্রিয়তার পর প্রথম রিকোয়েস্ট, যাকে Python চালু করতে, FastAPI আমদানি করতে ও Supabase ক্লায়েন্ট বানাতে হয় — এখানে প্রায় এক সেকেন্ড।",
                ),
                (
                    "Why is there no CORS problem in production but one locally?",
                    "প্রোডাকশনে CORS সমস্যা নেই কিন্তু লোকালে কেন?",
                    "In production the pages and the API share one origin, so the browser never makes a cross-origin request. Locally the page is on port 8417 and the API on 8000, which is cross-origin, so <code>CORS_ORIGINS</code> has to allow the page's address.",
                    "প্রোডাকশনে পেজ ও API একই origin-এ, তাই ব্রাউজার কখনো cross-origin রিকোয়েস্ট করে না। লোকালে পেজ ৮৪১৭ পোর্টে আর API ৮০০০-এ, যা cross-origin, তাই <code>CORS_ORIGINS</code>-কে পেজের ঠিকানা অনুমোদন করতে হয়।",
                ),
                (
                    "How do you prove the site is reading PostgreSQL and not the bundled file?",
                    "সাইটটি বান্ডল করা ফাইলের বদলে PostgreSQL পড়ছে কীভাবে প্রমাণ করবেন?",
                    "Three ways. Delete a row in the Table Editor and reload — the card disappears. Clear <code>localStorage</code>, reload, and the bookmarks come back from <code>GET /api/me/state</code>. Or watch the Network tab and see the <code>/api/content</code> response carrying the rows.",
                    "তিন উপায়। Table Editor-এ একটি রো মুছে রিলোড করুন — কার্ডটি চলে যায়। <code>localStorage</code> মুছে রিলোড করুন, বুকমার্ক <code>GET /api/me/state</code> থেকে ফিরে আসে। অথবা Network ট্যাব দেখুন, <code>/api/content</code> উত্তর রো বহন করছে।",
                ),
                (
                    "What happens if Vercel and Supabase are in different regions?",
                    "Vercel ও Supabase আলাদা রিজিয়নে থাকলে কী হয়?",
                    "Every query pays the round-trip twice — function to database and back — so latency adds up. The fix is to create the Supabase project in the region closest to the function; this project keeps both as close as the free plan allows.",
                    "প্রতিটি কোয়েরি রাউন্ড-ট্রিপ দুইবার দেয় — ফাংশন থেকে ডেটাবেস ও ফিরে — তাই লেটেন্সি যোগ হয়। সমাধান হলো ফাংশনের নিকটতম রিজিয়নে Supabase প্রজেক্ট বানানো; এই প্রজেক্টে ফ্রি প্ল্যান যতটা দেয়, দুটোই কাছাকাছি রাখা হয়েছে।",
                ),
                (
                    "What would you change for 10,000 users?",
                    "১০,০০০ ইউজারের জন্য কী বদলাতেন?",
                    "Five things. Use a connection pooler because serverless functions open many short connections. Add composite indexes matching the real filters. Cache content reads, which change rarely. Add rate limiting on sign-up and search. And move the list writes to a queue if they ever became heavy. The API shapes would not change.",
                    "পাঁচটি জিনিস। connection pooler ব্যবহার করতাম, কারণ serverless ফাংশন অনেক ছোট সংযোগ খোলে। বাস্তব ফিল্টারের সাথে মেলা composite index যোগ করতাম। কম বদলানো কনটেন্ট পড়া ক্যাশ করতাম। সাইন-আপ ও সার্চে rate limiting যোগ করতাম। আর লিস্ট-লেখা ভারী হলে queue-তে সরাতাম। API-এর আকার বদলাত না।",
                ),
                (
                    "How would you add email notification when a request arrives?",
                    "রিকোয়েস্ট এলে ইমেইল নোটিফিকেশন কীভাবে যোগ করবেন?",
                    "The row is already stored, so the insert is the event. Add a call after a successful insert to an email provider's API, inside a try block so a mail failure never loses the request. A background task or a Supabase database webhook would be the cleaner version at scale.",
                    "রো আগেই সংরক্ষিত হয়, তাই insert-ই ঘটনা। সফল insert-এর পরে ইমেইল প্রোভাইডারের API-তে একটি কল যোগ করতাম, try ব্লকে, যাতে মেইল ব্যর্থ হলেও রিকোয়েস্ট না হারায়। বড় পরিসরে background task বা Supabase database webhook আরও পরিচ্ছন্ন।",
                ),
            ]
        )
        + h3("Testing and honest limitations", "পরীক্ষা ও সৎ সীমাবদ্ধতা")
        + qa(
            [
                (
                    "How was this tested?",
                    "এটি কীভাবে পরীক্ষা করা হয়েছে?",
                    "In two layers. A 57-assertion HTTP suite ran against the real Supabase project and checked status codes, field names, the five lists, both request paths and the login round trip. Then a real browser run used the actual forms, including deleting local storage to prove the server restore. Zero failures at the end.",
                    "দুই স্তরে। ৫৭টি assertion-এর HTTP স্যুট আসল Supabase প্রজেক্টের বিরুদ্ধে চলে স্টেটাস কোড, ফিল্ড-নাম, পাঁচটি লিস্ট, দুই রিকোয়েস্ট পথ ও লগইন রাউন্ড ট্রিপ যাচাই করেছে। তারপর আসল ব্রাউজার রানে আসল ফর্ম ব্যবহার হয়েছে, লোকাল স্টোরেজ মুছে সার্ভার-রিস্টোর প্রমাণসহ। শেষে শূন্য ব্যর্থতা।",
                ),
                (
                    "What is the biggest weakness of this system?",
                    "এই সিস্টেমের সবচেয়ে বড় দুর্বলতা কী?",
                    "The token has no refresh flow, so a session ends after one hour and the user must log in again. It is a deliberate scope decision, not an oversight, and the honest fix is to store the refresh token and call Supabase's refresh endpoint before expiry.",
                    "টোকেনে রিফ্রেশ ফ্লো নেই, তাই এক ঘণ্টা পর সেশন শেষ হয় আর ইউজারকে আবার লগইন করতে হয়। এটি ইচ্ছাকৃত পরিসীমা-সিদ্ধান্ত, অবহেলা নয়, আর সৎ সমাধান হলো রিফ্রেশ টোকেন রাখা এবং মেয়াদ শেষের আগে Supabase-এর refresh endpoint কল করা।",
                ),
                (
                    "Two tabs change the same list. What happens?",
                    "দুই ট্যাব একই লিস্ট বদলায়। কী হয়?",
                    "Last write wins. Each tab sends its whole list, so the later request replaces the earlier one. For one student on two devices that is acceptable; a version number per list would turn it into a conflict the UI could report.",
                    "শেষ লেখাটি জেতে। প্রতিটি ট্যাব পুরো লিস্ট পাঠায়, তাই পরের রিকোয়েস্ট আগেরটি বদলে দেয়। দুই ডিভাইসে একজন শিক্ষার্থীর জন্য এটি গ্রহণযোগ্য; প্রতি লিস্টে একটি version নম্বর থাকলে এটি এমন সংঘাত হতো যা UI জানাতে পারত।",
                ),
                (
                    "If you had one more week, what would you build first?",
                    "আরেক সপ্তাহ পেলে প্রথমে কী বানাতেন?",
                    "Refresh tokens, then rate limiting, then password reset. Those three make the account system complete and safe. Email notification for requests and a small admin screen for supervisors would be next.",
                    "রিফ্রেশ টোকেন, তারপর rate limiting, তারপর পাসওয়ার্ড রিসেট। এই তিনটি অ্যাকাউন্ট সিস্টেমকে পূর্ণ ও নিরাপদ করে। এরপর রিকোয়েস্টের ইমেইল নোটিফিকেশন ও সুপারভাইজারদের জন্য ছোট admin স্ক্রিন।",
                ),
            ]
        )
    )


# =============================================================================
# 14. GLOSSARY
# =============================================================================


def s_glossary() -> str:
    return (
        para(
            "Every term used above, in one sentence each. Bengali is included because the "
            "explanation is more useful in the language you think in.",
            "উপরে ব্যবহৃত প্রতিটি পরিভাষা, প্রতিটি এক বাক্যে। বাংলা রাখা হয়েছে কারণ যে ভাষায় "
            "ভাবেন, সেই ভাষায় ব্যাখ্যা বেশি কাজে দেয়।",
        )
        + h3("Web and API", "ওয়েব ও API")
        + table(
            [("Term", "পরিভাষা"), ("Meaning", "অর্থ")],
            [
                (("API", "API"), ("A contract that lets one program ask another for data or an action, without knowing how it works inside.", "এমন চুক্তি যা এক প্রোগ্রামকে অন্য প্রোগ্রামের কাছে ডেটা বা কাজ চাইতে দেয়, ভিতরের কার্যপ্রণালী না জেনেই।")),
                (("REST", "REST"), ("A style where every piece of data is a URL and the HTTP method says what to do with it.", "এমন ধরন যেখানে প্রতিটি ডেটা একটি URL আর HTTP মেথড বলে তার সাথে কী করতে হবে।")),
                (("Endpoint", "এন্ডপয়েন্ট"), ("One method plus one path, for example <code>PUT /api/me/roadmap</code>.", "একটি মেথড যোগ একটি পাথ, যেমন <code>PUT /api/me/roadmap</code>।")),
                (("HTTP method", "HTTP মেথড"), ("The verb: GET reads, POST creates, PUT replaces, DELETE removes.", "ক্রিয়া: GET পড়ে, POST তৈরি করে, PUT বদলায়, DELETE মুছে ফেলে।")),
                (("Status code", "স্টেটাস কোড"), ("A three-digit result: 2xx success, 4xx the request was wrong, 5xx the server could not finish.", "তিন অঙ্কের ফল: 2xx সফল, 4xx রিকোয়েস্ট ভুল, 5xx সার্ভার শেষ করতে পারেনি।")),
                (("JSON", "JSON"), ("Text format for data: objects in braces, arrays in brackets, <code>\"key\": value</code> pairs.", "ডেটার টেক্সট ফরম্যাট: অবজেক্ট ব্রেসে, অ্যারে ব্র্যাকেটে, <code>\"key\": value</code> জোড়া।")),
                (("CORS", "CORS"), ("A browser rule: a page on one origin may only call another origin if that server allows it by header.", "ব্রাউজার নিয়ম: এক origin-এর পেজ অন্য origin-কে কল করতে পারে শুধু যদি সেই সার্ভার হেডারে অনুমতি দেয়।")),
                (("Origin", "অরিজিন"), ("Scheme + host + port, for example <code>http://127.0.0.1:8417</code>.", "স্কিম + হোস্ট + পোর্ট, যেমন <code>http://127.0.0.1:8417</code>।")),
                (("Pagination", "পেজিনেশন"), ("Returning results in pages with <code>limit</code> and <code>offset</code> instead of all at once.", "সব একবারে না দিয়ে <code>limit</code> ও <code>offset</code> দিয়ে পেজে পেজে ফল দেওয়া।")),
                (("Idempotent", "ইডেম্পোটেন্ট"), ("Sending the same request twice leaves the same final state.", "একই রিকোয়েস্ট দুইবার পাঠালেও চূড়ান্ত অবস্থা একই থাকে।")),
            ],
        )
        + h3("Python and FastAPI", "Python ও FastAPI")
        + table(
            [("Term", "পরিভাষা"), ("Meaning", "অর্থ")],
            [
                (("Virtual environment", "ভার্চুয়াল এনভায়রনমেন্ট"), ("A private folder of packages, so this project's versions do not clash with another project's.", "প্যাকেজের ব্যক্তিগত ফোল্ডার, যাতে এই প্রজেক্টের ভার্সন অন্য প্রজেক্টের সাথে সংঘর্ষ না করে।")),
                (("ASGI / async", "ASGI / async"), ("A server interface that lets one worker handle many requests while waiting on the network.", "সার্ভার ইন্টারফেস যা নেটওয়ার্কের অপেক্ষায় থাকা অবস্থায় একজন কর্মীকে অনেক রিকোয়েস্ট সামলাতে দেয়।")),
                (("Pydantic model", "Pydantic মডেল"), ("A Python class describing the shape of data; it validates input and serialises output.", "ডেটার আকার বর্ণনা করা Python ক্লাস; ইনপুট যাচাই ও আউটপুট সিরিয়ালাইজ করে।")),
                (("Dependency injection", "ডিপেন্ডেন্সি ইনজেকশন"), ("FastAPI calling a function for you and passing its result into the route.", "FastAPI আপনার হয়ে একটি ফাংশন চালিয়ে তার ফল রুটে পাঠায়।")),
                (("Decorator", "ডেকোরেটর"), ("The <code>@router.get(...)</code> line above a function; it registers the function as an endpoint.", "ফাংশনের উপরের <code>@router.get(...)</code> লাইন; ফাংশনটিকে endpoint হিসেবে নিবন্ধন করে।")),
                (("Docstring", "ডকস্ট্রিং"), ("The first string inside a module, class or function, used as documentation.", "মডিউল, ক্লাস বা ফাংশনের ভিতরের প্রথম স্ট্রিং, ডকুমেন্টেশন হিসেবে ব্যবহৃত।")),
                (("Router", "রাউটার"), ("A group of related endpoints collected in one file and mounted under a prefix.", "এক ফাইলে জড়ো করা সম্পর্কিত endpoint-এর দল, একটি প্রিফিক্সের নিচে বসানো।")),
                (("Middleware", "মিডলওয়্যার"), ("Code that runs around every request, such as CORS headers.", "প্রতিটি রিকোয়েস্টের চারপাশে চলা কোড, যেমন CORS হেডার।")),
                (("Exception handler", "এক্সসেপশন হ্যান্ডলার"), ("A function that converts a Python error into a chosen HTTP answer.", "Python এররকে নির্বাচিত HTTP উত্তরে বদলানো ফাংশন।")),
                (("Environment variable", "এনভায়রনমেন্ট ভ্যারিয়েবল"), ("A named value supplied by the machine or platform, used for secrets and URLs.", "মেশিন বা প্ল্যাটফর্মের দেওয়া নামযুক্ত মান, সিক্রেট ও URL-এর জন্য ব্যবহৃত।")),
            ],
        )
        + h3("Database", "ডেটাবেস")
        + table(
            [("Term", "পরিভাষা"), ("Meaning", "অর্থ")],
            [
                (("PostgreSQL", "PostgreSQL"), ("The relational database Supabase runs: tables, rows, SQL, transactions.", "Supabase-এ চলা রিলেশনাল ডেটাবেস: টেবিল, রো, SQL, লেনদেন।")),
                (("Schema", "স্কিমা"), ("The structure — tables and columns — as opposed to the data inside them.", "গঠন — টেবিল ও কলাম — তাদের ভিতরের ডেটার বিপরীতে।")),
                (("Primary key", "প্রাইমারি কী"), ("The column that uniquely identifies a row.", "যে কলাম একটি রোকে অনন্যভাবে চিহ্নিত করে।")),
                (("Foreign key", "ফরেন কী"), ("A column that must match a primary key in another table, enforcing a link.", "যে কলাম অন্য টেবিলের প্রাইমারি কী-এর সাথে মিলতে হয়, সংযোগ রক্ষা করে।")),
                (("Index", "ইনডেক্স"), ("A lookup structure that speeds up finding rows by a column.", "একটি কলাম দিয়ে রো খোঁজা দ্রুত করার গঠন।")),
                (("Constraint", "কনস্ট্রেইন্ট"), ("A rule the database enforces, such as unique, not null or a foreign key.", "ডেটাবেস যে নিয়ম বলবৎ করে, যেমন unique, not null বা foreign key।")),
                (("Migration", "মাইগ্রেশন"), ("A scripted change to the schema, so the database moves from one version to the next.", "স্কিমার স্ক্রিপ্টকৃত পরিবর্তন, যাতে ডেটাবেস এক ভার্সন থেকে পরেরটায় যায়।")),
                (("Seed", "সিড"), ("Inserting the starting content a fresh database needs.", "নতুন ডেটাবেসের প্রয়োজনীয় প্রাথমিক কনটেন্ট ইনসার্ট করা।")),
                (("Upsert", "আপসার্ট"), ("Update if the row exists, insert if it does not.", "রো থাকলে আপডেট, না থাকলে ইনসার্ট।")),
                (("RLS", "RLS"), ("Row Level Security: policies that decide which rows each user may see or change.", "Row Level Security: কোন ইউজার কোন রো দেখতে বা বদলাতে পারবে তা ঠিক করা পলিসি।")),
                (("PostgREST", "PostgREST"), ("The layer that turns HTTP requests into SQL for PostgreSQL; the Supabase client talks to it.", "HTTP রিকোয়েস্টকে PostgreSQL-এর SQL-এ বদলানো স্তর; Supabase ক্লায়েন্ট এর সাথে কথা বলে।")),
                (("Trigger", "ট্রিগার"), ("A function the database runs automatically on insert, update or delete.", "ইনসার্ট, আপডেট বা ডিলিটে ডেটাবেস যে ফাংশন নিজে চালায়।")),
            ],
        )
        + h3("Auth and deployment", "অথ ও ডিপ্লয়")
        + table(
            [("Term", "পরিভাষা"), ("Meaning", "অর্থ")],
            [
                (("Authentication", "অথেন্টিকেশন"), ("Proving who the user is.", "ইউজার কে তা প্রমাণ করা।")),
                (("Authorisation", "অথরাইজেশন"), ("Deciding what that user may read or change.", "সেই ইউজার কী পড়তে বা বদলাতে পারবে তা ঠিক করা।")),
                (("JWT", "JWT"), ("A signed token carrying claims; the signature proves it was issued by Supabase.", "ক্লেইম বহন করা স্বাক্ষরিত টোকেন; স্বাক্ষর প্রমাণ করে এটি Supabase দিয়েছে।")),
                (("Access token", "অ্যাক্সেস টোকেন"), ("The short-lived string sent as <code>Authorization: Bearer …</code>; one hour here.", "স্বল্পমেয়াদি স্ট্রিং যা <code>Authorization: Bearer …</code> হিসেবে যায়; এখানে এক ঘণ্টা।")),
                (("Refresh token", "রিফ্রেশ টোকেন"), ("A longer-lived token used to obtain a new access token without the password — not used in this version.", "পাসওয়ার্ড ছাড়া নতুন অ্যাক্সেস টোকেন পাওয়ার দীর্ঘমেয়াদি টোকেন — এই ভার্সনে ব্যবহৃত নয়।")),
                (("Publishable key", "পাবলিশেবল কী"), ("The public Supabase key (<code>sb_publishable_…</code>), safe in a browser, subject to RLS.", "পাবলিক Supabase কী (<code>sb_publishable_…</code>), ব্রাউজারে নিরাপদ, RLS-এর অধীন।")),
                (("Service role key", "সার্ভিস রোল কী"), ("The secret Supabase key (<code>sb_secret_…</code>) that bypasses RLS; server-only, never shipped.", "সিক্রেট Supabase কী (<code>sb_secret_…</code>) যা RLS বাইপাস করে; শুধু সার্ভারে, কখনো পাঠানো হয় না।")),
                (("Serverless", "সার্ভারলেস"), ("Running code in containers the platform starts on demand, with no server you manage.", "প্ল্যাটফর্মের চাহিদামতো চালু করা কনটেইনারে কোড চালানো, নিজের সামলানো সার্ভার ছাড়া।")),
                (("Cold start", "কোল্ড স্টার্ট"), ("The extra delay on the first request after a function was idle.", "ফাংশন নিষ্ক্রিয় থাকার পর প্রথম রিকোয়েস্টে অতিরিক্ত দেরি।")),
                (("Build", "বিল্ড"), ("The step where the platform installs dependencies and packages the code for running.", "যে ধাপে প্ল্যাটফর্ম ডিপেন্ডেন্সি ইনস্টল করে ও কোড চালানোর জন্য প্যাকেজ করে।")),
                (("Preview deployment", "প্রিভিউ ডিপ্লয়মেন্ট"), ("A temporary URL for a branch or pull request, separate from production.", "ব্রাঞ্চ বা pull request-এর অস্থায়ী URL, প্রোডাকশন থেকে আলাদা।")),
                (("localStorage", "localStorage"), ("A small key-value store in the browser that survives reloads but not clearing site data.", "ব্রাউজারের ছোট key-value ভাণ্ডার, রিলোডে থাকে কিন্তু সাইট-ডেটা মুছলে যায়।")),
                (("Hydration", "হাইড্রেশন"), ("Filling the local cache from the server so the screen shows saved data after login.", "লগইনের পর সংরক্ষিত ডেটা দেখানোর জন্য সার্ভার থেকে লোকাল ক্যাশ ভরা।")),
            ],
        )
        + note(
            "If an examiner asks for a term that is not here, the honest answer is \"I do not know "
            "that term yet\" followed by what you do know about the area. Guessing is worse than "
            "not knowing, and it is much easier to spot.",
            "পরীক্ষক এখানে নেই এমন পরিভাষা জিজ্ঞেস করলে সৎ উত্তর \"এই পরিভাষাটি এখনো জানি না\" "
            "এবং তারপর সেই ক্ষেত্র নিয়ে যা জানেন তা বলা। অনুমান করা না-জানার চেয়ে খারাপ, আর "
            "অনুমান ধরা অনেক সহজ।",
            "warn",
        )
    )


# =============================================================================
# 15. LIMITATIONS AND NEXT STEPS
# =============================================================================


def s_next() -> str:
    return (
        para(
            "A system is easier to defend when its edges are known. These are the real limits "
            "of the current version, each with the change that would remove it — and none of "
            "them is hidden behind optimistic wording.",
            "সিস্টেমের সীমানা জানা থাকলে তা defend করা সহজ। এগুলো বর্তমান ভার্সনের আসল সীমা, "
            "প্রত্যেকটির সাথে তা দূর করার পরিবর্তন — আর কোনোটিই আশাবাদী ভাষায় লুকানো নয়।",
        )
        + h3("Known limitations", "জানা সীমাবদ্ধতা")
        + table(
            [("Limitation", "সীমাবদ্ধতা"), ("What the user experiences", "ইউজার কী অনুভব করে"), ("How to remove it", "কীভাবে দূর করবেন")],
            [
                (
                    ("No refresh token", "রিফ্রেশ টোকেন নেই"),
                    ("After one hour every protected action answers 401 and the login button returns.", "এক ঘণ্টা পর প্রতিটি সুরক্ষিত কাজে ৪০১ আসে আর লগইন বোতাম ফিরে আসে।"),
                    ("Store the refresh token, call <code>/auth/v1/token?grant_type=refresh_token</code> shortly before expiry, and retry the failed request once.", "রিফ্রেশ টোকেন রাখুন, মেয়াদ শেষের কিছু আগে <code>/auth/v1/token?grant_type=refresh_token</code> কল করুন, আর ব্যর্থ রিকোয়েস্ট একবার পুনরায় চালান।"),
                ),
                (
                    ("Last write wins", "শেষ লেখাটি জেতে"),
                    ("Two devices editing the same list at once keep only the later save.", "একসাথে দুই ডিভাইস একই লিস্ট বদলালে শুধু পরের সেভটি থাকে।"),
                    ("Add a <code>version</code> integer per list; reject a save whose version is stale and let the UI offer a merge.", "প্রতি লিস্টে একটি <code>version</code> পূর্ণসংখ্যা যোগ করুন; পুরোনো ভার্সনের সেভ বাতিল করুন আর UI-কে একীভূত করার সুযোগ দিতে দিন।"),
                ),
                (
                    ("Requests are stored, not emailed", "রিকোয়েস্ট সংরক্ষিত হয়, ইমেইল যায় না"),
                    ("A supervisor does not know a request exists until someone opens the database or admin screen.", "কেউ ডেটাবেস বা admin স্ক্রিন না খোলা পর্যন্ত সুপারভাইজার জানতে পারেন না রিকোয়েস্ট এসেছে।"),
                    ("Send an email after a successful insert, or add a Supabase database webhook to a small notifier function.", "সফল insert-এর পরে ইমেইল পাঠান, বা ছোট notifier ফাংশনে Supabase database webhook যোগ করুন।"),
                ),
                (
                    ("No admin panel", "admin প্যানেল নেই"),
                    ("Requests can only be read in the Supabase Table Editor, which is not presentable to a supervisor.", "রিকোয়েস্ট শুধু Supabase Table Editor-এ পড়া যায়, যা সুপারভাইজারকে দেখানো যায় না।"),
                    ("Add a protected <code>/api/admin/requests</code> route and one HTML page, guarded by a role claim in the user's profile.", "সুরক্ষিত <code>/api/admin/requests</code> রুট ও একটি HTML পেজ যোগ করুন, প্রোফাইলের role claim দিয়ে পাহারা দেওয়া।"),
                ),
                (
                    ("No rate limiting", "rate limiting নেই"),
                    ("Sign-up and search can be called as fast as a script can send them.", "স্ক্রিপ্ট যত দ্রুত পাঠাতে পারে ততবার সাইন-আপ ও সার্চ কল করা যায়।"),
                    ("Count attempts per IP per minute in a small table, or enable Vercel firewall rules.", "ছোট টেবিলে প্রতি IP প্রতি মিনিটে চেষ্টা গণনা করুন, বা Vercel firewall নিয়ম চালু করুন।"),
                ),
                (
                    ("Matching quiz runs in the browser", "ম্যাচিং কুইজ ব্রাউজারে চলে"),
                    ("Answers are checked client-side, so a determined visitor can read them from the JavaScript.", "উত্তর ক্লায়েন্ট-সাইডে যাচাই হয়, তাই জেদি ভিজিটর JavaScript থেকে পড়ে ফেলতে পারে।"),
                    ("Move the check to <code>POST /api/quiz/answer</code> and return only correct/incorrect.", "যাচাই <code>POST /api/quiz/answer</code>-এ সরান এবং শুধু সঠিক/ভুল ফেরত দিন।"),
                ),
                (
                    ("No password reset", "পাসওয়ার্ড রিসেট নেই"),
                    ("A student who forgets the password cannot recover the account without help.", "পাসওয়ার্ড ভুলে যাওয়া শিক্ষার্থী সাহায্য ছাড়া অ্যাকাউন্ট ফিরে পায় না।"),
                    ("Supabase has <code>reset_password_for_email</code>; it needs an email sender configured first.", "Supabase-এ <code>reset_password_for_email</code> আছে; আগে ইমেইল সেন্ডার কনফিগার করতে হবে।"),
                ),
                (
                    ("Free-plan cold start and pause", "ফ্রি-প্ল্যান কোল্ড স্টার্ট ও পজ"),
                    ("The first visitor waits about a second, and an unused Supabase project pauses after roughly a week.", "প্রথম দর্শনার্থী প্রায় এক সেকেন্ড অপেক্ষা করে, আর অব্যবহৃত Supabase প্রজেক্ট প্রায় এক সপ্তাহ পর পজ হয়।"),
                    ("Open the site before a demo. A paid plan or a scheduled ping removes both.", "ডেমোর আগে সাইট খুলুন। পেইড প্ল্যান বা নির্ধারিত ping দুটোই সরায়।"),
                ),
                (
                    ("Tests are not committed", "টেস্ট কমিট করা নেই"),
                    ("The 57 assertions were run from a script during development; a future contributor cannot rerun them.", "৫৭টি assertion ডেভেলপমেন্টের সময় স্ক্রিপ্ট থেকে চালানো; ভবিষ্যৎ অবদানকারী তা আবার চালাতে পারেন না।"),
                    ("Turn them into <code>tests/test_api.py</code> with pytest, and run it in GitHub Actions on every push.", "সেগুলো pytest দিয়ে <code>tests/test_api.py</code> করুন, আর প্রতিটি পুশে GitHub Actions-এ চালান।"),
                ),
            ],
        )
        + h3("If you keep working on it", "যদি আরও কাজ করেন")
        + steps_list(
            [
                (
                    "<b>Week 1 — make accounts complete.</b> Refresh tokens, password reset, and rate limiting on sign-up and login.",
                    "<b>সপ্তাহ ১ — অ্যাকাউন্ট পূর্ণ করা।</b> রিফ্রেশ টোকেন, পাসওয়ার্ড রিসেট, আর সাইন-আপ ও লগইনে rate limiting।",
                ),
                (
                    "<b>Week 2 — make it operable.</b> An admin page for connection requests, and email notification on a new request.",
                    "<b>সপ্তাহ ২ — পরিচালনযোগ্য করা।</b> কানেকশন রিকোয়েস্টের admin পেজ, আর নতুন রিকোয়েস্টে ইমেইল নোটিফিকেশন।",
                ),
                (
                    "<b>Week 3 — make it trustworthy.</b> Move the assertions into pytest, add GitHub Actions, and add one end-to-end Playwright test for the sign-up and bookmark flow.",
                    "<b>সপ্তাহ ৩ — বিশ্বাসযোগ্য করা।</b> assertion-গুলো pytest-এ নিন, GitHub Actions যোগ করুন, আর সাইন-আপ ও বুকমার্ক ফ্লোর জন্য একটি end-to-end Playwright টেস্ট যোগ করুন।",
                ),
                (
                    "<b>Week 4 — make it faster.</b> Full-text search with a <code>tsvector</code> column, content caching, and composite indexes for the filters actually used.",
                    "<b>সপ্তাহ ৪ — দ্রুততর করা।</b> <code>tsvector</code> কলাম দিয়ে full-text search, কনটেন্ট ক্যাশিং, আর বাস্তবে ব্যবহৃত ফিল্টারের composite index।",
                ),
            ]
        )
        + h3("Adding a feature — the order that works", "ফিচার যোগ করা — যে ক্রমে কাজ করে")
        + pre(
            """
1. Database first     sql/002_add_column.sql   (and run it in the SQL Editor)
2. Seed / backfill    update the JSON and re-run the seeder if content changes
3. Schema             app/schemas.py          (add the field to the model)
4. Router             the endpoint that reads or writes it
5. Frontend           api.js helper, then the page module
6. Verify             /docs with a real token, then the browser
"""
        )
        + para(
            "That order exists because each step can be checked before the next one depends on "
            "it. Doing the frontend first means debugging three layers at once when something "
            "is wrong.",
            "এই ক্রমটি আছে কারণ প্রতিটি ধাপ পরেরটি তার উপর নির্ভর করার আগেই যাচাই করা যায়। "
            "আগে ফ্রন্টএন্ড করলে কিছু ভুল হলে একসাথে তিন স্তর ডিবাগ করতে হয়।",
        )
        + h3("What this project demonstrates", "এই প্রজেক্ট কী প্রমাণ করে")
        + bullets(
            [
                (
                    "A static site can gain real accounts and durable data without being rewritten — one new JavaScript file was enough.",
                    "পুনর্লিখন ছাড়াই একটি স্ট্যাটিক সাইটে আসল অ্যাকাউন্ট ও টেকসই ডেটা যোগ করা যায় — একটি নতুন JavaScript ফাইলই যথেষ্ট ছিল।",
                ),
                (
                    "Secrets belong on the server. The browser only ever holds a short-lived token.",
                    "সিক্রেট সার্ভারে থাকে। ব্রাউজার শুধু স্বল্পমেয়াদি টোকেন ধরে।",
                ),
                (
                    "Constraints and validation are cheaper than fixing corrupted data later: unique keys, Pydantic models and database checks caught mistakes at the door.",
                    "পরে নষ্ট ডেটা ঠিক করার চেয়ে constraint ও ভ্যালিডেশন সস্তা: unique key, Pydantic মডেল ও ডেটাবেস চেক ভুলকে দরজাতেই আটকেছে।",
                ),
                (
                    "An error message written for a human is part of the product, not decoration. The 503 handler turned a blank failure into an instruction.",
                    "মানুষের জন্য লেখা এরর বার্তা পণ্যের অংশ, সাজসজ্জা নয়। ৫০৩ হ্যান্ডলার ফাঁকা ব্যর্থতাকে করণীয়তে বদলেছে।",
                ),
                (
                    "Testing in two layers found different classes of bug. Neither layer alone would have found all three.",
                    "দুই স্তরে পরীক্ষা আলাদা ধরনের বাগ ধরেছে। কোনো একটি স্তর একা তিনটিই ধরত না।",
                ),
            ]
        )
        + note(
            "Keep this document next to the code. When the code changes, re-run "
            "<code>python scripts/build_prep_doc.py</code> — the file embeds the real sources, so "
            "the explanation cannot silently drift away from what the project actually does.",
            "এই ডকুমেন্টটি কোডের পাশে রাখুন। কোড বদলালে "
            "<code>python scripts/build_prep_doc.py</code> আবার চালান — ফাইলটি আসল সোর্স এমবেড করে, "
            "তাই ব্যাখ্যা চুপচাপ প্রজেক্টের বাস্তব আচরণ থেকে সরে যেতে পারে না।",
            "good",
        )
    )



if __name__ == "__main__":
    build()
