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
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        results.append(f"IfRegion@0:")
        results.append(f"  cond_block={r.condition_block.start_offset if r.condition_block else None}")
        results.append(f"  inline_boolop_chains:")
        for k, v in r.inline_boolop_chains.items():
            blocks_info = [(b.start_offset, b.get_last_instruction().opname if b.get_last_instruction() else None) for b in v.get('blocks', [])]
            results.append(f"    key={k}: op={v.get('op')}, negate={v.get('negate')}, blocks={blocks_info}")
            for b in v.get('blocks', []):
                last = b.get_last_instruction()
                results.append(f"      block@{b.start_offset}: last={last.opname if last else None}")
                for i in b.instructions:
                    results.append(f"        {i.offset}: {i.opname} {getattr(i, 'argval', '')}")

with open('d_temp/debug_out.txt', 'w') as f:
    f.write('\n'.join(results))
