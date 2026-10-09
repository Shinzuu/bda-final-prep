#!/usr/bin/env python3
"""Build the compact CSE 4345 final guide from cards/w05..w10.json.

    python3 build.py      # index.html (interactive) + bda-final-guide.pdf (print)
"""

import html
import json
import pathlib
import random
import re
import subprocess

ROOT = pathlib.Path(__file__).parent
WEEKS = range(5, 11)
FORMAT_NAMES = {
    "mcq": "MCQ", "blank": "Fill in the blank", "define": "Define / list", "steps": "Explain the steps",
    "why": "Why / justify", "distinguish": "Distinguish", "scenario": "Scenario", "one_step": "One-step calc",
    "full_calc": "Full calc", "long": "Long answer",
}
SRC_ORDER = ["MCQ", "True/False", "Descriptive", "Analytical", "Discussion", "Live Exercise"]
SRC_CLASS = {"MCQ": "mcq", "True/False": "tf", "Descriptive": "desc", "Analytical": "anal",
             "Discussion": "disc", "Live Exercise": "live"}

CSS = r"""
:root{--bg:#fbfaf7;--panel:#fff;--ink:#1c1b19;--mute:#6b6760;--line:#e4e0d8;--accent:#b45309;
--acc-soft:#fef3c7;--green:#15803d;--green-soft:#ecfdf3;--red:#b91c1c;--red-soft:#fef2f2;
--blue:#1d4ed8;--blue-soft:#eff6ff;--yel:#fde68a;--code:#f4f2ee;--violet:#6d28d9;--violet-soft:#f5f3ff}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121110;--panel:#1b1a18;--ink:#ebe8e2;
--mute:#a39e95;--line:#33302b;--accent:#f59e0b;--acc-soft:#3a2a0c;--green:#4ade80;--green-soft:#0f2417;
--red:#f87171;--red-soft:#2c1414;--blue:#93c5fd;--blue-soft:#111d33;--yel:#78590a;--code:#23211e;
--violet:#c4b5fd;--violet-soft:#221a3a}}
:root[data-theme=dark]{--bg:#121110;--panel:#1b1a18;--ink:#ebe8e2;--mute:#a39e95;--line:#33302b;--accent:#f59e0b;
--acc-soft:#3a2a0c;--green:#4ade80;--green-soft:#0f2417;--red:#f87171;--red-soft:#2c1414;--blue:#93c5fd;
--blue-soft:#111d33;--yel:#78590a;--code:#23211e;--violet:#c4b5fd;--violet-soft:#221a3a}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.55 Inter,"Segoe UI",system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:0 16px 96px}
a{color:var(--accent)}
code,pre{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:.86em}
pre{background:var(--code);padding:10px 12px;border-radius:8px;overflow-x:auto;white-space:pre-wrap}
code{background:var(--code);padding:0 4px;border-radius:4px;overflow-wrap:anywhere}pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:6px 0}
th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{background:var(--code);font-weight:600}
.tw{overflow-x:auto;max-width:100%}.grid2>*,.qa .txt,.ans{min-width:0}
/* top bar */
.bar{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);
backdrop-filter:blur(6px);border-bottom:1px solid var(--line)}
.bar-in{max-width:980px;margin:0 auto;padding:8px 16px;display:flex;gap:6px;align-items:center;overflow-x:auto}
.bar b{white-space:nowrap;margin-right:6px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:3px 11px;
font:inherit;font-size:.85rem;white-space:nowrap;cursor:pointer;text-decoration:none}
.chip.on,.chip:hover{border-color:var(--accent);color:var(--accent)}
.sp{flex:1}
/* hero */
.hero{padding:28px 0 8px}.hero h1{font-size:1.9rem;margin:0}.hero .sub{color:var(--mute);margin:.2em 0 1em}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.fact{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:.9rem}
.fact b{display:block;color:var(--accent);font-size:.75rem;text-transform:uppercase;letter-spacing:.06em}
/* chapter */
.ch{padding-top:30px}
.ch>header{border-bottom:3px solid var(--accent);padding-bottom:8px;margin-bottom:14px}
.ch h2{margin:0;font-size:1.5rem}.ch h2 small{color:var(--accent);font-size:.8rem;display:block;
letter-spacing:.08em;text-transform:uppercase}
.ch .summary{color:var(--mute);margin:.4em 0 0}
h3{font-size:1.1rem;margin:22px 0 10px;display:flex;align-items:center;gap:8px}
h3 .n{font-size:.75rem;color:var(--mute);font-weight:500}
/* pool */
.qa{background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:8px 0;overflow:hidden}
.qa .q{padding:10px 12px;cursor:pointer;display:flex;gap:10px}
.qa .q .txt{flex:1}
.tag{font-size:.7rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;border-radius:6px;
padding:2px 7px;height:fit-content;white-space:nowrap}
.tag.mcq{background:var(--blue-soft);color:var(--blue)}.tag.tf{background:var(--violet-soft);color:var(--violet)}
.tag.desc{background:var(--green-soft);color:var(--green)}.tag.anal{background:var(--acc-soft);color:var(--accent)}
.tag.disc{background:var(--code);color:var(--mute)}.tag.live{background:var(--red-soft);color:var(--red)}
.opts{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:2px}
.ans{display:none;border-top:1px dashed var(--line);background:var(--green-soft);padding:10px 12px 10px 14px;
border-left:4px solid var(--green)}
.qa.open .ans,body.all .ans{display:block}
.ans>:first-child{margin-top:0}.ans>:last-child{margin-bottom:0}
.hint{color:var(--mute);font-size:.75rem;white-space:nowrap}
.qa.open .hint{visibility:hidden}
/* cards */
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:14px 0;padding:14px 16px}
.card h4{margin:0 0 8px;font-size:1.05rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media (max-width:720px){.grid2{grid-template-columns:1fr}}
.lay{font-size:.92rem}.lay h5{margin:0 0 4px;font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--mute)}
.lay ul,.lay ol{margin:0;padding-left:1.2em}.lay li{margin:2px 0}
.lay.trap{background:var(--red-soft);border-radius:8px;padding:8px 10px}.lay.trap h5{color:var(--red)}
.lay.calc{background:var(--blue-soft);border-radius:8px;padding:8px 10px}.lay.calc h5{color:var(--blue)}
.lay+.lay,.grid2+.lay,.lay+.grid2{margin-top:10px}
.sc td:last-child{background:var(--yel);font-weight:600}
.marks{margin-top:8px;display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:.92rem}
.marks b{color:var(--accent);white-space:nowrap}
details.drill{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
details.drill summary{cursor:pointer;font-weight:600;font-size:.9rem;color:var(--accent)}
.fmt{font-size:.7rem;color:var(--mute);text-transform:uppercase;letter-spacing:.05em}
/* formulas & mock */
.fs td:nth-child(2){font-family:"JetBrains Mono",monospace;font-size:.85rem}
.mock .part{margin:8px 0}.mock .mk{float:right;color:var(--mute);font-size:.85rem}
.or{text-align:center;font-weight:700;color:var(--mute);margin:6px 0}
.toggle{margin-left:auto}
@media (max-width:640px){.qa .q{flex-wrap:wrap;gap:4px 8px}.qa .q .txt{order:3;flex-basis:100%}.hint{margin-left:auto}
.hero h1{font-size:1.5rem}.ch h2{font-size:1.25rem}.card{padding:12px}main{padding:0 12px 80px}
.marks{grid-template-columns:1fr}}
.dia{margin:4px 0 12px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px}
.dia svg{display:block;width:100%;height:auto;max-height:420px}
.dia figcaption{font-size:.82rem;color:var(--mute);text-align:center;margin-top:4px}
:root{--d-ink:#1c1b19;--d-mute:#78716c}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--d-box:#3a2a0c;--d-line:#f59e0b;--d-box2:#111d33;
--d-line2:#93c5fd;--d-box3:#0f2417;--d-line3:#4ade80;--d-ink:#ebe8e2;--d-mute:#a39e95}}
:root[data-theme=dark]{--d-box:#3a2a0c;--d-line:#f59e0b;--d-box2:#111d33;--d-line2:#93c5fd;--d-box3:#0f2417;
--d-line3:#4ade80;--d-ink:#ebe8e2;--d-mute:#a39e95}
@media print{
 body{background:#fff;font-size:9.2pt;line-height:1.38}.bar,.noprint,.hint{display:none!important}
 main{max-width:none;padding:0}.ans{display:block!important;padding:5px 9px}
 .qa .q{padding:5px 9px}.qa{margin:5px 0;break-inside:auto}.q{break-inside:avoid;break-after:avoid}
 .ch{break-before:page;padding-top:0}.hero{padding-top:0}
 .card{break-inside:auto;padding:8px 10px;margin:8px 0}.dia{break-inside:avoid;padding:4px;margin:2px auto 8px;max-width:150mm}.dia svg{max-height:62mm}.lay.scen{display:none}
 .lay li{margin:0}table{font-size:8.6pt}th,td{padding:3px 5px}
 h3{margin:12px 0 6px}.card h4{break-after:avoid}
 :root{--bg:#fff;--panel:#fff;--d-box:#fff7ed;--d-line:#b45309;--d-box2:#eff6ff;--d-line2:#1d4ed8;--d-box3:#ecfdf3;
 --d-line3:#15803d;--d-ink:#1c1b19;--d-mute:#78716c}
}
@page{size:A4;margin:11mm 10mm}
body.poolonly .cardsec,body.poolonly .card,body.poolonly #mock,body.poolonly .hero .facts:first-of-type{display:none!important}
"""

