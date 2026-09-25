# -*- coding: utf-8 -*-
"""bisect arms: C2b = _stack_effect (38931) BUILD_CONST_KEY_MAP pop = arg+1."""
import io
import json

GEN = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
C1 = json.load(io.open('specs/cand_r67_bare_return_sink.json', encoding='utf-8'))
C2 = json.load(io.open('specs/cand_r67_bckm_stack_effect.json', encoding='utf-8'))

ANCHOR2B = (
    "        if op == 'BUILD_STRING':\n"
    "            return 1, instr.arg or 0\n"
    "        if op.startswith('BUILD_'):\n"
    "            return 1, instr.arg or 0\n"
)
NEW2B = C2['edits'][0]['repl'][len(C2['edits'][0]['anchor']):]

for nm, edits in (('cand_r67_c2b_only', [{'anchor': ANCHOR2B, 'repl': ANCHOR2B + NEW2B}]),
                  ('cand_r67_c1_c2b', C1['edits'] + [{'anchor': ANCHOR2B, 'repl': ANCHOR2B + NEW2B}]),
                  ('cand_r67_all3', C1['edits'] + C2['edits']
                   + [{'anchor': ANCHOR2B, 'repl': ANCHOR2B + NEW2B}])):
    sp = {"name": nm, "file": "core/cfg/region_ast_generator.py", "edits": edits,
          "note": "R67 diag3 bisect"}
    u = io.open(GEN, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
    for e in edits:
        assert u.count(e['anchor']) == 1, (nm, u.count(e['anchor']))
    io.open('specs/%s.json' % nm, 'w', encoding='utf-8').write(
        json.dumps(sp, ensure_ascii=False, indent=1))
    print('ok', nm, len(edits))
