"""R18: 追踪 get_opt_objects 的完整生成"""
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

    # Patch _generate_region to trace ALL calls
    orig_generate_region = RegionASTGenerator._generate_region
    _depth = [0]
    def traced_generate_region(self, region):
        rtype = type(region).__name__
        entry_off = region.entry.start_offset if hasattr(region, 'entry') and region.entry else '?'
        _depth[0] += 1
        print(f"{'  '*_depth[0]}[GEN] _generate_region({rtype}, entry={entry_off})")
        result = orig_generate_region(self, region)
        _depth[0] -= 1
        if result:
            if isinstance(result, list):
                print(f"{'  '*_depth[0]}[GEN] => list[{len(result)}]")
            else:
                print(f"{'  '*_depth[0]}[GEN] => {type(result).__name__}")
        return result
    RegionASTGenerator._generate_region = traced_generate_region

    # Patch _generate_try_body
    orig_try_body = RegionASTGenerator._generate_try_body
    def traced_try_body(self, region):
        print(f"  [TRY_BODY] start, try_blocks={[b.start_offset for b in region.try_blocks]}")
        result = orig_try_body(self, region)
        print(f"  [TRY_BODY] => {len(result)} stmts")
        return result
    RegionASTGenerator._generate_try_body = traced_try_body

    # Patch _generate_block_statements
    orig_gen_block = RegionASTGenerator._generate_block_statements
    def traced_gen_block(self, block, _cjb_parent=None):
        print(f"    [BLK] _generate_block_statements(block={block.start_offset})")
        result = orig_gen_block(self, block, _cjb_parent)
        print(f"    [BLK] => {len(result)} stmts")
        return result
    RegionASTGenerator._generate_block_statements = traced_gen_block

    gen = RegionASTGenerator(cfg, ra)
    result = gen.generate()
    print(f"\n=== Final Result ===")
    if result and isinstance(result, dict):
        body = result.get('body', [])
        print(f"Function body has {len(body)} statements")
        for i, stmt in enumerate(body):
            print(f"  [{i}] {stmt}")


if __name__ == '__main__':
    main()
