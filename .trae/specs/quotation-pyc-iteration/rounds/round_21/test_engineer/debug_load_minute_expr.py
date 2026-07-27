"""R21 调试 load_minute_or_day_kline 的表达式重建"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.ast_generator_v2 import ExpressionReconstructor

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

# find block 12
b12 = cfg.blocks.get(12)
if not b12:
    print("block 12 not found")
    sys.exit(1)

# Extract instructions for the first statement (nowend = ...)
# up to STORE_FAST 'nowend'
stmt_instrs = []
for ins in b12.instructions:
    stmt_instrs.append(ins)
    if ins.opname == 'STORE_FAST' and ins.argval == 'nowend':
        break

print(f"=== Instructions for nowend = ... ({len(stmt_instrs)} instrs) ===")
for ins in stmt_instrs:
    print(f"  {ins.offset:4d}  {ins.opname:35s} arg={ins.arg!r} argval={ins.argval!r}")

# Reconstruct expression
rec = ExpressionReconstructor(cfg)
value_instrs = stmt_instrs[:-1]  # exclude STORE_FAST
print(f"\n=== value_instrs ({len(value_instrs)}) ===")
result = rec.reconstruct(value_instrs)
print(f"\n=== Reconstructed AST ===")
import json
print(json.dumps(result, indent=2, default=str))

# Show stack state after each instruction
print(f"\n=== Stack trace ===")
rec.reset()
for ins in value_instrs:
    rec._process_instruction(ins)
    print(f"  {ins.offset:4d}  {ins.opname:30s} argval={ins.argval!r}")
    print(f"        stack depth={len(rec.stack)}: {[str(s.get('type')) + (':' + str(s.get('attr','')) if s.get('type') == 'Attribute' else '') for s in rec.stack]}")
