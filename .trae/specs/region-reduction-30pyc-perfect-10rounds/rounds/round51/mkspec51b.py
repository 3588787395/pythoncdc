# -*- coding: utf-8 -*-
"""Derive the landing spec from the measured candidate builder (single source of truth).

Reads ANCHOR / BODY_A / BODY_B out of mk_cand51b.py with ast (no text duplication)
and writes spec_r51ab.json in the build2/r43g `anchor`+`repl` form (LF-normalised).

usage: python -X utf8 mkspec51b.py
"""
import ast
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:/Temp/r51b/mk_cand51b.py'
tree = ast.parse(io.open(SRC, encoding='utf-8').read())
vals = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in ('ANCHOR', 'BODY_A', 'BODY_B'):
                vals[t.id] = ast.literal_eval(node.value)
assert set(vals) == {'ANCHOR', 'BODY_A', 'BODY_B'}, sorted(vals)
repl = vals['BODY_A'] + vals['BODY_B'] + vals['ANCHOR']
assert repl.count('\r') == 0 and vals['ANCHOR'].count('\r') == 0, 'CR leaked into spec text'
assert repl.endswith(vals['ANCHOR'])
spec = {'file': 'core/cfg/region_ast_generator.py',
        'anchor': vals['ANCHOR'],
        'repl': repl,
        'inserted_lines': repl.count('\n') - vals['ANCHOR'].count('\n'),
        'note': 'R51-A (empty elif_final_else arm -> else: pass) + R51-B (unclaimed '
                'noise-only pad block whose sole successor is the chain merge and whose '
                'false edge comes from a chain test -> else: pass), both at the chain '
                'orelse anchor in _if_generate_elif_chain'}
io.open(r'D:/Temp/r51b/spec_r51ab.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('spec written: anchor %d chars, repl %d chars, +%d lines' % (
    len(vals['ANCHOR']), len(repl), spec['inserted_lines']))
