import marshal, dis, types, py_compile

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

cfile = py_compile.compile('site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__OK.py', doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

decomp_map = _extract_code_objects(decomp_code)

for name, code in sorted(decomp_map.items()):
    if 'get_daily_summary' not in name:
        continue
    print("=== DECOMP %s ===" % name)
    instrs = list(dis.get_instructions(code))
    for i, instr in enumerate(instrs):
        if 'benchmark_portfolio' in str(instr.argrepr):
            for j in range(max(0,i-3), min(len(instrs), i+6)):
                print("  %3d %s %s %s" % (j, instrs[j].opname, instrs[j].argval, instrs[j].argrepr))
            print()
