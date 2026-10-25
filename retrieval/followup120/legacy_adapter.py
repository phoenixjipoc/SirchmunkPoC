"""Read the English Word97 corpus file from stdin using its actual piece table.

This corpus-specific adapter preserves field codes and flattens table cells.
It does not infer physical pages. Raw source files are never modified.
"""
import hashlib
import io
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'parser_dependencies'))
import olefile

EXPECTED_SOURCE='0bd0f06fa9a0452ab67831a06146385ccc0f950ffbbeab95c3cbfbed518e91d6'
# Audit artifact used Windows CRLF; compare the same text with LF line endings.
EXPECTED_TEXT='744665d0888cd47bd36bd00a37f531b5ce3ee924ff74e38ba97f83efb482bdf9'


def extract(raw):
    assert hashlib.sha256(raw).hexdigest()==EXPECTED_SOURCE, 'Unsupported source; this adapter is corpus-specific'
    with olefile.OleFileIO(io.BytesIO(raw)) as ole:
        word=ole.openstream('WordDocument').read()
        flags=struct.unpack_from('<H',word,10)[0]
        assert not flags & 0x100, 'Encrypted document unsupported'
        table=ole.openstream('1Table' if flags & 0x200 else '0Table').read()
        fc_clx,lcb_clx=struct.unpack_from('<II',word,0x1A2)
        clx=table[fc_clx:fc_clx+lcb_clx]
        cursor=0
        while clx[cursor]==1: cursor+=3+struct.unpack_from('<H',clx,cursor+1)[0]
        assert clx[cursor]==2
        length=struct.unpack_from('<I',clx,cursor+1)[0]
        plc=clx[cursor+5:cursor+5+length]
        assert len(plc)==length and (length-4)%12==0
        n=(length-4)//12
        cp=struct.unpack_from('<'+'I'*(n+1),plc)
        parts=[]
        for i in range(n):
            fc=struct.unpack_from('<I',plc,4*(n+1)+8*i+2)[0]
            compressed=bool(fc & 0x40000000)
            offset=fc & 0x3FFFFFFF
            count=cp[i+1]-cp[i]
            assert count>0
            if compressed:
                offset//=2
                part=word[offset:offset+count].decode('cp1252',errors='replace')
            else: part=word[offset:offset+2*count].decode('utf-16-le',errors='strict')
            parts.append(part)
        text=''.join(parts)
        assert len(text)==cp[-1]
        count=struct.unpack_from('<I',word,0x4C)[0]
        assert 0<count<=len(text)
        text=text[:count].replace('\r','\n').replace('\x07','\t')
    assert hashlib.sha256(text.encode()).hexdigest()==EXPECTED_TEXT, 'Parser differs from independently audited text'
    return text


if __name__=='__main__':
    sys.stdout.buffer.write(extract(sys.stdin.buffer.read()).encode('utf-8'))
