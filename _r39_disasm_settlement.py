import sys, types, marshal, io, dis
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_accounts/account_model/future_account.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_and_disasm(code, name, path=''):
    if code.co_name == name:
        print(f"=== Found {name} at {path} ===")
        print(f"co_varnames: {code.co_varnames}")
        print(f"co_argcount: {code.co_argcount}")
        buf = io.StringIO()
        dis.dis(code, file=buf)
        lines = buf.getvalue().split('\n')
        for line in lines[:60]:
            print(line)
        return True
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if find_and_disasm(c, name, f"{path}.{c.co_name}"):
                return True
    return False

find_and_disasm(code, '_on_settlement')
