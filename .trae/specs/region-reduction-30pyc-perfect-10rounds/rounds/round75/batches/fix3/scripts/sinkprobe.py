# -*- coding: utf-8 -*-
import importlib.util, io, marshal, os, sys
sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'
arm, pyc, func = sys.argv[1], sys.argv[2], sys.argv[3]
s = importlib.util.spec_from_file_location('h62x', os.path.join(CENTER, 'h62.py'))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
pycdc = m._load_arm(arm)
from core.cfg import build_cfg
code = marshal.loads(io.open(pyc,'rb').read()[16:])
def find(c, name):
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            if k.co_name == name: return k
            r = find(k, name)
            if r: return r
    return None
target = find(code, func) if func != '<module>' else code
cfg = build_cfg(target)
def sink(b, seen=None):
    # b is a sink if ALL normal paths from b end in RETURN/RAISE (no exit to other regions)
    if seen is None: seen=set()
    if b in seen: return True
    seen.add(b)
    exc = getattr(b,'exception_successors',None) or set()
    succs=[x for x in (b.successors or []) if x not in exc]
    if not succs:
        last=b.get_last_instruction()
        return last is not None and last.opname in ('RETURN_VALUE','RETURN_CONST','RAISE_VARARGS','RERAISE')
    return all(sink(x,seen) for x in succs)
for arg in sys.argv[4:]:
    t,e = [int(x) for x in arg.split(',')]
    tb=cfg.get_block_by_offset(t); eb=cfg.get_block_by_offset(e)
    tl=tb.get_last_instruction(); el=eb.get_last_instruction()
    print('then=%d last=%s succs=%s sink=%s | else=%d last=%s succs=%d sink=%s' % (
        t, tl.opname if tl else None, [x.start_offset for x in (tb.successors or [])], sink(tb),
        e, el.opname if el else None, len(eb.successors or []), sink(eb)))
