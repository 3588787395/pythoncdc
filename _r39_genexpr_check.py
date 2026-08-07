import sys, os, types, marshal, json
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, decompile_pyc as base_decompile

# Read pyc_index.json
with open('pyc_index.json', 'r') as f:
    index = json.load(f)

# Count files with genexpr mismatch pattern
genexpr_mismatch_count = 0
total_checked = 0

for entry in index:
    pyc_path = entry.get('path', '')
    if not pyc_path.endswith('.pyc'):
        continue
    if not os.path.exists(pyc_path):
        continue
    
    status = entry.get('decompile_status', '')
    if status != 'partial':
        continue
    
    total_checked += 1
    
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        
        source = base_decompile(pyc_path)
        decomp_code = compile(source, '<decompiled>', 'exec')
        
        # Check all nested code objects for genexpr
        def check_genexprs(code, decomp_code_obj):
            global genexpr_mismatch_count
            for c in code.co_consts:
                if isinstance(c, types.CodeType):
                    if '<genexpr>' in c.co_name:
                        # Find matching genexpr in decompiled
                        for dc in decomp_code_obj.co_consts:
                            if isinstance(dc, types.CodeType) and dc.co_name == c.co_name:
                                result = compare_bytecode(c, dc)
                                if not result['match']:
                                    # Check if the only diff is FORWARD vs BACKWARD
                                    oo = result['orig_ops']
                                    do = result['decomp_ops']
                                    if len(oo) == len(do):
                                        only_jump_dir = True
                                        for i in range(len(oo)):
                                            if oo[i] != do[i]:
                                                if not (oo[i].replace('FORWARD','X') == do[i].replace('BACKWARD','X')):
                                                    only_jump_dir = False
                                                    break
                                        if only_jump_dir:
                                            genexpr_mismatch_count += 1
                                break
                    check_genexprs(c, decomp_code_obj)
            
            # Also check in decomp code for matching genexprs
            for dc in decomp_code_obj.co_consts:
                if isinstance(dc, types.CodeType):
                    if '<genexpr>' in dc.co_name:
                        # Already checked from orig side
                        pass
        
        # Find matching decomp code objects
        def find_decomp_match(orig_c, decomp_root):
            for dc in decomp_root.co_consts:
                if isinstance(dc, types.CodeType) and dc.co_name == orig_c.co_name:
                    return dc
            return None
        
        for c in orig_code.co_consts:
            if isinstance(c, types.CodeType):
                dc = find_decomp_match(c, decomp_code)
                if dc:
                    check_genexprs(c, dc)
    except Exception as e:
        pass

print(f"Checked {total_checked} partial files")
print(f"Files with genexpr FORWARD/BACKWARD mismatch: {genexpr_mismatch_count}")
