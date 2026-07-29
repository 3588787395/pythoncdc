"""R23-N18: 调试 date_convert 的 IfRegion merge_block 设置"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, RegionType
from core.cfg.cfg_builder import CFGBuilder

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # 找到 date_convert 函数
    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'date_convert':
            target = const
            break

    if target is None:
        print("未找到 date_convert")
        return

    print(f"=== date_convert ===")
    print(f"co_consts: {target.co_consts}")
    print(f"co_names: {target.co_names}")
    print(f"co_varnames: {target.co_varnames}")

    # 构建 CFG
    builder = CFGBuilder()
    cfg = builder.build(target)

    print(f"\n=== CFG blocks ===")
    for offset in sorted(cfg.blocks.keys()):
        b = cfg.blocks[offset]
        instrs = []
        for ins in b.instructions:
            if ins.opname in ('EXTENDED_ARG', 'CACHE'):
                continue
            instrs.append(f"{ins.opname}({ins.argval!r})")
        print(f"  @{offset:4d} preds={[p.start_offset for p in b.predecessors]} succs={[s.start_offset for s in b.successors]} instrs={instrs}")

    # 区域分析
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"\n=== Regions ===")
    for r in analyzer.regions:
        print(f"\n  Region type={r.region_type.name} entry={r.entry.start_offset if r.entry else None}")
        if isinstance(r, IfRegion):
            print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
            print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
            print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
            print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")
            if hasattr(r, 'elif_conditions') and r.elif_conditions:
                print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")
            if hasattr(r, 'elif_bodies') and r.elif_bodies:
                print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies]}")
            if hasattr(r, 'elif_final_else') and r.elif_final_else:
                print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else]}")
            print(f"    blocks={[b.start_offset for b in r.blocks]}")

    # 关键：检查 @200-252 (if branch's data_return) 和 @288-340 (shared data_return) 的归属
    print(f"\n=== 关键块归属分析 ===")
    for offset in [200, 252, 254, 256, 282, 284, 286, 288, 340, 342]:
        if offset not in cfg.blocks:
            continue
        b = cfg.blocks[offset]
        in_regions = []
        for r in analyzer.regions:
            if b in r.blocks:
                in_regions.append(f"{r.region_type.name}@{r.entry.start_offset if r.entry else None}")
        print(f"  @{offset:4d} in_regions={in_regions}")


if __name__ == '__main__':
    main()
