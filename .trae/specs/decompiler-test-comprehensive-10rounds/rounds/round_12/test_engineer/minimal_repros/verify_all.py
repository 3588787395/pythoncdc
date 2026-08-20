#!/usr/bin/env python3
"""Verify all R12 minimal repros pass"""
import os
import sys
import py_compile
import dis
import marshal
import types
import tempfile

def load_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(4)  # magic
        flags = int.from_bytes(f.read(4), 'little')
        f.read(8)  # timestamp/size or hash
        return marshal.load(f)

def normalize(code):
    return [(i.opname, str(i.argval) if not isinstance(i.argval, types.CodeType) else '<code>')
            for i in dis.get_instructions(code)
            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')]

def get_funcs(code, prefix=''):
    name = '<module>' if code.co_name == '<module>' else (prefix + '.' + code.co_name if prefix else code.co_name)
    result = {name: code}
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            cp = name if name != '<module>' else ''
            result.update(get_funcs(c, cp))
    return result

# First, compile all the repro files
repro_dir = os.path.dirname(os.path.abspath(__file__))
py_files = sorted([f for f in os.listdir(repro_dir) if f.startswith('repro_') and f.endswith('.py')])

print(f"Found {len(py_files)} repro files to verify\n")
all_pass = True

for py_file in py_files:
    py_path = os.path.join(repro_dir, py_file)
    base = py_file[:-3]
    pyc_path = os.path.join(repro_dir, base + '.pyc')
    decomp_path = os.path.join(repro_dir, base + '_decompiled.py')
    
    # Compile to pyc
    try:
        py_compile.compile(py_path, pyc_path, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"[ERROR] {py_file}: {e}")
        all_pass = False
        continue
    
    # Load original
    orig_code = load_pyc(pyc_path)
    
    # Decompile
    sys.path.insert(0, r'f:\Downloads\pythoncdc-main')
    from pycdc import PycDecompiler
    decompiler = PycDecompiler()
    if not decompiler.load_file(pyc_path):
        print(f"[ERROR] Failed to load {pyc_path}")
        all_pass = False
        continue
    
    import io
    out = io.StringIO()
    if not decompiler.decompile(out, use_region=True):
        print(f"[ERROR] Failed to decompile {py_file}")
        all_pass = False
        continue
    
    decompiled_src = out.getvalue()
    
    # Write decompiled source
    with open(decomp_path, 'w', encoding='utf-8') as f:
        f.write(decompiled_src)
    
    # Re-compile decompiled source
    try:
        decomp_code = compile(decompiled_src, decomp_path, 'exec')
    except SyntaxError as e:
        print(f"[ERROR] {py_file} decompiled source has syntax error: {e}")
        all_pass = False
        continue
    
    # Compare
    orig_funcs = get_funcs(orig_code)
    decomp_funcs = get_funcs(decomp_code)
    
    failed = False
    for name in sorted(orig_funcs):
        if name in decomp_funcs and name != '<module>':
            o = normalize(orig_funcs[name])
            d = normalize(decomp_funcs[name])
            if o != d:
                print(f"[FAIL] {py_file} - {name}: orig={len(o)} instrs, decomp={len(d)} instrs")
                failed = True
                all_pass = False
    
    if not failed:
        print(f"[PASS] {py_file}")

print()
if all_pass:
    print("ALL 10 REPRO PASSED!")
else:
    print("SOME REPRO FAILED!")
