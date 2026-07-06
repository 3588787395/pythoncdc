#!/usr/bin/env python3
"""Round2字节码验证"""
import py_compile, sys, os, json, dis, types

ROOT_DIR = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.insert(0, ROOT_DIR)

TEST_DIR = os.getcwd()
from pycdc import decompile_pyc

def is_code(obj):
    return hasattr(obj, 'co_code')

def get_instructions(code):
    result = []
    for instr in dis.get_instructions(code):
        av = instr.argval
        if instr.opname == 'LOAD_CONST' and is_code(av):
            av = '<code>'
        result.append((instr.opname, av))
    return result

def compare_bytecode(orig_insts, decomp_insts):
    jdiff, tdiff = 0, 0
    for i in range(min(len(orig_insts), len(decomp_insts))):
        o = orig_insts[i]; d = decomp_insts[i]
        if o == d:
            continue
        if 'JUMP' in o[0] or 'JUMP' in d[0]:
            jdiff += 1
        else:
            tdiff += 1
    return jdiff, tdiff

results = []
total, passed, failed, syntax_err, decomp_err = 0, 0, 0, 0, 0

files = sorted([f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')])

for f in files:
    total += 1
    name = f[:-3]
    py_path = os.path.join(TEST_DIR, f)
    pyc_path = os.path.join(TEST_DIR, f + 'c')
    
    try:
        py_compile.compile(py_path, cfile=pyc_path, doraise=True)
        
        try:
            src = decompile_pyc(pyc_path)
        except Exception as e:
            decomp_err += 1
            results.append({'name': name, 'status': 'DECOMP_ERROR', 'error': str(e)[:100]})
            continue
        
        try:
            compile(src, '<test>', 'exec')
        except SyntaxError as e:
            syntax_err += 1
            results.append({'name': name, 'status': 'SYNTAX_ERROR', 'error': str(e)[:100]})
            continue
        
        orig_code = compile(open(py_path, encoding='utf-8').read(), py_path, 'exec')
        decomp_code = compile(src, '<decompiled>', 'exec')
        
        jdiff, tdiff = compare_bytecode(get_instructions(orig_code), get_instructions(decomp_code))
        
        if tdiff == 0 and jdiff == 0:
            status = 'PASS'
            passed += 1
        elif tdiff == 0:
            status = 'JUMP_DIFF'
            passed += 1
        else:
            status = 'FAIL'
            failed += 1
        
        results.append({
            'name': name, 'status': status,
            'jump_diffs': jdiff, 'true_diffs': tdiff
        })
        
    except Exception as e:
        results.append({'name': name, 'status': 'ERROR', 'error': str(e)[:100]})
    finally:
        if os.path.exists(pyc_path):
            try: os.remove(pyc_path)
            except: pass

print(f"Total: {total}, Pass: {passed}, Fail: {failed}")
print(f"Decomp errors: {decomp_err}, Syntax errors: {syntax_err}")
print(f"Pass rate: {passed}/{total} = {passed*100//total}%")

failures = [r for r in results if r['status'] == 'FAIL']
if failures:
    print("\n=== FAILURES ===")
    for r in failures:
        print(f"  {r['name']}: jdiff={r.get('jump_diffs')} tdiff={r.get('true_diffs')}")

with open('round2_bytecode_results.json', 'w', encoding='utf-8') as fp:
    json.dump({'summary': {'total': total, 'passed': passed, 'failed': failed}, 'results': results}, fp, indent=2, ensure_ascii=False)
