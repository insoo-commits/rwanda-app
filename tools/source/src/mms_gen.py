"""Kinyarwanda mp3 via Meta MMS (facebook/mms-tts-kin, local CPU). Usage: python3 mms_gen.py list.json outdir [male]
male: same voice, pitch lowered (no male Kinyarwanda voice exists). Output 16 kHz mono 16 kbps mp3 (RYU rule)."""
import json,os,sys,re,subprocess,time,torch,numpy as np
from transformers import VitsModel,AutoTokenizer
import scipy.io.wavfile as wf
M=os.environ.get('MMS_DIR','/home/user/mms')
torch.set_num_threads(int(os.environ.get('MMS_THREADS','4')))
tok=AutoTokenizer.from_pretrained(M);model=VitsModel.from_pretrained(M).eval()
src,out=sys.argv[1],sys.argv[2];male=len(sys.argv)>3 and sys.argv[3]=='male'
os.makedirs(out,exist_ok=True);L=json.load(open(src))
todo=[(k,t) for k,t in L.items() if not os.path.exists(f'{out}/{k}.mp3')]
print('todo',len(todo),flush=True);t0=time.time()
def norm(t):
    t=t.lower().replace('’',"'").replace('—',',').replace('…',',')
    t=re.sub(r"[^a-z0-9' ,.?!\-]",' ',t)
    return re.sub(r'\s+',' ',t).strip()
for n,(k,t) in enumerate(todo):
    torch.manual_seed(0)
    x=norm(t)
    # sentence-final pause: split at punctuation, synth pieces, join with short gaps
    parts=[p.strip() for p in re.split(r'[,.?!]',x) if p.strip()] or [x]
    wav=[]
    for p in parts:
        ids=tok(p,return_tensors='pt')
        with torch.no_grad(): w=model(**ids).waveform[0].numpy()
        wav.append(w);wav.append(np.zeros(int(16000*0.18),dtype=np.float32))
    w=np.concatenate(wav[:-1]);w=w/max(1e-6,np.abs(w).max())*0.9
    tmp=f'{out}/{k}.wav';wf.write(tmp,16000,(w*32767).astype(np.int16))
    af=['-af','asetrate=16000*0.84,aresample=16000,atempo=1.19'] if male else []
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i',tmp,*af,'-ar','16000','-ac','1','-b:a','16k','-f','mp3',f'{out}/{k}.p'],check=True)
    os.remove(tmp);os.replace(f'{out}/{k}.p',f'{out}/{k}.mp3')
    if n%200==0: print(n,'done',int(time.time()-t0),'s',flush=True)
print('time',int(time.time()-t0))
