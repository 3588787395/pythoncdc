"""Probe: 追踪 IfRegion entry@1272 的 else 分支生成路径。"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

WATCH_ENTRY = 1272


def bs(blocks):
    return [getattr(b, 'start_offset', b) for b in (blocks or [])]


class Tracer:
    def __init__(self, gen):
        self.gen = gen


def wrap(name, log_result=True):
    orig = getattr(RegionASTGenerator, name)

    def patched(self, *a, **kw):
        region = a[0] if a else None
        entry = getattr(region, 'entry', None)
        eo = getattr(entry, 'start_offset', None) if entry is not None else None
        rel = (eo == WATCH_ENTRY) or (len(a) > 1 and getattr(a[1], 'entry', None) is not None
                                      and getattr(a[1].entry, 'start_offset', None) == WATCH_ENTRY)
        r = orig(self, *a, **kw)
        if rel or (eo is not None and abs((eo or 0) - WATCH_ENTRY) < 400):
            def summ(x, depth=0):
                if isinstance(x, list):
                    return '[%d stmts]' % len(x)
                if isinstance(x, dict):
                    t = x.get('type')
                    if t == 'If':
                        return 'If(body=%s, orelse=%s)' % (summ(x.get('body')), summ(x.get('orelse')))
                    return t
                return repr(x)[:60]
            print('%-40s entry=%s -> %s' % (name, eo, summ(r) if log_result else '?'))
        return r
    return patched


for name in ('_if_generate_else_branch', '_if_generate_then_branch',
             '_process_if_blocks', '_if_generate_branch_stmts',
             '_generate_block_statements', '_generate_region',
             '_if_generate_full_elif_chain', '_generate_if'):
    setattr(RegionASTGenerator, name, wrap(name))

from pycdc import decompile_pyc
decompile_pyc(sys.argv[1], use_cfg=True)
