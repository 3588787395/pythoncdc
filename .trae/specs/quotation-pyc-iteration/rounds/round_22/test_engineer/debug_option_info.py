"""R22 测试工程师：分析 get_option_info 的 match-case 结构回归问题。"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, BoolOpRegion, IfRegion

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
    co = pyc_codes['get_option_info']

    print("=== get_option_info bytecode (match-case area) ===")
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")

    print(f"\n=== CFG blocks ===")
    builder = CFGBuilder()
    cfg = builder.build(co)
    for b in cfg.get_blocks_in_order():
        print(f"  Block {b.id} (offset {b.start_offset}-{b.end_offset}):")
        for ins in b.instructions:
            print(f"    {ins.offset:4d}  {ins.opname:30s} {ins.argval!r}")
        print(f"    successors: {[s.id for s in b.successors]}")
        print(f"    exception_successors: {[s.id for s in b.exception_successors]}")

    print(f"\n=== Region Analysis ===")
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    for r in regions:
        print(f"  Region: {type(r).__name__}, entry={r.entry.id}")
        if hasattr(r, 'try_blocks'):
            print(f"    try_blocks={[b.id for b in r.try_blocks]}")
        if hasattr(r, 'then_blocks'):
            print(f"    then_blocks={[b.id for b in r.then_blocks]}")
            print(f"    else_blocks={[b.id for b in (r.else_blocks or [])]}")
            print(f"    merge_block={r.merge_block.id if r.merge_block else None}")
        if hasattr(r, 'case_blocks'):
            print(f"    case_blocks={[b.id for b in r.case_blocks]}")
        if hasattr(r, 'blocks'):
            print(f"    all blocks={[b.id for b in r.blocks]}")
        if hasattr(r, 'op_chain'):
            print(f"    op_chain={[(b.id, op) for b, op in r.op_chain]}")


if __name__ == '__main__':
    main()
