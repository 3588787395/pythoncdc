"""R22 测试工程师：trace IfRegion creation for block 11 in get_opt_objects.
Monkey-patch _build_basic_if_region and _build_elif_region to log inputs/outputs.
"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TryExceptRegion, Region

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
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
    co = pyc_codes['get_opt_objects']

    builder = CFGBuilder()
    cfg = builder.build(co)

    analyzer = RegionAnalyzer(cfg)

    # Monkey-patch _build_basic_if_region and _build_elif_region
    orig_build_basic = analyzer._build_basic_if_region
    orig_build_elif = analyzer._build_elif_region
    orig_identify_cond = analyzer._identify_conditional_regions

    def patched_build_basic(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, **kwargs):
        result = orig_build_basic(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **kwargs)
        print(f"  [_build_basic_if_region] block={block.id}, then={[b.id for b in then_blocks]}, "
              f"else={[b.id for b in else_blocks]}, merge={merge.id if merge else None}, "
              f"cond_block={condition_block.id if condition_block else None} -> "
              f"{'IfRegion(entry='+str(result.entry.id)+')' if result else 'None'}")
        return result

    def patched_build_elif(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, **kwargs):
        result = orig_build_elif(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, **kwargs)
        print(f"  [_build_elif_region] block={block.id}, then={[b.id for b in then_blocks]}, "
              f"else={[b.id for b in else_blocks]}, merge={merge.id if merge else None}, "
              f"cond_block={condition_block.id if condition_block else None} -> "
              f"{'IfRegion(entry='+str(result.entry.id)+')' if result else 'None'}")
        return result

    def patched_identify_cond(*args, **kwargs):
        print("=== _identify_conditional_regions START ===")
        # Temporarily patch the build methods
        analyzer._build_basic_if_region = patched_build_basic
        analyzer._build_elif_region = patched_build_elif
        result = orig_identify_cond(*args, **kwargs)
        print(f"=== _identify_conditional_regions END: {len(result)} IfRegions created ===")
        for r in result:
            print(f"  IfRegion entry={r.entry.id}, then={[b.id for b in r.then_blocks]}, "
                  f"else={[b.id for b in (r.else_blocks or [])]}, "
                  f"merge={r.merge_block.id if r.merge_block else None}")
        # Restore
        analyzer._build_basic_if_region = orig_build_basic
        analyzer._build_elif_region = orig_build_elif
        return result

    analyzer._identify_conditional_regions = patched_identify_cond

    # Also patch _should_skip_block_for_if_region to see if block 11 is skipped
    orig_skip = analyzer._should_skip_block_for_if_region
    def patched_skip(block, block_region, loop_regions, last_instr):
        result = orig_skip(block, block_region, loop_regions, last_instr)
        if block.start_offset == 164:  # block 11
            print(f"  [_should_skip] block={block.id} (offset 164), "
                  f"block_region={type(block_region).__name__}, skip={result}")
        return result
    analyzer._should_skip_block_for_if_region = patched_skip

    # Patch the main loop to trace block 11 processing
    # We need to trace what happens at the conditional check for block 11
    print("=== Running region analysis ===")
    regions = analyzer.analyze()

    print(f"\n=== Final regions ===")
    for r in regions:
        print(f"  {type(r).__name__}, entry={r.entry.id}")


if __name__ == '__main__':
    main()
