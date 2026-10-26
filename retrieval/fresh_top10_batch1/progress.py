"""Compact host-side progress from saved execution logs."""
import json
from common import HERE

def main():
    latest={}
    if (HERE/'runs/Baseline/queries/INV-01.json').exists():
        latest['Baseline','INV-01']=dict(group='Baseline',id='INV-01',status='ok',index=1)
    for p in sorted((HERE/'execution_logs').glob('*.log'),key=lambda p:p.stat().st_mtime):
        for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
            if line.startswith('{"group":'):
                r=json.loads(line); latest[r['group'],r['id']]=r
    summary={g:dict(completed=sum(k[0]==g for k in latest),last=next((r for k,r in reversed(list(latest.items())) if k[0]==g),None)) for g in ['Baseline','RR10']}
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
