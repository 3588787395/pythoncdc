import sys, types, marshal
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

pyc_path = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
code = orig_map['create_orders_stats']

cfg = build_cfg(code)

for off in sorted(cfg.blocks.keys()):
    if 900 <= off <= 1000:
        b = cfg.blocks[off]
        last = b.get_last_instruction()
        last_str = '%s %s' % (last.opname, last.argval) if last else 'None'
        succs = [s.start_offset for s in b.successors]
        instrs = []
        for instr in b.instructions:
            if instr.argrepr:
                instrs.append('%s(%s)' % (instr.opname, instr.argrepr))
            else:
                instrs.append(instr.opname)
        print('Block@%d: [%s] succs=%s' % (off, ' | '.join(instrs), succs))
