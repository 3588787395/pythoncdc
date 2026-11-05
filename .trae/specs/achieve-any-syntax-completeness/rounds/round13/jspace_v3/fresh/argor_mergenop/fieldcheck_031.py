# rr-v5r114 REAL46-031 全嵌套 code object 递归字节比对（判官盲区核查）
import marshal, dis, py_compile

OUT = 'D:/temp/opencode/cl_layout/r114diag'
PYC = 'D:/Python/Lib/site-packages/packaging/__pycache__/version.cpython-311.pyc'
PROD = OUT + '/REAL46-031_v114.py'

py_compile.compile(PROD, cfile=OUT + '/prod114.pyc', doraise=True)
with open(PYC, 'rb') as f:
    f.read(16); orig = marshal.load(f)
with open(OUT + '/prod114.pyc', 'rb') as f:
    f.read(16); prod = marshal.load(f)

def walk(code, path, acc):
    acc.append((path, code))
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            walk(c, path + '/' + c.co_name, acc)

oa, pa = [], []
walk(orig, '', oa); walk(prod, '', pa)
print('orig code objects: %d, prod: %d' % (len(oa), len(pa)))
bad = []
for (op, oc), (pp, pc) in zip(oa, pa):
    if op != pp:
        bad.append(('PATH-MISMATCH', op, pp)); continue
    diffs = []
    if oc.co_code != pc.co_code: diffs.append('co_code(%d vs %d)' % (len(oc.co_code), len(pc.co_code)))
    if oc.co_exceptiontable != pc.co_exceptiontable: diffs.append('exceptiontable')
    if oc.co_names != pc.co_names: diffs.append('co_names')
    if oc.co_varnames != pc.co_varnames: diffs.append('co_varnames')
    if oc.co_argcount != pc.co_argcount: diffs.append('argcount')
    if oc.co_flags != pc.co_flags: diffs.append('flags(0x%x vs 0x%x)' % (oc.co_flags, pc.co_flags))
    # consts：code object 按名归一
    def norm(c): return tuple('<code:%s>' % x.co_name if hasattr(x, 'co_name') else x for x in c)
    if norm(oc.co_consts) != norm(pc.co_consts): diffs.append('co_consts')
    if diffs:
        bad.append((op, diffs))
print('field-level DIFF code objects: %d' % len(bad))
for b in bad[:20]:
    print('  ', b[0], b[1] if len(b) > 1 else '')
if not bad:
    print('ALL BYTE-EQUAL (excl. co_filename/firstlineno noise)')
