# -*- coding: utf-8 -*-
"""diag2 R66: instrumented private mirror (workspace copy only; repo untouched).

build() creates mirr_head as a pristine mirror of the worktree core; this script
inserts local-variable prints into mirr_head's region_ast_generator.py so the
f-string reduction branch reports what it actually saw.  Then run any arm with
`--arm=head` against the instrumented mirror.
"""
import io
import sys

MIRR = sys.argv[1] if len(sys.argv) > 1 else 'mirr_head'
P = 'D:/Temp/opencode/r66gate/diag2/%s/core/cfg/region_ast_generator.py' % MIRR
src = io.open(P, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if src.count('\r') else '\n'
u = src.replace(nl, '\n')

DBG1 = """                print('[PDBG] fstring-branch vt=%r ctx=%r cond_val_start=%r skip=%r '
                      'condops=%r mergeops=%r parts=%r tail_ok=%r'
                      % (getattr(region, 'value_target', None), merge_ctx,
                         cond_val_start, _r65_callee_skip,
                         [i.opname for i in cond_block_instrs],
                         [i.opname for i in _mb_instrs],
                         [(p.get('type'), p.get('value') if p.get('type') == 'Constant'
                           else p.get('id', None)) for p in fstring_parts],
                         _r65_tail_ok), file=__import__('sys').stderr)
                joined_str = {
                    'type': 'JoinedStr',
                    'values': fstring_parts,
                }"""
ANCH1 = """                joined_str = {
                    'type': 'JoinedStr',
                    'values': fstring_parts,
                }"""
n = u.count(ANCH1)
assert n == 1, n
u = u.replace(ANCH1, DBG1)

io.open(P, 'w', encoding='utf-8' + ('-sig' if src.startswith('\ufeff') else ''),
        newline='').write(u.replace('\n', nl))
print('instrumented %s' % P)
