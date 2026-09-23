# -*- coding: utf-8 -*-
"""Round 53 diagnosis: build a print-instrumented mirror core for
_detect_boolop_conditional_chain so the operand-chain growth / pop / trim /
relabel decisions are observable for a synthetic witness and for the real
klinedata::_all_bars_of_cache site."""
import io
import json
import os
import sys

CR = chr(13)
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r53gate'
sys.stdout.reconfigure(encoding='utf-8')

SRC = io.open(os.path.join(REPO, 'core/cfg/region_analyzer.py'),
              encoding='utf-8-sig', newline='').read().replace(CR, '')


def anchor(txt):
    assert SRC.count(txt) == 1, 'anchor not unique (%d): %r' % (SRC.count(txt), txt[:60])
    return txt


A_CALL = anchor("""            chain = self._detect_boolop_conditional_chain(block, claimed, skip_claimed_check=_skip_claimed)
            if chain is None or len(chain) < 1:""")
A_APPEND = anchor("""                op_type = 'and' if 'FALSE' in last.opname else 'or'
            chain.append((current, op_type))""")
A_POP = anchor("""                    if not _normal_or and not _not_or_chain and (not _equivalent_exits or _is_scenario_b_ternary):
                        chain.pop()
                        break""")
A_TRIM = anchor("""                if len(_w14_kept) >= 2:
                    chain = _w14_kept
                else:
                    return None""")
A_UNI = anchor("""            if not _w14_all_true_jump:
                chain = [(_w14_blk, 'and') for _w14_blk, _ in chain]""")

edits = [
    {'anchor': A_APPEND, 'repl': A_APPEND + """
            print('[R53 append] start=%s cur=%s term=%s->%s op=%s chain=%s' % (
                start_block.start_offset, current.start_offset, last.opname, last.argval,
                op_type, [(b.start_offset, o) for b, o in chain]))"""},
    {'anchor': A_POP, 'repl': """                    if not _normal_or and not _not_or_chain and (not _equivalent_exits or _is_scenario_b_ternary):
                        print('[R53 POP] start=%s chain=%s op=%s prev=%s firstJT=%s curJT=%s eq=%s sbt=%s normOR=%s notOR=%s' % (
                            start_block.start_offset, [(b.start_offset, o) for b, o in chain],
                            op_type, prev_op,
                            None if first_jump_target is None else first_jump_target.start_offset,
                            None if cur_jump_target is None else cur_jump_target.start_offset,
                            _equivalent_exits, _is_scenario_b_ternary, _normal_or, _not_or_chain))
                        chain.pop()
                        break"""},
    {'anchor': A_TRIM, 'repl': A_TRIM[:A_TRIM.index('                if len')] + """                print('[R53 TRIM?] start=%s chain=%s t0=%s lastFT=%s kept=%s' % (
                    start_block.start_offset, [(b.start_offset, o) for b, o in chain],
                    None if _w14_t0 is None else _w14_t0.start_offset,
                    None if _w14_last_ft is None else _w14_last_ft.start_offset,
                    [(b.start_offset, o) for b, o in _w14_kept]))
""" + A_TRIM[A_TRIM.index('                if len'):]},
    {'anchor': A_UNI, 'repl': A_UNI + """
            print('[R53 UNIFORM->and] start=%s chain=%s' % (
                start_block.start_offset, [(b.start_offset, o) for b, o in chain]))"""},
    {'anchor': A_CALL, 'repl': A_CALL + """
            print('[R53 RESULT] start=%s -> %s' % (block.start_offset,
                None if chain is None else [(b.start_offset, o) for b, o in chain]))""",
     'note': 'printed after the detector returns, before the len check'},
]

# RESULT print must sit between the two anchor lines, not after the "if chain is None"
e = edits[4]
edits[4] = {'anchor': A_CALL, 'repl': """            chain = self._detect_boolop_conditional_chain(block, claimed, skip_claimed_check=_skip_claimed)
            print('[R53 RESULT] start=%s -> %s' % (block.start_offset,
                None if chain is None else [(b.start_offset, o) for b, o in chain]))
            if chain is None or len(chain) < 1:""", 'note': 'inline'}

spec = {'file': 'core/cfg/region_analyzer.py', 'edits': [
    {k: v for k, v in x.items() if k != 'note'} for x in edits]}
out = os.path.join(ROOT, 'spec_diag53.json')
io.open(out, 'w', encoding='utf-8').write(json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote', out, 'edits=%d' % len(edits))
for x in edits:
    assert x['anchor'] in x['repl'] or 'POP' in x['anchor'] or 'RESULT' in x['anchor'], x['anchor'][:40]
