import sys, os, traceback, types, marshal
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

try:
    from core.cfg.cfg_builder import ControlFlowGraph
    from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

    pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
    with open(pyc, 'rb') as f:
        f.read(16)
        code = marshal.load(f)

    def extract_all(co):
        result = {}
        name = co.co_name or '<module>'
        result[name] = co
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                result.update(extract_all(c))
        return result

    all_codes = extract_all(code)
    target = all_codes.get('handle_exrights')

    cfg = ControlFlowGraph(target)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    results = []
    results.append(f"Total regions: {len(regions)}")
    results.append(f"Analyzer regions: {len(analyzer.regions)}")
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else None
        results.append(f"  {rtype}: entry={entry_off}, blocks={len(r.blocks)}")
        if isinstance(r, BoolOpRegion):
            info = f"  BoolOpRegion: op_chain={[(b.start_offset, op) for b, op in r.op_chain]}, merge={r.merge_block.start_offset if r.merge_block else None}"
            results.append(info)
            if r.op_chain:
                for b, op in r.op_chain:
                    last = b.get_last_instruction()
                    results.append(f"    block@{b.start_offset}: last={last.opname if last else None}, op={op}")
        if isinstance(r, IfRegion):
            cond_off = r.condition_block.start_offset if r.condition_block else None
            then_offs = [b.start_offset for b in r.then_blocks]
            else_offs = [b.start_offset for b in r.else_blocks]
            results.append(f"  IfRegion: cond={cond_off}, then={then_offs}, else={else_offs}")
            if r.condition_block:
                for i in r.condition_block.instructions:
                    results.append(f"    cond: {i.offset}: {i.opname} {getattr(i, 'argval', '')}")

    with open('d_temp/debug_out.txt', 'w') as f:
        f.write('\n'.join(results))
except Exception as e:
    with open('d_temp/debug_out.txt', 'w') as f:
        f.write(f"ERROR: {e}\n{traceback.format_exc()}")
