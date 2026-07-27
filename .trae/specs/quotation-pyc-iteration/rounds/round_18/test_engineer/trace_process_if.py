"""R18: 追踪 _process_if_blocks 调用"""
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

    # Patch _process_if_blocks
    orig = RegionASTGenerator._process_if_blocks
    def traced(self, blocks, region, branch='then'):
        if region and hasattr(region, 'entry') and region.entry and region.entry.start_offset == 0:
            print(f"\n[_process_if_blocks] branch={branch}, blocks={[b.start_offset for b in blocks]}")
            print(f"  child_region_blocks={set(b.start_offset for b in self._tmp_crb)}" if hasattr(self, '_tmp_crb') else "")
        result = orig(self, blocks, region, branch)
        if region and hasattr(region, 'entry') and region.entry and region.entry.start_offset == 0:
            print(f"[_process_if_blocks] => {len(result)} stmts\n")
        return result
    RegionASTGenerator._process_if_blocks = traced

    # Patch _generate_region
    orig_gen = RegionASTGenerator._generate_region
    def traced_gen(self, region):
        rtype = type(region).__name__
        entry_off = region.entry.start_offset if hasattr(region, 'entry') and region.entry else '?'
        print(f"  [_generate_region] {rtype}(entry={entry_off})")
        result = orig_gen(self, region)
        print(f"  [_generate_region] {rtype}(entry={entry_off}) done")
        return result
    RegionASTGenerator._generate_region = traced_gen

    # Patch _generate_block_statements
    orig_blk = RegionASTGenerator._generate_block_statements
    def traced_blk(self, block, _cjb_parent=None):
        print(f"    [_gen_block] block={block.start_offset}")
        result = orig_blk(self, block, _cjb_parent)
        print(f"    [_gen_block] block={block.start_offset} => {len(result)} stmts")
        return result
    RegionASTGenerator._generate_block_statements = traced_blk

    # Patch get_entry_region_for_block to trace
    orig_get_entry = RegionAnalyzer.get_entry_region_for_block
    def traced_get_entry(self, block):
        result = orig_get_entry(self, block)
        if block.start_offset in (164, 270, 312, 314):
            print(f"      [get_entry_region_for_block({block.start_offset})] => {type(result).__name__ if result else None}")
        return result
    RegionAnalyzer.get_entry_region_for_block = traced_get_entry

    gen = RegionASTGenerator(cfg, ra)
    result = gen.generate()


if __name__ == '__main__':
    main()
