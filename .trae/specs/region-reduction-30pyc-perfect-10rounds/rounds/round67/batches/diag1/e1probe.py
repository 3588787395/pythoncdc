# -*- coding: utf-8 -*-
"""diag1 r67: evaluate _merge_block_is_then_exclusive on every IfRegion of one function.

usage: python -X utf8 e1probe.py <pyc> <func>
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag1')
from blk import load_pyc, walk, off  # noqa: E402


def main(pyc, name):
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.region_analyzer import IfRegion
    co = [c for c in walk(load_pyc(pyc), []) if c.co_name == name][0]
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regs = gen.region_analyzer.analyze()
    for r in regs:
        if not isinstance(r, IfRegion):
            continue
        mb = getattr(r, 'merge_block', None)
        tb = list(getattr(r, 'then_blocks', None) or [])
        eb = list(getattr(r, 'else_blocks', None) or [])
        cc = list(getattr(r, 'chained_compare_blocks', None) or [])
        cb = getattr(r, 'condition_block', None)
        verdict = gen._merge_block_is_then_exclusive(r)
        print('%-14s entry@%-5s cond@%-5s merge@%-5s then=%s else=%s cc=%s '
              'EXIT@%s parent=%s  => _merge_block_is_then_exclusive=%s'
              % (type(r).__name__, off(r.entry), off(cb) if cb else None,
                 off(mb) if mb else None,
                 [off(x) for x in tb], [off(x) for x in eb], [off(x) for x in cc],
                 off(getattr(r, 'exit', None)) if getattr(r, 'exit', None) else None,
                 type(getattr(r, 'parent', None)).__name__ if getattr(r, 'parent', None) else None,
                 verdict))
        for lbl, lst in (('then', tb), ('else', eb), ('cond', [cb] if cb else [])):
            for b in lst:
                ops = [i.opname for i in b.instructions]
                print('      %-5s@%-5s n=%-3d %s' % (lbl, off(b), len(ops), ' '.join(ops)[:150]))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
