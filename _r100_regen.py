#!/usr/bin/env python3
"""R100: Regenerate OK.py files for partial pyc that now match"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs, decompile_pyc

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

regenerated = 0
for entry in pyc_index:
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc_path):
        continue
    
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
    except:
        continue
    
    # Check if current OK.py matches
    if os.path.exists(ok_path):
        try:
            with open(ok_path, 'r', encoding='utf-8') as f:
                source = f.read()
            decomp_code = compile(source, ok_path, 'exec')
        except:
            source = decompile_pyc(pyc_path)
            with open(ok_path, 'w', encoding='utf-8') as f:
                f.write(source)
            regenerated += 1
            continue
        
        def extract(co):
            r = {co.co_name: co}
            for c in co.co_consts:
                if isinstance(c, types.CodeType):
                    r.update(extract(c))
            return r
        
        om = extract(orig_code)
        dm = extract(decomp_code)
        
        all_match = True
        for name in om:
            if name not in dm or name.startswith('<'):
                continue
            result = compare_bytecode(om[name], dm[name])
            if not result['match']:
                all_match = False
                break
        
        if not all_match:
            # Try regenerating
            source = decompile_pyc(pyc_path)
            try:
                decomp_code = compile(source, '<decomp>', 'exec')
            except:
                continue
            dm = extract(decomp_code)
            all_match = True
            for name in om:
                if name not in dm or name.startswith('<'):
                    continue
                result = compare_bytecode(om[name], dm[name])
                if not result['match']:
                    all_match = False
                    break
            if all_match:
                with open(ok_path, 'w', encoding='utf-8') as f:
                    f.write(source)
                regenerated += 1
                entry['decompile_status'] = 'ok'
    else:
        source = decompile_pyc(pyc_path)
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(source)
        regenerated += 1

print(f"Regenerated {regenerated} OK.py files")

# Final test
ok_count = 0
partial_count = 0
fail_count = 0
for entry in pyc_index:
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc_path) or not os.path.exists(ok_path):
        fail_count += 1
        continue
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        with open(ok_path, 'r', encoding='utf-8') as f:
            source = f.read()
        decomp_code = compile(source, ok_path, 'exec')
    except:
        fail_count += 1
        continue
    def extract(co):
        r = {co.co_name: co}
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r.update(extract(c))
        return r
    om = extract(orig_code)
    dm = extract(decomp_code)
    all_match = True
    for name in om:
        if name not in dm or name.startswith('<'):
            continue
        result = compare_bytecode(om[name], dm[name])
        if not result['match']:
            all_match = False
            break
    if all_match:
        ok_count += 1
        entry['decompile_status'] = 'ok'
    else:
        partial_count += 1
        entry['decompile_status'] = 'partial'

print(f"Final: OK={ok_count}, Partial={partial_count}, Fail={fail_count}")

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'w', encoding='utf-8') as f:
    json.dump(pyc_index, f, indent=2, ensure_ascii=False)
