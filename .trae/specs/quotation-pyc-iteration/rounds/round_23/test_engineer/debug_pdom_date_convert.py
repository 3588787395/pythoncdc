"""R23-N6: 分析 date_convert 的后支配树和merge决策"""
import sys
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def load_code():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            r = find_func(const, name)
            if r:
                return r
    return None


def main():
    code_obj = load_code()
    func = find_func(code_obj, 'date_convert')

    cfg = build_cfg(func)
    blocks_sorted = sorted(cfg.blocks.values(), key=lambda b: b.start_offset)
    print(f"=== CFG blocks ({len(blocks_sorted)}) ===")
    for b in blocks_sorted:
        ins_str = ', '.join(f"{i.opname}" for i in b.instructions[:3])
        succs = [s.id for s in b.successors]
        preds = [p.id for p in b.predecessors]
        ipdom = b.immediate_post_dominator.id if b.immediate_post_dominator else None
        print(f"  B{b.id} (off {b.start_offset}) [{ins_str}...] succs={succs} preds={preds} ipdom={ipdom}")

    # 找到 outer if 的 condition block (offset 158)
    cond_block = None
    for b in blocks_sorted:
        if b.start_offset == 158:
            cond_block = b
            break

    if cond_block:
        print(f"\n=== Outer if condition block: B{cond_block.id} ===")
        cond_succs = list(cond_block.conditional_successors)
        print(f"  conditional_successors: {[s.id for s in cond_succs]}")
        then_succ = sorted(cond_succs, key=lambda s: s.start_offset)[0]
        else_succ = sorted(cond_succs, key=lambda s: s.start_offset)[1]
        print(f"  then_succ: B{then_succ.id} (offset {then_succ.start_offset})")
        print(f"  else_succ: B{else_succ.id} (offset {else_succ.start_offset})")

        # 计算最近公共后支配点
        from core.cfg.region_analyzer import RegionAnalyzer
        # Need to access the analyzer instance through the generator
        gen = RegionASTGenerator(cfg, top_level_code=None)
        _ = gen.generate()
        analyzer = gen.region_analyzer
        merge = analyzer._find_nearest_common_post_dominator(then_succ, else_succ)
        print(f"  _find_nearest_common_post_dominator: B{merge.id if merge else '?'} (offset {merge.start_offset if merge else '?'})")

        # 输出区域信息
        regions = gen.regions
        print(f"\n=== 顶层区域 ({len(regions)}) ===")
        for r in regions:
            rtype = type(r).__name__
            blocks = list(r.blocks) if hasattr(r, 'blocks') else []
            block_ids = [b.id for b in blocks]
            extra = ''
            if hasattr(r, 'merge_block') and r.merge_block:
                extra += f' merge=B{r.merge_block.id}'
            if hasattr(r, 'entry') and r.entry:
                extra += f' entry=B{r.entry.id}'
            if hasattr(r, 'then_blocks') and r.then_blocks:
                extra += f' then={[b.id for b in r.then_blocks]}'
            if hasattr(r, 'else_blocks') and r.else_blocks:
                extra += f' else={[b.id for b in r.else_blocks]}'
            if hasattr(r, 'elif_conditions') and r.elif_conditions:
                extra += f' elif_conds={[b.id for b in r.elif_conditions]}'
            print(f"  {rtype} blocks={block_ids}{extra}")


if __name__ == '__main__':
    main()
