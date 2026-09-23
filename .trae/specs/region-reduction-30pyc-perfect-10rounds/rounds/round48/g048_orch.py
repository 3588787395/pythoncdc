"""G0: witness battery strict verdict + per-code-object instruction signature.
usage: python -X utf8 g048.py [arm ...]"""
import dis, hashlib, importlib.util, io, json, os, py_compile, sys
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r43gate'
HERE = r'D:/Temp/r48orchC'
WIT = [r'D:/Temp/r48orchC/w48_witness.py']
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s); _s.loader.exec_module(r10)

def sig(co):
    try:
        rows = [(i.opname, i.arg) for i in dis.get_instructions(co)]
    except Exception as e:
        rows = ['ERR %s' % e]
    return hashlib.sha256(repr(rows).encode('utf-8')).hexdigest()[:16]

def run(tag, base):
    for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
        del sys.modules[k]
    sys.path.insert(0, base); sys.path.append(REPO)
    _p = importlib.util.spec_from_file_location('pcg0', os.path.join(base, 'pycdc.py'))
    pc = importlib.util.module_from_spec(_p); _p.loader.exec_module(pc)
    out = {}
    for w in WIT:
        src = io.open(w, encoding='utf-8').read()
        py = os.path.join(HERE, 'g0_%s_%s.py' % (tag, os.path.basename(w)[:-3]))
        io.open(py, 'w', encoding='utf-8', newline='\n').write(src)
        pyc = py[:-3] + '.pyc'
        py_compile.compile(py, cfile=pyc, doraise=True)
        txt = pc.decompile_pyc(pyc)
        prod = os.path.join(HERE, 'g0prod_%s_%s.py' % (tag, os.path.basename(w)[:-3]))
        io.open(prod, 'w', encoding='utf-8', newline='\n').write(txt)
        orig = r10._load_map(pyc); dec = r10._compile_map(prod)
        defs, sigs = [], []
        for name, co in sorted(orig.items()):
            d = dec.get(name)
            if d is None:
                defs.append([name, 'MISSING']); sigs.append([name, 'MISSING']); continue
            kind, msg, isdef = r10.strict_compare(co, d)
            if isdef:
                defs.append([name, '%s %s' % (kind, msg)])
            sigs.append([name, sig(d)])
        out[os.path.basename(w)] = {'defective': defs, 'sigs': sigs, 'n': len(orig)}
    sys.path.pop(0)
    io.open(os.path.join(HERE, 'g0_%s.json' % tag), 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    return out

tags = {}
arms = ([''] + list(sys.argv[1:])) if len(sys.argv) > 1 else ['']
for arm in arms:
    tag = 'landed' if not arm else arm
    base = REPO if not arm else ROOT + '/mirr_' + arm
    tags[tag] = run(tag, base)
    sys.path.remove(REPO)
names = sorted({n for t in tags.values() for f in t.values() for n, _ in f['sigs']})
print('%-46s %-18s %-18s' % ('code object', 'landed sig', 'arm sig'))
keys = list(tags); land = tags.get('landed') or tags[keys[0]]
other = tags[keys[1]] if len(keys) > 1 else None
ident = 0
for nm in names:
    a = [s for f in land.values() for n, s in f['sigs'] if n == nm]
    b = [s for f in other.values() for n, s in f['sigs'] if n == nm] if other else []
    av = a[0] if a else '-'; bv = b[0] if b else '-'
    same = av == bv; ident += same
    print('%-46s %-18s %-18s %s' % (nm, av, bv, 'IDENTICAL' if same else '*** DIFFERS ***'))
print('n=%d identical=%d differs=%d' % (len(names), ident, len(names) - ident))
for tag, t in tags.items():
    tot = sum(len(f['defective']) for f in t.values())
    print('defective[%s]=%d/%d  %s' % (tag, tot, sum(f['n'] for f in t.values()),
                                       [d for f in t.values() for d in f['defective']]))
