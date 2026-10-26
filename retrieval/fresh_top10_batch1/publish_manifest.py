"""Check publication files and record their hashes without changing run records."""
import json
import re
from common import HERE, save, sha


def main():
    files = sorted(p for p in HERE.rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts
                   and p.name != 'artifact_manifest.json')
    assert not any(p.relative_to(HERE).parts[0] in {'cache', 'state'} for p in files)
    for p in files:
        if p.suffix.lower() not in {'.json', '.jsonl', '.txt', '.log', '.md', '.py', '.csv'}:
            continue
        raw = p.read_bytes()
        text = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
        assert not re.search(r'\bsk-[A-Za-z0-9_-]{20,}', text), f'Credential pattern: {p}'
        assert not re.search(r'(?i)bearer\s+[A-Za-z0-9._-]{20,}', text), f'Credential pattern: {p}'
        if p.suffix == '.md':
            assert not re.search(r'[\u4e00-\u9fff]', text), f'Non-English documentation: {p}'
            assert not re.search(r'(?i)\b(?:AI|LLM|GPT)\b', text), f'Documentation wording: {p}'
            for target in re.findall(r'\]\(([^)]+)\)', text):
                target = target.split('#', 1)[0]
                if target and not re.match(r'[a-z]+://', target):
                    linked = (p.parent / target).resolve()
                    assert linked == HERE/'artifact_manifest.json' or linked.exists(), f'Broken link: {p}: {target}'
    records = [dict(path=p.relative_to(HERE).as_posix(), bytes=p.stat().st_size, sha256=sha(p))
               for p in files]
    save(HERE/'artifact_manifest.json', dict(files=len(records),
         bytes=sum(r['bytes'] for r in records), artifacts=records))
    print(json.dumps(dict(files=len(records), bytes=sum(r['bytes'] for r in records))))


if __name__ == '__main__':
    main()
