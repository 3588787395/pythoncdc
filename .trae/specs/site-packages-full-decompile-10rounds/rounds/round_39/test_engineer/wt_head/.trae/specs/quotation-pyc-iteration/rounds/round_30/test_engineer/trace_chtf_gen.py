"""R30-6: Trace IF_THEN@608 generation in change_his_to_forward."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion
from core.cfg.region_ast_generator import RegionASTGenerator

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

    # Find IF_THEN@608 (offset 608)
    target_region = None
    for r in regions:
        if isinstance(r, IfRegion) and r.entry is not None and r.entry.start_offset == 608:
            target_region = r
            break

    if not target_region:
        print("IF_THEN@608 not found")
        return

    print(f"\nIF_THEN@608:")
    print(f"  entry={target_region.entry.start_offset}")
    print(f"  cond={target_region.condition_block.start_offset}")
    print(f"  then={[b.start_offset for b in target_region.then_blocks]}")
    print(f"  else={[b.start_offset for b in target_region.else_blocks]}")
    print(f"  merge={target_region.merge_block.start_offset if target_region.merge_block else None}")
    print(f"  blocks={sorted([b.start_offset for b in target_region.blocks])}")
    print(f"  children={[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in target_region.children]}")

    # Patch _process_if_blocks to trace
    gen = RegionASTGenerator(cfg, analyzer)

    original_process = gen._process_if_blocks
    original_generate_normal = gen._if_generate_normal
    original_generate_region = gen._generate_region

    trace_depth = [0]

    def traced_generate_region(region):
        if isinstance(region, IfRegion) and region.entry is not None:
            eid = region.entry.start_offset
            if eid in (608, 688, 562):
                indent = '  ' * trace_depth[0]
                print(f"{indent}_generate_region(IfRegion@{eid}): then={[b.start_offset for b in region.then_blocks]}, merge={region.merge_block.start_offset if region.merge_block else None}")
        trace_depth[0] += 1
        try:
            result = original_generate_region(region)
        finally:
            trace_depth[0] -= 1
        if isinstance(region, IfRegion) and region.entry is not None:
            eid = region.entry.start_offset
            if eid in (608, 688, 562):
                indent = '  ' * trace_depth[0]
                if isinstance(result, dict):
                    rtype = result.get('type', '?')
                    if rtype == 'If':
                        body_types = [s.get('type', '?') for s in result.get('body', [])] if isinstance(result.get('body'), list) else '?'
                        print(f"{indent}_generate_region(IfRegion@{eid}) -> If: body_types={body_types}")
                    else:
                        print(f"{indent}_generate_region(IfRegion@{eid}) -> {rtype}")
                elif isinstance(result, list):
                    print(f"{indent}_generate_region(IfRegion@{eid}) -> list[{len(result)}]: {[r.get('type','?') if isinstance(r,dict) else type(r).__name__ for r in result]}")
        return result

    def traced_process_if_blocks(blocks, region, branch='then'):
        if isinstance(region, IfRegion) and region.entry is not None:
            eid = region.entry.start_offset
            if eid in (608, 688, 562):
                indent = '  ' * trace_depth[0]
                block_offs = [b.start_offset for b in blocks]
                print(f"{indent}_process_if_blocks(blocks={block_offs}, region@{eid}, branch={branch})")
        return original_process(blocks, region, branch)

    gen._generate_region = traced_generate_region
    gen._process_if_blocks = traced_process_if_blocks

    # Generate the full module
    import core.cfg.region_ast_generator as mod
    # Save original and patch
    orig_init = mod.RegionASTGenerator.__init__
    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self._generate_region = self._generate_region.__get__(self)
        # Can't easily patch here, use different approach

    # Instead, just generate the function
    print("\n=== Generating change_his_to_forward ===")
    result = gen.generate()
    if isinstance(result, dict):
        body = result.get('body', [])
        for i, stmt in enumerate(body):
            if isinstance(stmt, dict):
                print(f"  [{i}] {stmt.get('type', '?')}: {str(stmt)[:200]}")


if __name__ == '__main__':
    main()
