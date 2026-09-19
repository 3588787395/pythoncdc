"""Compile repro .py -> .pyc, decompile with pycdc --region, recompile, compare.
Usage: python _r2_run_repro.py <repro.py> [funcname]
Writes <repro>.pyc next to the .py, decompiled source to <repro>_dec.py.
"""
import sys, os, py_compile, marshal, types, difflib, subprocess, tempfile
ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)
from testqouter.round1.base import compare_bytecode

def extract(code_obj, result=None):
    if result is None: result = {}
    result.setdefault(code_obj.co_name or '<module>', []).append(code_obj)
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType): extract(c, result)
    return result

def load(p):
    with open(p, 'rb') as f: f.read(16); return marshal.load(f)

def seq(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname in ('EXTENDED_ARG', 'PRECALL', 'NOP', 'RESUME', 'CACHE'): continue
        out.append(f"{i.opname} {i.argrepr}" if i.argrepr else i.opname)
    return out

import dis
def main():
    src = os.path.abspath(sys.argv[1])
    target_fn = sys.argv[2] if len(sys.argv) > 2 else None
    base = os.path.splitext(src)[0]
    pyc = base + '.pyc'
    py_compile.compile(src, cfile=pyc, doraise=True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'pycdc.py'), '--region', pyc],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    if r.returncode != 0 or not r.stdout.strip():
        print(f"DECOMPILE FAILED rc={r.returncode}\nstderr: {r.stderr[-2000:]}")
        return 2
    dec_src = r.stdout
    dec_py = base + '_dec.py'
    with open(dec_py, 'w', encoding='utf-8') as f: f.write(dec_src)
    try:
        dec_pyc = dec_py.replace('.py', '.pyc')
        py_compile.compile(dec_py, cfile=dec_pyc, doraise=True, quiet=2)
    except Exception as e:
        print(f"RECOMPILE FAILED: {e}")
        print(dec_src)
        return 3
    om, dm = extract(load(pyc)), extract(load(dec_pyc))
    names = [target_fn] if target_fn else sorted(set(om) & set(dm))
    any_mismatch = False
    for n in names:
        if n not in om or n not in dm:
            print(f"  [{n}] MISSING on one side (orig={n in om}, decomp={n in dm})"); any_mismatch = True; continue
        cmp = compare_bytecode(om[n][0], dm[n][0])
        o, d = seq(om[n][0]), seq(dm[n][0])
        ratio = difflib.SequenceMatcher(None, o, d, autojunk=False).ratio()
        status = 'MATCH' if (cmp.get('match') or cmp.get('jump_only')) else 'MISMATCH'
        if status == 'MISMATCH': any_mismatch = True
        print(f"  [{n}] {status} orig={cmp['orig_count']} decomp={cmp['decomp_count']} "
              f"true_diffs={len(cmp['true_diffs'])} jump_diffs={len(cmp['jump_diffs'])} raw_ratio={ratio:.3f}")
        for td in cmp.get('true_diffs', [])[:3]:
            if td.get('type') == 'missing_in_decomp':
                print(f"      idx{td['index']}: decomp missing {td['orig_op']} {td.get('orig_arg')}")
            else:
                print(f"      idx{td['index']}: orig {td['orig_op']}({td.get('orig_arg')}) vs decomp {td['decomp_op']}({td.get('decomp_arg')})")
    print("VERDICT:", "MISMATCH REPRODUCED" if any_mismatch else "decompiler matched (no repro)")
    return 0

sys.exit(main())
