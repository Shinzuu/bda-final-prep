#!/usr/bin/env python3
"""Line-by-line reader for single-file HTML study guides.

Inlines one <style> and one <script> before </body>, between marker comments, so the
page stays a single offline file. Running it again replaces the old copy.

    python3 line_reader.py page.html [more.html ...]      # inject in place
    from line_reader import inject; html = inject(html)   # from a generator

Reader: <- / -> (or swipe on a phone) step one item; the current item is highlighted and
centred and the rest dims (Focus); closed <details> open on arrival; K marks an item
"known" and later passes skip it; the counter opens a jump-to-section menu; a progress
bar runs along the top; the position is remembered per page. Nothing shows in print.

Items: elements with class "it" if the page has any; otherwise text leaves (p, li,
headings, pre, table rows, summaries, figures, diagram wrappers). A page can set its
own selector with <html data-lr-items="...">. Pages that already carry their own
reader (#nx inside .navb) are left alone; while a guide's deck mode is on
(.deck-on), the reader hides and ignores keys.
"""
import re
import sys

CSS = r"""
.lr-on .lr-it{transition:opacity .15s}
.lr-focus .lr-it{opacity:.33}
.lr-focus .lr-it.lr-cur{opacity:1}
.lr-it.lr-cur{background:#fff6c7!important;outline:2px solid #e0b400;outline-offset:2px;border-radius:4px;color:#111!important}
.lr-it.lr-cur *{color:#111}
.lr-it.lr-cur svg *{color:inherit}
.lr-it.lr-known{box-shadow:inset 3px 0 0 #2f9e5a}
.lr-focus .lr-it.lr-known:not(.lr-cur){opacity:.18}
#lr-prog{position:fixed;top:0;left:0;height:3px;width:0;background:#e0b400;z-index:2147483000;transition:width .15s}
#lr-bar{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);display:flex;gap:6px;align-items:center;z-index:2147483000;
 background:#1c2430;padding:5px 6px;border-radius:28px;box-shadow:0 2px 10px rgba(0,0,0,.35);font:14px/1 system-ui,Arial,sans-serif}
#lr-bar button{height:42px;min-width:44px;border:0;border-radius:21px;background:#3a6db3;color:#fff;font-size:20px;cursor:pointer;padding:0 10px}
#lr-bar button.lr-sm{background:#2d3a4d;font-size:15px}
#lr-bar button.lr-k.on{background:#2f9e5a}
#lr-pos{min-width:76px;font:13px ui-monospace,monospace!important;background:#2d3a4d!important}
#lr-menu{position:fixed;bottom:66px;left:50%;transform:translateX(-50%);width:min(92vw,420px);max-height:60vh;overflow:auto;
 background:#1c2430;color:#fff;border-radius:12px;padding:6px;z-index:2147483001;display:none;box-shadow:0 4px 18px rgba(0,0,0,.4);font:15px/1.3 system-ui,Arial,sans-serif}
#lr-menu.open{display:block}
#lr-menu a{display:block;color:#fff;text-decoration:none;padding:9px 10px;border-radius:8px}
#lr-menu a:hover,#lr-menu a:focus{background:#2d3a4d}
#lr-menu .lr-opt{display:flex;gap:8px;align-items:center;padding:8px 10px;border-top:1px solid #2d3a4d;font-size:13px;opacity:.85}
.lr-on body,body.lr-on{padding-bottom:84px}
.lr-deck #lr-bar,.lr-deck #lr-prog{display:none}
@media print{#lr-bar,#lr-menu,#lr-prog{display:none!important}.lr-it{opacity:1!important;background:none!important;outline:0!important;box-shadow:none!important}}
"""

