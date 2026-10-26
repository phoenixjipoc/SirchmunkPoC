"""Shared file and permutation helpers; no remote calls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)

def ordered_ids(value, expected):
    if not isinstance(value, dict) or set(value) != {'ordered_ids'}:
        raise ValueError('Expected only ordered_ids')
    ids = value['ordered_ids']
    if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids):
        raise ValueError('Expected a list of string identifiers')
    if len(ids) != len(expected) or len(set(ids)) != len(ids) or set(ids) != set(expected):
        raise ValueError('Identifiers must form an exact permutation')
    return ids

def apply_order(original, ordered, limit):
    prefix = original[:limit]
    if len(ordered) != len(prefix) or set(ordered) != set(prefix):
        raise ValueError('Candidate membership changed')
    return list(ordered) + original[limit:]
