import json, sys, os, marshal, types, dis
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
import py_compile, importlib.util

with open(r'F:\Downloads\pythoncdc-main\pyc_index.json', 'r') as f:
    data = json.load(f)

for entry in data:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            code = marshal.load(f)
        
        source = decompile_pyc(pyc_path)
        ok_path = pyc_path.replace('.pyc', 'OK.py')
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(source)
        
        py_compile.compile(ok_path, doraise=True, quiet=2)
        cfile = importlib.util.cache_from_source(ok_path)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
        
        def get_func_map(code_obj):
            result = {}
            for const in code_obj.co_consts:
                if isinstance(const, types.CodeType):
                    result[const.co_name] = const
                    result.update(get_func_map(const))
            return result
        
        orig_map = get_func_map(code)
        decomp_map = get_func_map(decomp_code)
        
        # Check each mismatched function for co_names/co_varnames differences
        short_name = pyc_path.split('site-packages/')[-1]
        for name in orig_map:
            if name not in decomp_map:
                continue
            o = orig_map[name]
            d = decomp_map[name]
            
            # Compare bytecode
            o_instrs = list(dis.get_instructions(o))
            d_instrs = list(dis.get_instructions(d))
            if len(o_instrs) != len(d_instrs):
                continue
            
            # Check if ONLY co_names/co_varnames differ
            names_diff = (o.co_names != d.co_names)
            varnames_diff = (o.co_varnames != d.co_varnames)
            
            if names_diff or varnames_diff:
                # Check if bytecode is identical when ignoring arg values
                all_same_ops = True
                for i in range(len(o_instrs)):
                    if o_instrs[i].opname != d_instrs[i].opname:
                        all_same_ops = False
                        break
                
                if all_same_ops:
                    diff_type = []
                    if names_diff:
                        diff_type.append(f"co_names: orig={o.co_names[:5]}... decomp={d.co_names[:5]}...")
                    if varnames_diff:
                        diff_type.append(f"co_varnames: orig={o.co_varnames[:5]}... decomp={d.co_varnames[:5]}...")
                    print(f"{short_name} :: {name}: ONLY {', '.join(diff_type)}")
    except Exception:
        pass
