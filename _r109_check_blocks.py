"""Check block 766 instructions"""
import sys
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
import marshal, types

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

for c in code.co_consts:
    if isinstance(c, types.CodeType):
        for cc in c.co_consts:
            if isinstance(cc, types.CodeType) and cc.co_name == 'exception_handling_complex':
                target_code = cc
                break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_code)

for block in cfg.blocks.values():
    if block.start_offset in (766, 806, 846, 658, 626):
        print(f"\n=== Block {block.start_offset} ===")
        for inst in block.instructions:
            print(f"  {inst.offset:4d} {inst.opname:30s} {inst.argrepr}")
        print(f"  Successors: {[s.start_offset for s in block.successors]}")
