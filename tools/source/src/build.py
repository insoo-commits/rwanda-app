"""Build the Kinyarwanda PWA (RWANDA Lang) from the Lao app code (src/base = insoo-commits/lao-app v2.53, the same base as the Thai app v1.2)
+ content files content/c*.txt.  Usage: python3 build.py <out_dir> [version]
Content DSL (as in the Thai app; ' | ' separates fields):
  # P5-K | 기초 회화                      sub id | name
  @ 1-01-01 | 첫인사 | Muraho·Murakoze | intro   bundle id | Korean title | Kinyarwanda label | intro
  w word | hint | meaning [| reading]     word (hint '=' = meaning); reading is automatic (rwrd.py) unless given
  e sentence | ko                        example of the last word (2nd example = lower voice)
  tp text / nx text / qz q | a
  pr rw | ko || rw | ko                   pair sentences
  dl who | rw | ko                        dialog (even lines voice 1, odd lines lower voice)
  sm rw | ko                              one-line summary sentence
  x word(s) | meaning [| reading]         note-dictionary entry (lowercase; up to 4 words)
  rd word | reading                       global reading override
"""
import json,sys,os,glob,base64,re,shutil,datetime
here=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,here)
import rwrd
out=sys.argv[1] if len(sys.argv)>1 else None; VER=sys.argv[2] if len(sys.argv)>2 else "0.1"
DATE=datetime.date.today().isoformat()
LAT=re.compile("[A-Za-z]")
EXTRA_E=[];subs=[];B={};BLAB={};X={};RDO={};SUBNAME={};SAYO={}
def P_(rest): return [x.strip() for x in rest.split(' | ')]
for f in sorted(glob.glob(here+'/content/c*.txt')):
    cur=None;sid=None
    for n,line in enumerate(open(f,encoding='utf-8'),1):
        line=line.rstrip('\n').strip()
        if not line or line.startswith('//'): continue
        tag,_,rest=line.partition(' ');P=P_(rest)
        try:
            if tag=='#':
                sid=P[0];SUBNAME[sid]=P[1]
                if not any(s["id"]==sid for s in subs): subs.append({"id":sid,"name":P[1].replace(' ',''),"b":[]})
            elif tag=='@':
                assert len(P)==4,P
                cur={"t":P[1],"h":"","i":P[3],"w":[],"tp":[],"nx":[],"pr":[],"dl":[],"sm":["","",""],"qz":[]}
                assert P[0] not in B,('dup bundle',P[0]);B[P[0]]=cur;BLAB[P[0]]=[P[1],P[2]]
                [s for s in subs if s["id"]==sid][0]["b"].append(P[0])
            elif tag=='w':
                assert len(P) in (3,4),P
                cur["w"].append([P[0],P[2] if P[1]=='=' else P[1],P[3] if len(P)==4 else None,P[2],[]])
            elif tag=='e': assert len(P)==2,P;cur["w"][-1][4].append([P[0],None,P[1]])
            elif tag=='tp': cur["tp"].append('• '+rest.strip())
            elif tag=='nx': cur["nx"].append(rest.strip())
            elif tag=='pr':
                a,b2=[[y.strip() for y in x.split(' | ')] for x in rest.split(' || ')];assert len(a)==2 and len(b2)==2,(a,b2)
                cur["pr"].append([[a[0],None,a[1]],[b2[0],None,b2[1]]])
            elif tag=='dl': assert len(P)==3,P;cur["dl"].append([P[0],P[1],None,P[2]])
            elif tag=='sm': assert len(P)==2,P;cur["sm"]=[P[0],None,P[1]]
            elif tag=='qz': assert len(P)==2,P;cur["qz"].append(P)
            elif tag=='x': assert len(P) in (2,3),P;X[P[0].lower()]=P[1];(len(P)==3 and RDO.__setitem__(P[0].lower(),P[2]))
            elif tag=='rd': assert len(P)==2,P;RDO[P[0].lower()]=P[1]
            elif tag=='E': assert len(P)==4,P;EXTRA_E.append((P,f,n))
            elif tag=='sy': assert len(P)==2,P;SAYO[P[0]]=P[1]
            else: raise ValueError('tag '+tag)
        except Exception as ex: raise SystemExit(f'{f}:{n}: {line} ({ex!r})')