JS = r"""
if(location.search.includes("pool"))document.body.classList.add("poolonly");
document.querySelectorAll('.qa .q').forEach(q=>q.addEventListener('click',()=>q.parentNode.classList.toggle('open')));
const all=document.getElementById('all');
all&&all.addEventListener('click',()=>{document.body.classList.toggle('all');all.classList.toggle('on')});
const th=document.getElementById('theme');
try{const t=localStorage.getItem('bda-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}
th&&th.addEventListener('click',()=>{const r=document.documentElement;
 const dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
 r.dataset.theme=dark?'light':'dark';try{localStorage.setItem('bda-theme',r.dataset.theme)}catch(e){}});
"""


def esc(s):
    return html.escape(html.unescape(str(s or "")), quote=False)


def ul(items, tag="ul"):
    return f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>"


def qa(tagcls, tagtxt, n, q, a, options=None, code=None, extra=""):
    opts = ""
    if options:
        opts = '<ul class="opts">' + "".join(f"<li>{o}</li>" for o in options) + "</ul>"
    cd = f"<pre><code>{esc(code)}</code></pre>" if code else ""
    num = f"<b>{esc(n)}.</b> " if n else ""
    return (f'<div class="qa{extra}"><div class="q"><span class="tag {tagcls}">{tagtxt}</span>'
            f'<div class="txt">{num}{q}{opts}{cd}</div><span class="hint">show answer</span></div>'
            f'<div class="ans">{a}</div></div>')


