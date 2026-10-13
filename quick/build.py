"""Build the quick-revision site: 4 pages + hub, responsive (phone and PC).

Sources live in src/ (print-ready HTML from the PDF builds). For the GitHub Q&A,
parts/gh_wN.clean.html (no-ai-slop pass) replaces the week when present.
Run: python3 quick/build.py  (writes quick/*.html)
"""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGES = [
    ("1", "cheatsheet.html", "Cheat sheet", "Every topic in one line. Fast scan before the exam.", "cheatsheet"),
    ("2", "questions.html", "Question bank", "Every likely question with a clear answer, week by week.", "questionbank"),
    ("3", "github.html", "Lecturer's GitHub Q&A", "His own questions (plan, pools, book), solved.", "github"),
    ("4", "diagrams.html", "Diagrams", "The diagrams to draw in the exam, boxes and arrows.", "diagrams"),
]

BASE_CSS = """
:root { --ink:#111; --muted:#5a6573; --accent:#1c4f8a; --bar:#1c2430; --bg:#fff; --line:#d5dbe3; }
html { scroll-padding-top: 96px; -webkit-text-size-adjust: 100%; }
body { margin:0 !important; background:var(--bg) !important; color:var(--ink);
  font: 17px/1.5 "Inter","Helvetica Neue",Arial,sans-serif !important; }
.wrap { max-width: 880px; margin: 0 auto; padding: 12px 16px 80px; }
.wide .wrap { max-width: 1500px; }
body:not(.wide) .wrap { max-width: 1100px; }
nav.top { position: sticky; top: 0; z-index: 10; background: var(--bar); color:#fff; box-shadow: 0 1px 4px rgba(0,0,0,.25); }
nav.top .in { max-width: 1500px; margin: 0 auto; padding: 6px 12px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
nav.top a { color:#fff; text-decoration:none; padding:6px 10px; border-radius:6px; font-size:15px; white-space:nowrap; }
nav.top a.on { background:#3a6db3; }
nav.top a:hover { background:#2d3a4d; }
nav.top .k { opacity:.6; font-size:12px; margin-right:3px; }
nav.weeks { display:flex; gap:6px; overflow-x:auto; padding:6px 12px; background:#eef2f7; position: sticky; top: 44px; z-index: 9; }
nav.weeks a { flex:none; padding:5px 12px; border-radius:14px; background:#fff; border:1px solid var(--line); color:var(--accent); text-decoration:none; font-size:14px; font-weight:600; }
h2 { break-before: auto !important; scroll-margin-top: 100px; }
img, svg, pre, table { max-width: 100%; }
pre { overflow-x: auto; }
a.totop { position: fixed; right: 14px; bottom: 14px; background: var(--bar); color:#fff; border-radius: 50%; width: 44px; height: 44px; display:grid; place-items:center; text-decoration:none; font-size:20px; opacity:.85; }
@media (max-width: 700px) {
  body { font-size: 16px !important; }
  nav.top a .t { display:none; } nav.top a.on .t { display:inline; }
  .wrap { padding: 10px 12px 80px; }
}
@media print { nav, a.totop { display:none; } }
"""

PER_DOC_CSS = {
    "cheatsheet": """
header { display:block !important; } header h1 { font-size: 22px !important; } header span { font-size: 14px !important; }
main { column-count: 1 !important; column-rule: none; }
h2 { font-size: 18px !important; padding: 6px 10px !important; margin: 18px 0 6px !important; column-span: all; }
h3 { font-size: 14px !important; margin: 10px 0 4px !important; break-after: avoid; }
p { font-size: 16px !important; margin: 0 0 6px !important; padding-left: 16px !important; text-indent: -16px !important; line-height: 1.4; }
@media (min-width: 900px) { main { column-count: 2 !important; column-gap: 28px !important; column-rule: 1px solid #ddd !important; } p { font-size: 15px !important; } }
@media (min-width: 1300px) { main { column-count: 3 !important; } }
""",
    "questionbank": """
h1 { font-size: 24px !important; } h2 { font-size: 20px !important; padding: 6px 10px !important; margin: 26px 0 10px !important; }
h3 { font-size: 14px !important; margin: 18px 0 8px !important; }
.q { font-size: 17px; } .src { font-size: 13px !important; } .a { padding-left: 12px !important; }
.qa { margin: 0 0 16px !important; }
""",
    "github": """
h1 { font-size: 24px !important; } h2 { font-size: 20px !important; padding: 6px 10px !important; margin: 26px 0 10px !important; }
.q { font-size: 17px; margin: 18px 0 6px !important; } .tag { font-size: 13px !important; }
.a { padding-left: 12px !important; margin-bottom: 12px !important; }
.a pre { font-size: 14px !important; padding: 8px !important; }
""",
    "diagrams": """
h1 { font-size: 24px !important; } .sub { font-size: 15px; }
h2 { font-size: 20px !important; padding: 6px 10px !important; margin: 24px 0 10px !important; }
.d { padding: 10px 12px !important; margin: 0 0 14px !important; }
.d h3 { font-size: 18px !important; } .d p { font-size: 15px !important; }
.sv { overflow-x: auto; -webkit-overflow-scrolling: touch; }
@media (max-width: 760px) { .sv svg { width: 720px !important; max-width: none !important; } .sv::after { content: "← swipe to see the whole diagram →"; display:block; font-size:12px; color:#5a6573; text-align:center; } }
""",
}


