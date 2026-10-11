#!/usr/bin/env python3
"""Build the CSE 4345 final guide from cards/w05..w10.json and diagrams/*.svg.

    python3 build.py      # index.html (interactive) + bda-final-guide.pdf + bda-exam-pool.pdf

The page is one self-contained file with one view per section (Start here, W5..W10, Comparisons, Slide
problems, Mock, Sheet). Start here leads with the one-day plan from extra/predicted.json, whose links resolve
to cards, pool questions, comparisons (extra/comparisons.json) and slide problems (extra/slide_problems.json);
the older 34-session full-coverage plan sits folded below it. Also: Known/Again progress saved in localStorage, and a
flashcard focus mode. Card layers are ordered answer first; everything after the scenario table
is folded until asked for.
"""

import html
import json
import math
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
SRC_SHORT = {"MCQ": "MCQ", "True/False": "T/F", "Descriptive": "Descriptive", "Analytical": "Analytical",
             "Discussion": "Discussion", "Live Exercise": "Live exercise"}
SESSION_TARGET = 21  # minutes; sessions land between ~15 and ~25

CSS = r"""
:root{--bg:#fbfaf7;--panel:#fff;--ink:#1c1b19;--mute:#6b6760;--line:#e4e0d8;--accent:#b45309;
--acc-soft:#fef3c7;--green:#15803d;--green-soft:#ecfdf3;--red:#b91c1c;--red-soft:#fef2f2;
--blue:#1d4ed8;--blue-soft:#eff6ff;--yel:#fde68a;--code:#f4f2ee;--violet:#6d28d9;--violet-soft:#f5f3ff;
--shadow:0 1px 2px rgba(28,27,25,.06),0 4px 14px rgba(28,27,25,.05)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121110;--panel:#1b1a18;--ink:#ebe8e2;
--mute:#a39e95;--line:#33302b;--accent:#f59e0b;--acc-soft:#3a2a0c;--green:#4ade80;--green-soft:#0f2417;
--red:#f87171;--red-soft:#2c1414;--blue:#93c5fd;--blue-soft:#111d33;--yel:#78590a;--code:#23211e;
--violet:#c4b5fd;--violet-soft:#221a3a;--shadow:none}}
:root[data-theme=dark]{--bg:#121110;--panel:#1b1a18;--ink:#ebe8e2;--mute:#a39e95;--line:#33302b;--accent:#f59e0b;
--acc-soft:#3a2a0c;--green:#4ade80;--green-soft:#0f2417;--red:#f87171;--red-soft:#2c1414;--blue:#93c5fd;
--blue-soft:#111d33;--yel:#78590a;--code:#23211e;--violet:#c4b5fd;--violet-soft:#221a3a;--shadow:none}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
[id]{scroll-margin-top:62px}
body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.55 Inter,"Segoe UI",system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:0 16px 110px}
a{color:var(--accent)}
button{font:inherit;color:inherit}
code,pre{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:.86em}
pre{background:var(--code);padding:10px 12px;border-radius:8px;overflow-x:auto;white-space:pre-wrap}
code{background:var(--code);padding:0 4px;border-radius:4px;overflow-wrap:anywhere}pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:6px 0}
th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{background:var(--code);font-weight:600}
.tw{overflow-x:auto;max-width:100%}.qa .txt,.ans{min-width:0}
.view:not(.cur){display:none}body.showall .view{display:block}
/* ---------- top bar ---------- */
.bar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 92%,transparent);
backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.bar-in{max-width:980px;margin:0 auto;padding:7px 16px;display:flex;gap:6px;align-items:center}
.brand{font-weight:700;text-decoration:none;color:var(--ink);white-space:nowrap;margin-right:4px}
.brand span{color:var(--accent)}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:4px 11px;
font-size:.85rem;white-space:nowrap;cursor:pointer;text-decoration:none;line-height:1.4}
.chip.on,.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.ico{padding:4px 9px}
.dnav{display:flex;gap:5px;align-items:center}
.sp{flex:1}
.opct{font-size:.8rem;color:var(--mute);white-space:nowrap;font-variant-numeric:tabular-nums}
.obar{position:absolute;left:0;right:0;bottom:-1px;height:3px;background:transparent}
.obar i{display:block;height:100%;width:0;background:var(--accent);transition:width .3s}
/* bottom tab bar (phone) */
.tabbar{position:fixed;left:0;right:0;bottom:0;z-index:20;display:none;background:var(--panel);
border-top:1px solid var(--line);padding:4px 4px calc(4px + env(safe-area-inset-bottom))}
.tabbar-in{display:grid;grid-template-columns:repeat(5,1fr);max-width:560px;margin:0 auto}
.tab{background:none;border:0;padding:5px 0 3px;font-size:.72rem;color:var(--mute);text-decoration:none;
display:flex;flex-direction:column;align-items:center;gap:1px;cursor:pointer}
.tab svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.tab.on{color:var(--accent);font-weight:600}
.wkmenu{position:fixed;left:8px;right:8px;bottom:64px;z-index:21;background:var(--panel);border:1px solid var(--line);
border-radius:14px;padding:10px;box-shadow:0 10px 30px rgba(0,0,0,.18);display:none;max-width:540px;margin:0 auto}
.wkmenu.open{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.wkmenu a{display:block;text-decoration:none;color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:8px 10px;font-size:.88rem}
.wkmenu a b{color:var(--accent)}.wkmenu a.bank{grid-column:span 1;background:var(--acc-soft)}.wpct{color:var(--mute);font-size:.75rem;white-space:nowrap}
@media (max-width:1099px){.dnav{display:none}.tabbar{display:block}}
@media (min-width:1100px){.m-only{display:none!important}}
/* ---------- progress ---------- */
.prog{display:flex;align-items:center;gap:10px;font-size:.82rem;color:var(--mute);flex-wrap:wrap}
.pbar{flex:1 1 140px;height:8px;border-radius:99px;background:var(--code);overflow:hidden;min-width:80px}
.pbar i{display:block;height:100%;width:0;background:var(--accent);border-radius:99px;transition:width .3s}
.ptxt{font-variant-numeric:tabular-nums}
/* ---------- start view ---------- */
.hero{padding:22px 0 4px}.hero h1{font-size:1.75rem;margin:0;line-height:1.2}
.hero .sub{color:var(--mute);margin:.25em 0 0}
.count{display:inline-block;background:var(--acc-soft);color:var(--accent);font-weight:700;font-size:.8rem;
border-radius:99px;padding:2px 10px;margin-top:8px}
.next{margin:16px 0 6px;background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--accent);
border-radius:12px;padding:12px 14px;box-shadow:var(--shadow)}
.next small{display:block;color:var(--accent);font-weight:700;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase}
.next .nt{font-weight:700;font-size:1.08rem;margin:2px 0}
.next .ns{color:var(--mute);font-size:.88rem}
.btnrow{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.btn{border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:10px;padding:7px 14px;
font-weight:600;font-size:.9rem;cursor:pointer;text-decoration:none;display:inline-block}
:root[data-theme=dark] .btn{color:#1c1b19}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .btn{color:#1c1b19}}
.btn.ghost{background:transparent;color:var(--accent)}
.btn.sm{padding:4px 10px;font-size:.82rem;border-radius:8px}
.resume{font-size:.88rem;color:var(--mute);margin:8px 0 0}
h2.sec{font-size:1.15rem;margin:26px 0 8px}
.day{margin:14px 0 4px;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.day b{font-size:1rem}.day span{color:var(--mute);font-size:.82rem}
.plan{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.plan .ph{list-style:none;font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:8px 0 0}
.sess{display:grid;grid-template-columns:20px 1fr auto;gap:0 10px;align-items:center;background:var(--panel);
border:1px solid var(--line);border-radius:10px;padding:7px 10px}
.sess .sdot{width:18px;height:18px;border-radius:50%;border:2px solid var(--line);display:grid;place-items:center;font-size:11px;color:#fff}
.sess.full .sdot{background:var(--green);border-color:var(--green)}
.sess.full .sdot::after{content:"\2713"}
.sess.isnext{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
.sess .sm{min-width:0;text-decoration:none;color:var(--ink)}
.sess .st{display:block;font-weight:600;font-size:.92rem;line-height:1.3}
.sess .sc{display:block;font-size:.78rem;color:var(--mute);line-height:1.35}
.sess .sr{display:flex;flex-direction:column;align-items:flex-end;gap:3px}
.sess .smin{font-size:.78rem;font-weight:700;color:var(--accent);white-space:nowrap}
.sess .sbar{grid-column:2/4;height:3px;border-radius:9px;background:var(--code);overflow:hidden;margin-top:5px}
.sess .sbar i{display:block;height:100%;width:0;background:var(--green)}
.sess.full .st{color:var(--mute)}
.mini{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:2px 8px;font-size:.78rem;
cursor:pointer;color:var(--accent);text-decoration:none;white-space:nowrap}
.mini:hover{border-color:var(--accent)}
.wkgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:8px}
.wk{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;text-decoration:none;color:var(--ink);display:block}
.wk small{color:var(--accent);font-weight:700;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase}
.wk b{display:block;margin:1px 0 6px;font-size:.95rem}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.85rem;color:var(--mute)}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:5px}
.fine{font-size:.82rem;color:var(--mute)}
/* ---------- week view ---------- */
.wkhead{padding:20px 0 6px;border-bottom:3px solid var(--accent);margin-bottom:10px}
.wkhead small{color:var(--accent);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;font-weight:700}
.wkhead h2{margin:2px 0 6px;font-size:1.45rem;line-height:1.25}
.summary{color:var(--mute);margin:.5em 0 .3em;font-size:.92rem}
.toc{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:10px 0 4px;font-size:.88rem}
.toc .row{display:flex;flex-wrap:wrap;gap:5px;align-items:center}
.toc .row+.row{margin-top:8px}
.toc .lbl{font-weight:700;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--mute);margin-right:2px}
.toc ol{margin:6px 0 0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:2px 14px}
.toc li a{text-decoration:none;color:var(--ink);display:flex;gap:6px;align-items:baseline;padding:2px 0}
.toc li a::before{content:"";flex:none;width:9px;height:9px;border-radius:50%;border:1.5px solid var(--mute);transform:translateY(1px)}
.toc li.isdone a::before{background:var(--green);border-color:var(--green)}
.toc li a span{color:var(--mute);font-size:.78rem;white-space:nowrap}
h3.sh{font-size:1.12rem;margin:24px 0 8px;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
h3.sh .n{font-size:.78rem;color:var(--mute);font-weight:500}
h4.grp{margin:16px 0 6px;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mute)}
/* ---------- questions: shared ---------- */
.qa{border-radius:10px;margin:7px 0;overflow:hidden}
.qa .q{padding:9px 12px;cursor:pointer;display:flex;gap:8px;align-items:flex-start}
.qa .q .txt{flex:1}
.tag{font-size:.68rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;border-radius:6px;
padding:2px 7px;height:fit-content;white-space:nowrap}
.tag.mcq{background:var(--blue-soft);color:var(--blue)}.tag.tf{background:var(--violet-soft);color:var(--violet)}
.tag.desc{background:var(--green-soft);color:var(--green)}.tag.anal{background:var(--acc-soft);color:var(--accent)}
.tag.disc{background:var(--code);color:var(--mute)}.tag.live{background:var(--red-soft);color:var(--red)}
.opts{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:2px}
.ans{display:none;padding:10px 12px 10px 14px}
.qa.open .ans,body.all .ans{display:block}
.ans>:first-child{margin-top:0}.ans>:last-child{margin-bottom:0}
.st8{flex:none;width:10px;height:10px;border-radius:50%;margin-top:6px;border:1.5px solid var(--line)}
[data-st=k] .st8{background:var(--green);border-color:var(--green)}
[data-st=a] .st8{background:var(--red);border-color:var(--red)}
.afoot{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin-top:10px;
padding-top:8px;border-top:1px dashed var(--line)}
.mk{display:flex;gap:6px;margin-left:auto}
.mk button{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:4px 12px;font-size:.82rem;cursor:pointer;font-weight:600}
.mk button[data-m=a]{color:var(--red)}.mk button[data-m=k]{color:var(--green)}
[data-st=a] .mk button[data-m=a]{background:var(--red);border-color:var(--red);color:#fff}
[data-st=k] .mk button[data-m=k]{background:var(--green);border-color:var(--green);color:#fff}
.tocard{font-size:.82rem;text-decoration:none;font-weight:600}
/* pool: solid card, amber spine, number */
.qa.pool{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);box-shadow:var(--shadow)}
.qa.pool .num{font-weight:800;font-size:.8rem;color:var(--accent);white-space:nowrap;min-width:1.9em;padding-top:2px}
.qa.pool .ans{background:var(--green-soft);border-top:1px dashed var(--line)}
.qa.pool[data-st=k]{border-left-color:var(--green)}.qa.pool[data-st=a]{border-left-color:var(--red)}
/* drill: dashed, flat, violet */
.qa.drill{background:transparent;border:1.5px dashed var(--line);font-size:.93rem}
.qa.drill .tag{background:var(--violet-soft);color:var(--violet)}
.qa.drill .ans{background:var(--violet-soft);border-top:1.5px dashed var(--line)}
.qa.drill[data-st=k]{border-color:color-mix(in srgb,var(--green) 55%,var(--line))}
.qa.drill[data-st=a]{border-color:color-mix(in srgb,var(--red) 55%,var(--line))}
.hl{animation:hl 1.6s ease-out}
@keyframes hl{0%{box-shadow:0 0 0 3px var(--accent)}100%{box-shadow:0 0 0 3px transparent}}
/* ---------- cards ---------- */
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:14px 0;padding:14px 16px;box-shadow:var(--shadow)}
.card>header{display:flex;gap:10px;align-items:flex-start}
.card h4{margin:0;font-size:1.06rem;flex:1;line-height:1.3}
.card .meta{font-size:.75rem;color:var(--mute);margin-top:2px;display:block;font-weight:500}
.done{border:1.5px solid var(--line);background:var(--panel);border-radius:99px;padding:3px 11px 3px 8px;font-size:.8rem;
cursor:pointer;white-space:nowrap;font-weight:600;color:var(--mute)}
.done::before{content:"\25CB  "}
.card.isdone .done{background:var(--green);border-color:var(--green);color:#fff}
.card.isdone .done::before{content:"\2713  "}
.card.isdone{border-color:color-mix(in srgb,var(--green) 45%,var(--line))}
.one{background:var(--yel);background:color-mix(in srgb,var(--yel) 70%,var(--panel));border-radius:8px;padding:8px 11px;margin:10px 0 0;font-weight:500}
.one b.l,.lay h5{display:block;margin:0 0 3px;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;color:var(--mute);font-weight:700}
.one b.l{color:color-mix(in srgb,var(--ink) 60%,transparent)}
.lay{font-size:.92rem;margin-top:10px}
.lay ul,.lay ol{margin:0;padding-left:1.2em}.lay li{margin:2px 0}
.lay.trap{background:var(--red-soft);border-radius:8px;padding:8px 10px}.lay.trap h5{color:var(--red)}
.lay.calc{background:var(--blue-soft);border-radius:8px;padding:8px 10px}.lay.calc h5{color:var(--blue)}
.sc td:last-child{background:var(--yel);background:color-mix(in srgb,var(--yel) 70%,var(--panel));font-weight:600}
.sc{margin:0}
.pills{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px;padding-top:10px;border-top:1px solid var(--line)}
.pill{border:1px solid var(--line);background:var(--bg);border-radius:99px;padding:3px 10px;font-size:.8rem;cursor:pointer;color:var(--ink)}
.pill::after{content:" +";color:var(--mute)}
.pill.on{border-color:var(--accent);color:var(--accent);background:var(--acc-soft)}.pill.on::after{content:" \2212"}
.pill.calc{color:var(--blue)}.pill.drl{color:var(--violet)}
.fold-b{display:none}.fold-b.open{display:block}
.fold-b>.lay:first-child{margin-top:10px}
.marks{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:.92rem}
.marks b{color:var(--accent);white-space:nowrap}
.back{margin-top:10px;font-size:.8rem;color:var(--mute);display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline}
.back a{text-decoration:none;font-weight:600}
.fmt{font-size:.7rem;color:var(--mute);text-transform:uppercase;letter-spacing:.05em}
/* ---------- diagrams ---------- */
.dia{margin:10px 0 4px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px}
.dia .pan{overflow-x:auto;-webkit-overflow-scrolling:touch}
.dia svg{display:block;width:100%;height:auto;max-height:60vh;margin:0 auto}
.dia figcaption{font-size:.82rem;color:var(--mute);text-align:center;margin-top:4px}
.panhint{display:none;font-size:.72rem;color:var(--accent);text-align:center;font-weight:600}
@media (max-width:760px){.dia svg{min-width:var(--minw);max-height:none}.panhint{display:block}}
.dialink{font-weight:600;text-decoration:none}
:root{--d-ink:#1c1b19;--d-mute:#78716c}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--d-box:#3a2a0c;--d-line:#f59e0b;--d-box2:#111d33;
--d-line2:#93c5fd;--d-box3:#0f2417;--d-line3:#4ade80;--d-ink:#ebe8e2;--d-mute:#a39e95}}
:root[data-theme=dark]{--d-box:#3a2a0c;--d-line:#f59e0b;--d-box2:#111d33;--d-line2:#93c5fd;--d-box3:#0f2417;
--d-line3:#4ade80;--d-ink:#ebe8e2;--d-mute:#a39e95}
/* ---------- mock: exam paper ---------- */
.paper{background:var(--panel);border:2px solid var(--ink);border-radius:4px;padding:14px 16px;margin:16px 0;
box-shadow:4px 4px 0 var(--line)}
.paper>header{display:flex;justify-content:space-between;align-items:baseline;gap:8px;border-bottom:1px solid var(--ink);
padding-bottom:6px;margin-bottom:6px;font-family:Georgia,"Times New Roman",serif}
.paper>header b{font-size:1.12rem}.paper>header span{font-size:.85rem;color:var(--mute)}
.qa.mock{border:0;border-radius:0;margin:0;border-top:1px dotted var(--line)}
.qa.mock:first-of-type{border-top:0}
.qa.mock .q{padding:10px 2px;display:block}
.qa.mock .pl{font-family:Georgia,serif;font-weight:700;font-size:.95rem;margin-bottom:2px;display:flex;justify-content:space-between;gap:8px}
.qa.mock .pl span{font-family:inherit;font-weight:400;color:var(--mute);font-size:.85rem;white-space:nowrap}
.qa.mock .ans{background:var(--blue-soft);border-left:3px solid var(--blue);border-radius:6px;margin:0 0 10px}
.qa.mock .ans::before{content:"Model answer";display:block;font-size:.68rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--blue);margin-bottom:4px}
.qa.mock .tap{font-size:.75rem;color:var(--mute)}.qa.mock.open .tap,body.all .qa.mock .tap{display:none}
ol.rom{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:4px}
ol.rom li{display:grid;grid-template-columns:2.1em 1fr;gap:4px}
ol.rom li>b:first-child{font-family:Georgia,serif;color:var(--mute)}
.or{text-align:center;font-family:Georgia,serif;font-weight:700;letter-spacing:.2em;color:var(--mute);margin:6px 0;
display:flex;align-items:center;gap:10px}.or::before,.or::after{content:"";flex:1;border-top:1px solid var(--line)}
/* ---------- sheet ---------- */
.fgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:8px}
.fcard{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:8px;padding:7px 10px;font-size:.88rem;break-inside:avoid}
.fcard b{display:block;font-size:.84rem}
.fcard .fx{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:.82rem;background:var(--blue-soft);color:var(--ink);
border-radius:6px;padding:5px 7px;margin:5px 0;overflow-wrap:anywhere}
.fcard .fn{color:var(--mute);font-size:.82rem}
.toplist{columns:2 300px;column-gap:20px;font-size:.88rem;margin:0;padding:0;list-style:none}
.toplist li{break-inside:avoid;padding:2px 0}.toplist li span{color:var(--mute);font-size:.75rem;margin-right:6px}
/* ---------- focus mode ---------- */
.focus{position:fixed;inset:0;z-index:50;background:var(--bg);display:none;flex-direction:column}
.focus.open{display:flex}
body.locked{overflow:hidden}
.f-top{display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid var(--line);max-width:760px;width:100%;margin:0 auto}
.f-top b{flex:1;font-size:.95rem;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.f-top span{font-size:.8rem;color:var(--mute);white-space:nowrap;font-variant-numeric:tabular-nums}
.f-bar{height:4px;background:var(--code)}.f-bar i{display:block;height:100%;width:0;background:var(--green);transition:width .25s}
.f-body{flex:1;overflow-y:auto;padding:16px;width:100%;max-width:760px;margin:0 auto}
.f-card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:var(--shadow);cursor:pointer}
.f-card .tag{display:inline-block;margin-bottom:8px}
.f-q{font-size:1.05rem}.f-q h4{margin:0 0 6px;font-size:1.15rem}
.f-a{display:none;margin-top:14px;padding-top:12px;border-top:2px dashed var(--line)}
.f-card.rev .f-a{display:block}.f-card.rev .f-tap{display:none}
.f-tap{text-align:center;color:var(--mute);font-size:.85rem;margin:14px 0 0}
.f-prompt{color:var(--mute);font-size:.92rem;margin:0}
.f-btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px 16px calc(12px + env(safe-area-inset-bottom));
max-width:760px;width:100%;margin:0 auto;border-top:1px solid var(--line)}
.f-btns button{border:0;border-radius:12px;padding:13px;font-weight:700;font-size:1rem;cursor:pointer}
.f-btns .fr{grid-column:span 2;background:var(--accent);color:#fff}
.f-btns .fa{background:var(--red-soft);color:var(--red);border:1px solid var(--red)}
.f-btns .fk{background:var(--green-soft);color:var(--green);border:1px solid var(--green)}
.f-btns kbd{font:inherit;font-size:.7rem;opacity:.6;margin-left:6px}@media (pointer:coarse){.f-btns kbd{display:none}}
.f-pick h3{margin:18px 0 8px;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--mute)}
.f-pick .pg{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px}
.f-pick button{text-align:left;border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:9px 11px;cursor:pointer;font-size:.88rem}
.f-pick button small{display:block;color:var(--mute);font-size:.75rem}
.f-pick button.big{border-color:var(--accent);grid-column:1/-1}
.f-end{text-align:center;padding:30px 10px}.f-end .big{font-size:2.4rem;line-height:1}
/* ---------- one-day plan ---------- */
.honest{background:var(--green-soft);border:1px solid color-mix(in srgb,var(--green) 35%,var(--line));border-radius:10px;padding:8px 11px;font-size:.86rem;margin:8px 0}
details.fold{background:var(--panel);border:1px solid var(--line);border-radius:10px;margin:8px 0;font-size:.88rem}
details.fold>summary{cursor:pointer;padding:8px 11px;font-weight:600;color:var(--accent)}
details.fold>div{padding:0 11px 10px}
.emph{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.emph li{display:grid;grid-template-columns:2.2em 1fr;gap:2px 8px;border-top:1px dashed var(--line);padding-top:6px}
.emph .sc9{font-weight:800;color:var(--accent);font-variant-numeric:tabular-nums}
.emph .ev{grid-column:2;color:var(--mute);font-size:.8rem}
.blks{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.blk{min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:var(--shadow)}
.blk.isnext{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
.blk .bh{display:grid;grid-template-columns:26px 1fr auto;gap:8px;align-items:center}
.blk .bn{width:24px;height:24px;border-radius:50%;border:2px solid var(--line);display:grid;place-items:center;font-size:.75rem;font-weight:800;color:var(--mute)}
.blk.full .bn{background:var(--green);border-color:var(--green);color:#fff}
.blk .bt{font-weight:700;font-size:.95rem;line-height:1.3;min-width:0}
.blk.full .bt{color:var(--mute);text-decoration:line-through;text-decoration-color:var(--line)}
.blk .bm{font-size:.8rem;font-weight:700;color:var(--accent);white-space:nowrap}
.blk .bk{font-size:.86rem;margin:6px 0 0;color:var(--ink)}
.lks{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.lk{border:1px solid var(--line);border-radius:7px;padding:2px 7px;font-size:.76rem;text-decoration:none;color:var(--ink);
background:var(--bg);cursor:pointer;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.5}
.lk::before{font-weight:800;margin-right:4px;font-size:.66rem;letter-spacing:.04em}
.lk.lcard{border-color:color-mix(in srgb,var(--accent) 45%,var(--line))}.lk.lcard::before{content:"CARD";color:var(--accent)}
.lk.lpool{border-color:color-mix(in srgb,var(--green) 45%,var(--line))}.lk.lpool::before{content:"POOL";color:var(--green)}
.lk.lcmp{border-color:color-mix(in srgb,var(--violet) 45%,var(--line))}.lk.lcmp::before{content:"VS";color:var(--violet)}
.lk.lprob{border-color:color-mix(in srgb,var(--blue) 45%,var(--line))}.lk.lprob::before{content:"CALC";color:var(--blue)}
.lk.lpaper{border-color:var(--ink)}.lk.lpaper::before{content:"PAPER"}
.lk.lgo::before{content:"\25B6";color:var(--accent)}
.lk.isdone{opacity:.55;text-decoration:line-through}
.blk .bf{display:flex;gap:8px;align-items:center;margin-top:9px;flex-wrap:wrap}
.blk .bf .bp{flex:1 1 90px;height:4px;border-radius:9px;background:var(--code);overflow:hidden;min-width:60px}
.blk .bf .bp i{display:block;height:100%;width:0;background:var(--green)}
.tk{border:1.5px solid var(--line);background:var(--panel);border-radius:99px;padding:3px 11px 3px 8px;font-size:.8rem;cursor:pointer;font-weight:600;color:var(--mute)}
.tk::before{content:"\25CB  "}.tk.on{background:var(--green);border-color:var(--green);color:#fff}.tk.on::before{content:"\2713  "}
/* ---------- banks: filters ---------- */
.filt{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin:6px 0}
.filt .lbl{font-weight:700;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--mute);margin-right:2px;min-width:4.6em}
.fb{border:1px solid var(--line);background:var(--panel);border-radius:999px;padding:3px 10px;font-size:.8rem;cursor:pointer}
.fb.on{border-color:var(--accent);background:var(--acc-soft);color:var(--accent);font-weight:600}
.shown{font-size:.8rem;color:var(--mute);margin:4px 0 0}
.lik{font-size:.66rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;border-radius:6px;padding:2px 7px;white-space:nowrap;height:fit-content}
.lik.high{background:var(--red-soft);color:var(--red)}.lik.medium{background:var(--code);color:var(--mute)}
.lik.vl{background:var(--red-soft);color:var(--red)}.lik.l{background:var(--code);color:var(--mute)}
/* comparisons */
.cmpc{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--violet);border-radius:12px;margin:10px 0;padding:11px 13px;box-shadow:var(--shadow)}
.cmpc>header{display:flex;gap:8px;align-items:flex-start}
.cmpc h4{margin:0;font-size:1rem;flex:1;line-height:1.3}
.cmpc .meta{display:block;font-size:.74rem;color:var(--mute);font-weight:500;margin-top:2px}
.cmpc .cue{font-size:.88rem;margin-top:8px}.cmpc .cue b{color:var(--mute);font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;display:block}
.cmpc[data-st=k]{border-left-color:var(--green)}.cmpc[data-st=a]{border-left-color:var(--red)}
.cmpc table th:first-child,.cmpc table td:first-child{color:var(--mute);font-weight:600;width:22%}
/* slide problems */
.prob{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:12px;margin:12px 0;padding:11px 13px;box-shadow:var(--shadow)}
.prob>header{display:flex;gap:8px;align-items:flex-start}
.prob h4{margin:0;font-size:1rem;flex:1;line-height:1.3}
.prob .meta{display:block;font-size:.74rem;color:var(--mute);font-weight:500;margin-top:2px}
.given{background:var(--blue-soft);border-radius:8px;padding:8px 10px;margin-top:8px;font-size:.92rem}
.given b,.prob h5{display:block;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--blue);margin:0 0 2px}
.prob h5{color:var(--mute);margin:12px 0 2px}
.qa.sol{border:1px solid var(--line);margin:8px 0 0;font-size:.92rem}
.qa.sol .q{color:var(--blue);font-weight:600}
.qa.sol .ans{background:var(--blue-soft);border-top:1px dashed var(--line)}
.qa.sol .ans ol{margin:0;padding-left:1.3em}
.qa.prac{border:1.5px dashed var(--line);font-size:.92rem;margin:6px 0}
.qa.prac .tag{background:var(--blue-soft);color:var(--blue)}
.qa.prac .ans{background:var(--blue-soft);border-top:1.5px dashed var(--line)}
.qa.prac[data-st=k]{border-color:color-mix(in srgb,var(--green) 55%,var(--line))}.qa.prac[data-st=a]{border-color:color-mix(in srgb,var(--red) 55%,var(--line))}
/* predicted papers */
.predban{border:2px dashed var(--accent);border-radius:10px;padding:9px 12px;margin:22px 0 6px;background:var(--acc-soft)}
.predban b{display:block;color:var(--accent);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
.predban h3{margin:2px 0 4px;font-size:1.08rem}.predban p{margin:0;font-size:.86rem}
.paper.pred{border-style:dashed}
.paper .why{background:var(--acc-soft);border-radius:6px;padding:6px 9px;font-size:.84rem;margin:4px 0 6px}
.paper .why b{color:var(--accent)}
.qa.mock .scn{margin-bottom:4px}
.orwk{font-size:.75rem;color:var(--mute);font-family:inherit;font-weight:400}
/* must-know */
.mkl{list-style:none;margin:0;padding:0;columns:2 340px;column-gap:18px;font-size:.8rem;line-height:1.32}
.mkl li{break-inside:avoid;display:grid;grid-template-columns:20px 1fr;gap:6px;padding:2px 0;border-bottom:1px dotted var(--line)}
.mkl button{width:17px;height:17px;border-radius:4px;border:1.5px solid var(--mute);background:var(--panel);padding:0;cursor:pointer;margin-top:1px;font-size:11px;line-height:1;color:#fff}
.mkl button.on{background:var(--green);border-color:var(--green)}.mkl button.on::after{content:"\2713"}
.mkl li.on span{color:var(--mute)}
/* ---------- misc ---------- */
.totop{position:fixed;right:14px;bottom:24px;z-index:19;width:42px;height:42px;border-radius:50%;border:1px solid var(--line);
background:var(--panel);color:var(--accent);font-size:1.2rem;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.12);
opacity:0;pointer-events:none;transition:opacity .2s}
.totop.show{opacity:1;pointer-events:auto}
@media (max-width:1099px){.totop{bottom:76px}}
.toast{position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:8px 14px;
border-radius:10px;font-size:.88rem;z-index:60;display:none}
@media (max-width:640px){.qa.pool .q .tag{display:none}.hero h1{font-size:1.45rem}.wkhead h2{font-size:1.22rem}.card{padding:12px}main{padding:0 12px 110px}
.marks{grid-template-columns:1fr}.qa .q{padding:9px 10px}.paper{padding:12px}.bar-in{padding:7px 12px}}
@media print{
 body{background:#fff;font-size:9.2pt;line-height:1.38}
 .bar,.tabbar,.wkmenu,.focus,.totop,.toast,.noprint,#start,#cmp,#probs,.predsec,.mkl button,.toc,.afoot,.pills,.done,.back,.panhint,.st8,.tap,.prog,h3.sh .n{display:none!important}
 .opts{grid-template-columns:1fr 1fr;gap:0 12px}
 .view{display:block!important}main{max-width:none;padding:0}*{box-shadow:none!important;text-shadow:none!important}
 .ans{display:block!important;padding:5px 9px}.qa .q{padding:5px 9px}.qa{margin:5px 0;break-inside:auto;box-shadow:none}
 .q{break-inside:avoid;break-after:avoid}
 .view{break-before:page}.wkhead{padding-top:0}
 .card{break-inside:auto;padding:8px 10px;margin:8px 0;box-shadow:none}
 .fold-b{display:none!important}.fold-b[data-k=how],.fold-b[data-k=calc]{display:block!important}
 .fold-b[data-k=how]>:not(.dia){display:none!important}
 .dia{break-inside:avoid;padding:3px;margin:4px auto 6px;max-width:120mm}.dia svg{max-height:46mm;min-width:0!important}.dia figcaption{font-size:7.5pt;margin-top:1px}
 .lay li{margin:0}table{font-size:8.6pt}th,td{padding:3px 5px}
 h3.sh{margin:12px 0 6px}.card h4{break-after:avoid}.paper{box-shadow:none;padding:6px 10px;margin:8px 0}.paper>header{break-after:avoid}.qa.mock{break-inside:avoid}
 .fgrid{grid-template-columns:1fr 1fr}.qa.pool .ans,.qa.mock .ans{background:#f6fbf7}
 :root{--shadow:none!important;--bg:#fff;--panel:#fff;--d-box:#fff7ed;--d-line:#b45309;--d-box2:#eff6ff;--d-line2:#1d4ed8;--d-box3:#ecfdf3;
 --d-line3:#15803d;--d-ink:#1c1b19;--d-mute:#78716c}
}
@page{size:A4;margin:11mm 10mm}
body.poolonly .cards-sec,body.poolonly #mock,body.poolonly #cmp,body.poolonly #probs,body.poolonly #sheet,body.poolonly .summary{display:none!important}
"""

