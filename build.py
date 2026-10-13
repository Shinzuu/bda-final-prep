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
    "mcq": "Multiple choice", "blank": "Fill in the blank", "define": "Define or list", "steps": "Explain the steps",
    "why": "Why", "distinguish": "Tell apart", "scenario": "Scenario", "one_step": "One-step calculation",
    "full_calc": "Full calculation", "long": "Long answer",
}
SRC_ORDER = ["MCQ", "True/False", "Descriptive", "Analytical", "Discussion", "Live Exercise"]
SRC_CLASS = {"MCQ": "mcq", "True/False": "tf", "Descriptive": "desc", "Analytical": "anal",
             "Discussion": "disc", "Live Exercise": "live"}
SRC_SHORT = {"MCQ": "MCQ", "True/False": "T/F", "Descriptive": "Descriptive", "Analytical": "Analytical",
             "Discussion": "Discussion", "Live Exercise": "Live exercise"}
SRC_KIND = {"MCQ": "multiple choice", "True/False": "true or false", "Descriptive": "descriptive",
            "Analytical": "analytical", "Discussion": "discussion", "Live Exercise": "live exercise"}
SRC_GROUP = {"MCQ": "Multiple choice", "True/False": "True or false", "Descriptive": "Descriptive",
             "Analytical": "Analytical", "Discussion": "Discussion", "Live Exercise": "Live exercises"}
SESSION_TARGET = 21  # minutes; sessions land between ~15 and ~25

