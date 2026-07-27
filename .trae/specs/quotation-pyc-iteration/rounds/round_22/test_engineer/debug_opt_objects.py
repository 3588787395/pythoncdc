"""R22 测试工程师：详细分析 get_opt_objects 的 try-except 结构问题。
pyc 中 try 体的首条语句是 check_datetime(date)，但反编译生成 strategy_log.error(...)。
"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

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

    print("=== get_opt_objects bytecode (full) ===")
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")

    print(f"\nco_varnames={co.co_varnames}")
    print(f"co_names={co.co_names}")
    print(f"co_consts={co.co_consts}")
    print(f"co_exceptiontable:")
    if hasattr(co, 'co_exceptiontable'):
        et = co.co_exceptiontable
        print(f"  raw bytes: {et!r}")
    # Print exception table via dis
    print(f"\nException table (parsed):")
    try:
        for entry in dis.Bytecode(co).exception_table:
            print(f"  start={entry.start} end={entry.end} lasti={entry.lasti} "
                  f"handler={entry.target} depth={entry.depth} lasti_flag={entry.lasti}")
    except Exception as e:
        print(f"  (error: {e})")

    # Build CFG and analyze regions
    print(f"\n=== CFG blocks ===")
    builder = CFGBuilder()
    cfg = builder.build(co)
    for b in cfg.get_blocks_in_order():
        print(f"  Block {b.id} (offset {b.start_offset}-{b.end_offset}):")
        for ins in b.instructions:
            print(f"    {ins.offset:4d}  {ins.opname:30s} {ins.argval!r}")
        print(f"    successors: {[s.id for s in b.successors]}")
        print(f"    exception_successors: {[s.id for s in b.exception_successors]}")

    # Analyze regions
    print(f"\n=== Region Analysis ===")
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    for r in regions:
        print(f"  Region: {type(r).__name__}, entry={r.entry.id}")
        if hasattr(r, 'try_blocks'):
            print(f"    try_blocks={[b.id for b in r.try_blocks]}")
            print(f"    handler_entry_blocks={[b.id for b in r.handler_entry_blocks]}")
            for attr in ('handler_type', 'else_blocks', 'finally_blocks'):
                if hasattr(r, attr):
                    v = getattr(r, attr)
                    if v:
                        print(f"    {attr}={v}")
        if hasattr(r, 'then_blocks'):
            print(f"    then_blocks={[b.id for b in r.then_blocks]}")
            print(f"    else_blocks={[b.id for b in (r.else_blocks or [])]}")
            print(f"    merge_block={r.merge_block.id if r.merge_block else None}")
        if hasattr(r, 'body_blocks'):
            print(f"    body_blocks={[b.id for b in r.body_blocks]}")
        if hasattr(r, 'condition_blocks'):
            print(f"    condition_blocks={[b.id for b in r.condition_blocks]}")
        # Print all blocks
        if hasattr(r, 'blocks'):
            print(f"    all blocks={[b.id for b in r.blocks]}")
        # BoolOpRegion specific
        if hasattr(r, 'op_chain'):
            print(f"    op_chain={[(b.id, op) for b, op in r.op_chain]}")
            print(f"    is_condition_context={getattr(r, 'is_condition_context', 'N/A')}")
            print(f"    merge_block={r.merge_block.id if r.merge_block else None}")
            print(f"    value_target={getattr(r, 'value_target', 'N/A')}")

    # Print block_to_region mapping
    print(f"\n=== block_to_region mapping ===")
    for b in cfg.get_blocks_in_order():
        r = analyzer.block_to_region.get(b)
        if r is not None:
            print(f"  Block {b.id} -> {type(r).__name__}(entry={r.entry.id})")
        else:
            print(f"  Block {b.id} -> None")


if __name__ == '__main__':
    main()