JS = r"""
(function(){
if(window.__lineReader)return;window.__lineReader=1;
if(document.querySelector('.navb #nx'))return; // page already has its own reader
var D=document,H=D.documentElement,B=D.body,KEY='lr:'+location.pathname,vv=window.visualViewport;
var st={i:-1,known:{},skip:true};try{var s=JSON.parse(localStorage.getItem(KEY)||'{}');for(var k in s)st[k]=s[k]}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
var SKIP='nav,header nav,script,style,noscript,button,#lr-bar,#lr-menu,.deckbar,.lr-no,[aria-hidden="true"],.navb,.weeks,.totop,input,select,textarea';
var LEAF='h1,h2,h3,h4,p,li,pre,blockquote,tr,figure,summary,dt,dd,.d,.sv';
var sel=H.getAttribute('data-lr-items')||(D.querySelector('.it')?'.it':LEAF);
var items=[].slice.call(D.querySelectorAll(sel)).filter(function(e){
  if(e.closest(SKIP))return false;
  if(sel===LEAF&&e.querySelector(LEAF))return false; // keep the innermost text block
  if(e.tagName==='SUMMARY'||e.closest('details:not([open])'))return true;
  if(!e.getClientRects().length)return false;        // hidden by the page
  return (e.textContent||'').trim().length>1||e.querySelector('svg,img');
});
if(items.length<3)return;
items.forEach(function(e,n){e.classList.add('lr-it');e.dataset.lrN=n});
H.classList.add('lr-on');
function isDeck(){return !!D.querySelector('.deck-on')}
var mo=new MutationObserver(function(){H.classList.toggle('lr-deck',isDeck())});
mo.observe(H,{attributes:true,subtree:true,attributeFilter:['class']});H.classList.toggle('lr-deck',isDeck());

var prog=D.createElement('div');prog.id='lr-prog';B.appendChild(prog);
var bar=D.createElement('div');bar.id='lr-bar';bar.innerHTML=
 '<button id="lr-pv" aria-label="Previous line" title="Previous (←)">&#8592;</button>'+
 '<button id="lr-pos" aria-label="Jump to section" title="Jump to section">0/0</button>'+
 '<button id="lr-nx" aria-label="Next line" title="Next (→)">&#8594;</button>'+
 '<button id="lr-k" class="lr-sm lr-k" aria-label="Mark known" title="Mark known, skip next pass (K)">&#10003;</button>'+
 '<button id="lr-fm" class="lr-sm" aria-label="Focus mode" title="Focus (F)">Focus</button>';
B.appendChild(bar);
var menu=D.createElement('div');menu.id='lr-menu';B.appendChild(menu);
var $=function(id){return D.getElementById(id)};

function knownN(){var n=0;for(var k in st.known)if(st.known[k])n++;return n}
function ui(){var i=st.i;$('lr-pos').textContent=(i+1)+'/'+items.length;
 prog.style.width=(items.length?((i+1)/items.length*(vv?vv.width:innerWidth)):0)+'px';
 var c=items[i];$('lr-k').classList.toggle('on',!!(c&&st.known[i]));
 $('lr-fm').textContent=H.classList.contains('lr-focus')?'Focus off':'Focus'}
items.forEach(function(e,n){if(st.known[n])e.classList.add('lr-known')});
function openUp(el){var d=el.closest('details');while(d){d.open=true;d=d.parentElement&&d.parentElement.closest('details')}
 if(el.tagName==='SUMMARY'&&el.parentElement)el.parentElement.open=true}
function show(n,dir){if(!items.length)return;n=Math.max(0,Math.min(items.length-1,n));
 if(dir&&st.skip){var m=n;while(m>=0&&m<items.length&&st.known[m])m+=dir;if(m>=0&&m<items.length)n=m}
 var old=D.querySelector('.lr-cur');if(old)old.classList.remove('lr-cur');
 st.i=n;var el=items[n];openUp(el);el.classList.add('lr-cur');H.classList.add('lr-focus');
 var r=el.getBoundingClientRect(),far=Math.abs(r.top+r.height/2-innerHeight/2)>innerHeight*1.2;
 el.scrollIntoView({block:r.height>innerHeight*.8?'start':'center',behavior:far?'auto':'smooth'});save();ui()}
function step(d){show(st.i<0?0:st.i+d,d)}
function known(){if(st.i<0)return;var i=st.i;st.known[i]=!st.known[i];items[i].classList.toggle('lr-known',!!st.known[i]);save();ui()}
function focus(){if(H.classList.toggle('lr-focus')){show(st.i<0?0:st.i)}else{var c=D.querySelector('.lr-cur');if(c)c.classList.remove('lr-cur')}ui()}

function buildMenu(){var hs=items.filter(function(e){return /^H[12]$/.test(e.tagName)});
 if(hs.length<2)hs=items.filter(function(e){return /^H[1-3]$/.test(e.tagName)||e.tagName==='SUMMARY'&&!e.closest('details details')});
 menu.innerHTML=hs.slice(0,80).map(function(e){return '<a href="#" data-n="'+e.dataset.lrN+'">'+(e.textContent||'').trim().slice(0,70).replace(/</g,'&lt;')+'</a>'}).join('')+
  '<label class="lr-opt"><input type="checkbox" id="lr-skip"'+(st.skip?' checked':'')+'> Skip lines marked known ('+knownN()+')</label>'+
  '<a href="#" id="lr-clear" class="lr-opt">Clear known marks</a>';
 $('lr-skip').onchange=function(){st.skip=this.checked;save()};
 $('lr-clear').onclick=function(ev){ev.preventDefault();st.known={};items.forEach(function(e){e.classList.remove('lr-known')});save();ui();menu.classList.remove('open')};
 [].forEach.call(menu.querySelectorAll('a[data-n]'),function(a){a.onclick=function(ev){ev.preventDefault();menu.classList.remove('open');show(+a.dataset.n)}})}
$('lr-pos').onclick=function(){if(!menu.classList.contains('open'))buildMenu();menu.classList.toggle('open')};
$('lr-nx').onclick=function(){step(1)};$('lr-pv').onclick=function(){step(-1)};
$('lr-k').onclick=known;$('lr-fm').onclick=focus;

D.addEventListener('keydown',function(e){
 if(e.defaultPrevented||isDeck()||e.ctrlKey||e.metaKey||e.altKey)return;
 if(/input|textarea|select/i.test(e.target.tagName)||e.target.isContentEditable)return;
 if(e.key==='ArrowRight'){e.preventDefault();step(1)}
 else if(e.key==='ArrowLeft'){e.preventDefault();step(-1)}
 else if(e.key==='k'||e.key==='K'){known()}
 else if(e.key==='f'||e.key==='F'){focus()}
 else if(e.key==='Escape'){menu.classList.remove('open');if(H.classList.contains('lr-focus'))focus()}
});
items.forEach(function(e,n){e.addEventListener('click',function(ev){
 if(H.classList.contains('lr-focus')&&!ev.target.closest('a,input,button,summary')){show(n)}})});
// swipe left/right on a phone, only in Focus mode, not on things that scroll sideways
var t0=null;
D.addEventListener('touchstart',function(e){if(e.touches.length!==1||!H.classList.contains('lr-focus')||isDeck()||e.target.closest('pre,table,svg,#lr-bar,#lr-menu,[style*="overflow"]')){t0=null;return}
 t0={x:e.touches[0].clientX,y:e.touches[0].clientY,t:Date.now()}},{passive:true});
D.addEventListener('touchend',function(e){if(!t0)return;var c=e.changedTouches[0],dx=c.clientX-t0.x,dy=c.clientY-t0.y;
 if(Math.abs(dx)>60&&Math.abs(dy)<45&&Date.now()-t0.t<600)step(dx<0?1:-1);t0=null},{passive:true});
// keep the bar centred on what the reader sees, even when a page is wider than the phone screen
function place(){if(!vv)return;var x=vv.offsetLeft+vv.width/2;bar.style.left=x+'px';menu.style.left=x+'px';
 prog.style.left=vv.offsetLeft+'px';prog.style.maxWidth=vv.width+'px'}
if(vv){vv.addEventListener('resize',place);vv.addEventListener('scroll',place);place()}
ui();
})();
"""

START, END = "<!-- line-reader:start -->", "<!-- line-reader:end -->"
BLOCK = f"{START}<style>{CSS}</style><script>{JS}</script>{END}"


def inject(html: str) -> str:
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S)
    i = html.lower().rfind("</body>")
    return html[:i] + BLOCK + html[i:] if i >= 0 else html + BLOCK


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        out = inject(src)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print("line reader ->", path)
