"""Disassemble _close_holding and make_trade to understand the pass issue."""
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

# Show make_trade first 60 instructions
target = all_codes.get('make_trade')
if target:
    print(f"=== make_trade (first 80 instructions) ===")
    print(f"co_varnames: {target.co_varnames}")
    print(f"co_names: {target.co_names}")
    instrs = list(dis.get_instructions(target))
    for i, ins in enumerate(instrs[:80]):
        print(f"  {i:3d}  {ins.offset:4d}  {ins.opname:30s}  {ins.argrepr}")
