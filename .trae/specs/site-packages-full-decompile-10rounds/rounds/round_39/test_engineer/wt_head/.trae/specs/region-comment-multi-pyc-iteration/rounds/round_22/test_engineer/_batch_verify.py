"""R22: batch verify all pyc files after while-else fix"""
import json, os, sys, subprocess, tempfile, dis, marshal, types

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

INDEX = r'f:/Downloads/pythoncdc-main/pyc_index.json'
with open(INDEX, 'r', encoding='utf-8') as f:
    index = json.load(f)

total_funcs = 0
match_funcs = 0
ok_files = 0
partial_files = 0
failed_files = 0
syntax_error_files = 0

results = []

for entry in index:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    
    try:
        dec_src = decompile_pyc(pyc_path)
    except Exception as e:
        failed_files += 1
        results.append({'path': pyc_path, 'status': 'decompile_error', 'error': str(e)})
        continue
    
    # Save OK file
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    try:
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(dec_src)
    except:
        pass
    
    # Compile check
    try:
        compile(dec_src, '<dec>', 'exec')
    except SyntaxError:
        syntax_error_files += 1
        results.append({'path': pyc_path, 'status': 'syntax_error'})
        continue
    
    # Bytecode comparison
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    
    try:
        compiled = compile(dec_src, '<dec>', 'exec')
    except:
        partial_files += 1
        results.append({'path': pyc_path, 'status': 'compile_error'})
        continue
    
    def collect_funcs(code, out):
        out.append(code)
        for c in getattr(code, 'co_consts', []):
            if isinstance(c, types.CodeType):
                collect_funcs(c, out)
        return out
    
    orig_funcs = collect_funcs(orig_code, [])
    try:
        dec_funcs = collect_funcs(compiled, [])
    except:
        partial_files += 1
        continue
    
    file_total = 0
    file_match = 0
    
    for orig, dec in zip(orig_funcs, dec_funcs):
        file_total += 1
        total_funcs += 1
        orig_bytes = orig.co_code
        dec_bytes = dec.co_code
        if orig_bytes == dec_bytes:
            file_match += 1
            match_funcs += 1
    
    if file_total == file_match:
        ok_files += 1
        results.append({'path': pyc_path, 'status': '100%', 'total': file_total, 'match': file_match})
    elif file_match > 0:
        partial_files += 1
        results.append({'path': pyc_path, 'status': 'partial', 'total': file_total, 'match': file_match})
    else:
        failed_files += 1
        results.append({'path': pyc_path, 'status': '0%', 'total': file_total, 'match': file_match})

print(f'=== R22 Batch Verification Results ===')
print(f'Total pyc files: {len(index)}')
print(f'Processed: {len(results)}')
print(f'100% OK: {ok_files}')
print(f'Partial: {partial_files}')
print(f'Syntax error: {syntax_error_files}')
print(f'Failed: {failed_files}')
print(f'Total functions: {total_funcs}')
print(f'Matching functions: {match_funcs}')
print(f'Global match rate: {match_funcs/total_funcs*100:.2f}%' if total_funcs else 'N/A')

# Save results
out_path = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w') as f:
    json.dump({
        'ok_files': ok_files, 'partial_files': partial_files,
        'syntax_error_files': syntax_error_files, 'failed_files': failed_files,
        'total_funcs': total_funcs, 'match_funcs': match_funcs,
        'match_rate': match_funcs/total_funcs if total_funcs else 0,
        'results': results
    }, f, indent=2)
print(f'\nResults saved to {out_path}')
