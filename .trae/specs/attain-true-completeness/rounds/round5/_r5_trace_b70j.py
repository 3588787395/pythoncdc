#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnose _r5_b70j_loopless_while_break preconditions on b70a wbc_nested."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator, FORWARD_CONDITIONAL_JUMP_OPS, IfRegion

data = open(os.path.join(ROOT, 'test_repros/round5/rec1_synth_b70a_wt_with_bc.pyc'), 'rb').read()
code = marshal.loads(data[16:])
f = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == 'wbc_nested'][0]
cfg = build_cfg(f)
ra = RegionAnalyzer(cfg)
rs = ra.analyze()
g = RegionASTGenerator(cfg, ra)
g.regions = list(rs)
w = [r for r in rs if type(r).__name__ == 'WithRegion'][0]
print('W blocks', [b.start_offset for b in w.blocks])
for r in g.regions:
    if isinstance(r, IfRegion):
        print('IF entry', r.entry.start_offset, 'inW', r.entry in w.blocks,
              'merge', getattr(r.merge_block, 'start_offset', None),
              'mergeInW', r.merge_block in w.blocks if r.merge_block else None,
              'then', [b.start_offset for b in r.then_blocks],
              'else', [b.start_offset for b in r.else_blocks])
        c = r.condition_block
        li = c.get_last_instruction() if c else None
        print('  cond', c.start_offset if c else None, li.opname if li else None,
              li.argval if li else None, 'in FORWARD', bool(li and li.opname in FORWARD_CONDITIONAL_JUMP_OPS))
        if li and li.argval is not None:
            T = r.merge_block
            false = cfg.get_block_by_offset(li.argval)
            true = None
            for s in c.successors:
                if s.instructions and s.instructions[0].opname == 'PUSH_EXC_INFO':
                    continue
                if s is not false:
                    true = s
                    break
            print('  true', true.start_offset if true else None, 'false', false.start_offset)

            def noise(b):
                return not any(i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL') for i in b.instructions)

            def cleanup(b):
                return ra._is_with_exit_cleanup(b)

            def walk(start, want):
                cur = start
                seen = set()
                for step in range(12):
                    if cur is None or cur in seen or cur not in w.blocks:
                        print('   walk stop', getattr(cur, 'start_offset', None), 'seen', cur in seen, 'inW', cur in w.blocks if cur else None)
                        return None
                    seen.add(cur)
                    tag = 'noise' if noise(cur) else ('cleanup' if cleanup(cur) else 'real')
                    print('   walk', step, cur.start_offset, tag)
                    if noise(cur):
                        nxt = [s for s in cur.successors
                               if not (s.instructions and s.instructions[0].opname == 'PUSH_EXC_INFO')]
                        if len(nxt) != 1:
                            print('    noise succ != 1', len(nxt))
                            return None
                        if nxt[0] is T:
                            return 'fall' if want == 'fall' else None
                        cur = nxt[0]
                        continue
                    if not cleanup(cur):
                        return None
                    lj = cur.get_last_instruction()
                    if lj is not None and lj.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') and lj.argval is not None:
                        tgt = cfg.get_block_by_offset(lj.argval)
                        print('    jump ->', tgt.start_offset, 'T?', tgt is T)
                        if tgt is T:
                            return 'jump' if want == 'jump' else None
                        cur = tgt
                        continue
                    nxt = [s for s in cur.successors
                           if not (s.instructions and s.instructions[0].opname == 'PUSH_EXC_INFO')]
                    if len(nxt) != 1:
                        return None
                    cur = nxt[0]
                return None

            print('  truewalk', walk(true, 'jump'))
            print('  falsewalk', walk(false, 'fall'))
            print('  arms noise/cleanup:',
                  [(b.start_offset, 'noise' if noise(b) else ('cleanup' if cleanup(b) else 'real'))
                   for b in list(r.then_blocks) + list(r.else_blocks)])
print('current_loop', g._current_loop)
wa = {'type': 'With', 'items': [],
      'body': [{'type': 'If', 'test': {'type': 'Name', 'id': 'a'},
                'body': [{'type': 'Pass'}], 'orelse': None}]}
print('result', g._r5_b70j_loopless_while_break(w, wa, [], []))
