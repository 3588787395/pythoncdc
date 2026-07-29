"""R23-N4: 跟踪 _process_if_blocks 对 check_index_code 的 elif_final_else 处理"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, RegionType, IfRegion, BoolOpRegion, TernaryRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from pycdc import decompile_pyc

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['check_index_code']

    cfg = build_cfg(co)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # 找最外层 IfRegion
    outer = None
    for r in analyzer.regions:
        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
            outer = r
            break

    # 创建 generator
    gen = RegionASTGenerator(cfg, analyzer)

    # Monkey-patch _process_if_blocks
    original_process = gen._process_if_blocks
    def traced_process(blocks, region, branch='then'):
        print(f"\n[_process_if_blocks] branch={branch}, region.entry={region.entry.start_offset if region.entry else None}")
        print(f"  blocks: {[b.start_offset for b in blocks]}")
        print(f"  region.children: {[c.region_type.name + '@' + str(c.entry.start_offset if c.entry else None) for c in (region.children or [])]}")
        _block_set = set(blocks)
        # 检查每个 block
        for b in sorted(blocks, key=lambda x: x.start_offset):
            _nr = analyzer.get_region_for_block(b)
            in_gen = b in gen.generated_blocks
            print(f"  block@{b.start_offset}: in_generated={in_gen}, region={type(_nr).__name__}@{_nr.entry.start_offset if _nr and _nr.entry else None}")
            if isinstance(_nr, IfRegion) and _nr is not region and _nr.entry is not None:
                print(f"    -> _nr.entry={_nr.entry.start_offset}, in_block_set={_nr.entry in _block_set}")
                if _nr.entry in _block_set and b == _nr.entry:
                    _has_cc = bool(getattr(_nr, 'chained_compare_blocks', None))
                    _has_elif = bool(getattr(_nr, 'elif_conditions', None))
                    print(f"    -> _has_cc={_has_cc}, _has_elif={_has_elif}")
                    _has_boolop_child = any(
                        isinstance(_c, BoolOpRegion) and _c.entry is _nr.entry
                        for _c in getattr(_nr, 'children', [])
                    )
                    print(f"    -> _has_boolop_child={_has_boolop_child}")
                    if not _has_cc and not _has_elif and not _has_boolop_child:
                        _nr_id = id(_nr)
                        in_generated = _nr_id in gen._generated_regions
                        in_generating = _nr_id in gen._generating_regions
                        print(f"    -> _nr_id={_nr_id}, in_generated_regions={in_generated}, in_generating_regions={in_generating}")
                        _nr_blocks_in_set = all(_nb in _block_set for _nb in _nr.blocks)
                        print(f"    -> _nr.blocks={[b.start_offset for b in _nr.blocks]}, all_in_block_set={_nr_blocks_in_set}")

        result = original_process(blocks, region, branch)
        print(f"  RESULT: {[s.get('type') if isinstance(s, dict) else type(s).__name__ for s in result]}")
        return result
    gen._process_if_blocks = traced_process

    # Monkey-patch _generate_region
    original_gen_region = gen._generate_region
    def traced_gen_region(region, skip_store_targets=None):
        print(f"\n[_generate_region] region={type(region).__name__}@{region.entry.start_offset if region.entry else None}")
        result = original_gen_region(region, skip_store_targets)
        if isinstance(result, list):
            print(f"  RESULT: list of {len(result)} items: {[s.get('type') if isinstance(s, dict) else type(s).__name__ for s in result]}")
        elif isinstance(result, dict):
            print(f"  RESULT: {result.get('type')}")
        else:
            print(f"  RESULT: {type(result).__name__}")
        return result
    gen._generate_region = traced_gen_region

    # 调用生成
    print("=== 开始生成 ===")
    ast = gen._generate_region(outer)
    print(f"\n=== 最终结果 ===")
    if isinstance(ast, list):
        for s in ast:
            print(s)
    else:
        print(ast)


if __name__ == '__main__':
    main()