CSS = r"""
:root{--bg:#f4f5f2;--panel:#fff;--ink:#1e2320;--mute:#5d6560;--faint:#687069;--line:#e1e4df;--accent:#6a3d7a;
--acc-soft:#f3ecf5;--green:#2f7d4f;--green-soft:#e8f3eb;--red:#b3372f;--red-soft:#fbeeec;
--blue:#2457a6;--blue-soft:#ecf1fa;--yel:#fbe6a0;--code:#eceee9;--violet:#6a3d7a;--violet-soft:#f3ecf5;
--serif:Newsreader,"Iowan Old Style",Georgia,serif;--sans:"Atkinson Hyperlegible",system-ui,"Segoe UI",sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161816;--panel:#1e211f;--ink:#e6e9e5;
--mute:#a3aba6;--faint:#8d948f;--line:#303531;--accent:#d3aae2;--acc-soft:#2d2233;--green:#72cf98;--green-soft:#15281c;
--red:#f08b80;--red-soft:#2e1816;--blue:#94b6f0;--blue-soft:#16213a;--yel:#5a4812;--code:#262a27;
--violet:#d3aae2;--violet-soft:#2d2233}}
:root[data-theme=dark]{--bg:#161816;--panel:#1e211f;--ink:#e6e9e5;--mute:#a3aba6;--faint:#8d948f;--line:#303531;--accent:#d3aae2;
--acc-soft:#2d2233;--green:#72cf98;--green-soft:#15281c;--red:#f08b80;--red-soft:#2e1816;--blue:#94b6f0;
--blue-soft:#16213a;--yel:#5a4812;--code:#262a27;--violet:#d3aae2;--violet-soft:#2d2233}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
[id]{scroll-margin-top:64px}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 var(--sans)}
main{max-width:740px;margin:0 auto;padding:0 20px 120px}
a{color:var(--accent);text-underline-offset:.18em;text-decoration-thickness:1px}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.005em}
code,pre{font-family:ui-monospace,"JetBrains Mono",monospace;font-size:.84em;font-variant-ligatures:none}
pre{background:var(--code);padding:10px 12px;border-radius:8px;overflow-x:auto;white-space:pre-wrap;line-height:1.45}
code{background:var(--code);padding:0 4px;border-radius:4px;overflow-wrap:anywhere}pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:8px 0;line-height:1.45}
th,td{border-bottom:1px solid var(--line);padding:7px 10px 7px 0;text-align:left;vertical-align:top}
th{font-weight:700;color:var(--mute);font-size:.85rem}
.tw{overflow-x:auto;max-width:100%}.qa .txt,.ans{min-width:0}
.view:not(.cur){display:none}body.showall .view{display:block}
.quiet{color:var(--mute);font-size:.9rem;margin:.4em 0}
/* ---------- top bar ---------- */
.bar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 90%,transparent);
backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.bar-in{max-width:1180px;margin:0 auto;padding:10px 20px;display:flex;gap:4px;align-items:center}
.brand{font-family:var(--serif);font-weight:600;font-size:1.08rem;text-decoration:none;color:var(--ink);white-space:nowrap;margin-right:12px}
.chip{border:0;background:none;color:var(--mute);border-radius:8px;padding:5px 9px;
font-size:.9rem;white-space:nowrap;cursor:pointer;text-decoration:none;line-height:1.4}
.chip:hover{color:var(--ink);background:var(--code)}
.chip.on{color:var(--ink);background:var(--panel);box-shadow:inset 0 0 0 1px var(--line)}
.chip.ico{font-size:1rem}
.dnav{display:flex;gap:2px;align-items:center}
.dnav .gap{width:10px}
.sp{flex:1}
.obar{position:absolute;left:0;right:0;bottom:0;height:2px;background:var(--line)}
.obar i{display:block;height:100%;width:0;background:var(--green);transition:width .3s}
/* bottom tab bar (phone) */
.tabbar{position:fixed;left:0;right:0;bottom:0;z-index:20;display:none;background:var(--panel);
border-top:1px solid var(--line);padding:4px 4px calc(4px + env(safe-area-inset-bottom))}
.tabbar-in{display:grid;grid-template-columns:repeat(5,1fr);max-width:560px;margin:0 auto}
.tab{background:none;border:0;padding:6px 0 4px;font-size:.74rem;color:var(--mute);text-decoration:none;
display:flex;flex-direction:column;align-items:center;gap:2px;cursor:pointer}
.tab svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.tab.on{color:var(--accent);font-weight:700}
.wkmenu{position:fixed;right:10px;top:54px;z-index:21;background:var(--panel);border:1px solid var(--line);
border-radius:16px;padding:6px;box-shadow:0 12px 32px rgba(20,24,22,.16);display:none;width:min(380px,calc(100vw - 20px));
max-height:calc(100vh - 70px);overflow-y:auto}
.wkmenu.open{display:block}
.wkmenu a,.wkmenu button{display:flex;gap:10px;align-items:baseline;text-decoration:none;color:var(--ink);border-radius:10px;padding:8px 10px;
font-size:.95rem;width:100%;background:none;border:0;cursor:pointer;text-align:left}
.wkmenu a:hover,.wkmenu button:hover{background:var(--code)}
.wkmenu button.on b{color:var(--accent)}
.opct{font-size:.85rem;color:var(--mute);font-variant-numeric:tabular-nums;margin-right:6px}
.wkmenu a b{font-weight:700;white-space:nowrap}.wkmenu a span.t{flex:1;color:var(--mute);font-size:.88rem}
.wkmenu hr{border:0;border-top:1px solid var(--line);margin:6px 10px}
.wpct{color:var(--faint);font-size:.8rem;white-space:nowrap;font-variant-numeric:tabular-nums}
/* ---------- checklist ---------- */
.chnav{margin-top:28px}
.cpct{font-size:.85rem;color:var(--mute);white-space:nowrap;font-variant-numeric:tabular-nums}
.cpct.full{color:var(--green);font-weight:700}
.chap{margin-top:56px}
.chead small{color:var(--mute);font-size:.95rem;display:block}
.chead h2{font-size:1.75rem;line-height:1.15;margin:2px 0 4px}
h3.step{font-size:1.3rem;margin:34px 0 2px}
h3.step span{display:block;font-family:var(--sans);font-weight:400;font-size:.9rem;color:var(--mute);letter-spacing:0}
.ck{list-style:none;margin:8px 0 0;padding:0}
.ci{border-top:1px solid var(--line)}
.ci:last-child{border-bottom:1px solid var(--line)}
.ch{display:flex;gap:12px;align-items:flex-start}
.tick{flex:none;width:26px;height:26px;margin:12px 0 0;border-radius:8px;border:1.5px solid var(--faint);background:var(--panel);cursor:pointer;
padding:0;display:grid;place-items:center;color:#fff;font-size:15px;line-height:1}
.ci.on .tick{background:var(--green);border-color:var(--green)}
.ci.on .tick::after{content:"\2713"}
.ci[data-st=a]:not(.on) .tick{border-color:var(--red);background:var(--red-soft)}
.ct{flex:1;min-width:0;text-align:left;background:none;border:0;padding:13px 0;cursor:pointer;display:block;font-size:1rem;line-height:1.4}
.ct .tt{display:block;font-weight:700}
.ct .tm{display:block;font-size:.85rem;color:var(--mute);margin-top:1px}
.ci.on .ct .tt{color:var(--mute);font-weight:400}
.cb{display:none;padding:0 0 20px 38px}
.ci.open .cb,body.all .cb{display:block}
.cb>:first-child{margin-top:0}
.cb .fa{display:none;margin-top:10px}
.cb .fa.open,body.all .cb .fa{display:block}
.cb .show{margin-top:12px}
.cb .show[hidden]{display:none}
.cb .pans,.cb .vans{border-left:3px solid var(--yel);padding:2px 0 2px 14px}
.cb .steps{margin:0;padding-left:1.3em}
.cb .fq>:first-child{margin-top:0}
.cb .more{font-size:.9rem;margin:16px 0 0}
.cb .afoot a{font-size:.9rem}
.cb .fgrid{grid-template-columns:1fr}
.cb .fcard{background:var(--bg)}
.cb .paper,.cb .qa.mock{background:none}
.complete{margin-top:24px;background:var(--green-soft);border-radius:16px;padding:16px 20px}
.complete h2{margin:0;color:var(--green);font-size:1.5rem}.complete p{margin:4px 0 0}
.complete[hidden]{display:none}
.go[hidden]{display:none}
@media (max-width:640px){.cb{padding-left:0}}
/* ---------- progress ---------- */
.prog{display:flex;align-items:center;gap:12px;font-size:.88rem;color:var(--mute);flex-wrap:wrap;margin:8px 0 0}
.pbar{flex:0 0 72px;height:5px;border-radius:99px;background:var(--code);overflow:hidden}
.pbar i{display:block;height:100%;width:0;background:var(--green);border-radius:99px;transition:width .3s}
.ptxt{font-variant-numeric:tabular-nums;flex:1 1 200px}
/* ---------- start view ---------- */
.hero{padding:40px 0 8px}
.hero h1{font-size:2.3rem;line-height:1.12;margin:0;font-weight:500;max-width:15em}
.hero .sub{color:var(--mute);margin:.6em 0 0;font-size:.95rem}
.todayp{margin:22px 0 0;font-size:1rem}
.todayp .tbar{display:block;height:6px;border-radius:99px;background:var(--code);margin-top:8px;overflow:hidden;max-width:420px}
.todayp .tbar i{display:block;height:100%;width:0;background:var(--green);transition:width .3s}
.go{display:block;margin:20px 0 0;background:var(--accent);color:#fff;text-decoration:none;border-radius:16px;
padding:18px 20px;font-weight:700;font-size:1.12rem;line-height:1.35}
.go .nt{font-weight:700}
:root[data-theme=dark] .go{color:#1d1420}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .go{color:#1d1420}}
.go.done{background:var(--green)}
.alt{display:flex;flex-wrap:wrap;gap:4px 18px;margin:12px 2px 0;font-size:.92rem}
.link{background:none;border:0;padding:0;color:var(--accent);cursor:pointer;text-decoration:underline;text-underline-offset:.18em;text-decoration-thickness:1px;font-size:inherit}
.resume{color:var(--mute);margin:0}
.btnrow{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;align-items:center}
.btn{border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:10px;padding:8px 16px;
font-weight:700;font-size:.92rem;cursor:pointer;text-decoration:none;display:inline-block}
:root[data-theme=dark] .btn{color:#1d1420}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .btn{color:#1d1420}}
.btn.ghost{background:transparent;color:var(--accent);border-color:var(--line)}
.btn.sm{padding:6px 12px;font-size:.88rem;border-radius:9px}
.btn.warn{color:var(--red);border-color:var(--line)}
h2.sec{font-size:1.45rem;margin:52px 0 6px}
h2.sec+.quiet{margin-top:0}
.day{margin:28px 0 8px;font-size:.95rem}
.day b{font-family:var(--serif);font-size:1.12rem;display:block}.day span{color:var(--mute)}
.plan{list-style:none;margin:0;padding:0}
.plan .ph{font-size:.88rem;font-weight:700;color:var(--mute);margin:18px 0 4px}
.sess{display:grid;grid-template-columns:22px 1fr auto;gap:0 12px;align-items:center;padding:10px 0;border-top:1px solid var(--line)}
.sess .sdot{width:18px;height:18px;border-radius:50%;border:1.5px solid var(--faint);display:grid;place-items:center;font-size:11px;color:#fff}
.sess.full .sdot{background:var(--green);border-color:var(--green)}
.sess.full .sdot::after{content:"\2713"}
.sess .sm{min-width:0;text-decoration:none;color:var(--ink)}
.sess .st{display:block;font-weight:700;font-size:.95rem;line-height:1.35}
.sess .sc{display:block;font-size:.85rem;color:var(--mute);line-height:1.4}
.sess .sr{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.sess .smin{font-size:.85rem;color:var(--mute);white-space:nowrap}
.sess .sbar{grid-column:2/4;height:3px;border-radius:9px;background:var(--code);overflow:hidden;margin-top:6px}
.sess .sbar i{display:block;height:100%;width:0;background:var(--green)}
.sess.full .st{color:var(--mute)}
.mini{border:0;background:none;padding:2px 0;font-size:.88rem;cursor:pointer;color:var(--accent);text-decoration:underline;
text-underline-offset:.18em;text-decoration-thickness:1px;white-space:nowrap}
.rows{list-style:none;margin:6px 0 0;padding:0}
.rows li{border-top:1px solid var(--line)}
.rows a{display:flex;gap:12px;align-items:center;padding:12px 0;text-decoration:none;color:var(--ink)}
.rows a .t{flex:1;min-width:0}.rows a .t b{display:block;font-weight:700}.rows a .t span{color:var(--mute);font-size:.88rem}
.rows .prog{margin:0;flex:none}.rows .prog .ptxt{display:none}
.rows .chev{color:var(--faint)}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.92rem;color:var(--mute);margin:8px 0}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:6px}
.fine{font-size:.9rem;color:var(--mute)}
/* ---------- week view ---------- */
.wkhead{padding:36px 0 8px}
.wkhead small{color:var(--mute);font-size:.95rem;display:block}
.wkhead h2{margin:2px 0 4px;font-size:1.9rem;line-height:1.15}
.summary{color:var(--mute);margin:.7em 0 .3em;font-size:.97rem}
.toc{margin:16px 0 8px;font-size:.95rem}
.toc .row{display:flex;flex-wrap:wrap;gap:4px 16px;align-items:baseline}
.toc .row+.row{margin-top:8px}
.toc .lbl{color:var(--mute);margin-right:-6px}
.toc ol{margin:12px 0 0;padding:0;list-style:none}
.toc li a{text-decoration:none;color:var(--ink);display:flex;gap:10px;align-items:baseline;padding:5px 0}
.toc li a::before{content:"";flex:none;width:9px;height:9px;border-radius:50%;border:1.5px solid var(--faint);transform:translateY(-1px)}
.toc li.isdone a::before{background:var(--green);border-color:var(--green)}
.toc li a span{color:var(--faint);font-size:.82rem;white-space:nowrap;margin-left:auto;padding-left:8px}
h3.sh{font-size:1.4rem;margin:48px 0 4px}
h3.sh .n{display:block;font-family:var(--sans);font-size:.9rem;color:var(--mute);font-weight:400;letter-spacing:0;margin-top:2px}
h4.grp{margin:28px 0 6px;font-size:1rem;color:var(--mute);font-weight:700}
/* ---------- questions: shared ---------- */
.qa{margin:0;border-top:1px solid var(--line)}
.qa .q{padding:14px 0;cursor:pointer;display:flex;gap:10px;align-items:flex-start}
.qa .q .txt{flex:1}
.qa .q .txt>:first-child{margin-top:0}.qa .q .txt>:last-child{margin-bottom:0}
.tag{font-size:.8rem;color:var(--faint);white-space:nowrap;padding-top:3px}
.opts{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:3px}
.ans{display:none;padding:2px 0 16px 20px}
.qa.open .ans,body.all .ans{display:block}
.ans>:first-child{margin-top:0}.ans>:last-child{margin-bottom:0}
.st8{flex:none;width:10px;height:10px;border-radius:50%;margin-top:8px;border:1.5px solid var(--faint)}
[data-st=k] .st8{background:var(--green);border-color:var(--green)}
[data-st=a] .st8{background:var(--red);border-color:var(--red)}
.afoot{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-top:14px}
.mk{display:flex;gap:8px;margin-left:auto}
.mk button{border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:6px 14px;font-size:.88rem;cursor:pointer;font-weight:700}
.mk button[data-m=a]{color:var(--mute)}.mk button[data-m=k]{color:var(--green)}
[data-st=a] .mk button[data-m=a]{background:var(--red-soft);border-color:var(--red);color:var(--red)}
[data-st=k] .mk button[data-m=k]{background:var(--green);border-color:var(--green);color:#fff}
.tocard{font-size:.9rem}
.qa.pool .num{font-weight:700;font-size:.9rem;color:var(--mute);white-space:nowrap;min-width:2.2em;padding-top:1px}
.qa.pool .ans{border-left:3px solid var(--yel);margin:0 0 14px 20px;padding:2px 0 2px 14px}
.qa.drill{font-size:.96rem}
.qa.drill .ans{border-left:3px solid var(--line);margin:0 0 14px 20px;padding:2px 0 2px 14px}
.hl{animation:hl 1.6s ease-out}
@keyframes hl{0%{background:var(--acc-soft)}100%{background:transparent}}
@media (prefers-reduced-motion:reduce){.hl{animation:none}*{transition:none!important}}
/* ---------- cards (topics) ---------- */
.card{background:var(--panel);border-radius:18px;margin:18px 0;padding:20px 22px}
.card>header{display:flex;gap:12px;align-items:flex-start}
.card h4{margin:0;font-family:var(--serif);font-size:1.3rem;font-weight:600;flex:1;line-height:1.25}
.card .meta{font-family:var(--sans);font-size:.85rem;color:var(--mute);margin-top:4px;display:block;font-weight:400}
.done,.tk{border:1px solid var(--line);background:none;border-radius:99px;padding:4px 12px;font-size:.85rem;
cursor:pointer;white-space:nowrap;font-weight:700;color:var(--mute)}
.done .y,.tk .y{display:none}
.card.isdone .done,.tk.on{background:var(--green);border-color:var(--green);color:#fff}
.card.isdone .done .y,.tk.on .y{display:inline}.card.isdone .done .n,.tk.on .n{display:none}
.one{background:color-mix(in srgb,var(--yel) 75%,var(--panel));border-radius:10px;padding:10px 14px;margin:14px 0 0}
.one b.l,.lay h5{display:block;margin:0 0 2px;font-size:.85rem;color:var(--mute);font-weight:700}
.one b.l{color:color-mix(in srgb,var(--ink) 65%,transparent)}
.lay{font-size:.96rem;margin-top:18px}
.lay ul,.lay ol{margin:0;padding-left:1.2em}.lay li{margin:4px 0}
.lay.trap h5{color:var(--red)}
.lay.trap ul{list-style:none;padding:0}
.lay.trap li{padding-left:16px;position:relative}
.lay.trap li::before{content:"";position:absolute;left:0;top:.62em;width:7px;height:7px;border-radius:50%;background:var(--red)}
.lay.calc{background:var(--blue-soft);border-radius:10px;padding:12px 14px}.lay.calc h5{color:var(--blue)}
.sc td:last-child{background:color-mix(in srgb,var(--yel) 55%,transparent);font-weight:700;padding-left:10px}
.sc{margin:0}
.pills{display:flex;flex-wrap:wrap;gap:4px 18px;margin-top:20px;padding-top:14px;border-top:1px solid var(--line)}
.pill{border:0;background:none;padding:2px 0;font-size:.92rem;cursor:pointer;color:var(--accent)}
.pill::after{content:" +";color:var(--faint)}
.pill.on{color:var(--ink);font-weight:700}.pill.on::after{content:" \2212"}
.pill.calc{color:var(--blue)}
.fold-b{display:none}.fold-b.open{display:block}
.fold-b>.lay:first-child{margin-top:14px}
.marks{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:.96rem}
.marks b{color:var(--mute);white-space:nowrap}
.back{margin-top:14px;font-size:.9rem;color:var(--mute)}
.back+.back{margin-top:4px}
.back a{text-decoration:none}
.back span{margin-right:4px}
.fmt{font-size:.85rem;color:var(--faint)}
/* phone tables: stacked criterion -> X / Y */
@media (max-width:640px){
 table.stk,table.stk tbody,table.stk tr,table.stk td{display:block;width:auto}
 table.stk thead{display:none}
 table.stk tr{padding:10px 0;border-bottom:1px solid var(--line)}
 table.stk td{border:0;padding:2px 0}
 table.stk td:first-child{font-weight:700;color:var(--ink)}
 table.stk td+td::before{content:attr(data-h) ": ";color:var(--mute);font-weight:700}
 table.stk td+td[data-h=""]::before{content:none}
 table.sc.stk td:first-child{font-weight:400}
 table.sc.stk td+td{display:inline-block;margin-top:4px;padding:2px 8px;border-radius:6px}
 table.sc.stk td+td::before{content:"\2192  ";color:var(--mute)}
 .cmpc table.stk td:first-child,.cmpc table th:first-child{width:auto}
}
/* ---------- diagrams ---------- */
.dia{margin:14px 0 6px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px}
.dia .pan{overflow-x:auto;-webkit-overflow-scrolling:touch}
.dia svg{display:block;width:100%;height:auto;max-height:60vh;margin:0 auto}
.dia figcaption{font-size:.85rem;color:var(--mute);text-align:center;margin-top:4px}
.panhint{display:none;font-size:.8rem;color:var(--mute);text-align:center}
@media (max-width:760px){.dia svg{min-width:var(--minw);max-height:none}.panhint{display:block}}
.dialink{text-decoration:none}
:root{--d-ink:#1c1b19;--d-mute:#78716c}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--d-box:#3a2a0c;--d-line:#f59e0b;--d-box2:#111d33;
--d-line2:#93c5fd;--d-box3:#0f2417;--d-line3:#4ade80;--d-ink:#ebe8e2;--d-mute:#a39e95}}
:root[data-theme=dark]{--d-box:#3a2a0c;--d-line:#f59e0b;--d-box2:#111d33;--d-line2:#93c5fd;--d-box3:#0f2417;
--d-line3:#4ade80;--d-ink:#ebe8e2;--d-mute:#a39e95}
/* ---------- mock: exam paper ---------- */
.paper{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:18px 20px;margin:20px 0}
.paper>header{display:flex;justify-content:space-between;align-items:baseline;gap:8px;border-bottom:1px solid var(--ink);
padding-bottom:6px;margin-bottom:6px;font-family:var(--serif)}
.paper>header b{font-size:1.2rem}.paper>header span{font-size:.9rem;color:var(--mute)}
.qa.mock{border-top:1px solid var(--line)}
.qa.mock:first-of-type{border-top:0}
.qa.mock .q{padding:12px 0;display:block}
.qa.mock .pl{font-family:var(--serif);font-weight:600;font-size:1.02rem;margin-bottom:4px;display:flex;justify-content:space-between;gap:8px}
.qa.mock .pl span{font-family:var(--sans);font-weight:400;color:var(--mute);font-size:.88rem;white-space:nowrap}
.qa.mock .ans{background:var(--blue-soft);border-radius:8px;margin:0 0 12px;padding:12px 14px}
.qa.mock .ans::before{content:"Model answer";display:block;font-size:.85rem;font-weight:700;color:var(--blue);margin-bottom:4px}
.qa.mock .tap{font-size:.82rem;color:var(--faint)}.qa.mock.open .tap,body.all .qa.mock .tap{display:none}
ol.rom{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:6px}
ol.rom li{display:grid;grid-template-columns:2.1em 1fr;gap:4px}
ol.rom li>b:first-child{font-family:var(--serif);color:var(--mute)}
.or{text-align:center;font-family:var(--serif);font-weight:600;color:var(--mute);margin:8px 0;
display:flex;align-items:center;gap:12px}.or::before,.or::after{content:"";flex:1;border-top:1px solid var(--line)}
/* ---------- sheet ---------- */
.fgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.fcard{background:var(--panel);border-radius:12px;padding:12px 14px;font-size:.94rem;break-inside:avoid}
.fcard b{display:block;font-size:.94rem}
.fcard .fx{font-family:ui-monospace,"JetBrains Mono",monospace;font-size:.86rem;background:var(--blue-soft);color:var(--ink);
border-radius:8px;padding:6px 9px;margin:6px 0;overflow-wrap:anywhere}
.fcard .fn{color:var(--mute);font-size:.88rem}
.toplist{columns:2 300px;column-gap:24px;font-size:.95rem;margin:0;padding:0;list-style:none}
.toplist li{break-inside:avoid;padding:3px 0}.toplist li span{color:var(--faint);font-size:.82rem;margin-right:8px}
/* ---------- focus mode ---------- */
.focus{position:fixed;inset:0;z-index:50;background:var(--bg);display:none;flex-direction:column}
.focus.open{display:flex}
body.locked{overflow:hidden}
.f-top{display:flex;align-items:center;gap:10px;padding:12px 20px;max-width:760px;width:100%;margin:0 auto}
.f-top b{flex:1;font-family:var(--serif);font-weight:600;font-size:1.05rem;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.f-top span{font-size:.85rem;color:var(--mute);white-space:nowrap;font-variant-numeric:tabular-nums}
.f-bar{height:3px;background:var(--line)}.f-bar i{display:block;height:100%;width:0;background:var(--green);transition:width .25s}
.f-body{flex:1;overflow-y:auto;padding:20px;width:100%;max-width:760px;margin:0 auto}
.f-card{background:var(--panel);border-radius:20px;padding:22px 20px;cursor:pointer}
.f-lab{display:block;font-size:.88rem;color:var(--mute);margin-bottom:10px}
.f-q{font-size:1.06rem}.f-q h4{margin:0 0 6px;font-family:var(--serif);font-size:1.35rem;font-weight:600;line-height:1.25}
.f-a{display:none;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
.f-card.rev .f-a{display:block}.f-card.rev .f-tap{display:none}
.f-tap{text-align:center;color:var(--faint);font-size:.9rem;margin:18px 0 0}
.f-prompt{color:var(--mute);font-size:.95rem;margin:0}
.f-btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 20px calc(14px + env(safe-area-inset-bottom));
max-width:760px;width:100%;margin:0 auto}
.f-btns button{border:0;border-radius:14px;padding:15px;font-weight:700;font-size:1rem;cursor:pointer}
.f-btns .fr{grid-column:span 2;background:var(--accent);color:#fff}
:root[data-theme=dark] .f-btns .fr{color:#1d1420}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .f-btns .fr{color:#1d1420}}
.f-btns .fa{background:var(--panel);color:var(--red);border:1px solid var(--line)}
.f-btns .fk{background:var(--green);color:#fff}
:root[data-theme=dark] .f-btns .fk{color:#0c1a11}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .f-btns .fk{color:#0c1a11}}
.f-btns kbd{font:inherit;font-size:.72rem;opacity:.6;margin-left:6px}@media (pointer:coarse){.f-btns kbd{display:none}}
.f-pick h3{margin:28px 0 8px;font-size:1.15rem}
.f-pick .pg{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.f-pick button{text-align:left;border:0;background:var(--panel);border-radius:12px;padding:11px 13px;cursor:pointer;font-size:.92rem;font-weight:700}
.f-pick button small{display:block;color:var(--mute);font-size:.82rem;font-weight:400}
.f-pick button.big{background:var(--accent);color:#fff;grid-column:1/-1;padding:16px}
.f-pick button.big small{color:inherit;opacity:.85}
:root[data-theme=dark] .f-pick button.big{color:#1d1420}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .f-pick button.big{color:#1d1420}}
.f-end{text-align:center;padding:40px 10px}.f-end .big{font-size:2.4rem;line-height:1;color:var(--green)}
/* ---------- one-day plan ---------- */
details.fold{margin:12px 0;font-size:.95rem}
details.fold>summary{cursor:pointer;padding:6px 0;color:var(--accent)}
details.fold>div{padding:4px 0 8px}
.emph{list-style:none;margin:0;padding:0}
.emph li{display:grid;grid-template-columns:2.2em 1fr;gap:2px 10px;border-top:1px solid var(--line);padding:8px 0}
.emph .sc9{font-weight:700;color:var(--accent);font-variant-numeric:tabular-nums}
.emph .ev{grid-column:2;color:var(--mute);font-size:.88rem}
.blks{list-style:none;margin:8px 0 0;padding:0;counter-reset:none}
.blk{min-width:0;background:var(--panel);border-radius:18px;padding:18px 20px;margin:12px 0}
.blk.isnext{box-shadow:inset 0 0 0 2px var(--accent)}
.blk .bh{display:grid;grid-template-columns:28px 1fr auto;gap:10px;align-items:baseline}
.blk .bn{width:26px;height:26px;border-radius:50%;background:var(--code);display:grid;place-items:center;font-size:.82rem;font-weight:700;color:var(--mute);align-self:start}
.blk.isnext .bn{background:var(--accent);color:#fff}
:root[data-theme=dark] .blk.isnext .bn{color:#1d1420}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .blk.isnext .bn{color:#1d1420}}
.blk.full .bn{background:var(--green);color:#fff}
.blk .bt{font-family:var(--serif);font-weight:600;font-size:1.18rem;line-height:1.3;min-width:0}
.blk.full .bt{color:var(--mute)}
.blk .bm{font-size:.88rem;color:var(--mute);white-space:nowrap}
.blk .bk{margin:10px 0 0;font-size:.98rem}
.lks{margin-top:14px;font-size:.94rem;display:grid;gap:8px}
.lg{display:grid;grid-template-columns:5.6em 1fr;gap:0 10px}
.lgl{color:var(--mute)}
.lgi{min-width:0}
.lk{color:var(--accent);background:none;border:0;padding:0;cursor:pointer;font-size:inherit;text-align:left;
text-decoration:underline;text-underline-offset:.18em;text-decoration-thickness:1px;text-decoration-color:color-mix(in srgb,var(--accent) 45%,transparent)}
.lk.isdone{color:var(--mute);text-decoration-line:line-through}
.lks.long .lg.x{display:none}.lks.long.all .lg.x{display:grid}
.lks .more{justify-self:start;margin-left:calc(5.6em + 10px)}
.lks.long.all .more{display:none}
@media (max-width:480px){.lg{grid-template-columns:1fr}.lks .more{margin-left:0}}
.blk .bf{display:flex;gap:14px;align-items:center;margin-top:16px;flex-wrap:wrap}
.blk .bf .bp{flex:1 1 60px;height:4px;border-radius:9px;background:var(--code);overflow:hidden;min-width:40px}
.blk .bf .bp i{display:block;height:100%;width:0;background:var(--green)}
.blk .bf .btn{order:-1}
/* ---------- banks: filters ---------- */
.filt{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:14px 0 4px}
.filt select{font:inherit;font-size:.9rem;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:6px 10px}
.filt .btn{margin-left:auto}
.shown{font-size:.9rem;color:var(--mute);margin:6px 0 0;font-variant-numeric:tabular-nums}
h3.gh{font-size:1.25rem;margin:36px 0 4px}
/* comparisons */
.qa.cmpc .q{display:flex}
.cmpc h4{margin:0 0 2px;font-size:1.04rem;line-height:1.35}
.cmpc .one{margin-top:6px;font-size:.96rem}
.cmpc .ans{padding:0 0 18px 20px}
.cmpc .cue{font-size:.94rem;margin-top:10px}.cmpc .cue b{color:var(--mute);font-size:.85rem;display:block}
.cmpc .meta{display:block;font-size:.85rem;color:var(--faint);margin-top:8px}
.cmpc table th:first-child,.cmpc table td:first-child{color:var(--mute);font-weight:700;width:24%}
/* worked examples */
.prob{background:var(--panel);border-radius:18px;margin:16px 0;padding:18px 20px}
.prob>header{display:block}
.prob h4{margin:0;font-size:1.08rem;line-height:1.35}
.prob .meta{display:block;font-size:.85rem;color:var(--mute);margin-top:4px}
.given{background:var(--blue-soft);border-radius:10px;padding:10px 14px;margin-top:12px;font-size:.96rem}
.given b,.prob h5{display:block;font-size:.85rem;color:var(--blue);margin:0 0 2px}
.prob h5{color:var(--mute);margin:18px 0 0;font-size:.9rem}
.qa.sol{border-top:0;font-size:.96rem;margin-top:4px}
.qa.sol .q{color:var(--blue);font-weight:700;padding:10px 0}
.qa.sol .ans{border-left:3px solid var(--blue);margin:0 0 6px;padding:2px 0 2px 14px}
.qa.sol .ans ol{margin:0;padding-left:1.3em}
.qa.prac{font-size:.96rem}
.qa.prac .ans{border-left:3px solid var(--blue);margin:0 0 12px 20px;padding:2px 0 2px 14px}
/* predicted papers */
.predban{margin:40px 0 8px}
.predban b{display:block;color:var(--mute);font-size:.9rem;font-weight:400}
.predban h3{margin:2px 0 4px;font-size:1.4rem}.predban p{margin:0;font-size:.92rem;color:var(--mute)}
.paper.pred{border-style:dashed}
.paper .why{background:var(--acc-soft);border-radius:8px;padding:8px 12px;font-size:.9rem;margin:6px 0 8px}
.paper .why b{color:var(--accent)}
.qa.mock .scn{margin-bottom:4px}
.orwk{font-size:.82rem;color:var(--mute);font-family:var(--sans);font-weight:400}
/* must-know */
.mkl{list-style:none;margin:8px 0 0;padding:0;columns:2 320px;column-gap:24px;font-size:.92rem;line-height:1.45}
.mkl li{break-inside:avoid;display:grid;grid-template-columns:22px 1fr;gap:8px;padding:6px 0;border-bottom:1px solid var(--line)}
.mkl button{width:18px;height:18px;border-radius:5px;border:1.5px solid var(--faint);background:var(--panel);padding:0;cursor:pointer;margin-top:2px;font-size:11px;line-height:1;color:#fff}
.mkl button.on{background:var(--green);border-color:var(--green)}.mkl button.on::after{content:"\2713"}
.mkl li.on span{color:var(--mute)}
/* ---------- misc ---------- */
.totop{position:fixed;right:16px;bottom:26px;z-index:19;width:42px;height:42px;border-radius:50%;border:1px solid var(--line);
background:var(--panel);color:var(--mute);font-size:1.1rem;cursor:pointer;
opacity:0;pointer-events:none;transition:opacity .2s}
.totop.show{opacity:1;pointer-events:auto}
@media (max-width:1099px){.totop{bottom:80px}}
.toast{position:fixed;left:50%;bottom:94px;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:9px 16px;
border-radius:12px;font-size:.92rem;z-index:60;display:none}
@media (max-width:640px){main{padding:0 16px 120px}.bar-in{padding:10px 16px}.hero{padding-top:28px}.hero h1{font-size:2rem}
.wkhead h2{font-size:1.65rem}.card,.blk,.prob{padding:16px;border-radius:16px;margin-left:-4px;margin-right:-4px}
.marks{grid-template-columns:1fr}.paper{padding:14px}.ans{padding-left:0}.qa.pool .ans,.qa.drill .ans,.qa.prac .ans{margin-left:0}
.cmpc .ans{padding-left:0}.go{font-size:1.06rem}}
@media print{
 body{background:#fff;font-size:9.2pt;line-height:1.38}
 .bar,.tabbar,.wkmenu,.focus,.totop,.toast,.noprint,#start,#dayplan,#cmp,#probs,.predsec,.mkl button,.toc,.afoot,.pills,.done,.back,.panhint,.st8,.tap,.prog,h3.sh .n{display:none!important}
 .opts{grid-template-columns:1fr 1fr;gap:0 12px}
 .view{display:block!important}main{max-width:none;padding:0}*{box-shadow:none!important;text-shadow:none!important}
 .ans{display:block!important;padding:5px 9px}.qa .q{padding:5px 0}.qa{margin:5px 0;break-inside:auto}
 .qa.pool .ans,.qa.drill .ans{margin:0 0 5px}
 .q{break-inside:avoid;break-after:avoid}
 .view{break-before:page}.wkhead{padding-top:0}
 .card{break-inside:auto;padding:8px 10px;margin:8px 0;border:1px solid #ddd}
 .fold-b{display:none!important}.fold-b[data-k=how],.fold-b[data-k=calc]{display:block!important}
 .fold-b[data-k=how]>:not(.dia){display:none!important}
 .dia{break-inside:avoid;padding:3px;margin:4px auto 6px;max-width:120mm}.dia svg{max-height:46mm;min-width:0!important}.dia figcaption{font-size:7.5pt;margin-top:1px}
 .lay li{margin:0}table{font-size:8.6pt}th,td{padding:3px 5px}
 h3.sh{margin:12px 0 6px}.card h4{break-after:avoid}.paper{padding:6px 10px;margin:8px 0}.paper>header{break-after:avoid}.qa.mock{break-inside:avoid}
 .fgrid{grid-template-columns:1fr 1fr}.fcard{border:1px solid #ddd}
 :root{--bg:#fff;--panel:#fff;--d-box:#fff7ed;--d-line:#b45309;--d-box2:#eff6ff;--d-line2:#1d4ed8;--d-box3:#ecfdf3;
 --d-line3:#15803d;--d-ink:#1c1b19;--d-mute:#78716c}
}
@page{size:A4;margin:11mm 10mm}
body.poolonly .cards-sec,body.poolonly #mock,body.poolonly #cmp,body.poolonly #probs,body.poolonly #sheet,body.poolonly .summary{display:none!important}

/* ---------- lecturer's files: provenance badges ---------- */
.ghbs{display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 0;line-height:1.2}
.ct .tm .ghbs{margin-top:5px}
.ghb{display:inline-flex;align-items:center;gap:4px;font:700 .76rem/1.25 var(--sans);letter-spacing:.01em;border-radius:6px;
padding:3px 7px 3px 6px;color:var(--accent);background:var(--acc-soft);border:1px solid color-mix(in srgb,var(--accent) 45%,transparent);white-space:normal}
.ghb::before{content:"";flex:none;width:.95em;height:.95em;background:currentColor;
-webkit-mask:var(--ic) center/contain no-repeat;mask:var(--ic) center/contain no-repeat}
.ghb.gs{--ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linejoin='round'%3E%3Cpath d='M6 2h9l5 5v15H6z'/%3E%3Cpath d='M14 2v6h6M9 13h7M9 17h5'/%3E%3C/svg%3E")}
.ghb.vl{--ic:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2l3 6.6 7.2.8-5.4 4.9 1.5 7.1L12 17.8 5.7 21.4l1.5-7.1L1.8 9.4 9 8.6z'/%3E%3C/svg%3E");
background:var(--accent);color:#fff;border-color:var(--accent)}
:root[data-theme=dark] .ghb.vl{color:#1d1420}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .ghb.vl{color:#1d1420}}
.ghb.gc{background:transparent;color:var(--mute);border-color:var(--line)}
.ghb.gc::before{display:none}
.lay.trap li .ghbs{margin-top:4px}
.ghn{margin:14px 0 0;border-left:3px solid var(--accent);background:var(--acc-soft);border-radius:0 10px 10px 0;padding:8px 14px;font-size:.95rem}
.ghn b.l{display:block;font-size:.85rem;color:var(--accent);margin-bottom:2px}
.ghn p{margin:.3em 0}
/* ---------- lecturer's files: home entry + section ---------- */
.chnav li.lnav{border-top:0;margin:8px 0;background:var(--acc-soft);border-radius:14px;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--accent) 35%,transparent)}
.chnav li.lnav+li{border-top:0}
.chnav li.lnav a{padding:14px 16px}
.chnav li.lnav b{color:var(--accent)}
.chnav li.lnav .chev{color:var(--accent);font-size:1.4rem;line-height:1}
.lect{margin-top:64px;padding-top:8px;border-top:3px solid var(--accent)}
.lhead small{color:var(--accent);font-size:.95rem;display:block;font-weight:700}
.lhead h2{font-size:1.75rem;line-height:1.15;margin:2px 0 8px}
.lhead p{margin:0;color:var(--mute);font-size:.95rem;max-width:62ch}
.lhead p .ghb{vertical-align:1px}
h3.lw{font-size:1.2rem;margin:30px 0 4px}
h3.lw span{font:400 .88rem var(--sans);color:var(--mute);margin-left:6px}
.lects{list-style:none;margin:0;padding:0}
.lects li{border-top:1px solid var(--line)}
.lects li:last-child{border-bottom:1px solid var(--line)}
.lects a{display:block;padding:11px 0;min-height:44px;text-decoration:none;color:var(--ink)}
.lects a:hover b{color:var(--accent)}
.lects .lt{display:block}
.lects .lt b{display:block;font-weight:700;line-height:1.35}
.lects .lk2{display:block;font-size:.85rem;color:var(--mute);margin-top:1px}
:root[data-theme=dark] .btn.ghost,:root[data-theme=dark] .btn.warn{color:var(--accent)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .btn.ghost,:root:not([data-theme=light]) .btn.warn{color:var(--accent)}}
:root[data-theme=dark] .btn.warn{color:var(--red)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .btn.warn{color:var(--red)}}
h4.ghh{margin:22px 0 2px;font-size:.95rem}
h4.ghh.plain{font-family:var(--serif);font-size:1.1rem;font-weight:600}
/* ---------- tap targets (44 px) and readability ---------- */
.chip{min-height:44px;min-width:44px;display:inline-flex;align-items:center;justify-content:center}
.chip.ico{font-size:1.15rem}
.tick{width:44px;height:44px;margin:3px -9px 0 -9px;border:0;background:none;position:relative;border-radius:10px}
.tick::before{content:"";position:absolute;inset:9px;border-radius:8px;border:1.5px solid var(--faint);background:var(--panel)}
.ci.on .tick{background:none}
.ci.on .tick::before{background:var(--green);border-color:var(--green)}
.ci.on .tick::after{position:relative;color:#fff}
:root[data-theme=dark] .ci.on .tick::after{color:#0c1a11}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .ci.on .tick::after{color:#0c1a11}}
.ci[data-st=a]:not(.on) .tick{background:none}
.ci[data-st=a]:not(.on) .tick::before{border-color:var(--red);background:var(--red-soft)}
.ct{min-height:44px}
.mk button,.btn.sm{min-height:44px;padding-top:0;padding-bottom:0;display:inline-flex;align-items:center;justify-content:center}
.link.show{min-height:44px;display:inline-flex;align-items:center}
.afoot>a,.cb .more a,.brand{min-height:44px;display:inline-flex;align-items:center}
.cb .more{margin-top:8px}
.cb .fq,.cb .pans,.cb .given{max-width:68ch}
.cb .pans ol,.cb .pans ul{padding-left:1.25em}
.cb .pans li+li{margin-top:4px}
.cb .pans .fine,.ghn .fine{margin-top:10px}
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
$('#all').onclick=()=>{B.classList.toggle('all');$('#all').classList.toggle('on');closeMenus()};
const toast=(t)=>{const el=$('#toast');el.textContent=t;el.style.display='block';clearTimeout(toast.t);toast.t=setTimeout(()=>el.style.display='none',1800)};
/* greeting with days left */
(()=>{const d=Math.ceil((EXAM-new Date(new Date().toDateString()))/864e5);const el=$('#greet');if(!el)return;
 const h=new Date().getHours(),g=h<5?'Still up?':h<12?'Good morning.':h<18?'Good afternoon.':'Good evening.';
 const W=['Zero','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten'];
 el.textContent=g+' '+(d>1?(W[d]||d)+' days to go.':d===1?'The exam is tomorrow.':d===0?'It’s exam day.':'The exam is done.')})();
/* ---------- progress carried over from the day plan ----------
   A block ticked in the old one-day plan means its linked topics, questions and papers were done: fill those
   in once, without overwriting a "review again" mark. */
$$('.blk').forEach(b=>{const sid=b.dataset.sid;if(!S.s[sid]||S.s['ckm-'+sid])return;
 (b.dataset.items||'').split(' ').filter(Boolean).forEach(id=>{const t=document.getElementById(id);if(!t)return;
  if(t.classList.contains('card'))S.c[id]=1;else if(!S.m[id])S.m[id]='k'});
 (b.dataset.papers||'').split(' ').filter(Boolean).forEach(p=>S.s['ck-'+p]=1);
 S.s['ckm-'+sid]=1;save()});
/* ---------- progress ---------- */
const isDone=(el)=>el.classList.contains('card')?!!S.c[el.id]:S.m[el.dataset.id]==='k';
const itemDone=(el)=>el.classList.contains('card')?!!S.c[el.id]:el.dataset.id?S.m[el.dataset.id]==='k':false;
const ckOn=(li)=>{const k=li.dataset.key,t=li.dataset.kind;return t==='card'?!!S.c[k]:t==='m'?S.m[k]==='k':!!S.s[k]};
function ckToggle(li){const k=li.dataset.key,t=li.dataset.kind,on=ckOn(li);
 if(t==='card'){on?delete S.c[k]:S.c[k]=1}else if(t==='m'){on?delete S.m[k]:S.m[k]='k'}else{on?delete S.s[k]:S.s[k]=1}
 save();paint()}
function mark(id,m){if(S.m[id]===m)delete S.m[id];else S.m[id]=m;save();paint()}
function setBar(el,f){const i=el&&$('i',el);if(i)i.style.width=(100*f).toFixed(1)+'%'}
function stats(w){const sel=w?'[data-w="'+w+'"]':'';
 const P=$$('.qa.pool'+sel),C=$$('.card'+sel),R=$$('.qa.drill'+sel);
 const p=P.filter(isDone).length,c=C.filter(isDone).length,r=R.filter(isDone).length;
 return{p,P:P.length,c,C:C.length,r,R:R.length,f:(p+c+r)/Math.max(1,P.length+C.length+R.length)}}
const plural=(n,a,b)=>n+' '+(n===1?a:(b||a+'s'));
function paint(){
 $$('[data-id]').forEach(el=>{const s=S.m[el.dataset.id]||'';if(el.dataset.st!==s)el.dataset.st=s});
 $$('.card').forEach(el=>el.classList.toggle('isdone',!!S.c[el.id]));
 $$('.toc li[data-c]').forEach(li=>li.classList.toggle('isdone',!!S.c[li.dataset.c]));
 $$('.prog[data-pw]').forEach(el=>{const s=stats(el.dataset.pw==='all'?'':el.dataset.pw);setBar($('.pbar',el),s.f);
  $('.ptxt',el).textContent=s.p+' of '+s.P+' exam questions, '+s.c+' of '+s.C+' topics and '+s.r+' of '+s.R+' practice questions done.'});
 $$('.wpct').forEach(e=>e.textContent=Math.round(100*stats(e.dataset.wp).f)+'%');
 /* checklist */
 const all=$$('.ci');let done=0,next=null;
 all.forEach(li=>{const on=ckOn(li);li.classList.toggle('on',on);if(on)done++;else if(!next)next=li});
 $$('.chap').forEach(ch=>{const its=$$('.ci',ch),d=its.filter(li=>li.classList.contains('on')).length,f=d/Math.max(1,its.length);
  setBar($('.pbar',ch),f);const pt=$('.ptxt',ch);
  if(pt)pt.textContent=d===its.length?'All '+its.length+' done.':d+' of '+its.length+' done. About '+pt.dataset.mins+' minutes in all.';
  $$('.cpct[data-cw="'+ch.dataset.cw+'"]').forEach(e=>{e.textContent=d===its.length?'Done':d+' of '+its.length;e.classList.toggle('full',d===its.length)})});
 if(all.length){const f=done/all.length;setBar($('.todayp'),f);setBar($('.obar'),f);
  $$('.opct').forEach(e=>e.textContent=Math.round(100*f)+'%');
  const ap=$('#allp');if(ap)ap.textContent=done===0?'Nothing ticked yet. '+all.length+' items to go.':done+' of '+all.length+' items ticked.';
  const go=$('#nextopen');if(go){go.hidden=!next;if(next){$('.nt',go).textContent=(done?'Continue: ':'Start: ')+$('.tt',next).textContent;go.setAttribute('href','#'+next.id)}}
  $$('.complete').forEach(c=>c.hidden=!!next)}
 /* old day plan */
 $$('.sess').forEach(el=>{const ids=(el.dataset.items||'').split(' ').filter(Boolean);let f;
  if(ids.length){const k=el.dataset.kind;f=ids.filter(id=>k==='card'?S.c[id]:S.m[id]==='k').length/ids.length}
  else f=S.s[el.dataset.sid]?1:0;
  el.classList.toggle('full',f>=1);setBar($('.sbar',el),f)});
 $$('[data-tick]').forEach(b=>{const on=!!S.s[b.dataset.tick];b.classList.toggle('on',on);const li=b.closest('.mkl li');if(li)li.classList.toggle('on',on)});
 $$('.lk[href]').forEach(a=>{const t=document.getElementById(a.getAttribute('href').slice(1));a.classList.toggle('isdone',!!t&&itemDone(t))});
 let nb=null;
 $$('.blk').forEach(el=>{const ids=(el.dataset.items||'').split(' ').filter(Boolean);
  const d=ids.filter(id=>{const t=document.getElementById(id);return t&&itemDone(t)}).length;
  const f=ids.length?d/ids.length:0,full=!!S.s[el.dataset.sid];
  el.classList.toggle('full',full);setBar($('.bp',el),full?1:f);el.classList.remove('isnext');if(!nb&&!full)nb=el});
 if(nb)nb.classList.add('isnext');
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
 $$('select[data-f]',sec).forEach(s=>s.value=f[s.dataset.f]);
 const its=$$('.bitem',sec);its.forEach(el=>{const ok=(!f.w||el.dataset.w===f.w)&&(!f.l||el.dataset.l===f.l);el.hidden=!ok;n+=ok});
 $$('.gh',sec).forEach(h=>{let e=h.nextElementSibling,any=false;while(e&&!e.classList.contains('gh')){if(!e.hidden)any=true;e=e.nextElementSibling}h.hidden=!any});
 const k=its.filter(x=>!x.hidden&&S.m[x.dataset.id||'']==='k').length;
 const sh=$('.shown',sec);if(sh)sh.textContent=(n===its.length?'Showing all '+n:'Showing '+n+' of '+its.length)+(v==='cmp'?', '+k+' marked got it.':'.')}
document.addEventListener('change',e=>{const s=e.target.closest('select[data-f]');if(!s)return;const v=s.closest('.view').id;FL[v][s.dataset.f]=s.value;applyF(v)});
/* ---------- router ---------- */
let cur=null;
function route(h){let el=h&&document.getElementById(h);if(!el)el=$('#start');
 const view=el.classList.contains('view')?el:el.closest('.view');if(!view)return;
 if(el!==view&&el.closest('[hidden]')&&FL[view.id]){FL[view.id]={w:'',l:''};applyF(view.id)}
 const dt=el.closest('details');if(dt)dt.open=true;
 if(cur&&cur!==view)S.y[cur.id]=scrollY;
 $$('.view').forEach(v=>v.classList.toggle('cur',v===view));cur=view;
 const fb=el.closest('.fold-b');if(fb)setFold(fb.closest('.card'),fb.dataset.k,true);
 if(el.classList.contains('qa')||el.classList.contains('ci'))el.classList.add('open');centerPans(view);
 if(el===view)scrollTo(0,S.y[view.id]||0);
 else{el.scrollIntoView({block:'start'});el.classList.remove('hl');void el.offsetWidth;el.classList.add('hl')}
 S.v=view.id;save();closeMenus();
 document.title=(view.dataset.title?view.dataset.title+', ':'')+'BDA final'}
function go(h){history.pushState(null,'','#'+h);route(h)}
addEventListener('popstate',()=>route(location.hash.slice(1)));
let scT=0;addEventListener('scroll',()=>{$('#totop').classList.toggle('show',scrollY>700);
 clearTimeout(scT);scT=setTimeout(()=>{if(cur){S.y[cur.id]=scrollY;save()}},300)},{passive:true});
$('#totop').onclick=()=>scrollTo({top:0,behavior:'smooth'});
const closeMenus=()=>$('#wkmenu').classList.remove('open');
/* ---------- clicks ---------- */
document.addEventListener('click',e=>{const t=e.target;
 const m=t.closest('[data-m]');if(m){const it=m.closest('[data-id]');if(it){mark(it.dataset.id,m.dataset.m);
  const li=m.closest('.ci');if(li&&S.m[it.dataset.id]==='k'){li.classList.remove('open')}}return}
 const f=t.closest('[data-focus]');if(f){e.preventDefault();startDeck(f.dataset.focus);return}
 if(t.closest('#focus'))return;
 if(t.closest('#menubtn')){$('#wkmenu').classList.toggle('open');return}
 const tk=t.closest('.tick');if(tk){ckToggle(tk.closest('.ci'));return}
 const ct=t.closest('.ct');if(ct){const li=ct.closest('.ci');li.classList.toggle('open');if(li.classList.contains('open'))centerPans(li);return}
 const sh=t.closest('[data-show]');if(sh){const fa=sh.nextElementSibling;if(fa){fa.classList.add('open');centerPans(fa)}sh.hidden=true;return}
 const mo=t.closest('[data-more]');if(mo){mo.closest('.lks').classList.add('all');return}
 const tick=t.closest('[data-tick]');if(tick){const k=tick.dataset.tick;S.s[k]?delete S.s[k]:S.s[k]=1;save();paint();return}
 const dn=t.closest('.done');if(dn){const id=dn.closest('.card').id;S.c[id]?delete S.c[id]:S.c[id]=1;save();paint();return}
 const pl=t.closest('.pill');if(pl){setFold(pl.closest('.card'),pl.dataset.k,!pl.classList.contains('on'));return}
 if(t.closest('#reset')){if(confirm('Clear every tick and mark on this device?')){const v=S.v;S=blank();S.v=v;$$('.blk').forEach(b=>S.s['ckm-'+b.dataset.sid]=1);save();paint();toast('Progress cleared')}return}
 const a=t.closest('a[href^="#"]');if(a){e.preventDefault();go(a.getAttribute('href').slice(1));return}
 const q=t.closest('.qa .q');if(q&&!t.closest('a,button')){q.parentNode.classList.toggle('open');centerPans(q.parentNode);return}
 if(!t.closest('#wkmenu'))closeMenus()});
document.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const q=e.target.closest&&e.target.closest('.qa .q');
 if(q&&!F){e.preventDefault();q.parentNode.classList.toggle('open')}}if(e.key==='Escape')closeMenus()});
/* ---------- focus mode ---------- */
const FX=$('#focus');let F=null,figN=0;
function cloneAns(el){const c=el.cloneNode(true);$$('.afoot',c).forEach(x=>x.remove());
 $$('.dialink',c).forEach(a=>{const fig=document.getElementById(a.getAttribute('href').slice(1));if(!fig)return;
  const n=++figN,fc=fig.cloneNode(true);fc.removeAttribute('id');let h=fc.innerHTML;
  $$('[id]',fc).forEach(x=>{const id=x.id;h=h.split('id="'+id+'"').join('id="'+id+'-f'+n+'"').split('#'+id+')').join('#'+id+'-f'+n+')')});
  fc.innerHTML=h;(a.closest('p')||a).replaceWith(fc)});
 return c.innerHTML}
const ttl=(el)=>$('h4',el).firstChild.textContent;
function itemOf(el){const lab=el.dataset.lab||'';
 if(el.classList.contains('cmpc')){const t=$('.tw',el);
  return{id:el.dataset.id,kind:'cmp',tag:lab,q:'<h4>'+ttl(el)+'?</h4><p class="f-prompt">Say the key difference, then the scenario that points to each side.</p>',
   a:$('.one',el).outerHTML+$('.cue',el).outerHTML+(t?t.outerHTML:'')}}
 if(el.classList.contains('prac')){const pr=el.closest('.prob');
  return{id:el.dataset.id,kind:'prac',tag:lab,
   q:'<p class="f-prompt">'+ttl(pr)+'</p>'+$('.q .txt',el).innerHTML,a:cloneAns($('.ans',el))}}
 if(el.classList.contains('card')){const tr=$('.lay.trap',el),sc=$('.lay.scen',el);
  return{id:el.id,kind:'card',tag:lab,
   q:'<h4>'+ttl(el)+'</h4><p class="f-prompt">Say the one-line answer, then the traps, then which scenarios point here.</p>',
   a:$('.one',el).outerHTML+tr.outerHTML+sc.outerHTML}}
 return{id:el.dataset.id,kind:el.classList.contains('pool')?'pool':'drill',tag:lab,
  q:$('.q .txt',el).innerHTML,a:cloneAns($('.ans',el))}}
function deck(spec){const [k,v]=spec.split(':');let els=[],title='';
 if(k==='sess'){const s=$('.sess[data-sid="'+v+'"]');if(!s)return[[],''];title=$('.st',s).textContent;
  els=s.dataset.items.split(' ').filter(Boolean).map(id=>document.getElementById(id)).filter(Boolean)}
 else if(k==='next'){const nx=$('.ci:not(.on)');if(!nx)return[[],''];const ch=nx.closest('.chap');
  return ch&&ch.dataset.cw!=='m'?deck('pool:'+ch.dataset.cw):[[],'']}
 else if(k==='pool'||k==='drill'){els=$$('.qa.'+k+'[data-w="'+v+'"]');title='Week '+v+(k==='pool'?' exam questions':' practice')}
 else if(k==='card'){els=$$('.card[data-w="'+v+'"]');title='Week '+v+' topics: traps and scenarios'}
 else if(k==='again'){els=$$('.qa.pool,.qa.drill,.cmpc,.qa.prac').filter(e=>S.m[e.dataset.id]==='a');title='Review pile'}
 else if(k==='blk'){const b=document.getElementById('blk'+v.slice(1));if(!b)return[[],''];title=$('.bt',b).textContent;
  const seen=new Set();els=b.dataset.items.split(' ').filter(Boolean).map(id=>document.getElementById(id)).filter(e=>e&&!seen.has(e)&&seen.add(e))}
 else if(k==='cmp'||k==='probs'){const sel=k==='cmp'?'.cmpc':'.qa.prac';const f=FL[k];const nm=k==='cmp'?'Compare':'Worked examples';
  if(v==='f'){els=$$(sel).filter(e=>(!f.w||e.dataset.w===f.w)&&(!f.l||(e.closest('.bitem')||e).dataset.l===f.l));title=nm+(f.w?', week '+f.w:'')}
  else{els=$$(sel).filter(e=>!v||v==='all'||e.dataset.w===v);title=nm+(v&&v!=='all'?', week '+v:'')}}
 else if(k==='src'){els=$$('.qa.pool').filter(e=>e.dataset.id.includes('-'+v+'-'));title=(v==='mcq'?'Multiple choice':'True or false')+', every week'}
 else if(k==='traps'){els=$$('.card');title='Every topic: one-liner, traps, scenarios'}
 else if(k==='one'){title='Every topic in one line';
  return[$$('.card').filter(c=>!v||c.dataset.w===v).map(c=>({id:'o-'+c.id,kind:'one',tag:'Week '+c.dataset.w+' one-liner',
   q:'<h4>'+ttl(c)+'</h4><p class="f-prompt">Say it in one line.</p>',a:$('.one',c).outerHTML})),title]}
 return[els.map(itemOf),title]}
function openFX(){FX.classList.add('open');B.classList.add('locked');closeMenus()}
function closeFX(){FX.classList.remove('open');B.classList.remove('locked');F=null;paint()}
function startDeck(spec){if(spec==='pick')return pick();const [items,title]=deck(spec);
 if(!items.length){toast(spec==='again'?'Nothing marked review again yet':'Nothing to quiz here');return}
 F={map:new Map(items.map(i=>[i.id,i])),q:items.map(i=>i.id),title,total:items.length,known:0,again:0,rev:false};openFX();show()}
function pick(){F=null;openFX();$('#f-title').textContent='Focus mode';$('#f-count').textContent='';setBar($('.f-bar'),0);
 $('#f-btns').innerHTML='';$('#f-body').innerHTML=$('#pickt').innerHTML;
 const ag=Object.values(S.m).filter(v=>v==='a').length;$$('#f-body .againn').forEach(e=>e.textContent=ag);
 const nx=$('.ci:not(.on)'),ch=nx&&nx.closest('.chap'),sm=$('#f-body [data-focus="next"] small');
 if(sm)sm.textContent=ch&&ch.dataset.cw!=='m'?'Week '+ch.dataset.cw+' exam questions':'Checklist done'}
function show(){const body=$('#f-body'),btns=$('#f-btns');$('#f-title').textContent=F.title;
 setBar($('.f-bar'),F.known/F.total);
 if(!F.q.length){$('#f-count').textContent='';body.innerHTML='<div class="f-end"><div class="big">&#10003;</div><h2>All done</h2><p>'+plural(F.total,'card')+', '+plural(F.again,'repeat')+'.</p></div>';
  btns.innerHTML='<button class="fk" data-fx="pick">Another set</button><button class="fa" data-fx="close" style="color:var(--ink)">Close</button>';return}
 const it=F.map.get(F.q[0]);F.rev=false;
 $('#f-count').textContent=F.q.length+' left';
 body.innerHTML='<div class="f-card" id="f-card"><span class="f-lab">'+it.tag+'</span><div class="f-q">'+it.q+'</div><div class="f-a">'+it.a+'</div><p class="f-tap">Tap to see the answer</p></div>';
 body.scrollTop=0;btns.innerHTML='<button class="fr" data-fx="rev">Show the answer<kbd>space</kbd></button>'}
function reveal(){if(!F||F.rev||!F.q.length)return;F.rev=true;$('#f-card').classList.add('rev');centerPans($('#f-card'));
 $('#f-btns').innerHTML='<button class="fa" data-fx="a">Review again<kbd>1</kbd></button><button class="fk" data-fx="k">Got it<kbd>2</kbd></button>'}
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


def svg_inline(path, sfx=""):
    """Inline an SVG with a per-figure min width so its smallest text renders at >= 11 px on a phone.
    sfx renames the SVG's internal ids so a second copy on the page doesn't clash with the first."""
    svg = re.sub(r"<\?xml[^>]*>", "", (ROOT / path).read_text()).strip()
    if sfx:
        for i in set(re.findall(r'\sid="([^"]+)"', svg)):
            svg = svg.replace(f'id="{i}"', f'id="{i}{sfx}"').replace(f"#{i})", f"#{i}{sfx})").replace(f'"#{i}"', f'"#{i}{sfx}"')
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    sizes = [float(x) for x in re.findall(r"font-size[:=]\"?\s*([\d.]+)", svg)] or [12]
    minw = math.ceil(float(vb.group(1)) * 11 / min(sizes)) if vb else 640
    return svg.replace("<svg ", f'<svg style="--minw:{minw}px" ', 1)


def figure(file, caption="", fid="", sfx=""):
    if not file or not (ROOT / file).exists():
        return ""
    idattr = f' id="{fid}"' if fid else ""
    cap = f"<figcaption>{caption}</figcaption>" if caption else ""
    return (f'<figure class="dia"{idattr}><div class="pan">{svg_inline(file, sfx)}</div>'
            f'<div class="panhint">swipe sideways to see the whole diagram</div>{cap}</figure>')


def marks_btns():
    return '<span class="mk"><button data-m="a">Review again</button><button data-m="k">Got it</button></span>'


# ---------------------------------------------------------------- lecturer's GitHub provenance
GH_LABEL = {"plan": "Lecturer's plan", "topic": "Lecturer: important exam topic", "v1": "Old slides (v1)"}
GH = {"items": [], "list": []}  # new items (extra/gh_sweep.json) and the index for the home-screen list


def gh_label(s):
    return GH_LABEL.get(s) or (f"Lecturer's textbook ch {s[4:]}" if s.startswith("book") else s)


def gh_badges(g):
    """Small provenance badges: Very likely first, then each source, then the CLO."""
    if not g:
        return ""
    out = ['<span class="ghb vl">Very likely</span>'] if g.get("vl") else []
    out += [f'<span class="ghb gs">{esc(gh_label(x))}</span>' for x in g.get("src", [])]
    if g.get("clo"):
        out.append(f'<span class="ghb gc">{esc(g["clo"])}</span>')
    return f'<span class="ghbs">{"".join(out)}</span>'


def gh_extra(g):
    """The note or old-slides model justification that an enriched item gains, shown under its answer."""
    if not g:
        return ""
    parts = []
    if g.get("just"):
        parts.append(f'<p><b>Model justification (old slides):</b> {g["just"]}</p>')
    if g.get("note"):
        parts.append(f'<p>{g["note"]}</p>')
    return f'<div class="ghn"><b class="l">From the lecturer&rsquo;s files</b>{"".join(parts)}</div>' if parts else ""


def pool_code(p):
    """How a pool question is named in the interface: Q2, TF1, D1, A2, Discussion 1, L1."""
    n = str(p.get("n", ""))
    return {"True/False": f"TF{n}", "Discussion": f"Discussion {n}"}.get(p["src"], n)


def pool_label(w, p):
    """'Week 6 exam question D1 (descriptive)'."""
    src, n = p["src"], str(p.get("n", ""))
    if src == "Discussion":
        return f"Week {w} discussion question {n}"
    if src == "Live Exercise":
        return f"Week {w} live exercise {n}"
    return f"Week {w} exam question {pool_code(p)} ({SRC_KIND[src]})"


# ---------------------------------------------------------------- pool

def pool_minutes(p):
    return 0.5 + (words(p["q"]) + words(p["a"]) + words(p.get("code")) + words(" ".join(p.get("options") or []))) / 90


def dialink(t):
    return (f'<p class="dl"><a class="dialink" href="#fig-{t["id"]}">See the diagram on the topic &ldquo;{esc(t["title"])}&rdquo;</a></p>')


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
    link = f'<a class="tocard" href="#{t["id"]}">Topic: {esc(t["title"])}</a>' if t else "<span></span>"
    return (f'<article class="qa pool" id="{pid}" data-id="{pid}" data-w="{w}" data-lab="{esc(pool_label(w, p))}">'
            f'<div class="q" tabindex="0"><span class="st8"></span><span class="num">{esc(p.get("n", ""))}</span>'
            f'<div class="txt">{p["q"]}{opts}{cd}{gh_badges(p.get("gh"))}</div></div>'
            f'<div class="ans">{pool_answer(p, t)}{gh_extra(p.get("gh"))}<div class="afoot">{link}{marks_btns()}</div></div></article>')


def pool_items_sorted(d):
    return sorted(d["pool"], key=lambda p: SRC_ORDER.index(p["src"]))


def pool_section(d, tops):
    w = d["week"]
    out = [f'<h3 class="sh" id="w{w}-pool">Exam questions <span class="n">The {len(d["pool"])} questions from the slides. '
           "Tap one to see the answer, then mark it.</span></h3>"]
    last = None
    for p in pool_items_sorted(d):
        if p["src"] != last:
            last = p["src"]
            n = sum(1 for x in d["pool"] if x["src"] == last)
            out.append(f'<h4 class="grp" id="w{w}-pool-{SRC_CLASS[last]}">{SRC_GROUP[last]} ({n})</h4>')
        out.append(pool_item(d, p, tops))
    return "".join(out)


# ---------------------------------------------------------------- cards

def _plain(s):
    return html.escape(re.sub(r"<[^>]+>", "", html.unescape(str(s or ""))).strip())


def stack_table(head, rows, cls="", cell=lambda x: x):
    """A table that turns into stacked 'criterion -> X / Y' rows on a phone (CSS .stk)."""
    if not head:
        body = "".join("<tr>" + "".join(f"<td>{cell(x)}</td>" for x in r) + "</tr>" for r in rows)
        return f'<div class="tw"><table class="{cls}">{body}</table></div>'
    h = "<thead><tr>" + "".join(f"<th>{cell(x)}</th>" for x in head) + "</tr></thead>"
    body = "".join("<tr>" + "".join(
        f'<td data-h="{_plain(head[j]) if j < len(head) else ""}">{cell(x)}</td>' for j, x in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="stk {cls}">{h}<tbody>{body}</tbody></table></div>'


def contrast_tables(cs):
    return "".join(stack_table(c.get("head"), c["rows"]) for c in cs)


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
        fmt = FORMAT_NAMES.get(q["format"], q["format"])
        out.append(f'<div class="qa drill" id="{did}" data-id="{did}" data-w="{w}" data-lab="Week {w} practice: {esc(t["title"])} ({fmt.lower()})">'
                   f'<div class="q" tabindex="0"><span class="st8"></span><div class="txt">{q["q"]}{opts}</div>'
                   f'<span class="tag">{fmt}</span></div>'
                   f'<div class="ans">{a}<div class="afoot"><span></span>{marks_btns()}</div></div></div>')
    return "".join(out)


def card(t, w, pool_refs):
    calc = t.get("calculation")
    a = t["answers"]
    folds = [
        ("facts", "Facts", "", f'<div class="lay"><h5>Facts</h5>{ul(t["facts"])}</div>'),
        ("how", "How it works" + (" (with diagram)" if t.get("diagram") else ""), "",
         (figure(t["diagram"]["file"], t["diagram"].get("caption", ""), f"fig-{t['id']}") if t.get("diagram") else "")
         + f'<div class="lay"><h5>How it works</h5>{ul(t["mechanism"], "ol")}</div>'),
        ("why", "Why it matters", "", f'<div class="lay"><h5>Why it matters, pros and limits</h5>{ul(t["why"])}</div>'),
        ("cmp", "Compare", "", f'<div class="lay"><h5>Compare</h5>{contrast_tables(t["contrasts"])}</div>'),
    ]
    if calc:
        folds.append(("calc", "Worked example", "calc",
                      f'<div class="lay calc"><h5>Worked example</h5>{calc["example"]}'
                      f'<p><b>Step by step</b></p>{ul(calc["steps"], "ol")}'
                      f'<p><b>Variants</b></p>{ul(calc["variants"])}</div>'))
    folds.append(("marks", "Longer answers", "",
                  f'<div class="lay"><h5>3-mark and 5-mark answers (the 1-mark answer is the line at the top)</h5><div class="marks">'
                  f'<b>3 marks</b><div>{a["3"]}</div><b>5 marks</b><div>{a["5"]}</div></div></div>'))
    folds.append(("drill", f"Practice ({len(t['questions'])})", "drl",
                  f'<div class="lay"><h5>Practise this topic in {len(t["questions"])} question styles</h5>{drill_items(t, w)}</div>'))
    pills = "".join(f'<button class="pill {c}" data-k="{k}">{lab}</button>' for k, lab, c, _ in folds)
    bodies = "".join(f'<div class="fold-b" data-k="{k}">{body}</div>' for k, _, _, body in folds)
    refs = pool_refs.get(t["id"], [])

    def lst(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
    back = ('<div class="back"><span>Exam questions on this:</span>' + lst([
        f'<a href="#{p["_id"]}">{esc(pool_code(p))}</a>' for p in refs]) + "</div>") if refs else \
        '<div class="back"><span>No exam question on this topic, so use the practice questions.</span></div>'
    cl = EXTRA["cmp_by_card"].get(t["id"], [])
    if cl:
        back += ('<div class="back"><span>Compare:</span>' + lst([
            f'<a href="#c-{c["id"]}">{esc(short(cmp_title(c), 40))}</a>' for c in cl]) + "</div>")
    pl = EXTRA["prob_by_card"].get(t["id"], [])
    if pl:
        back += ('<div class="back"><span>Worked examples:</span>' + lst([
            f'<a href="#x-{x["id"]}">{esc(short(x["title"], 40))}</a>' for x in pl]) + "</div>")
    sc = stack_table(["If the question describes…", "Answer"], [[s["cue"], s["answer"]] for s in t["scenarios"]], "sc")
    return (f'<article class="card" id="{t["id"]}" data-w="{w}" data-lab="Week {w} topic"><header><h4>{esc(t["title"])}</h4>'
            f'<button class="done"><span class="n">Mark done</span><span class="y">&#10003; Done</span></button></header>'
            f'<div class="one"><b class="l">In one line</b>{a["1"]}</div>'
            f'<div class="lay trap"><h5>Traps</h5>{ul(t["traps"])}</div>'
            f'<div class="lay scen"><h5>Spot it in a scenario</h5>{sc}</div>'
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
            groups.append(f'<a href="#w{w}-pool-{SRC_CLASS[s]}">{SRC_GROUP[s].lower()}</a>')
    cardlist = "".join(
        f'<li data-c="{t["id"]}"><a href="#{t["id"]}">{esc(t["title"])}</a></li>'
        for t in d["topics"])
    ndr = sum(len(t["questions"]) for t in d["topics"])
    return (f'<section class="view week" id="w{w}" data-title="Week {w}: {esc(d["title"])}">'
            f'<header class="wkhead"><small>Week {w}</small><h2>{esc(d["title"])}</h2>'
            f'<p class="summary">{d["summary"]}</p>'
            f'<div class="prog" data-pw="{w}"><div class="pbar"><i></i></div><span class="ptxt"></span></div></header>'
            f'<nav class="toc" aria-label="In this week">'
            f'<div class="row"><span class="lbl">Quiz me on</span>'
            f'<button class="mini" data-focus="pool:{w}">exam questions</button>'
            f'<button class="mini" data-focus="card:{w}">topics</button>'
            f'<button class="mini" data-focus="drill:{w}">practice</button>'
            f'<button class="mini" data-focus="one:{w}">one-liners</button></div>'
            f'<div class="row"><span class="lbl">Jump to</span>{", ".join(groups)}, <a href="#w{w}-cards">topics</a></div>'
            f'<ol>{cardlist}</ol></nav>'
            + pool_html
            + f'<div class="cards-sec"><h3 class="sh" id="w{w}-cards">Topics <span class="n">{len(d["topics"])} topics, {ndr} practice questions. '
              "Each starts with the answer, the traps and the scenarios; tap a heading underneath for the rest.</span></h3>"
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
    out = ['<section class="view" id="mock" data-title="Mock paper"><header class="wkhead"><small>Mock papers</small>'
           "<h2>Mock final paper</h2>"
           '<p class="summary">One 10-mark question per chapter, in the shape of the October 2026 Data Mining final from '
           "the same department: a short scenario, then short parts. Answer either the main pair or the OR pair. "
           "Tap a part for its model answer.</p></header>"
           + ('<div class="toc noprint"><div class="row"><span class="lbl">Jump to</span><a href="#mock-q1">the mock (all six chapters)</a>'
              '<a href="#pred-A">predicted paper A</a><a href="#pred-B">predicted paper B</a></div></div>' if pred_html else "")]
    nsplit = 0
    for i, d in enumerate(chs, 1):
        m = d["mock"]
        out.append(f'<div class="paper" id="mock-q{i}"><header><b>Question {i}</b><span>Week {d["week"]}, 10 marks</span></header>')
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
                           f'<span>{p["marks"]} marks <span class="tap">(tap for the answer)</span></span></div>'
                           f'<div class="txt">{q}</div></div><div class="ans">{a}</div></div>')
        out.append("</div>")
    out.append(pred_html + "</section>")
    return "".join(out), nsplit


def sheet(chs, pred=None):
    out = ['<section class="view" id="sheet" data-title="Sheet"><header class="wkhead"><small>For the last ten minutes</small>'
           "<h2>Must-know list and formula sheet</h2><p class=\"summary\">The must-know list first, then every formula from weeks 5–10. "
           "Each topic's one-line answer sits at the top of the topic; you can run through all 36 at the end.</p></header>"
           + (must_html(pred) if pred and pred.get("must_know") else "")
           + '<div class="toc noprint" id="sheet-formulas"><div class="row"><span class="lbl">Formulas for week</span>'
           + "".join(f'<a href="#sheet-w{d["week"]}">{d["week"]}</a>' for d in chs)
           + '<a href="#sheet-one">One-liners</a></div></div>']
    for d in chs:
        fs = d.get("formulas", [])
        if not fs:
            continue
        out.append(f'<h3 class="sh" id="sheet-w{d["week"]}">Week {d["week"]} formulas <span class="n">{esc(d["title"])}</span></h3><div class="fgrid">')
        for f in fs:
            note = f'<div class="fn">{f["note"]}</div>' if f.get("note") else ""
            out.append(f'<div class="fcard"><b>{f["name"]}</b><div class="fx">{f["formula"]}</div>{note}</div>')
        out.append("</div>")
    out.append('<h3 class="sh" id="sheet-one">Every topic in one line <span class="n">The 36 one-liners live at the top of each topic.</span></h3>'
               '<div class="btnrow noprint"><button class="btn sm" data-focus="one">Quiz me on all 36</button></div>'
               '<ul class="toplist noprint" style="margin-top:10px">')
    for d in chs:
        for t in d["topics"]:
            out.append(f'<li><span>Week {d["week"]}</span><a href="#{t["id"]}">{esc(t["title"])}</a></li>')
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
                if SRC_KIND[p["src"]] not in kinds:
                    kinds.append(SRC_KIND[p["src"]])
            sessions.append(dict(kind="pool", phase="Exam questions", title=f"Week {w} exam questions" + (f", part {j} of {len(gs)}" if len(gs) > 1 else ""),
                                 scope=f"{len(g)} questions: {', '.join(kinds)}", min=sum(m for _, m in g),
                                 items=[p["_id"] for p, _ in g], href=g[0][0]["_id"]))
    for d in chs:
        w = d["week"]
        mins = [card_minutes(t) for t in d["topics"]]
        sessions.append(dict(kind="card", phase="Traps and scenarios", title=f"Week {w} traps and scenarios",
                             scope=f"{len(d['topics'])} topics: the one-liner, traps and scenario table", min=sum(mins),
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
            sessions.append(dict(kind="drill", phase="Practice", title=f"Week {w} practice" + (f", part {j} of {len(gs)}" if len(gs) > 1 else ""),
                                 scope=f"{len(g)} questions across {len(topics)} topics", min=sum(m for _, m in g),
                                 items=[q["_id"] for (_t, q), _m in g], href=g[0][0][1]["_id"]))
    for j, (a, b) in enumerate([(1, 2), (3, 4), (5, 6)], 1):
        sessions.append(dict(kind="mock", phase="Mock paper", title=f"Mock paper, questions {a} and {b}", scope="Closed book, then check the model answers",
                             min=20, items=[], href=f"mock-q{a}"))
    sessions.append(dict(kind="sheet", phase="Exam morning", title="Formula sheet and review pile",
                         scope="52 formulas, then everything marked review again", min=20, items=[], href="sheet"))
    for i, s in enumerate(sessions, 1):
        s["sid"] = f"s{i}"
        s["raw"] = s["min"]
        s["min"] = max(15, min(25, round(s["min"])))
    # days: pool + cards on day 1, drills + mock on day 2, sheet on exam morning
    days = [("Day 1, 11 October", "exam questions, then traps and scenarios", [s for s in sessions if s["kind"] in ("pool", "card")]),
            ("Day 2, 12 October", "practice, then the mock paper", [s for s in sessions if s["kind"] in ("drill", "mock")]),
            ("Exam morning, 13 October", "a last pass", [s for s in sessions if s["kind"] == "sheet"])]
    return sessions, days


def plan_html(days):
    out = []
    for name, what, ss in days:
        phase = None
        tot = sum(s["min"] for s in ss)
        out.append(f'<div class="day"><b>{name}</b><span>{len(ss)} sessions, {tot // 60} h {tot % 60:02d} min: {what}</span></div><ol class="plan">')
        for s in ss:
            if s["phase"] != phase:
                phase = s["phase"]
                out.append(f'<li class="ph">{phase}</li>')
            act = (f'<button class="mini" data-focus="sess:{s["sid"]}">Quiz me</button>' if s["items"]
                   else f'<button class="mini" data-tick="{s["sid"]}">Mark done</button>')
            out.append(f'<li class="sess" data-sid="{s["sid"]}" data-kind="{s["kind"]}" data-items="{" ".join(s["items"])}">'
                       f'<span class="sdot"></span><a class="sm" href="#{s["href"]}"><span class="st">{s["title"]}</span>'
                       f'<span class="sc">{s["scope"]}</span></a><span class="sr"><span class="smin">{s["min"]} min</span>{act}</span>'
                       f'<span class="sbar"><i></i></span></li>')
        out.append("</ol>")
    return "".join(out)


def plan_view(chs, days, nsess, total_min, dp=None, pred=None):
    """Reference: the emphasis-ordered one-day plan and the older full-coverage plan."""
    npool = sum(len(d["pool"]) for d in chs)
    today, morn, tt, tm = dp or ([], [], 0, 0)
    return (
        '<section class="view" id="dayplan" data-title="Day plan">'
        '<header class="wkhead"><small>Reference</small><h2>The one-day plan</h2>'
        f'<p class="summary">The earlier plan, ordered by how much the slides stress each topic: {len(today)} blocks, about {tt // 60} hours '
        f'{tt % 60} minutes. The checklist on the home screen replaces it; ticks here still count there.</p></header>'
        + (emphasis_html(pred) if pred else "")
        + f'<ol class="blks">{"".join(today)}</ol>'
        + (f'<h2 class="sec" id="morning">Exam morning</h2><p class="quiet">{len(morn)} short blocks, {tm} minutes.</p>'
           f'<ol class="blks">{"".join(morn)}</ol>' if morn else "")
        + f'<details class="fold" id="fullplan"><summary>Backup plan: every exam question, topic and practice question in {nsess} sessions</summary><div>'
        f'<p class="fine">About {total_min // 60}&frac12; hours, ordered by how much each part is worth: all {npool} exam '
        'questions first, then each topic&rsquo;s traps and scenarios, then practice. '
        'A session ticks itself once everything in it is marked got it or done.</p>'
        + plan_html(days) + '</div></details>'
        "</section>")


ABOUT = (
    '<h2 class="sec">About this page</h2>'
    '<div class="legend"><span><i style="background:var(--yel)"></i>yellow is the answer</span>'
    '<span><i style="background:var(--red)"></i>red is a trap</span><span><i style="background:var(--blue)"></i>blue is maths</span></div>'
    '<p class="fine">Your ticks are saved in this browser only, so your phone and laptop keep separate copies. '
    'The full topics, every comparison, the mock papers and the formula sheet are in the menu at the top. '
    'In focus mode on a keyboard: space shows the answer, 1 is review again, 2 is got it, Esc closes.</p>'
    '<div class="btnrow"><a class="btn ghost sm" href="bda-final-guide.pdf">Full guide (PDF)</a>'
    '<a class="btn ghost sm" href="bda-exam-pool.pdf">Exam questions only (PDF)</a>'
    '<button class="btn ghost sm warn" id="reset">Reset progress</button></div>')


def picker(chs, cmps=(), probs=()):
    weeks = "".join(
        f'<button data-focus="pool:{d["week"]}">Week {d["week"]} exam questions<small>{len(d["pool"])} questions</small></button>'
        f'<button data-focus="card:{d["week"]}">Week {d["week"]} topics<small>{len(d["topics"])} topics: traps and scenarios</small></button>'
        f'<button data-focus="drill:{d["week"]}">Week {d["week"]} practice<small>{sum(len(t["questions"]) for t in d["topics"])} questions</small></button>'
        for d in chs)
    return ('<template id="pickt"><div class="f-pick">'
            '<div class="pg"><button class="big" data-focus="next">The next block in today&rsquo;s plan<small></small></button>'
            '<button data-focus="again">Review pile<small><span class="againn">0</span> marked review again</small></button>'
            '<button data-focus="one">One-liners<small>all 36 topics</small></button></div>'
            + (f'<h3>Across all weeks</h3><div class="pg"><button data-focus="cmp:all">Compare<small>all {len(cmps)} pairs</small></button>'
               f'<button data-focus="probs:all">Worked examples<small>{sum(len(x.get("variants", [])) + bool(x.get("why")) for x in probs)} practice questions</small></button>'
               '<button data-focus="src:mcq">Multiple choice<small>every week</small></button><button data-focus="src:tf">True or false<small>every week</small></button>'
               + "".join(f'<button data-focus="cmp:{w}">Week {w} compare<small>{sum(1 for c in cmps if c["week"] == w)} pairs</small></button>'
                         f'<button data-focus="probs:{w}">Week {w} worked examples<small>{sum(1 for x in probs if x["week"] == w)} examples</small></button>'
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
    GH["items"] = rd("gh_sweep.json") or []
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
            return [("go", "every topic's traps (quiz)", None, "traps", None)]
        cid = v.split("/")[-1]
        if cid in ctx["cards"]:
            return [("card", ctx["cards"][cid], "#" + cid, None, cid)]
    elif k == "pool":
        m = re.fullmatch(r"W(\d+)-W(\d+)\s+(MCQ|TF).*", v)
        if m:
            src = "mcq" if m.group(3) == "MCQ" else "tf"
            n = sum(1 for x in ctx["pool_ids"] if f"-{src}-" in x)
            return [("go", f"all {n} {'multiple-choice' if src == 'mcq' else 'true-or-false'} questions, weeks {m.group(1)}–{m.group(2)} (quiz)", None, f"src:{src}", None)]
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
                out = [(f"p{P}-q{n}", f"Paper {P} question {n}") for n in range(int(mm.group(1)), int(mm.group(2)) + 1)]
            elif (mm := re.fullmatch(r"Q(\d)\s+OR.*", rest)):
                out = [(f"p{P}-q{mm.group(1)}-or", f"Paper {P} question {mm.group(1)} OR")]
            elif (mm := re.fullmatch(r"Q(\d)", rest)):
                out = [(f"p{P}-q{mm.group(1)}", f"Paper {P} question {mm.group(1)}")]
            elif rest.startswith("ORs"):
                out = [(pid, f"Paper {P} question {pid.split('-q')[1][0]} OR") for pid in ctx["paper_ids"] if pid.startswith(f"p{P}-") and pid.endswith("-or")]
            if out and all(pid in ctx["paper_ids"] for pid, _ in out):
                return [("paper", lab, "#" + pid, None, None) for pid, lab in out]
    elif k.startswith("formulas"):
        return [("go", "the formula sheet", "#sheet-formulas", None, None)]
    elif k == "must_know":
        return [("go", "the must-know list", "#sheet-must", None, None)]
    elif k == "misses sheet":
        return [("go", "your review pile (quiz)", None, "again", None)]
    report["unresolved"].append(l)
    return []


def link_html(kind, label, href, focus, title=""):
    t = f' title="{esc(title)}"' if title else ""
    if focus:
        return f'<button class="lk" data-focus="{focus}">{esc(label)}</button>'
    return f'<a class="lk" href="{href}"{t}>{esc(label)}</a>'


def _and(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def pool_links_html(pids, ctx):
    """Pool links grouped by week and kind: 'Week 6: D1, D2 and D3 (descriptive); Q2 (multiple choice)'."""
    byw = {}
    for pid in pids:
        w, p = ctx["pool_meta"][pid]
        byw.setdefault(w, {}).setdefault(p["src"], []).append((pid, p))
    rows = []
    for w, kinds in byw.items():
        parts = []
        for src in SRC_ORDER:
            if src in kinds:
                ls = [link_html("pool", pool_code(p), "#" + pid, None, pool_label(w, p)) for pid, p in kinds[src]]
                parts.append(_and(ls) + f" ({SRC_KIND[src]})")
        rows.append(f"Week {w}: " + "; ".join(parts))
    return rows


def dayplan(pred, ctx, report):
    blocks = pred.get("plan", [])
    out_today, out_morn, tot_today, tot_morn = [], [], 0, 0
    for i, b in enumerate(blocks, 1):
        items, papers = [], []
        grp = {"Read": [], "Answer": [], "Compare": [], "Practise": []}
        pools = []
        for l in b.get("links", []):
            report["n"] += 1
            for kind, lab, href, focus, iid in resolve_link(l, ctx, report):
                if kind == "pool":
                    pools.append(iid)
                elif kind == "card":
                    grp["Read"].append(link_html(kind, lab, href, focus))
                elif kind == "paper":
                    papers.append(href[1:])
                    grp["Answer"].append(link_html(kind, lab, href, focus))
                elif kind == "cmp":
                    grp["Compare"].append(link_html(kind, lab, href, focus))
                elif kind == "prob":
                    grp["Practise"].append(link_html(kind, lab, href, focus))
                else:
                    grp["Read" if href else "Practise"].append(link_html(kind, lab, href, focus))
                if iid:
                    items.extend(ctx["prac"].get(iid, [iid]))
        items = list(dict.fromkeys(items))
        rows = []
        if grp["Read"]:
            rows.append(("Read", _and(grp["Read"])))
        ans = pool_links_html(list(dict.fromkeys(pools)), ctx) + ([_and(grp["Answer"])] if grp["Answer"] else [])
        for j, r in enumerate(ans):
            rows.append(("Answer" if j == 0 else "", r))
        if grp["Compare"]:
            rows.append(("Compare", _and(grp["Compare"])))
        if grp["Practise"]:
            rows.append(("Practise", _and(grp["Practise"])))
        nlinks = sum(len(v) for v in grp.values()) + len(pools)
        long = nlinks > 9 and len(rows) > 2
        lks = "".join(f'<div class="lg{" x" if long and j >= 2 else ""}"><span class="lgl">{lab}</span><span class="lgi">{r}</span></div>'
                      for j, (lab, r) in enumerate(rows))
        if long:
            lks += f'<button class="link more" data-more>Show all {nlinks} links</button>'
        morning = b["block"].lower().startswith("exam morning")
        m = re.match(r"Day (\d+)\.\s*(.*)", b["block"])
        num, title = (m.group(1), m.group(2)) if m else (("M" + str(len(out_morn) + 1)) if morning else str(i), b["block"])
        title = re.sub(r"\bW(\d+)\b", r"Week \1", title)
        focus = (f'<button class="btn sm ghost" data-focus="blk:b{i}">Quiz me on these {len(items)}</button>' if items else "")
        li = (f'<li class="blk" id="blk{i}" data-sid="b{i}" data-items="{" ".join(items)}" data-papers="{" ".join(papers)}">'
              f'<div class="bh"><span class="bn">{esc(num)}</span><span class="bt">{esc(title)}</span><span class="bm">{b["minutes"]} min</span></div>'
              f'<p class="bk">{esc(b["task"])}</p><div class="lks{" long" if long else ""}">{lks}</div>'
              f'<div class="bf">{focus}<span class="bp"><i></i></span><button class="tk" data-tick="b{i}"><span class="n">Mark done</span><span class="y">&#10003; Done</span></button></div></li>')
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
        f'<li><span class="sc9">{e["score"]}</span><span><b>Week {e["week"]}:</b> {esc(re.sub(r"\s*\[card [^]]+\]", "", e["topic"]))}</span>'
        f'<span class="ev">{esc(e["evidence"])}</span></li>' for e in em)
    return (f'<details class="fold"><summary>Why this order</summary>'
            f'<div><p class="fine">The order follows how heavily the slides stress each topic, but every week still gets its own blocks, '
            f'weeks 9 and 10 included, and the multiple-choice and true-or-false sweep covers all six. A prediction is a guess, so nothing is dropped because of it.</p>'
            f'<p class="fine">Each score is out of 10, from how many slides, drawn figures, exam questions and instructor notes a topic has. '
            f'It is a reading of the slides, not inside knowledge of the paper.</p><ol class="emph">{lis}</ol></div></details>')


def filt_row(v, weeks, lopts, label):
    return ('<div class="filt noprint"><select data-f="w" aria-label="Week"><option value="">All weeks</option>'
            + "".join(f'<option value="{w}">Week {w}</option>' for w in weeks)
            + f'</select><select data-f="l" aria-label="Likelihood">'
            + "".join(f'<option value="{k}">{t}</option>' for k, t in lopts)
            + f'</select><button class="btn sm" data-focus="{v}:f">{label}</button></div><p class="shown"></p>')


def cmp_view(cmps, cards):
    order = sorted(cmps, key=lambda c: (c.get("likelihood") != "high", c["week"]))
    weeks = sorted({c["week"] for c in cmps})
    out = ['<section class="view" id="cmp" data-title="Compare"><header class="wkhead"><small>Reference, all weeks</small>'
           f'<h2>Compare: {len(cmps)} pairs</h2>'
           '<p class="summary">Pairs the slides set against each other. Each shows the key difference; tap it for the table and the '
           'scenario cue that tells you which side a question means. The most likely pairs come first.</p></header>'
           + filt_row("cmp", weeks, [("", "Any likelihood"), ("high", "Most likely"), ("medium", "Less likely")], "Quiz me on these")]
    last = None
    for c in order:
        cid = c["id"]
        lik = c.get("likelihood", "medium")
        if lik != last:
            last = lik
            out.append(f'<h3 class="gh" data-g="{lik}">{"Most likely to come up" if lik == "high" else "Also worth knowing"}</h3>')
        tbl = stack_table(["", c["x"], c["y"]], c.get("rows", []), cell=esc)
        link = (f'<a class="tocard" href="#{c["card_id"]}">Topic: {esc(cards[c["card_id"]])}</a>'
                if c.get("card_id") in cards else '<span></span>')
        out.append(f'<article class="qa cmpc bitem" id="c-{cid}" data-id="c-{cid}" data-w="{c["week"]}" data-l="{lik}" data-lab="Week {c["week"]} compare">'
                   f'<div class="q" tabindex="0"><span class="st8"></span><div class="txt"><h4>{esc(cmp_title(c))}</h4>'
                   f'<div class="one"><b class="l">Key difference</b>{esc(c["key"])}</div>{gh_badges(c.get("gh"))}</div></div>'
                   f'<div class="ans">{tbl}{gh_extra(c.get("gh"))}'
                   f'<div class="cue"><b>Spot it in a scenario</b>{esc(c["cue"])}</div>'
                   f'<span class="meta">Week {c["week"]}, slides {esc(c.get("slides", ""))}</span>'
                   f'<div class="afoot">{link}{marks_btns()}</div></div></article>')
    out.append("</section>")
    return "".join(out)


def prob_view(probs, cards):
    weeks = sorted({p["week"] for p in probs})
    rk = {"very likely": "vl", "likely": "l"}
    order = sorted(probs, key=lambda p: (p["week"], p.get("rank") != "very likely"))
    out = ['<section class="view" id="probs" data-title="Worked examples"><header class="wkhead"><small>Reference, all weeks</small>'
           f'<h2>Worked examples: {len(probs)} from the slides</h2>'
           '<p class="summary">The teacher said solving the slide exercises covers the paper. Each one shows the slide&rsquo;s numbers; '
           'tap for the steps, then try the variants and the &ldquo;why&rdquo; question.</p></header>'
           + filt_row("probs", weeks, [("", "Any likelihood"), ("vl", "Very likely"), ("l", "Likely")], "Practise these")]
    last = None
    for p in order:
        pid, w = p["id"], p["week"]
        if w != last:
            last = w
            out.append(f'<h3 class="gh" data-g="{w}">Week {w}</h3>')
        cid = (p.get("card") or "").split("/")[-1]
        link = f'<a class="tocard" href="#{cid}">Topic: {esc(cards[cid])}</a>' if cid in cards else "<span></span>"
        steps = "".join(f"<li>{esc(x)}</li>" for x in p.get("solution_steps", []))
        prac = []
        for j, v in enumerate(p.get("variants", []), 1):
            prac.append((f"x-{pid}-v{j}", f"Variant {j}", v["q"], v["a"]))
        if p.get("why"):
            prac.append((f"x-{pid}-why", "Why", p["why"]["q"], p["why"]["a"]))
        pr = "".join(
            f'<div class="qa prac" id="{xid}" data-id="{xid}" data-w="{w}" data-lab="Week {w} worked example, {lab.lower()}">'
            f'<div class="q" tabindex="0"><span class="st8"></span>'
            f'<div class="txt">{esc(q)}</div><span class="tag">{lab}</span></div>'
            f'<div class="ans">{esc(a)}<div class="afoot">{link if lab == "Why" else "<span></span>"}{marks_btns()}</div></div></div>'
            for xid, lab, q, a in prac)
        r = p.get("rank", "likely")
        out.append(f'<article class="prob bitem" id="x-{pid}" data-w="{w}" data-l="{rk.get(r, "l")}">'
                   f'<header><h4>{esc(p["title"])}</h4><span class="meta">Week {w}, {esc(r)}. Slides: {esc(p.get("slides", ""))}</span></header>'
                   f'<div class="given"><b>Given</b>{esc(p["given"])}</div>'
                   f'<div class="qa sol"><div class="q" tabindex="0"><div class="txt">Show the {len(p.get("solution_steps", []))} steps</div></div>'
                   f'<div class="ans"><ol>{steps}</ol><div class="one"><b class="l">Answer</b>{esc(p["answer"])}</div></div></div>'
                   f'<h5>Try it yourself</h5>{pr}</article>')
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
    wks = f' <span class="orwk">Week {wk}</span>' if wk else ""
    return (f'<div class="qa mock"><div class="q" tabindex="0"><div class="pl">({lab}){wks}'
            f'<span>{pt["marks"]} marks <span class="tap">(tap for the answers)</span></span></div>'
            f'<div class="txt"><div class="scn">{esc(pt.get("scenario", ""))}</div>{q}</div></div><div class="ans">{a}</div></div>')


def predicted_html(pred):
    out, ids = [], set()
    for pi, pp in enumerate(pred.get("papers", [])):
        P = "AB"[pi] if pi < 2 else str(pi + 1)
        out.append(f'<div class="predsec"><div class="predban" id="pred-{P}"><b>A prediction, not the real paper</b>'
                   f'<h3>{esc(pp["name"])}</h3><p>Built from how much the slides stress each chapter; the reasoning is shown on every question. '
                   'The real paper can pick any chapter, so the plan and the pool still cover all six weeks.</p></div>')
        for q in pp.get("questions", []):
            n = re.sub(r"\D", "", q["q"]) or "?"
            qid = f"p{P}-q{n}"
            ids.add(qid)
            tot = sum(pt["marks"] for pt in q.get("parts", []))
            out.append(f'<div class="paper pred" id="{qid}"><header><b>Question {n}</b><span>Week {q["week"]}, {tot:g} marks</span></header>'
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
    return (f'<h3 class="sh" id="sheet-must">Must-know list <span class="n">{len(mk)} lines. Tick each one you can say from memory.</span></h3>'
            f'<ul class="mkl">{lis}</ul>'
            + (f'<details class="fold"><summary>Short on time? {len(sk)} things you can skip</summary><div>'
               f'<p class="fine">Low-yield detail by the slide evidence. Skip only if the clock forces it; everything else stays in.</p>'
               f'<ul>{skip}</ul></div></details>' if sk else ""))


# ---------------------------------------------------------------- checklist (home)

# Figures the exam might ask for: every topic with a "draw / diagram / sketch" pool question, plus the
# figures the slides make students redraw (the plan's redraw tasks and the six exam-morning figures).
REDRAW = {"rdd", "narrow-wide", "yarn-arch", "hive-arch", "lambda-kappa", "kafka-log", "forecasting"}


def _toks_plain(h):
    return _toks(re.sub(r"<[^>]+>", " ", html.unescape(str(h or ""))))


def key_points(t):
    """At most 3 bullets that add to the one-liner: two facts, then one 'why', skipping any that mostly
    repeat the one-liner."""
    one = _toks_plain(t["answers"]["1"])

    def fresh(x):
        tk = _toks_plain(x)
        return len(tk & one) / max(1, len(tk)) <= 0.5
    facts = [x for x in t["facts"] if fresh(x)]
    whys = [x for x in t["why"] if fresh(x) and not x.lower().startswith("limitation")]
    out = facts[:2] + whys[:1]
    for x in facts[2:]:
        if len(out) >= 3:
            break
        out.append(x)
    return out[:3]


def ck_row(rid, kind, key, title, meta, body):
    dataid = f' data-id="{key}"' if kind == "m" else ""
    return (f'<li class="ci" id="{rid}" data-kind="{kind}" data-key="{key}"{dataid}>'
            f'<div class="ch"><button class="tick" aria-label="Tick off"></button>'
            f'<button class="ct"><span class="tt">{title}</span>{f"<span class=tm>{meta}</span>" if meta else ""}</button></div>'
            f'<div class="cb">{body}</div></li>')


def _plain_short(h, n=78):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(str(h or "")))).strip()
    return html.escape(t if len(t) <= n else t[: n - 1].rsplit(" ", 1)[0] + "…")


class Svgs:
    n = 0

    @classmethod
    def sfx(cls):
        cls.n += 1
        return f"-ck{cls.n}"


def checklist_view(chs, cmps, probs, pred, ctx, morning):
    """The home screen: one linear checklist, Week 5 to Week 10, each chapter Learn -> Practise -> Test,
    then Exam morning. Each row maps onto the existing progress store (S.c topic done, S.m 'k' marks,
    S.s ticks), so ticks made anywhere else on the site show here too."""
    papers = pred.get("papers", [])
    draw_topics = set(REDRAW)
    for d in chs:
        for p in d["pool"]:
            if re.search(r"\b(draw|diagram|sketch|illustrat)", p["q"], re.I) and p.get("topic"):
                draw_topics.add(p["topic"])
    report = []
    chap_html, nav = [], []
    for d in chs:
        w = d["week"]
        rows_l, rows_p, rows_t, rows_gt, rows_gp = [], [], [], [], []
        words_n, prac_n = 0, 0
        # ---- learn: topics
        for t in d["topics"]:
            kp = key_points(t)
            dia = ""
            if t.get("diagram") and t["id"] in draw_topics:
                dia = ('<div class="lay"><h5>Be ready to draw this</h5>'
                       + figure(t["diagram"]["file"], t["diagram"].get("caption", ""), "", Svgs.sfx()) + "</div>")
            body = (f'<div class="one"><b class="l">In one line</b>{t["answers"]["1"]}</div>'
                    + (f'<div class="lay"><h5>Key points</h5>{ul(kp)}</div>' if kp else "")
                    + f'<div class="lay trap"><h5>Traps</h5>{ul(t["traps"])}</div>' + dia
                    + f'<p class="more"><a href="#{t["id"]}">More detail: the full topic, scenarios and longer answers</a></p>')
            words_n += words(t["answers"]["1"]) + sum(words(x) for x in kp) + sum(words(x) for x in t["traps"])
            rows_l.append(ck_row(f"ck-{t['id']}", "card", t["id"], esc(t["title"]), "", body))
            for x in t["traps"]:
                if 'class="ghb' in x:
                    GH["list"].append(dict(week=w, vl='ghb vl' in x, new=False, href=f"#ck-{t['id']}",
                                           title=f"Trap in &ldquo;{esc(t['title'])}&rdquo;: {_plain_short(x, 70)}", kind="Trap",
                                           g={"src": ["v1"], "vl": 'ghb vl' in x}))
        # ---- learn: high-likelihood comparisons
        for c in [c for c in cmps if c["week"] == w and c.get("likelihood") == "high"]:
            rows = c.get("rows", [])[:4]
            tbl = stack_table(["", c["x"], c["y"]], rows, cell=esc)
            body = (f'<div class="one"><b class="l">Key difference</b>{esc(c["key"])}</div>{tbl}{gh_extra(c.get("gh"))}'
                    + f'<div class="afoot"><a href="#c-{c["id"]}">More detail: full table and scenario cue</a>{marks_btns()}</div>')
            words_n += words(c["key"]) + sum(words(x) for r in rows for x in r)
            rows_l.append(ck_row(f"ck-c-{c['id']}", "m", f"c-{c['id']}", esc(cmp_title(c)), "Compare" + gh_badges(c.get("gh")), body))
            if c.get("gh"):
                GH["list"].append(dict(week=w, vl=c["gh"].get("vl"), new=False, href=f"#ck-c-{c['id']}",
                                       title=esc(cmp_title(c)), kind="Compare", g=c["gh"]))
            report.append(("cmp", c["id"]))
        # ---- learn: formulas
        fs = d.get("formulas", [])
        if fs:
            body = '<div class="fgrid">' + "".join(
                f'<div class="fcard"><b>{f["name"]}</b><div class="fx">{f["formula"]}</div>'
                + (f'<div class="fn">{f["note"]}</div>' if f.get("note") else "") + "</div>" for f in fs) + "</div>"
            words_n += sum(words(f["name"]) + words(f["formula"]) + words(f.get("note")) for f in fs)
            rows_l.append(ck_row(f"ck-f{w}", "s", f"ck-f{w}", f"Week {w} formulas", f"{len(fs)} formulas", body))
        # ---- practise: slide worked examples, very likely first
        for x in sorted([x for x in probs if x["week"] == w], key=lambda x: x.get("rank") != "very likely"):
            v = (x.get("variants") or [None])[0]
            steps = "".join(f"<li>{esc(st)}</li>" for st in x.get("solution_steps", []))
            body = (f'<div class="given"><b>Given</b>{esc(x["given"])}</div>'
                    f'<button class="link show" data-show>Show the solution</button>'
                    f'<div class="fa"><ol class="steps">{steps}</ol><div class="one"><b class="l">Answer</b>{esc(x["answer"])}</div></div>')
            words_n += words(x["given"]) + words(" ".join(x.get("solution_steps", []))) + words(x["answer"])
            key = f"x-{x['id']}-v1" if v else f"ck-x-{x['id']}"
            if v:
                body += (f'<div class="lay"><h5>Now try one</h5><p>{esc(v["q"])}</p></div>'
                         f'<button class="link show" data-show>Show the answer</button>'
                         f'<div class="fa"><div class="vans">{esc(v["a"])}</div></div>')
                words_n += words(v["q"]) + words(v["a"])
            body += f'<div class="afoot"><a href="#x-{x["id"]}">More detail: the other variant and the why question</a>{marks_btns() if v else ""}</div>'
            prac_n += 1
            meta = "Very likely" if x.get("rank") == "very likely" else ""
            rows_p.append(ck_row(f"ck-x-{x['id']}", "m" if v else "s", key, esc(x["title"]), meta, body))
        nslide = len(rows_p)
        gh_p = sorted([g for g in GH["items"] if g["week"] == w and g["list"] == "practise"], key=lambda g: not g.get("vl"))
        gh_t = sorted([g for g in GH["items"] if g["week"] == w and g["list"] == "test"], key=lambda g: not g.get("vl"))
        for g in gh_p + gh_t:
            body = (f'<div class="fq">{g["q"]}</div>'
                    f'<button class="btn sm ghost show" data-show>Show the answer</button>'
                    f'<div class="fa"><div class="pans">{g["a"]}</div><div class="afoot"><span></span>{marks_btns()}</div></div>')
            words_n += words(g["q"]) + words(g["a"])
            if g["list"] == "practise":
                prac_n += 1
            row = ck_row(f"ck-{g['id']}", "m", g["id"], esc(g["title"]), f'{esc(g["kind"])}{gh_badges(g)}', body)
            (rows_gp if g["list"] == "practise" else rows_gt).append(row)
            GH["list"].append(dict(week=w, vl=g.get("vl"), new=True, href=f"#ck-{g['id']}", title=esc(g["title"]),
                                   kind=g["kind"], g=g))
        # ---- test: exam questions, flashcard style
        tops = {t["id"]: t for t in d["topics"]}
        for p in pool_items_sorted(d):
            pid = p["_id"]
            opts = ('<ul class="opts">' + "".join(f"<li>{o}</li>" for o in p["options"]) + "</ul>") if p.get("options") else ""
            cd = f"<pre><code>{esc(p['code'])}</code></pre>" if p.get("code") else ""
            ans = pool_answer(p, tops.get(p.get("topic")))
            body = (f'<div class="fq">{p["q"]}{opts}{cd}</div>'
                    f'<button class="btn sm ghost show" data-show>Show the answer</button>'
                    f'<div class="fa"><div class="pans">{ans}</div>{gh_extra(p.get("gh"))}<div class="afoot"><span></span>{marks_btns()}</div></div>')
            words_n += words(p["q"]) + words(p["a"]) + words(" ".join(p.get("options") or [])) + words(p.get("code"))
            src = p["src"]
            meta = f'{esc(pool_code(p))}, {SRC_KIND[src]}' if src not in ("Discussion", "Live Exercise") else (
                f"Discussion {esc(p.get('n', ''))}" if src == "Discussion" else f"Live exercise {esc(p.get('n', ''))}")
            rows_t.append(ck_row(f"ck-{pid}", "m", pid, _plain_short(p["q"]), meta + gh_badges(p.get("gh")), body))
            report.append(("pool", pid))
            if p.get("gh"):
                GH["list"].append(dict(week=w, vl=p["gh"].get("vl"), new=False, href=f"#ck-{pid}",
                                       title=f'{esc(pool_code(p))}: {_plain_short(p["q"], 70)}', kind=SRC_SHORT[src], g=p["gh"]))
        npool_rows = len(rows_t)
        # ---- test: the chapter's predicted-paper questions
        for pi, pp in enumerate(papers):
            P = "AB"[pi] if pi < 2 else str(pi + 1)
            for q in pp.get("questions", []):
                n = re.sub(r"\D", "", q["q"]) or "?"
                sets = []
                if q["week"] == w:
                    sets.append((f"p{P}-q{n}", f"Paper {P}, question {n}", q.get("parts", []), q.get("why", "")))
                ors = [pt for pt in (q.get("or") or []) if pt.get("week") == w]
                if ors:
                    sets.append((f"p{P}-q{n}-or", f"Paper {P}, question {n} (the OR choice)", ors, ""))
                for qid, lab, parts, why in sets:
                    tot = sum(pt["marks"] for pt in parts)
                    body = ('<p class="fine">Write it closed book, then tap each part to check.</p>'
                            + "".join(_part(pt) for pt in parts)
                            + f'<p class="more"><a href="#{qid}">Open it in the mock papers</a></p>')
                    words_n += sum(words(pt.get("scenario")) + sum(words(sb["q"]) + words(sb["a"]) for sb in pt.get("subs", [])) for pt in parts)
                    rows_t.append(ck_row(f"ck-{qid}", "s", f"ck-{qid}", f"Predicted p{lab[1:]}", f"{tot:g} marks", body))
        mins = round(words_n / 200 + 2 * prac_n)
        nitems = len(rows_l) + len(rows_p) + len(rows_gp) + len(rows_t) + len(rows_gt)
        ctx["ck_report"].append(dict(week=w, learn=len(rows_l), practise=len(rows_p) + len(rows_gp), test=len(rows_t) + len(rows_gt), items=nitems,
                                     words=words_n, prac=prac_n, minutes=mins))
        ntop = len(d["topics"])
        ncm = len(rows_l) - ntop - (1 if fs else 0)
        nav.append(f'<li><a href="#ch{w}"><span class="t"><b>Week {w}</b><span>{esc(d["title"])}</span></span>'
                   f'<span class="cpct" data-cw="{w}"></span></a></li>')
        chap_html.append(
            f'<section class="chap" id="ch{w}" data-cw="{w}"><header class="chead"><small>Week {w}</small><h2>{esc(d["title"])}</h2>'
            f'<div class="prog"><div class="pbar"><i></i></div><span class="ptxt" data-mins="{mins}"></span></div></header>'
            f'<h3 class="step">Learn <span>{ntop} topics, {ncm} comparisons and the formulas</span></h3><ol class="ck">{"".join(rows_l)}</ol>'
            f'<h3 class="step">Practise <span>{nslide} worked examples from the slides'
            + (f', then {len(gh_p)} from the lecturer&rsquo;s own files' if gh_p else "") + '</span></h3>'
            f'<ol class="ck">{"".join(rows_p)}</ol>'
            + (f'<h4 class="ghh"><span class="ghb gs">From the lecturer&rsquo;s own files</span></h4><ol class="ck">{"".join(rows_gp)}</ol>' if rows_gp else "")
            + f'<h3 class="step">Test <span>{len(d["pool"])} exam questions'
            + (f', {len(gh_t)} from the lecturer&rsquo;s own files' if gh_t else "") + ', then the predicted paper</span></h3>'
            f'<p class="quiet"><button class="link" data-focus="pool:{w}">Quiz me on all {len(d["pool"])} exam questions in focus mode</button></p>'
            f'<ol class="ck">{"".join(rows_t[:npool_rows])}</ol>'
            + (f'<h4 class="ghh"><span class="ghb gs">From the lecturer&rsquo;s own files</span></h4><ol class="ck">{"".join(rows_gt)}</ol>' if rows_gt else "")
            + (f'<h4 class="ghh plain">Predicted paper</h4><ol class="ck">{"".join(rows_t[npool_rows:])}</ol>' if rows_t[npool_rows:] else "")
            + '</section>')
    # ---- exam morning: the three morning blocks of the old plan (their ticks are the same keys)
    mk = pred.get("must_know", [])
    mrows = []
    for j, (sid, b) in enumerate(morning):
        if j == 0:
            title = "Must-know list and formula sheet"
            body = (f'<p>{esc(b["task"])}</p><ul class="mkl">'
                    + "".join(f'<li><button data-tick="mk{i}" aria-label="Known"></button><span>{esc(x)}</span></li>' for i, x in enumerate(mk, 1))
                    + '</ul><p class="more"><a href="#sheet-formulas">Open the formula sheet</a></p>')
        elif j == 1:
            title = "Redraw the six key figures"
            body = f'<p>{esc(b["task"])}</p>'
        else:
            title = "Go through your review pile"
            body = f'<p>{esc(b["task"])}</p><p><button class="btn sm ghost" data-focus="again">Quiz me on the review pile</button></p>'
        mrows.append(ck_row(f"ck-m{j + 1}", "s", sid, title, f'{b["minutes"]} min', body))
    # ---- the lecturer's own files: every new or enriched item, by week, Very likely first
    gl = GH["list"]
    nnew, nenr, nvl = sum(1 for x in gl if x["new"]), sum(1 for x in gl if not x["new"]), sum(1 for x in gl if x["vl"])
    lect = []
    for wk in sorted({x["week"] for x in gl}):
        its = sorted([x for x in gl if x["week"] == wk], key=lambda x: (not x["vl"], not x["new"]))
        lis = "".join(
            f'<li><a href="{x["href"]}"><span class="lt"><b>{x["title"]}</b>'
            f'<span class="lk2">{"New: " if x["new"] else "Added note: "}{esc(x["kind"])}</span>{gh_badges(x["g"])}</span></a></li>'
            for x in its)
        lect.append(f'<h3 class="lw">Week {wk} <span>{len(its)} items</span></h3><ul class="lects">{lis}</ul>')
    lect_html = (
        '<section class="lect" id="lect"><header class="lhead"><small>Extra, from the lecturer&rsquo;s public GitHub</small>'
        '<h2>From the lecturer&rsquo;s own files</h2>'
        f'<p>{nnew} new questions with model answers and {nenr} existing items with an added note, taken from his course plan, '
        'the first (v1) version of the slides, and his textbook. Items marked <span class="ghb vl">Very likely</span> are ones his '
        'files flag: the &ldquo;important exam topic&rdquo; label, the CLO4 design questions in weeks 7, 8 and 10, and plan questions '
        'that the slides repeat.</p></header>' + "".join(lect) + "</section>") if gl else ""
    lect_nav = (f'<li class="lnav"><a href="#lect"><span class="t"><b>From the lecturer&rsquo;s own files</b>'
                f'<span>{nnew} new questions, {nenr} added notes, {nvl} marked very likely</span></span>'
                '<span class="chev" aria-hidden="true">&rsaquo;</span></a></li>') if gl else ""
    html_out = (
        '<section class="view" id="start" data-title="Checklist">'
        '<header class="hero"><h1 id="greet">Two days to go.</h1>'
        '<p class="sub">CSE 4345 Big Data Analytics, weeks 5 to 10. Work down the list: in each chapter, learn, practise, then test. '
        'When the last box is ticked, you&rsquo;re ready.</p>'
        '<div class="todayp"><span id="allp"></span><span class="tbar"><i></i></span></div>'
        '<a class="go" href="#ch5" id="nextopen"><span class="nt">Start with Week 5</span></a><a class="go" href="quick/" style="background:#1c2430"><span class="nt">Quick revision: cheat sheet, questions, GitHub Q&amp;A, diagrams</span></a>'
        '<p class="resume" id="resume" hidden>Or go back to <a href="#start"></a></p>'
        '<div class="complete" hidden><h2>Preparation complete</h2><p>Every item is ticked. Read the must-know list once more, then rest.</p></div>'
        '</header>'
        f'<ul class="rows chnav">{"".join(nav)}{lect_nav}<li><a href="#exam-morning"><span class="t"><b>Exam morning</b>'
        '<span>Must-know list, six figures, review pile</span></span><span class="cpct" data-cw="m"></span></a></li></ul>'
        + "".join(chap_html) + lect_html
        + f'<section class="chap" id="exam-morning" data-cw="m"><header class="chead"><small>13 October</small><h2>Exam morning</h2>'
          '<div class="prog"><div class="pbar"><i></i></div><span class="ptxt" data-mins="45"></span></div></header>'
          f'<ol class="ck">{"".join(mrows)}</ol>'
          '<div class="complete" hidden><h2>Preparation complete</h2><p>Every item is ticked. Good luck on Tuesday.</p></div></section>'
        + ABOUT + "</section>")

    def inl(m):
        return figure(m.group(1), "", "", Svgs.sfx()) if (ROOT / m.group(1)).exists() else m.group(0)
    html_out = re.sub(r'<img[^>]*src="(diagrams/[^"]+\.svg)"[^>]*>', inl, html_out)
    return html_out, report


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
               pool_meta={p["_id"]: (d["week"], p) for d in chs for p in d["pool"]},
               cmps={c["id"]: c for c in cmps}, probs={x["id"]: x for x in probs}, paper_ids=paper_ids,
               prac={f'x-{x["id"]}': [f'x-{x["id"]}-v{j}' for j in range(1, len(x.get("variants", [])) + 1)]
                     + ([f'x-{x["id"]}-why'] if x.get("why") else []) for x in probs}, ck_report=[])
    report = dict(n=0, unresolved=[], partial=[], stale=[], auto=[])
    dp = dayplan(pred, ctx, report)
    morning = [(f"b{i}", b) for i, b in enumerate(pred.get("plan", []), 1) if b["block"].lower().startswith("exam morning")]
    ck_html, ck_rep = checklist_view(chs, cmps, probs, pred, ctx, morning)
    menu = ('<a href="#start"><b>Checklist</b><span class="t">the home screen</span></a><hr>'
            + "".join(f'<a href="#w{d["week"]}"><b>Week {d["week"]}</b><span class="t">{esc(d["title"])}</span>'
                      f'<span class="wpct" data-wp="{d["week"]}"></span></a>' for d in chs)
            + '<hr>'
            f'<a href="#cmp"><b>Compare</b><span class="t">all {len(cmps)} pairs</span></a>'
            f'<a href="#probs"><b>Worked examples</b><span class="t">all {len(probs)}, with variants</span></a>'
            '<a href="#mock"><b>Mock papers</b><span class="t">the mock and two predicted papers</span></a>'
            '<a href="#sheet"><b>Sheet</b><span class="t">must-know list and formulas</span></a>'
            '<a href="#dayplan"><b>Day plan</b><span class="t">the earlier one-day plan</span></a><hr>'
            '<button data-focus="pick"><b>Focus mode</b><span class="t">flashcards for any set</span></button>'
            '<button id="all"><b>Show every answer</b><span class="t">open all answers on the page</span></button>'
            '<a href="quick/"><b>Quick revision</b><span class="t">4 pages, phone and PC</span></a><a href="bda-final-guide.pdf"><b>Full guide</b><span class="t">PDF</span></a>'
            '<a href="bda-exam-pool.pdf"><b>Exam questions</b><span class="t">PDF</span></a>')
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#6a3d7a">'
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400'
        '&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap">'
        f"<title>BDA final checklist</title><style>{CSS}</style></head><body>"
        '<nav class="bar"><div class="bar-in"><a class="brand" href="#start">BDA final</a>'
        '<span class="sp"></span><span class="opct" title="Checklist progress"></span>'
        '<a class="chip" href="quick/" style="text-decoration:none">Quick</a><button class="chip" id="menubtn" aria-haspopup="true">Menu</button>'
        '<button class="chip ico" id="theme" aria-label="Toggle dark mode">&#9680;</button></div>'
        '<div class="obar"><i></i></div></nav>'
        f'<div class="wkmenu" id="wkmenu">{menu}</div>'
        "<main>"
        + ck_html + weeks_html
        + (cmp_view(cmps, cards) if cmps else "") + (prob_view(probs, cards) if probs else "") + mock_html + sheet(chs, pred)
        + plan_view(chs, days, len(sessions), total_min, dp, pred)
        + "</main>"
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
    from line_reader import inject  # line-by-line reader, shared with other guides
    (ROOT / "index.html").write_text(inject(page))
    for out, q in (("bda-final-guide.pdf", ""), ("bda-exam-pool.pdf", "?pool")):
        subprocess.run(
            ["nice", "-n", "10", "google-chrome-stable", "--headless=new", "--disable-gpu", "--mute-audio", "--no-pdf-header-footer", "--virtual-time-budget=3000",
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
    print("checklist:")
    for r in ctx["ck_report"]:
        print(f"  week {r['week']}: {r['items']} items (learn {r['learn']}, practise {r['practise']}, test {r['test']}), "
              f"{r['words']} words + {r['prac']} practice items = about {r['minutes']} min")
    print(f"  total {sum(r['items'] for r in ctx['ck_report'])} items, about {sum(r['minutes'] for r in ctx['ck_report'])} min")


if __name__ == "__main__":
    main()
