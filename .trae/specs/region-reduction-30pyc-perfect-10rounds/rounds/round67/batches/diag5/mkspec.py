# -*- coding: utf-8 -*-
"""Build a spec json from a here-doc-ish pair: python -X utf8 mkspec.py <name> <file> <anchorfile> <replfile>"""
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
name = sys.argv[1]
rel = sys.argv[2]
anchor = io.open(sys.argv[3], encoding='utf-8').read()
repl = io.open(sys.argv[4], encoding='utf-8').read()
u = io.open(os.path.join(REPO, rel.replace('/', os.sep)), encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
c = u.count(anchor)
print('anchor count =', c, ' repl adds lines =', repl.count('\n') - anchor.count('\n'))
assert c == 1, 'anchor not unique'
os.makedirs('specs', exist_ok=True)
edits = [{'anchor': anchor, 'repl': repl}]
io.open('specs/%s.json' % name, 'w', encoding='utf-8').write(
    json.dumps({'name': name, 'file': rel, 'edits': edits}, ensure_ascii=False, indent=1))
print('wrote specs/%s.json' % name)
