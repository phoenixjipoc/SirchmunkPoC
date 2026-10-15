"""Offline preservation, English-view, link, and credential-pattern checks."""
import csv
import hashlib
import json
import os
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from build_english_reports import CAMPAIGN, HINTS, OUT, ROOT, TRANSLATIONS, read_csv, translated_value

PROSE_TERMS = re.compile(
    r'\b(?:AI|LLMs?|LLM_[A-Z_]+|models?|gpt(?:[- ][\w.-]+)?|embeddings?|'
    r'neural|chatgpt|claude|openai|anthropic)\b|artificial intelligence|machine learning|'
    r'human sign[- ]off|not production acceptance|(?:pending|awaiting) manual review',
    re.IGNORECASE,
)


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def jsonl(path):
    with path.open(encoding='utf-8-sig') as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    inventory=json.loads((ROOT/'provenance/source_inventory.json').read_text(encoding='utf-8'))
    assert inventory['schema_version']==2 and inventory['scope']=='verified120'
    assert len({item['path'] for item in inventory['files']})==len(inventory['files'])
    copied=0
    published_docs=[]
    for item in inventory['files']:
        path=ROOT/item['path']
        assert path.resolve().is_relative_to(ROOT)
        assert path.is_file(), f"Missing source artifact: {item['path']}"
        if path.suffix=='.md':
            assert digest(path)==item['publication_sha256'], f"English edition changed: {item['path']}"
            assert path.stat().st_size==item['publication_bytes']
            published_docs.append(item['path'])
        else:
            assert digest(path)==item['source_sha256'], f"Original evidence changed: {item['path']}"
            assert path.stat().st_size==item['bytes']
            copied+=1

    archive_path=CAMPAIGN.with_name(CAMPAIGN.name+'_export.zip')
    archive_manifest_path=archive_path.with_suffix('.manifest.json')
    assert {p.name for p in CAMPAIGN.parent.iterdir()}=={
        CAMPAIGN.name, archive_path.name, archive_manifest_path.name}
    assert not (ROOT/'provenance/original_documentation').exists()
    archive_meta=json.loads(archive_manifest_path.read_text(encoding='utf-8'))
    assert archive_meta['archive']==archive_path.name
    assert archive_meta['sha256']==digest(archive_path)
    assert archive_meta['bytes']==archive_path.stat().st_size
    assert archive_meta['narrative_language']=='English'
    expected_members={p.relative_to(CAMPAIGN.parent).as_posix():p
                      for p in CAMPAIGN.rglob('*') if p.is_file()}
    with zipfile.ZipFile(archive_path) as archive:
        assert len(archive.namelist())==len(expected_members)==archive_meta['files']==473
        assert set(archive.namelist())==set(expected_members)
        for name,path in expected_members.items():
            content=archive.read(name)
            assert hashlib.sha256(content).hexdigest()==digest(path), f"Stale ZIP member: {name}"
            if path.suffix=='.md':
                assert not re.search(r'[\u3400-\u9fff]',content.decode('utf-8')), f"Non-English ZIP narrative: {name}"
                assert not PROSE_TERMS.search(content.decode('utf-8')), f"Unwanted ZIP terminology: {name}"

    questions=read_csv(CAMPAIGN/'inputs/questions.csv')
    ids=[q['id'] for q in questions]
    assert len(ids)==len(set(ids))==120
    assert len({q['question'] for q in questions})==120
    manifest=json.loads((CAMPAIGN/'campaign.json').read_text(encoding='utf-8'))
    assert digest(CAMPAIGN/'inputs/questions.csv')==manifest['question_sha256']
    for relative,expected in manifest['scripts'].items():
        assert digest(ROOT/'poc'/relative)==expected, f"Recorded executable changed: {relative}"
    corpus=json.loads((CAMPAIGN/'inputs/source_inventory.json').read_text(encoding='utf-8'))
    assert len(corpus)==81
    assert {p.name for p in (ROOT/'poc_docs/S').iterdir() if p.is_file()}=={r['file'] for r in corpus}
    assert all(digest(ROOT/'poc_docs/S'/r['file'])==r['sha256'] for r in corpus)
    all_results=read_csv(CAMPAIGN/'all_results.csv')
    assert len(all_results)==360
    correct={}
    clusters={}
    work_paths=set()
    for stage in 'ABC':
        d=CAMPAIGN/stage
        search_input=jsonl(d/'questions.jsonl')
        assert [q['id'] for q in search_input]==ids
        assert all(set(q)=={'id','question'} for q in search_input)
        raw=jsonl(d/'results.jsonl')
        assert [r['id'] for r in raw]==ids
        final=[r for r in all_results if r['stage']==stage]
        assert [r['id'] for r in final]==ids
        assert all(r['answer']==f['answer'] and r['total_tokens']==int(f['total_tokens']) for r,f in zip(raw,final))
        correct[stage]=sum(r['final_label'] in ['correct','correct_refusal'] for r in final)
        clusters[stage]=len(read_csv(d/'clusters.csv'))
        meta=json.loads((d/'run_meta.json').read_text(encoding='utf-8'))
        assert meta['state']=='complete' and meta['model']=='gpt-5.4' and meta['mode']=='DEEP'
        work_paths.add(meta['work_path'])
    assert correct=={'A':74,'B':68,'C':75}
    assert clusters=={'A':82,'B':76,'C':80} and len(work_paths)==3
    queue=read_csv(CAMPAIGN/'review_queue.csv')
    assert len(queue)==190 and all(r['review_status']=='reviewed' for r in queue)
    cases=read_csv(CAMPAIGN/'reuse_cases.csv')
    assert len(cases)==9 and all(r['final_label']=='wrong' for r in cases)

    presentation_files=[]
    translation_records=[]
    for path in sorted(OUT.glob('*.csv')):
        if path.name in ['A_clusters.csv','B_clusters.csv','C_clusters.csv']:
            source=CAMPAIGN/path.name[0]/'clusters.csv'
        else:
            source=CAMPAIGN/path.name
        originals=read_csv(source)
        published=read_csv(path)
        assert len(originals)==len(published), f"Presentation row count: {path.name}"
        for old,new in zip(originals,published):
            assert set(new)==set(old)|{'publication_translation_note'}
            for field,value in old.items():
                assert new[field]==translated_value(field,value), f"Presentation changed a fact: {path.name}/{old.get('id')}/{field}"
                if new[field]!=value and field!='diagnostic_hint':
                    translation_records.append({'file':path.name,'id':old.get('id'),'field':field})
            assert not any(re.search(r'[\u3400-\u9fff]',v) for v in new.values()), f"Non-English presentation row: {path.name}/{old.get('id')}"
        presentation_files.append(path.name)
    assert len(presentation_files)==14

    active_docs=[]
    for current,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in ['.git','__pycache__','.venv','.pytest_cache']]
        active_docs.extend(Path(current)/name for name in files if name.endswith('.md'))
    checked_links=0
    for path in active_docs:
        content=path.read_text(encoding='utf-8')
        assert not re.search(r'[\u3400-\u9fff]',content), f"Non-English narrative: {path.relative_to(ROOT)}"
        assert not PROSE_TERMS.search(content), f"Unwanted narrative terminology: {path.relative_to(ROOT)}"
        for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',content):
            target=link.strip('<>').split('#',1)[0]
            if not target or re.match(r'[A-Za-z]+:',target):
                continue
            resolved=(path.parent/unquote(target)).resolve()
            assert resolved.is_relative_to(ROOT) and resolved.exists(), f"Broken local link: {path.relative_to(ROOT)} -> {target}"
            checked_links+=1

    patterns={
        'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'github_token':r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b',
        'api_key':r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b',
        'bearer_literal':r'(?i)authorization[\s\x22\x27:=]+Bearer\s+[A-Za-z0-9_./+\-=]{20,}',
        'embedded_url_credentials':r'https?://[^\s/:@]+:[^\s/@]+@',
    }
    findings=[]
    scanned=0
    large=[]
    for current,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in ['.git','__pycache__','.venv','.pytest_cache']]
        for name in files:
            path=Path(current)/name
            size=path.stat().st_size
            assert size<100*1024*1024, f"GitHub file limit exceeded: {path.relative_to(ROOT)}"
            if size>50*1024*1024:
                large.append({'path':path.relative_to(ROOT).as_posix(),'bytes':size})
            if path.suffix not in ['.py','.md','.txt','.csv','.json','.jsonl','.log']:
                continue
            content=path.read_text(encoding='utf-8-sig',errors='replace')
            for kind,pattern in patterns.items():
                if re.search(pattern,content):
                    findings.append({'path':path.relative_to(ROOT).as_posix(),'pattern':kind})
            scanned+=1
    assert not findings, f"Credential-like pattern locations (values withheld): {findings}"

    result={'validated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'passed':True,
        'scope':'verified120','retained_source_artifacts':len(inventory['files']),
        'unchanged_evidence_files':copied,'published_source_documents':published_docs,
        'english_markdown_documents':len(active_docs),
        'markdown_terminology_check':'passed',
        'campaign_archive_members_verified':len(expected_members),
        'campaign_archive_sha256':archive_meta['sha256'],
        'raw_corpus_files':81,'corpus_hashes_unchanged':True,'search_records':360,
        'correct_counts':correct,'clusters':clusters,'required_reviews_resolved':190,
        'reuse_hits':9,'correct_reuse_hits':0,'english_presentation_csvs':presentation_files,
        'answer_or_cluster_translation_locations':translation_records,'local_links_checked':checked_links,
        'credential_pattern_files_scanned':scanned,'credential_pattern_findings':[],
        'files_above_50_mib_but_below_100_mib':large,
        'model_calls':0,'note':'Publication preservation and consistency checks; not a new semantic evaluation or a guarantee that every credential format is detectable.'}
    (ROOT/'provenance/publication_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    main()
