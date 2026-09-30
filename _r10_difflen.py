import bisect, dis, difflib, marshal, py_compile, sys
from pathlib import Path
NOISE = {'NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG'}

def load_map(p):
    with open(p, 'rb') as f:
        f.read(16); code = marshal.load(f)
    out = {}
    def w(c, pfx=''):
        out.setdefault(pfx + c.co_name, c)
        for k in c.co_consts:
            if hasattr(k, 'co_name'): w(k, pfx + c.co_name + '.')
    w(code); return out

pyc = sys.argv[1]; fn = sys.argv[2]
ok = pyc[:-4] + 'OK.py'
o = load_map(pyc)[fn]
cf = py_compile.compile(ok, doraise=True, quiet=2)
d = load_map(cf)[fn]

def filt(c):
    return [i for i in dis.get_instructions(c) if i.opname not in NOISE]

fo, fd = filt(o), filt(d)
print('orig=%d decomp=%d' % (len(fo), len(fd)))
so = ['%s %s' % (i.opname, i.argrepr) for i in fo]
sd = ['%s %s' % (i.opname, i.argrepr) for i in fd]
sm = difflib.SequenceMatcher(None, so, sd, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        continue
    print('--- %s orig[%d:%d] decomp[%d:%d] ---' % (tag, i1, i2, j1, j2))
    for k in range(max(0, i1 - 7), min(len(so), i2 + 7)):
        mark = '  ' if i1 <= k < i2 else '  '
        print('   O%3d %-40s' % (k, so[k][:70]))
    for k in range(max(0, j1 - 7), min(len(sd), j2 + 7)):
        mark = '>>' if j1 <= k < j2 else '  '
        print('   %s D%3d %-40s' % (mark, k, sd[k][:70]))
    print()