for P,f,n in EXTRA_E:
    ws=[w for w in B.get(P[0],{"w":[]})["w"] if w[0]==P[1]]
    if not ws: raise SystemExit(f'{f}:{n}: E target not found {P[0]} {P[1]}')
    ws[0][4].append([P[2],None,P[3]])
for s in subs: s["b"].sort()
for k,b in B.items():
    b["h"]=" · ".join(w[0] for w in b["w"])
    for w in b["w"]: assert len(w[4])>=2,(k,w[0],'needs 2+ examples')
    for w in b["w"]:
        if w[2]: RDO.setdefault(w[0].lower(),w[2])
# ---------- '원래 x-xx-xx' references: point each copy at a bundle that really holds the word, else drop it
def _hw(x): return re.sub(r'\s*\([^)]*\)\s*$','',x).replace('…','').strip()
_ORIG={}
for bid,b in B.items():
    for w in b["w"]:
        if '원래' not in w[1]: _ORIG.setdefault(_hw(w[0]),[]).append(bid)
REFFIX=[]
for bid,b in B.items():
    for w in b["w"]:
        m=re.search(r'\s*·?\s*원래 (\d-\d{2}-\d{2})',w[1])
        if not m: continue
        ref=m.group(1);hw=_hw(w[0])
        if ref in B and ref!=bid and any(_hw(x[0])==hw for x in B[ref]["w"]): continue
        cand=[c for c in _ORIG.get(hw,[]) if c!=bid]
        if cand: w[1]=w[1][:m.start()]+' · 원래 '+cand[0]+w[1][m.end():];REFFIX.append((bid,hw,ref,cand[0]))
        else: w[1]=(w[1][:m.start()]+w[1][m.end():]).strip(' ·');REFFIX.append((bid,hw,ref,None))
# ---------- readings (rule-based, rwrd.py; rd/x lines override single words)
WRE=re.compile(r"[A-Za-z][A-Za-z'’\-]*")
TOKS={}
def rdw(t):
    k=t.lower().replace('’',"'")
    if k in RDO: return RDO[k]
    if "'" in k:
        a,_,b=k.partition("'")
        if b in RDO: return rwrd.word(a)[:-1]+RDO[b] if False else rwrd.word(k)
    return rwrd.word(k)
def rd(t):
    t=t.replace('…',' … ')
    outp=[]
    for tk in re.findall(r"[A-Za-z][A-Za-z'’\-]*|\d[\d.,:]*|[?!.,…—–:;]",t):
        if LAT.match(tk):
            TOKS[tk.lower()]=TOKS.get(tk.lower(),0)+1
            outp.append(rdw(tk.strip('-')))
        elif tk in '?!.,:;':
            if outp: outp[-1]+=tk
        else: outp.append(tk)
    return re.sub(r'\s+',' ',' '.join(outp)).strip()
def rdhead(t):
    t=re.sub(r'\s*\([^)]*[가-힣][^)]*\)','',t)
    k=t.replace('…','').strip().lower()
    if k in RDO: return RDO[k]+('…' if t.endswith('…') else '')
    return rd(t)
for b in B.values():
    for w in b["w"]:
        w[2]=rdhead(w[0])
        for e in w[4]: e[1]=rd(e[0])
    for pr in b["pr"]:
        for x in pr: x[1]=rd(x[0])
    for x in b["dl"]: x[2]=rd(x[1])
    if b["sm"][0]: b["sm"][1]=rd(b["sm"][0])
# front text: a Kinyarwanda phrase in intro/tips gets its reading in parentheses (as in the Thai and Khmer apps)
def addrd(t):
    def f(m):
        run,par=m.group(1),m.group(3)
        if run.endswith('-') or run.startswith('-') or len(run)<=1: return m.group(0)   # prefixes (Mu-, Nti-) are not words
        if run.lower() in ('k','sms','ok','tv','id'): return m.group(0)
        r=rd(run)
        if par is not None:
            sq=lambda x:re.sub(r'[\s,?·!.]','',x)
            if sq(par).startswith(sq(r)): return m.group(0)
            return f'{run}({r} · {par})'
        return f'{run}({r})'
    return re.sub(r"(-?[A-Za-z][A-Za-z'’]*-?(?: [A-Za-z][A-Za-z'’]*-?)*)(\(([^()]*)\))?",f,t)
_T0=dict(TOKS)
for b in B.values():
    b["i"]=addrd(b["i"]);b["tp"]=[addrd(t) for t in b["tp"]];b["qz"]=[[q,addrd(a)] for q,a in b["qz"]]
