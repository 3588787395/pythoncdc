import marshal, dis, types

def _load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def _extract_code_objects(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    result[key] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(_extract_code_objects(const, prefix + code.co_name + '.'))
    return result

orig_code = _load_pyc_code('site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc')
orig_map = _extract_code_objects(orig_code)

for name, code in sorted(orig_map.items()):
    if 'get_daily_summary' not in name:
        continue
    print("=== ORIG %s ===" % name)
    instrs = list(dis.get_instructions(code))
    # Find the POP_JUMP around the benchmark_portfolio check
    for i, instr in enumerate(instrs):
        if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE' and i > 0:
            prev_instrs = [instrs[j].opname for j in range(max(0,i-3), i)]
            if 'benchmark_portfolio' in str(instrs[i-1].argrepr):
                for j in range(max(0,i-3), min(len(instrs), i+5)):
                    print("  %3d %s %s %s" % (j, instrs[j].opname, instrs[j].argval, instrs[j].argrepr))
