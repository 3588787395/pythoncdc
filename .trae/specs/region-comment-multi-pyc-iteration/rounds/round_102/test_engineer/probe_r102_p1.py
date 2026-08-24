import sys, os, marshal, types, importlib.util, dis, tempfile
sys.path.insert(0, '.')

SRC = os.path.join('.trae', 'specs', 'region-comment-multi-pyc-iteration',
                   'rounds', 'round_102', 'test_engineer', 'minimal_repros',
                   'repro_102_05_const_key_map_in_try_for_if.py')
source = open(SRC, encoding='utf-8').read()
code = compile(source, SRC, 'exec')

def find(code, name):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find(c, name)
            if r:
                return r

fn = find(code, 'trans')
print("=== ORIG trans ===")
dis.dis(fn)

import pycdc
pyc_path = tempfile.mkstemp(suffix='.pyc')[1]
with open(pyc_path, 'wb') as f:
    f.write(importlib.util.MAGIC_NUMBER + b'\x00' * 12)
    marshal.dump(code, f)
out = pycdc.decompile_pyc(pyc_path)
print("\n=== DECOMPILED SOURCE ===")
print(out)
