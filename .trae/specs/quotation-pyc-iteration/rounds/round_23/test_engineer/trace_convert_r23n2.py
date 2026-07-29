"""R23-N2 调试：追踪 convert_to_list 的 IfRegion 和 BoolOpRegion 处理"""
import sys
sys.path.insert(0, '/workspace')

# 给 region_ast_generator 的关键位置打补丁，输出诊断信息
import core.cfg.region_ast_generator as rag_mod


# 保存原始方法
_orig_build_boolop_expression = rag_mod.RegionASTGenerator._build_boolop_expression
_orig_try_build_and_inner_or = rag_mod.RegionASTGenerator._try_build_and_inner_or_pattern

# Patch _try_build_and_inner_or_pattern
def _patched_try_build_and_inner_or(self, region):
    result = _orig_try_build_and_inner_or(self, region)
    # 只对 convert_to_list 输出
    try:
        co_name = getattr(self, 'current_function_name', '')
    except Exception:
        co_name = ''
    if 'convert_to_list' in str(getattr(self, '_debug_func_name', '')) or result is not None:
        merge_off = region.merge_block.start_offset if region.merge_block else None
        op_chain_summary = [(b.start_offset, op) for b, op in region.op_chain]
        print(f"[TRACE _try_build_and_inner_or_pattern]")
        print(f"  op_chain: {op_chain_summary}")
        print(f"  merge_block: {merge_off}")
        print(f"  result: {result}")
    return result

# Patch _build_boolop_expression
def _patched_build_boolop(self, region):
    result = _orig_build_boolop_expression(self, region)
    print(f"[TRACE _build_boolop_expression]")
    print(f"  op_chain: {[(b.start_offset, op) for b, op in region.op_chain]}")
    print(f"  merge: {region.merge_block.start_offset if region.merge_block else None}")
    print(f"  result: {result}")
    return result

rag_mod.RegionASTGenerator._build_boolop_expression = _patched_build_boolop
rag_mod.RegionASTGenerator._try_build_and_inner_or_pattern = _patched_try_build_and_inner_or


# 找到处理 IfRegion 的方法并打补丁
# _build_condition_from_boolop_region 应该是处理 IfRegion 中 BoolOp 的方法
for attr_name in dir(rag_mod.RegionASTGenerator):
    if 'boolop' in attr_name.lower() and 'condition' in attr_name.lower():
        print(f"Found method: {attr_name}")


# 反编译
from pycdc import decompile_pyc
PYC = '/workspace/quotation.pyc'

# 只反编译 convert_to_list
import importlib.util
import dis
import types

# 加载原始 pyc 找到 convert_to_list 的 code object
from core.pyc_loader_v2 import load_pyc_file_v2
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 查找 convert_to_list
target_code = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'convert_to_list':
        target_code = const
        break

if target_code is None:
    print("convert_to_list not found!")
    sys.exit(1)

print(f"Found convert_to_list: co_consts={target_code.co_consts[:5]}...")
print(f"co_code length: {len(target_code.co_code)}")

# 直接反编译这个函数
from pycdc import decompile_pyc
try:
    src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
    # 提取 convert_to_list
    import re
    m = re.search(r'def convert_to_list\(.*?(?=\ndef |\nclass |\Z)', src, re.DOTALL)
    if m:
        print("\n=== Decompiled convert_to_list ===")
        print(m.group(0))
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
