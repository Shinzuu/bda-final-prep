#!/usr/bin/env python3
"""Build the CSE 4345 final prep book from data/w05..w10.json.

    python3 build.py          # writes index.html and bda-final-prep.pdf
"""

import html
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).parent
WEEKS = range(5, 11)

CSS = """
:root{--ink:#1d1d1f;--mute:#5b5b66;--line:#d9d9e0;--bg:#fff;--card:#f7f7fa;
--accent:#b45309;--ans:#ecfdf3;--ansline:#16a34a;--q:#fff7ed;--qline:#f59e0b;
--math:#eff6ff;--mathline:#2563eb;--code:#f3f4f6}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--ink:#e8e8ee;--mute:#a1a1ad;
--line:#33333d;--bg:#141418;--card:#1c1c22;--accent:#f59e0b;--ans:#0f2a1a;--ansline:#22c55e;
--q:#2a1f10;--qline:#f59e0b;--math:#0f1d33;--mathline:#60a5fa;--code:#24242c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Inter","Segoe UI",system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:2rem;margin:0 0 .2em}
h2{font-size:1.6rem;color:var(--accent);border-bottom:2px solid var(--accent);padding-bottom:.2em;margin-top:0}
h3{font-size:1.2rem;margin:1.6em 0 .6em}
.sub{color:var(--mute)}
.cover{padding:48px 0 24px}
.toc ol{padding-left:1.2em}.toc li{margin:.5em 0}.toc a{color:var(--ink);text-decoration:none}
.toc a b{color:var(--accent)}.toc ul{color:var(--mute);font-size:.92rem;margin:.2em 0}
.chapter{padding-top:24px}
.primer{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 18px}
.qa{margin:14px 0 22px;break-inside:avoid-page}
.q{background:var(--q);border-left:4px solid var(--qline);padding:10px 14px;border-radius:6px}
.q .n{font-weight:700;color:var(--accent);margin-right:.4em}
.q ul.opts{list-style:none;padding-left:.4em;margin:.4em 0 0}
.a{background:var(--ans);border-left:4px solid var(--ansline);padding:10px 14px;margin-top:6px;border-radius:6px}
.a::before{content:"Answer";display:block;font-size:.75rem;font-weight:700;letter-spacing:.06em;
text-transform:uppercase;color:var(--ansline);margin-bottom:2px}
.a p:first-child,.q p:first-child{margin-top:0}.a p:last-child{margin-bottom:0}
.math{background:var(--math);border-left:4px solid var(--mathline);padding:12px 16px;border-radius:6px;margin:14px 0}
.math h4{margin:0 0 .4em}.formula{font-family:"JetBrains Mono",monospace;font-size:1.05rem;
background:var(--bg);border:1px solid var(--line);padding:8px 12px;border-radius:6px;overflow-x:auto}
.lbl{font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mathline);margin-top:.8em}
pre{background:var(--code);padding:10px;border-radius:6px;overflow-x:auto;font-size:.85rem;white-space:pre-wrap}
code{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:.9em}
table{border-collapse:collapse;margin:.6em 0;font-size:.92rem;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{background:var(--card)}
@media print{body{font-size:11pt}main{max-width:none;padding:0}.chapter{break-before:page}
.qa{break-inside:auto}.q{break-inside:avoid;break-after:avoid}a{color:inherit}
:root{--bg:#fff}}
@page{size:A4;margin:16mm 14mm}
"""


def esc(s):
    return html.escape(html.unescape(s or ""), quote=False)


def question(q):
    out = ['<div class="qa"><div class="q">']
    out.append(f'<span class="n">{esc(q.get("n"))}.</span>{q["q"]}')
    if q.get("options"):
        out.append('<ul class="opts">' + "".join(f"<li>{o}</li>" for o in q["options"]) + "</ul>")
    if q.get("code"):
        out.append(f'<pre><code>{esc(q["code"])}</code></pre>')
    out.append(f'</div><div class="a">{q["a"]}</div></div>')
    return "".join(out)


def chapter(d, idx):
    w = d["week"]
    out = [f'<section class="chapter" id="w{w}"><h2>Chapter {idx} · Week {w}: {esc(d["title"])}</h2>']
    if d.get("primer"):
        out.append('<div class="primer"><h3 style="margin-top:.4em">The chapter in plain words</h3>')
        out += [f"<p>{p}</p>" for p in d["primer"]]
        out.append("</div>")
    for s in d["sections"]:
        sid = f'w{w}-' + "".join(c for c in (s["part"] + s["heading"]).lower() if c.isalnum())
        out.append(f'<h3 id="{sid}">{esc(s["part"])} · {esc(s["heading"])}</h3>')
        out += [question(q) for q in s["questions"]]
    m = d.get("maths")
    if m:
        out.append(f'<h3 id="w{w}-maths">Maths for Week {w}</h3>')
        if m.get("intro"):
            out.append(f'<p>{m["intro"]}</p>')
        for it in m["items"]:
            out.append(f'<div class="math"><h4>{esc(it["title"])}</h4>'
                       f'<div class="formula">{it["formula"]}</div>'
                       f'<div class="lbl">What each symbol means</div>{it.get("symbols", "")}'
                       f'<div class="lbl">Worked example</div>{it.get("example", "")}'
                       f'<div class="lbl">Practice</div>{it.get("practice", "")}</div>')
    out.append("</section>")
    return "".join(out)


def toc(chapters):
    items = []
    for i, d in enumerate(chapters, 1):
        w = d["week"]
        subs = [f'{esc(s["part"])} · {esc(s["heading"])} ({len(s["questions"])})' for s in d["sections"]]
        if d.get("maths"):
            subs.append("Maths section")
        items.append(f'<li><a href="#w{w}"><b>Chapter {i} · Week {w}</b> {esc(d["title"])}</a>'
                     f'<ul>{"".join(f"<li>{x}</li>" for x in subs)}</ul></li>')
    return '<nav class="toc"><h2>Contents</h2><ol>' + "".join(items) + "</ol></nav>"


def main():
    chapters = [json.loads((ROOT / f"data/w{w:02d}.json").read_text()) for w in WEEKS]
    total = sum(len(s["questions"]) for d in chapters for s in d["sections"])
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>BDA Final Prep</title><style>{CSS}</style></head><body><main>"
        '<header class="cover"><h1>CSE 4345 Big Data Analytics</h1>'
        '<p class="sub">Final exam prep book · Weeks 5 to 10 · exam on 13 October 2026</p>'
        f'<p>Every end-of-chapter question from the slides ({total} in all), copied as written, '
        "with the answer directly under it. Part 1 questions come from the Student Assessment Pool; "
        "Part 2 questions come from the Discussion Questions and Live Exercise. Chapters with "
        "calculations end with a maths section.</p></header>"
        + toc(chapters)
        + "".join(chapter(d, i) for i, d in enumerate(chapters, 1))
        + "</main></body></html>"
    )
    (ROOT / "index.html").write_text(page)
    subprocess.run(
        ["google-chrome-stable", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={ROOT / 'bda-final-prep.pdf'}", (ROOT / "index.html").as_uri()],
        check=True, capture_output=True)
    print(f"{len(chapters)} chapters, {total} questions -> index.html, bda-final-prep.pdf")


if __name__ == "__main__":
    main()
