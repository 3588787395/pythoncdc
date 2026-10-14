"""trace_r108.py — read-only: which declared region entries are ever dispatched for clock_worker?

usage: python -X utf8 trace_r108.py [LO] [HI]

Monkeypatches RegionASTGenerator._generate_region / _generate_block_statements /
_generate_try_body / _generate_loop / _generate_if / _process_if_blocks to record every call
during a real decompile of the victim pyc, then reports, for the census-declared never-dispatched
entries, whether they were reached and whether their blocks produced statements.
No pipeline semantics are changed (hooks only append to a log).
"""
import marshal
import sys
import types

sys.path.insert(0, '.')

import core.cfg.region_ast_generator as RAG  # noqa: E402

PYC = ('D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/'
       'plugins/plugin_system_event_source/realtime_event_source.pyc')

LOG = []


def off(x):
    return getattr(x, 'start_offset', x)


def find(c, n):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == n:
                return k
            r = find(k, n)
            if r:
                return r


LO = int(sys.argv[1]) if len(sys.argv) > 1 else 7900
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 8600

G = RAG.RegionASTGenerator
orig_region = G._generate_region
orig_block = G._generate_block_statements


def in_clock(self):
    try:
        return 'clock_worker' in str(getattr(self.cfg, 'name', '')) or \
            'clock_worker' in str(getattr(self.cfg, 'qualname', '')) or \
            'clock_worker' in str(getattr(self, 'code', ''))
    except Exception:
        return False


def patched_region(self, region, *a, **kw):
    e = off(region.entry) if getattr(region, 'entry', None) is not None else None
    inrange = e is not None and LO <= e <= HI and in_clock(self)
    if inrange:
        LOG.append(('gen_region', type(region).__name__, e,
                    sorted(off(b) for b in (region.blocks or ())),
                    getattr(region, 'parent', None) is not None))
    return orig_region(self, region, *a, **kw)


def patched_block(self, block, *a, **kw):
    o = off(block)
    if LO <= o <= HI and in_clock(self):
        LOG.append(('block', o, len(list(block.instructions)),
                    list(block.instructions)[-1].opname if list(block.instructions) else '-'))
    return orig_block(self, block, *a, **kw)


G._generate_region = patched_region
G._generate_block_statements = patched_block

from pycdc import decompile_pyc  # noqa: E402

code = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
decompile_pyc(PYC)

regions = {}
disp = set()
blocks_seen = set()
for rec in LOG:
    if rec[0] == 'gen_region':
        disp.add(rec[2])
    else:
        blocks_seen.add(rec[1])

print('--- dispatch log (%d..%d) ---' % (LO, HI))
for rec in LOG:
    print(rec)
print('--- entries ever dispatched by _generate_region:', sorted(disp))
print('--- blocks ever passed to _generate_block_statements:', sorted(blocks_seen))
DECL = [7972, 8294, 8350, 8354, 8400, 8450, 8186, 7270, 7216, 7634]
print('--- census declared-never-dispatched ---')
for d in DECL:
    print('@%-6d dispatched=%s' % (d, d in disp))
