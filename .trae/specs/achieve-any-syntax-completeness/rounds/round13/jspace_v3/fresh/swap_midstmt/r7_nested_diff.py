# Deep-dive one G2c entry: diff the nested code object at module co_consts[idx]
# original = code object unmarshalled from the entry's pyc
# product  = compile(decompiled product .py)
import json, sys, types, dis, io, os, difflib, marshal

ROOT = r'F:\Downloads\pythoncdc-main'
entry_id = sys.argv[1]
idx = int(sys.argv[2])

space = json.load(open(os.path.join(ROOT, r'.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json'), encoding='utf-8'))
rec = None
for e in space['entries']:
    if isinstance(e, dict) and e.get('id') == entry_id:
        rec = e
        break
if rec is None:
    print('entry not found'); sys.exit(1)

pyc = os.path.join(ROOT, rec['pyc'])
prod_path = os.path.join(r'D:\temp\opencode\g2c_r5_products', entry_id + '.py')
print('pyc:', pyc, os.path.exists(pyc))
print('product:', prod_path, os.path.exists(prod_path))

# original code from pyc (py3.7+: header 16 bytes)
with open(pyc, 'rb') as f:
    data = f.read()
oc = None
for hdr in (16, 12):
    try:
        oc = marshal.loads(data[hdr:])
        if isinstance(oc, types.CodeType):
            break
    except Exception:
        oc = None
assert isinstance(oc, types.CodeType), 'marshal load failed'

psrc = open(prod_path, encoding='utf-8').read()
pc = compile(psrc, prod_path, 'exec')

def nested(c, i):
    v = c.co_consts[i]
    return v if isinstance(v, types.CodeType) else None

on, pn = nested(oc, idx), nested(pc, idx)
if on is None or pn is None:
    print('not code object: orig=%r prod=%r' % (type(on).__name__, type(pn).__name__))
    sys.exit(2)

print('orig nested: name=%s qualname=%s firstlineno=%s' % (on.co_name, on.co_qualname, on.co_firstlineno))
print('prod  nested: name=%s qualname=%s firstlineno=%s' % (pn.co_name, pn.co_qualname, pn.co_firstlineno))

def dump(c):
    buf = io.StringIO()
    dis.dis(c, file=buf, show_caches=False)
    return buf.getvalue().split('\n')

ol, pl = dump(on), dump(pn)
diff = list(difflib.unified_diff(ol, pl, 'original', 'product', lineterm='', n=3))
if not diff:
    print('DIS IDENTICAL -- metadata differs')
    print('name equal:', on.co_name == pn.co_name)
    print('qualname equal:', on.co_qualname == pn.co_qualname)
    print('consts equal:', on.co_consts == pn.co_consts)
    if on.co_consts != pn.co_consts:
        for i, (a, b) in enumerate(zip(on.co_consts, pn.co_consts)):
            if a != b:
                print('  const[%d]: %r vs %r' % (i, a, b))
        print('  len:', len(on.co_consts), len(pn.co_consts))
    print('names equal:', on.co_names == pn.co_names)
    if on.co_names != pn.co_names:
        print('  orig names:', on.co_names)
        print('  prod names:', pn.co_names)
    print('varnames equal:', on.co_varnames == pn.co_varnames, on.co_varnames, pn.co_varnames)
    print('flags:', on.co_flags, pn.co_flags)
else:
    print('DIS DIFF lines: %d' % len(diff))
    for l in diff[:130]:
        print(l)