JS = r"""
(function(){
const KEY='bda-final-v3', EXAM=new Date(2026,9,13);
const D=document.documentElement,B=document.body,$=(s,r)=>(r||document).querySelector(s),$$=(s,r)=>[...(r||document).querySelectorAll(s)];
const blank=()=>({m:{},c:{},s:{},y:{},v:null});
let S=blank();
try{const r=JSON.parse(localStorage.getItem(KEY)||'null');if(r&&typeof r==='object')S=Object.assign(blank(),r)}catch(e){}
let saveT=0;const save=()=>{clearTimeout(saveT);saveT=setTimeout(()=>{try{localStorage.setItem(KEY,JSON.stringify(S))}catch(e){}},120)};
if(location.search.includes('pool'))B.classList.add('poolonly');
try{history.scrollRestoration='manual'}catch(e){}
/* theme */
try{const t=localStorage.getItem('bda-theme');if(t)D.dataset.theme=t}catch(e){}
$('#theme').onclick=()=>{const dark=D.dataset.theme?D.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
 D.dataset.theme=dark?'light':'dark';try{localStorage.setItem('bda-theme',D.dataset.theme)}catch(e){}};
$('#all').onclick=()=>{B.classList.toggle('all');$('#all').classList.toggle('on')};
const toast=(t)=>{const el=$('#toast');el.textContent=t;el.style.display='block';clearTimeout(toast.t);toast.t=setTimeout(()=>el.style.display='none',1800)};
/* countdown */
(()=>{const d=Math.ceil((EXAM-new Date(new Date().toDateString()))/864e5);const el=$('#count');
 if(el)el.textContent=d>1?d+' days to go':d===1?'Exam tomorrow':d===0?'Exam day':'Exam done'})();
/* ---------- progress ---------- */
const isDone=(el)=>el.classList.contains('card')?!!S.c[el.id]:S.m[el.dataset.id]==='k';
const itemDone=(el)=>el.classList.contains('card')?!!S.c[el.id]:el.dataset.id?S.m[el.dataset.id]==='k':false;
function mark(id,m){if(S.m[id]===m)delete S.m[id];else S.m[id]=m;save();paint()}
function setBar(el,f){const i=$('i',el);if(i)i.style.width=(100*f).toFixed(1)+'%'}
function stats(w){const sel=w?'[data-w="'+w+'"]':'';
 const P=$$('.qa.pool'+sel),C=$$('.card'+sel),R=$$('.qa.drill'+sel);
 const p=P.filter(isDone).length,c=C.filter(isDone).length,r=R.filter(isDone).length;
 return{p,P:P.length,c,C:C.length,r,R:R.length,f:(p+c+r)/Math.max(1,P.length+C.length+R.length)}}
function paint(){
 $$('[data-id]').forEach(el=>{const s=S.m[el.dataset.id]||'';if(el.dataset.st!==s)el.dataset.st=s});
 $$('.card').forEach(el=>el.classList.toggle('isdone',!!S.c[el.id]));
 $$('.toc li[data-c]').forEach(li=>li.classList.toggle('isdone',!!S.c[li.dataset.c]));
 $$('.prog').forEach(el=>{const s=stats(el.dataset.pw==='all'?'':el.dataset.pw);setBar($('.pbar',el),s.f);
  $('.ptxt',el).textContent='Pool '+s.p+'/'+s.P+' · Cards '+s.c+'/'+s.C+' · Drills '+s.r+'/'+s.R});
 $$('.wpct').forEach(e=>e.textContent=Math.round(100*stats(e.dataset.wp).f)+'%');
 const o=stats('');setBar($('.obar'),o.f);$$('.opct').forEach(e=>e.textContent=Math.round(100*o.f)+'%');
 $$('.sess').forEach(el=>{const ids=(el.dataset.items||'').split(' ').filter(Boolean);let f;
  if(ids.length){const k=el.dataset.kind;f=ids.filter(id=>k==='card'?S.c[id]:S.m[id]==='k').length/ids.length}
  else f=S.s[el.dataset.sid]?1:0;
  el.classList.toggle('full',f>=1);setBar($('.sbar',el),f)});
 $$('[data-tick]').forEach(b=>{const on=!!S.s[b.dataset.tick];b.classList.toggle('on',on);const li=b.closest('.mkl li');if(li)li.classList.toggle('on',on)});
 $$('.lk[href]').forEach(a=>{const t=document.getElementById(a.getAttribute('href').slice(1));a.classList.toggle('isdone',!!t&&itemDone(t))});
 let next=null;
 $$('.blk').forEach(el=>{const ids=(el.dataset.items||'').split(' ').filter(Boolean);
  const d=ids.filter(id=>{const t=document.getElementById(id);return t&&itemDone(t)}).length;
  const f=ids.length?d/ids.length:0,full=!!S.s[el.dataset.sid];
  el.classList.toggle('full',full);setBar($('.bp',el),full?1:f);el.classList.remove('isnext');if(!next&&!full)next=el});
 if(next)next.classList.add('isnext');
 const nb=$('#nextbox');if(nb){if(next){$('.nt',nb).textContent=$('.bt',next).textContent;
  const tk=$('.bk',next).textContent;$('.ns',nb).textContent=$('.bm',next).textContent+' · '+(tk.length>150?tk.slice(0,147)+'…':tk);
  nb.dataset.sid=next.dataset.sid;$('#nextopen').setAttribute('href','#'+next.id)}else{$('.nt',nb).textContent='Every block done';$('.ns',nb).textContent='Run the Again pile, the must-know list and the formula sheet until the exam.';nb.dataset.sid=''}}
 $$('[data-bank]').forEach(e=>{const els=$$(e.dataset.bank);e.textContent=els.filter(x=>S.m[x.dataset.id]==='k').length+'/'+els.length+' known'});
 const ag=Object.values(S.m).filter(v=>v==='a').length;$$('.againn').forEach(e=>e.textContent=ag);
 const rs=$('#resume');if(rs){const v=S.v&&S.v!=='start'&&document.getElementById(S.v);
  rs.hidden=!v;if(v)$('a',rs).textContent=v.dataset.title||S.v,$('a',rs).setAttribute('href','#'+S.v)}
}
/* ---------- folds ---------- */
function centerPans(r){$$('.pan',r).forEach(p=>{if(p.scrollWidth>p.clientWidth&&!p.dataset.c){p.scrollLeft=(p.scrollWidth-p.clientWidth)/2;p.dataset.c=1}})}
function setFold(card,k,on){const p=$('.pill[data-k="'+k+'"]',card),b=$('.fold-b[data-k="'+k+'"]',card);
 if(p)p.classList.toggle('on',on);if(b){b.classList.toggle('open',on);if(on)centerPans(b)}}
/* ---------- bank filters ---------- */
const FL={cmp:{w:'',l:''},probs:{w:'',l:''}};
function applyF(v){const f=FL[v],sec=document.getElementById(v);if(!sec)return;let n=0;
 $$('[data-fw]',sec).forEach(b=>b.classList.toggle('on',b.dataset.fw===f.w));$$('[data-fl]',sec).forEach(b=>b.classList.toggle('on',b.dataset.fl===f.l));
 $$('.bitem',sec).forEach(el=>{const ok=(!f.w||el.dataset.w===f.w)&&(!f.l||el.dataset.l===f.l);el.hidden=!ok;n+=ok});
 const sh=$('.shown',sec);if(sh)sh.textContent='Showing '+n}
/* ---------- router ---------- */
let cur=null;
function route(h){let el=h&&document.getElementById(h);if(!el)el=$('#start');
 const view=el.classList.contains('view')?el:el.closest('.view');if(!view)return;
 if(el!==view&&el.closest('[hidden]')&&FL[view.id]){FL[view.id]={w:'',l:''};applyF(view.id)}
 const dt=el.closest('details');if(dt)dt.open=true;
 if(cur&&cur!==view)S.y[cur.id]=scrollY;
 $$('.view').forEach(v=>v.classList.toggle('cur',v===view));cur=view;
 $$('[data-nav]').forEach(t=>t.classList.toggle('on',t.dataset.nav===view.id||(t.dataset.nav==='weeks'&&(view.classList.contains('week')||view.id==='cmp'||view.id==='probs'))));
 const fb=el.closest('.fold-b');if(fb)setFold(fb.closest('.card'),fb.dataset.k,true);
 if(el.classList.contains('qa'))el.classList.add('open');centerPans(view);
 if(el===view)scrollTo(0,S.y[view.id]||0);
 else{el.scrollIntoView({block:'start'});el.classList.remove('hl');void el.offsetWidth;el.classList.add('hl')}
 S.v=view.id;save();closeMenus();
 document.title=(view.dataset.title?view.dataset.title+' · ':'')+'BDA Final Guide'}
function go(h){history.pushState(null,'','#'+h);route(h)}
addEventListener('popstate',()=>route(location.hash.slice(1)));
let scT=0;addEventListener('scroll',()=>{$('#totop').classList.toggle('show',scrollY>700);
 clearTimeout(scT);scT=setTimeout(()=>{if(cur){S.y[cur.id]=scrollY;save()}},300)},{passive:true});
$('#totop').onclick=()=>scrollTo({top:0,behavior:'smooth'});
const closeMenus=()=>$('#wkmenu').classList.remove('open');
/* ---------- clicks ---------- */
document.addEventListener('click',e=>{const t=e.target;
 const m=t.closest('[data-m]');if(m){const it=m.closest('[data-id]');if(it)mark(it.dataset.id,m.dataset.m);return}
 const f=t.closest('[data-focus]');if(f){e.preventDefault();startDeck(f.dataset.focus);return}
 if(t.closest('#focus'))return;
 const fb=t.closest('.fb');if(fb){const v=fb.closest('.view').id;if('fw' in fb.dataset)FL[v].w=fb.dataset.fw;else FL[v].l=fb.dataset.fl;applyF(v);return}
 const sw=t.closest('[data-setw]');if(sw){const [v,w]=sw.dataset.setw.split(':');FL[v]={w,l:''};applyF(v);go(v);return}
 const tick=t.closest('[data-tick]');if(tick){const k=tick.dataset.tick;S.s[k]?delete S.s[k]:S.s[k]=1;save();paint();return}
 const dn=t.closest('.done');if(dn){const id=dn.closest('.card').id;S.c[id]?delete S.c[id]:S.c[id]=1;save();paint();return}
 const pl=t.closest('.pill');if(pl){setFold(pl.closest('.card'),pl.dataset.k,!pl.classList.contains('on'));return}
 if(t.closest('#wkbtn')){$('#wkmenu').classList.toggle('open');return}
 if(t.closest('#reset')){if(confirm('Reset all progress (Known/Again marks, done ticks, sessions)?')){const v=S.v;S=blank();S.v=v;save();paint();toast('Progress reset')}return}
 const a=t.closest('a[href^="#"]');if(a){e.preventDefault();go(a.getAttribute('href').slice(1));return}
 const q=t.closest('.qa .q');if(q&&!t.closest('a,button')){q.parentNode.classList.toggle('open');centerPans(q.parentNode);return}
 if(!t.closest('#wkmenu'))closeMenus()});
document.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const q=e.target.closest&&e.target.closest('.qa .q');
 if(q&&!F){e.preventDefault();q.parentNode.classList.toggle('open')}}});
/* ---------- focus mode ---------- */
const FX=$('#focus');let F=null,figN=0;
function cloneAns(el){const c=el.cloneNode(true);$$('.afoot',c).forEach(x=>x.remove());
 $$('.dialink',c).forEach(a=>{const fig=document.getElementById(a.getAttribute('href').slice(1));if(!fig)return;
  const n=++figN,fc=fig.cloneNode(true);fc.removeAttribute('id');let h=fc.innerHTML;
  $$('[id]',fc).forEach(x=>{const id=x.id;h=h.split('id="'+id+'"').join('id="'+id+'-f'+n+'"').split('#'+id+')').join('#'+id+'-f'+n+')')});
  fc.innerHTML=h;(a.closest('p')||a).replaceWith(fc)});
 return c.innerHTML}
function itemOf(el){
 if(el.classList.contains('cmpc')){const t=$('.tw',el);
  return{id:el.dataset.id,kind:'cmp',tag:'Compare · W'+el.dataset.w,q:'<h4>'+$('h4',el).firstChild.textContent+'?</h4><p class="f-prompt">Say the key difference, then the scenario that points to each side.</p>',
   a:$('.one',el).outerHTML+$('.cue',el).outerHTML+(t?t.outerHTML:'')}}
 if(el.classList.contains('prac')){const pr=el.closest('.prob');
  return{id:el.dataset.id,kind:'prac',tag:'Slide problem · W'+el.dataset.w+' · '+$('.q .tag',el).textContent,
   q:'<p class="f-prompt">'+$('h4',pr).firstChild.textContent+'</p>'+$('.q .txt',el).innerHTML,a:cloneAns($('.ans',el))}}
 if(el.classList.contains('card')){const tr=$('.lay.trap',el),sc=$('.lay.scen',el);
  return{id:el.id,kind:'card',tag:'Card · W'+el.dataset.w,
   q:'<h4>'+$('h4',el).firstChild.textContent+'</h4><p class="f-prompt">Say the one-line answer, then the traps, then which scenarios point here.</p>',
   a:$('.one',el).outerHTML+tr.outerHTML+sc.outerHTML}}
 const tg=$('.q .tag',el),num=$('.q .num',el);
 return{id:el.dataset.id,kind:el.classList.contains('pool')?'pool':'drill',
  tag:(el.classList.contains('pool')?'Pool · W'+el.dataset.w+' · '+(num?num.textContent+' ':''):'Drill · W'+el.dataset.w+' · ')+tg.textContent,
  q:$('.q .txt',el).innerHTML,a:cloneAns($('.ans',el))}}
function deck(spec){const [k,v]=spec.split(':');let els=[],title='';
 if(k==='sess'){const s=$('.sess[data-sid="'+v+'"]');if(!s)return[[],''];title=$('.st',s).textContent;
  els=s.dataset.items.split(' ').filter(Boolean).map(id=>document.getElementById(id)).filter(Boolean)}
 else if(k==='next'){const nb=$('#nextbox');return nb&&nb.dataset.sid?deck('blk:'+nb.dataset.sid):[[],'']}
 else if(k==='pool'||k==='drill'){els=$$('.qa.'+k+'[data-w="'+v+'"]');title='Week '+v+(k==='pool'?' pool':' drills')}
 else if(k==='card'){els=$$('.card[data-w="'+v+'"]');title='Week '+v+' cards: traps and scenarios'}
 else if(k==='again'){els=$$('.qa.pool,.qa.drill,.cmpc,.qa.prac').filter(e=>S.m[e.dataset.id]==='a');title='Again pile'}
 else if(k==='blk'){const b=document.getElementById('blk'+v.slice(1));if(!b)return[[],''];title=$('.bt',b).textContent;
  const seen=new Set();els=b.dataset.items.split(' ').filter(Boolean).map(id=>document.getElementById(id)).filter(e=>e&&!seen.has(e)&&seen.add(e))}
 else if(k==='cmp'||k==='probs'){const sel=k==='cmp'?'.cmpc':'.qa.prac';const f=FL[k];
  if(v==='f'){els=$$(sel).filter(e=>(!f.w||e.dataset.w===f.w)&&(!f.l||(e.closest('.bitem')||e).dataset.l===f.l));title=(k==='cmp'?'Comparisons':'Slide problems')+(f.w?' · W'+f.w:'')+(f.l?' · '+f.l:'')}
  else{els=$$(sel).filter(e=>!v||v==='all'||e.dataset.w===v);title=(k==='cmp'?'Comparisons':'Slide problems')+(v&&v!=='all'?' · W'+v:'')}}
 else if(k==='src'){els=$$('.qa.pool').filter(e=>e.dataset.id.includes('-'+v+'-'));title='Every '+(v==='mcq'?'MCQ':'True/False')+', all weeks'}
 else if(k==='traps'){els=$$('.card');title='Every card: one-liner, traps, scenarios'}
 else if(k==='one'){title='Every topic in one line';
  return[$$('.card').filter(c=>!v||c.dataset.w===v).map(c=>({id:'o-'+c.id,kind:'one',tag:'One-liner · W'+c.dataset.w,
   q:'<h4>'+$('h4',c).firstChild.textContent+'</h4><p class="f-prompt">Say it in one line.</p>',a:$('.one',c).outerHTML})),title]}
 return[els.map(itemOf),title]}
function openFX(){FX.classList.add('open');B.classList.add('locked');closeMenus()}
function closeFX(){FX.classList.remove('open');B.classList.remove('locked');F=null;paint()}
function startDeck(spec){if(spec==='pick')return pick();const [items,title]=deck(spec);
 if(!items.length&&spec==='next'){const nb=$('#nextbox');if(nb&&nb.dataset.sid){go('blk'+nb.dataset.sid.slice(1));toast('This block is a paper or a sheet: work it on the page');return}}
 if(!items.length){toast(spec==='again'?'The Again pile is empty':'Nothing to drill here');return}
 F={map:new Map(items.map(i=>[i.id,i])),q:items.map(i=>i.id),title,total:items.length,known:0,again:0,rev:false};openFX();show()}
function pick(){F=null;openFX();$('#f-title').textContent='Focus mode';$('#f-count').textContent='';setBar($('.f-bar'),0);
 $('#f-btns').innerHTML='';$('#f-body').innerHTML=$('#pickt').innerHTML;
 const ag=Object.values(S.m).filter(v=>v==='a').length;$$('#f-body .againn').forEach(e=>e.textContent=ag);
 const nb=$('#nextbox'),nx=$('#f-body [data-focus="next"] small');if(nx)nx.textContent=nb&&nb.dataset.sid?$('.nt',nb).textContent:'All blocks done'}
function show(){const body=$('#f-body'),btns=$('#f-btns');$('#f-title').textContent=F.title;
 setBar($('.f-bar'),F.known/F.total);
 if(!F.q.length){$('#f-count').textContent='';body.innerHTML='<div class="f-end"><div class="big">&#10003;</div><h2>Session complete</h2><p>'+F.total+' items, '+F.again+' repeat'+(F.again===1?'':'s')+'.</p></div>';
  btns.innerHTML='<button class="fk" data-fx="pick">Another deck</button><button class="fa" data-fx="close" style="background:var(--panel);color:var(--ink);border-color:var(--line)">Close</button>';return}
 const it=F.map.get(F.q[0]);F.rev=false;
 $('#f-count').textContent=F.q.length+' left · '+F.known+' known';
 body.innerHTML='<div class="f-card" id="f-card"><span class="tag '+(it.kind==='pool'?'anal':it.kind==='drill'?'tf':it.kind==='cmp'?'tf':it.kind==='prac'?'mcq':'desc')+'">'+it.tag+'</span><div class="f-q">'+it.q+'</div><div class="f-a">'+it.a+'</div><p class="f-tap">Tap to reveal</p></div>';
 body.scrollTop=0;btns.innerHTML='<button class="fr" data-fx="rev">Show answer<kbd>space</kbd></button>'}
function reveal(){if(!F||F.rev||!F.q.length)return;F.rev=true;$('#f-card').classList.add('rev');centerPans($('#f-card'));
 $('#f-btns').innerHTML='<button class="fa" data-fx="a">Again<kbd>1</kbd></button><button class="fk" data-fx="k">Known<kbd>2</kbd></button>'}
function answer(ok){if(!F||!F.rev)return;const id=F.q.shift(),it=F.map.get(id);
 if(ok){F.known++;if(it.kind==='card')S.c[id]=1;else if(it.kind!=='one')S.m[id]='k'}
 else{F.again++;if(['pool','drill','cmp','prac'].includes(it.kind))S.m[id]='a';F.q.splice(Math.min(3,F.q.length),0,id)}
 save();show()}
FX.addEventListener('click',e=>{const b=e.target.closest('[data-fx]');
 if(b){const k=b.dataset.fx;k==='close'?closeFX():k==='pick'?pick():k==='rev'?reveal():answer(k==='k');return}
 const f=e.target.closest('[data-focus]');if(f){startDeck(f.dataset.focus);return}
 if(e.target.closest('#f-card')&&!e.target.closest('a'))reveal()});
document.addEventListener('keydown',e=>{if(!FX.classList.contains('open'))return;
 if(e.key==='Escape')closeFX();else if(e.key===' '||e.key==='Enter'){e.preventDefault();reveal()}
 else if(e.key==='1'||e.key==='j')answer(false);else if(e.key==='2'||e.key==='k')answer(true)});
/* ---------- boot ---------- */
applyF('cmp');applyF('probs');paint();route(location.hash.slice(1)||S.v||'start');
})();
"""

