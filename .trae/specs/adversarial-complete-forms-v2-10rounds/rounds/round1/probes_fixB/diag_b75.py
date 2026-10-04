"""[B75] 取证：r10_15.g_in_try_except 块布局 + 区域归属。"""
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

import marshal

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

PYC = r'F:\Downloads\pythoncdc-main\test_repros\round10\r10_15_global_hosts.pyc'


def load_code(pyc):
    with open(pyc, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


code = load_code(PYC)
fn_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'g_in_try_except':
        fn_code = c
        break

builder = CFGBuilder()
cfg = builder.build(fn_code)

print('=== blocks ===')
for b in cfg.get_blocks_in_order():
    instrs = [(i.offset, i.opname, i.argval) for i in b.instructions]
    succ = [s.start_offset for s in getattr(b, 'successors', [])]
    pred = [s.start_offset for s in getattr(b, 'predecessors', [])]
    print(f'block {b.start_offset}: succ={succ} pred={pred}')
    for off, op, av in instrs:
        print(f'    {off:5d} {op:26s} {av!r}')

print('=== exception table ===')
for e in cfg.exception_table:
    print(e)

analyzer = RegionAnalyzer(cfg, fn_code)
regions = analyzer.analyze()
print('=== regions ===')


def dump_region(r, depth=0):
    eb = getattr(r, 'entry_block', None) or getattr(r, 'entry', None)
    eo = eb.start_offset if eb is not None else '?'
    print('  ' * depth + f'{r.region_type.name}@{eo} blocks={sorted(b.start_offset for b in r.blocks)}')
    for ch in getattr(r, 'children', []) or []:
        dump_region(ch, depth + 1)


for r in regions:
    dump_region(r)
