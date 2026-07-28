"""R30-6: Trace region structure for change_his_to_forward."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # Find change_his_to_forward
    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'change_his_to_forward':
            target = const
            break

    if not target:
        print("Function not found")
        return

    print(f"=== {target.co_name} ===")
    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    # Print region tree
    def blk_off(b):
        if b is None:
            return None
        return getattr(b, 'offset', getattr(b, 'start_offset', '?'))

    def blk_list_offs(blks):
        return [blk_off(b) for b in blks] if blks else []

    def print_region(region, depth=0):
        indent = '  ' * depth
        rtype = region.region_type.name if hasattr(region.region_type, 'name') else str(region.region_type)
        entry_off = blk_off(region.entry)
        block_offs = sorted([blk_off(b) for b in region.blocks]) if region.blocks else []
        print(f"{indent}{rtype}@{entry_off} blocks={block_offs[:15]}")

        if isinstance(region, IfRegion):
            cond_off = blk_off(region.condition_block)
            print(f"{indent}  cond={cond_off}")
            print(f"{indent}  then={blk_list_offs(region.then_blocks)[:10]}")
            print(f"{indent}  else={blk_list_offs(region.else_blocks)[:10]}")
            print(f"{indent}  merge={blk_off(region.merge_block)}")
            if region.elif_conditions:
                print(f"{indent}  elif_conds={blk_list_offs(region.elif_conditions)[:10]}")
            for i, body in enumerate(region.elif_bodies):
                print(f"{indent}  elif_body[{i}]={blk_list_offs(body)[:10]}")
            if region.elif_final_else:
                print(f"{indent}  elif_final_else={blk_list_offs(region.elif_final_else)[:10]}")

        elif isinstance(region, LoopRegion):
            print(f"{indent}  header={blk_off(region.header_block)}")
            print(f"{indent}  body={blk_list_offs(region.body_blocks)[:10]}")
            print(f"{indent}  merge/exit={blk_off(getattr(region, 'exit_block', None))}")

        for child in region.children:
            print_region(child, depth + 1)

    for region in regions:
        print_region(region)


if __name__ == '__main__':
    main()
