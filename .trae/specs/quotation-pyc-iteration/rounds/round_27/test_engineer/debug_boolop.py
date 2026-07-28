"""R27 测试工程师：调试ctx_02案例的BoolOpRegion检测，找出为什么AND链未被识别"""
import os
import sys
import dis
import py_compile

sys.path.insert(0, '/workspace')

OUT_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_27/test_engineer/minimal_repros'

# ctx_02: if-elif链后有代码 -> FAIL
SRC_CTX02 = '''def f(start_year, end_year, params):
    if start_year is not None and end_year is None:
        params['start_year'] = start_year
    elif start_year is None and end_year is not None:
        params['end_year'] = end_year
    elif start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
    x = 1
'''

# ctx_00: 纯if-elif链 -> PASS
SRC_CTX00 = '''def f(start_year, end_year, params):
    if start_year is not None and end_year is None:
        params['start_year'] = start_year
    elif start_year is None and end_year is not None:
        params['end_year'] = end_year
    elif start_year is not None and end_year is not None:
        params['start_year'] = start_year
        params['end_year'] = end_year
'''


def debug_case(name, src):
    print(f"\n{'='*80}\n=== {name} ===\n{'='*80}")
    src_path = os.path.join(OUT_DIR, f'debug_{name}.py')
    pyc_path = os.path.join(OUT_DIR, f'debug_{name}.pyc')
    with open(src_path, 'w', encoding='utf-8') as f:
        f.write(src)
    py_compile.compile(src_path, pyc_path, doraise=True)

    # 加载pyc并构建CFG
    from core.pyc_loader_v2 import load_pyc_file_v2
    from core.cfg.cfg_builder import CFGBuilder

    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # 找到f函数的code object
    f_co = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'f':
            f_co = const
            break

    print(f"Function: {f_co.co_name}")
    print(f"\n--- Bytecode ---")
    for ins in dis.get_instructions(f_co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")

    # 构建CFG
    builder = CFGBuilder()
    cfg = builder.build(f_co)

    print(f"\n--- CFG Blocks ---")
    for blk in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
        last = blk.get_last_instruction()
        last_str = f"{last.opname} → {last.argval}" if last else "None"
        succs = [s.start_offset for s in blk.successors]
        print(f"  Block@{blk.start_offset:>3} last={last_str:<45} succs={succs}")

    # 运行区域分析
    from core.cfg.region_analyzer import RegionAnalyzer
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    print(f"\n--- Regions ({len(regions)}) ---")
    for r in regions:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={[b.start_offset for b in r.blocks]}")
        if hasattr(r, 'op_chain'):
            print(f"    op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
        if hasattr(r, 'then_blocks'):
            print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
        if hasattr(r, 'else_blocks'):
            print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"    merge_block={r.merge_block.start_offset}")


def main():
    debug_case('ctx00', SRC_CTX00)
    debug_case('ctx02', SRC_CTX02)


if __name__ == '__main__':
    main()
