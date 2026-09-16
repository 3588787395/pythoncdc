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
    results = []
    results.append(f"CFG blocks: {len(cfg.blocks)}")
    for b in cfg.blocks:
        last = b.get_last_instruction()
        results.append(f"  Block@{b.start_offset}: last={last.opname if last else None}, succs={[s.start_offset for s in b.successors]}")
        for i in b.instructions[:5]:
            results.append(f"    {i.offset}: {i.opname} {getattr(i, 'argval', '')}")
        if len(b.instructions) > 5:
            results.append(f"    ... ({len(b.instructions)} total)")

    with open('d_temp/debug_out.txt', 'w') as f:
        f.write('\n'.join(results))
except Exception as e:
    with open('d_temp/debug_out.txt', 'w') as f:
        f.write(f"ERROR: {e}\n{traceback.format_exc()}")
