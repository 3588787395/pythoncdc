import sys, types, marshal, dis
sys.path.insert(0, '.')

pyc_path = 'site-packages/IQData/plugins/plugin_system_db/iqdata_db_base.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Find the BaseDatabase class code object
def find_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            result.update(find_code_objects(const, child_name))
    return result

code_map = find_code_objects(orig_code)

# Show the BaseDatabase class body bytecode
for name, code in sorted(code_map.items()):
    if name == 'BaseDatabase':
        print(f"=== {name} class body bytecode ===")
        instrs = list(dis.get_instructions(code))
        for instr in instrs:
            if 'load_table' in str(instr.argval) or 'load_view' in str(instr.argval) or 'STORE_NAME' in instr.opname or 'MAKE_FUNCTION' in instr.opname:
                print(f"  {instr.offset:4d} {instr.opname:25s} {instr.argval}")
        
        # Show all co_consts names
        print(f"\n  co_consts code object names:")
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                print(f"    {const.co_name}")
        break

# Also show how __load_table_names is called (LOAD_ATTR)
print("\n=== LOAD_ATTR with mangled names ===")
for name, code in sorted(code_map.items()):
    instrs = list(dis.get_instructions(code))
    for instr in instrs:
        if instr.opname in ('LOAD_ATTR', 'LOAD_METHOD', 'STORE_ATTR') and '__load_table' in str(instr.argval):
            print(f"  {name}: {instr.opname} {instr.argval}")
