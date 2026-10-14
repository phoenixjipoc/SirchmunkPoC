import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
AUDIT=Path(__file__).resolve().parent
SOURCES=ROOT/'poc_docs/S'
FRESH=AUDIT/'source_text'
OLD=ROOT/'poc/corpus/text_S'
def files(key=''):
    return sorted(p for p in SOURCES.iterdir() if key.lower() in p.name.lower())
def source(key):
    hits=files(key)
    if len(hits)!=1: raise ValueError((key,[p.name for p in hits]))
    return hits[0]
def pages(key):
    p=source(key)
    fresh=FRESH/(p.name+'.txt')
    if fresh.exists():
        t=fresh.read_text(encoding='utf-8-sig')
        chunks=re.split(r'\[PDF page (\d+)\]',t)
        if len(chunks)>1: return [(int(chunks[i]),chunks[i+1]) for i in range(1,len(chunks),2)]
        return [('document',t)]
    if p.suffix.lower()=='.pdf':
        import fitz
        with fitz.open(p) as doc: return [(i+1,pg.get_text()) for i,pg in enumerate(doc)]
    if p.suffix.lower()=='.docx':
        import zipfile, xml.etree.ElementTree as ET
        with zipfile.ZipFile(p) as z: root=ET.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        return [('document','\n'.join(''.join(x.itertext()) for x in root.findall('.//w:p',ns)))]
    prior=[x for x in OLD.iterdir() if x.name.startswith(p.stem)]
    if len(prior)!=1: raise ValueError((p.name,prior))
    return [('legacy extraction (not fresh)',prior[0].read_text(encoding='utf-8-sig'))]
def norm(t): return re.sub(r'\s+',' ',t).strip()
def ev(key,quote,section=None):
    hits=[(pg,t) for pg,t in pages(key) if norm(quote) in norm(t)]
    if not hits: raise ValueError(('quote absent',key,quote))
    return {'file':source(key).name,'page':section if section is not None else hits[0][0],'quote':quote}
def save(batch):
    out=AUDIT/'blind_answers_3.jsonl'
    qs={x['id']:x['question'] for x in map(json.loads,(ROOT/'poc/questions/verification/blind_3.jsonl').read_text(encoding='utf-8-sig').splitlines())}
    old=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines()] if out.exists() else []
    assert len(batch)==5
    assert not set(x['id'] for x in old)&set(x['id'] for x in batch)
    for x in batch:
        x['question']=qs[x['id']]
        assert x['blind_source_file'] and x['evidence']
    with out.open('a',encoding='utf-8',newline='\n') as f:
        for x in batch: f.write(json.dumps(x,ensure_ascii=False)+'\n')
    print('Saved',len(old)+len(batch),'blind records')
def rec(id,answer,keys,evidence,notes='',confidence='high'):
    return dict(id=id,blind_answer=answer,blind_source_file=';'.join(source(k).name for k in keys),evidence=evidence,confidence=confidence,notes=notes)
if __name__=='__main__':
    key,pattern=sys.argv[1:3]
    radius=int(sys.argv[3]) if len(sys.argv)>3 else 350
    for f in files('' if key=='ALL' else key):
        for pg,t in pages(f.name):
            t=norm(t)
            matches=list(re.finditer(pattern,t,re.I))
            if matches:
                print('\nFILE',f.name,'PAGE',pg)
                last=-1
                for m in matches:
                    a,b=max(0,m.start()-radius),min(len(t),m.end()+radius)
                    if b<=last: continue
                    print(t[max(a,last):b]);last=b
