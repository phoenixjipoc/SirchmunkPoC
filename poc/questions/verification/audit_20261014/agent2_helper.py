import sys,re,json,base64
sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
AUDIT=Path(__file__).parent
def source(pat):
    files=list((ROOT/'poc_docs/S').glob(pat+'*'))
    if len(files)!=1: raise ValueError([p.name for p in files])
    f=files[0]
    fresh=AUDIT/'source_text'/(f.name+'.txt')
    if fresh.exists(): return f.name,fresh.read_text(encoding='utf-8')
    return f.name,(ROOT/'poc/corpus/text_S'/(f.name+'.txt')).read_text(encoding='utf-8')
def append(rows):
    qs={r['id']:r['question'] for r in map(json.loads,(ROOT/'poc/questions/verification/blind_2.jsonl').read_text(encoding='utf-8-sig').splitlines())}
    out=AUDIT/'blind_answers_2.jsonl'
    old=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines()] if out.exists() else []
    assert len(rows)==5
    assert not set(r['id'] for r in rows)&set(r['id'] for r in old)
    for r in rows:
        r['question']=qs[r['id']]
    payload=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
    payload.encode('utf-8')
    with out.open('a',encoding='utf-8') as f:f.write(payload)
    print('Saved',len(old)+len(rows),'blind records')
if __name__=='__main__':
    if sys.argv[1]=='append':append(json.loads(sys.stdin.read()) if sys.argv[2]=='-' else json.loads(base64.b64decode(sys.argv[2])))
    elif sys.argv[1]=='page':
        import fitz
        p=list((ROOT/'poc_docs/S').glob(sys.argv[2]+'*'))[0]
        d=fitz.open(p)
        for n in map(int,sys.argv[3].split(',')):
            print('\n'+p.name+' [PDF page '+str(n)+']\n'+d[n-1].get_text())
    else:
        name,s=source(sys.argv[1]);lines=s.splitlines();ctx=int(sys.argv[3]) if len(sys.argv)>3 else 4
        hits=[i for i,l in enumerate(lines) if re.search(sys.argv[2],l,re.I)]
        shown=set();page='section'
        print(name)
        for i,l in enumerate(lines):
            if l.startswith('[PDF page'):page=l
            if any(abs(i-h)<=ctx for h in hits):
                print(str(i+1)+' '+page+' '+l)
