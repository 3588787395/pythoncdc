import dis, marshal, types, importlib.util

PATH = r"F:\Downloads\pythoncdc-main\site-packages\IQCommon\data\local_finance.pyc"

with open(PATH, "rb") as f:
    header = f.read(16)
    code = marshal.load(f)

found = []
def walk(co, path):
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            name = c.co_name
            b = c.co_code
            # look for POP_JUMP_FORWARD_IF_TRUE
            import opcode
            has_true = b'\x90' in b  # 0x90 = POP_JUMP_FORWARD_IF_TRUE in 3.11? check
            found.append((path + "/" + name, c))
            walk(c, path + "/" + name)

walk(code, "<module>")

print("Total code objects:", len(found))
for name, c in found:
    if 'lambda' in name or 'company_type' in (c.co_names or ()):
        print("==== ", name, " ====")
        dis.dis(c)
