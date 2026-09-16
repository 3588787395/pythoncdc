import sys, os, types, marshal
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

from core.cfg.cfg_builder import CFGBuilder
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

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

results = []
results.append(f"Total regions: {len(analyzer.regions)}")
for r in analyzer.regions:
    rtype = type(r).__name__
    entry_off = r.entry.start_offset if r.entry else None
    results.append(f"{rtype}: entry={entry_off}")
    if isinstance(r, IfRegion):
        cond_off = r.condition_block.start_offset if r.condition_block else None
        then_offs = [b.start_offset for b in r.then_blocks]
        else_offs = [b.start_offset for b in r.else_blocks]
        merge_off = r.merge_block.start_offset if r.merge_block else None
        ibc_keys = list(r.inline_boolop_chains.keys()) if r.inline_boolop_chains else []
        results.append(f"  cond={cond_off}, then={then_offs[:5]}, else={else_offs[:5]}, merge={merge_off}")
        results.append(f"  inline_boolop_chains keys={ibc_keys}")
        results.append(f"  chained_compare_blocks={[b.start_offset for b in r.chained_compare_blocks]}")
        if r.condition_block:
            results.append(f"  cond_block instructions:")
            for i in r.condition_block.instructions:
                results.append(f"    {i.offset}: {i.opname} {getattr(i, 'argval', '')}")
    if isinstance(r, BoolOpRegion):
        chain = [(b.start_offset, op) for b, op in r.op_chain]
        merge_off = r.merge_block.start_offset if r.merge_block else None
        results.append(f"  op_chain={chain}, merge={merge_off}")
        for b, op in r.op_chain:
            last = b.get_last_instruction()
            results.append(f"    block@{b.start_offset}: last={last.opname if last else None}, op={op}")
            for i in b.instructions:
                results.append(f"      {i.offset}: {i.opname} {getattr(i, 'argval', '')}")

with open('d_temp/debug_out.txt', 'w') as f:
    f.write('\n'.join(results))