TOKS.clear();TOKS.update(_T0)
PMETA=[("P5","기초회화","학교·식당·시장·병원 등 장면별 단어와 문장"),("P6","문자학습","르완다어 글자와 소리: 모음, 자음, 함께 읽는 글자(cy·shy·ny·rw…)"),("P7","문장규칙","어순·명사 부류·인칭·시제·부정·질문 등 문장을 만드는 기초 문법"),("P4","짝말비교","반대말·단수와 복수·묻고 답하는 짝"),("P3","비슷한말","뜻은 비슷하지만 쓰임이 다른 말"),("P2","단어가족","뿌리가 같은 말. 앞뒤에 붙는 말로 뜻이 넓어지는 단어 가족"),("P1","발음구별","한글로 쓰면 같거나 비슷해서 헷갈리는 소리")]
DATA={"P":[{"id":p,"ko":k,"desc":d,"subs":[x for x in subs if x["id"].startswith(p+'-')]} for p,k,d in PMETA],"B":B}
DATA["P"]=[p for p in DATA["P"] if p["subs"]]
# ---------- note dictionary (keys lowercase; phrases up to 4 words)
ND={};NR={}
def nk(x): return re.sub(r'\s+',' ',re.sub(r'\+?\s*[\uac00-\ud7a3]+','',x).replace('…','').replace('?','').replace('!','').replace('’',"'")).strip().lower()
for b in B.values():
    for w in b["w"]:
        k=nk(re.sub(r'\s*\([^)]*\)','',w[0]))
        if not k or len(k.split())>4: continue
        ND.setdefault(k,re.split(r"[;(]",w[3])[0].strip());NR.setdefault(k,rdhead(w[0]))
for k,mn in X.items(): ND[k]=mn;NR[k]=RDO.get(k) or rd(k)
alltxt=" ".join(e[0] for b in B.values() for w in b["w"] for e in w[4]).lower()
NF={k:len(re.findall(r'(?<![a-z\'])'+re.escape(k)+r'(?![a-z])',alltxt)) for k in ND}
def known(t):
    if t in ND: return True
    if "'" in t: return known(t.split("'",1)[1])
    return any(v+t in ND for v in 'iua')   # nouns lose their first vowel after mu/ku/nta (mu nzu = inzu)
def _cover(t):
    ws=[x.rstrip('-') for x in re.findall(r"[a-z][a-z'\-]*",t.lower().replace('’',"'"))];miss=[];i=0
    while i<len(ws):
        for L in range(min(4,len(ws)-i),0,-1):
            if ' '.join(ws[i:i+L]) in ND: i+=L;break
        else:
            if not known(ws[i]): miss.append(ws[i])
            i+=1
    return miss
_MC={}
for b in B.values():
    for w in b["w"]:
        hw=set(nk(w[0]).split())
        for e in w[4]:
            for m in _cover(e[0]):
                if m not in hw: _MC[m]=_MC.get(m,0)+1
    for x in [y[1] for y in b["dl"]]+[q[0] for pr in b["pr"] for q in pr]+([b["sm"][0]] if b["sm"][0] else []):
        for m in _cover(x): _MC[m]=_MC.get(m,0)+1
NOMEAN=sorted(_MC,key=lambda t:-_MC[t]);TOKS.update({k:_MC[k] for k in _MC})
J=lambda o:json.dumps(o,ensure_ascii=False,separators=(",",":"))
def akey(t):
    t=re.sub(r'\s+',' ',t).strip();h=0x811c9dc5
    for ch in t:
        for cu in ([ord(ch)] if ord(ch)<0x10000 else [0xD800+((ord(ch)-0x10000)>>10),0xDC00+((ord(ch)-0x10000)&0x3FF)]):
            h^=cu;h=(h*0x01000193)&0xFFFFFFFF
    d='0123456789abcdefghijklmnopqrstuvwxyz';o=''
    while True:
        o=d[h%36]+o;h//=36
        if not h: break
    return o
def kosay(t):
    t=re.sub('[①-⑳]','',t);t=re.sub(r'\s*\([^)]*\)','',t);t=re.sub('[;·]',',',t);t=re.sub(r'\s+',' ',t).strip()
    return t.replace('—',',').replace('~','')
