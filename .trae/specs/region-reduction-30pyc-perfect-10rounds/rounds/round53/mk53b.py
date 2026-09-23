# -*- coding: utf-8 -*-
"""Round 53: R53-B = R53-A + representability conjunct.

The escape hatch must only preserve operands the BoolOp build layer can turn into ONE
abstract node: its grouping walks consecutive equal labels, so a chain that carries a
second operator boundary (>= 3 runs, e.g. `(A and B) or (C and D)`) is not representable
at this level and must stay with the parent IfRegion (the original pop).

usage: python -X utf8 mk53b.py
"""
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

ANCHOR = """                    if not _normal_or and not _not_or_chain and (not _equivalent_exits or _is_scenario_b_ternary):
                        chain.pop()
                        break"""
assert SRC.count(ANCHOR) == 1

REPL = """                    # [R53-A/R53-B] Same-operator-run exit consistency. This test compares
                    # the tail operand's short-circuit target with chain[0]'s, but in
                    # `A or (B and C)` / `A and (B or C)` chain[0] belongs to a DIFFERENT
                    # operator run: CPython routes the first run's short-circuit into the
                    # next run's entry (for an 'or' head, straight into the body), while
                    # every operand of one run jumps to that run's own shared exit (B and
                    # C are both POP_JUMP_IF_FALSE -> exit). A cross-run comparison is
                    # therefore not evidence of a swallowed nested-if condition.
                    # Region-reduction principle 2 (a block has exactly one owner at this
                    # level) makes the discriminator the run the tail operand actually
                    # reduces against: if the head of the maximal same-operator run that
                    # holds `current` shares `current`'s exit target, `current` is a
                    # genuine operand of that run.
                    # [R53-B] ... but only while the preserved chain stays representable as
                    # ONE BoolOp node here: the build layer groups consecutive equal
                    # labels, so a second operator boundary (>= 3 runs, e.g.
                    # `(A and B) or (C and D)`) cannot be reduced at this level and its
                    # trailing operand goes back to the parent IfRegion (principle 3).
                    _r53_run_head = None
                    _r53_rh_i = len(chain) - 2
                    while _r53_rh_i >= 0 and chain[_r53_rh_i][1] == op_type:
                        _r53_run_head = chain[_r53_rh_i][0]
                        _r53_rh_i -= 1
                    _r53_run_head_jt = None
                    if _r53_run_head is not None:
                        _r53_rh_last = _r53_run_head.get_last_instruction()
                        if (_r53_rh_last is not None
                                and getattr(_r53_rh_last, 'argval', None) is not None):
                            _r53_run_head_jt = self.cfg.get_block_by_offset(_r53_rh_last.argval)
                    _r53_same_run_exit = (_r53_run_head_jt is not None
                                           and _r53_run_head_jt is cur_jump_target)
                    _r53_boundaries = sum(1 for _r53_k in range(1, len(chain))
                                          if chain[_r53_k][1] != chain[_r53_k - 1][1])
                    if (not _normal_or and not _not_or_chain
                            and (not _equivalent_exits or _is_scenario_b_ternary)
                            and not (_r53_same_run_exit and _r53_boundaries <= 1)):
                        chain.pop()
                        break"""

spec = {'file': 'core/cfg/region_analyzer.py', 'edits': [{'anchor': ANCHOR, 'repl': REPL}]}
out = os.path.join(ROOT, 'spec_r53b.json')
io.open(out, 'w', encoding='utf-8').write(json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote %s (+%d lines)' % (out, REPL.count(chr(10)) - ANCHOR.count(chr(10))))
