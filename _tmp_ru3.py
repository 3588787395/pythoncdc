import marshal, types, dis

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\util\replace_utils.pyc'
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    f.read(8)
    code = marshal.load(f)

def find_func(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_func(const, name)
            if r: return r
    return None

func = find_func(code, 'decrypt_database_url')
for instr in dis.get_instructions(func):
    if 420 <= instr.offset <= 450:
        print(f"{instr.offset:4d} {instr.opname:30s} arg={instr.arg} argrepr={instr.argrepr}")
