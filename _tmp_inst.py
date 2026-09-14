import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\manager\instance.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_func(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_func(const, name)
            if r: return r
    return None

func = find_func(code, '_init_config')
instrs = list(dis.get_instructions(func))

for i, instr in enumerate(instrs):
    print(f"  {i:3d}: {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
