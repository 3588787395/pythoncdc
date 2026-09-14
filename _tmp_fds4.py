import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQData\plugins\plugin_system_local_finance\finance_data_source.pyc'
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

func = find_func(code, 'growth_factors_sql_get')
instrs = list(dis.get_instructions(func))

for i, instr in enumerate(instrs):
    if 2080 <= instr.offset <= 2140:
        print(f"  {i:4d}: {instr.offset:4d} {instr.opname:25s} {instr.argrepr}")
