"""R18 诊断：打印 get_str_data 的 TernaryRegion 信息，确认 value_target 误识别。"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TernaryRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 找到 get_str_data code object
target_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'get_str_data':
        target_co = const
        break

if target_co is None:
    print("get_str_data not found")
    sys.exit(1)

print(f"Found get_str_data: co_name={target_co.co_name}")

# 构建 CFG 和区域分析
cfg = build_cfg(target_co)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()  # 触发 analyze()
analyzer = gen.region_analyzer

# 打印所有 TernaryRegion
ternary_regions = [r for r in analyzer.regions if isinstance(r, TernaryRegion)]
print(f"\nTotal TernaryRegions: {len(ternary_regions)}")
print(f"Total regions: {len(analyzer.regions)}")

for i, tr in enumerate(ternary_regions):
    entry_off = tr.entry.start_offset if hasattr(tr.entry, 'start_offset') else '?'
    merge_off = tr.merge_block.start_offset if tr.merge_block and hasattr(tr.merge_block, 'start_offset') else '?'
    print(f"\nTernaryRegion[{i}]: entry={entry_off} merge_block={merge_off}")
    print(f"  value_target={tr.value_target!r}")
    print(f"  merge_context={getattr(tr, 'merge_context', None)!r}")
    print(f"  container_type={getattr(tr, 'container_type', None)!r}")
    print(f"  dict_const_keys={getattr(tr, 'dict_const_keys', None)!r}")
    # 打印 merge_block 的指令
    if tr.merge_block:
        print(f"  merge_block instructions (non-noise):")
        for ins in tr.merge_block.instructions:
            if ins.opname not in ('EXTENDED_ARG', 'CACHE', 'NOP'):
                print(f"    {ins.offset:>4} {ins.opname:<28} {ins.argval!r}")
