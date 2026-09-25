# -*- coding: utf-8 -*-
"""Print the live analyzer's region tree (full structural fields) for one code object.
usage: probe_regions.py <pyc> <fn> [nested-firstlineno]  -- if the fn has no nested match, dumps fn itself"""
import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag6')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
import regdump

def o(b): return getattr(b, 'start_offset', None)

pyc, fn = sys.argv[1], sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else None
root = regdump.load_pyc(pyc)
codes = [c for c in regdump.walk(root, []) if c.co_name == fn]
sel = []
for c in codes:
    for k in c.co_consts:
        if isinstance(k, types.CodeType) and (not want or k.co_firstlineno == want):
            sel.append(k)
if not sel: sel = codes
import dis
for code in sel:
    print('##### %s@L%d free=%s' % (code.co_name, code.co_firstlineno, code.co_freevars))
    for i in dis.get_instructions(code):
        if i.opname != 'CACHE': print('   %5d %-26s %s' % (i.offset, i.opname, str(i.argrepr)[:40]))
    gen, regions = regdump.dump(code)
