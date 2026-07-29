"""R19 诊断：打印 get_str_data 的 TernaryRegion 信息，确认 R18 修复根因 A 后的状态，
并定位根因 B（兄弟 TernaryRegion 被遗漏）和 C（链式共享 merge_block）的修复点。"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TernaryRegion, IfRegion, LoopRegion

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

# 统计 region 类型
from collections import Counter
type_counts = Counter(type(r).__name__ for r in analyzer.regions)
print(f"Region types: {dict(type_counts)}")

# 打印所有 region 的 entry/merge_block 信息（用于定位链式共享）
print("\n=== All regions (entry/merge_block) ===")
for i, r in enumerate(analyzer.regions):
    entry_off = r.entry.start_offset if hasattr(r, 'entry') and hasattr(r.entry, 'start_offset') else '?'
    merge_off = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block and hasattr(r.merge_block, 'start_offset') else '?'
    parent_off = r.parent.start_offset if hasattr(r, 'parent') and r.parent and hasattr(r.parent, 'start_offset') else '?'
    parent_type = type(r.parent).__name__ if hasattr(r, 'parent') and r.parent else '?'
    print(f"  Region[{i}] {type(r).__name__}: entry={entry_off} merge={merge_off} parent={parent_type}@{parent_off}")

# 详细打印 TernaryRegion
for i, tr in enumerate(ternary_regions):
    entry_off = tr.entry.start_offset if hasattr(tr.entry, 'start_offset') else '?'
    merge_off = tr.merge_block.start_offset if tr.merge_block and hasattr(tr.merge_block, 'start_offset') else '?'
    parent_off = tr.parent.start_offset if hasattr(tr, 'parent') and tr.parent and hasattr(tr.parent, 'start_offset') else '?'
    parent_type = type(tr.parent).__name__ if hasattr(tr, 'parent') and tr.parent else '?'
    print(f"\nTernaryRegion[{i}]: entry={entry_off} merge_block={merge_off}")
    print(f"  parent={parent_type}@{parent_off}")
    print(f"  value_target={tr.value_target!r}")
    print(f"  merge_context={getattr(tr, 'merge_context', None)!r}")
    print(f"  container_type={getattr(tr, 'container_type', None)!r}")
    print(f"  dict_const_keys={getattr(tr, 'dict_const_keys', None)!r}")
    # 父节点的子区域列表
    if hasattr(tr, 'parent') and tr.parent is not None:
        siblings = [type(s).__name__ + '@' + str(s.entry.start_offset if hasattr(s, 'entry') and hasattr(s.entry, 'start_offset') else '?') for s in (tr.parent.children if hasattr(tr.parent, 'children') else [])]
        print(f"  parent.children: {siblings}")
    # 打印 merge_block 的指令
    if tr.merge_block:
        print(f"  merge_block instructions (non-noise):")
        for ins in tr.merge_block.instructions:
            if ins.opname not in ('EXTENDED_ARG', 'CACHE', 'NOP'):
                print(f"    {ins.offset:>4} {ins.opname:<28} {ins.argval!r}")

# 关键定位：查找 IfRegion@614（get_str_data 的 datas 循环里 if 块）
print("\n=== Looking for IfRegion around offset 614 (datas loop) ===")
for i, r in enumerate(analyzer.regions):
    if isinstance(r, IfRegion):
        if_entry = r.entry.start_offset if hasattr(r, 'entry') and hasattr(r.entry, 'start_offset') else '?'
        print(f"  IfRegion[{i}] entry={if_entry}")
        if hasattr(r, 'then_blocks'):
            print(f"    then_blocks count={len(r.then_blocks) if r.then_blocks else 0}")
        if hasattr(r, 'else_blocks'):
            print(f"    else_blocks count={len(r.else_blocks) if r.else_blocks else 0}")

# 找外层 LoopRegion@612
print("\n=== Looking for LoopRegion around offset 612 ===")
for i, r in enumerate(analyzer.regions):
    if isinstance(r, LoopRegion):
        l_entry = r.entry.start_offset if hasattr(r, 'entry') and hasattr(r.entry, 'start_offset') else '?'
        l_children = [type(s).__name__ + '@' + str(s.entry.start_offset if hasattr(s, 'entry') and hasattr(s.entry, 'start_offset') else '?') for s in (r.children if hasattr(r, 'children') else [])]
        print(f"  LoopRegion[{i}] entry={l_entry} children={l_children}")
