# -*- coding: utf-8 -*-
"""FIX-A 判定性实验 2：finally 副本同构性验证。

对比 TryExceptRegion children 中各 TernaryRegion 的逐块剥噪 opname 序列：
- T@4（try 体语句）vs T@100（exception 副本）→ 预期不同构
- T@86（normal 副本）vs T@100（exception 副本）→ 预期同构
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..')))

from core.pyc_loader_v2 import load_pyc_file_v2  # noqa: E402

NOISE = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'}
EXC = {'PUSH_EXC_INFO', 'RERAISE', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH',
       'CHECK_EG_MATCH', 'POP_EXCEPT'}


def get_code(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            if c.co_name == name:
                return c
            found = get_code(c, name)
            if found is not None:
                return found
    return None


def seq(r):
    out = []
    for b in sorted(r.blocks, key=lambda x: x.start_offset):
        ops = [i.opname for i in b.instructions
               if i.opname not in NOISE and i.opname not in EXC]
        out.append(ops)
    return out


def main():
    pyc = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else 't_host_try_sections'
    module = load_pyc_file_v2(pyc)
    code_obj = module.code
    if hasattr(code_obj, 'get'):
        code_obj = code_obj.get()
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    c = get_code(code_obj, name)
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, TryExceptRegion

    cfg = build_cfg(c)
    ra = RegionAnalyzer(cfg)
    ra.analyze()

    for reg in ra.regions:
        if not isinstance(reg, TryExceptRegion):
            continue
        print('TryExceptRegion@%s children ternaries:' % reg.entry.start_offset)
        terns = [ch for ch in (reg.children or []) if isinstance(ch, TernaryRegion)]
        for t in terns:
            print('  %s seqs=%s' % (
                'T@%s' % t.entry.start_offset,
                seq(t)))
        # 同构矩阵
        for i, a in enumerate(terns):
            for b in terns[i + 1:]:
                print('  iso(%s, %s) = %s' % (
                    'T@%s' % a.entry.start_offset, 'T@%s' % b.entry.start_offset,
                    seq(a) == seq(b)))


if __name__ == '__main__':
    main()
