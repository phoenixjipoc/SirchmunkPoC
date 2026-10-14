import argparse, pathlib, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(__file__).parent
p=argparse.ArgumentParser()
p.add_argument('glob');p.add_argument('pattern');p.add_argument('--context',type=int,default=4);p.add_argument('--all',action='store_true');p.add_argument('--page')
a=p.parse_args()
for f in sorted((ROOT/'source_text').glob(a.glob)):
    lines=f.read_text(encoding='utf-8-sig').splitlines()
    pages=[];page='section'
    for line in lines:
        m=re.search(r'\[PDF page (\d+)\]',line)
        if m:page=m.group(1)
        pages.append(page)
    hits=[i for i,l in enumerate(lines) if re.search(a.pattern,l,re.I)]
    if a.page: hits=[i for i,pg in enumerate(pages) if pg==a.page]
    if not hits:continue
    print('\nFILE',f.name)
    shown=set()
    for i in hits:
        for j in range(max(0,i-a.context),min(len(lines),i+a.context+1)):
            if j not in shown:
                print(f'p{pages[j]} L{j+1}: {lines[j][:800]}');shown.add(j)