ICONS = {
    "plan": '<svg viewBox="0 0 24 24"><path d="M4 5h16M4 12h16M4 19h10"/><circle cx="19" cy="19" r="2"/></svg>',
    "weeks": '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/></svg>',
    "focus": '<svg viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 12l2 2 4-4"/></svg>',
    "mock": '<svg viewBox="0 0 24 24"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h8M9 17h6"/></svg>',
    "sheet": '<svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16M9 3v18"/></svg>',
}


def esc(s):
    return html.escape(html.unescape(str(s or "")), quote=False)


def words(s):
    return len(re.sub(r"<[^>]+>", " ", str(s or "")).split())


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


def ul(items, tag="ul"):
    return f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>"


def svg_inline(path):
    """Inline an SVG with a per-figure min width so its smallest text renders at >= 11 px on a phone."""
    svg = re.sub(r"<\?xml[^>]*>", "", (ROOT / path).read_text()).strip()
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    sizes = [float(x) for x in re.findall(r"font-size[:=]\"?\s*([\d.]+)", svg)] or [12]
    minw = math.ceil(float(vb.group(1)) * 11 / min(sizes)) if vb else 640
    return svg.replace("<svg ", f'<svg style="--minw:{minw}px" ', 1)


def figure(file, caption="", fid=""):
    if not file or not (ROOT / file).exists():
        return ""
    idattr = f' id="{fid}"' if fid else ""
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return (f'<figure class="dia"{idattr}><div class="pan">{svg_inline(file)}</div>'
            f'<div class="panhint">swipe sideways to see the whole diagram</div>{cap}</figure>')


