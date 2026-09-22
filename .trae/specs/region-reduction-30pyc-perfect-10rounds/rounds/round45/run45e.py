"""Round 45 line E G0: does the core under test drop a 3.11 if/elif chain's post-chain tail?

usage: python -X utf8 run45e.py [arm]      (arm omitted => the LANDED repo core)
Compiles the synthetic witnesses with the local 3.11.7, decompiles them with that core,
then runs the strict ruler per code object and prints the emitted source.
"""
import importlib.util
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r43gate'
HERE = r'D:/Temp/r45e'
HERE = os.path.join(ROOT, 'r45e')
sys.stdout.reconfigure(encoding='utf-8')

arm = sys.argv[1] if len(sys.argv) > 1 else ''
BASE = REPO if not arm else ROOT + '/mirr_' + arm
assert os.path.isdir(BASE), BASE
print('=== core under test: %s' % BASE)

_r10 = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_r10)
_r10.loader.exec_module(r10)

src = os.path.join(HERE, 'r45e_witnesses.py')
pyc = os.path.join(HERE, 'r45e_witnesses.pyc')
py_compile.compile(src, cfile=pyc, doraise=True)
print('compiled with', sys.version.split()[0])

_p = importlib.util.spec_from_file_location('pc', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
sys.path.insert(0, REPO)
sys.path.insert(0, BASE)
_p.loader.exec_module(pc)
out = os.path.join(HERE, 'r45e_prod_%s.py' % (arm or 'landed'))
txt = pc.decompile_pyc(pyc)
io.open(out, 'w', encoding='utf-8').write(txt)

orig = r10._load_map(pyc)
dec = r10._compile_map(out)
bad = 0
for name, co in sorted(orig.items()):
    d = dec.get(name)
    if d is None:
        print('MISSING %s' % name)
        bad += 1
        continue
    kind, msg, isdef = r10.strict_compare(co, d)
    if isdef:
        bad += 1
    print('%-8s %-40s %s %s' % ('DEFECT' if isdef else 'clean', name, kind, msg[:70]))
print('RESULT %s: defective=%d/%d' % (arm or 'landed', bad, len(orig)))
print('----- emitted -----')
print(txt)
