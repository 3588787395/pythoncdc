# -*- coding: utf-8 -*-
"""probe163_gate: 门控命中/拒绝实证（临时探针，不写入仓库）。

对目标函数建 CFG 后，monkeypatch RegionASTGenerator._v163_boolop_merge_is_iter_source，
逐次调用记录：调用点行号、merge 块偏移、去噪指令序列、门控返回（True=允许整块
BoolOp 作 iterable / False=拒绝并回落指令级拆分）。
"""
import sys, marshal, types, traceback
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

path, want = sys.argv[1], sys.argv[2]

def load(p):
    return marshal.loads(open(p, 'rb').read()[16:])

def walk(co, prefix=''):
    yield prefix + co.co_name, co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c, prefix + co.co_name + '.')

co = None
for name, c in walk(load(path)):
    if c.co_name == want:
        co = c
        break
assert co is not None, 'function %s not found in %s' % (want, path)
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg)

_orig = RegionASTGenerator._v163_boolop_merge_is_iter_source
_calls = []

def _wrap(self, merge_block):
    res = _orig(self, merge_block)
    caller = traceback.extract_stack(limit=3)[-2]
    _noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
    seq = ([(i.offset, i.opname, getattr(i, 'argval', None))
            for i in merge_block.instructions if i.opname not in _noise]
           if merge_block is not None else None)
    _calls.append((caller.lineno, getattr(merge_block, 'start_offset', None), res))
    print('  gate call @region_ast_generator.py:%s merge_block=%s' %
          (caller.lineno, getattr(merge_block, 'start_offset', None)))
    print('    instrs=%r' % (seq,))
    print('    -> %s (%s)' % ('ALLOW' if res else 'REJECT',
                              'BoolOp 可作 iterable' if res else '回落指令级拆分'))
    return res

RegionASTGenerator._v163_boolop_merge_is_iter_source = _wrap
try:
    gen.generate()
finally:
    RegionASTGenerator._v163_boolop_merge_is_iter_source = _orig

print('[probe163] total gate calls=%d, reject=%d' %
      (len(_calls), sum(1 for c in _calls if not c[2])))
