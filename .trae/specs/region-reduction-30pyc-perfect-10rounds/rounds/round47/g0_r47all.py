"""Round 47 G0: R47-A witness battery (line A) + R47-B falsification battery + prior batteries.

usage: python -X utf8 g0_r47all.py [arm]     (no arm = landed repo core)
Two witness sources:
  w47_witness.py       — 9 code objects: R47-A shape + 7 controls (line A)
  r47_tryret_witness.py— 15 code objects: try-body `return <expr>` shape (R47-B, falsified)
Plus the three pre-existing batteries (R45-A/R45-E controls/R46-B) as inertness controls.
"""
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r43gate'
HERE = r'D:/Temp/r47mine'
ARM = sys.argv[1] if len(sys.argv) > 1 else None
BASE = REPO if ARM is None else ROOT + '/mirr_' + ARM
WIT = [r'D:/Temp/r47diagA/w47_witness.py',
       r'D:/Temp/r47mine/r47_tryret_witness.py',
       r'D:/Temp/r46diagB/r46b_witness.py',
       r'D:/Temp/r43gate/r45e/r45e_witnesses.py',
       r'D:/Temp/r43gate/r45e/r45e2_controls.py']
sys.stdout.reconfigure(encoding='utf-8')
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
_p = importlib.util.spec_from_file_location('pc47all', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
_p.loader.exec_module(pc)
import dis


def sig(co):
    try:
        rows = [(i.opname, i.arg) for i in dis.get_instructions(co)]
    except Exception as e:
        rows = ['ERR %s' % e]
    return hashlib.sha256(repr(rows).encode('utf-8')).hexdigest()[:16]


tag = 'landed' if ARM is None else ARM
out = {}
for w in WIT:
    src = io.open(w, encoding='utf-8').read()
    py = os.path.join(HERE, 'z_%s_%s.py' % (tag, os.path.basename(w)[:-3]))
    io.open(py, 'w', encoding='utf-8', newline='\n').write(src)
    pyc = py[:-3] + '.pyc'
    py_compile.compile(py, cfile=pyc, doraise=True)
    txt = pc.decompile_pyc(pyc)
    prod = os.path.join(HERE, 'zprod_%s_%s.py' % (tag, os.path.basename(w)[:-3]))
    io.open(prod, 'w', encoding='utf-8', newline='\n').write(txt)
    orig = r10._load_map(pyc)
    dec = r10._compile_map(prod)
    defs, sigs = [], []
    for name, co in sorted(orig.items()):
        d = dec.get(name)
        s = sig(co)
        if d is None:
            defs.append([name, 'MISSING'])
            sigs.append([name, 'MISSING', s])
            continue
        kind, msg, is_defect = r10.strict_compare(co, d)
        if is_defect:
            defs.append([name, '%s %s' % (kind, msg)])
        sigs.append([name, sig(d), s])
    out[os.path.basename(w)] = {'n': len(orig), 'defective': defs, 'sigs': sigs}
    print('%-28s objs=%2d defective=%d %s' % (os.path.basename(w), len(orig), len(defs), [d[0] for d in defs]))
json.dump(out, io.open(os.path.join(HERE, 'zg0_%s.json' % tag), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
if len(sys.argv) > 2:
    a = json.load(io.open(sys.argv[2], encoding='utf-8'))
    for f in out:
        ch = [n for (n, x, _o) in out[f]['sigs'] if a[f] and dict((m, s) for m, s, o in a[f]['sigs']).get(n) != x]
        print('sig-changed-in %-28s %d/%d %s' % (f, len(ch), len(out[f]['sigs']), ch))