LF={};LM={};LK={}
def say(t):
    if t in SAYO: return SAYO[t]
    t=re.sub(r'\s*\([^)]*[가-힣][^)]*\)','',t)
    t=re.sub(r'[가-힣]+','',t).replace('+',' ')
    return re.sub(r'\s+',' ',t.replace('…',' ').replace('—',', ')).strip()
def clip(t,male):
    if not t: return
    male=False   # RYU 2026-11-19: one Kinyarwanda voice for everything (the lowered second voice sounded odd)
    (LM.__setitem__('m_'+akey(t),say(t)) if male else LF.__setitem__(akey(t),say(t)))
def kclip(t):
    if t: LK['k_'+akey(t)]=kosay(t)
for b in B.values():
    for w in b["w"]:
        clip(w[0],False);kclip(w[3])
        for i,e in enumerate(w[4]): clip(e[0],i==1);kclip(e[2])
    for pr in b["pr"]:
        for x in pr: clip(x[0],False);kclip(x[2])
    for i,x in enumerate(b["dl"]): clip(x[1],i%2==1);kclip(x[3])
    if b["sm"][0]: clip(b["sm"][0],False);kclip(b["sm"][2])
nw=sum(len(b["w"]) for b in B.values());ns=sum(sum(len(w[4]) for w in b["w"])+len(b["pr"])*2+len(b["dl"])+(1 if b["sm"][0] else 0) for b in B.values())
if out is None:
    print(len(B),'bundles',nw,'words',ns,'sentences; no meaning:',len(NOMEAN));print(' '.join(NOMEAN[:400]));sys.exit()
os.makedirs(out+'/audio',exist_ok=True)
json.dump({"reffix":REFFIX,"nomean":[[t,TOKS[t]] for t in NOMEAN]},open(out+'/../lint.json','w'),ensure_ascii=False,indent=0)
# ---------- app.js from the Lao base
L=open(here+'/base/app.js',encoding='utf-8').read().split('\n')
def find(prefix,start=0):
    for i in range(start,len(L)):
        if L[i].startswith(prefix): return i
    raise SystemExit('marker not found: '+prefix)
code=list(L)
def setline(prefix,new):
    i=find(prefix);code[i]=new
# bundle ids follow the tab order: content files keep their own numbers (1 주제별, 6 글자 → 2, 7 문법 → 3, 2 짝말 → 4, 3 닮은말 → 5, 4 말뿌리 → 6, 5 말소리 → 7)
# (only parts that exist count: the app numbers parts by position)
order=[p["id"] for p in DATA["P"]];FILEN={'P5':'1','P6':'6','P7':'7','P4':'2','P3':'3','P2':'4','P1':'5'}
IDP={FILEN[p]:str(i+1) for i,p in enumerate(order)}
_IDRE=re.compile(r'(?<![\d\-])([1-7])-(\d{2})(-\d{2})?(?![\d\-])')
def _rid(x):
    if isinstance(x,str): return _IDRE.sub(lambda m:IDP.get(m.group(1),m.group(1))+'-'+m.group(2)+(m.group(3) or ''),x)
    if isinstance(x,list): return [_rid(y) for y in x]
    if isinstance(x,dict): return {_rid(k):_rid(v) for k,v in x.items()}
    return x
DATA=_rid(DATA);BLAB=_rid(BLAB)
import titles;titles.apply(DATA,BLAB)
DATA,BLAB=titles.move(DATA,BLAB)
DATA["B"]=dict(sorted(DATA["B"].items()))
code[0]="const DATA=JSON.parse("+json.dumps(J(DATA),ensure_ascii=False)+");"
i4=find('const NDICT=');code[i4]=f"const NDICT={J(ND)},NRD={J(NR)},NFREQ={J(NF)},NSTOP=new Set([]);"
for i in range(i4+1,find('function notesOf')):
    if code[i].startswith('Object.assign(NDICT') or code[i].startswith('/*') and 'Object.assign(NDICT' in code[i]: code[i]=''
