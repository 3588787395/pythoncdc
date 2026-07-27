"""R18: 追踪 get_opt_objects 的 try body 生成"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, BoolOpRegion, IfRegion
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator


def main():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_opt_objects':
            target = const
            break

    cfg = CFGBuilder().build(target)
    ra = RegionAnalyzer(cfg, parent_code=target)
    ra.analyze()

    # Find the TryExceptRegion
    try_region = None
    for r in ra.regions:
        if isinstance(r, TryExceptRegion) and r.entry.start_offset == 164:
            try_region = r
            break

    if not try_region:
        print("TryExceptRegion at 164 not found")
        return

    print(f"TryExceptRegion try_blocks: {[b.start_offset for b in try_region.try_blocks]}")

    # Patch _generate_region to trace
    orig_generate_region = RegionASTGenerator._generate_region
    def traced_generate_region(self, region):
        if hasattr(region, 'entry') and region.entry and region.entry.start_offset in (164, 232, 270, 312, 314, 418):
            rtype = type(region).__name__
            print(f"  [TRACE] _generate_region({rtype}, entry={region.entry.start_offset})")
        result = orig_generate_region(self, region)
        if hasattr(region, 'entry') and region.entry and region.entry.start_offset in (164, 232, 270, 312, 314, 418):
            rtype = type(region).__name__
            print(f"  [TRACE] _generate_region({rtype}, entry={region.entry.start_offset}) => {result}")
        return result
    RegionASTGenerator._generate_region = traced_generate_region

    # Patch _generate_block_statements to trace
    orig_gen_block = RegionASTGenerator._generate_block_statements
    def traced_gen_block(self, block, _cjb_parent=None):
        if block.start_offset in (164, 232, 270, 312, 314, 418):
            print(f"  [TRACE] _generate_block_statements(block={block.start_offset})")
        result = orig_gen_block(self, block, _cjb_parent)
        if block.start_offset in (164, 232, 270, 312, 314, 418):
            print(f"  [TRACE] _generate_block_statements(block={block.start_offset}) => {result}")
        return result
    RegionASTGenerator._generate_block_statements = traced_gen_block

    # Patch _generate_try_body
    orig_try_body = RegionASTGenerator._generate_try_body
    def traced_try_body(self, region):
        if region is try_region:
            print(f"\n=== _generate_try_body START (try_blocks={[b.start_offset for b in region.try_blocks]}) ===")
        result = orig_try_body(self, region)
        if region is try_region:
            print(f"=== _generate_try_body END => {result} ===\n")
        return result
    RegionASTGenerator._generate_try_body = traced_try_body

    # Generate
    gen = RegionASTGenerator(cfg, ra)
    print("=== Generating function ===")
    result = gen.generate()
    print(f"\n=== Result ===")
    if result:
        for stmt in result:
            print(f"  {stmt}")


if __name__ == '__main__':
    main()
