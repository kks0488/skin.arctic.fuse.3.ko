#!/usr/bin/env python3
"""Validate and package only distributable skin files (no runtime userdata)."""
from pathlib import Path
import ast, hashlib, json, re, zipfile, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
def catalog(path):
    entries = {}
    for block in path.read_text().split('\n\n'):
        ctx = re.search(r'^msgctxt "(#\d+)"$', block, re.M)
        if not ctx: continue
        fields = {}
        key = None
        for line in block.splitlines():
            match = re.match(r'^(msgid|msgstr) (".*")$', line)
            if match:
                key = match[1]; fields[key] = ast.literal_eval(match[2])
            elif line.startswith('"') and key:
                fields[key] += ast.literal_eval(line)
        assert ctx[1] not in entries, ctx[1]
        entries[ctx[1]] = fields
    return entries

def main():
    metadata = ET.parse(ROOT/'addon.xml').getroot()
    addonid, version = metadata.get('id'), metadata.get('version')
    en = catalog(ROOT/'language/resource.language.en_gb/strings.po')
    ko = catalog(ROOT/'language/resource.language.ko_kr/strings.po')
    assert en.keys() == ko.keys()
    for key in en:
        assert ko[key]['msgid'] == en[key]['msgid'] and ko[key]['msgstr'], key
        tokens = lambda s: sorted(re.findall(r'\$[A-Z]+(?:\[[^\]]+\])?|\{[^}]+\}|%[sd]', s))
        assert tokens(en[key]['msgid']) == tokens(ko[key]['msgstr']), key
    files = [ROOT/n for n in ('addon.xml','LICENSE.txt','Readme.md','HOME-KO.md','icon.png','fanart.jpg')]
    for folder in ('1080i','colors','extras','fonts','language','media','shortcuts'):
        files += [f for f in (ROOT/folder).rglob('*') if f.is_file()]
    for f in files:
        if f.suffix == '.xml': ET.parse(f)
        if f.suffix == '.json': json.loads(f.read_text())
        if f.suffix in ('.xml','.json','.xmltemplate'):
            assert not re.search(r'skin\.arctic\.fuse\.3(?!\.ko)', f.read_text()), str(f)
    out = ROOT/'dist'/f'{addonid}-{version}.zip';out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(files): z.write(f,str(Path(addonid)/f.relative_to(ROOT)))
    with zipfile.ZipFile(out) as z: assert z.testzip() is None
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix('.zip.sha256').write_text(f'{digest}  {out.name}\n')
    print(f'{len(ko)} translated strings; {len(files)} packaged files; SHA256 {digest}')
    print(out)
if __name__ == '__main__': main()
