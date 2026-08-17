#!/usr/bin/env python3
"""R92 check block 2758 instructions"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)

# Check block 2758 and 2710
for offset in [2710, 2758]:
    block = cfg.get_block_by_offset(offset)
    if block:
        print(f"=== Block@{offset} ===")
        for instr in block.instructions:
            print(f"  {instr.offset:4d} {instr.opname:30s} {getattr(instr, 'argval', getattr(instr, 'arg', ''))}")
        print(f"  predecessors: {[p.start_offset for p in block.predecessors]}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        print()