a=find('let known=store.get(');b2=find('let S={')
for i in range(a,b2): code[i]=''
code[a]='let known=store.get("rw-known",{});const saved=store.get("rw-sel",{});'
code[find('const BLAB=')]="const BLAB="+J(BLAB)+";"
# no tones in written Kinyarwanda: a stub TN, no marks, no legend
a=find('const TN=(()=>');b2=find('return {seg:seg,tone:tone,MK:MK}})();')
code[a]='const TN={seg:()=>[],tone:()=>"",MK:{}};'
for i in range(a+1,b2+1): code[i]=''
setline('const PARTEN=','const PARTEN={P1:"SOUND",P2:"ROOT",P3:"MEANING",P4:"PAIR",P5:"SCENE",P6:"LETTER",P7:"GRAMMAR"};')
setline('const TLEG=','const TLEG=[];')
setline('const TONE_IDS=','const TONE_IDS={has:()=>false}; /* Kinyarwanda: tones are not written */')
a=find('const HCL=');b2=find('const nmean0=')
code[a]='const NSENSE={};const nmean=(t,lo,ko)=>NDICT[t];'
for i in range(a+1,b2+1): code[i]=''
a=find('const SWATCH=');code[a]=open(here+'/swatch.js',encoding='utf-8').read().rstrip('\n')
a=find('(function(){var KEYS=');code[a]=''
# ※ notes: whole words (Kinyarwanda is written with spaces, so a word is never cut), longest phrase first (up to 4 words)
a=find('function notesOf(');b2=find('function noteMark(')
code[a]=r'''function notesOf(lo,w){const hw=(w||"").replace(/[…?!]/g,"").trim().toLowerCase().replace(/’/g,"'");const hws=new Set(hw.split(/\s+/));const seen=new Set(),out=[];
  const ws=(lo.toLowerCase().replace(/’/g,"'").match(/[a-z][a-z'\-]*/g)||[]).map(x=>x.replace(/-+$/,""));
  for(let i=0;i<ws.length;){let hit=null,len=1;for(let L=Math.min(4,ws.length-i);L>=1;L--){const t=ws.slice(i,i+L).join(" ");if(NDICT[t]!==undefined){hit=t;len=L;break}}
    if(!hit){let x=ws[i];const k=x.indexOf("'");if(k>0&&NDICT[x.slice(k+1)]!==undefined)hit=x.slice(k+1);else{if(k>0)x=x.slice(k+1);for(const v of "iua")if(NDICT[v+x]!==undefined){hit=v+x;break}}}
    i+=len;if(!hit||seen.has(hit)||hit===hw||(len===1&&hws.has(hit))||(hw.length>3&&hit.length>3&&hw.includes(hit)&&hit.includes(" ")))continue;seen.add(hit);out.push(hit)}
  const wd=t=>t.length*0.62+[...((NRD[t]?" "+NRD[t]:"")+"("+NDICT[t]+")")].reduce((a,c)=>a+(/[가-힣]/.test(c)?1:0.55),0)+1.6;
  const cap=(typeof isBig==="function"&&isBig())?140:60;let tot=out.reduce((a,t)=>a+wd(t),0);
  if(tot>cap){const drop=out.slice().sort((a,b)=>(NFREQ[b]||0)-(NFREQ[a]||0)||a.length-b.length);const gone=new Set();for(const t of drop){if(tot<=cap||out.length-gone.size<=3)break;gone.add(t);tot-=wd(t)}return out.filter(t=>!gone.has(t))}return out}'''
for i in range(a+1,b2): code[i]=''
s="\n".join(code)+"\n"
def rp(a,b,n=None):
    global s
    c=s.count(a)
    assert c>0 and (n is None or c==n),(a[:80],c)
    s=s.replace(a,b)