def pool(d):
    tops = {t["id"]: t for t in d["topics"]}
    for p in d["pool"]:
        t = tops.get(p.get("topic"))
        if t and t.get("diagram") and re.search(r"\b(draw|diagram|sketch|illustrat)", p["q"], re.I) \
                and "<svg" not in p["a"] and "diagrams/" not in p["a"]:
            p["a"] = re.sub(r"\s*\(?(draw|see) the [^.)]*?(card|figure) above\)?", "", p["a"])
            p["a"] = figure(t) + p["a"]
    items = sorted(d["pool"], key=lambda p: SRC_ORDER.index(p["src"]) if p["src"] in SRC_ORDER else 99)
    out = [f'<h3 id="w{d["week"]}-pool">Exam question pool <span class="n">{len(items)} questions from the '
           "slides · click a question for its answer</span></h3>"]
    for p in items:
        out.append(qa(SRC_CLASS.get(p["src"], "disc"), esc(p["src"]), p.get("n"), p["q"], p["a"],
                      p.get("options"), p.get("code")))
    return "".join(out)


def contrast_tables(cs):
    out = []
    for c in cs:
        head = c.get("head")
        h = "<tr>" + "".join(f"<th>{x}</th>" for x in head) + "</tr>" if head else ""
        rows = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in c["rows"])
        out.append(f'<div class="tw"><table>{h}{rows}</table></div>')
    return "".join(out)


