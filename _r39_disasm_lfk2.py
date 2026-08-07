import sys, marshal, dis, types, io
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_and_disasm(code, name, path=''):
    if code.co_name == name:
        print(f"=== Found {name} at {path} ===")
        print(f"co_varnames: {code.co_varnames}")
        print(f"co_consts (non-code): {[c for c in code.co_consts if not hasattr(c, 'co_code')][:20]}")
        buf = io.StringIO()
        dis.dis(code, file=buf)
        print(buf.getvalue())
        return True
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if find_and_disasm(c, name, f"{path}.{c.co_name}"):
                return True
    return False

find_and_disasm(code, 'load_from_kwargs')
