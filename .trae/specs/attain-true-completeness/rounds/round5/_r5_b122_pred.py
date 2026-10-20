# -*- coding: utf-8 -*-
"""R5 B122：对 n1 各块直接调用 match 谓词（不跑 analyze）。

用法: python -X utf8 _r5_b122_pred.py <pyc> <out.txt> [func=n1]
"""
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

pyc, out_path = sys.argv[1], sys.argv[2]
func_name = sys.argv[3] if len(sys.argv) > 3 else 'n1'

out = open(out_path, 'w', encoding='utf-8')


def log(msg):
    out.write(msg + '\n')
    out.flush()


from core.pyc_loader_v2 import load_pyc_file_v2  # noqa: E402
from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

mod = load_pyc_file_v2(pyc)
code = mod.code.get()
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
target = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == func_name:
        target = c
        break
if target is None:
    log('function not found: %s' % func_name)
    sys.exit(1)

cfg = build_cfg(target)
an = RegionAnalyzer(cfg)

preds = [
    ('_has_match_op', lambda b: an._has_match_op(b)),
    ('_is_case_pattern_block', lambda b: an._is_case_pattern_block(b)),
    ('_is_match_subject_block', lambda b: an._is_match_subject_block(b)),
    ('_is_capture_guard_case_block', lambda b: an._is_capture_guard_case_block(b)),
    ('_is_simple_match_case_block', lambda b: an._is_simple_match_case_block(b)),
    ('_is_wildcard_match_block', lambda b: an._is_wildcard_match_block(b)),
    ('_is_none_match_block', lambda b: an._is_none_match_block(b)),
]

for b in cfg.get_blocks_in_order():
    inss = []
    for ins in b.instructions:
        inss.append('%s%s' % (ins.opname,
                              ('(%r)' % (ins.argval,)) if getattr(ins, 'argval', None) is not None else ''))
    log('[%s] %s' % (b.start_offset, '; '.join(inss)))
    log('    preds=%s' % sorted(getattr(p, 'start_offset', None) for p in b.predecessors))
    res = []
    for name, fn in preds:
        try:
            res.append('%s=%s' % (name, fn(b)))
        except Exception as e:
            res.append('%s=EXC(%r)' % (name, e))
    log('    ' + ' '.join(res))

out.close()
