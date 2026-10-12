"""unit_diff with the small-window filter removed (prints every hunk with 3 lines of context).

usage: python -X utf8 allwin_r63.py <pyc-abs> <unit> <prod>
"""
import argparse
import difflib
import importlib.util
import marshal
import sys

ap = argparse.ArgumentParser()
ap.add_argument('pyc')
ap.add_argument('unit')
ap.add_argument('prod')
A = ap.parse_args()

spec = importlib.util.spec_from_file_location('ud', 'D:/Temp/r73/work/unit_diff.py')
ud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ud)

orig = marshal.loads(open(A.pyc, 'rb').read()[16:])
comp = compile(open(A.prod, encoding='utf-8-sig').read(), '<p>', 'exec')
o, p = [], []
ud.gather(orig, o)
ud.gather(comp, p)
ol, pl = ud.dump(ud.pick(o, A.unit)), ud.dump(ud.pick(p, A.unit))
ok = [x.split(None, 1)[1].strip() for x in ol]
pk = [x.split(None, 1)[1].strip() for x in pl]
print('len orig=%d prod=%d delta=%d' % (len(ok), len(pk), len(pk) - len(ok)))
n = 0
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ok, pk, autojunk=False).get_opcodes():
    if tag == 'equal':
        continue
    n += 1
    print('== #%d %s orig[%d..%d %s..%s] prod[%d..%d] del=%d ins=%d' % (
        n, tag, i1, i2, ol[i1].split()[0] if i1 < len(ol) else '-',
        ol[i2 - 1].split()[0] if i2 > i1 else '-', j1, j2, i2 - i1, j2 - j1))
    for x in ol[max(0, i1 - 3):i2]:
        print('   - ' + x)
    for x in pl[max(0, j1 - 3):j2]:
        print('   + ' + x)
print('hunks=%d' % n)
