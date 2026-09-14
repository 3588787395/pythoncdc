import marshal, types, dis, sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_system_persist\__init__.pyc'
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

func = find_func(code, 'setup')
instrs = list(dis.get_instructions(func))

# Find around index 79 (first_diff area)
# first_diff: orig=JUMP_FORWARD(630) decomp=LOAD_GLOBAL(os)
# That means at some point, the original has JUMP_FORWARD while decompiled has LOAD_GLOBAL
# Let's look at the original around the JUMP_FORWARD

# Find all JUMP_FORWARD instructions
for i, instr in enumerate(instrs):
    if instr.opname == 'JUMP_FORWARD' and instr.offset < 700:
        print(f"  {i:4d}: {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
