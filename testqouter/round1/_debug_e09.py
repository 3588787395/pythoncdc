import sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
import py_compile
from dis import get_instructions

tf = 'test_e09_nested_try.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
import marshal

with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = code.co_consts[0]

cfg = CFGBuilder().build(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

print("=== Blocks ===")
for offset in sorted(cfg.offset_to_block.keys()):
    block = cfg.offset_to_block[offset]
    instrs = [(i.offset, i.opname, i.argval) for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    print(f"  Block {offset}: {instrs} -> {succs}")

print("\n=== Regions ===")
for r in ra.regions:
    if isinstance(r, TryExceptRegion):
        print(f"  TryExceptRegion: entry={r.entry.start_offset if r.entry else None}")
        print(f"    try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"    try_offset_start={r.try_offset_start}, try_offset_end={r.try_offset_end}")
        print(f"    has_finally={r.has_finally}")
        print(f"    finally_blocks={[b.start_offset for b in r.finally_blocks]}")
        print(f"    finally_copy_blocks={r.finally_copy_blocks}")
        print(f"    handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}")
        for exc_type, exc_name, hblocks in r.except_handlers:
            print(f"    except_handler: type={exc_type}, name={exc_name}, blocks={[b.start_offset for b in hblocks]}")
        print(f"    has_else={r.has_else}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"    all_blocks={[b.start_offset for b in r.blocks]}")

if os.path.exists(pyc):
    os.remove(pyc)