# headword underline: whole words only (case-insensitive), first match
a=s.index('const hlSyl=');b2=s.index('/* v2.28 RYU: underline')
s=s[:a]+'const hlBad=()=>false;\n'+s[b2:]
a=s.index('const hl=(text,w)=>');b2=s.index('\n',a)
s=s[:a]+r'''const hl=(text,w)=>{const e=esc(text);if(!w)return e;const k=esc(w.replace(/[…?!]/g,"").trim());if(!k)return e;const re=new RegExp("(^|[^A-Za-z'’])("+k.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+")(?![A-Za-z])","i");const m=re.exec(e);if(!m)return e;const i=m.index+m[1].length;return e.slice(0,i)+"<mark>"+m[2]+"</mark>"+e.slice(i+m[2].length)};'''+s[b2:]
rp('const laoWrap=t=>esc(t).replace(/([຀-໿][຀-໿\\s◌]*)/g,\'<span class="lo">$1</span>\');','const laoWrap=t=>esc(t);',1)
rp('</span><span class="hint">${hintHtml(hint)}</span></span><span class="bk"','</span><span class="rd frd">${esc(rd)}</span><span class="hint">${hintHtml(hint)}</span></span><span class="bk"',1)
rp('if(t.dataset.next){if(P.active)stopPlay();goto(t.dataset.next);','if(t.dataset.next){if(P.active)stopPlay();{const m=S.mode;goto(t.dataset.next);if(m!=="dlg"){S.mode=m;S.flipped={};save();render()}}',1)
a=s.index('function rep(t){');b2=s.index('function utterOf')
s=s[:a]+'function rep(t){return t}\n'+s[b2:]
rp('/^lo([-_]|$)/i','/^rw([-_]|$)/i',1); rp('"lo-LA"','"rw-RW"'); rp('Intl.Segmenter("lo"','Intl.Segmenter("rw"',1)
rp('(id==="2-04-10"||id==="2-04-11")&&SWATCH[lo]','SWATCH[lo]',1)
rp('라오스어','르완다어'); rp('LAO Lang','RWANDA Lang'); rp('lao-','rw-')
left=[l[:80] for l in s.split('\n')[1:] if re.search('[຀-໿]',l)]
print('code lines still holding Lao letters:',len(left));[print('  ',x) for x in left[:12]]
open(out+'/app.js','w',encoding='utf-8').write(s)
os.makedirs(out+'/../lists',exist_ok=True)
for n,o in (('f',LF),('m',LM),('k',LK)): json.dump(o,open(out+f'/../lists/{n}.json','w'),ensure_ascii=False)
# ---------- index.html
h=open(here+'/base/index.html',encoding='utf-8').read()
h,n=re.subn(r'@font-face\{font-family:"Lao Local";.*?\}','',h,count=1,flags=re.S);assert n==1
def hp(a,b):
    global h
    assert a in h,a
    h=h.replace(a,b)
hp('"Lao Local","Noto Sans Lao Looped","Phetsarath OT","Saysettha OT","Lao UI",','')
h=h.replace('"Lao Local",','')
hp('라오스어, 주제별로 공부하기','르완다어, 주제별로 공부하기')
hp('ຮຽນ ພາສາລາວ','Kinyarwanda')
hp('라오스어, 독음, 뜻으로 검색 (예: ໝາກ, 막, 과일)','르완다어, 독음, 뜻으로 검색 (예: amazi, 아마지, 물)')
h,n=re.subn(r'<span><b>[\d,]+</b>묶음</span><span><b>[\d,]+</b>단어</span><span><b>[\d,]+</b>문장</span>',f'<span><b>{len(B)}</b>묶음</span><span><b>{nw:,}</b>단어</span><span><b>{ns:,}</b>문장</span>',h);assert n==1
h,n=re.subn(r'\d{4}-\d\d-\d\d v[\d.]+ · Claude',f'{DATE} v{VER} · Claude',h);assert n>=1,'ver'
h,n=re.subn(r'app\.js\?v=[\d.]+"',f'app.js?v={VER}"',h);assert n>=1
h=h.replace('LAO Lang','RWANDA Lang').replace('lao-','rw-').replace('라오스어','르완다어').replace('lang="lo"','lang="rw"')
h=h.replace('</head>','<style>'+open(here+'/extra.css',encoding='utf-8').read()+'</style></head>',1)
assert not re.search('[຀-໿]',h),"Lao text left in html: "+re.search('.{40}[຀-໿].{40}',h).group()
open(out+'/index.html','w',encoding='utf-8').write(h)
sw=open(here+'/base/sw.js').read();sw=re.sub(r'lao-shell-v[\d.]+',f'rw-shell-v{VER}',sw).replace('lao-','rw-');open(out+'/sw.js','w').write(sw)
mf=json.load(open(here+'/base/manifest.webmanifest'));mf["name"]=mf["short_name"]="RWANDA Lang";json.dump(mf,open(out+'/manifest.webmanifest','w'),ensure_ascii=False)
for f in ('header.svg','header-day.svg','icon-180.png','icon-192.png','icon-512.png'):
    src=here+'/art/'+f if os.path.exists(here+'/art/'+f) else here+'/base/'+f
    if os.path.exists(src): shutil.copyfile(src,out+'/'+f)
for f in ('_gap450.mp3','_gap900.mp3'): shutil.copyfile(here+'/base/'+f,out+'/audio/'+f)
open(out+'/.nojekyll','w').write('')
print('built',len(B),'bundles',nw,'words',ns,'sentences; tokens without note meaning:',len(NOMEAN),'; voice2',len(LM),'voice1',len(LF),'korean',len(LK))