def drill(t, seed):
    rnd = random.Random(seed)
    out = []
    for q in t["questions"]:
        opts = None
        if q.get("options"):
            opts = list(q["options"])
            correct = opts[0]
            rnd.shuffle(opts)
            letter = "abcdefgh"[opts.index(correct)]
            opts = [f"({'abcdefgh'[i]}) {o}" for i, o in enumerate(opts)]
            a = f"<b>({letter}) {correct}</b><br>{q['a']}"
        else:
            a = q["a"]
        out.append(qa("disc", FORMAT_NAMES.get(q["format"], q["format"]), "", q["q"], a, opts))
    return f'<details class="drill noprint"><summary>Practise this topic in {len(out)} formats</summary>{"".join(out)}</details>'


def figure(t):
    d = t.get("diagram")
    if not d or not (ROOT / d["file"]).exists():
        return ""
    svg = (ROOT / d["file"]).read_text()
    svg = re.sub(r"<\?xml[^>]*>", "", svg).strip()
    return f'<figure class="dia">{svg}<figcaption>{d.get("caption", "")}</figcaption></figure>'


def card(t):
    calc = t.get("calculation")
    sc = "".join(f"<tr><td>{s['cue']}</td><td>{s['answer']}</td></tr>" for s in t["scenarios"])
    parts = [
        f'<div class="card" id="{t["id"]}"><h4>{esc(t["title"])}</h4>',
        figure(t),
        '<div class="grid2">',
        f'<div class="lay"><h5>Facts</h5>{ul(t["facts"])}</div>',
        f'<div class="lay"><h5>How it works</h5>{ul(t["mechanism"], "ol")}</div>',
        "</div><div class=\"grid2\">",
        f'<div class="lay"><h5>Why · pros · limits</h5>{ul(t["why"])}</div>',
        f'<div class="lay"><h5>Compare</h5>{contrast_tables(t["contrasts"])}</div>',
        "</div>",
        f'<div class="lay scen"><h5>Spot it in a scenario</h5><div class="tw"><table class="sc">'
        f'<tr><th>If the question describes…</th><th>Answer</th></tr>{sc}</table></div></div>',
    ]
    if calc:
        parts.append(f'<div class="lay calc"><h5>Calculation</h5>{calc["example"]}'
                     f'<p><b>Step by step</b></p>{ul(calc["steps"], "ol")}'
                     f'<p><b>Variants</b></p>{ul(calc["variants"])}</div>')
    parts.append(f'<div class="lay trap"><h5>Traps</h5>{ul(t["traps"])}</div>')
    a = t["answers"]
    parts.append(f'<details class="drill noprint"><summary>Model answers at 1, 3 and 5 marks</summary><div class="marks">'
                 f'<b>1 mark</b><div>{a["1"]}</div><b>3 marks</b><div>{a["3"]}</div>'
                 f'<b>5 marks</b><div>{a["5"]}</div></div></details>')
    parts.append(drill(t, t["id"]))
    parts.append("</div>")
    return "".join(parts)


def chapter(d, i):
    w = d["week"]
    return (f'<section class="ch" id="w{w}"><header><h2><small>Chapter {i} · Week {w}</small>{esc(d["title"])}</h2>'
            f'<p class="summary">{d["summary"]}</p></header>'
            + pool(d)
            + f'<h3 class="cardsec" id="w{w}-cards">Topic cards <span class="n">{len(d["topics"])} topics · everything the pool tests</span></h3>'
            + "".join(card(t) for t in d["topics"]) + "</section>")


def mock(chs):
    out = ['<section class="ch mock" id="mock"><header><h2><small>Practice</small>Mock final paper</h2>'
           '<p class="summary">One 10-mark question per chapter, in the shape of the October 2026 Data Mining '
           "final from the same department: a short scenario, then short parts. Answer either the main pair or "
           "the OR pair. Click a part for its answer.</p></header>"]
    for i, d in enumerate(chs, 1):
        m = d["mock"]
        out.append(f'<h3>Q{i} · Week {d["week"]} <span class="n">10 marks</span></h3>')
        for k, lab in (("a", "a"), ("b", "b")):
            p = m[k]
            out.append(qa("anal", f"{lab} · {p['marks']} marks", "", p["q"], p["a"]))
        if m.get("or_a"):
            out.append('<div class="or">OR</div>')
            for k, lab in (("or_a", "a"), ("or_b", "b")):
                p = m[k]
                out.append(qa("desc", f"{lab} · {p['marks']} marks", "", p["q"], p["a"]))
    out.append("</section>")
    return "".join(out)


