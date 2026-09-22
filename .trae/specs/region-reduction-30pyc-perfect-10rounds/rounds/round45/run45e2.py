"""G0 extension runner: land-vs-arm byte identity over the r45e2 control shapes.

usage: python -X utf8 run45e2.py            (both sides: landed core and arm r45a)
A control shape that is already strict-clean on landed must be emitted BYTE-IDENTICAL
by the candidate; a shape the candidate changes must be reported for adjudication.
"""
import importlib.util
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r43gate'
HERE = os.path.join(ROOT, 'r45e')
ARM = sys.argv[1] if len(sys.argv) > 1 else 'r45a'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

src = os.path.join(HERE, 'r45e2_controls.py')
pyc = os.path.join(HERE, 'r45e2_controls.pyc')
py_compile.compile(src, cfile=pyc, doraise=True)


def produce(base, tag):
    for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
        del sys.modules[k]
    _p = importlib.util.spec_from_file_location('pc_' + tag, os.path.join(base, 'pycdc.py'))
    pc = importlib.util.module_from_spec(_p)
    sys.path.insert(0, REPO)
    sys.path.insert(0, base)
    _p.loader.exec_module(pc)
    out = os.path.join(HERE, 'r45e2_prod_%s.py' % tag)
    io.open(out, 'w', encoding='utf-8', newline='\n').write(pc.decompile_pyc(pyc))
    return out


def report(tag, out):
    orig = r10._load_map(pyc)
    dec = r10._compile_map(out)
    bad = []
    for name, co in sorted(orig.items()):
        d = dec.get(name)
        if d is None:
            bad.append((name, 'MISSING'))
            continue
        kind, msg, isdef = r10.strict_compare(co, d)
        if isdef:
            bad.append((name, '%s %s' % (kind, msg[:60])))
    print('%-8s defective=%d %s' % (tag, len(bad), bad))
    return bad


a = produce(REPO, 'landed')
b = produce(ROOT + '/mirr_' + ARM, ARM)
ta = report('landed', a)
tb = report(ARM, b)
sa = io.open(a, encoding='utf-8').read()
sb = io.open(b, encoding='utf-8').read()
if sa == sb:
    print('BYTE-IDENTICAL products: candidate is inert on all %d control shapes' % len(r10._load_map(pyc)))
else:
    import difflib
    print('PRODUCTS DIFFER:')
    print('\n'.join(difflib.unified_diff(sa.split('\n'), sb.split('\n'), 'landed', ARM, lineterm='', n=2)))
