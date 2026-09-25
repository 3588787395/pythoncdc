# -*- coding: utf-8 -*-
"""Print every TernaryRegion / BoolOpRegion structural field for one code object.
usage: tfields.py <pyc> <fn> [nested-firstlineno]"""
import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main'); sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag6')
os.chdir(r'F:/Downloads/pythoncdc-main'); sys.stdout.reconfigure(encoding='utf-8')
import regdump
O = lambda b: getattr(b, 'start_offset', None)
LL = lambda v: (None if v is None else ([O(x) if hasattr(x,'start_offset') else (O(x[0]), x[1]) for x in v] if isinstance(v, list) else v))
pyc, fn = sys.argv[1], sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else None
root = regdump.load_pyc(pyc)
codes = [c for c in regdump.walk(root, []) if c.co_name == fn]
sel = [k for c in codes for k in c.co_consts if isinstance(k, types.CodeType) and (not want or k.co_firstlineno == want)] or codes
F = ['condition_block','true_value_block','false_value_block','merge_block','value_target','container_type',
     'condition_chain_blocks','merge_context','entry','blocks','is_condition_context','store_blocks','preload_exprs']
for code in sel:
    print('##### %s@L%d' % (code.co_name, code.co_firstlineno))
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg)
    rs = gen.region_analyzer.analyze()
    for r in sorted(rs, key=lambda x: O(x.entry) or 0):
        t = type(r).__name__
        if 'Ternary' in t or 'BoolOp' in t or 'Loop' in t:
            print('  %s@%s' % (t, O(r.entry)))
            for f in F:
                if hasattr(r, f):
                    v = getattr(r, f)
                    if v is None or (isinstance(v, (list, tuple, set, dict)) and not v): continue
                    print('      %-24s %s' % (f, LL(v) if not isinstance(v, (str, int, bool)) else v))