def marks_btns():
    return '<span class="mk"><button data-m="a">Again</button><button data-m="k">Known</button></span>'


# ---------------------------------------------------------------- pool

def pool_minutes(p):
    return 0.5 + (words(p["q"]) + words(p["a"]) + words(p.get("code")) + words(" ".join(p.get("options") or []))) / 90


def dialink(t):
    return (f'<p class="dl"><a class="dialink" href="#fig-{t["id"]}">Diagram for this answer: '
            f'on the card &ldquo;{esc(t["title"])}&rdquo; &#8599;</a></p>')


def pool_answer(p, t):
    """The verified answer, with any copy of the card's diagram swapped for a link to it."""
    a = p["a"]
    if t and t.get("diagram"):
        f = t["diagram"]["file"]
        pat = r'<img[^>]*src="' + re.escape(f) + r'"[^>]*>'
        if re.search(pat, a):
            a = re.sub(pat, dialink(t).replace('<p class="dl">', "").replace("</p>", ""), a)
        elif re.search(r"\b(draw|diagram|sketch|illustrat)", p["q"], re.I) and "<svg" not in a and "diagrams/" not in a:
            a = dialink(t) + a
    return a


def pool_item(d, p, tops):
    w = d["week"]
    t = tops.get(p.get("topic"))
    pid = f"p{w}-{SRC_CLASS[p['src']]}-{slug(p.get('n', ''))}"
    p["_id"] = pid
    opts = ('<ul class="opts">' + "".join(f"<li>{o}</li>" for o in p["options"]) + "</ul>") if p.get("options") else ""
    cd = f"<pre><code>{esc(p['code'])}</code></pre>" if p.get("code") else ""
    link = f'<a class="tocard" href="#{t["id"]}">Card: {esc(t["title"])} &rarr;</a>' if t else "<span></span>"
    return (f'<article class="qa pool" id="{pid}" data-id="{pid}" data-w="{w}">'
            f'<div class="q" tabindex="0"><span class="st8"></span><span class="num">{esc(p.get("n", ""))}</span>'
            f'<div class="txt">{p["q"]}{opts}{cd}</div><span class="tag {SRC_CLASS[p["src"]]}">{SRC_SHORT[p["src"]]}</span></div>'
            f'<div class="ans">{pool_answer(p, t)}<div class="afoot">{link}{marks_btns()}</div></div></article>')


