"""Check CFG blocks for exception_handling_complex."""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

builder = CFGBuilder()
cfg = builder.build(ehc)

for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    instrs = [(i.offset, i.opname) for i in b.instructions]
    succs = [s.start_offset for s in b.successors]
    preds = [p.start_offset for p in b.predecessors]
    print(f"B@{b.start_offset:3d} succ={succs} pred={preds} instrs={instrs}")
