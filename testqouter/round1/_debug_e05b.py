import sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
import py_compile
from dis import get_instructions

tf = 'test_e05_try_except_finally.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion, TernaryRegion
import marshal

with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = code.co_consts[0]

cfg = CFGBuilder().build(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

print("=== All Regions ===")
for r in ra.regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")
    if isinstance(r, TryExceptRegion):
        print(f"    try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"    finally_copy_blocks={r.finally_copy_blocks}")
    if isinstance(r, (IfRegion, TernaryRegion)):
        print(f"    blocks={[b.start_offset for b in r.blocks]}")
        if hasattr(r, 'condition_block'):
            print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
        if hasattr(r, 'true_blocks'):
            print(f"    true_blocks={[b.start_offset for b in r.true_blocks]}")
        if hasattr(r, 'false_blocks'):
            print(f"    false_blocks={[b.start_offset for b in r.false_blocks]}")

print("\n=== Block 52 details ===")
block52 = cfg.get_block_by_offset(52)
if block52:
    for i in block52.instructions:
        print(f"  {i.offset}: {i.opname} {i.argval}")
    print(f"  successors: {[s.start_offset for s in block52.successors]}")

print("\n=== Block region mapping for copy blocks ===")
for offset in [52, 84, 94, 96]:
    block = cfg.get_block_by_offset(offset)
    if block:
        region = ra.block_to_region.get(block)
        entry_region = ra.get_entry_region_for_block(block)
        print(f"  Block {offset}: region={type(region).__name__ if region else None}, entry_region={type(entry_region).__name__ if entry_region else None}")

if os.path.exists(pyc):
    os.remove(pyc)