def nav(active):
    links = ['<a href="./"><span class="t">Home</span><span class="k">0</span></a>'.replace('<span class="t">Home</span><span class="k">0</span>', '⌂ <span class="t">Home</span>')]
    for key, href, title, _, _ in PAGES:
        on = ' class="on"' if href == active else ""
        links.append(f'<a href="{href}"{on}><span class="k">{key}</span><span class="t">{title}</span></a>')
    return f'<nav class="top"><div class="in">{"".join(links)}</div></nav>'


KEYS_JS = """<script>
document.addEventListener('keydown', e => {
  if (e.ctrlKey || e.metaKey || e.altKey || /input|textarea/i.test(e.target.tagName)) return;
  const map = {'0':'./','1':'cheatsheet.html','2':'questions.html','3':'github.html','4':'diagrams.html'};
  if (map[e.key]) location.href = map[e.key];
});
</script>"""


def read_doc(src):
    s = open(os.path.join(ROOT, "src", src + ".html"), encoding="utf-8").read()
    style = "\n".join(re.findall(r"<style>(.*?)</style>", s, re.S))
    style = re.sub(r"@page\s*\{[^}]*\}", "", style)
    body = s[s.find("<body>") + 6 : s.rfind("</body>")]
    return style, body


def github_body():
    head = open(os.path.join(ROOT, "parts", "gh_head.html"), encoding="utf-8").read()
    out = [head]
    for w in range(5, 11):
        clean = os.path.join(ROOT, "parts", f"gh_w{w}.clean.html")
        raw = os.path.join(ROOT, "parts", f"gh_w{w}.html")
        out.append(open(clean if os.path.exists(clean) else raw, encoding="utf-8").read())
    return "".join(out)


def add_week_ids(body):
    def rep(m):
        tag, attrs, text = m.group(1), m.group(2), m.group(3)
        wk = re.search(r"Week\s+(\d+)", text)
        if not wk or "id=" in attrs:
            return m.group(0)
        return f'<{tag} id="w{wk.group(1)}"{attrs}>{text}'
    return re.sub(r"<(h2)([^>]*)>([^<]*)", rep, body)


def diagrams_grid(body):
    # wrap each week's run of .d cards in a grid div so PC shows 2 per row
    parts = re.split(r"(<h2[^>]*>.*?</h2>)", body, flags=re.S)
    out = []
    for p in parts:
        if p.startswith("<h2"):
            out.append(p)
        elif '<div class="d"' in p:
            i = p.find('<div class="d"')
            out.append(p[:i] + '<div class="grid">' + p[i:] + "</div>")
        else:
            out.append(p)
    return "".join(out)


def page(key, href, title, src):
    style, body = read_doc(src)
    if src == "github":
        body = github_body()
    if src == "diagrams":
        body = re.sub(r"(<svg\b.*?</svg>)", r'<div class="sv">\1</div>', body, flags=re.S)
    body = add_week_ids(body)
    weeks = "".join(f'<a href="#w{w}">W{w}</a>' for w in range(5, 11) if f'id="w{w}"' in body)
    wide = ' class="wide"' if src == "cheatsheet" else ""
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · BDA Weeks 5–10</title>
<style>{style}</style><style>{BASE_CSS}{PER_DOC_CSS[src]}</style></head>
<body{wide}>{nav(href)}<nav class="weeks">{weeks}</nav><div class="wrap" id="top">{body}</div>
<a class="totop" href="#top" aria-label="Back to top">↑</a>{KEYS_JS}</body></html>"""
    open(os.path.join(ROOT, href), "w", encoding="utf-8").write(html)


def hub():
    cards = "".join(
        f'<a class="card" href="{href}"><span class="n">{key}</span><span><b>{title}</b><br><small>{desc}</small></span></a>'
        for key, href, title, desc, _ in PAGES
    )
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BDA Quick Revision</title>
<style>{BASE_CSS}
.card {{ display:flex; gap:14px; align-items:center; padding:16px; margin:0 0 12px; border:1px solid var(--line); border-radius:12px; text-decoration:none; color:var(--ink); background:#fff; }}
.card:hover {{ border-color: var(--accent); background:#f5f8fc; }}
.card .n {{ flex:none; width:44px; height:44px; border-radius:10px; background:var(--bar); color:#fff; display:grid; place-items:center; font-size:22px; font-weight:700; }}
.card small {{ color: var(--muted); font-size: 15px; }}
h1 {{ font-size: 26px; margin: 18px 0 4px; }} p.lead {{ color: var(--muted); margin: 0 0 18px; }}
</style></head><body>{nav("")}<div class="wrap">
<h1>CSE 4345 BDA: quick revision, Weeks 5–10</h1>
<p class="lead">Pick one. Keys 1–4 jump between pages on a PC, 0 comes back here.</p>
{cards}
<p class="lead">Suggested order: 1 the cheat sheet first, then 2 the ★ questions, then 4 the diagrams. Use 3 if time is left.</p>
<p class="lead"><a href="../">Full study guide</a></p>
</div>{KEYS_JS}</body></html>"""
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)


if __name__ == "__main__":
    for key, href, title, _, src in PAGES:
        page(key, href, title, src)
    hub()
    print("built", [p[1] for p in PAGES] + ["index.html"])
