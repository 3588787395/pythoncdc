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
        
        for name in orig_map:
            if name not in decomp_map:
                continue
            orig_instrs = list(dis.get_instructions(orig_map[name]))
            decomp_instrs = list(dis.get_instructions(decomp_map[name]))
            
            for i in range(min(len(orig_instrs), len(decomp_instrs))):
                o = orig_instrs[i]
                d = decomp_instrs[i]
                if o.opname != d.opname:
                    if 'POP_JUMP_FORWARD_IF_TRUE' in o.opname and 'POP_JUMP_FORWARD_IF_FALSE' in d.opname:
                        short_name = pyc_path.split('site-packages/')[-1]
                        print(f"{short_name} :: {name}: orig={o.opname}(to {o.argrepr}) decomp={d.opname}(to {d.argrepr}) at orig_off={o.offset}")
                    break
    except Exception:
        pass