def sheet(chs):
    rows = []
    for d in chs:
        for f in d.get("formulas", []):
            rows.append(f"<tr><td>W{d['week']} · {f['name']}</td><td>{f['formula']}</td><td>{f.get('note', '')}</td></tr>")
    facts = []
    for d in chs:
        for t in d["topics"]:
            facts.append(f"<tr><td>W{d['week']}</td><td><b>{esc(t['title'])}</b></td><td>{t['answers']['1']}</td></tr>")
    return ('<section class="ch" id="sheet"><header><h2><small>Last ten minutes</small>Formula and fact sheet</h2></header>'
            '<h3>Formulas</h3><div class="tw"><table class="fs"><tr><th>What</th><th>Formula</th><th>Note</th></tr>'
            + "".join(rows) + "</table></div>"
            '<h3>Every topic in one line</h3><div class="tw"><table><tr><th>Wk</th><th>Topic</th><th>One-line answer</th></tr>'
            + "".join(facts) + "</table></div></section>")


def main():
    chs = [json.loads(p.read_text()) for w in WEEKS if (p := ROOT / f"cards/w{w:02d}.json").exists()]
    npool = sum(len(d["pool"]) for d in chs)
    ntop = sum(len(d["topics"]) for d in chs)
    nav = "".join(f'<a class="chip" href="#w{d["week"]}">W{d["week"]}</a>' for d in chs)
    toc = "".join(
        f'<div class="fact"><b>Week {d["week"]}</b><a href="#w{d["week"]}">{esc(d["title"])}</a><br>'
        f'<span style="color:var(--mute)">{len(d["pool"])} pool questions · {len(d["topics"])} topics</span></div>'
        for d in chs)
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>BDA Final Guide</title><style>{CSS}</style></head><body>"
        f'<nav class="bar"><div class="bar-in"><b>BDA final</b>{nav}'
        '<a class="chip" href="#mock">Mock</a><a class="chip" href="#sheet">Sheet</a><span class="sp"></span>'
        '<button class="chip" id="all">All answers</button><button class="chip" id="theme" aria-label="Toggle dark mode">Theme</button></div></nav><main>'
        '<header class="hero"><h1>CSE 4345 Big Data Analytics</h1>'
        '<p class="sub">Final exam guide · Weeks 5–10 · 13 October 2026</p>'
        '<div class="facts">'
        '<div class="fact"><b>Where questions come from</b>The teacher said the end-of-chapter pools. '
        f'All {npool} pool questions are here, answered at exam length.</div>'
        f'<div class="fact"><b>How to study</b>1. Read a chapter\'s pool. 2. Learn its {round(ntop / max(len(chs), 1))} topic cards. '
        '3. Drill a card in every format. 4. Sit the mock. 5. Revise from the sheet.</div>'
        '<div class="fact"><b>Colours</b><span style="background:var(--yel)">yellow</span> = the answer · '
        '<span style="color:var(--red)">red</span> = traps · <span style="color:var(--blue)">blue</span> = maths</div>'
        "</div><h3>Chapters</h3><div class=\"facts\">" + toc + "</div></header>"
        + "".join(chapter(d, i) for i, d in enumerate(chs, 1))
        + mock(chs) + sheet(chs)
        + f"</main><script>{JS}</script></body></html>"
    )
    def inline_img(m):
        f = ROOT / m.group(1)
        if not f.exists():
            return m.group(0)
        svg = re.sub(r"<\?xml[^>]*>", "", f.read_text()).strip()
        return f'<figure class="dia">{svg}</figure>'
    page = re.sub(r'<img[^>]*src="(diagrams/[^"]+\.svg)"[^>]*>', inline_img, page)
    page = re.sub(r'(?<!<div class="tw">)(<table.*?</table>)', r'<div class="tw">\1</div>', page, flags=re.S)
    (ROOT / "index.html").write_text(page)
    subprocess.run(
        ["google-chrome-stable", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={ROOT / 'bda-final-guide.pdf'}", (ROOT / "index.html").as_uri()],
        check=True, capture_output=True)
    subprocess.run(
        ["google-chrome-stable", "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=3000",
         f"--print-to-pdf={ROOT / 'bda-exam-pool.pdf'}", (ROOT / "index.html").as_uri() + "?pool"],
        check=True, capture_output=True)
    print(f"{len(chs)} chapters, {ntop} topics, {npool} pool questions")


if __name__ == "__main__":
    main()
