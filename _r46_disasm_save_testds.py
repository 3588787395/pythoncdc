import dis, marshal, types, sys
sys.path.insert(0, '.')

# Load original pyc
with open('site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find save_testds_to_json
def find_code(code_obj, name, prefix=''):
    result = {}
    n = code_obj.co_name or '<module>'
    result[n] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(find_code(const, name, prefix + n + '.'))
    return result

all_codes = find_code(code, '')
target = all_codes.get('save_testds_to_json')
if target:
    print(f"=== save_testds_to_json ===")
    print(f"co_varnames: {target.co_varnames}")
    print(f"co_freevars: {target.co_freevars}")
    print(f"co_cellvars: {target.co_cellvars}")
    print(f"co_names: {target.co_names}")
    print(f"co_consts (non-code): {[c for c in target.co_consts if not isinstance(c, types.CodeType)]}")
    print(f"co_consts (code): {[c.co_name for c in target.co_consts if isinstance(c, types.CodeType)]}")
    print(f"\nInstructions ({len(target.co_code)//2}):")
    dis.dis(target)
else:
    print("save_testds_to_json not found")
    print("Available:", list(all_codes.keys()))
