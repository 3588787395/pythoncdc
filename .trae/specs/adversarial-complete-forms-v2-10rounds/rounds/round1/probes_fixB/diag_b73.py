"""[B73] 取证：r10_04.imp_try_sections 块布局 + 区域归属 + 生成 AST。"""
import json
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

import marshal
import importlib.util

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

PYC = r'F:\Downloads\pythoncdc-main\test_repros\round10\r10_04_import_try_cross.pyc'


def load_code(pyc):
    with open(pyc, 'rb') as f:
        data = f.read()
    # 3.11 pyc header: 16 bytes
    return marshal.loads(data[16:])


code = load_code(PYC)
fn_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'imp_try_sections':
        fn_code = c
        break

builder = CFGBuilder()
cfg = builder.build(fn_code)

print('=== blocks ===')
log = []
for b in cfg.get_blocks_in_order():
    instrs = [(i.offset, i.opname, i.argval) for i in b.instructions]
    succ = [s.start_offset for s in getattr(b, 'successors', [])]
    pred = [s.start_offset for s in getattr(b, 'predecessors', [])]
    log.append({'block': b.start_offset, 'instrs': instrs,
                'succ': succ, 'pred': pred})
    print(f'block {b.start_offset}: succ={succ} pred={pred}')
    for off, op, av in instrs:
        print(f'    {off:5d} {op:28s} {av!r}')

print('=== exception table ===')
for e in cfg.exception_table:
    print(e)

analyzer = RegionAnalyzer(cfg, fn_code)
regions = analyzer.analyze()
print('=== regions ===')


def dump_region(r, depth=0):
    print('  ' * depth + f'{r.region_type.name}@{getattr(r, "entry_block", None).start_offset if getattr(r, "entry_block", None) is not None else "?"} blocks={[b.start_offset for b in r.blocks]}')
    for ch in getattr(r, 'children', []) or []:
        dump_region(ch, depth + 1)


for r in regions:
    dump_region(r)

with open(r'F:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b73_blocks.json', 'w', encoding='utf-8') as f:
    json.dump(log, f, indent=1, ensure_ascii=False)
print('saved b73_blocks.json')
