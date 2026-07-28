"""R23-N19 调试 BoolOpRegion 的 _build_boolop_expression 输出"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'share_change':
        target_co = const
        break

builder = CFGBuilder()
cfg = builder.build(target_co)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

ast_gen = RegionASTGenerator(cfg, analyzer)
# 不调用 analyze_regions，直接调用 generate
# ast_gen.analyze_regions()

# 找到 BoolOpRegion@154
target_boolop = None
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion) and r.entry.start_offset == 154:
        target_boolop = r
        break

if target_boolop is None:
    print("BoolOpRegion@154 not found")
    sys.exit(0)

print(f"=== BoolOpRegion@154 ===")
print(f"  merge={target_boolop.merge_block.start_offset if target_boolop.merge_block else None}")
print(f"  op_chain ({len(target_boolop.op_chain)}):")
for i, (blk, op) in enumerate(target_boolop.op_chain):
    last = blk.get_last_instruction()
    last_str = f"{last.opname} -> {last.argval}" if last else "(none)"
    print(f"    [{i}] block@{blk.start_offset} op={op} last={last_str}")

# 调用 _build_boolop_expression
print(f"\n=== _build_boolop_expression 输出 ===")
try:
    result = ast_gen._build_boolop_expression(target_boolop)
    print(f"  result: {result}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"  ERROR: {e}")

# 检查 NONE_CHECK_OPS
try:
    from core.cfg.bytecode_constants import NONE_CHECK_OPS
    print(f"\n  NONE_CHECK_OPS: {NONE_CHECK_OPS}")
except ImportError:
    pass

# 搜索 NONE_CHECK_OPS 定义
import core.cfg
import inspect
# 找到 NONE_CHECK_OPS
for name in dir(core.cfg):
    obj = getattr(core.cfg, name, None)
    if isinstance(obj, frozenset) and 'POP_JUMP_FORWARD_IF_NONE' in obj:
        print(f"  Found NONE_CHECK_OPS as core.cfg.{name}: {obj}")
        break

# 从 region_ast_generator 模块导入
from core.cfg.region_ast_generator import NONE_CHECK_OPS as NCO
print(f"  NONE_CHECK_OPS (from region_ast_generator): {NCO}")

# 检查 last_instr 是否在 NONE_CHECK_OPS 中
for i, (blk, op) in enumerate(target_boolop.op_chain):
    last = blk.get_last_instruction()
    in_nco = last.opname in NCO if last else False
    print(f"  [{i}] last.opname={last.opname if last else None} in NONE_CHECK_OPS={in_nco}")
