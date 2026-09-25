# -*- coding: utf-8 -*-
"""Build specs/cand_r67_orchain_tail.json from anchor/repl text files (LF-normalised).

usage: python -X utf8 mk_cand.py <name> <anchorfile> <replfile> [more anchor/repl pairs]
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'D:/Temp/opencode/r67gate/diag2'
TARGET = os.environ.get('CAND_FILE', 'core/cfg/region_analyzer.py')

args = sys.argv[1:]
name = args[0]
pairs = args[1:]
edits = []
for i in range(0, len(pairs), 2):
    a = io.open(os.path.join(ROOT, pairs[i]), encoding='utf-8').read()
    r = io.open(os.path.join(ROOT, pairs[i + 1]), encoding='utf-8').read()
    src = io.open(os.path.join('F:/Downloads/pythoncdc-main', TARGET.replace('/', os.sep)),
                  encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
    n = src.count(a)
    print('%s: anchor occurrences in landed bytes = %d' % (pairs[i], n))
    assert n == 1, 'anchor not unique'
    edits.append({'anchor': a, 'repl': r})

spec = {'file': TARGET, 'edits': edits}
out = os.path.join(ROOT, 'specs', 'cand_r67_%s.json' % name)
io.open(out, 'w', encoding='utf-8').write(json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote', out, 'edits=%d' % len(edits))