def pool_items_sorted(d):
    return sorted(d["pool"], key=lambda p: SRC_ORDER.index(p["src"]))


def pool_section(d, tops):
    w = d["week"]
    out = [f'<h3 class="sh" id="w{w}-pool">Pool questions <span class="n">{len(d["pool"])} from the slides · '
           "tap a question for its answer, then mark it</span></h3>"]
    last = None
    for p in pool_items_sorted(d):
        if p["src"] != last:
            last = p["src"]
            n = sum(1 for x in d["pool"] if x["src"] == last)
            out.append(f'<h4 class="grp" id="w{w}-pool-{SRC_CLASS[last]}">{last} · {n}</h4>')
        out.append(pool_item(d, p, tops))
    return "".join(out)


# ---------------------------------------------------------------- cards

def contrast_tables(cs):
    out = []
    for c in cs:
        head = c.get("head")
        h = "<tr>" + "".join(f"<th>{x}</th>" for x in head) + "</tr>" if head else ""
        rows = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in c["rows"])
        out.append(f'<div class="tw"><table>{h}{rows}</table></div>')
    return "".join(out)


def drill_items(t, w):
    rnd = random.Random(t["id"])
    out = []
    for i, q in enumerate(t["questions"]):
        opts = ""
        if q.get("options"):
            o = list(q["options"])
            correct = o[0]
            rnd.shuffle(o)
            letter = "abcdefgh"[o.index(correct)]
            opts = '<ul class="opts">' + "".join(f"<li>({'abcdefgh'[j]}) {x}</li>" for j, x in enumerate(o)) + "</ul>"
            a = f"<b>({letter}) {correct}</b><br>{q['a']}"
        else:
            a = q["a"]
        did = f"d-{t['id']}-{i}"
        q["_id"] = did
        out.append(f'<div class="qa drill" id="{did}" data-id="{did}" data-w="{w}"><div class="q" tabindex="0">'
                   f'<span class="st8"></span><div class="txt">{q["q"]}{opts}</div>'
                   f'<span class="tag">{FORMAT_NAMES.get(q["format"], q["format"])}</span></div>'
                   f'<div class="ans">{a}<div class="afoot"><span class="fmt">Drill</span>{marks_btns()}</div></div></div>')
    return "".join(out)


def card(t, w, pool_refs):
    calc = t.get("calculation")
    sc = "".join(f"<tr><td>{s['cue']}</td><td>{s['answer']}</td></tr>" for s in t["scenarios"])
    a = t["answers"]
    folds = [
        ("facts", f"Facts {len(t['facts'])}", "", f'<div class="lay"><h5>Facts</h5>{ul(t["facts"])}</div>'),
        ("how", "How it works" + (" + diagram" if t.get("diagram") else ""), "",
         (figure(t["diagram"]["file"], t["diagram"].get("caption", ""), f"fig-{t['id']}") if t.get("diagram") else "")
         + f'<div class="lay"><h5>How it works</h5>{ul(t["mechanism"], "ol")}</div>'),
        ("why", "Why · pros · limits", "", f'<div class="lay"><h5>Why · pros · limits</h5>{ul(t["why"])}</div>'),
        ("cmp", "Compare", "", f'<div class="lay"><h5>Compare</h5>{contrast_tables(t["contrasts"])}</div>'),
    ]
    if calc:
        folds.append(("calc", "Maths", "calc",
                      f'<div class="lay calc"><h5>Calculation</h5>{calc["example"]}'
                      f'<p><b>Step by step</b></p>{ul(calc["steps"], "ol")}'
                      f'<p><b>Variants</b></p>{ul(calc["variants"])}</div>'))
    folds.append(("marks", "3 &amp; 5-mark answers", "",
                  f'<div class="lay"><h5>Model answers (the 1-mark answer is the one-liner above)</h5><div class="marks">'
                  f'<b>3 marks</b><div>{a["3"]}</div><b>5 marks</b><div>{a["5"]}</div></div></div>'))
    folds.append(("drill", f"Drill {len(t['questions'])}", "drl",
                  f'<div class="lay"><h5>Practise this topic in {len(t["questions"])} formats</h5>{drill_items(t, w)}</div>'))
    pills = "".join(f'<button class="pill {c}" data-k="{k}">{lab}</button>' for k, lab, c, _ in folds)
    bodies = "".join(f'<div class="fold-b" data-k="{k}">{body}</div>' for k, _, _, body in folds)
    refs = pool_refs.get(t["id"], [])
    back = ('<div class="back"><span>In the pool:</span>' + "".join(
        f'<a href="#{p["_id"]}">{SRC_SHORT[p["src"]]} {esc(p.get("n", ""))}</a>' for p in refs) + "</div>") if refs else \
        '<div class="back"><span>No pool question on this topic; the drills cover it.</span></div>'
    cl = EXTRA["cmp_by_card"].get(t["id"], [])
    if cl:
        back += ('<div class="back"><span>Compare:</span>' + "".join(
            f'<a href="#c-{c["id"]}">{esc(short(cmp_title(c), 40))}</a>' for c in cl) + "</div>")
    pl = EXTRA["prob_by_card"].get(t["id"], [])
    if pl:
        back += ('<div class="back"><span>Slide problems:</span>' + "".join(
            f'<a href="#x-{x["id"]}">{esc(short(x["title"], 40))}</a>' for x in pl) + "</div>")
    return (f'<article class="card" id="{t["id"]}" data-w="{w}"><header><h4>{esc(t["title"])}'
            f'<span class="meta">Week {w} · {len(refs)} pool question{"" if len(refs) == 1 else "s"}</span></h4>'
            f'<button class="done">Done</button></header>'
            f'<div class="one"><b class="l">Answer in one line</b>{a["1"]}</div>'
            f'<div class="lay trap"><h5>Traps</h5>{ul(t["traps"])}</div>'
            f'<div class="lay scen"><h5>Spot it in a scenario</h5><div class="tw"><table class="sc">'
            f'<tr><th>If the question describes…</th><th>Answer</th></tr>{sc}</table></div></div>'
            f'<div class="pills">{pills}</div>{bodies}{back}</article>')


def card_minutes(t):
    return 1 + (words(t["answers"]["1"]) + words(" ".join(t["traps"]))
                + sum(words(s["cue"]) + words(s["answer"]) for s in t["scenarios"])) / 90


def drill_minutes(q):
    return 0.3 + (words(q["q"]) + words(q["a"]) + words(" ".join(q.get("options") or []))) / 110


# ---------------------------------------------------------------- week view

def week_view(d, i):
    w = d["week"]
    tops = {t["id"]: t for t in d["topics"]}
    pool_html = pool_section(d, tops)  # assigns p["_id"]
    refs = {}
    for p in pool_items_sorted(d):
        refs.setdefault(p.get("topic"), []).append(p)
    cards_html = "".join(card(t, w, refs) for t in d["topics"])
    groups = []
    for s in SRC_ORDER:
        n = sum(1 for p in d["pool"] if p["src"] == s)
        if n:
            groups.append(f'<a class="mini" href="#w{w}-pool-{SRC_CLASS[s]}">{SRC_SHORT[s]} {n}</a>')
    cardlist = "".join(
        f'<li data-c="{t["id"]}"><a href="#{t["id"]}">{esc(t["title"])} <span>{len(refs.get(t["id"], []))} pool</span></a></li>'
        for t in d["topics"])
    ndr = sum(len(t["questions"]) for t in d["topics"])
    return (f'<section class="view week" id="w{w}" data-title="Week {w}: {esc(d["title"])}">'
            f'<header class="wkhead"><small>Week {w} · Chapter {i}</small><h2>{esc(d["title"])}</h2>'
            f'<div class="prog" data-pw="{w}"><div class="pbar"><i></i></div><span class="ptxt"></span></div>'
            f'<p class="summary">{d["summary"]}</p></header>'
            f'<nav class="toc" aria-label="In this week">'
            f'<div class="row"><span class="lbl">Flash</span>'
            f'<button class="mini" data-focus="pool:{w}">Pool {len(d["pool"])}</button>'
            f'<button class="mini" data-focus="card:{w}">Cards {len(d["topics"])}</button>'
            f'<button class="mini" data-focus="drill:{w}">Drills {ndr}</button>'
            f'<button class="mini" data-focus="one:{w}">One-liners</button></div>'
            f'<div class="row"><span class="lbl">Pool</span>{"".join(groups)}</div>'
            f'<div class="row"><span class="lbl">Cards</span><a class="mini" href="#w{w}-cards">all {len(d["topics"])}</a></div>'
            f'<ol>{cardlist}</ol></nav>'
            + pool_html
            + f'<div class="cards-sec"><h3 class="sh" id="w{w}-cards">Topic cards <span class="n">{len(d["topics"])} topics · '
              "answer, traps and scenarios first; tap a pill for the rest</span></h3>"
            + cards_html + "</div></section>")


# ---------------------------------------------------------------- mock & sheet

ROMAN = re.compile(r"(?:^|(?<=\s)|(?<=>))(i|ii|iii|iv)\)\s+")


def split_parts(s):
    """Put i) ii) iii) iv) on their own lines. Text is unchanged; only structure is added."""
    ms = list(ROMAN.finditer(s))
    if [m.group(1) for m in ms] != ["i", "ii", "iii", "iv"]:
        return s, False
    lead = re.sub(r"(\s*<br\s*/?>\s*)+$", "", s[:ms[0].start()]).strip()
    items = []
    for k, m in enumerate(ms):
        end = ms[k + 1].start() if k + 1 < len(ms) else len(s)
        items.append(re.sub(r"(\s*<br\s*/?>\s*)+$", "", s[m.end():end]).strip())
    lis = "".join(f"<li><b>{lab})</b><div>{it}</div></li>" for lab, it in zip(["i", "ii", "iii", "iv"], items))
    return (f"<div>{lead}</div>" if lead else "") + f'<ol class="rom">{lis}</ol>', True


