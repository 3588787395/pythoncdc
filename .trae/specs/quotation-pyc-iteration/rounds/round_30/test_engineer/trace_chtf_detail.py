"""R30-6: Detailed trace of _process_if_blocks for @826."""
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

    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'change_his_to_forward':
            target = const
            break

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    # Find block @826
    block_826 = None
    for b in cfg.blocks.values():
        if b.start_offset == 826:
            block_826 = b
            break

    print(f"Block @826: predecessors={[p.start_offset for p in block_826.predecessors]}")
    print(f"  successors={[s.start_offset for s in block_826.successors]}")
    print(f"  instructions:")
    for ins in block_826.instructions:
        print(f"    {ins.opname} {repr(ins.argval)[:60]}")

    # Find IF_THEN@608
    target_region = None
    for r in regions:
        if isinstance(r, IfRegion) and r.entry is not None and r.entry.start_offset == 608:
            target_region = r
            break

    print(f"\nIF_THEN@608 then_blocks={[b.start_offset for b in target_region.then_blocks]}")
    print(f"  @826 in then_blocks: {block_826 in target_region.then_blocks}")

    # Now trace _process_if_blocks in detail
    gen = RegionASTGenerator(cfg, analyzer)

    original_process = gen._process_if_blocks

    def traced_process(blocks, region, branch='then'):
        if isinstance(region, IfRegion) and region.entry is not None and region.entry.start_offset == 608:
            print(f"\n=== _process_if_blocks called for IF_THEN@608, branch={branch} ===")
            print(f"  blocks={[b.start_offset for b in blocks]}")
            print(f"  generated_blocks before: {sorted([b.start_offset for b in gen.generated_blocks if b.start_offset in [608,688,752,822,826,978]])}")

            # Check each block
            for b in sorted(blocks, key=lambda b: b.start_offset):
                in_gen = b in gen.generated_blocks
                role = analyzer.get_block_role(b)
                print(f"  block@{b.start_offset}: in_generated={in_gen}, role={role}, preds={[p.start_offset for p in b.predecessors]}")

        result = original_process(blocks, region, branch)

        if isinstance(region, IfRegion) and region.entry is not None and region.entry.start_offset == 608:
            print(f"\n  _process_if_blocks result: {len(result)} stmts")
            for i, s in enumerate(result):
                if isinstance(s, dict):
                    print(f"    [{i}] type={s.get('type')}")
                    if s.get('type') == 'If':
                        body = s.get('body', [])
                        orelse = s.get('orelse')
                        print(f"        body={[(b.get('type') if isinstance(b,dict) else type(b).__name__) for b in body] if isinstance(body, list) else body}")
                        if orelse:
                            print(f"        orelse={[(b.get('type') if isinstance(b,dict) else type(b).__name__) for b in orelse] if isinstance(orelse, list) else orelse}")
            print(f"  generated_blocks after: {sorted([b.start_offset for b in gen.generated_blocks if b.start_offset in [608,688,752,822,826,978]])}")

        return result

    gen._process_if_blocks = traced_process

    print("\n=== Generating ===")
    result = gen.generate()


if __name__ == '__main__':
    main()
