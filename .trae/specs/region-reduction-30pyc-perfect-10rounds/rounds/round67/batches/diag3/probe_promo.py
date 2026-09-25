# -*- coding: utf-8 -*-
"""r67-diag3 read-only probe: why does _apply_r23n6_return_promotion not fire?

Wraps the landed generator method + the ternary-demotion decision and logs the
early-return reason for every call while decompiling a chosen pyc/function.
Nothing in the repo is modified.
"""
import io
import json
import os
import sys

sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag3')
import h62  # noqa: E402

pycdc = h62._load_arm('landed')
import core.cfg.region_ast_generator as G  # noqa: E402

CLS = None
for nm, obj in list(vars(G).items()):
    if isinstance(obj, type) and hasattr(obj, '_apply_r23n6_return_promotion'):
        CLS = obj
        break
assert CLS is not None, 'generator class not found'
print('generator class =', CLS.__name__)

TARGET = sys.argv[1] if len(sys.argv) > 1 else 't1'
LOG = []
_orig = CLS._apply_r23n6_return_promotion
NOISE = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')


def wrapped(self, block, stmts, block_role):
    try:
        last = stmts[-1] if stmts else None
        nn = [i for i in block.instructions if i.opname not in NOISE]
        k = len(nn) - 1
        while k >= 0 and nn[k].opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                                          'JUMP_BACKWARD_NO_INTERRUPT', 'EXTENDED_ARG'):
            k -= 1
        tail = nn[k].opname if k >= 0 else 'EMPTY'
        rec = {'blk': getattr(block, 'start_offset', None), 'role': str(block_role),
               'try_depth': self._try_depth, 'nstmt': len(stmts),
               'last_type': last.get('type') if isinstance(last, dict) else None,
               'last_vtype': (last.get('value') or {}).get('type') if isinstance(last, dict) else None,
               'tail_after_jumps': tail,
               'ninstr': len(nn),
               'chain': None}
        try:
            ch = self._find_return_chain_via_successors(block)
            rec['chain'] = [getattr(b, 'start_offset', b) for b in (ch or [])]
        except Exception as e:
            rec['chain'] = 'ERR %s' % e
        _orig(self, block, stmts, block_role)
        rec['after_type'] = stmts[-1].get('type') if stmts and isinstance(stmts[-1], dict) else None
        LOG.append(rec)
    except Exception as e:
        LOG.append({'probe_error': repr(e)})
    return None


CLS._apply_r23n6_return_promotion = wrapped

out = pycdc.decompile_pyc(TARGET)
io.open('scratch_probe_out.py', 'w', encoding='utf-8').write(out)
print('--- calls touching %s ---' % TARGET)
for r in LOG:
    print(json.dumps(r, ensure_ascii=False))