def mock(chs, pred_html=""):
    out = ['<section class="view" id="mock" data-title="Mock paper"><header class="wkhead"><small>Practice</small>'
           "<h2>Mock final paper</h2>"
           '<p class="summary">One 10-mark question per chapter, in the shape of the October 2026 Data Mining final from '
           "the same department: a short scenario, then short parts. Answer either the main pair or the OR pair. "
           "Tap a part for its model answer.</p></header>"
           + ('<div class="toc noprint"><div class="row"><span class="lbl">Papers</span><a class="mini" href="#mock-q1">Mock (6 chapters)</a>'
              '<a class="mini" href="#pred-A">Predicted A</a><a class="mini" href="#pred-B">Predicted B</a></div></div>' if pred_html else "")]
    nsplit = 0
    for i, d in enumerate(chs, 1):
        m = d["mock"]
        out.append(f'<div class="paper" id="mock-q{i}"><header><b>Question {i}</b><span>Week {d["week"]} · 10 marks</span></header>')
        for keys in (("a", "b"), ("or_a", "or_b")):
            if keys[0] not in m:
                continue
            if keys[0] == "or_a":
                out.append('<div class="or">OR</div>')
            for k in keys:
                p = m[k]
                q, s1 = split_parts(p["q"])
                a, s2 = split_parts(p["a"])
                nsplit += s1 + s2
                out.append(f'<div class="qa mock"><div class="q" tabindex="0"><div class="pl">({k[-1]})'
                           f'<span>{p["marks"]} marks <span class="tap">· tap for answer</span></span></div>'
                           f'<div class="txt">{q}</div></div><div class="ans">{a}</div></div>')
        out.append("</div>")
    out.append(pred_html + "</section>")
    return "".join(out), nsplit


def sheet(chs, pred=None):
    out = ['<section class="view" id="sheet" data-title="Sheet"><header class="wkhead"><small>Last ten minutes</small>'
           "<h2>Must-know and formula sheet</h2><p class=\"summary\">The must-know list first, then every formula from weeks 5–10. "
           "The one-line answer for each topic sits at the top of its card; flash all 36 below.</p></header>"
           + (must_html(pred) if pred and pred.get("must_know") else "")
           + '<div class="toc noprint" id="sheet-formulas"><div class="row"><span class="lbl">Formulas</span>'
           + "".join(f'<a class="mini" href="#sheet-w{d["week"]}">W{d["week"]}</a>' for d in chs)
           + '<a class="mini" href="#sheet-one">One-liners</a></div></div>']
    for d in chs:
        fs = d.get("formulas", [])
        if not fs:
            continue
        out.append(f'<h3 class="sh" id="sheet-w{d["week"]}">Week {d["week"]} <span class="n">{esc(d["title"])} · {len(fs)}</span></h3><div class="fgrid">')
        for f in fs:
            note = f'<div class="fn">{f["note"]}</div>' if f.get("note") else ""
            out.append(f'<div class="fcard"><b>{f["name"]}</b><div class="fx">{f["formula"]}</div>{note}</div>')
        out.append("</div>")
    out.append('<h3 class="sh" id="sheet-one">Every topic in one line <span class="n">36 one-liners, kept on the cards</span></h3>'
               '<div class="btnrow noprint" style="margin-top:0"><button class="btn sm" data-focus="one">Flash all 36 one-liners</button></div>'
               '<ul class="toplist noprint" style="margin-top:10px">')
    for d in chs:
        for t in d["topics"]:
            out.append(f'<li><span>W{d["week"]}</span><a href="#{t["id"]}">{esc(t["title"])}</a></li>')
    out.append("</ul></section>")
    return "".join(out)


# ---------------------------------------------------------------- plan

def split_even(items, mins, target=SESSION_TARGET):
    total = sum(mins)
    k = max(1, round(total / target))
    if total / k > 25:
        k += 1
    groups, cur, acc, cut = [], [], 0, total / k
    for it, m in zip(items, mins):
        if cur and acc + m / 2 > cut * (len(groups) + 1) and len(groups) < k - 1:
            groups.append(cur)
            cur = []
        cur.append((it, m))
        acc += m
    groups.append(cur)
    return groups


def build_plan(chs):
    sessions = []  # dict(kind,title,scope,min,items,href,focus)
    for d in chs:
        w = d["week"]
        ps = pool_items_sorted(d)
        gs = split_even(ps, [pool_minutes(p) for p in ps])
        for j, g in enumerate(gs, 1):
            kinds = []
            for p, _ in g:
                if SRC_SHORT[p["src"]] not in kinds:
                    kinds.append(SRC_SHORT[p["src"]])
            sessions.append(dict(kind="pool", phase="Pool questions", title=f"Week {w} pool" + (f" · {j} of {len(gs)}" if len(gs) > 1 else ""),
                                 scope=f"{len(g)} questions · {', '.join(kinds)}", min=sum(m for _, m in g),
                                 items=[p["_id"] for p, _ in g], href=g[0][0]["_id"]))
    for d in chs:
        w = d["week"]
        mins = [card_minutes(t) for t in d["topics"]]
        sessions.append(dict(kind="card", phase="Traps and scenarios", title=f"Week {w} traps + scenarios",
                             scope=f"{len(d['topics'])} cards: one-liner, traps, scenario table", min=sum(mins),
                             items=[t["id"] for t in d["topics"]], href=f"w{w}-cards"))
    for d in chs:
        w = d["week"]
        qs = [(t, q) for t in d["topics"] for q in t["questions"]]
        gs = split_even(qs, [drill_minutes(q) for _, q in qs])
        for j, g in enumerate(gs, 1):
            topics = []
            for (t, _q), _m in g:
                if t["title"] not in topics:
                    topics.append(t["title"])
            sessions.append(dict(kind="drill", phase="Drills", title=f"Week {w} drills" + (f" · {j} of {len(gs)}" if len(gs) > 1 else ""),
                                 scope=f"{len(g)} drills · {len(topics)} topics", min=sum(m for _, m in g),
                                 items=[q["_id"] for (_t, q), _m in g], href=g[0][0][1]["_id"]))
    for j, (a, b) in enumerate([(1, 2), (3, 4), (5, 6)], 1):
        sessions.append(dict(kind="mock", phase="Mock paper", title=f"Mock paper Q{a}–Q{b}", scope="closed book, then check the model answers",
                             min=20, items=[], href=f"mock-q{a}"))
    sessions.append(dict(kind="sheet", phase="Exam morning", title="Formula sheet + Again pile",
                         scope="52 formulas, then every item marked Again", min=20, items=[], href="sheet"))
    for i, s in enumerate(sessions, 1):
        s["sid"] = f"s{i}"
        s["raw"] = s["min"]
        s["min"] = max(15, min(25, round(s["min"])))
    # days: pool + cards on day 1, drills + mock on day 2, sheet on exam morning
    days = [("Day 1 · 11 October", "pool questions, then traps and scenarios", [s for s in sessions if s["kind"] in ("pool", "card")]),
            ("Day 2 · 12 October", "drills, then the mock paper", [s for s in sessions if s["kind"] in ("drill", "mock")]),
            ("Exam morning · 13 October", "a last pass", [s for s in sessions if s["kind"] == "sheet"])]
    return sessions, days


def plan_html(days):
    out = []
    for name, what, ss in days:
        phase = None
        tot = sum(s["min"] for s in ss)
        out.append(f'<div class="day"><b>{name}</b><span>{len(ss)} sessions · {tot // 60} h {tot % 60:02d} min · {what}</span></div><ol class="plan">')
        for s in ss:
            if s["phase"] != phase:
                phase = s["phase"]
                out.append(f'<li class="ph">{phase}</li>')
            act = (f'<button class="mini" data-focus="sess:{s["sid"]}">&#9654; Focus</button>' if s["items"]
                   else f'<button class="mini" data-tick="{s["sid"]}">Tick</button>')
            out.append(f'<li class="sess" data-sid="{s["sid"]}" data-kind="{s["kind"]}" data-items="{" ".join(s["items"])}">'
                       f'<span class="sdot"></span><a class="sm" href="#{s["href"]}"><span class="st">{s["title"]}</span>'
                       f'<span class="sc">{s["scope"]}</span></a><span class="sr"><span class="smin">{s["min"]} min</span>{act}</span>'
                       f'<span class="sbar"><i></i></span></li>')
        out.append("</ol>")
    return "".join(out)


def start_view(chs, days, nsess, total_min, dp=None, pred=None, nc=0, nx=0):
    npool = sum(len(d["pool"]) for d in chs)
    today, morn, tt, tm = dp or ([], [], 0, 0)
    wk = "".join(
        f'<a class="wk" href="#w{d["week"]}"><small>Week {d["week"]}</small><b>{esc(d["title"])}</b>'
        f'<div class="prog" data-pw="{d["week"]}"><div class="pbar"><i></i></div><span class="ptxt"></span></div></a>'
        for d in chs)
    return (
        '<section class="view" id="start" data-title="Start here">'
        '<header class="hero"><h1>CSE 4345 Big Data Analytics</h1>'
        '<p class="sub">Final exam guide · Weeks 5–10 · 13 October 2026</p><span class="count" id="count"></span></header>'
        '<div class="next" id="nextbox"><small>Next up</small><div class="nt"></div><div class="ns"></div>'
        '<div class="btnrow"><button class="btn" data-focus="next">Start in focus mode</button>'
        '<a class="btn ghost" href="#plan" id="nextopen">Open the block</a></div>'
        '<p class="resume" id="resume" hidden>Last place: <a href="#start"></a></p></div>'
        '<div class="prog" data-pw="all" style="margin:10px 0 0"><div class="pbar"><i></i></div><span class="ptxt"></span></div>'
        f'<h2 class="sec" id="plan">Today: {len(today)} blocks · {tt // 60} h {tt % 60:02d} min</h2>'
        '<p class="fine" style="margin-top:0">Work top to bottom. Each block lists its minutes, the task, and links to the exact cards, '
        'pool questions, comparisons (VS) and slide problems (CALC). &#9654; Focus flashes every linked item; tick the block when its task is done.</p>'
        '<div class="honest"><b>Still covers all 6 weeks.</b> The order follows how heavily the slides stress each topic (evidence below), '
        'but every week gets its own blocks, W9 and W10 included, and the MCQ/TF sweep runs over all six. A prediction is a guess: '
        'nothing is dropped because of it.</div>'
        + (emphasis_html(pred) if pred else "")
        + f'<ol class="blks">{"".join(today)}</ol>'
        + (f'<div class="day"><b>Exam morning · 13 October</b><span>{len(morn)} blocks · {tm} min</span></div><ol class="blks">{"".join(morn)}</ol>' if morn else "")
        + f'<details class="fold" id="fullplan"><summary>Backup: the full-coverage plan, {nsess} sessions (every pool question, card and drill)</summary><div>'
        f'<p class="fine">About {total_min // 60}&frac12; hours, ordered by exam yield: all {npool} pool '
        'questions first, then each card\'s traps and scenarios, then drills. '
        'A session ticks itself when every item in it is Known or Done.</p>'
        + plan_html(days) + '</div></details>'
        + '<h2 class="sec">Banks</h2><div class="wkgrid">'
        f'<a class="wk" href="#cmp"><small>All weeks</small><b>Comparisons · {nc} X vs Y pairs</b><span class="fine">table, key difference, scenario cue</span></a>'
        f'<a class="wk" href="#probs"><small>All weeks</small><b>Slide problems · {nx} worked examples</b><span class="fine">given numbers, steps, one-step variants</span></a>'
        '<a class="wk" href="#pred-A"><small>Mock</small><b>Two predicted papers</b><span class="fine">with the evidence for each question</span></a></div>'
        + '<h2 class="sec">Weeks</h2><div class="wkgrid">' + wk + "</div>"
        '<h2 class="sec">How the page works</h2>'
        '<div class="legend"><span><i style="background:var(--yel)"></i>yellow = the answer</span>'
        '<span><i style="background:var(--red)"></i>red = traps</span><span><i style="background:var(--blue)"></i>blue = maths</span>'
        '<span><i style="background:var(--accent)"></i>amber spine = pool question</span>'
        '<span><i style="border:1.5px dashed var(--mute)"></i>dashed = drill</span></div>'
        '<p class="fine">Progress is saved in this browser only (phone and laptop keep separate copies). '
        'Pool questions and drills take Known / Again; cards take a Done tick. '
        'Keys in focus mode: space reveals, 1 = Again, 2 = Known, Esc closes.</p>'
        '<div class="btnrow"><a class="btn ghost sm" href="bda-final-guide.pdf">Full guide PDF</a>'
        '<a class="btn ghost sm" href="bda-exam-pool.pdf">Pool-only PDF</a>'
        '<button class="btn ghost sm" id="reset" style="border-color:var(--red);color:var(--red)">Reset progress</button></div>'
        "</section>")


def picker(chs, cmps=(), probs=()):
    weeks = "".join(
        f'<button data-focus="pool:{d["week"]}">W{d["week"]} pool<small>{len(d["pool"])} questions</small></button>'
        f'<button data-focus="card:{d["week"]}">W{d["week"]} cards<small>traps + scenarios · {len(d["topics"])}</small></button>'
        f'<button data-focus="drill:{d["week"]}">W{d["week"]} drills<small>{sum(len(t["questions"]) for t in d["topics"])} drills</small></button>'
        for d in chs)
    return ('<template id="pickt"><div class="f-pick">'
            '<div class="pg"><button class="big" data-focus="next">Next block of today\'s plan<small></small></button>'
            '<button data-focus="again">Again pile<small><span class="againn">0</span> items</small></button>'
            '<button data-focus="one">One-liners<small>all 36 topics</small></button></div>'
            + (f'<h3>Banks</h3><div class="pg"><button data-focus="cmp:all">Comparisons<small>all {len(cmps)}: X vs Y?</small></button>'
               f'<button data-focus="probs:all">Slide problems<small>{sum(len(x.get("variants", [])) + bool(x.get("why")) for x in probs)} practice items</small></button>'
               '<button data-focus="src:mcq">Every MCQ<small>all weeks</small></button><button data-focus="src:tf">Every True/False<small>all weeks</small></button>'
               + "".join(f'<button data-focus="cmp:{w}">W{w} compare<small>{sum(1 for c in cmps if c["week"] == w)} pairs</small></button>'
                         f'<button data-focus="probs:{w}">W{w} slide problems<small>{sum(1 for x in probs if x["week"] == w)} problems</small></button>'
                         for w in sorted({c["week"] for c in cmps} | {x["week"] for x in probs})) + '</div>' if cmps or probs else "")
            + f'<h3>By week</h3><div class="pg">{weeks}</div></div></template>')


