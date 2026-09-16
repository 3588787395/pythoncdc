import sys, os, traceback
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

try:
    from core.cfg.cfg_builder import ControlFlowGraph
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.region_analyzer import BoolOpRegion, IfRegion
    import marshal

    pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
    with open(pyc, 'rb') as f:
        f.read(16)
        code = marshal.load(f)

    for const in code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'handle_exrights':
            code = const
            break

    cfg = ControlFlowGraph(code)
    generator = RegionASTGenerator(cfg)
    regions = generator.region_analyzer.analyze()

    results = []
    results.append(f"Total regions: {len(regions)}")
    for r in regions:
        if isinstance(r, BoolOpRegion):
            info = f"BoolOpRegion: entry={r.entry.start_offset if r.entry else None}, op_chain={[(b.start_offset, op) for b, op in r.op_chain]}, merge={r.merge_block.start_offset if r.merge_block else None}"
            results.append(info)
            if r.op_chain:
                for b, op in r.op_chain:
                    last = b.get_last_instruction()
                    info2 = f"  block@{b.start_offset}: last_instr={last.opname if last else None}, op={op}"
                    results.append(info2)
                    for i in b.instructions:
                        results.append(f"    {i.offset}: {i.opname} {getattr(i, 'argval', '')}")

        if isinstance(r, IfRegion):
            info = f"IfRegion: entry={r.entry.start_offset if r.entry else None}, cond={r.condition_block.start_offset if r.condition_block else None}, then={[b.start_offset for b in r.then_blocks]}, else={[b.start_offset for b in r.else_blocks]}"
            results.append(info)

    with open('d_temp/debug_out.txt', 'w') as f:
        f.write('\n'.join(results))
except Exception as e:
    with open('d_temp/debug_out.txt', 'w') as f:
        f.write(f"ERROR: {e}\n{traceback.format_exc()}")
