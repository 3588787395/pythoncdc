import dis, marshal, types

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'handle_exrights':
        print(f"=== handle_exrights (offset 0) ===")
        dis.dis(const)
