# 키보드 단축키 + 키 표시 (라오스 앱 v2.74~v2.78과 같은 기능). usage: python3 kbd_patch.py <pwa dir>
import sys, os, re, shutil
R = sys.argv[1]; H = os.path.dirname(os.path.abspath(__file__))
s = open(R + '/app.js').read(); blk = open(H + '/kbd_block.js').read()
blk = re.sub(r'v2\.7\d RYU: ', '', blk)
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:50], s.count(a)); s = s.replace(a, b)
a = 'document.addEventListener("click",e=>{\n  const ko=e.target.closest(".hide-ko .ko")'
rep(a, blk + a)
rep('const it=P.queue[P.i];if(!it){P.i++;return}if(P.i<it.ge){P.i++;return}', 'const it=P.queue[P.i];if(!it){P.i++;return}if(P.rel){P.rel=0;P.k=0;P.i=it.ge+1;return}if(P.i<it.ge){P.i++;return}')
rep('function stopPlay(){P.token++;', 'function stopPlay(){P.rel=0;P.token++;')
# K = Korean voice on/off
rep('let REP=store.get("rw-rep",2);', 'let REP=store.get("rw-rep",2);let SAYKO=store.get("rw-sayko",true)!==false;')
rep('<span class="nbl">← 이전 묶음</span>', '<span class="nbl"><kbd class="kc">&lt;</kbd>← 이전 묶음</span>')
rep('<span class="nbl">다음 묶음 →</span>', '<span class="nbl">다음 묶음 →<kbd class="kc">&gt;</kbd></span>')
# no target-language-only review pass after word cards
m = re.findall(r'\n  if\(!single&&items\.every\(it=>it&&/\^cd-/\.test\(it\.id\|\|""\)\)\)\{[^\n]*', s)
assert len(m) == 1, len(m); s = s.replace(m[0], '')
rep('blobUrl("_gap450").catch(()=>{});', 'blobUrl("_gap150").catch(()=>{});blobUrl("_gap450").catch(()=>{});')
rep('  const it=P.queue[P.i];cardSync(it);mark(it.id);showPlayer();', '  const it=P.queue[P.i];if(it.ko&&!SAYKO){advQ();nextPlay(tok);return}cardSync(it);mark(it.id);showPlayer();')
g = 'P.i>=P.queue.length||(P.queue[P.i].rv&&P.queue[P.i].rv0===P.i)?900:450'
assert s.count(g) == 2, s.count(g); s = s.replace(g, 'gapMs(it)')
fn = '''/* the same sentence again = short pause only */
function gapMs(it){const q=P.queue;if(P.i>=q.length)return 900;let j=P.i;if(!SAYKO)while(j<q.length&&q[j].ko)j++;const n=q[j];return n&&!it.ko&&!n.ko&&n.text===it.text?150:450}
function setSayKo(v){SAYKO=!!v;store.set("rw-sayko",SAYKO);const c=document.getElementById("koChk");if(c)c.checked=SAYKO}
{const c=document.getElementById("koChk");if(c){c.checked=SAYKO;c.addEventListener("change",()=>{setSayKo(c.checked);try{c.blur()}catch(e){}})}}
'''
rep('document.addEventListener("keydown",e=>{if(e.ctrlKey', fn + 'document.addEventListener("keydown",e=>{if(e.ctrlKey')
rep('data-playbundle="${b}" data-chain="1" aria-label="이 묶음부터 다음 묶음으로 이어서 반복">${RPT}<span>연속 재생</span></button>', 'data-playbundle="${b}" data-chain="1" aria-label="이 묶음부터 다음 묶음으로 이어서 반복">${RPT}<span>연속 재생</span><kbd class="kc">C</kbd></button>')
rep('<button class="speak all" data-playbundle="${b}">${RPT}<span>묶음 재생</span></button>', '<button class="speak all" data-playbundle="${b}">${RPT}<span>묶음 재생</span><kbd class="kc">G</kbd></button>')
rep('Promise.all([blobUrl("_gap450"),', 'Promise.all([blobUrl("_gap150"),blobUrl("_gap450"),')
# v1.11: follow scroll only when the playing item leaves the middle area; speed 0.7-2.0; tighter lists; moved bundles keep their records
rep('d=(r.top+r.height/2)-(innerHeight-ph)/2;if(Math.abs(d)>24)window.scrollBy({top:d,behavior:"smooth"})', 'H=innerHeight-ph,c=r.top+r.height/2,d=c-H*.25;if(c<H*.25||c>H*.75||(r.top<0&&r.height<H)||(r.bottom>H&&r.height<H))window.scrollBy({top:d,behavior:"smooth"})')
rep('let RATE=store.get("rw-rate",1);if(![0.8,1,1.2,1.5,2].includes(RATE))RATE=1;', 'let RATE=store.get("rw-rate",1);if(!(RATE>=0.7&&RATE<=2))RATE=1;RATE=Math.round(RATE*10)/10;')
rep("line-height:1.35}';\ndocument.head.appendChild(st);", "line-height:1.35}.ddl button:not(.ctr){padding:.22em 1em;line-height:1.25}';\ndocument.head.appendChild(st);")
import json, titles
a = 'let known=store.get("rw-known",{});const saved=store.get("rw-sel",{});'
rep(a, a + 'const IDMAP1=' + json.dumps(titles.IDMAP) + ';if(store.get("rw-idv",0)<1){const k2={};for(const k in known){const m=/^(\\d-\\d{2}-\\d{2})::/.exec(k);k2[m&&IDMAP1[m[1]]?IDMAP1[m[1]]+k.slice(m[1].length):k]=known[k]}known=k2;store.set("rw-known",known);if(saved.bun)for(const k in saved.bun)if(IDMAP1[saved.bun[k]])saved.bun[k]=IDMAP1[saved.bun[k]];store.set("rw-sel",saved);store.set("rw-idv",1)}')
s = s + '\n' + open(H + '/swipe_block.js').read()
# bundle list opens only on a real tap (a swipe's synthetic click on 다음 묶음 has x=y=0 and could hit the list box at the top)
rep('document.addEventListener("click",function(e){if(e.target.closest&&e.target.closest(".ddl,.ddbg"))return;', 'document.addEventListener("click",function(e){if(!e.isTrusted)return;if(e.target.closest&&e.target.closest(".ddl,.ddbg"))return;')
open(R + '/app.js', 'w').write(s)

