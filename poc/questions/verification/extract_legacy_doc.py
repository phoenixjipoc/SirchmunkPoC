"""Read the audit's single legacy Word document using its actual text piece table.

Not a Word renderer. Retains field codes and table cell separators; cite sections,
not inferred page numbers. Handles this English Word97-format corpus file only.
Format reference: https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/1caae71f-35c4-49d7-adf0-af5fc766331c
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE / "audit_20261014"
sys.path.insert(0, str(AUDIT / "deps"))
import olefile

name = "INREV__INREV_DDQ_Fund_of_Funds_and_Multi-Managers.doc"
path = HERE.parents[2] / "poc_docs" / "S" / name
with olefile.OleFileIO(path) as ole:
    word = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", word, 10)[0]
    assert not flags & 0x100, "Encrypted document is unsupported"
    table = ole.openstream("1Table" if flags & 0x200 else "0Table").read()
    fc_clx, lcb_clx = struct.unpack_from("<II", word, 0x1A2)
    clx = table[fc_clx:fc_clx + lcb_clx]
    cursor = 0
    while clx[cursor] == 1:
        cursor += 3 + struct.unpack_from("<H", clx, cursor + 1)[0]
    assert clx[cursor] == 2
    length = struct.unpack_from("<I", clx, cursor + 1)[0]
    plc = clx[cursor + 5:cursor + 5 + length]
    assert len(plc) == length and (length - 4) % 12 == 0
    n = (length - 4) // 12
    cp = struct.unpack_from("<" + "I" * (n + 1), plc)
    parts = []
    for i in range(n):
        fc = struct.unpack_from("<I", plc, 4 * (n + 1) + 8 * i + 2)[0]
        compressed = bool(fc & 0x40000000)
        offset = fc & 0x3FFFFFFF
        chars = cp[i + 1] - cp[i]
        assert chars > 0
        if compressed:
            offset //= 2
            part = word[offset:offset + chars].decode("cp1252", errors="replace")
        else:
            part = word[offset:offset + 2 * chars].decode("utf-16-le", errors="strict")
        parts.append(part)
    text = "".join(parts)
    assert len(text) == cp[-1], "Text piece character count mismatch"
    ccp_text = struct.unpack_from("<I", word, 0x4C)[0]
    assert 0 < ccp_text <= len(text)
    text = text[:ccp_text].replace("\r", "\n").replace("\x07", "\t")
out = AUDIT / "source_text" / (name + ".txt")
out.write_text(text, encoding="utf-8")
meta = {"file": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "method": "OLE Word97 PlcPcd extraction from original; field codes retained",
        "piece_count": n, "main_text_characters": ccp_text, "chars": len(text),
        "text_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "limitations": "No rendered pagination; use section numbers. Table cells flattened."}
(AUDIT / "legacy_doc_extraction.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
inventory_path = AUDIT / "source_inventory.json"
inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
inventory = [meta if item['file'] == name else item for item in inventory]
inventory_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
print(json.dumps(meta, indent=2))
