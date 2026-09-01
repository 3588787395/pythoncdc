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

orig_code = _load_pyc_code('site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc')
orig_map = _extract_code_objects(orig_code)

code = orig_map['<module>.PluginRiskCalculation.get_daily_summary']
instrs = list(dis.get_instructions(code))

# Show around position 480-530 (filtered)
for i, instr in enumerate(instrs):
    if 480 <= i <= 530:
        print("  %3d %04d %s %s %s" % (i, instr.offset, instr.opname, instr.argval, instr.argrepr))