s = open(R + '/index.html').read()
for k, c in (('예문보기', 'Q'), ('단어공부', 'W'), ('확인퀴즈', 'E')):
    rep('<span class="ll">%s</span></button>' % k, '<span class="ll">%s</span><kbd class="kc">%s</kbd></button>' % (k, c))
rep('<span class="ll olab">반복</span>', '<span class="ll olab">반복<kbd class="kc">1~5</kbd></span>')
rep('<span class="ll olab">배속</span>', '<span class="ll olab">배속<kbd class="kc">±</kbd></span>')
rep('<div class="bact" id="bact"></div>', '<div class="bact" id="bact"></div>\n      <div class="kbinfo" id="kbinfo"><span><kbd class="kc">Esc</kbd>재생 정지</span><span><kbd class="kc">Enter</kbd>무한 반복/취소</span><span><kbd class="kc">←</kbd>이전 문장</span><span><kbd class="kc">→</kbd>다음 문장</span><label class="kok"><input type="checkbox" id="koChk" checked><kbd class="kc">K</kbd>한국어 말하기</label></div>')
css = '''<style>/* keyboard key badges next to the buttons (PC and pad only) */
.kc{display:none;font:600 10.5px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;min-width:17px;height:17px;padding:0 4px;box-sizing:border-box;align-items:center;justify-content:center;border:1px solid currentColor;border-bottom-width:2.5px;border-radius:5px;margin-left:6px;opacity:.72;vertical-align:1px;letter-spacing:0;white-space:nowrap}
html.tab .kc{display:inline-flex;font-size:12.5px;min-width:21px;height:21px;border-radius:6px}
@media (hover:hover) and (pointer:fine){.kc{display:inline-flex}}
.nextbun .nbl{display:inline-flex;align-items:center}.nextbun.prevbun .kc{margin-left:0;margin-right:6px}
/* second key line under 연속/묶음 재생 (PC and pad only) + K = Korean on/off */
.kbinfo{display:none;order:99;flex-basis:100%;justify-content:center;flex-wrap:wrap;gap:4px 16px;font-size:12.5px;color:var(--muted);margin-top:2px}
.kbinfo span,.kbinfo label{display:inline-flex;align-items:center;gap:0;white-space:nowrap}.kbinfo .kc{margin:0 5px 0 0}
.kbinfo label{cursor:pointer;color:var(--ink)}.kbinfo input{margin:0 6px 0 0;width:15px;height:15px;accent-color:var(--accent);cursor:pointer}
html.tab .kbinfo{display:flex;font-size:15px}html.tab .kbinfo input{width:18px;height:18px}
@media (hover:hover) and (pointer:fine){.kbinfo{display:flex}}
/* flatter header (tighter lines) + key info line in small muted text */
header{padding-top:12px!important;padding-bottom:10px!important;min-height:0!important}
header .eyebrow{line-height:1.15;display:block}
h1.lotitle{line-height:.98!important;margin-top:-.06em!important}
.kbinfo{font-size:11.5px!important;color:var(--muted)}.kbinfo label{color:var(--muted)}.kbinfo .kc{font-size:10px;height:16px;min-width:16px}
html.tab .kbinfo{font-size:14px!important}html.tab .kbinfo .kc{font-size:11.5px;height:19px;min-width:19px}
</style></head>'''
css = css.replace('</style></head>', """/* phone shows only the 한국어 말하기 checkbox from the key line */
html:not(.tab) .kbinfo{display:flex;justify-content:center;font-size:12.5px!important}html:not(.tab) .kbinfo>span{display:none}html:not(.tab) .kbinfo label{color:var(--ink);-webkit-tap-highlight-color:transparent;user-select:none;-webkit-user-select:none}
@media (hover:hover) and (pointer:fine){html:not(.tab) .kbinfo{justify-content:center;font-size:11.5px!important}html:not(.tab) .kbinfo>span{display:inline-flex}html:not(.tab) .kbinfo label{color:var(--muted)}}
/* phone: 연속·묶음 재생 and 한국어 말하기 centred */
.controls .bact{justify-content:center!important}
@media (hover:none),(pointer:coarse){html:not(.tab) .controls::after{content:"";order:7;flex:0 0 100%;height:0}html:not(.tab) .controls .kbinfo{order:8;flex:0 0 auto;margin:0!important}html:not(.tab) .controls .bact{order:9;flex:0 0 auto;margin-top:0}html:not(.tab) .controls{row-gap:10px;justify-content:center!important}}
/* menu separators | (before 기초회화, before 르완다, before and after 도움말) */
.group[data-g="P8"]::before,.group[data-g="PH"]::before{content:"|"!important;font-weight:400!important;opacity:.7!important;transform:translate(-50%,-52%)!important}.groups::before,.groups::after{content:"|";flex:0 0 auto;align-self:center;color:var(--muted);opacity:.7;font-size:20px;line-height:1;transform:translateY(-2px)}.groups::before{margin-right:-14px;transform:translate(-2px,-2px)}.groups::after{margin-left:-12px}
/* small middle dot between main tabs, inside the same 18px gap */
.group+.group::before{content:"·";position:absolute;left:-9px;top:50%;transform:translate(-50%,-55%);color:var(--muted);opacity:.55;font-weight:700;pointer-events:none}
</style></head>""")
css = css.replace('</style></head>', """/* menu also in a box (PC padding = content box), phone side gutters smaller */
.menubox{background:var(--sheet);border:1px solid var(--line);border-radius:16px;padding:12px 20px 10px;display:flex;flex-direction:column;gap:10px;min-width:0}html.pre .menubox{display:none!important}.menubox .groups{padding-left:0!important;padding-right:0!important}@media (max-width:640px){.wrap{padding-left:max(6px,env(safe-area-inset-left,0px))!important;padding-right:max(6px,env(safe-area-inset-right,0px))!important}.menubox{padding:8px 8px 6px;border-radius:12px}.sheet{border-radius:12px}.sheet>.band,.sheet>.controls,.sheet>.body{padding-left:8px!important;padding-right:8px!important}.sheet .entry{margin-left:-8px!important;margin-right:-8px!important;padding-left:8px!important;padding-right:8px!important}}
</style></head>""")
rep('</head>', css)
rep('  <nav class="groups" id="groups" aria-label="대분류"></nav>\n  <nav class="subs" id="subs" role="tablist" aria-label="소분류"></nav>\n  <div class="sinfo" id="sinfo"></div>\n', '  <div class="menubox">\n  <nav class="groups" id="groups" aria-label="대분류"></nav>\n  <nav class="subs" id="subs" role="tablist" aria-label="소분류"></nav>\n  <div class="sinfo" id="sinfo"></div>\n  </div>\n')
rep('<option value="0.8">x 0.8</option><option value="1">x 1.0</option><option value="1.2">x 1.2</option><option value="1.5">x 1.5</option><option value="2">x 2.0</option>', ''.join('<option value="%g">x %.1f</option>' % (n / 10, n / 10) for n in range(7, 21)))
rep('<div class="kbinfo" id="kbinfo"><span>', '<div class="kbinfo" id="kbinfo"><span><kbd class="kc">Space</kbd>일시정지/재개</span><span>')
open(R + '/index.html', 'w').write(s)

s = open(R + '/sw.js').read()
if '"_gap450"' in s: rep('["_gap450",', '["_gap150","_gap450",')
open(R + '/sw.js', 'w').write(s)
shutil.copyfile(H + '/base/_gap150.mp3', R + '/audio/_gap150.mp3')
print('keyboard ok')