# ---------------------------------------------------------------- extra banks (extra/*.json)

EXTRA = {"cmp_by_card": {}, "prob_by_card": {}}
# Plan links whose topic names several pairs or a problem by a different name. Ids are checked at build
# time; an id that no longer exists falls back to topic matching and is reported.
LINK_OVERRIDES = {
    "cmp:MapReduce vs Spark (W6)": ["w06-mapreduce-vs-spark"],
    "cmp:Lambda vs Kappa (W8)": ["w08-lambda-vs-kappa"],
    "cmp:Sqoop vs Flume vs Kafka (W8)": ["w08-sqoop-vs-flume", "w08-flume-vs-kafka"],
    "cmp:FIFO vs Capacity vs Fair scheduler (W5)": ["w05-capacity-vs-fair"],
    "cmp:Avro vs Parquet vs ORC (W5)": ["w05-avro-vs-parquet", "w05-parquet-vs-orc"],
    "cmp:Snappy vs Gzip vs LZO vs Bzip2 vs Zstd (W5)": ["w05-snappy-vs-gzip", "w05-splittable-vs-not"],
    "cmp:Tableau vs Power BI vs D3 vs Grafana vs Superset vs Kibana (W9)": ["w09-tableau-vs-d3", "w09-tableau-vs-grafana"],
    "cmp:alpha vs hexbin vs KDE (W9)": ["w09-alpha-vs-hexbin", "w09-hexbin-vs-kde"],
    "cmp:HIPAA vs GDPR vs PDPA (W10)": ["w10-hipaa-vs-gdpr"],
    "prob:W6 GraySort per-node efficiency": ["w06-graysort"],
    "prob:W5 LinkedIn capacity planning (containers per queue)": ["w05-live-capacity"],
    "prob:W5 splits per file": ["w05-gzip-mappers"],
    "prob:W7 bucket number and file size": ["w07-bucketing", "w07-a1-design"],
    "prob:W10 Prophet component sum": ["w10-live-prophet"],
    "prob:W10 Spark batch forecasting speedup": ["w10-sku-40x"],
}
# Parts of a multi-item link that no pair in comparisons.json covers on its own (reported as partial).
LINK_PARTIAL = {
    "cmp:FIFO vs Capacity vs Fair scheduler (W5)": "no FIFO pair; FIFO is on the yarn-sched card",
    "cmp:Snappy vs Gzip vs LZO vs Bzip2 vs Zstd (W5)": "LZO, Bzip2, Zstd sit in the splittable pair and the compression card",
    "cmp:Tableau vs Power BI vs D3 vs Grafana vs Superset vs Kibana (W9)": "no Superset or Kibana pair; both are on the streaming-tools card",
    "cmp:HIPAA vs GDPR vs PDPA (W10)": "no PDPA pair; PDPA is on the health-data card",
}
_STOP = set("vs the a of and x pool per to in on".split())


def load_extras():
    def rd(n):
        f = ROOT / "extra" / n
        return json.loads(f.read_text()) if f.exists() else None
    return rd("predicted.json") or {}, rd("comparisons.json") or [], rd("slide_problems.json") or []


def _toks(s):
    return {t[:5] for t in re.findall(r"[a-z0-9]+", s.lower().replace("-", " ")) if t not in _STOP and not re.fullmatch(r"w\d+", t)}


def cmp_title(c):
    return f'{c["x"]} vs {c["y"]}'


