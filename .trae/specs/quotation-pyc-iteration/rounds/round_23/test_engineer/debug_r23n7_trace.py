"""R23-N7: 追踪 _if_generate_elif_chain 中 R23-N7 修复是否被触发"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def find_code_obj(co, name):
    for const in co.co_consts:
        if isinstance(const, type(co)):
            if const.co_name == name:
                return const
            sub = find_code_obj(const, name)
            if sub:
                return sub
    return None


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = find_code_obj(code_obj, 'api_get_financial')

    # Patch _detect_chained_compare_pattern to trace
    orig_detect = None
    import core.cfg.region_analyzer as ra_mod
    orig_detect = ra_mod.RegionAnalyzer._detect_chained_compare_pattern
    def traced_detect(self, block):
        result = orig_detect(self, block)
        if block.start_offset == 694:
            import sys as _sys
            print(f"[TRACE] _detect_chained_compare_pattern(block@{block.start_offset}) = {result}", file=_sys.stderr)
        return result
    ra_mod.RegionAnalyzer._detect_chained_compare_pattern = traced_detect

    # Patch _try_build_attr_middle_from_blocks to trace
    orig_attr = RegionASTGenerator._try_build_attr_middle_from_blocks
    def traced_attr(self, cond_block, chain_blocks, ops):
        import sys as _sys
        if cond_block and cond_block.start_offset == 694:
            print(f"[TRACE] _try_build_attr_middle_from_blocks CALLED block@{cond_block.start_offset}, chain={[b.start_offset for b in chain_blocks]}, ops={ops}", file=_sys.stderr)
        result = orig_attr(self, cond_block, chain_blocks, ops)
        if cond_block and cond_block.start_offset == 694:
            print(f"[TRACE] _try_build_attr_middle_from_blocks RESULT = {result}", file=_sys.stderr)
        return result
    RegionASTGenerator._try_build_attr_middle_from_blocks = traced_attr

    # Also patch _if_generate_elif_chain to trace
    orig_elif = RegionASTGenerator._if_generate_elif_chain
    def traced_elif(self, region):
        import sys as _sys
        if getattr(region, 'elif_conditions', None):
            for ec in region.elif_conditions:
                if ec.start_offset == 694:
                    print(f"[TRACE] _if_generate_elif_chain: region entry={region.entry.start_offset if region.entry else None}, elif_cond@694 found, elif_condition initially None", file=_sys.stderr)
        return orig_elif(self, region)
    RegionASTGenerator._if_generate_elif_chain = traced_elif

    cfg = build_cfg(target)
    generator = RegionASTGenerator(cfg, top_level_code=target)
    result = generator.generate()

    # Find the relevant part
    print("\n=== Generated code (api_get_financial) ===")
    import ast
    try:
        tree = ast.parse(result)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'api_get_financial':
                print(ast.unparse(node))
                break
    except Exception as e:
        print(f"Parse error: {e}")
        # Print raw lines
        for i, line in enumerate(result.split('\n')):
            if 'api_get_financial' in line or '400' in line or '499' in line:
                print(f"  {i}: {line}")


if __name__ == '__main__':
    main()
