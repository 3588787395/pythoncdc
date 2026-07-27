"""R21 调试 load_minute_or_day_kline：查看含 BINARY_OP + LOAD_METHOD 的块"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'load_minute_or_day_kline':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)

# find blocks containing BINARY_OP near LOAD_METHOD 'strftime'
for bid, b in sorted(cfg.blocks.items()):
    instrs = b.instructions
    has_binop = any(i.opname == 'BINARY_OP' for i in instrs)
    has_strftime = any(i.opname == 'LOAD_METHOD' and i.argval == 'strftime' for i in instrs)
    if has_binop and has_strftime:
        print(f"=== block {bid} (has BINARY_OP + LOAD_METHOD strftime) ===")
        for ins in instrs:
            print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")
        print(f"  succs={[s.id for s in b.successors]}")
        print()
