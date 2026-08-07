import sys, marshal, dis, types
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_func(code, name, path=''):
    if code.co_name == name:
        print(f"Found at {path}")
        print(f"co_varnames: {code.co_varnames}")
        print(f"co_consts (non-code): {[c for c in code.co_consts if not hasattr(c, 'co_code')][:20]}")
        dis.dis(code)
        return True
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if find_func(c, name, f"{path}.{c.co_name}"):
                return True
    return False

find_func(code, 'load_from_kwargs')
