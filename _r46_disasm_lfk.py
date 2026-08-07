"""Disassemble load_from_kwargs to understand the for-else pattern."""
import dis, marshal, types, sys
sys.path.insert(0, '.')

with open('site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    result = {}
    n = code_obj.co_name or '<module>'
    result[n] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(find_code(const, name))
    return result

all_codes = find_code(code, '')
target = all_codes.get('load_from_kwargs')
if target:
    print(f"=== load_from_kwargs ===")
    print(f"co_varnames: {target.co_varnames}")
    print(f"co_freevars: {target.co_freevars}")
    print(f"co_cellvars: {target.co_cellvars}")
    print(f"co_names: {target.co_names}")
    print(f"\nInstructions:")
    dis.dis(target)
