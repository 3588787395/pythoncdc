"""R19 诊断：详细打印 TernaryRegion@844 和 @1226 的结构。"""
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

target_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'get_str_data':
        target_co = const
        break

print(f"Found get_str_data: co_name={target_co.co_name}")

cfg = build_cfg(target_co)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()
analyzer = gen.region_analyzer

ternary_regions = [r for r in analyzer.regions if isinstance(r, TernaryRegion)]
print(f"\nTotal TernaryRegions: {len(ternary_regions)}")

# 打印 LoopRegion@610 的子节点
for r in analyzer.regions:
    if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 610:
        print(f"\nLoopRegion@610 children:")
        for c in (r.children or []):
            c_entry = c.entry.start_offset if hasattr(c, 'entry') and c.entry else '?'
            print(f"  {type(c).__name__}@{c_entry}")
        print(f"LoopRegion@610 blocks (start_offsets): {[b.start_offset for b in r.blocks]}")

# 打印 IfRegion@614 的 then_blocks 和 else_blocks
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 614:
        print(f"\nIfRegion@614:")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
        print(f"  children: {[type(c).__name__ + '@' + str(c.entry.start_offset) for c in (r.children or [])]}")
        # 检查 else_blocks 中是否包含 TernaryRegion@844 和 @1226 的 entry
        for tr in ternary_regions:
            tr_entry = tr.entry.start_offset if tr.entry else None
            in_else = any(b.start_offset == tr_entry for b in r.else_blocks) if tr_entry else False
            in_then = any(b.start_offset == tr_entry for b in r.then_blocks) if tr_entry else False
            print(f"  TernaryRegion@{tr_entry}: in_then={in_then} in_else={in_else}")

# 详细打印每个 TernaryRegion
for i, tr in enumerate(ternary_regions):
    entry_off = tr.entry.start_offset if tr.entry else None
    cond_off = tr.condition_block.start_offset if tr.condition_block else None
    tvb_off = tr.true_value_block.start_offset if tr.true_value_block else None
    fvb_off = tr.false_value_block.start_offset if tr.false_value_block else None
    merge_off = tr.merge_block.start_offset if tr.merge_block else None
    print(f"\nTernaryRegion[{i}]@{entry_off}:")
    print(f"  entry={entry_off}")
    print(f"  condition_block={cond_off}")
    print(f"  true_value_block={tvb_off}")
    print(f"  false_value_block={fvb_off}")
    print(f"  merge_block={merge_off}")
    print(f"  value_target={tr.value_target!r}")
    print(f"  merge_context={tr.merge_context!r}")
    print(f"  container_type={tr.container_type!r}")
    print(f"  dict_const_keys={tr.dict_const_keys!r}")
    print(f"  parent={type(tr.parent).__name__ if tr.parent else None}")
    print(f"  blocks (start_offsets): {[b.start_offset for b in tr.blocks]}")
    # 检查 merge_block 是否是其他 TernaryRegion 的 entry
    for j, otr in enumerate(ternary_regions):
        if otr is tr:
            continue
        otr_entry = otr.entry.start_offset if otr.entry else None
        if otr_entry == merge_off:
            print(f"  ** merge_block {merge_off} IS the entry of TernaryRegion[{j}]@{otr_entry} **")

# 检查 _try_build_ternary_chained_container 的链构建
print("\n=== Chain analysis (following merge_block -> entry) ===")
for i, tr in enumerate(ternary_regions):
    if not tr.merge_block:
        continue
    chain = [tr]
    visited = {id(tr)}
    current = tr
    while True:
        next_inner = None
        for r in ternary_regions:
            if id(r) not in visited and r.entry == current.merge_block:
                next_inner = r
                break
        if next_inner is None:
            break
        chain.append(next_inner)
        visited.add(id(next_inner))
        if next_inner.container_type:
            break
        current = next_inner
    if len(chain) > 1:
        print(f"  Chain from TernaryRegion[{i}]:")
        for k, c in enumerate(chain):
            c_entry = c.entry.start_offset if c.entry else None
            c_merge = c.merge_block.start_offset if c.merge_block else None
            print(f"    [{k}] entry={c_entry} merge={c_merge} container_type={c.container_type!r} value_target={c.value_target!r}")
        innermost = chain[-1]
        const_keys = getattr(innermost, 'dict_const_keys', None)
        print(f"    innermost.dict_const_keys={const_keys}")
        print(f"    chain length={len(chain)}, const_keys length={len(const_keys) if const_keys else 0}")
        if const_keys and len(const_keys) != len(chain):
            print(f"    ** MISMATCH: chain has {len(chain)} ternaries but dict has {len(const_keys)} keys **")
