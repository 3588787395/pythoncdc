import sys, os, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc_path = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
ok_path = pyc_path.replace('.pyc', 'OK.py')

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

import py_compile
cfile = py_compile.compile(ok_path, doraise=True, quiet=2)
if cfile is None:
    import importlib.util
    cfile = importlib.util.cache_from_source(ok_path)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

from testqouter.round1.base import compare_bytecode

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

for name in ['create_orders_stats', 'create_transactions_stats', 'save_testds_to_json']:
    if name in orig_map and name in decomp_map:
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            print(f"\n{'='*80}")
            print(f"MISMATCH: {name}")
            print(f"  orig_count={cmp.get('orig_count')}, decomp_count={cmp.get('decomp_count')}")
            
            true_diffs = cmp.get('true_diffs', [])
            print(f"\n  true_diffs ({len(true_diffs)} total, showing first 15):")
            for td in true_diffs[:15]:
                print(f"    {td}")
            
            jump_diffs = cmp.get('jump_diffs', [])
            print(f"\n  jump_diffs ({len(jump_diffs)} total):")
            for jd in jump_diffs:
                print(f"    {jd}")
            
            print(f"\n  --- ORIGINAL bytecode ---")
            orig_instrs = list(dis.get_instructions(orig_map[name]))
            for i in orig_instrs:
                arg_str = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                print(f"    {i.offset:4d} {i.opname:35s} {arg_str}")
            
            print(f"\n  --- DECOMPILED bytecode ---")
            decomp_instrs = list(dis.get_instructions(decomp_map[name]))
            for i in decomp_instrs:
                arg_str = f'{i.arg} ({i.argrepr})' if i.arg is not None and i.argrepr else (str(i.arg) if i.arg is not None else '')
                print(f"    {i.offset:4d} {i.opname:35s} {arg_str}")
            
            print(f"\n  --- Decompiled source ---")
            with open(ok_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            in_func = False
            func_lines = []
            for line in lines:
                stripped = line.strip()
                if f'def {name}' in stripped:
                    in_func = True
                    func_lines.append(line.rstrip())
                    continue
                if in_func:
                    current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
                    def_indent = len(func_lines[0]) - len(func_lines[0].lstrip()) if func_lines else 0
                    if stripped and current_indent <= def_indent and func_lines:
                        break
                    func_lines.append(line.rstrip())
            for fl in func_lines[:80]:
                print(f"    {fl}")
            if len(func_lines) > 80:
                print(f"    ... ({len(func_lines)} total lines)")
