import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from testqouter.round1.base import decompile_pyc
import py_compile

with open('testqouter/round1/test_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fails = {k: v for k, v in data['details'].items() if v['status'] == 'FAIL'}

for name, info in sorted(fails.items()):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    
    py_file = info['file']
    py_path = os.path.join('testqouter/round1', py_file)
    pyc_path = py_path + 'c'
    
    if os.path.exists(pyc_path):
        os.remove(pyc_path)
    py_compile.compile(py_path, pyc_path)
    
    result = decompile_pyc(pyc_path)
    
    if 'bytecode_compare' in info.get('steps', {}):
        bc = info['steps']['bytecode_compare']
        true_diffs = bc.get('true_diffs', [])
        if true_diffs:
            td0 = true_diffs[0]
            print(f"  TRUE_DIFF: {td0.get('code_name', '?')} orig={td0.get('orig_ops', [])[:5]}... decomp={td0.get('decomp_ops', [])[:5]}...")
    
    if 'semantic_equivalence' in info.get('steps', {}):
        se = info['steps']['semantic_equivalence']
        mismatches = se.get('mismatches', [])
        if mismatches:
            m0 = mismatches[0]
            print(f"  SEMANTIC_MISMATCH: {m0.get('code_name', '?')} orig={m0.get('expected')} decomp={m0.get('actual')}")

print(f"\n\nTOTAL FAILS: {len(fails)}")