def short(s, n=46):
    s = re.sub(r"\s*\([^)]*\)", "", s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


POOL_CLS = {"Q": "mcq", "TF": "tf", "D": "desc", "A": "anal", "Disc": "disc"}


def _pool_ids(w, rest, pool_ids):
    """'D1' / 'MCQ Q1, Q3' / 'TF1-TF4' / 'Disc 2' -> pool element ids (None if any piece fails)."""
    out = []
    for piece in [x.strip() for x in rest.split(",")]:
        piece = re.sub(r"^MCQ\s+", "", piece)
        m = re.fullmatch(r"(Q|TF|D|A|Disc)\s?(\d+)(?:-(?:Q|TF|D|A|Disc)?\s?(\d+))?", piece)
        if not m:
            return None
        lo, hi = int(m.group(2)), int(m.group(3) or m.group(2))
        for n in range(lo, hi + 1):
            lab = f"Q{n}" if m.group(1) == "Q" else f"{m.group(1)}{n}" if m.group(1) in ("D", "A") else str(n)
            pid = f"p{w}-{POOL_CLS[m.group(1)]}-{slug(lab)}"
            if pid not in pool_ids:
                return None
            out.append((pid, f"W{w} {'MCQ ' if m.group(1) == 'Q' else 'TF' if m.group(1) == 'TF' else 'Disc ' if m.group(1) == 'Disc' else ''}{lab}"))
    return out


def resolve_link(l, ctx, report):
    """One plan link -> list of (css kind, label, href or None, focus spec or None, item id or None)."""
    k, _, v = l.partition(":")
    k, v = k.strip(), v.strip()
    if k == "card":
        if v == "all traps":
            return [("go", "Flash every card's traps", None, "traps", None)]
        cid = v.split("/")[-1]
        if cid in ctx["cards"]:
            return [("card", ctx["cards"][cid], "#" + cid, None, cid)]
    elif k == "pool":
        m = re.fullmatch(r"W(\d+)-W(\d+)\s+(MCQ|TF).*", v)
        if m:
            src = "mcq" if m.group(3) == "MCQ" else "tf"
            n = sum(1 for x in ctx["pool_ids"] if f"-{src}-" in x)
            return [("go", f"Flash all {n} {'MCQ' if src == 'mcq' else 'True/False'} (W{m.group(1)}–W{m.group(2)})", None, f"src:{src}", None)]
        m = re.fullmatch(r"W(\d+)\s+(.+)", v)
        ids = m and _pool_ids(int(m.group(1)), m.group(2), ctx["pool_ids"])
        if ids:
            return [("pool", lab, "#" + pid, None, pid) for pid, lab in ids]
    elif k in ("cmp", "prob"):
        bank = ctx["cmps"] if k == "cmp" else ctx["probs"]
        pre = "c-" if k == "cmp" else "x-"
        ids = [i for i in LINK_OVERRIDES.get(l, []) if i in bank]
        if LINK_OVERRIDES.get(l) and len(ids) < len(LINK_OVERRIDES[l]):
            report["stale"].append(l)
        if not ids:
            m = re.search(r"W(\d+)", v)
            w = int(m.group(1)) if m else None
            q = _toks(re.sub(r"\(W\d+\)", "", v))
            best = []
            for i, it in bank.items():
                if w and it["week"] != w:
                    continue
                txt = (cmp_title(it) if k == "cmp" else it["title"]) + " " + i
                sc = len(q & _toks(txt)) / max(1, len(q))
                best.append((sc, i))
            best.sort(reverse=True)
            if best and best[0][0] >= 0.4 and (len(best) == 1 or best[1][0] < best[0][0]):
                ids = [best[0][1]]
                report["auto"].append(f"{l} -> {ids[0]} ({best[0][0]:.2f})")
        if ids:
            if l in LINK_PARTIAL:
                report["partial"].append(f"{l}: {LINK_PARTIAL[l]}")
            if k == "cmp":
                return [("cmp", short(cmp_title(bank[i])), f"#c-{i}", None, f"c-{i}") for i in ids]
            return [("prob", short(bank[i]["title"]), f"#x-{i}", None, f"x-{i}") for i in ids]
    elif k == "paper":
        m = re.fullmatch(r"([AB])\s+(.+)", v)
        if m:
            P, rest = m.group(1), m.group(2)
            out = []
            if (mm := re.fullmatch(r"Q(\d)-Q(\d)", rest)):
                out = [(f"p{P}-q{n}", f"Paper {P} Q{n}") for n in range(int(mm.group(1)), int(mm.group(2)) + 1)]
            elif (mm := re.fullmatch(r"Q(\d)\s+OR.*", rest)):
                out = [(f"p{P}-q{mm.group(1)}-or", f"Paper {P} Q{mm.group(1)} OR")]
            elif (mm := re.fullmatch(r"Q(\d)", rest)):
                out = [(f"p{P}-q{mm.group(1)}", f"Paper {P} Q{mm.group(1)}")]
            elif rest.startswith("ORs"):
                out = [(pid, f"Paper {P} Q{pid.split('-q')[1][0]} OR") for pid in ctx["paper_ids"] if pid.startswith(f"p{P}-") and pid.endswith("-or")]
            if out and all(pid in ctx["paper_ids"] for pid, _ in out):
                return [("paper", lab, "#" + pid, None, None) for pid, lab in out]
    elif k.startswith("formulas"):
        return [("go", "Formula sheet", "#sheet-formulas", None, None)]
    elif k == "must_know":
        return [("go", "Must-know list", "#sheet-must", None, None)]
    elif k == "misses sheet":
        return [("go", "Again pile (your misses)", None, "again", None)]
    report["unresolved"].append(l)
    return []


def link_html(kind, label, href, focus):
    if focus:
        return f'<button class="lk l{kind}" data-focus="{focus}">{esc(label)}</button>'
    return f'<a class="lk l{kind}" href="{href}">{esc(label)}</a>'


def dayplan(pred, ctx, report):
    blocks = pred.get("plan", [])
    out_today, out_morn, tot_today, tot_morn = [], [], 0, 0
    for i, b in enumerate(blocks, 1):
        links, items = [], []
        for l in b.get("links", []):
            report["n"] += 1
            for kind, lab, href, focus, iid in resolve_link(l, ctx, report):
                links.append(link_html(kind, lab, href, focus))
                if iid:
                    items.extend(ctx["prac"].get(iid, [iid]))
        items = list(dict.fromkeys(items))
        morning = b["block"].lower().startswith("exam morning")
        m = re.match(r"Day (\d+)\.\s*(.*)", b["block"])
        num, title = (m.group(1), m.group(2)) if m else (("M" + str(len(out_morn) + 1)) if morning else str(i), b["block"])
        focus = (f'<button class="btn sm" data-focus="blk:b{i}">&#9654; Focus {len(items)}</button>' if items else "")
        li = (f'<li class="blk" id="blk{i}" data-sid="b{i}" data-items="{" ".join(items)}">'
              f'<div class="bh"><span class="bn">{esc(num)}</span><span class="bt">{esc(title)}</span><span class="bm">{b["minutes"]} min</span></div>'
              f'<p class="bk">{esc(b["task"])}</p><div class="lks">{"".join(links)}</div>'
              f'<div class="bf">{focus}<span class="bp"><i></i></span><button class="tk" data-tick="b{i}">Block done</button></div></li>')
        if morning:
            out_morn.append(li)
            tot_morn += b["minutes"]
        else:
            out_today.append(li)
            tot_today += b["minutes"]
    return out_today, out_morn, tot_today, tot_morn


def emphasis_html(pred):
    em = sorted(pred.get("emphasis", []), key=lambda e: (-e["score"], e["week"]))
    lis = "".join(
        f'<li><span class="sc9">{e["score"]}</span><span><b>W{e["week"]}</b> · {esc(re.sub(r"\s*\[card [^]]+\]", "", e["topic"]))}</span>'
        f'<span class="ev">{esc(e["evidence"])}</span></li>' for e in em)
    return (f'<details class="fold"><summary>Why this order: teacher-emphasis score for {len(em)} topics, with the slide evidence</summary>'
            f'<div><p class="fine">Score out of 10, from how many slides, drawn figures, pool questions and instructor notes each topic has. '
            f'It is a reading of the slides, not inside knowledge of the paper.</p><ol class="emph">{lis}</ol></div></details>')


def cmp_view(cmps, cards):
    order = sorted(cmps, key=lambda c: (c.get("likelihood") != "high", c["week"]))
    weeks = sorted({c["week"] for c in cmps})
    out = ['<section class="view" id="cmp" data-title="Comparisons"><header class="wkhead"><small>All weeks · from the slides</small>'
           f'<h2>Comparisons: {len(cmps)} &ldquo;X vs Y&rdquo; pairs</h2>'
           '<p class="summary">Each pair has the slide table, the one-line key difference (yellow) and the scenario cue that tells you '
           'which side a question means. &ldquo;High&rdquo; pairs are on the slides as an explicit comparison or asked in the pool; they come first.</p>'
           '<div class="prog"><span class="ptxt" data-bank=".cmpc"></span></div></header>'
           '<div class="toc noprint"><div class="filt"><span class="lbl">Week</span><button class="fb" data-fw="">All</button>'
           + "".join(f'<button class="fb" data-fw="{w}">W{w}</button>' for w in weeks)
           + '</div><div class="filt"><span class="lbl">Likely</span><button class="fb" data-fl="">All</button>'
           '<button class="fb" data-fl="high">High</button><button class="fb" data-fl="medium">Medium</button></div>'
           '<div class="btnrow" style="margin-top:6px"><button class="btn sm" data-focus="cmp:f">&#9654; Flash these: X vs Y?</button></div>'
           '<p class="shown"></p></div>']
    for c in order:
        cid = c["id"]
        head = f'<tr><th></th><th>{esc(c["x"])}</th><th>{esc(c["y"])}</th></tr>'
        rows = "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in r) + "</tr>" for r in c.get("rows", []))
        link = (f'<a class="tocard" href="#{c["card_id"]}">Card: {esc(cards[c["card_id"]])} &rarr;</a>'
                if c.get("card_id") in cards else f'<span class="fmt">W{c["week"]} · no single card</span>')
        lik = c.get("likelihood", "medium")
        out.append(f'<article class="cmpc bitem" id="c-{cid}" data-id="c-{cid}" data-w="{c["week"]}" data-l="{lik}">'
                   f'<header><h4>{esc(cmp_title(c))}<span class="meta">Week {c["week"]} · {esc(c.get("slides", ""))}</span></h4>'
                   f'<span class="lik {lik}">{lik}</span></header>'
                   f'<div class="tw"><table>{head}{rows}</table></div>'
                   f'<div class="one"><b class="l">Key difference</b>{esc(c["key"])}</div>'
                   f'<div class="cue"><b>Spot it in a scenario</b>{esc(c["cue"])}</div>'
                   f'<div class="afoot">{link}{marks_btns()}</div></article>')
    out.append("</section>")
    return "".join(out)


def prob_view(probs, cards):
    weeks = sorted({p["week"] for p in probs})
    rk = {"very likely": "vl", "likely": "l"}
    order = sorted(probs, key=lambda p: (p["week"], p.get("rank") != "very likely"))
    out = ['<section class="view" id="probs" data-title="Slide problems"><header class="wkhead"><small>All weeks · the slides\' own numbers</small>'
           f'<h2>Slide problems: {len(probs)} worked examples</h2>'
           '<p class="summary">The teacher said solving the slide exercises covers the paper. Each problem shows the slide\'s given numbers; '
           'tap for the worked steps. Then do the two one-step variants and the &ldquo;why&rdquo; question, and mark each Known or Again.</p>'
           '<div class="prog"><span class="ptxt" data-bank=".qa.prac"></span></div></header>'
           '<div class="toc noprint"><div class="filt"><span class="lbl">Week</span><button class="fb" data-fw="">All</button>'
           + "".join(f'<button class="fb" data-fw="{w}">W{w}</button>' for w in weeks)
           + '</div><div class="filt"><span class="lbl">Rank</span><button class="fb" data-fl="">All</button>'
           '<button class="fb" data-fl="vl">Very likely</button><button class="fb" data-fl="l">Likely</button></div>'
           '<div class="btnrow" style="margin-top:6px"><button class="btn sm" data-focus="probs:f">&#9654; Practise these</button></div>'
           '<p class="shown"></p></div>']
    for p in order:
        pid, w = p["id"], p["week"]
        cid = (p.get("card") or "").split("/")[-1]
        link = f'<a class="tocard" href="#{cid}">Card: {esc(cards[cid])} &rarr;</a>' if cid in cards else "<span></span>"
        steps = "".join(f"<li>{esc(x)}</li>" for x in p.get("solution_steps", []))
        prac = []
        for j, v in enumerate(p.get("variants", []), 1):
            prac.append((f"x-{pid}-v{j}", f"Variant {j}", v["q"], v["a"]))
        if p.get("why"):
            prac.append((f"x-{pid}-why", "Why", p["why"]["q"], p["why"]["a"]))
        pr = "".join(
            f'<div class="qa prac" id="{xid}" data-id="{xid}" data-w="{w}"><div class="q" tabindex="0"><span class="st8"></span>'
            f'<div class="txt">{esc(q)}</div><span class="tag">{lab}</span></div>'
            f'<div class="ans">{esc(a)}<div class="afoot">{link if lab == "Why" else "<span></span>"}{marks_btns()}</div></div></div>'
            for xid, lab, q, a in prac)
        r = p.get("rank", "likely")
        out.append(f'<article class="prob bitem" id="x-{pid}" data-w="{w}" data-l="{rk.get(r, "l")}">'
                   f'<header><h4>{esc(p["title"])}<span class="meta">Week {w} · {esc(p.get("slides", ""))}</span></h4>'
                   f'<span class="lik {rk.get(r, "l")}">{esc(r)}</span></header>'
                   f'<div class="given"><b>Given</b>{esc(p["given"])}</div>'
                   f'<div class="qa sol"><div class="q" tabindex="0"><div class="txt">Worked solution · {len(p.get("solution_steps", []))} steps (tap)</div></div>'
                   f'<div class="ans"><ol>{steps}</ol><div class="one"><b class="l">Answer</b>{esc(p["answer"])}</div></div></div>'
                   f'<h5>Practice · {len(prac)}</h5>{pr}</article>')
    out.append("</section>")
    return "".join(out)


def _subs(subs):
    q, a = [], []
    for s in subs:
        m = re.match(r"\s*\(?(i|ii|iii|iv|v)\)\s*", s["q"])
        lab = m.group(1) if m else ""
        qt = s["q"][m.end():] if m else s["q"]
        q.append(f"<li><b>{lab})</b><div>{esc(qt)}</div></li>")
        a.append(f"<li><b>{lab})</b><div>{esc(s['a'])}</div></li>")
    return f'<ol class="rom">{"".join(q)}</ol>', f'<ol class="rom">{"".join(a)}</ol>'


def _part(pt, wk=None):
    q, a = _subs(pt.get("subs", []))
    lab = esc(pt["label"])
    wks = f' <span class="orwk">W{wk}</span>' if wk else ""
    return (f'<div class="qa mock"><div class="q" tabindex="0"><div class="pl">({lab}){wks}'
            f'<span>{pt["marks"]} marks <span class="tap">· tap for answers</span></span></div>'
            f'<div class="txt"><div class="scn">{esc(pt.get("scenario", ""))}</div>{q}</div></div><div class="ans">{a}</div></div>')


def predicted_html(pred):
    out, ids = [], set()
    for pi, pp in enumerate(pred.get("papers", [])):
        P = "AB"[pi] if pi < 2 else str(pi + 1)
        out.append(f'<div class="predsec"><div class="predban" id="pred-{P}"><b>Prediction · not the real paper</b>'
                   f'<h3>{esc(pp["name"])}</h3><p>Built from how much the slides stress each chapter; the reasoning is shown on every question. '
                   'The real paper can pick any chapter, so the plan and the pool still cover all six weeks.</p></div>')
        for q in pp.get("questions", []):
            n = re.sub(r"\D", "", q["q"]) or "?"
            qid = f"p{P}-q{n}"
            ids.add(qid)
            tot = sum(pt["marks"] for pt in q.get("parts", []))
            out.append(f'<div class="paper pred" id="{qid}"><header><b>Question {n}</b><span>Week {q["week"]} · {tot:g} marks</span></header>'
                       f'<div class="why"><b>Why predicted:</b> {esc(q.get("why", ""))}</div>')
            out.extend(_part(pt) for pt in q.get("parts", []))
            ors = q.get("or") or []
            if ors:
                ids.add(qid + "-or")
                out.append(f'<div class="or" id="{qid}-or">OR</div>')
                out.extend(_part(pt, pt.get("week")) for pt in ors)
            out.append("</div>")
        out.append("</div>")
    return "".join(out), ids


def must_html(pred):
    mk = pred.get("must_know", [])
    sk = pred.get("skip", [])
    lis = "".join(f'<li><button data-tick="mk{i}" aria-label="Known"></button><span>{esc(x)}</span></li>' for i, x in enumerate(mk, 1))
    skip = "".join(f"<li>{esc(x)}</li>" for x in sk)
    return (f'<h3 class="sh" id="sheet-must">Must-know: {len(mk)} lines <span class="n">tick each one you can say from memory</span></h3>'
            f'<ul class="mkl">{lis}</ul>'
            + (f'<details class="fold"><summary>If short on time: {len(sk)} things you can skip</summary><div>'
               f'<p class="fine">Low-yield detail by the slide evidence. Skip only if the clock forces it; everything else stays in.</p>'
               f'<ul>{skip}</ul></div></details>' if sk else ""))


# ---------------------------------------------------------------- page

def main():
    chs = [json.loads(p.read_text()) for w in WEEKS if (p := ROOT / f"cards/w{w:02d}.json").exists()]
    npool = sum(len(d["pool"]) for d in chs)
    ntop = sum(len(d["topics"]) for d in chs)
    pred, cmps, probs = load_extras()
    cards = {t["id"]: t["title"] for d in chs for t in d["topics"]}
    for c in cmps:
        EXTRA["cmp_by_card"].setdefault(c.get("card_id"), []).append(c)
    for x in probs:
        EXTRA["prob_by_card"].setdefault((x.get("card") or "").split("/")[-1], []).append(x)
    weeks_html = "".join(week_view(d, i) for i, d in enumerate(chs, 1))  # assigns ids used by the plan
    sessions, days = build_plan(chs)
    total_min = sum(s["min"] for s in sessions)
    pred_html, paper_ids = predicted_html(pred)
    mock_html, nsplit = mock(chs, pred_html)
    ctx = dict(cards=cards, pool_ids={p["_id"] for d in chs for p in d["pool"]},
               cmps={c["id"]: c for c in cmps}, probs={x["id"]: x for x in probs}, paper_ids=paper_ids,
               prac={f'x-{x["id"]}': [f'x-{x["id"]}-v{j}' for j in range(1, len(x.get("variants", [])) + 1)]
                     + ([f'x-{x["id"]}-why'] if x.get("why") else []) for x in probs})
    report = dict(n=0, unresolved=[], partial=[], stale=[], auto=[])
    dp = dayplan(pred, ctx, report)
    dnav = "".join(f'<a class="chip" data-nav="w{d["week"]}" href="#w{d["week"]}">W{d["week"]}</a>' for d in chs)
    wkmenu = "".join(
        f'<a href="#w{d["week"]}"><b>W{d["week"]}</b> {esc(d["title"])} <span class="wpct" data-wp="{d["week"]}"></span></a>' for d in chs)
    wkmenu += (f'<a class="bank" href="#cmp"><b>VS</b> Comparisons <span class="wpct">{len(cmps)}</span></a>'
               f'<a class="bank" href="#probs"><b>CALC</b> Slide problems <span class="wpct">{len(probs)}</span></a>')
    tabs = (f'<a class="tab" data-nav="start" href="#start">{ICONS["plan"]}Plan</a>'
            f'<button class="tab" data-nav="weeks" id="wkbtn">{ICONS["weeks"]}Browse</button>'
            f'<button class="tab" data-focus="pick">{ICONS["focus"]}Focus</button>'
            f'<a class="tab" data-nav="mock" href="#mock">{ICONS["mock"]}Mock</a>'
            f'<a class="tab" data-nav="sheet" href="#sheet">{ICONS["sheet"]}Sheet</a>')
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#b45309">'
        f"<title>BDA Final Guide</title><style>{CSS}</style></head><body>"
        '<nav class="bar"><div class="bar-in"><a class="brand" href="#start">BDA <span>final</span></a>'
        f'<div class="dnav"><a class="chip" data-nav="start" href="#start">Plan</a>{dnav}'
        '<a class="chip" data-nav="cmp" href="#cmp">Compare</a><a class="chip" data-nav="probs" href="#probs">Problems</a>'
        '<a class="chip" data-nav="mock" href="#mock">Mock</a><a class="chip" data-nav="sheet" href="#sheet">Sheet</a>'
        '<button class="chip" data-focus="pick">Focus</button></div>'
        '<span class="sp"></span><span class="opct" title="Overall progress">0%</span>'
        '<button class="chip" id="all">Answers</button>'
        '<button class="chip ico" id="theme" aria-label="Toggle dark mode">&#9680;</button></div>'
        '<div class="obar"><i></i></div></nav>'
        f'<div class="wkmenu" id="wkmenu">{wkmenu}</div>'
        "<main>"
        + start_view(chs, days, len(sessions), total_min, dp, pred, len(cmps), len(probs)) + weeks_html
        + (cmp_view(cmps, cards) if cmps else "") + (prob_view(probs, cards) if probs else "") + mock_html + sheet(chs, pred)
        + "</main>"
        f'<nav class="tabbar"><div class="tabbar-in">{tabs}</div></nav>'
        '<button class="totop" id="totop" aria-label="Back to top">&uarr;</button>'
        '<div class="focus" id="focus" role="dialog" aria-label="Focus mode"><div class="f-top"><b id="f-title"></b>'
        '<span id="f-count"></span><button class="chip" data-fx="close">Close</button></div><div class="f-bar"><i></i></div>'
        '<div class="f-body" id="f-body"></div><div class="f-btns" id="f-btns"></div></div>'
        '<div class="toast" id="toast"></div>'
        + picker(chs, cmps, probs)
        + f"<script>{JS}</script></body></html>"
    )

    def inline_img(m):
        f = ROOT / m.group(1)
        return figure(m.group(1)) if f.exists() else m.group(0)
    page = re.sub(r'<img[^>]*src="(diagrams/[^"]+\.svg)"[^>]*>', inline_img, page)
    page = re.sub(r'(?<!<div class="tw">)(<table.*?</table>)', r'<div class="tw">\1</div>', page, flags=re.S)
    (ROOT / "index.html").write_text(page)
    for out, q in (("bda-final-guide.pdf", ""), ("bda-exam-pool.pdf", "?pool")):
        subprocess.run(
            ["google-chrome-stable", "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=3000",
             f"--user-data-dir=/tmp/claude-1000/bda-pdf-profile", f"--print-to-pdf={ROOT / out}",
             (ROOT / "index.html").as_uri() + q],
            check=True, capture_output=True)
    print(f"{len(chs)} chapters, {ntop} topics, {npool} pool questions, {len(sessions)} sessions "
          f"({total_min} min), mock parts split into i-iv: {nsplit}")
    print(f"extras: {len(cmps)} comparisons, {len(probs)} slide problems, {len(pred.get('papers', []))} predicted papers, "
          f"{len(pred.get('plan', []))} plan blocks, {len(pred.get('must_know', []))} must-know, {len(pred.get('skip', []))} skip")
    print(f"plan links: {report['n']} total, {len(report['unresolved'])} unresolved, {len(report['partial'])} partial")
    for l in report["unresolved"]:
        print("  UNRESOLVED", l)
    for l in report["partial"]:
        print("  partial   ", l)
    for l in report["auto"]:
        print("  matched   ", l)
    for l in report["stale"]:
        print("  stale override", l)


if __name__ == "__main__":
    main()
