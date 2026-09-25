# -*- coding: utf-8 -*-
"""read-only: count TernaryRegions and their merge_context / demotion fields."""
import io, marshal, sys, types, os
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

def load(path):
    d = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try: return marshal.loads(d[off:])
        except Exception: pass

def walk(c, out):
    out.append(c)
    for x in c.co_consts:
        if isinstance(x, types.CodeType): walk(x, out)
    return out

pyc, name = sys.argv[1], sys.argv[2]
for code in [c for c in walk(load(pyc), []) if c.co_name == name]:
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    regions = gen.region_analyzer.analyze()
    TR = [r for r in regions if type(r).__name__ == 'TernaryRegion']
    print('%s: regions=%d TernaryRegion=%d' % (name, len(regions), len(TR)))
    n_none = 0
    for r in TR:
        mc = getattr(r, 'merge_context', 'NO-ATTR')
        if mc is None: n_none += 1
        print('  Ternary@%-5s merge_block=%s merge_context=%r func_call_info=%s' % (
            getattr(r.entry, 'start_offset', None),
            getattr(r.merge_block, 'start_offset', None),
            type(mc).__name__ if mc != 'NO-ATTR' else mc,
            bool(getattr(r, 'func_call_info', None))))
    print('  merge_context is None:', n_none)
