"""Kinyarwanda -> Korean reading (한글 독음). Kinyarwanda spelling is regular, so the reading is rule-based.
Rules: a e i o u = 아 에 이 오 우; c/cy = ㅊ, j/jy = ㅈ, sh/shy = ㅅ+y (샤 시 셰 쇼 슈), ny = 냐 녜 니 뇨 뉴,
ts = ㅊ, pf = ㅍ, k = ㅋ, t = ㅌ, p = ㅍ, r = ㄹ, l = ㄹ (ㄹㄹ between vowels: Kigali 키갈리), v = ㅂ, z = ㅈ;
consonant + w = one syllable (bwa 봐, kwa 콰, mwa 뫄), but rw = 르 + 와 (Rwanda 르완다);
consonant + y = 야 계열 (bya 뱌, rya 랴); n/m before a consonant = 받침 (inka 잉카, inzu 인주, imbwa 임봐), or 은/음/응 at the start (ndi 은디);
an apostrophe joins words (n'umwana 누뫄나)."""
import re
CH={'b':7,'c':14,'d':3,'f':17,'g':0,'h':18,'j':12,'k':15,'l':5,'m':6,'n':2,'p':17,'r':5,'s':9,'t':16,'v':7,'z':12,'':11}
V={'a':0,'e':5,'i':20,'o':8,'u':13}
VY={'a':2,'e':7,'i':20,'o':12,'u':17}
VW={'a':9,'e':15,'i':16,'o':14,'u':13}
FIN={'n':4,'l':8,'m':16,'ng':21}
ONS=['shy','sh','cy','jy','ny','pf','ts','b','c','d','f','g','h','j','k','l','m','n','p','r','s','t','v','z']
PAL={'shy','sh','cy','jy','ny'}
def syl(i,v,f=0): return [i,v,f]
def word(w):
    w=w.lower().replace("’","'").replace("'","").replace('-','')
    w=re.sub(r'[^a-z]','',w)
    S=[];i=0;n=len(w)
    def coda(c):
        k={'b':'m','p':'m','f':'m','v':'m','k':'ng','g':'ng'}.get(c,'n')
        if S and S[-1][2]==0: S[-1][2]=FIN[k]
        else: S.append(syl(11,{'n':18,'m':18,'ng':18}[k],FIN[k]))   # 은/음/응
    while i<n:
        ch=w[i]
        # nasal before a consonant (not ny, not a vowel, not y/w glide on the nasal itself)
        if ch in 'nm' and i+1<n and w[i+1] not in 'aeiouyw' and not (ch=='n' and w[i+1]=='y'):
            # nn / mm: first one is the coda
            coda(w[i+1] if w[i+1] not in 'nm' else ch); i+=1; continue
        if ch in 'aeiou':
            S.append(syl(11,V[ch]));i+=1;continue
        if ch in 'yw':
            if i+1<n and w[i+1] in 'aeiou':
                S.append(syl(11,(VY if ch=='y' else VW)[w[i+1]]));i+=2;continue
            i+=1;continue
        on=next((o for o in ONS if w.startswith(o,i)),None)
        if on is None: i+=1;continue
        j=i+len(on);gy=on in PAL;gw=False
        if j<n and w[j]=='y': gy=True;j+=1
        if j<n and w[j]=='w': gw=True;j+=1
        if j<n and w[j]=='y': gy=True;j+=1
        if j>=n or w[j] not in 'aeiou':
            # consonant with no vowel (loan words, abbreviations): 으
            S.append(syl(CH.get(on[0],11),18));i=j;continue
        v=w[j]
        if on=='l' and S and S[-1][2]==0 and i>0 and w[i-1] in 'aeiou': S[-1][2]=8
        if gw and on=='r':
            S.append(syl(5,18));S.append(syl(11,VW[v]))
        elif gw: S.append(syl(CH[on[0]] if on not in ('ts','pf') else CH['c' if on=='ts' else 'p'],VW[v]))
        elif gy: S.append(syl(CH[{'shy':'s','sh':'s','cy':'c','jy':'j','ny':'n'}.get(on,on[0])] if on not in('ts','pf') else CH['c' if on=='ts' else 'p'],VY[v]))
        else: S.append(syl(CH['c'] if on=='ts' else CH['p'] if on=='pf' else CH[on[0]],V[v]))
        i=j+1
    return ''.join(chr(0xAC00+(a*21+b)*28+c) for a,b,c in S)
def reading(t):
    """a whole phrase/sentence: words keep their spaces, punctuation stays"""
    out=[]
    for tk in re.findall(r"[A-Za-zÀ-ÿ'’\-]+|\d[\d.,:]*|[?!.,…—–:;]",t.replace("…"," … ")):
        if re.match(r"[A-Za-zÀ-ÿ]",tk) or "'" in tk:
            out.append(word(tk))
        elif tk in '?!.,:;':
            if out: out[-1]+=tk
        else: out.append(tk)
    return re.sub(r'\s+',' ',' '.join(out)).strip()
if __name__=='__main__':
    for x in "Muraho Mwaramutse Murakoze cyane Rwanda Kinyarwanda Kigali umwana inka inzu imbwa ndashaka n'umwana amazi shyira icyayi ejo Ni byiza nyabuneka amafaranga isomo umwarimu abanyeshuri mbese ntabwo ingagi Nyamirambo inkweto".split():
        print(x,word(x))
    print(reading("Murakoze cyane, mwarimu!"))
