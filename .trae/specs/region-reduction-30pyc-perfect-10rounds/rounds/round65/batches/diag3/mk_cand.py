# -*- coding: utf-8 -*-
"""Build a candidate spec by splicing an anchor out of the LANDED generator bytes and
pairing it with a replacement block, asserting the anchor occurs exactly once.

usage: python -X utf8 -B mk_cand.py <name> <startline> <endline> <replfile>
Writes specs/cand_<name>.json
"""
import io
import json
import sys

SRC = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'

name = sys.argv[1]
a, b = int(sys.argv[2]), int(sys.argv[3])
repl_file = sys.argv[4]

raw = io.open(SRC, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
lines = raw.split('\n')
anchor = '\n'.join(lines[a - 1:b])
repl = io.open(repl_file, encoding='utf-8').read().rstrip('\n')

n = raw.count(anchor)
print('anchor = lines %d..%d  occurrences=%d  (len %d)' % (a, b, n, len(anchor)))
assert n == 1, 'anchor not unique'
out = r'D:/Temp/opencode/r65gate/diag3/specs/cand_%s.json' % name
io.open(out, 'w', encoding='utf-8', newline='').write(
    json.dumps({'file': 'core/cfg/region_ast_generator.py',
                'edits': [{'anchor': anchor, 'repl': repl}]}, ensure_ascii=False))
print('wrote %s  delta_lines=%d' % (out, repl.count('\n') - anchor.count('\n')))
