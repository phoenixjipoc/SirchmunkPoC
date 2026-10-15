"""Rebuild the recorded campaign ZIP with English narratives and unchanged evidence."""
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / 'poc/results/20261014_ABC_verified120'
ARCHIVE = CAMPAIGN.with_name(CAMPAIGN.name + '_export.zip')
MANIFEST = ARCHIVE.with_suffix('.manifest.json')


def main():
    files = sorted(p for p in CAMPAIGN.rglob('*') if p.is_file())
    assert len(files) == 473, 'Unexpected recorded-campaign file count'
    narratives = [p for p in files if p.suffix == '.md']
    assert len(narratives) == 3
    for path in narratives:
        assert not re.search(r'[\u3400-\u9fff]', path.read_text(encoding='utf-8'))
    temporary = ARCHIVE.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files:
                member = zipfile.ZipInfo(path.relative_to(CAMPAIGN.parent).as_posix(),
                                         date_time=(1980, 1, 1, 0, 0, 0))
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                archive.writestr(member, path.read_bytes(),
                                 compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None, 'Archive CRC validation failed'
        temporary.replace(ARCHIVE)
    finally:
        temporary.unlink(missing_ok=True)
    record = {
        'created': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'archive': ARCHIVE.name,
        'files': len(files),
        'bytes': ARCHIVE.stat().st_size,
        'sha256': hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        'zip_integrity_passed': True,
        'narrative_language': 'English',
        'english_narratives': [p.relative_to(CAMPAIGN).as_posix() for p in narratives],
        'contents': 'Complete verified 120-question campaign: current English narratives, unchanged raw outputs, logs, clusters, and frozen inputs/scripts. Corpus, full question audit, and English presentation tables are separate repository directories.',
        'raw_evidence_policy': 'Original multilingual model and library outputs are preserved byte-for-byte.',
        'rebuild_command': 'python tools/export_campaign.py',
    }
    MANIFEST.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
