import dis, marshal, py_compile, sys

def dump(path, label):
    print(f"=== {label}: {path} ===")
    if path.endswith('.py'):
        out = r'F:/Downloads/pythoncdc-main/_r05_compiled.pyc'
        py_compile.compile(path, out, doraise=True)
        path = out
    f = open(path, 'rb')
    f.read(16)
    code = marshal.load(f)
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            print(f'--- {c.co_name} ---')
            for i, ins in enumerate(dis.get_instructions(c)):
                print(f'{i:4d} {ins.offset:4d} {ins.opname:30s} {ins.argrepr}')

dump(r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/base_storage.pyc', 'ORIG PYC')
print()
dump(r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/base_storageOK.py', 'DECOMP OK.py')
