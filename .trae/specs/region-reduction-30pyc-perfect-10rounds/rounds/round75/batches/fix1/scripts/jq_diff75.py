"""R75 fix1 · jq_trans_module 两单元指令级 diff（诊断，只读 repo）。"""
import sys, io, os, dis, difflib, marshal, json

sys.stdout.reconfigure(encoding='utf-8')
SITE = 'F:/Downloads/pythoncdc-main/site-packages/'
REL = 'IQCommon/strategy/jq_trans_module.pyc'
OUT = r'D:/Temp/opencode/r75gate/fix1/dump/jq_diff75.txt'
UNITS = ['func_attribute_history_convert_code.replace_args',
         'func_get_bars_convert_code.replace_args']


def load_pyc(p):
    return marshal.loads(io.open(p, 'rb').read()[16:])


def find(co, path):
    parts = path.split('.')
    cur = co
    for p in parts:
        nxt = [c for c in cur.co_consts if hasattr(c, 'co_name') and c.co_name == p]
        if not nxt:
            return None
        cur = nxt[0]
    return cur


def tup(co):
    out = []
    for i in dis.get_instructions(co):
        out.append((i.opname, i.argval if i.arg is not None else None,
                    i.argrepr or '', i.offset))
    return out


def lines(co):
    d = {}
    for s, e, ln in co.co_lines():
        if ln is not None:
            for o in range(s, e, 2):
                d[o] = ln
    return d


os.makedirs(os.path.dirname(OUT), exist_ok=True)
o = load_pyc(SITE + REL)
p = compile(io.open(SITE + REL.replace('.pyc', 'OK.py'), encoding='utf-8').read(),
            'ok', 'exec')
res = {}
for u in UNITS:
    co, cp = find(o, u), find(p, u)
    A, B = tup(co), tup(cp)
    la, lb = lines(co), lines(cp)
    out = ['=' * 100, 'unit %s' % u, 'lenA=%d lenB=%d (bytes %d/%d)' % (
        len(A), len(B), len(co.co_code), len(cp.co_code)), '']
    # first divergence (opname+argval+line)
    fd = None
    for i in range(min(len(A), len(B))):
        if A[i][:2] != B[i][:2] or la.get(A[i][3]) != lb.get(B[i][3]):
            fd = i
            break
    if fd is not None:
        out.append('first div idx=%d  A=%s  B=%s  lineA=%s lineB=%s' % (
            fd, A[fd], B[fd], la.get(A[fd][3]), lb.get(B[fd][3])))
    # difflib over (opname, argval, line)
    sa = ['%s|%s|L%s' % (x[0], x[1], la.get(x[3])) for x in A]
    sb = ['%s|%s|L%s' % (x[0], x[1], lb.get(x[3])) for x in B]
    sm = difflib.SequenceMatcher(a=sa, b=sb, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        out.append('-- %s A[%d:%d](%d) B[%d:%d](%d)' % (tag, i1, i2, i2 - i1, j1, j2, j2 - j1))
        for k in range(i1, i2):
            out.append('   A %4d off=%-5d L%-4s %s %s' % (
                k, A[k][3], la.get(A[k][3]), A[k][0], A[k][2]))
        for k in range(j1, j2):
            out.append('   B %4d off=%-5d L%-4s %s %s' % (
                k, B[k][3], lb.get(B[k][3]), B[k][0], B[k][2]))
    res[u] = {'div': fd, 'ops': (len(A), len(B)),
              'blocks': [t for t in sm.get_opcodes() if t[0] != 'equal']}
    io.open(OUT, 'a', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')

print('wrote', OUT)
for k, v in res.items():
    print(k, v)
