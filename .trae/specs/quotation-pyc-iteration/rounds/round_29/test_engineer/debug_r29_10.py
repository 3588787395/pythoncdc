"""R29 测试工程师：调试repro_r29_10 (if-elif + while)"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

SRC = '''def f(x, items):
    if x == 1:
        items = items[1:]
    elif x == 2:
        items = items[2:]
    i = 0
    while i < len(items):
        items[i] = items[i] + 1
        i += 1
    return items
'''

co = compile(SRC, '<test>', 'exec')
f_co = co.co_consts[0]

builder = CFGBuilder()
cfg = builder.build(f_co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

blocks = {b.start_offset: b for b in cfg.get_blocks_in_order()}
print("=== Blocks ===")
for off in sorted(blocks.keys()):
    b = blocks[off]
    ipd = b.immediate_post_dominator
    ipd_off = ipd.start_offset if ipd else None
    succs = [s.start_offset for s in b.successors]
    last = b.get_last_instruction()
    last_str = f"{last.opname}→{last.argval}" if last else "None"
    print(f"  blk@{off}: ipd={ipd_off}, succs={succs}, last={last_str}")

print("\n=== Regions ===")
for r in regions:
    rtype = r.region_type.name if hasattr(r.region_type, 'name') else str(r.region_type)
    entry_off = r.entry.start_offset
    merge_off = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block else None
    blocks_str = [b.start_offset for b in r.blocks]
    print(f"  {type(r).__name__}({rtype}): entry={entry_off}, merge={merge_off}, blocks={blocks_str}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then={[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'elif_conditions') and r.elif_conditions:
        print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")
    if hasattr(r, 'elif_bodies') and r.elif_bodies:
        print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies]}")
    if hasattr(r, 'elif_final_else') and r.elif_final_else:
        print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else]}")

# Decompile and show
from pycdc import decompile_pyc
import py_compile, os
pyc_path = '/tmp/repro_r29_10.pyc'
src_path = '/tmp/repro_r29_10.py'
with open(src_path, 'w') as f:
    f.write(SRC)
py_compile.compile(src_path, pyc_path, doraise=True)
decompiled = decompile_pyc(pyc_path)
print("\n=== Decompiled ===")
print(decompiled)
