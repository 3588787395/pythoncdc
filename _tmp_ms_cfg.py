import dis, marshal

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\data\merger_storage.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code, name):
    if hasattr(code, 'co_name') and code.co_name == name: return code
    for c in getattr(code, 'co_consts', []):
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r: return r
    return None

cls = find_code(code, 'MergerStorage')
func = find_code(cls, 'get_merger_date_info')

for instr in dis.get_instructions(func):
    if 46 <= instr.offset <= 60:
        print(f"offset={instr.offset:4d} {instr.opname:30s} {instr.argval if instr.argval is not None else ''}"[:100])
